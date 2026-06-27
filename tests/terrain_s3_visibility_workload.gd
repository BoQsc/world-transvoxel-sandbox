extends SceneTree
const ProbeUtil = preload("res://tests/terrain_probe_util.gd")
const WORLD_ROOT := "res://artifacts/scale_ladder/L4/world"
const WORLD_PATH := WORLD_ROOT + "/world.wtworld"
const JOURNAL_PATH := WORLD_ROOT + "/world.wtedit"
const TIMEOUT_FRAMES := 3600
const ACTIVE_CHUNK_CAPACITY := 1024
const RENDER_APPLY_BUDGET := 1
const MAX_INITIAL_SETTLE_MS := 20000
const MAX_PHASE_SETTLE_MS := 20000
const MAX_FRAME_MS := 250.0
const MAX_JOURNAL_GROWTH_BYTES := 2097152
const MAX_EDIT_MS := 15000
const SETTLED_MS := 300
var _scene_root: Node
var _terrain: Node
var _viewer: Node3D
var _camera: Camera3D
var _max_frame_ms := 0.0
var _last_us := 0
func _initialize() -> void:
	call_deferred("_run")
func _run() -> void:
	if not FileAccess.file_exists(WORLD_PATH):
		return _fail("L4 world missing; run python tools/scale_ladder.py --level L4 --force")
	_remove_journal()
	var started := Time.get_ticks_msec()
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		return _fail("terrain lab scene could not load")
	_scene_root = packed.instantiate()
	_scene_root.world_manifest_path = WORLD_PATH
	_scene_root.world_object_root = WORLD_ROOT
	_scene_root.world_max = Vector3(2047.999, 63.999, 2047.999)
	_scene_root.radius_chunks = 3
	_scene_root.maximum_lod = 1
	_scene_root.streaming_update_distance = 0.0
	_scene_root.streaming_follows_viewer = true
	_terrain = _scene_root.get_node("Terrain")
	var config: Resource = _terrain.get("configuration").duplicate(true)
	config.set("active_chunk_capacity", ACTIVE_CHUNK_CAPACITY)
	config.set("render_apply_budget", RENDER_APPLY_BUDGET)
	_terrain.set("configuration", config)
	_viewer = _scene_root.get_node("Viewer")
	_camera = _scene_root.get_node("Viewer/Camera3D")
	_viewer.set("input_enabled", false)
	root.add_child(_scene_root)
	_last_us = Time.get_ticks_usec()
	if not await _wait_for_world():
		return _fail("world did not become ready")
	var startup_ms := Time.get_ticks_msec() - started
	_move_viewer(Vector3(1024.0, 56.0, 1024.0), Vector3(1024.0, 20.0, 1100.0))
	var settle_started := Time.get_ticks_msec()
	if not await _wait_for_settled_resources(MAX_INITIAL_SETTLE_MS):
		return _fail("initial S3 streaming window did not settle")
	var settle_ms := Time.get_ticks_msec() - settle_started
	var stable := await _phase_stable()
	var normal := await _phase_movement([
		Vector3(768.0, 56.0, 768.0), Vector3(896.0, 56.0, 896.0),
		Vector3(1024.0, 56.0, 1024.0), Vector3(1152.0, 56.0, 1152.0),
	])
	var rapid := await _phase_rapid_turns()
	var underground := await _phase_movement([
		Vector3(896.0, 18.0, 1152.0), Vector3(1024.0, 18.0, 1024.0),
		Vector3(1152.0, 18.0, 896.0),
	])
	var mining := await _phase_mining_while_moving()
	for item in [stable, normal, rapid, underground, mining]:
		if not bool(item["ok"]):
			return _fail(str(item["error"]))
	if not _terrain.stop_world():
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if _terrain.get_world_state_name() == "stopped":
			print(
				"WT_SANDBOX_S3_VISIBILITY_WORKLOAD_PASS startup_ms=%d settle_ms=%d "
				% [startup_ms, settle_ms] +
				"classes=5 normal_positions=%d underground_positions=%d "
				% [int(normal["positions"]), int(underground["positions"])] +
				"rapid_turns=%d frustum_min=%d frustum_max=%d "
				% [int(rapid["turns"]), int(rapid["frustum_min"]), int(rapid["frustum_max"])] +
				"viewer_updates_delta=%d planned_demands_delta=%d "
				% [int(rapid["viewer_updates_delta"]), int(rapid["planned_demands_delta"])] +
				"min_render=%d min_collision=%d max_active=%d "
				% [int(normal["min_render"]), int(normal["min_collision"]), int(normal["max_active"])] +
				"edit_cycles=%d max_edit_ms=%d journal_growth_bytes=%d "
				% [int(mining["edit_cycles"]), int(mining["max_edit_ms"]), int(mining["journal_growth_bytes"])] +
				"max_frame_ms=%.3f fast_travel_policy=loading_screen_required"
				% _max_frame_ms
			)
			_scene_root.queue_free()
			_remove_journal()
			quit(0)
			return
		await process_frame
	_fail("world did not stop after S3 workload")
