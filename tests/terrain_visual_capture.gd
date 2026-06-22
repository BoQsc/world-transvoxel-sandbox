extends SceneTree

const OUTPUT_ROOT := "res://artifacts/visual"
const TIMEOUT_FRAMES := 1800

var _scene_root: Node


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var journal := "res://world/world.wtedit"
	if FileAccess.file_exists(journal):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(journal))
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		return _fail("terrain lab scene could not load")
	_scene_root = packed.instantiate()
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	var viewer: Node3D = _scene_root.get_node("Viewer")
	var camera: Camera3D = _scene_root.get_node("Viewer/Camera3D")
	var sun: DirectionalLight3D = _scene_root.get_node("Sun")
	var material: ShaderMaterial = _scene_root.get_node(
		"Visualizer"
	).terrain_material
	if not await _wait_for_world(terrain):
		return _fail("world did not start for visual capture")

	viewer.global_position = Vector3(64, 72, 112)
	viewer.look_at(Vector3(64, 30, 64), Vector3.UP)
	viewer.emit_signal("position_changed", viewer.global_position)
	if not await _wait_for_settled_resources(terrain):
		return _fail("overview resources did not settle")
	if not await _capture("overview_surface"):
		return
	material.set_shader_parameter("debug_mode", 1)
	await process_frame
	await process_frame
	if not await _capture("overview_material"):
		return
	material.set_shader_parameter("debug_mode", 2)
	await process_frame
	await process_frame
	if not await _capture("overview_lod"):
		return

	material.set_shader_parameter("debug_mode", 0)
	viewer.global_position = Vector3(64, 118, 64)
	viewer.look_at(Vector3(64, 24, 64), Vector3.FORWARD)
	viewer.emit_signal("position_changed", viewer.global_position)
	if not await _wait_for_settled_resources(terrain):
		return _fail("top-view resources did not settle")
	if not await _capture("top_surface"):
		return
	sun.shadow_enabled = false
	await process_frame
	await process_frame
	if not await _capture("top_unshadowed"):
		return
	sun.shadow_enabled = true
	material.set_shader_parameter("debug_mode", 2)
	await process_frame
	await process_frame
	if not await _capture("top_lod"):
		return
	material.set_shader_parameter("debug_mode", 0)

	viewer.global_position = Vector3(-18, 38, 64)
	viewer.look_at(Vector3(12, 28, 64), Vector3.UP)
	# Keep the complete center-loaded set. Moving streaming demand outside the
	# finite map intentionally exposes partial demand boundaries and is not a
	# valid closed-world inspection.
	for _frame in range(180):
		await process_frame
	var probe_results: Array[String] = []
	for screen_y in range(430, 671, 40):
		var probe_origin := camera.project_ray_origin(Vector2(660, screen_y))
		var probe_direction := camera.project_ray_normal(Vector2(660, screen_y))
		var probe := PhysicsRayQueryParameters3D.create(
			probe_origin, probe_origin + probe_direction * 256.0
		)
		var probe_hit: Dictionary = terrain.get_world_3d().direct_space_state.intersect_ray(probe)
		var render_hit := _render_ray_hit(terrain, probe_origin, probe_direction)
		if probe_hit.is_empty() or render_hit.is_empty() or (
				(probe_hit.position as Vector3).distance_to(render_hit.position) > 0.001):
			return _fail("boundary render/collision rays disagree at y=" + str(screen_y))
		probe_results.append(
			"%d:c=%s/r=%s/m=%s" % [screen_y,
				probe_hit.get("position", "miss"),
				render_hit.get("position", "miss"),
				render_hit.get("material", "none")]
		)
	print("WT_SANDBOX_BOUNDARY_PROBE camera=%s rays=%s" % [
		camera.global_position, probe_results])
	if not await _capture("closed_boundary"):
		return
	material.set_shader_parameter("debug_mode", 1)
	await process_frame
	await process_frame
	if not await _capture("closed_boundary_material"):
		return
	print("WT_SANDBOX_VISUAL_CAPTURE_PASS images=8")
	if terrain.is_world_running():
		terrain.stop_world()
	_scene_root.queue_free()
	quit(0)


func _capture(name: String) -> bool:
	await RenderingServer.frame_post_draw
	var image := root.get_viewport().get_texture().get_image()
	if image == null or image.is_empty():
		_fail("viewport capture was empty: " + name)
		return false
	var minimum := 1.0
	var maximum := 0.0
	for y_step in range(1, 8):
		for x_step in range(1, 12):
			var pixel := image.get_pixel(
				x_step * image.get_width() / 12,
				y_step * image.get_height() / 8
			)
			var luminance := (pixel.r + pixel.g + pixel.b) / 3.0
			minimum = minf(minimum, luminance)
			maximum = maxf(maximum, luminance)
	if maximum - minimum < 0.05:
		_fail("viewport capture lacks visual range: " + name)
		return false
	var absolute_root := ProjectSettings.globalize_path(OUTPUT_ROOT)
	DirAccess.make_dir_recursive_absolute(absolute_root)
	var output := absolute_root.path_join(name + ".png")
	if image.save_png(output) != OK:
		_fail("could not save visual capture: " + output)
		return false
	print(
		"WT_SANDBOX_CAPTURE image=%s size=%dx%d range=%.3f"
		% [name, image.get_width(), image.get_height(), maximum - minimum]
	)
	return true


func _wait_for_world(terrain: Node) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.is_world_running():
			return true
		await process_frame
	return false


func _wait_for_settled_resources(terrain: Node) -> bool:
	var stable_frames := 0
	var previous := Vector2i(-1, -1)
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = terrain.get_runtime_metrics()
		var current := Vector2i(
			terrain.get_rendered_chunk_count(),
			int(metrics.get("mesh_completions", 0))
		)
		if current.x > 0 and terrain.get_collision_chunk_count() > 0 and \
				int(metrics.get("queued_render", 0)) == 0 and \
				int(metrics.get("queued_collision", 0)) == 0:
			stable_frames = stable_frames + 1 if current == previous else 0
			if stable_frames >= 180:
				return true
		else:
			stable_frames = 0
		previous = current
		await process_frame
	return false


func _render_ray_hit(terrain: Node, origin: Vector3, direction: Vector3) -> Dictionary:
	var best := {"distance": INF}
	for child in terrain.get_children():
		if not child is MeshInstance3D or not child.name.begins_with("WT_Render_"):
			continue
		var arrays: Array = child.mesh.surface_get_arrays(0)
		var positions: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var materials: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV2]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		for triangle in range(0, indices.size(), 3):
			var ia: int = indices[triangle]
			var ib: int = indices[triangle + 1]
			var ic: int = indices[triangle + 2]
			var a: Vector3 = child.global_transform * positions[ia]
			var b: Vector3 = child.global_transform * positions[ib]
			var c: Vector3 = child.global_transform * positions[ic]
			var edge_ab := b - a
			var edge_ac := c - a
			var h := direction.cross(edge_ac)
			var determinant := edge_ab.dot(h)
			if absf(determinant) < 0.000001:
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
			var distance := inverse * edge_ac.dot(q)
			if distance <= 0.0 or distance >= float(best.distance):
				continue
			var material_id := (
				materials[ia].x * (1.0 - u - v)
				+ materials[ib].x * u + materials[ic].x * v
			)
			best = {"distance": distance, "position": origin + direction * distance,
				"material": material_id, "chunk": child.name}
	return {} if is_inf(float(best.distance)) else best


func _fail(message: String) -> void:
	push_error("WT_SANDBOX_VISUAL_CAPTURE_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
