extends SceneTree
const ProbeUtil = preload("res://tests/terrain_probe_util.gd")
const WORLD_ROOT := "res://artifacts/scale_ladder/L4/world"
const WORLD_PATH := WORLD_ROOT + "/world.wtworld"
const JOURNAL_PATH := WORLD_ROOT + "/world.wtedit"
const OUTPUT_ROOT := "res://artifacts/s3_visual_gpu"
const TIMEOUT_FRAMES := 3600
const ACTIVE_CHUNK_CAPACITY := 1024
const RENDER_APPLY_BUDGET := 1
const PREFETCH_DISTANCE := 64.0
const MIN_RENDER_COLLISION := 160
var _scene_root: Node
var _terrain: Node
var _viewer: Node3D
var _visualizer: Node
var _last_us := 0
var _max_frame_ms := 0.0
var _prefetch_revision := 0
var _capture_count := 0
var _min_render := 999999
var _min_collision := 999999
var _max_active := 0

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	if not FileAccess.file_exists(WORLD_PATH):
		return _fail("L4 world missing; run python tools/scale_ladder.py --level L4 --force")
	_remove_journal()
	if not _setup_scene():
		return
	_last_us = Time.get_ticks_usec()
	if not await _wait_for_world():
		return _fail("world did not become ready")
	_last_us = Time.get_ticks_usec()
	_max_frame_ms = 0.0
	if not await _phase_static_and_movement():
		return
	var rapid := await _phase_rapid_turns()
	if not bool(rapid["ok"]):
		return _fail(str(rapid["error"]))
	if not await _phase_underground_and_edit():
		return
	if _max_frame_ms > 250.0:
		return _fail("graphical frame interval exceeded S3 budget: %.3f ms" % _max_frame_ms)
	if not _terrain.stop_world():
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if _terrain.get_world_state_name() == "stopped":
			print("WT_SANDBOX_S3_VISUAL_GPU_PASS images=%d max_frame_ms=%.3f min_render=%d min_collision=%d max_active=%d rapid_turns=%d viewer_updates_delta=%d planned_demands_delta=%d" % [_capture_count, _max_frame_ms, _min_render, _min_collision, _max_active, int(rapid["turns"]), int(rapid["viewer_updates_delta"]), int(rapid["planned_demands_delta"])])
			_scene_root.queue_free()
			_remove_journal()
			quit(0)
			return
		await process_frame
		_track_frame()
	_fail("world did not stop after S3 visual/GPU audit")

func _setup_scene() -> bool:
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		_fail("terrain lab scene could not load")
		return false
	_scene_root = packed.instantiate()
	_scene_root.world_manifest_path = WORLD_PATH
	_scene_root.world_object_root = WORLD_ROOT
	_scene_root.world_max = Vector3(2047.999, 63.999, 2047.999)
	_scene_root.radius_chunks = 3
	_scene_root.maximum_lod = 1
	_scene_root.streaming_update_distance = 0.0
	_scene_root.streaming_follows_viewer = true
	_terrain = _scene_root.get_node("Terrain")
	var config: Resource = _terrain.get("configuration").duplicate(true)
	config.set("active_chunk_capacity", ACTIVE_CHUNK_CAPACITY)
	config.set("render_apply_budget", RENDER_APPLY_BUDGET)
	_terrain.set("configuration", config)
	_viewer = _scene_root.get_node("Viewer")
	_viewer.set("input_enabled", false)
	_scene_root.get_node("Overlay").visible = false
	_visualizer = _scene_root.get_node("Visualizer")
	_visualizer.world_bounds_extent = Vector3(2048, 64, 2048)
	root.add_child(_scene_root)
	return true

func _phase_static_and_movement() -> bool:
	if not await _move_and_capture("stable_overview", Vector3(1024, 76, 1776), Vector3(1024, 30, 1024), true):
		return false
	_visualizer.call("set_debug_mode", 1)
	await process_frame
	if not await _capture("stable_material"):
		return false
	_visualizer.call("set_debug_mode", 0)
	var positions: Array[Vector3] = [Vector3(768, 56, 768), Vector3(896, 56, 896), Vector3(1024, 56, 1024), Vector3(1152, 56, 1152)]
	for index in range(positions.size()):
		var position := positions[index]
		if not await _move_and_capture("normal_%02d" % index, position, position + Vector3(0, -24, 96), true):
			return false
	return true

