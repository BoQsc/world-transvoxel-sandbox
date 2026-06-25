extends SceneTree

const OUTPUT_ROOT := "res://artifacts/dynamic_lod"
const TIMEOUT_FRAMES := 1800
const VIEWER_ID := 1
const RADIUS_CHUNKS := 3
const MAXIMUM_LOD := 1

var _scene_root: Node
var _last_signature := ""
var _replacement_frames := 0
var _capture_count := 0
var _max_retiring := 0
var _max_queued_render := 0
var _max_queued_collision := 0
var _max_render_delta := 0
var _last_render_count := 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		return _fail("terrain lab scene could not load")
	_scene_root = packed.instantiate()
	_scene_root.radius_chunks = RADIUS_CHUNKS
	_scene_root.maximum_lod = MAXIMUM_LOD
	_scene_root.streaming_update_distance = 0.0
	_scene_root.streaming_follows_viewer = false
	_scene_root.fixed_streaming_position = Vector3(64.0, 32.0, 64.0)
	_scene_root.get_node("Viewer").set("input_enabled", false)
	_scene_root.get_node("Overlay").visible = false
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	var viewer: Node3D = _scene_root.get_node("Viewer")
	var visualizer: Node = _scene_root.get_node("Visualizer")
	viewer.global_position = Vector3(64, 78, 118)
	viewer.look_at(Vector3(64, 28, 64), Vector3.UP)
	visualizer.call("set_debug_mode", 2)
	if not await _wait_for_world(terrain):
		return _fail("world did not start")
	if not await _wait_for_settled_resources(terrain):
		return _fail("initial terrain did not settle")
	_last_signature = _render_signature(terrain)
	_last_render_count = terrain.get_rendered_chunk_count()
	if not await _save_capture("baseline_lod"):
		return
	var anchors: Array[Vector3] = [
		Vector3(24, 56, 64),
		Vector3(40, 56, 64),
		Vector3(56, 56, 64),
		Vector3(72, 56, 64),
		Vector3(88, 56, 64),
		Vector3(104, 56, 64),
	]
	var revision := 1000
	for anchor_index in range(anchors.size()):
		revision += 1
		if not terrain.call(
			"update_viewer",
			VIEWER_ID,
			revision,
			anchors[anchor_index],
			RADIUS_CHUNKS,
			MAXIMUM_LOD
		):
			return _fail("viewer update rejected at anchor " + str(anchor_index))
		if not await _observe_transition(terrain, anchor_index):
			return
	if not await _wait_for_settled_resources(terrain):
		return _fail("terrain did not settle after dynamic LOD capture")
	var classification := "lod_transition_visual_swap_without_geomorph"
	print(
		"WT_SANDBOX_LOD_POP_EVIDENCE_PASS anchors=%d replacement_frames=%d captures=%d max_retiring=%d max_queued_render=%d max_queued_collision=%d max_render_delta=%d classification=%s"
		% [
			anchors.size(),
			_replacement_frames,
			_capture_count,
			_max_retiring,
			_max_queued_render,
			_max_queued_collision,
			_max_render_delta,
			classification,
		]
	)
	if terrain.is_world_running():
		terrain.stop_world()
	_scene_root.queue_free()
	quit(0)


func _observe_transition(terrain: Node, anchor_index: int) -> bool:
	for frame in range(90):
		await process_frame
		await physics_frame
		var metrics: Dictionary = terrain.get_runtime_metrics()
		_max_retiring = maxi(_max_retiring, int(metrics.get("pending_chunk_retirements", 0)))
		_max_queued_render = maxi(_max_queued_render, int(metrics.get("queued_render", 0)))
		_max_queued_collision = maxi(_max_queued_collision, int(metrics.get("queued_collision", 0)))
		if not _probe_render_and_collision(terrain, Vector3(64, 60, 64), Vector3.DOWN):
			return _fail("center render/collision probe failed during dynamic LOD")
		var render_count: int = terrain.get_rendered_chunk_count()
		_max_render_delta = maxi(_max_render_delta, absi(render_count - _last_render_count))
		_last_render_count = render_count
		var signature := _render_signature(terrain)
		if signature != _last_signature:
			_last_signature = signature
			_replacement_frames += 1
			var counts: Dictionary = _lod_counts(terrain)
			print(
				"WT_SANDBOX_LOD_POP_FRAME anchor=%d frame=%d render=%d collision=%d active=%d ready=%d retiring=%d queued_render=%d queued_collision=%d lod0=%d lod1=%d"
				% [
					anchor_index,
					frame,
					render_count,
					terrain.get_collision_chunk_count(),
					int(metrics.get("active_chunk_records", 0)),
					int(metrics.get("fully_ready_chunk_records", 0)),
					int(metrics.get("pending_chunk_retirements", 0)),
					int(metrics.get("queued_render", 0)),
					int(metrics.get("queued_collision", 0)),
					int(counts.get(0, 0)),
					int(counts.get(1, 0)),
				]
			)
			if _capture_count < 12 and not await _save_capture(
				"anchor_%02d_frame_%02d_lod" % [anchor_index, frame]
			):
				return false
		if frame >= 10 and _is_settled(terrain):
			return true
	return _fail("dynamic LOD transition did not settle at anchor " + str(anchor_index))


