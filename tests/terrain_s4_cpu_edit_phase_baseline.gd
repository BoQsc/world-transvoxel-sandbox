extends SceneTree
const ProbeUtil = preload("res://tests/terrain_probe_util.gd")
const WORLD_ROOT := "res://artifacts/scale_ladder/L4/world"
const WORLD_PATH := WORLD_ROOT + "/world.wtworld"
const JOURNAL_PATH := WORLD_ROOT + "/world.wtedit"
const TIMEOUT_FRAMES := 3600
const ACTIVE_CHUNK_CAPACITY := 1024
const RENDER_APPLY_BUDGET := 1
const SETTLED_MS := 300
const SAMPLE_SCALE := 65536
const EDIT_RADIUS := 2.0
const EDIT_STRENGTH := 6.0
var _scene_root: Node
var _terrain: Node
var _viewer: Node3D
var _samples: Dictionary = {}
var _sample_failures: Dictionary = {}
var _max_frame_ms := 0.0
var _last_us := 0
func _initialize() -> void:
	call_deferred("_run")
func _run() -> void:
	if not FileAccess.file_exists(WORLD_PATH):
		return _fail("L4 world missing; run python tools/scale_ladder.py --level L4 --force")
	_remove_journal()
	if not _setup_scene():
		return
	if not await _wait_for_world():
		return _fail("world did not become ready")
	_move_viewer(Vector3(1024, 56, 1024), Vector3(1024, 20, 1120))
	if not await _wait_for_settled_resources(20000):
		return _fail("initial S4 window did not settle")
	var journal_before := _file_size(JOURNAL_PATH)
	var cycles: Array[Dictionary] = []
	var centers: Array[Vector3] = [Vector3(1200, 16, 1200), Vector3(1320, 16, 1320)]
	for index in range(centers.size()):
		var cycle := await _run_cycle(index, centers[index])
		if not bool(cycle.get("ok", false)):
			return _fail(str(cycle["error"]))
		cycles.append(cycle)
	if not _terrain.stop_world():
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if _terrain.get_world_state_name() == "stopped":
			_print_pass(cycles, _file_size(JOURNAL_PATH) - journal_before)
			_scene_root.queue_free()
			_remove_journal()
			quit(0)
			return
		await process_frame
	_fail("world did not stop after S4 CPU edit phase baseline")
func _setup_scene() -> bool:
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		_fail("terrain lab scene could not load")
		return false
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
	_viewer.set("input_enabled", false)
	_terrain.authoritative_samples_ready.connect(_on_samples_ready)
	_terrain.authoritative_samples_failed.connect(_on_samples_failed)
	root.add_child(_scene_root)
	_last_us = Time.get_ticks_usec()
	return true