func _phase_rapid_turns() -> Dictionary:
	_move_viewer(Vector3(1024, 56, 1024), Vector3(1024, 20, 1100))
	if not await _wait_for_settled_resources(20000):
		return {"ok": false, "error": "rapid-turn start did not settle"}
	var before: Dictionary = _terrain.get_runtime_metrics()
	var targets: Array[Vector3] = [Vector3(1024, 20, 1220), Vector3(1220, 20, 1024), Vector3(1024, 20, 828), Vector3(828, 20, 1024)]
	for index in range(targets.size()):
		_viewer.look_at(targets[index], Vector3.UP)
		await process_frame
		await process_frame
		_track_frame()
		if not await _capture("rapid_turn_%02d" % index):
			return {"ok": false, "error": "rapid-turn capture failed"}
	var after: Dictionary = _terrain.get_runtime_metrics()
	var viewer_delta := int(after.get("viewer_updates", 0)) - int(before.get("viewer_updates", 0))
	var demand_delta := int(after.get("planned_demands", 0)) - int(before.get("planned_demands", 0))
	return {"ok": viewer_delta == 0 and demand_delta == 0, "turns": targets.size(), "viewer_updates_delta": viewer_delta, "planned_demands_delta": demand_delta, "error": "rapid turns changed terrain demand"}

func _phase_underground_and_edit() -> bool:
	if not await _move_and_capture("underground_tunnel", Vector3(992, 17, 1395), Vector3(1024, 13, 1392), false):
		return false
	var edit_point := Vector3(1200, 16, 1200)
	if not await _move_and_capture("pre_edit", Vector3(1200, 56, 1200), Vector3(1200, 20, 1296), true):
		return false
	var revision_before: int = _terrain.get_world_revision()
	var transaction: Object = _terrain.begin_edit_transaction(603)
	if transaction == null or not transaction.add_density_sphere(edit_point, 3.0, 6.0) or not _terrain.commit_edit_transaction(transaction):
		return _fail_bool("visual mining edit was rejected")
	if not await _wait_for_revision_and_settle(revision_before):
		return _fail_bool("visual mining edit did not settle")
	return await _capture("post_edit")

func _move_and_capture(name: String, position: Vector3, target: Vector3, probe: bool) -> bool:
	_move_viewer(position, target)
	if not await _wait_for_settled_resources(20000):
		return _fail_bool("view did not settle: " + name)
	if probe and not ProbeUtil.probe_render_and_collision(_terrain, Vector3(position.x, 0, position.z)):
		return _fail_bool("render/collision probe failed: " + name)
	return await _capture(name)

func _move_viewer(position: Vector3, target: Vector3) -> void:
	_viewer.global_position = position
	_viewer.look_at(target, Vector3.UP)
	_viewer.emit_signal("position_changed", _viewer.global_position)
	var ahead := position + (target - position).normalized() * PREFETCH_DISTANCE
	ahead = Vector3(clampf(ahead.x, 0.001, 2047.999), clampf(ahead.y, 0.001, 63.999), clampf(ahead.z, 0.001, 2047.999))
	_prefetch_revision += 1
	if not _terrain.update_viewer(603, _prefetch_revision, ahead, 1, 1):
		_fail("forward prefetch viewer rejected")