func _wait_for_world(terrain: Node) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.is_world_running():
			return true
		await process_frame
	return false


func _wait_for_settled_resources(terrain: Node) -> bool:
	var ready_since_ms := -1
	for _frame in range(TIMEOUT_FRAMES):
		if _is_settled(terrain):
			if ready_since_ms < 0:
				ready_since_ms = Time.get_ticks_msec()
			elif Time.get_ticks_msec() - ready_since_ms >= 300:
				return true
		else:
			ready_since_ms = -1
		await process_frame
	return false


func _is_settled(terrain: Node) -> bool:
	var metrics: Dictionary = terrain.get_runtime_metrics()
	return terrain.get_rendered_chunk_count() > 0 and terrain.get_collision_chunk_count() > 0 and \
		int(metrics.get("queued_render", 0)) == 0 and int(metrics.get("queued_collision", 0)) == 0 and \
		int(metrics.get("mesh_jobs", 0)) == int(metrics.get("mesh_completions", -1)) and \
		int(metrics.get("fully_ready_chunk_records", -1)) == int(metrics.get("active_chunk_records", 0)) and \
		int(metrics.get("pending_chunk_retirements", 0)) == 0


func _render_signature(terrain: Node) -> String:
	var names: PackedStringArray = []
	for child in terrain.get_children():
		if child is MeshInstance3D and child.name.begins_with("WT_Render_"):
			names.append(str(child.name))
	names.sort()
	return "|".join(names)


func _lod_counts(terrain: Node) -> Dictionary:
	var counts := {0: 0, 1: 0}
	for child in terrain.get_children():
		if not child is MeshInstance3D or not child.name.begins_with("WT_Render_"):
			continue
		if child.name.ends_with("_L0"):
			counts[0] += 1
		elif child.name.ends_with("_L1"):
			counts[1] += 1
	return counts


func _save_capture(name: String) -> bool:
	await RenderingServer.frame_post_draw
	var image := root.get_viewport().get_texture().get_image()
	if image == null or image.is_empty():
		return _fail("viewport capture was empty: " + name)
	var absolute_root := ProjectSettings.globalize_path(OUTPUT_ROOT)
	DirAccess.make_dir_recursive_absolute(absolute_root)
	var output := absolute_root.path_join(name + ".png")
	if image.save_png(output) != OK:
		return _fail("could not save dynamic LOD capture: " + output)
	_capture_count += 1
	return true


func _probe_render_and_collision(terrain: Node, origin: Vector3, direction: Vector3) -> bool:
	var ray := PhysicsRayQueryParameters3D.create(origin, origin + direction * 96.0)
	var collision_hit: Dictionary = terrain.get_world_3d().direct_space_state.intersect_ray(ray)
	return not collision_hit.is_empty() and _render_ray_hit(terrain, origin, direction)


func _render_ray_hit(terrain: Node, origin: Vector3, direction: Vector3) -> bool:
	for child in terrain.get_children():
		if not child is MeshInstance3D or not child.name.begins_with("WT_Render_"):
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
			var q := offset.cross(edge_ab)
			var v := inverse * direction.dot(q)
			if u >= 0.0 and v >= 0.0 and u + v <= 1.0 and inverse * edge_ac.dot(q) > 0.0:
				return true
	return false


func _fail(message: String) -> bool:
	push_error("WT_SANDBOX_LOD_POP_CAPTURE_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
	return false