func _run_cycle(index: int, center: Vector3) -> Dictionary:
	_move_viewer(center + Vector3(0, 40, 0), center + Vector3(0, 8, 96))
	if not await _wait_for_settled_resources(20000):
		return _bad("pre-edit movement did not settle")
	if not ProbeUtil.probe_render_and_collision(_terrain, Vector3(center.x, 0, center.z)):
		return _bad("pre-edit probe failed")
	var points := _sphere_grid_points(center, EDIT_RADIUS)
	var before: Dictionary = _terrain.get_runtime_metrics()
	var revision_before: int = _terrain.get_world_revision()
	var edit_start := Time.get_ticks_msec()
	var capture_ms := await _time_capture(points)
	if capture_ms < 0:
		return _bad("pre-edit sample capture failed")
	var submit_start := Time.get_ticks_msec()
	var transaction: Object = _terrain.begin_edit_transaction(603)
	if transaction == null or not transaction.add_density_sphere(center, EDIT_RADIUS, EDIT_STRENGTH):
		return _bad("edit transaction build failed")
	if not _terrain.commit_edit_transaction(transaction):
		return _bad("edit transaction commit was rejected")
	var submit_ms := Time.get_ticks_msec() - submit_start
	var commit_ms := await _time_wait("commit", revision_before, before)
	var mesh_ms := await _time_wait("mesh", revision_before, before)
	var render_ms := await _time_wait("render", revision_before, before)
	var collision_ms := await _time_wait("collision", revision_before, before)
	var settle_ms := await _time_wait("settle", revision_before, before)
	for value in [commit_ms, mesh_ms, render_ms, collision_ms, settle_ms]:
		if int(value) < 0:
			return _bad("edit phase wait failed")
	var after: Dictionary = _terrain.get_runtime_metrics()
	var cycle := {
		"ok": true, "index": index, "samples": points.size(),
		"capture_ms": capture_ms, "submit_ms": submit_ms, "commit_ms": commit_ms,
		"mesh_ms": mesh_ms, "render_ms": render_ms, "collision_ms": collision_ms,
		"settle_ms": settle_ms, "total_ms": Time.get_ticks_msec() - edit_start,
		"replacements": _delta(after, before, "edit_replacements"),
		"mesh_delta": _delta(after, before, "mesh_completions"),
		"render_delta": _delta(after, before, "application_applied_render"),
		"collision_delta": _delta(after, before, "application_applied_collision"),
	}
	print("WT_SANDBOX_S4_CPU_EDIT_PHASE_CYCLE " + _fields(cycle))
	return cycle
func _time_capture(points: Array[Vector3i]) -> int:
	var started := Time.get_ticks_msec()
	var samples := await _query_samples(points)
	return Time.get_ticks_msec() - started if samples.size() == points.size() else -1
func _time_wait(kind: String, revision: int, before: Dictionary) -> int:
	var started := Time.get_ticks_msec()
	if kind == "settle":
		return Time.get_ticks_msec() - started if await _wait_for_settled_resources(20000) else -1
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = _terrain.get_runtime_metrics()
		var ready := false
		if kind == "commit":
			ready = _terrain.get_world_revision() > revision and int(metrics.get("edit_commits", 0)) > int(before.get("edit_commits", 0))
		elif kind == "mesh":
			ready = int(metrics.get("edit_replacements", 0)) > int(before.get("edit_replacements", 0)) and int(metrics.get("mesh_jobs", 0)) > int(before.get("mesh_jobs", 0)) and int(metrics.get("mesh_completions", 0)) >= int(metrics.get("mesh_jobs", 0))
		elif kind == "render":
			ready = int(metrics.get("queued_render", 0)) == 0 and int(metrics.get("visual_ready_chunk_records", -1)) == int(metrics.get("active_chunk_records", 0))
		elif kind == "collision":
			ready = int(metrics.get("queued_collision", 0)) == 0 and int(metrics.get("fully_ready_chunk_records", -1)) == int(metrics.get("active_chunk_records", 0))
		if ready:
			return Time.get_ticks_msec() - started
		await process_frame
		_track_frame()
	return -1
func _wait_for_settled_resources(max_ms: int) -> bool:
	var started := Time.get_ticks_msec()
	var ready_since := -1
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = _terrain.get_runtime_metrics()
		var ready: bool = _terrain.get_rendered_chunk_count() > 0 and _terrain.get_collision_chunk_count() > 0 and int(metrics.get("queued_render", 0)) == 0 and int(metrics.get("queued_collision", 0)) == 0 and int(metrics.get("mesh_jobs", 0)) == int(metrics.get("mesh_completions", -1)) and int(metrics.get("fully_ready_chunk_records", -1)) == int(metrics.get("active_chunk_records", 0)) and int(metrics.get("pending_chunk_retirements", 0)) == 0 and int(metrics.get("render_fading_resources", 0)) == 0 and int(metrics.get("active_chunk_records", 0)) <= ACTIVE_CHUNK_CAPACITY
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
func _query_samples(points: Array[Vector3i]) -> Array:
	var request_id: int = _terrain.request_authoritative_samples(points, 0)
	if request_id <= 0:
		return []
	for _frame in range(TIMEOUT_FRAMES):
		if _samples.has(request_id):
			var samples: Array = _samples[request_id]
			_samples.erase(request_id)
			return samples
		if _sample_failures.has(request_id):
			return []
		await process_frame
		_track_frame()
	return []
