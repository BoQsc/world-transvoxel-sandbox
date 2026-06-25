extends SceneTree

const OUTPUT_ROOT := "res://artifacts/dynamic_lod_temporal"
const TIMEOUT_FRAMES := 1800
const CAPTURE_FRAMES := 90
const VIEWER_ID := 1
const RADIUS_CHUNKS := 3
const MAXIMUM_LOD := 1

var _scene_root: Node
var _max_render_fading := 0
var _fade_frames := 0
var _max_render_delta := 0
var _last_render_count := 0
var _captured_frames := 0


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
	_scene_root.get_node("Visualizer").call("set_debug_mode", 0)
	viewer.global_position = Vector3(64, 78, 118)
	viewer.look_at(Vector3(64, 28, 64), Vector3.UP)
	if not await _wait_for_world(terrain):
		return _fail("world did not start")
	if not await _wait_for_settled_resources(terrain):
		return _fail("initial terrain did not settle")
	_last_render_count = terrain.get_rendered_chunk_count()
	var anchors: Array[Vector3] = [
		Vector3(24, 56, 64),
		Vector3(40, 56, 64),
		Vector3(56, 56, 64),
		Vector3(72, 56, 64),
		Vector3(88, 56, 64),
		Vector3(104, 56, 64),
	]
	for anchor_index in range(anchors.size()):
		if not terrain.call(
			"update_viewer",
			VIEWER_ID,
			1001 + anchor_index,
			anchors[anchor_index],
			RADIUS_CHUNKS,
			MAXIMUM_LOD
		):
			return _fail("viewer update rejected at anchor " + str(anchor_index))
		if not await _capture_anchor(terrain, anchor_index):
			return
	if _max_render_fading <= 0:
		return _fail("temporal capture did not observe native render fade")
	print(
		"WT_SANDBOX_LOD_TEMPORAL_CAPTURE_PASS anchors=%d frames=%d max_render_delta=%d max_render_fading=%d fade_frames=%d classification=%s"
		% [
			anchors.size(),
			_captured_frames,
			_max_render_delta,
			_max_render_fading,
			_fade_frames,
			"temporal_surface_pending_human_review",
		]
	)
	if terrain.is_world_running():
		terrain.stop_world()
	_scene_root.queue_free()
	quit(0)


func _capture_anchor(terrain: Node, anchor_index: int) -> bool:
	for frame in range(CAPTURE_FRAMES):
		await process_frame
		await physics_frame
		var metrics: Dictionary = terrain.get_runtime_metrics()
		var render_fading := int(metrics.get("render_fading_resources", 0))
		var render_count: int = terrain.get_rendered_chunk_count()
		_max_render_fading = maxi(_max_render_fading, render_fading)
		_max_render_delta = maxi(_max_render_delta, absi(render_count - _last_render_count))
		_last_render_count = render_count
		if render_fading > 0:
			_fade_frames += 1
		if not await _save_capture("anchor_%02d_frame_%03d" % [anchor_index, frame]):
			return false
		_captured_frames += 1
		print(
			"WT_SANDBOX_LOD_TEMPORAL_FRAME anchor=%d frame=%d render=%d collision=%d render_fading=%d queued_render=%d queued_collision=%d"
			% [
				anchor_index,
				frame,
				render_count,
				terrain.get_collision_chunk_count(),
				render_fading,
				int(metrics.get("queued_render", 0)),
				int(metrics.get("queued_collision", 0)),
			]
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


func _save_capture(name: String) -> bool:
	await RenderingServer.frame_post_draw
	var image := root.get_viewport().get_texture().get_image()
	if image == null or image.is_empty():
		return _fail("viewport capture was empty: " + name)
	var absolute_root := ProjectSettings.globalize_path(OUTPUT_ROOT)
	DirAccess.make_dir_recursive_absolute(absolute_root)
	var output := absolute_root.path_join(name + ".png")
	if image.save_png(output) != OK:
		return _fail("could not save temporal capture: " + output)
	return true


func _fail(message: String) -> bool:
	push_error("WT_SANDBOX_LOD_TEMPORAL_CAPTURE_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
	return false
