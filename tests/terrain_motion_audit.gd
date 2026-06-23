extends SceneTree

const TIMEOUT_FRAMES := 1800
const START_X := 16.25
const END_X := 111.75
const CENTER := 64.25
const STEP_DISTANCE := 0.5

var _scene_root: Node


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		return _fail("terrain lab scene could not load")
	_scene_root = packed.instantiate()
	# Load the finite map before motion so every miss is an LOD/transition swap,
	# not a camera outrunning newly entering world coverage.
	_scene_root.radius_chunks = 3
	_scene_root.maximum_lod = 1
	_scene_root.streaming_update_distance = 0.0
	_scene_root.streaming_follows_viewer = true
	_scene_root.get_node("Viewer").set("input_enabled", false)
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	var viewer: Node3D = _scene_root.get_node("Viewer")
	if not await _wait_for_world(terrain):
		return _fail("world did not become ready")

	viewer.global_position = Vector3(START_X, 56.0, CENTER)
	viewer.emit_signal("position_changed", viewer.global_position)
	if not await _wait_for_settled_resources(terrain):
		return _fail("streaming did not settle before motion")
	await physics_frame
	await physics_frame

	var minimum_rendered: int = terrain.get_rendered_chunk_count()
	var minimum_collision: int = terrain.get_collision_chunk_count()
	var maximum_retiring := 0
	var positions: Array[Vector3] = []
	var segment_steps := int(round((END_X - START_X) / STEP_DISTANCE))
	for step in range(segment_steps + 1):
		positions.append(Vector3(
			START_X + float(step) * STEP_DISTANCE, 56.0, CENTER
		))
	var half_segment_steps := int(round((END_X - CENTER) / STEP_DISTANCE))
	for step in range(half_segment_steps + 1):
		positions.append(Vector3(
			END_X, 56.0, CENTER + float(step) * STEP_DISTANCE
		))
	for step in range(segment_steps + 1):
		positions.append(Vector3(
			END_X - float(step) * STEP_DISTANCE,
			56.0,
			END_X - float(step) * STEP_DISTANCE
		))
	var probe_offsets: Array[Vector3] = [
		Vector3.ZERO,
		Vector3(12.0, 0.0, 0.0),
		Vector3(-12.0, 0.0, 0.0),
		Vector3(0.0, 0.0, 12.0),
		Vector3(0.0, 0.0, -12.0),
	]
	for step in range(positions.size()):
		var position := positions[step]
		viewer.global_position = position
		viewer.emit_signal("position_changed", viewer.global_position)
		await process_frame
		await physics_frame
		var metrics: Dictionary = terrain.get_runtime_metrics()
		maximum_retiring = maxi(
			maximum_retiring,
			int(metrics.get("pending_chunk_retirements", 0))
		)
		minimum_rendered = mini(
			minimum_rendered, terrain.get_rendered_chunk_count()
		)
		minimum_collision = mini(
			minimum_collision, terrain.get_collision_chunk_count()
		)
		if not _render_ray_hit(
			terrain, Vector3(position.x, 60.0, position.z), Vector3.DOWN
		):
			return _fail(
				"render disappeared during motion at step=%d point=(%.2f, %.2f)"
				% [step, position.x, position.z]
			)
		for offset in probe_offsets:
			var probe := position + offset
			var ray := PhysicsRayQueryParameters3D.create(
				Vector3(probe.x, 60.0, probe.z),
				Vector3(probe.x, 0.0, probe.z)
			)
			var hit: Dictionary = (
				terrain.get_world_3d().direct_space_state.intersect_ray(ray)
			)
			if hit.is_empty():
				var render_hit := _render_ray_hit(
					terrain, Vector3(probe.x, 60.0, probe.z), Vector3.DOWN
				)
				var recovery := await _collision_recovery_frames(terrain, probe)
				return _fail(
					"%s disappeared during motion at step=%d point=(%.1f, %.1f) "
					% [
						"collision" if render_hit else "render and collision",
						step,
						probe.x,
						probe.z,
					]
					+ "render=%d collision=%d retiring=%d queued=(%d,%d) recovery=%d"
					% [
						terrain.get_rendered_chunk_count(),
						terrain.get_collision_chunk_count(),
						int(metrics.get("pending_chunk_retirements", 0)),
						int(metrics.get("queued_render", 0)),
						int(metrics.get("queued_collision", 0)),
						recovery,
					]
				)
	if maximum_retiring <= 0:
		return _fail("motion did not exercise staged chunk retirement")
	if not await _wait_for_settled_resources(terrain):
		return _fail("terrain did not release staged chunks after motion stopped")

	if not terrain.stop_world():
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.get_world_state_name() == "stopped":
			print(
				"WT_SANDBOX_MOTION_PASS steps=%d probes=%d min_render=%d min_collision=%d max_retiring=%d"
				% [
					positions.size(),
					positions.size() * 5,
					minimum_rendered,
					minimum_collision,
					maximum_retiring,
				]
			)
			_scene_root.queue_free()
			quit(0)
			return
		await process_frame
	_fail("world did not stop after motion audit")


