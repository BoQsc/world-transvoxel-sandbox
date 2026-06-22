class_name WtSandboxTerrainLab
extends Node3D

signal lab_status_changed(message: String)

@export_file("*.wtworld") var world_manifest_path := "res://world/world.wtworld"
@export_dir var world_object_root := "res://world"
@export var terrain_path: NodePath
@export var viewer_path: NodePath
@export var camera_path: NodePath
@export_range(1, 1024, 1) var viewer_id := 1
@export_range(0, 16, 1) var radius_chunks := 2
@export_range(0, 20, 1) var maximum_lod := 1
@export_range(0.25, 16.0, 0.25) var mining_radius := 3.0
@export_range(1.0, 32.0, 0.5) var mining_strength := 6.0

@onready var terrain: Node3D = get_node(terrain_path)
@onready var viewer: Node3D = get_node(viewer_path)
@onready var camera: Camera3D = get_node(camera_path)

var _viewer_revision := 0
var _last_viewer_position := Vector3.INF
var _status := "initializing"


func _ready() -> void:
	viewer.connect("position_changed", _on_viewer_position_changed)
	terrain.connect("world_state_changed", _on_world_state_changed)
	terrain.connect("world_failed", _on_world_failed)
	terrain.connect("edit_committed", _on_edit_committed)
	terrain.connect("edit_failed", _on_edit_failed)
	if not FileAccess.file_exists(world_manifest_path):
		_set_status("world missing: run python tools/generate_world.py --force")
		return
	if not terrain.call(
		"start_world", world_manifest_path, world_object_root
	):
		_set_status("startup rejected: " + str(terrain.call("get_world_error")))
		return
	_set_status("starting world")


func _exit_tree() -> void:
	if terrain != null and terrain.call("is_world_running"):
		terrain.call("stop_world")


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventMouseButton or 			event.button_index != MOUSE_BUTTON_LEFT or 			not event.pressed or 			Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		return
	_apply_mining(event.shift_pressed, event.ctrl_pressed)
	get_viewport().set_input_as_handled()


func _on_world_state_changed(_state: int, state_name: String) -> void:
	_set_status("world " + state_name)
	if state_name == "running":
		_submit_viewer(viewer.global_position)


func _on_world_failed(message: String) -> void:
	_set_status("world failed: " + message)


func _on_viewer_position_changed(position: Vector3) -> void:
	if terrain.call("is_world_running"):
		_submit_viewer(position)


func _submit_viewer(position: Vector3) -> void:
	if position.is_equal_approx(_last_viewer_position):
		return
	_viewer_revision += 1
	if terrain.call(
		"update_viewer",
		viewer_id,
		_viewer_revision,
		position,
		radius_chunks,
		maximum_lod
	):
		_last_viewer_position = position
	else:
		_set_status("viewer rejected: " + str(terrain.call("get_world_error")))


func _apply_mining(fill: bool, paint: bool) -> void:
	if not terrain.call("is_world_running"):
		_set_status("mining ignored: world is not running")
		return
	var origin := camera.global_position
	var direction := -camera.global_transform.basis.z
	var query := PhysicsRayQueryParameters3D.create(
		origin, origin + direction * 256.0
	)
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		_set_status("mining ray missed terrain")
		return
	var transaction: Object = terrain.call("begin_edit_transaction", 1)
	if transaction == null:
		_set_status("edit rejected: " + str(terrain.call("get_world_error")))
		return
	var point: Vector3 = hit["position"]
	var command_ok := false
	var operation := "carve"
	if paint:
		operation = "paint ore"
		command_ok = transaction.call(
			"paint_material_sphere", point, mining_radius, 4
		)
	elif fill:
		operation = "fill"
		command_ok = transaction.call(
			"add_density_sphere", point, mining_radius, -mining_strength
		)
	else:
		command_ok = transaction.call(
			"add_density_sphere", point, mining_radius, mining_strength
		)
	if not command_ok or not terrain.call(
		"commit_edit_transaction", transaction
	):
		_set_status("edit failed: " + str(transaction.call("get_error")))
		return
	_set_status(operation + " submitted at " + str(point.round()))


func _on_edit_committed(world_revision: int) -> void:
	_set_status("edit committed; world revision " + str(world_revision))


func _on_edit_failed(message: String) -> void:
	_set_status("edit failed: " + message)


func _set_status(message: String) -> void:
	_status = message
	lab_status_changed.emit(message)
	print("WT_SANDBOX ", message)


func get_status() -> String:
	return _status
