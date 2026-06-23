extends SceneTree

const TIMEOUT_FRAMES := 1800
const JOURNAL_PATH := "res://world/world.wtedit"

var _scene_root: Node
var _samples: Dictionary = {}
var _sample_failures: Dictionary = {}


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
	_scene_root.get_node("Viewer").set("input_enabled", false)
	root.add_child(_scene_root)
	var terrain: Node = _scene_root.get_node("Terrain")
	terrain.authoritative_sample_ready.connect(_on_sample_ready)
	terrain.authoritative_sample_failed.connect(_on_sample_failed)
	if not await _wait_for_world(terrain):
		return _fail("world did not become ready")

	var floor := await _query_sample(terrain, Vector3i(40, 8, 40))
	var cavity := await _query_sample(terrain, Vector3i(40, 18, 40))
	var roof := await _query_sample(terrain, Vector3i(40, 27, 40))
	var sky := await _query_sample(terrain, Vector3i(40, 60, 40))
	if floor == null or cavity == null or roof == null or sky == null:
		return _fail("volumetric column queries failed")
	if floor.get_density() >= 0.0 or cavity.get_density() <= 0.0 or \
			roof.get_density() >= 0.0 or sky.get_density() <= 0.0:
		return _fail("underground column is not solid-void-solid-air")

	var rock_a := await _query_sample(terrain, Vector3i(32, 12, 8))
	var rock_b := await _query_sample(terrain, Vector3i(56, 12, 8))
	if rock_a == null or rock_b == null:
		return _fail("underground material queries failed")
	if rock_a.get_density() >= 0.0 or rock_b.get_density() >= 0.0 or \
			rock_a.get_material() != 5 or rock_b.get_material() != 3:
		return _fail("underground materials are not selected from the XYZ field")

	if not terrain.stop_world():
		return _fail("world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.get_world_state_name() == "stopped":
			print(
				"WT_SANDBOX_VOLUMETRIC_PASS column=solid-void-solid-air "
				+ "geology=xyz materials=5,3"
			)
			_scene_root.queue_free()
			if FileAccess.file_exists(JOURNAL_PATH):
				DirAccess.remove_absolute(absolute_journal)
			quit(0)
			return
		await process_frame
	_fail("world did not stop after volumetric audit")


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


func _on_sample_ready(request_id: int, sample: RefCounted) -> void:
	_samples[request_id] = sample


func _on_sample_failed(request_id: int, error: String) -> void:
	_sample_failures[request_id] = error


func _fail(message: String) -> void:
	push_error("WT_SANDBOX_VOLUMETRIC_FAIL: " + message)
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
