extends SceneTree

const TIMEOUT_FRAMES := 1800
const OBSERVE_FRAMES := 90

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
		return _fail("accepted playtest FPS cap is not 60")
	if _scene_root.radius_chunks != 4:
		return _fail("accepted playtest radius is not full-map LOD0")
	if _scene_root.maximum_lod != 0:
		return _fail("accepted playtest path enabled mixed LOD")
	if _scene_root.streaming_follows_viewer:
		return _fail("accepted playtest path follows the viewer")
	if _scene_root.fixed_streaming_position != Vector3(64.0, 32.0, 64.0):
		return _fail("accepted playtest fixed anchor changed")
	var config: Resource = terrain.get("configuration")
	if config == null or int(config.get("render_apply_budget")) != 1:
		return _fail("render apply budget is not the locked value 1")
	if not await _wait_for_world(terrain):
		return _fail("world did not become ready")
	if not await _wait_for_settled_resources(terrain):
		return _fail("accepted playtest terrain did not settle")
	if not _all_render_chunks_are_lod0(terrain):
		return _fail("accepted playtest path rendered non-LOD0 chunks")
	var baseline: Dictionary = terrain.get_runtime_metrics()
	var baseline_updates := int(baseline.get("viewer_updates", 0))
	var anchor: Vector3 = _scene_root.call("get_streaming_position")
	viewer.global_position += Vector3(24.0, 0.0, 24.0)
	viewer.emit_signal("position_changed", viewer.global_position)
	for _frame in range(OBSERVE_FRAMES):
		await process_frame
	var after: Dictionary = terrain.get_runtime_metrics()
	if int(after.get("viewer_updates", -1)) != baseline_updates:
		return _fail("viewer movement changed the accepted fixed-anchor demand")
	if _scene_root.call("get_streaming_position") != anchor:
		return _fail("viewer movement changed the accepted streaming anchor")
	if int(after.get("pending_chunk_retirements", 0)) != 0:
		return _fail("accepted fixed path produced staged retirements")
	if not terrain.call("stop_world"):
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.call("get_world_state_name") == "stopped":
			print(
				"WT_SANDBOX_S1_DEFAULT_POLICY_PASS "
				+ "mode=fixed_lod0_reference radius=%d max_lod=%d viewer_updates=%d"
				% [_scene_root.radius_chunks, _scene_root.maximum_lod, baseline_updates]
			)
			_scene_root.queue_free()
			quit(0)
			return
		await process_frame
	_fail("world did not stop after S1 default policy audit")


func _wait_for_world(terrain: Node) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.call("is_world_running"):
			return true
		await process_frame
	return false


func _wait_for_settled_resources(terrain: Node) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = terrain.call("get_runtime_metrics")
		if int(metrics.get("active_chunk_records", 0)) >= 256 and \
				int(metrics.get("fully_ready_chunk_records", -1)) == \
				int(metrics.get("active_chunk_records", 0)) and \
				terrain.call("get_rendered_chunk_count") > 0 and \
				terrain.call("get_collision_chunk_count") > 0 and \
				int(metrics.get("queued_render", 0)) == 0 and \
				int(metrics.get("queued_collision", 0)) == 0 and \
				int(metrics.get("mesh_jobs", 0)) == \
				int(metrics.get("mesh_completions", -1)) and \
				int(metrics.get("pending_chunk_retirements", 0)) == 0:
			return true
		await process_frame
	return false


func _all_render_chunks_are_lod0(terrain: Node) -> bool:
	for child in terrain.get_children():
		if child is MeshInstance3D and child.name.begins_with("WT_Render_") and \
				not String(child.name).ends_with("_L0"):
			return false
	return true


func _fail(message: String) -> void:
	push_error("WT_SANDBOX_S1_DEFAULT_POLICY_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