func _sphere_grid_points(center: Vector3, radius: float) -> Array[Vector3i]:
	var center_q := Vector3i(roundi(center.x * SAMPLE_SCALE), roundi(center.y * SAMPLE_SCALE), roundi(center.z * SAMPLE_SCALE))
	var radius_q := roundi(radius * SAMPLE_SCALE)
	var minimum := Vector3i(floori(float(center_q.x - radius_q) / SAMPLE_SCALE), floori(float(center_q.y - radius_q) / SAMPLE_SCALE), floori(float(center_q.z - radius_q) / SAMPLE_SCALE))
	var maximum := Vector3i(ceili(float(center_q.x + radius_q) / SAMPLE_SCALE), ceili(float(center_q.y + radius_q) / SAMPLE_SCALE), ceili(float(center_q.z + radius_q) / SAMPLE_SCALE))
	var points: Array[Vector3i] = []
	for z in range(minimum.z, maximum.z + 1):
		for y in range(minimum.y, maximum.y + 1):
			for x in range(minimum.x, maximum.x + 1):
				var delta := Vector3i(x * SAMPLE_SCALE - center_q.x, y * SAMPLE_SCALE - center_q.y, z * SAMPLE_SCALE - center_q.z)
				if delta.length_squared() <= radius_q * radius_q:
					points.append(Vector3i(x, y, z))
	return points
func _print_pass(cycles: Array[Dictionary], journal_growth: int) -> void:
	var maximum := {"capture_ms": 0, "submit_ms": 0, "commit_ms": 0, "mesh_ms": 0, "render_ms": 0, "collision_ms": 0, "settle_ms": 0, "total_ms": 0}
	for cycle in cycles:
		for key in maximum.keys():
			maximum[key] = maxi(int(maximum[key]), int(cycle.get(key, 0)))
	var metrics: Dictionary = _terrain.get_runtime_metrics()
	print("WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_PASS cycles=%d samples=%d max_capture_ms=%d max_submit_ms=%d max_commit_ms=%d max_mesh_ms=%d max_render_ms=%d max_collision_ms=%d max_settle_ms=%d max_total_ms=%d journal_growth_bytes=%d max_frame_ms=%.3f max_active=%d active_capacity=%d" % [cycles.size(), int(cycles[0]["samples"]), maximum["capture_ms"], maximum["submit_ms"], maximum["commit_ms"], maximum["mesh_ms"], maximum["render_ms"], maximum["collision_ms"], maximum["settle_ms"], maximum["total_ms"], journal_growth, _max_frame_ms, int(metrics.get("active_chunk_records", 0)), ACTIVE_CHUNK_CAPACITY])
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
func _fields(fields: Dictionary) -> String:
	var items: Array[String] = []
	for key in fields.keys():
		if key != "ok":
			items.append(str(key) + "=" + str(fields[key]))
	return " ".join(items)
func _delta(after: Dictionary, before: Dictionary, key: String) -> int:
	return int(after.get(key, 0)) - int(before.get(key, 0))
func _bad(message: String) -> Dictionary:
	return {"ok": false, "error": message}
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
func _on_samples_ready(request_id: int, samples: Array) -> void:
	_samples[request_id] = samples
func _on_samples_failed(request_id: int, error: String) -> void:
	_sample_failures[request_id] = error
func _fail(message: String) -> void:
	push_error("WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_FAIL: " + message)
	if _terrain != null:
		print("WT_SANDBOX_S4_CPU_EDIT_PHASE_BASELINE_METRICS " + str(_terrain.get_runtime_metrics()))
	if _scene_root != null:
		_scene_root.queue_free()
	_remove_journal()
	quit(1)
