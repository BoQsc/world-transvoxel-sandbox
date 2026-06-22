extends SceneTree

const TIMEOUT_FRAMES := 1800
const QUANTIZATION := 10000.0

var _scene_root: Node


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		return _fail("terrain lab scene could not load")
	_scene_root = packed.instantiate()
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	var viewer: Node3D = _scene_root.get_node("Viewer")
	if not await _wait_for_world(terrain):
		return _fail("world did not start")
	viewer.global_position = Vector3(64, 56, 64)
	viewer.emit_signal("position_changed", viewer.global_position)
	if not await _wait_for_complete_lod_set(terrain):
		return _fail("complete mixed-LOD set did not become ready")

	var edge_counts: Dictionary = {}
	var edge_sources: Dictionary = {}
	var normal_records: Dictionary = {}
	var boundary_material_counts: Dictionary = {}
	var boundary_material_ranges: Dictionary = {}
	var triangles := 0
	var chunks := 0
	for child in terrain.get_children():
		if not child is MeshInstance3D or not child.name.begins_with("WT_Render_"):
			continue
		chunks += 1
		var arrays: Array = child.mesh.surface_get_arrays(0)
		var positions: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		var materials: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV2]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		for vertex in range(positions.size()):
			var world_position: Vector3 = child.global_transform * positions[vertex]
			_record_normal(
				normal_records,
				world_position,
				(child.global_transform.basis * normals[vertex]).normalized(),
				child.name
			)
			if absf(world_position.x - 0.5) < 0.001:
				var material_id := roundi(materials[vertex].x)
				boundary_material_counts[material_id] = int(
					boundary_material_counts.get(material_id, 0)) + 1
				var material_range: Vector2 = boundary_material_ranges.get(
					material_id, Vector2(world_position.y, world_position.y))
				boundary_material_ranges[material_id] = Vector2(
					minf(material_range.x, world_position.y),
					maxf(material_range.y, world_position.y))
		for triangle in range(0, indices.size(), 3):
			var a: Vector3 = child.global_transform * positions[indices[triangle]]
			var b: Vector3 = child.global_transform * positions[indices[triangle + 1]]
			var c: Vector3 = child.global_transform * positions[indices[triangle + 2]]
			_increment_edge(edge_counts, edge_sources, a, b, child.name)
			_increment_edge(edge_counts, edge_sources, b, c, child.name)
			_increment_edge(edge_counts, edge_sources, c, a, child.name)
			triangles += 1

	var invalid := 0
	var examples: Array[String] = []
	for edge in edge_counts:
		if edge_counts[edge] != 2:
			invalid += 1
			if examples.size() < 8:
				examples.append(
					str(edge) + "=" + str(edge_counts[edge])
					+ "@" + str(edge_sources[edge])
				)
	if triangles <= 0 or invalid != 0:
		return _fail(
			"mixed-LOD surface is open or non-manifold: triangles=%d "
			% triangles
			+ "edges=%d invalid=%d examples=%s"
			% [edge_counts.size(), invalid, str(examples)]
		)
	var worst_normal_dot := 1.0
	var mismatched_normals := 0
	var worst_normal_example := ""
	for point in normal_records:
		var records: Array = normal_records[point]
		for left in range(records.size()):
			for right in range(left + 1, records.size()):
				if records[left].source == records[right].source:
					continue
				var normal_dot: float = records[left].normal.dot(records[right].normal)
				if normal_dot < 0.999:
					mismatched_normals += 1
				if normal_dot < worst_normal_dot:
					worst_normal_dot = normal_dot
					worst_normal_example = (
						str(point) + "@" + records[left].source
						+ "," + records[right].source
					)
	print(
		"WT_SANDBOX_SEAM_PASS chunks=%d triangles=%d edges=%d invalid=0 "
		% [chunks, triangles, edge_counts.size()]
		+ "normal_mismatches=%d worst_normal_dot=%.6f example=%s"
		% [mismatched_normals, worst_normal_dot, worst_normal_example]
		+ " boundary_materials=%s ranges=%s"
		% [boundary_material_counts, boundary_material_ranges]
	)
	if terrain.is_world_running():
		terrain.stop_world()
	_scene_root.queue_free()
	quit(0)


func _increment_edge(
	counts: Dictionary,
	sources: Dictionary,
	a: Vector3,
	b: Vector3,
	source: String
) -> void:
	var first := _point_key(a)
	var second := _point_key(b)
	var key := first + "|" + second if first < second else second + "|" + first
	counts[key] = int(counts.get(key, 0)) + 1
	sources[key] = str(sources.get(key, "")) + ("," if sources.has(key) else "") + source


func _record_normal(
	records: Dictionary,
	point: Vector3,
	normal: Vector3,
	source: String
) -> void:
	var key := _point_key(point)
	if not records.has(key):
		records[key] = []
	records[key].append({"normal": normal, "source": source})


func _point_key(point: Vector3) -> String:
	return "%d,%d,%d" % [
		roundi(point.x * QUANTIZATION),
		roundi(point.y * QUANTIZATION),
		roundi(point.z * QUANTIZATION),
	]


func _wait_for_world(terrain: Node) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.is_world_running():
			return true
		await process_frame
	return false


func _wait_for_complete_lod_set(terrain: Node) -> bool:
	var stable_frames := 0
	var previous := Vector2i(-1, -1)
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = terrain.get_runtime_metrics()
		var counts := Vector2i(
			terrain.get_rendered_chunk_count(),
			int(metrics.get("transition_mesh_completions", 0))
		)
		if int(metrics.get("active_chunk_records", 0)) == 88 and \
				counts.x > 0 and counts.y >= 16 and \
				int(metrics.get("queued_render", 0)) == 0:
			stable_frames = stable_frames + 1 if counts == previous else 0
			if stable_frames >= 60:
				return true
		else:
			stable_frames = 0
		previous = counts
		await process_frame
	return false


func _fail(message: String) -> void:
	push_error("WT_SANDBOX_SEAM_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
