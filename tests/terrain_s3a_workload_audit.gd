extends SceneTree
const ProbeUtil = preload("res://tests/terrain_probe_util.gd")
const TIMEOUT_FRAMES := 1800
const IDLE_FRAMES := 120
const JOURNAL_PATH := "res://world/world.wtedit"
const EXPECTED_ACTIVE_CHUNKS := 256
const MIN_RENDER_COLLISION_CHUNKS := 160
const MAX_ACTIVE_CHUNKS := 512
const MAX_STARTUP_MS := 10000
const MAX_SETTLE_MS := 10000
const MAX_FRAME_MS := 250.0
const MAX_EDIT_MS := 10000
const MAX_JOURNAL_GROWTH_BYTES := 1048576
const EDIT_CYCLES := 3
var _scene_root: Node
func _initialize() -> void:
	call_deferred("_run")
func _run() -> void:
	var absolute_journal := ProjectSettings.globalize_path(JOURNAL_PATH)
	if FileAccess.file_exists(JOURNAL_PATH):
		DirAccess.remove_absolute(absolute_journal)
	var started := Time.get_ticks_msec()
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		return _fail("terrain lab scene could not load")
	_scene_root = packed.instantiate()
	_scene_root.radius_chunks = 4
	_scene_root.maximum_lod = 0
	_scene_root.streaming_follows_viewer = false
	_scene_root.streaming_update_distance = 8.0
	_scene_root.get_node("Viewer").set("input_enabled", false)
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	var viewer: Node3D = _scene_root.get_node("Viewer")
	if not await _wait_for_world(terrain):
		return _fail("world did not become ready")
	var startup_ms := Time.get_ticks_msec() - started
	if startup_ms > MAX_STARTUP_MS:
		return _fail("startup exceeded budget: %d ms" % startup_ms)
	var settle_started := Time.get_ticks_msec()
	if not await _wait_for_settled_resources(terrain):
		return _fail("initial LOD0 world did not settle")
	var settle_ms := Time.get_ticks_msec() - settle_started
	if settle_ms > MAX_SETTLE_MS:
		return _fail("initial settle exceeded budget: %d ms" % settle_ms)
	var settled: Dictionary = terrain.get_runtime_metrics()
	if int(settled.get("active_chunk_records", 0)) < EXPECTED_ACTIVE_CHUNKS or \
			int(settled.get("fully_ready_chunk_records", 0)) < EXPECTED_ACTIVE_CHUNKS:
		return _fail("full LOD0 active set was not loaded")
	if terrain.get_rendered_chunk_count() < MIN_RENDER_COLLISION_CHUNKS or \
			terrain.get_collision_chunk_count() < MIN_RENDER_COLLISION_CHUNKS:
		return _fail("LOD0 render/collision resource coverage is too low")
	if int(settled.get("active_chunk_records", 0)) > MAX_ACTIVE_CHUNKS:
		return _fail("active chunk records exceed L0 capacity")
	var idle := await _measure_cold_phase(terrain, IDLE_FRAMES)
	if not bool(idle["ok"]):
		return _fail(str(idle["error"]))
	var movement := await _audit_fixed_anchor_movement(terrain, viewer)
	if not bool(movement["ok"]):
		return _fail(str(movement["error"]))
	viewer.global_position = Vector3(64.0, 60.0, 64.0)
	viewer.look_at(Vector3(64.0, 28.0, 64.0), Vector3.FORWARD)
	viewer.emit_signal("position_changed", viewer.global_position)
	await physics_frame
	await physics_frame
	if not ProbeUtil.probe_render_and_collision(terrain, Vector3(64.0, 0.0, 64.0)):
		return _fail("center edit probe does not have render/collision coverage")
	var metrics_before: Dictionary = terrain.get_runtime_metrics()
	var journal_before := _file_size(JOURNAL_PATH)
	var max_carve_submit_ms := 0
	var max_carve_total_ms := 0
	var max_restore_ms := 0
	for _cycle in range(EDIT_CYCLES):
		var revision_before: int = terrain.get_world_revision()
		var carve_started := Time.get_ticks_msec()
		if not await _scene_root.call("submit_mining_at_aim", false, false):
			return _fail("carve submission was rejected")
		max_carve_submit_ms = maxi(
			max_carve_submit_ms, Time.get_ticks_msec() - carve_started
		)
		if not await _wait_for_revision_and_settle(terrain, revision_before):
			return _fail("carve did not commit and settle")
		max_carve_total_ms = maxi(
			max_carve_total_ms, Time.get_ticks_msec() - carve_started
		)
		if _scene_root.call("get_restorable_carve_count") != 1:
			return _fail("carve was not recorded for exact restoration")
		revision_before = terrain.get_world_revision()
		var restore_started := Time.get_ticks_msec()
		if not _scene_root.call("restore_last_carve"):
			return _fail("restore submission was rejected")
		if not await _wait_for_revision_and_settle(terrain, revision_before):
			return _fail("restore did not commit and settle")
		max_restore_ms = maxi(
			max_restore_ms, Time.get_ticks_msec() - restore_started
		)
		if _scene_root.call("get_restorable_carve_count") != 0:
			return _fail("restore left stale carve history")
	var metrics_after: Dictionary = terrain.get_runtime_metrics()
	var edit_commits := (
		int(metrics_after.get("edit_commits", 0)) -
		int(metrics_before.get("edit_commits", 0))
	)
	if edit_commits != EDIT_CYCLES * 2:
		return _fail("unexpected edit commit count: %d" % edit_commits)
	if int(metrics_after.get("edit_rejections", 0)) != \
			int(metrics_before.get("edit_rejections", 0)):
		return _fail("edit rejection count changed")
	var journal_growth := _file_size(JOURNAL_PATH) - journal_before
	if journal_growth > MAX_JOURNAL_GROWTH_BYTES:
		return _fail("edit journal growth exceeded budget: %d" % journal_growth)
	if max_carve_submit_ms > MAX_EDIT_MS or max_carve_total_ms > MAX_EDIT_MS or \
			max_restore_ms > MAX_EDIT_MS:
		return _fail("edit or restore latency exceeded budget")
	var post_edit_idle := await _measure_cold_phase(terrain, IDLE_FRAMES)
	if not bool(post_edit_idle["ok"]):
		return _fail("post-edit idle: " + str(post_edit_idle["error"]))
	var final_render: int = terrain.get_rendered_chunk_count()
	var final_collision: int = terrain.get_collision_chunk_count()
	var final_active := int(metrics_after.get("active_chunk_records", 0))
	if not terrain.stop_world():
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.get_world_state_name() == "stopped":
			print(
				"WT_SANDBOX_S3A_WORKLOAD_PASS startup_ms=%d settle_ms=%d "
				% [startup_ms, settle_ms] +
				"render=%d collision=%d active=%d idle_frames=%d "
				% [
					final_render,
					final_collision,
					final_active,
					IDLE_FRAMES * 2,
				] +
				"max_idle_frame_ms=%.3f max_move_frame_ms=%.3f "
				% [
					maxf(float(idle["max_frame_ms"]), float(post_edit_idle["max_frame_ms"])),
					float(movement["max_frame_ms"]),
				] +
				"move_positions=%d edit_cycles=%d edit_commits=%d "
				% [int(movement["positions"]), EDIT_CYCLES, edit_commits] +
				"max_carve_submit_ms=%d max_carve_total_ms=%d "
				% [max_carve_submit_ms, max_carve_total_ms] +
				"max_restore_ms=%d journal_growth_bytes=%d"
				% [max_restore_ms, journal_growth]
			)
			_scene_root.queue_free()
			if FileAccess.file_exists(JOURNAL_PATH):
				DirAccess.remove_absolute(absolute_journal)
			quit(0)
			return
		await process_frame
	_fail("world did not stop after S3a workload audit")
