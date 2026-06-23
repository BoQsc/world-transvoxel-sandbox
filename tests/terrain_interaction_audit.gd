extends SceneTree

const TIMEOUT_FRAMES := 1800
const JOURNAL_PATH := "res://world/world.wtedit"

var _scene_root: Node
var _samples: Dictionary = {}
var _sample_failures: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var absolute_journal := ProjectSettings.globalize_path(JOURNAL_PATH)
	if FileAccess.file_exists(JOURNAL_PATH):
		DirAccess.remove_absolute(absolute_journal)
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		return _fail("terrain lab scene could not load")
	_scene_root = packed.instantiate()
	_scene_root.get_node("Viewer").set("input_enabled", false)
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	var viewer: Node3D = _scene_root.get_node("Viewer")
	var camera: Camera3D = _scene_root.get_node("Viewer/Camera3D")
	terrain.authoritative_sample_ready.connect(_on_sample_ready)
	terrain.authoritative_sample_failed.connect(_on_sample_failed)
	if not await _wait_for_world(terrain):
		return _fail("world did not become ready")

	viewer.global_position = Vector3(64, 60, 64)
	viewer.look_at(Vector3(64, 28, 64), Vector3.FORWARD)
	viewer.emit_signal("position_changed", viewer.global_position)
	if not await _wait_for_settled_resources(terrain):
		return _fail("terrain resources did not settle")
	await physics_frame
	await physics_frame

	var ray := PhysicsRayQueryParameters3D.create(
		camera.global_position,
		camera.global_position - camera.global_transform.basis.z * 128.0
	)
	var hit: Dictionary = terrain.get_world_3d().direct_space_state.intersect_ray(ray)
	if hit.is_empty():
		return _fail("center-screen mining ray did not hit terrain")
	var sample_point := Vector3i((hit.position as Vector3).round())
	var before := await _query_sample(terrain, sample_point)
	if before == null:
		return _fail("pre-click authoritative sample query failed")
	var density_before: float = before.get_density()
	var revision_before: int = terrain.get_world_revision()
	var mesh_hash_before := _mesh_hash(terrain)

	if not _scene_root.call("submit_mining_at_aim", false, false):
		return _fail("center-screen carve submission was rejected")
	if _scene_root.get_node_or_null("WT_EditMarker") == null:
		return _fail("center-screen carve did not create immediate edit feedback")
	if "submitted" not in str(_scene_root.call("get_status")):
		return _fail("left click did not report a submitted carve")
	if not await _wait_for_edit(terrain, revision_before, mesh_hash_before):
		return _fail("left click did not commit and remesh terrain")

	var after := await _query_sample(terrain, sample_point)
	if after == null:
		return _fail("post-click authoritative sample query failed")
	var density_delta: float = after.get_density() - density_before
	if absf(density_delta - 6.0) > 0.001:
		return _fail(
			"left click carve changed density by %.6f instead of 6.0"
			% density_delta
		)
	if not terrain.stop_world():
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.get_world_state_name() == "stopped":
			print(
				"WT_SANDBOX_INTERACTION_PASS click=carve hit=%s "
				% str((hit.position as Vector3).round())
				+ "density_delta=%.1f remesh=observable feedback=visible"
				% density_delta
			)
			_scene_root.queue_free()
			if FileAccess.file_exists(JOURNAL_PATH):
				DirAccess.remove_absolute(absolute_journal)
			quit(0)
			return
		await process_frame
	_fail("world did not stop after interaction audit")


func _mesh_hash(terrain: Node) -> int:
	var value := 0
	for child in terrain.get_children():
		if child is MeshInstance3D and child.name.begins_with("WT_Render_"):
			var arrays: Array = child.mesh.surface_get_arrays(0)
			value = hash([
				value,
				child.name,
				arrays[Mesh.ARRAY_VERTEX],
				arrays[Mesh.ARRAY_INDEX],
			])
	return value


func _query_sample(terrain: Node, point: Vector3i) -> RefCounted:
	var request_id: int = terrain.request_authoritative_sample(point, 0)
	if request_id <= 0:
		return null
	for _frame in range(TIMEOUT_FRAMES):
		if _samples.has(request_id):
			var sample: RefCounted = _samples[request_id]
			_samples.erase(request_id)
			return sample
		if _sample_failures.has(request_id):
			return null
		await process_frame
	return null


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
			await process_frame
			return true
		await process_frame
	return false


func _wait_for_edit(terrain: Node, revision: int, old_hash: int) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.get_world_revision() > revision and _mesh_hash(terrain) != old_hash:
			return await _wait_for_settled_resources(terrain)
		await process_frame
	return false


func _on_sample_ready(request_id: int, sample: RefCounted) -> void:
	_samples[request_id] = sample


func _on_sample_failed(request_id: int, error: String) -> void:
	_sample_failures[request_id] = error


func _fail(message: String) -> void:
	push_error("WT_SANDBOX_INTERACTION_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
