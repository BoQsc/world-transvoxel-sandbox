extends SceneTree

const WORLD_ROOT := "res://artifacts/scale_ladder/L3/world"
const WORLD_PATH := WORLD_ROOT + "/world.wtworld"
const OUTPUT_ROOT := "res://artifacts/scale_ladder/L3/visual"
const TIMEOUT_FRAMES := 2400
const ACTIVE_CHUNK_CAPACITY := 1024

var _scene_root: Node


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	if not FileAccess.file_exists(WORLD_PATH):
		return _fail("L3 world missing; run python tools/scale_ladder.py --level L3 --force")
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		return _fail("terrain lab scene could not load")
	_scene_root = packed.instantiate()
	_scene_root.world_manifest_path = WORLD_PATH
	_scene_root.world_object_root = WORLD_ROOT
	_scene_root.world_max = Vector3(1023.999, 63.999, 1023.999)
	_scene_root.radius_chunks = 3
	_scene_root.maximum_lod = 1
	_scene_root.streaming_update_distance = 0.0
	_scene_root.streaming_follows_viewer = true
	_scene_root.get_node("Visualizer").world_bounds_extent = Vector3(1024, 64, 1024)
	var terrain: Node = _scene_root.get_node("Terrain")
	var config: Resource = terrain.get("configuration").duplicate(true)
	config.set("active_chunk_capacity", ACTIVE_CHUNK_CAPACITY)
	terrain.set("configuration", config)
	_scene_root.get_node("Viewer").set("input_enabled", false)
	root.add_child(_scene_root)
	var viewer: Node3D = _scene_root.get_node("Viewer")
	var sun: DirectionalLight3D = _scene_root.get_node("Sun")
	var visualizer: Node = _scene_root.get_node("Visualizer")
	if not await _wait_for_world(terrain):
		return _fail("L3 world did not start for visual capture")

	if not await _view(viewer, terrain, Vector3(512, 76, 888), Vector3(512, 30, 512)):
		return
	if not await _capture("overview_surface"):
		return
	visualizer.call("set_debug_mode", 1)
	await process_frame
	if not await _capture("overview_material"):
		return
	visualizer.call("set_debug_mode", 2)
	await process_frame
	if not await _capture("overview_lod"):
		return
	visualizer.call("set_debug_mode", 0)

	if not await _view(viewer, terrain, Vector3(512, 96, 512), Vector3(512, 24, 512), Vector3.FORWARD):
		return
	sun.shadow_enabled = false
	await process_frame
	if not await _capture("top_unshadowed"):
		return
	sun.shadow_enabled = true

	if not await _view(viewer, terrain, Vector3(480, 17, 699), Vector3(512, 13, 696)):
		return
	var tunnel_light := OmniLight3D.new()
	tunnel_light.light_energy = 20.0
	tunnel_light.omni_range = 22.0
	viewer.add_child(tunnel_light)
	tunnel_light.position = Vector3(2, 3, -3)
	await process_frame
	if not await _capture("underground_tunnel"):
		return
	tunnel_light.queue_free()

	sun.shadow_enabled = false
	await process_frame
	if not await _view(viewer, terrain, Vector3(-24, 38, 512), Vector3(18, 28, 512)):
		return
	var boundary_query := PhysicsRayQueryParameters3D.create(
		Vector3(-24, 12, 546), Vector3(12, 12, 546)
	)
	var boundary_hit: Dictionary = terrain.get_world_3d().direct_space_state.intersect_ray(boundary_query)
	if boundary_hit.is_empty() or absf(float(boundary_hit["position"].x) - 0.5) > 0.01:
		return _fail("L3 targeted finite boundary collision ray failed: " + str(boundary_hit))
	print("WT_SANDBOX_L3_BOUNDARY_PASS hit_x=%.3f" % float(boundary_hit["position"].x))
	for _frame in range(120):
		await process_frame
	if not await _capture("closed_boundary"):
		return
	visualizer.call("set_debug_mode", 1)
	await process_frame
	if not await _capture("closed_boundary_material"):
		return
	print("WT_SANDBOX_L3_VISUAL_CAPTURE_PASS images=7 active_capacity=%d" % ACTIVE_CHUNK_CAPACITY)
	if terrain.is_world_running():
		terrain.stop_world()
	_scene_root.queue_free()
	quit(0)


func _view(
	viewer: Node3D, terrain: Node, position: Vector3, target: Vector3,
	up: Vector3 = Vector3.UP
) -> bool:
	viewer.global_position = position
	viewer.look_at(target, up)
	viewer.emit_signal("position_changed", viewer.global_position)
	return await _wait_for_settled_resources(terrain)


func _capture(name: String) -> bool:
	await RenderingServer.frame_post_draw
	var image := root.get_viewport().get_texture().get_image()
	if image == null or image.is_empty():
		_fail("viewport capture was empty: " + name)
		return false
	var minimum := 1.0
	var maximum := 0.0
	for y_step in range(1, 8):
		for x_step in range(5, 12):
			var pixel := image.get_pixel(
				x_step * image.get_width() / 12,
				y_step * image.get_height() / 8
			)
			var luminance := (pixel.r + pixel.g + pixel.b) / 3.0
			minimum = minf(minimum, luminance)
			maximum = maxf(maximum, luminance)
	var visual_range := maximum - minimum
	if visual_range < 0.05:
		_fail("viewport capture lacks visual range: " + name)
		return false
	var absolute_root := ProjectSettings.globalize_path(OUTPUT_ROOT)
	DirAccess.make_dir_recursive_absolute(absolute_root)
	var output := absolute_root.path_join(name + ".png")
	if image.save_png(output) != OK:
		_fail("could not save visual capture: " + output)
		return false
	print(
		"WT_SANDBOX_L3_CAPTURE image=%s size=%dx%d range=%.3f"
		% [name, image.get_width(), image.get_height(), visual_range]
	)
	return true


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
		if terrain.get_rendered_chunk_count() > 0 and terrain.get_collision_chunk_count() > 0 and \
				int(metrics.get("queued_render", 0)) == 0 and int(metrics.get("queued_collision", 0)) == 0 and \
				int(metrics.get("mesh_jobs", 0)) == int(metrics.get("mesh_completions", -1)) and \
				int(metrics.get("fully_ready_chunk_records", -1)) == int(metrics.get("active_chunk_records", 0)) and \
				int(metrics.get("pending_chunk_retirements", 0)) == 0:
			if ready_since_ms < 0:
				ready_since_ms = Time.get_ticks_msec()
			elif Time.get_ticks_msec() - ready_since_ms >= 500:
				return true
		else:
			ready_since_ms = -1
		await process_frame
	return false


func _fail(message: String) -> void:
	push_error("WT_SANDBOX_L3_VISUAL_CAPTURE_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