func _audit_fixed_anchor_movement(terrain: Node, viewer: Node3D) -> Dictionary:
	var before: Dictionary = terrain.get_runtime_metrics()
	var max_frame_ms := 0.0
	var last_us := Time.get_ticks_usec()
	var positions: Array[Vector3] = [
		Vector3(16.0, 72.0, 16.0),
		Vector3(112.0, 72.0, 16.0),
		Vector3(112.0, 20.0, 112.0),
		Vector3(16.0, 20.0, 112.0),
		Vector3(64.0, 28.0, 64.0),
	]
	for position in positions:
		viewer.global_position = position
		viewer.emit_signal("position_changed", viewer.global_position)
		await process_frame
		await physics_frame
		var now_us := Time.get_ticks_usec()
		max_frame_ms = maxf(max_frame_ms, float(now_us - last_us) / 1000.0)
		last_us = now_us
		if not ProbeUtil.probe_render_and_collision(terrain, Vector3(position.x, 0.0, position.z)):
			return {"ok": false, "error": "movement probe failed at " + str(position)}
	var after: Dictionary = terrain.get_runtime_metrics()
	if int(after.get("viewer_updates", -1)) != int(before.get("viewer_updates", -2)):
		return {"ok": false, "error": "fixed-anchor movement triggered streaming"}
	if max_frame_ms > MAX_FRAME_MS:
		return {"ok": false, "error": "movement frame exceeded budget"}
	return {"ok": true, "positions": positions.size(), "max_frame_ms": max_frame_ms}