func _wait_for_world(terrain: Node) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.is_world_running():
			return true
		await process_frame
	return false


func _wait_for_settled_resources(terrain: Node) -> bool:
	var ready_since_ms := -1
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = terrain.get_runtime_metrics()
		var current := Vector2i(
			terrain.get_rendered_chunk_count(),
			terrain.get_collision_chunk_count()
		)
		if current.x > 0 and current.y > 0 and \
				int(metrics.get("queued_render", 0)) == 0 and \
				int(metrics.get("queued_collision", 0)) == 0 and \
				int(metrics.get("mesh_jobs", 0)) == \
				int(metrics.get("mesh_completions", -1)) and \
				int(metrics.get("fully_ready_chunk_records", -1)) == \
				int(metrics.get("active_chunk_records", 0)) and \
				int(metrics.get("pending_chunk_retirements", 0)) == 0:
			if ready_since_ms < 0:
				ready_since_ms = Time.get_ticks_msec()
			elif Time.get_ticks_msec() - ready_since_ms >= 300:
				return true
		else:
			ready_since_ms = -1
		await process_frame
	return false


func _collision_recovery_frames(terrain: Node, probe: Vector3) -> int:
	for frame in range(1, 301):
		await process_frame
		await physics_frame
		var ray := PhysicsRayQueryParameters3D.create(
			Vector3(probe.x, 60.0, probe.z),
			Vector3(probe.x, 0.0, probe.z)
		)
		if not terrain.get_world_3d().direct_space_state.intersect_ray(ray).is_empty():
			return frame
	return -1


func _render_ray_hit(
	terrain: Node, origin: Vector3, direction: Vector3
) -> bool:
	for child in terrain.get_children():
		if not child is MeshInstance3D or \
				not child.name.begins_with("WT_Render_"):
			continue
		var bounds: AABB = child.global_transform * child.get_aabb()
		if origin.x < bounds.position.x or origin.x > bounds.end.x or \
				origin.z < bounds.position.z or origin.z > bounds.end.z:
			continue
		var arrays: Array = child.mesh.surface_get_arrays(0)
		var positions: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		for triangle in range(0, indices.size(), 3):
			var a: Vector3 = child.global_transform * positions[indices[triangle]]
			var b: Vector3 = child.global_transform * positions[indices[triangle + 1]]
			var c: Vector3 = child.global_transform * positions[indices[triangle + 2]]
			var edge_ab := b - a
			var edge_ac := c - a
			var h := direction.cross(edge_ac)
			var determinant := edge_ab.dot(h)
			if determinant >= -0.000001:
				continue
			var inverse := 1.0 / determinant
			var offset := origin - a
			var u := inverse * offset.dot(h)
			if u < 0.0 or u > 1.0:
				continue
			var q := offset.cross(edge_ab)
			var v := inverse * direction.dot(q)
			if v < 0.0 or u + v > 1.0:
				continue
			if inverse * edge_ac.dot(q) > 0.0:
				return true
	return false


func _fail(message: String) -> void:
	push_error("WT_SANDBOX_MOTION_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
