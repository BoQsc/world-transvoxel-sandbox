class_name WtSandboxTerrainProbeUtil
extends RefCounted


static func probe_render_and_collision(terrain: Node, probe: Vector3) -> bool:
	var origin := Vector3(probe.x, 60.0, probe.z)
	var ray := PhysicsRayQueryParameters3D.create(
		origin, Vector3(probe.x, 0.0, probe.z)
	)
	return not terrain.get_world_3d().direct_space_state.intersect_ray(ray).is_empty() and \
		render_ray_hit(terrain, origin, Vector3.DOWN)


static func render_ray_hit(
		terrain: Node, origin: Vector3, direction: Vector3
) -> bool:
	for child in terrain.get_children():
		if not child is MeshInstance3D or not child.name.begins_with("WT_Render_"):
			continue
		var bounds: AABB = child.global_transform * child.get_aabb()
		if origin.x < bounds.position.x or origin.x > bounds.end.x or \
				origin.z < bounds.position.z or origin.z > bounds.end.z:
			continue
		var arrays: Array = child.mesh.surface_get_arrays(0)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		for triangle in range(0, indices.size(), 3):
			var a: Vector3 = child.global_transform * vertices[indices[triangle]]
			var b: Vector3 = child.global_transform * vertices[indices[triangle + 1]]
			var c: Vector3 = child.global_transform * vertices[indices[triangle + 2]]
			var edge_ab := b - a
			var edge_ac := c - a
			var h := direction.cross(edge_ac)
			var determinant := edge_ab.dot(h)
			if determinant >= -0.000001:
				continue
			var inverse := 1.0 / determinant
			var offset := origin - a
			var u := inverse * offset.dot(h)
			var q := offset.cross(edge_ab)
			var v := inverse * direction.dot(q)
			if u >= 0.0 and v >= 0.0 and u + v <= 1.0 and \
					inverse * edge_ac.dot(q) > 0.0:
				return true
	return false
