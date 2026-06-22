extends SceneTree

const TIMEOUT_FRAMES := 1800
const JOURNAL_PATH := "res://world/world.wtedit"
var _scene_root: Node
var _samples: Dictionary = {}
var _sample_failures: Dictionary = {}
var _committed_revisions: Array[int] = []

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
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	var viewer: Node3D = _scene_root.get_node("Viewer")
	terrain.authoritative_sample_ready.connect(_on_sample_ready)
	terrain.authoritative_sample_failed.connect(_on_sample_failed)
	terrain.edit_committed.connect(_on_edit_committed)
	if not await _wait_for_world(terrain):
		return _fail("world did not become ready")

	viewer.global_position = Vector3(64, 56, 64)
	viewer.emit_signal("position_changed", viewer.global_position)
	if not await _wait_for_settled_resources(terrain):
		return _fail("streaming did not settle at the audit position")
	var settled_metrics: Dictionary = terrain.get_runtime_metrics()
	print(
		"WT_SANDBOX_GEOMETRY_STATE active=%d render=%d collision=%d transitions=%d"
		% [
			int(settled_metrics.get("active_chunk_records", 0)),
			int(settled_metrics.get("render_resources", 0)),
			int(settled_metrics.get("collision_resources", 0)),
			int(settled_metrics.get("transition_mesh_completions", 0)),
		]
	)

	var audit := _audit_geometry(terrain)
	if not audit.error.is_empty():
		return _fail(audit.error)
	await physics_frame
	await physics_frame
	var ray := PhysicsRayQueryParameters3D.create(
		Vector3(64, 60, 64),
		Vector3(64, 0, 64)
	)
	var hit: Dictionary = terrain.get_world_3d().direct_space_state.intersect_ray(ray)
	if hit.is_empty():
		return _fail("outside ray missed terrain collision")
	var hit_point: Vector3 = hit.position
	if hit_point.y < 24.0 or hit_point.y > 34.0:
		return _fail("terrain collision height is inconsistent: " + str(hit_point))

	var below := await _query_sample(terrain, Vector3i(64, 20, 64))
	var above := await _query_sample(terrain, Vector3i(64, 60, 64))
	var boundary := await _query_sample(terrain, Vector3i(0, 20, 64))
	var boundary_inner := await _query_sample(terrain, Vector3i(2, 20, 64))
	if below == null or above == null or boundary == null or boundary_inner == null:
		return _fail("authoritative density queries failed")
	if below.get_density() >= 0.0 or above.get_density() <= 0.0:
		return _fail("terrain density sign does not place solid below empty")
	if boundary.get_density() <= 0.0 or boundary_inner.get_density() >= 0.0:
		return _fail("finite map boundary is not closed from empty to solid")

	var edit_point := Vector3i(64, 28, 64)
	var before := await _query_sample(terrain, edit_point)
	if before == null:
		return _fail("pre-edit sample query failed")
	var mesh_hash_before := _mesh_hash(terrain)
	var revision_before: int = terrain.get_world_revision()
	var transaction: Object = terrain.begin_edit_transaction(77)
	if transaction == null or not transaction.add_density_sphere(
		Vector3(edit_point), 3.0, 6.0
	) or not terrain.commit_edit_transaction(transaction):
		return _fail("geometry audit edit submission failed")
	if not await _wait_for_edit(terrain, revision_before, mesh_hash_before):
		return _fail("edit committed without an observable remesh")
	var after := await _query_sample(terrain, edit_point)
	if after == null or absf(
		after.get_density() - before.get_density() - 6.0
	) > 0.001:
		return _fail("edit did not change authoritative density by the requested value")

	if not terrain.stop_world():
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.get_world_state_name() == "stopped":
			print(
				"WT_SANDBOX_GEOMETRY_PASS triangles=%d upward=%d "
				% [audit.triangles, audit.upward]
				+ "lod0=%d lod1=%d max_alignment=%.6f "
				% [audit.lod0, audit.lod1, audit.max_alignment]
				+ "collision=front edit=observable boundary=closed"
			)
			_scene_root.queue_free()
			if FileAccess.file_exists(JOURNAL_PATH):
				DirAccess.remove_absolute(absolute_journal)
			quit(0)
			return
		await process_frame
	_fail("world did not stop after geometry audit")


func _audit_geometry(terrain: Node) -> Dictionary:
	var result := {"error": "", "triangles": 0, "upward": 0, "lod0": 0,
		"lod1": 0, "max_alignment": -1.0}
	for child in terrain.get_children():
		if not child is MeshInstance3D or not child.name.begins_with("WT_Render_"):
			continue
		result.lod0 += int(child.name.ends_with("_L0"))
		result.lod1 += int(child.name.ends_with("_L1"))
		var arrays: Array = child.mesh.surface_get_arrays(0)
		var positions: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		if positions.size() != normals.size() or indices.size() % 3 != 0:
			result.error = "render array shape mismatch in " + child.name
			return result
		for normal in normals:
			if not normal.is_finite() or normal.length_squared() < 0.5:
				result.error = "invalid terrain normal in " + child.name
				return result
		for triangle in range(0, indices.size(), 3):
			var a := positions[indices[triangle]]
			var b := positions[indices[triangle + 1]]
			var c := positions[indices[triangle + 2]]
			var outward := (
				normals[indices[triangle]]
				+ normals[indices[triangle + 1]]
				+ normals[indices[triangle + 2]]
			)
			var geometric := (b - a).cross(c - a)
			if not a.is_finite() or geometric.length_squared() <= 0.0:
				result.error = "non-finite or degenerate terrain triangle"
				return result
			var alignment := geometric.normalized().dot(outward.normalized())
			result.max_alignment = maxf(result.max_alignment, alignment)
			if alignment >= 0.01:
				result.error = (
					"terrain triangle is not clockwise/outward for Godot: "
					+ child.name + " triangle=" + str(triangle / 3)
					+ " alignment=" + str(alignment)
					+ " vertices=" + str([a, b, c]) + " normals=" + str([
						normals[indices[triangle]], normals[indices[triangle + 1]], normals[indices[triangle + 2]]])
				)
				return result
			result.triangles += 1
			result.upward += int(outward.normalized().y > 0.5)
	if result.triangles <= 0 or result.upward <= 0:
		result.error = "terrain audit found no upward-facing exterior surface"
	elif result.lod0 <= 0 or result.lod1 <= 0:
		result.error = (
			"terrain audit did not cover both LOD0 and LOD1: "
			+ str([result.lod0, result.lod1])
		)
	return result


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
		var counts := Vector2i(
			terrain.get_rendered_chunk_count(),
			terrain.get_collision_chunk_count()
		)
		if counts.x > 0 and counts.y > 0 and \
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
		if terrain.get_world_revision() > revision and \
				not _committed_revisions.is_empty() and \
				_mesh_hash(terrain) != old_hash:
			return await _wait_for_settled_resources(terrain)
		await process_frame
	return false


func _on_sample_ready(request_id: int, sample: RefCounted) -> void:
	_samples[request_id] = sample


func _on_sample_failed(request_id: int, error: String) -> void:
	_sample_failures[request_id] = error


func _on_edit_committed(revision: int) -> void:
	_committed_revisions.append(revision)


func _fail(message: String) -> void:
	push_error("WT_SANDBOX_GEOMETRY_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