func _phase_stable() -> Dictionary:
	var before: Dictionary = _terrain.get_runtime_metrics()
	for _frame in range(60):
		await process_frame
		_track_frame()
	var after: Dictionary = _terrain.get_runtime_metrics()
	for key in ["viewer_updates", "sample_jobs", "mesh_jobs", "mesh_completions",
			"published_events", "edit_commits"]:
		if int(after.get(key, -1)) != int(before.get(key, -2)):
			return {"ok": false, "error": "stable phase changed " + key}
	if _max_frame_ms > MAX_FRAME_MS:
		return {"ok": false, "error": "stable frame exceeded budget"}
	return {"ok": true, "frustum_visible": _estimate_visible_render_chunks()}
func _phase_movement(positions: Array[Vector3]) -> Dictionary:
	var min_render := 999999
	var min_collision := 999999
	var max_active := 0
	for position in positions:
		_move_viewer(position, position + Vector3(0.0, -24.0, 96.0))
		if not await _wait_for_settled_resources(MAX_PHASE_SETTLE_MS):
			return {"ok": false, "error": "movement did not settle at " + str(position)}
		var metrics: Dictionary = _terrain.get_runtime_metrics()
		min_render = mini(min_render, _terrain.get_rendered_chunk_count())
		min_collision = mini(min_collision, _terrain.get_collision_chunk_count())
		max_active = maxi(max_active, int(metrics.get("active_chunk_records", 0)))
		if not ProbeUtil.probe_render_and_collision(_terrain, Vector3(position.x, 0.0, position.z)):
			return {"ok": false, "error": "probe failed at " + str(position)}
	return {"ok": true, "positions": positions.size(), "min_render": min_render,
		"min_collision": min_collision, "max_active": max_active}
func _phase_rapid_turns() -> Dictionary:
	var before: Dictionary = _terrain.get_runtime_metrics()
	var min_visible := 999999
	var max_visible := 0
	var targets: Array[Vector3] = [
		Vector3(1024.0, 20.0, 1220.0), Vector3(1220.0, 20.0, 1024.0),
		Vector3(1024.0, 20.0, 828.0), Vector3(828.0, 20.0, 1024.0),
		Vector3(1160.0, 20.0, 1160.0), Vector3(888.0, 20.0, 1160.0),
	]
	for target in targets:
		_viewer.look_at(target, Vector3.UP)
		await process_frame
		await process_frame
		_track_frame()
		var visible := _estimate_visible_render_chunks()
		min_visible = mini(min_visible, visible)
		max_visible = maxi(max_visible, visible)
	var after: Dictionary = _terrain.get_runtime_metrics()
	var viewer_delta := int(after.get("viewer_updates", 0)) - int(before.get("viewer_updates", 0))
	var demand_delta := int(after.get("planned_demands", 0)) - int(before.get("planned_demands", 0))
	if viewer_delta != 0 or demand_delta != 0:
		return {"ok": false, "error": "rapid turns changed terrain demand"}
	return {"ok": true, "turns": targets.size(), "frustum_min": min_visible,
		"frustum_max": max_visible, "viewer_updates_delta": viewer_delta,
		"planned_demands_delta": demand_delta}
