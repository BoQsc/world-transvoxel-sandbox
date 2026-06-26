extends SceneTree

const TIMEOUT_FRAMES := 1800
const JOURNAL_PATH := "res://world/world.wtedit"
const SAMPLE_POINT := Vector3i(64, 31, 64)

var _scene_root: Node
var _samples: Dictionary = {}
var _sample_failures: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var absolute_journal := ProjectSettings.globalize_path(JOURNAL_PATH)
	if FileAccess.file_exists(JOURNAL_PATH):
		DirAccess.remove_absolute(absolute_journal)
	var first := await _start_scene()
	if first.is_empty():
		return
	var terrain: Node = first["terrain"]
	var density_before := await _query_density(terrain, SAMPLE_POINT)
	var mesh_before := _mesh_hash(terrain)
	var revision_before: int = terrain.get_world_revision()
	var transaction: Object = terrain.begin_edit_transaction(9)
	if transaction == null or not transaction.add_density_box(
		Vector3(62, 28, 62), Vector3(66, 34, 66), 8.0
	) or not terrain.commit_edit_transaction(transaction):
		return _fail("persistent edit transaction was rejected")
	if not await _wait_for_edit(terrain, revision_before, mesh_before):
		return _fail("persistent edit did not commit and remesh")
	var density_after := await _query_density(terrain, SAMPLE_POINT)
	if is_nan(density_after) or density_after <= density_before + 0.5:
		return _fail(
			"persistent edit did not materially change density: before=%.6f after=%.6f"
			% [density_before, density_after]
		)
	var mesh_after := _mesh_hash(terrain)
	if mesh_after == mesh_before:
		return _fail("persistent edit did not change the rendered mesh")
	if not FileAccess.file_exists(JOURNAL_PATH):
		return _fail("persistent edit did not create an edit journal")
	var journal_size := FileAccess.get_file_as_bytes(JOURNAL_PATH).size()
	if journal_size <= 0:
		return _fail("persistent edit journal is empty")
	if not await _stop_scene(terrain):
		return

	var second := await _start_scene()
	if second.is_empty():
		return
	var restarted_terrain: Node = second["terrain"]
	var density_restart := await _query_density(restarted_terrain, SAMPLE_POINT)
	var mesh_restart := _mesh_hash(restarted_terrain)
	if absf(density_restart - density_after) > 0.001:
		return _fail(
			"restart density mismatch: after=%.6f restart=%.6f"
			% [density_after, density_restart]
		)
	if mesh_restart != mesh_after:
		return _fail("restart mesh did not match the edited mesh")
	if not await _stop_scene(restarted_terrain):
		return
	if FileAccess.file_exists(JOURNAL_PATH):
		DirAccess.remove_absolute(absolute_journal)
	print(
		"WT_SANDBOX_S1_LOD0_PERSISTENCE_PASS "
		+ "density_delta=%.3f journal_bytes=%d restart=exact mesh=stable"
		% [density_after - density_before, journal_size]
	)
	quit(0)


func _start_scene() -> Dictionary:
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		_fail("terrain lab scene could not load")
		return {}
	_scene_root = packed.instantiate()
	_scene_root.get_node("Viewer").set("input_enabled", false)
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	terrain.authoritative_sample_ready.connect(_on_sample_ready)
	terrain.authoritative_sample_failed.connect(_on_sample_failed)
	if not await _wait_for_world(terrain):
		_fail("world did not become ready")
		return {}
	if not await _wait_for_settled_resources(terrain):
		_fail("terrain resources did not settle")
		return {}
	return {"terrain": terrain}


func _stop_scene(terrain: Node) -> bool:
	if not terrain.stop_world():
		_fail("world stop was rejected")
		return false
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.get_world_state_name() == "stopped":
			_scene_root.queue_free()
			_scene_root = null
			await process_frame
			return true
		await process_frame
	_fail("world did not stop")
	return false


func _query_density(terrain: Node, point: Vector3i) -> float:
	var request_id: int = terrain.request_authoritative_sample(point, 0)
	if request_id <= 0:
		return NAN
	for _frame in range(TIMEOUT_FRAMES):
		if _samples.has(request_id):
			var sample: RefCounted = _samples[request_id]
			_samples.erase(request_id)
			return sample.get_density()
		if _sample_failures.has(request_id):
			return NAN
		await process_frame
	return NAN


func _mesh_hash(terrain: Node) -> int:
	var records: Array = []
	var value := 0
	for child in terrain.get_children():
		if child is MeshInstance3D and child.name.begins_with("WT_Render_"):
			if str(child.name).contains("_retiring_"):
				continue
			var arrays: Array = child.mesh.surface_get_arrays(0)
			records.append([
				str(child.name),
				hash([arrays[Mesh.ARRAY_VERTEX], arrays[Mesh.ARRAY_INDEX]]),
			])
	records.sort()
	for record in records:
		value = hash([value, record])
	return value


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
				int(metrics.get("pending_chunk_retirements", 0)) == 0 and \
				int(metrics.get("render_fading_resources", 0)) == 0:
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
	push_error("WT_SANDBOX_S1_LOD0_PERSISTENCE_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	var absolute_journal := ProjectSettings.globalize_path(JOURNAL_PATH)
	if FileAccess.file_exists(JOURNAL_PATH):
		DirAccess.remove_absolute(absolute_journal)
	quit(1)