func _measure_cold_phase(terrain: Node, frames: int) -> Dictionary:
	var before: Dictionary = terrain.get_runtime_metrics()
	var max_frame_ms := 0.0
	var last_us := Time.get_ticks_usec()
	for _frame in range(frames):
		await process_frame
		var now_us := Time.get_ticks_usec()
		max_frame_ms = maxf(max_frame_ms, float(now_us - last_us) / 1000.0)
		last_us = now_us
	var after: Dictionary = terrain.get_runtime_metrics()
	for key in ["viewer_updates", "sample_jobs", "mesh_jobs",
			"mesh_completions", "published_events", "edit_commits"]:
		if int(after.get(key, -1)) != int(before.get(key, -2)):
			return {"ok": false, "error": "cold phase changed " + key}
	if int(after.get("queued_render", -1)) != 0 or \
			int(after.get("queued_collision", -1)) != 0 or \
			int(after.get("pending_chunk_retirements", -1)) != 0:
		return {"ok": false, "error": "cold phase left queued work"}
	if max_frame_ms > MAX_FRAME_MS:
		return {"ok": false, "error": "cold frame exceeded budget"}
	return {"ok": true, "max_frame_ms": max_frame_ms}
func _wait_for_world(terrain: Node) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.is_world_running():
			return true
		await process_frame
	return false
func _wait_for_settled_resources(terrain: Node) -> bool:
	var stable_frames := 0
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = terrain.get_runtime_metrics()
		if terrain.get_rendered_chunk_count() >= MIN_RENDER_COLLISION_CHUNKS and \
				terrain.get_collision_chunk_count() >= MIN_RENDER_COLLISION_CHUNKS and \
				int(metrics.get("active_chunk_records", 0)) >= EXPECTED_ACTIVE_CHUNKS and \
				int(metrics.get("queued_render", 0)) == 0 and \
				int(metrics.get("queued_collision", 0)) == 0 and \
				int(metrics.get("fully_ready_chunk_records", -1)) == int(metrics.get("active_chunk_records", 0)) and \
				int(metrics.get("pending_chunk_retirements", 0)) == 0:
			stable_frames += 1
			if stable_frames >= 10:
				return true
		else:
			stable_frames = 0
		await process_frame
	return false
func _wait_for_revision_and_settle(terrain: Node, revision: int) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.get_world_revision() > revision:
			return await _wait_for_settled_resources(terrain)
		await process_frame
	return false
func _file_size(path: String) -> int:
	if not FileAccess.file_exists(path):
		return 0
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return 0
	var length := file.get_length()
	file.close()
	return length
func _fail(message: String) -> void:
	push_error("WT_SANDBOX_S3A_WORKLOAD_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
