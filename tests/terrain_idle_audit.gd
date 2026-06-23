extends SceneTree

const TIMEOUT_FRAMES := 1800
const IDLE_FRAMES := 120

var _scene_root: Node


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		return _fail("terrain lab scene could not load")
	_scene_root = packed.instantiate()
	_scene_root.get_node("Viewer").set("input_enabled", false)
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	var viewer: Node3D = _scene_root.get_node("Viewer")
	if int(ProjectSettings.get_setting("application/run/max_fps", 0)) != 60:
		return _fail("interactive frame rate is not capped at 60 FPS")
	if _scene_root.maximum_lod != 0:
		return _fail("interactive reference scene is not LOD0-only")
	if _scene_root.streaming_follows_viewer:
		return _fail("interactive reference scene does not use a fixed anchor")
	if _scene_root.radius_chunks != 4:
		return _fail("interactive reference scene does not load the full map")
	if not is_equal_approx(_scene_root.streaming_update_distance, 8.0):
		return _fail("interactive streaming update distance is not 8")
	if not await _wait_for_world(terrain):
		return _fail("world did not become ready")
	if not await _wait_for_settled_resources(terrain):
		return _fail("initial terrain did not settle")

	var baseline: Dictionary = terrain.get_runtime_metrics()
	var anchor: Vector3 = _scene_root.get_streaming_position()
	if not await _wait_without_runtime_work(terrain, baseline):
		return _fail("settled terrain continued doing runtime work")

	viewer.global_position += Vector3(1.0, 0.0, 0.0)
	viewer.emit_signal("position_changed", viewer.global_position)
	for _frame in range(30):
		await process_frame
	var below_threshold: Dictionary = terrain.get_runtime_metrics()
	if int(below_threshold.get("viewer_updates", -1)) != \
			int(baseline.get("viewer_updates", -2)):
		return _fail("sub-threshold movement triggered a viewer replan")
	if _scene_root.get_streaming_position() != anchor:
		return _fail("viewer movement changed the fixed streaming anchor")

	_scene_root.streaming_follows_viewer = true
	viewer.global_position += Vector3(8.0, 0.0, 0.0)
	viewer.emit_signal("position_changed", viewer.global_position)
	if not await _wait_for_viewer_update(terrain, baseline):
		return _fail("threshold movement did not trigger one viewer update")
	if not await _wait_for_settled_resources(terrain):
		return _fail("terrain did not settle after threshold movement")
	var moved: Dictionary = terrain.get_runtime_metrics()
	if not await _wait_without_runtime_work(terrain, moved):
		return _fail("terrain continued doing work after movement settled")

	if not terrain.stop_world():
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.get_world_state_name() == "stopped":
			print(
				"WT_SANDBOX_IDLE_PASS fps_cap=60 max_lod=0 full_map=1 "
				+ "update_distance=8 idle_frames=%d viewer_updates=%d"
				% [IDLE_FRAMES * 2, int(moved.get("viewer_updates", 0))]
			)
			_scene_root.queue_free()
			quit(0)
			return
		await process_frame
	_fail("world did not stop after idle audit")


func _wait_for_world(terrain: Node) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.is_world_running():
			return true
		await process_frame
	return false


func _wait_for_settled_resources(terrain: Node) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = terrain.get_runtime_metrics()
		if terrain.get_rendered_chunk_count() > 0 and \
				terrain.get_collision_chunk_count() > 0 and \
				int(metrics.get("queued_render", 0)) == 0 and \
				int(metrics.get("queued_collision", 0)) == 0 and \
				int(metrics.get("mesh_jobs", 0)) == \
				int(metrics.get("mesh_completions", -1)) and \
				int(metrics.get("fully_ready_chunk_records", -1)) == \
				int(metrics.get("active_chunk_records", 0)) and \
				int(metrics.get("pending_chunk_retirements", 0)) == 0:
			return true
		await process_frame
	return false


func _wait_for_viewer_update(terrain: Node, baseline: Dictionary) -> bool:
	var expected := int(baseline.get("viewer_updates", 0)) + 1
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = terrain.get_runtime_metrics()
		if int(metrics.get("viewer_updates", 0)) >= expected:
			return true
		await process_frame
	return false


func _wait_without_runtime_work(
	terrain: Node, baseline: Dictionary
) -> bool:
	for _frame in range(IDLE_FRAMES):
		await process_frame
	var after: Dictionary = terrain.get_runtime_metrics()
	for name in [
		"viewer_updates",
		"sample_jobs",
		"mesh_jobs",
		"mesh_completions",
		"published_events",
	]:
		if int(after.get(name, -1)) != int(baseline.get(name, -2)):
			return false
	return int(after.get("queued_render", -1)) == 0 and \
		int(after.get("queued_collision", -1)) == 0 and \
		int(after.get("pending_chunk_retirements", -1)) == 0


func _fail(message: String) -> void:
	push_error("WT_SANDBOX_IDLE_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
