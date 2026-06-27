extends SceneTree

const BaseSampler = preload("res://scripts/terrain_base_sampler.gd")
const SculptController = preload("res://scripts/terrain_sculpt_controller.gd")
const WORLD_ROOT := "res://artifacts/scale_ladder/L4/world"
const WORLD_PATH := WORLD_ROOT + "/world.wtworld"
const JOURNAL_PATH := WORLD_ROOT + "/world.wtedit"
const TIMEOUT_FRAMES := 3600
const ACTIVE_CHUNK_CAPACITY := 1024
const RENDER_APPLY_BUDGET := 1
const EDIT_CENTER := Vector3(1200.0, 16.0, 1200.0)
const EDIT_RADIUS := 2.0
const EDIT_STRENGTH := 6.0
const DENSITY_EPSILON := 0.002
var _scene_root: Node
var _terrain: Node
var _samples: Dictionary = {}
var _sample_failures: Dictionary = {}
var _controller := SculptController.new()

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	if not FileAccess.file_exists(WORLD_PATH):
		return _fail("L4 world missing; run python tools/scale_ladder.py --level L4 --force")
	_remove_journal()
	var packed := load("res://scenes/terrain_lab.tscn") as PackedScene
	if packed == null:
		return _fail("terrain lab scene could not load")
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
	_scene_root.get_node("Viewer").set("input_enabled", false)
	root.add_child(_scene_root)
	_wire_controller()
	if not await _wait_for_world():
		return _fail("world did not become ready")
	_submit_viewer(EDIT_CENTER + Vector3(0.0, 40.0, 0.0))
	if not await _wait_for_settled_resources():
		return _fail("initial restore_to_base window did not settle")
	var points := BaseSampler.sphere_grid_points(EDIT_CENTER, EDIT_RADIUS)
	if points.is_empty():
		return _fail("restore_to_base point set is empty")
	var before := await _query_samples(points)
	if before.size() != points.size():
		return _fail("pre-edit sample query failed")
	if not _samples_match_base(before):
		return _fail("unmodified terrain does not match deterministic base")
	var revision_before: int = _terrain.get_world_revision()
	var journal_before := _file_size(JOURNAL_PATH)
	var carve_started := Time.get_ticks_msec()
	var carve: Dictionary = await _controller.submit(EDIT_CENTER, SculptController.MODE_CARVE)
	if not bool(carve.get("ok", false)):
		return _fail(str(carve["status"]))
	if not await _wait_for_revision_and_settle(revision_before):
		return _fail("carve did not settle")
	var carve_ms := Time.get_ticks_msec() - carve_started
	revision_before = _terrain.get_world_revision()
	var restore_started := Time.get_ticks_msec()
	var restore: Dictionary = _controller.restore_last_carve_to_base()
	if not bool(restore.get("ok", false)):
		return _fail(str(restore["status"]))
	if not await _wait_for_revision_and_settle(revision_before):
		return _fail("restore_to_base did not settle")
	var restore_ms := Time.get_ticks_msec() - restore_started
	var restored := await _query_samples(points)
	if restored.size() != points.size() or not _samples_match_base(restored):
		return _fail("restored samples do not match deterministic base")
	var journal_growth := _file_size(JOURNAL_PATH) - journal_before
	if not _terrain.stop_world():
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if _terrain.get_world_state_name() == "stopped":
			print(
				"WT_SANDBOX_S3_RESTORE_TO_BASE_PASS points=%d carve_ms=%d "
				% [points.size(), carve_ms] +
				"restore_ms=%d journal_growth_bytes=%d active_capacity=%d"
				% [restore_ms, journal_growth, ACTIVE_CHUNK_CAPACITY]
			)
			_scene_root.queue_free()
			_remove_journal()
			quit(0)
			return
		await process_frame
	_fail("world did not stop after restore_to_base audit")

func _wire_controller() -> void:
	_terrain.authoritative_samples_ready.connect(_on_sample_ready)
	_terrain.authoritative_samples_failed.connect(_on_sample_failed)
	_controller.configure(_terrain, EDIT_RADIUS, EDIT_STRENGTH, 3, 4, 2048, 64)
	_terrain.edit_committed.connect(func(_revision: int): _controller.edit_committed())
	_terrain.edit_failed.connect(func(_message: String): _controller.edit_failed())

func _submit_viewer(position: Vector3) -> void:
	if not _terrain.update_viewer(1, 1, position, 3, 1):
		_fail("viewer update rejected")

func _samples_match_base(samples: Array) -> bool:
	for sample: RefCounted in samples:
		var point: Vector3i = sample.get_grid_point()
		var base: Dictionary = BaseSampler.l4_sample(point)
		if absf(float(sample.get_density()) - float(base["density"])) > DENSITY_EPSILON:
			return false
		if int(sample.get_material()) != int(base["material"]):
			return false
	return true

func _query_samples(points: Array[Vector3i]) -> Array:
	var request_id: int = _terrain.request_authoritative_samples(points, 0)
	if request_id <= 0:
		return []
	for _frame in range(TIMEOUT_FRAMES):
		if _samples.has(request_id):
			var samples: Array = _samples[request_id]
			_samples.erase(request_id)
			return samples
		if _sample_failures.has(request_id):
			return []
		await process_frame
	return []

func _wait_for_world() -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if _terrain.is_world_running():
			return true
		await process_frame
	return false

func _wait_for_revision_and_settle(revision: int) -> bool:
	for _frame in range(TIMEOUT_FRAMES):
		if _terrain.get_world_revision() > revision:
			return await _wait_for_settled_resources()
		await process_frame
	return false

func _wait_for_settled_resources() -> bool:
	var ready_since := -1
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = _terrain.get_runtime_metrics()
		var ready: bool = _terrain.get_rendered_chunk_count() > 0 and _terrain.get_collision_chunk_count() > 0 and \
			int(metrics.get("queued_render", 0)) == 0 and int(metrics.get("queued_collision", 0)) == 0 and \
			int(metrics.get("mesh_jobs", 0)) == int(metrics.get("mesh_completions", -1)) and \
			int(metrics.get("fully_ready_chunk_records", -1)) == int(metrics.get("active_chunk_records", 0)) and \
			int(metrics.get("pending_chunk_retirements", 0)) == 0
		if ready:
			if ready_since < 0:
				ready_since = Time.get_ticks_msec()
			elif Time.get_ticks_msec() - ready_since >= 300:
				return true
		else:
			ready_since = -1
		await process_frame
	return false

func _file_size(path: String) -> int:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return 0
	var length := file.get_length(); file.close()
	return length

func _remove_journal() -> void:
	if FileAccess.file_exists(JOURNAL_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(JOURNAL_PATH))

func _on_sample_ready(request_id: int, samples: Array) -> void:
	_samples[request_id] = samples

func _on_sample_failed(request_id: int, error: String) -> void:
	_sample_failures[request_id] = error

func _fail(message: String) -> void:
	push_error("WT_SANDBOX_S3_RESTORE_TO_BASE_FAIL: " + message)
	if _terrain != null:
		print("WT_SANDBOX_S3_RESTORE_TO_BASE_METRICS " + str(_terrain.get_runtime_metrics()))
	if _scene_root != null:
		_scene_root.queue_free()
	_remove_journal()
	quit(1)
