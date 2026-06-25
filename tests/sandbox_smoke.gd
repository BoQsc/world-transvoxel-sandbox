extends SceneTree

const TIMEOUT_MS := 45000

var _scene_root: Node


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		_fail("terrain lab scene could not load")
		return
	_scene_root = packed.instantiate()
	_scene_root.get_node("Viewer").set("input_enabled", false)
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	var started := Time.get_ticks_msec()
	while not terrain.call("is_world_running"):
		if Time.get_ticks_msec() - started > TIMEOUT_MS:
			_fail("world did not reach running: " + str(terrain.call("get_world_error")))
			return
		await process_frame
	if terrain.call("get_addon_version") != "1.0.5":
		_fail("unexpected addon version")
		return
	if terrain.call("get_world_page_count") != 288:
		_fail("unexpected sandbox page count")
		return
	while true:
		var metrics: Dictionary = terrain.call("get_runtime_metrics")
		if terrain.call("get_rendered_chunk_count") > 0 and \
				terrain.call("get_collision_chunk_count") > 0 and \
				int(metrics.get("mesh_jobs", 0)) == \
				int(metrics.get("mesh_completions", -1)) and \
				int(metrics.get("fully_ready_chunk_records", -1)) == \
				int(metrics.get("active_chunk_records", 0)) and \
				int(metrics.get("pending_chunk_retirements", 0)) == 0:
			break
		if Time.get_ticks_msec() - started > TIMEOUT_MS:
			_fail("render/collision resources did not become ready")
			return
		await process_frame

	var found_material := false
	for child in terrain.get_children():
		if child is MeshInstance3D and child.name.begins_with("WT_Render_"):
			found_material = child.material_override != null
			if found_material:
				break
	if not found_material:
		_fail("sandbox material was not applied to streamed terrain")
		return

	var initial_revision: int = terrain.call("get_world_revision")
	var transaction: Object = terrain.call("begin_edit_transaction", 9)
	if transaction == null or not transaction.call(
		"add_density_box",
		Vector3(62, 28, 62),
		Vector3(66, 34, 66),
		8.0
	) or not terrain.call("commit_edit_transaction", transaction):
		_fail("interactive edit contract failed")
		return
	while terrain.call("get_world_revision") <= initial_revision:
		if Time.get_ticks_msec() - started > TIMEOUT_MS:
			_fail("edit did not commit")
			return
		await process_frame

	if not terrain.call("stop_world"):
		_fail("world stop was rejected")
		return
	while terrain.call("get_world_state_name") != "stopped":
		if Time.get_ticks_msec() - started > TIMEOUT_MS:
			_fail("world did not stop")
			return
		await process_frame
	print(
		"WT_SANDBOX_SMOKE_PASS pages=288 render=1 collision=1 "
		+ "material=1 edit=1 shutdown=clean"
	)
	_scene_root.queue_free()
	quit(0)


func _fail(message: String) -> void:
	push_error("WT_SANDBOX_SMOKE_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