func _phase_mining_while_moving() -> Dictionary:
	var journal_before := _file_size(JOURNAL_PATH)
	var max_edit_ms := 0
	var points: Array[Vector3i] = [Vector3i(1200, 16, 1200), Vector3i(1320, 16, 1320)]
	for point in points:
		_move_viewer(Vector3(point.x, 56.0, point.z), Vector3(point.x, 20.0, point.z + 96))
		if not await _wait_for_settled_resources(MAX_PHASE_SETTLE_MS):
			return {"ok": false, "error": "pre-edit movement did not settle"}
		var revision_before: int = _terrain.get_world_revision()
		var edit_started := Time.get_ticks_msec()
		var transaction: Object = _terrain.begin_edit_transaction(603)
		if transaction == null or not transaction.add_density_sphere(Vector3(point), 3.0, 6.0) or \
				not _terrain.commit_edit_transaction(transaction):
			return {"ok": false, "error": "mining edit was rejected"}
		if not await _wait_for_revision_and_settle(revision_before):
			return {"ok": false, "error": "mining edit did not settle"}
		max_edit_ms = maxi(max_edit_ms, Time.get_ticks_msec() - edit_started)
	var journal_growth := _file_size(JOURNAL_PATH) - journal_before
	if max_edit_ms > MAX_EDIT_MS:
		return {"ok": false, "error": "mining edit exceeded latency budget"}
	if journal_growth > MAX_JOURNAL_GROWTH_BYTES:
		return {"ok": false, "error": "journal growth exceeded budget"}
	return {"ok": true, "edit_cycles": points.size(), "max_edit_ms": max_edit_ms,
		"journal_growth_bytes": journal_growth}
func _move_viewer(position: Vector3, target: Vector3) -> void:
	_viewer.global_position = position
	_viewer.look_at(target, Vector3.UP)
	_viewer.emit_signal("position_changed", _viewer.global_position)
func _wait_for_world() -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if _terrain.is_world_running():
			return true
		await process_frame
		_track_frame()
	return false
func _wait_for_revision_and_settle(revision: int) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if _terrain.get_world_revision() > revision:
			return await _wait_for_settled_resources(MAX_PHASE_SETTLE_MS)
		await process_frame
		_track_frame()
	return false
func _wait_for_settled_resources(max_ms: int) -> bool:
	var started := Time.get_ticks_msec()
	var ready_since := -1
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = _terrain.get_runtime_metrics()
		var ready: bool = _terrain.get_rendered_chunk_count() > 0 and _terrain.get_collision_chunk_count() > 0 and \
			int(metrics.get("queued_render", 0)) == 0 and int(metrics.get("queued_collision", 0)) == 0 and \
			int(metrics.get("mesh_jobs", 0)) == int(metrics.get("mesh_completions", -1)) and \
			int(metrics.get("fully_ready_chunk_records", -1)) == int(metrics.get("active_chunk_records", 0)) and \
			int(metrics.get("pending_chunk_retirements", 0)) == 0 and \
			int(metrics.get("render_fading_resources", 0)) == 0 and \
			int(metrics.get("active_chunk_records", 0)) <= ACTIVE_CHUNK_CAPACITY
		if ready:
			if ready_since < 0:
				ready_since = Time.get_ticks_msec()
			elif Time.get_ticks_msec() - ready_since >= SETTLED_MS:
				return true
		else:
			ready_since = -1
		if Time.get_ticks_msec() - started > max_ms:
			return false
		await process_frame
		_track_frame()
	return false
func _estimate_visible_render_chunks() -> int:
	var count := 0
	for child in _terrain.get_children():
		if child is MeshInstance3D and child.name.begins_with("WT_Render_"):
			var bounds: AABB = child.global_transform * child.get_aabb()
			if _camera.is_position_in_frustum(bounds.get_center()):
				count += 1
	return count
func _track_frame() -> void:
	var now_us := Time.get_ticks_usec()
	if _last_us > 0:
		_max_frame_ms = maxf(_max_frame_ms, float(now_us - _last_us) / 1000.0)
	_last_us = now_us
func _file_size(path: String) -> int:
	if not FileAccess.file_exists(path):
		return 0
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return 0
	var length := file.get_length()
	file.close()
	return length
func _remove_journal() -> void:
	if FileAccess.file_exists(JOURNAL_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(JOURNAL_PATH))
func _fail(message: String) -> void:
	push_error("WT_SANDBOX_S3_VISIBILITY_WORKLOAD_FAIL: " + message)
	if _terrain != null:
		print("WT_SANDBOX_S3_VISIBILITY_WORKLOAD_METRICS " + str(_terrain.get_runtime_metrics()))
	if _scene_root != null:
		_scene_root.queue_free()
	_remove_journal()
	quit(1)