func _capture(name: String) -> bool:
	var metrics: Dictionary = _terrain.get_runtime_metrics()
	var render_count: int = _terrain.get_rendered_chunk_count()
	var collision_count: int = _terrain.get_collision_chunk_count()
	_min_render = mini(_min_render, render_count)
	_min_collision = mini(_min_collision, collision_count)
	_max_active = maxi(_max_active, int(metrics.get("active_chunk_records", 0)))
	if render_count < MIN_RENDER_COLLISION or collision_count < MIN_RENDER_COLLISION:
		return _fail_bool("low render/collision coverage before capture: " + name)
	for key in ["queued_render", "queued_collision", "pending_chunk_retirements", "render_fading_resources"]:
		if int(metrics.get(key, 0)) != 0:
			return _fail_bool("unsettled " + key + " before capture: " + name)
	await RenderingServer.frame_post_draw
	var image := root.get_viewport().get_texture().get_image()
	if image == null or image.is_empty():
		return _fail_bool("viewport capture was empty: " + name)
	var visual_range := _image_luminance_range(image)
	if visual_range < 0.05:
		return _fail_bool("viewport capture lacks visual range: " + name)
	var absolute_root := ProjectSettings.globalize_path(OUTPUT_ROOT)
	DirAccess.make_dir_recursive_absolute(absolute_root)
	var output := absolute_root.path_join(name + ".png")
	if image.save_png(output) != OK:
		return _fail_bool("could not save S3 visual/GPU capture: " + output)
	_capture_count += 1
	_last_us = Time.get_ticks_usec()
	print("WT_SANDBOX_S3_VISUAL_CAPTURE image=%s size=%dx%d range=%.3f" % [name, image.get_width(), image.get_height(), visual_range])
	return true

func _image_luminance_range(image: Image) -> float:
	var minimum := 1.0
	var maximum := 0.0
	for y_step in range(1, 8):
		for x_step in range(2, 11):
			var pixel := image.get_pixel(x_step * image.get_width() / 12, y_step * image.get_height() / 8)
			var luminance := (pixel.r + pixel.g + pixel.b) / 3.0
			minimum = minf(minimum, luminance)
			maximum = maxf(maximum, luminance)
	return maximum - minimum

func _wait_for_world() -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if _terrain.is_world_running():
			return true
		await process_frame
		_track_frame()
	return false

func _wait_for_revision_and_settle(revision: int) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if _terrain.get_world_revision() > revision:
			return await _wait_for_settled_resources(20000)
		await process_frame
		_track_frame()
	return false

func _wait_for_settled_resources(max_ms: int) -> bool:
	var started := Time.get_ticks_msec()
	var ready_since := -1
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = _terrain.get_runtime_metrics()
		var ready: bool = _terrain.get_rendered_chunk_count() >= MIN_RENDER_COLLISION and _terrain.get_collision_chunk_count() >= MIN_RENDER_COLLISION and int(metrics.get("queued_render", 0)) == 0 and int(metrics.get("queued_collision", 0)) == 0 and int(metrics.get("mesh_jobs", 0)) == int(metrics.get("mesh_completions", -1)) and int(metrics.get("fully_ready_chunk_records", -1)) == int(metrics.get("active_chunk_records", 0)) and int(metrics.get("pending_chunk_retirements", 0)) == 0 and int(metrics.get("render_fading_resources", 0)) == 0 and int(metrics.get("active_chunk_records", 0)) <= ACTIVE_CHUNK_CAPACITY
		if ready:
			if ready_since < 0:
				ready_since = Time.get_ticks_msec()
			elif Time.get_ticks_msec() - ready_since >= 300:
				return true
		else:
			ready_since = -1
		if Time.get_ticks_msec() - started > max_ms:
			return false
		await process_frame
		_track_frame()
	return false

func _track_frame() -> void:
	var now_us := Time.get_ticks_usec()
	if _last_us > 0:
		_max_frame_ms = maxf(_max_frame_ms, float(now_us - _last_us) / 1000.0)
	_last_us = now_us

func _remove_journal() -> void:
	if FileAccess.file_exists(JOURNAL_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(JOURNAL_PATH))

func _fail_bool(message: String) -> bool:
	_fail(message)
	return false

func _fail(message: String) -> void:
	push_error("WT_SANDBOX_S3_VISUAL_GPU_FAIL: " + message)
	if _terrain != null:
		print("WT_SANDBOX_S3_VISUAL_GPU_METRICS " + str(_terrain.get_runtime_metrics()))
	if _scene_root != null:
		_scene_root.queue_free()
	_remove_journal()
	quit(1)
