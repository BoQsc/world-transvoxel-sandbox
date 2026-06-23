class_name WtSandboxTerrainLab
extends Node3D

signal lab_status_changed(message: String)

const WORLD_MIN := Vector3(0.001, 0.001, 0.001)
const WORLD_MAX := Vector3(127.999, 63.999, 127.999)

@export_file("*.wtworld") var world_manifest_path := "res://world/world.wtworld"
@export_dir var world_object_root := "res://world"
@export var terrain_path: NodePath
@export var viewer_path: NodePath
@export var camera_path: NodePath
@export_range(1, 1024, 1) var viewer_id := 1
@export_range(0, 16, 1) var radius_chunks := 2
@export_range(0, 20, 1) var maximum_lod := 1
@export_range(0.0, 32.0, 0.25) var streaming_update_distance := 8.0
@export var streaming_follows_viewer := true
@export var fixed_streaming_position := Vector3(64.0, 32.0, 64.0)
@export_range(0.25, 16.0, 0.25) var mining_radius := 3.0
@export_range(1.0, 32.0, 0.5) var mining_strength := 6.0
@export_range(16.0, 512.0, 1.0) var aim_distance := 256.0

@onready var terrain: Node3D = get_node(terrain_path)
@onready var viewer: Node3D = get_node(viewer_path)
@onready var camera: Camera3D = get_node(camera_path)

var _viewer_revision := 0
var _last_viewer_position := Vector3.INF
var _streaming_position := Vector3.ZERO
var _status := "initializing"
var _aim_status := "waiting for collision"
var _aim_elapsed := 0.0


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


func _physics_process(delta: float) -> void:
	_aim_elapsed += delta
	if _aim_elapsed < 0.1:
		return
	_aim_elapsed = 0.0
	if not terrain.call("is_world_running"):
		_aim_status = "world is not running"
		return
	var hit := _raycast_terrain()
	if hit.is_empty():
		_aim_status = "miss (aim at loaded collision)"
	else:
		var aim_point: Vector3 = hit["position"]
		_aim_status = "hit " + str(aim_point.round())


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventMouseButton or \
			event.button_index != MOUSE_BUTTON_LEFT or \
			not event.pressed or \
			Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		return
	submit_mining_at_aim(event.shift_pressed, event.ctrl_pressed)
	get_viewport().set_input_as_handled()


func _on_world_state_changed(_state: int, state_name: String) -> void:
	_set_status("world " + state_name)
	if state_name == "running":
		_submit_viewer(_streaming_target(viewer.global_position), true)


func _on_world_failed(message: String) -> void:
	_set_status("world failed: " + message)


func _on_viewer_position_changed(position: Vector3) -> void:
	if streaming_follows_viewer and terrain.call("is_world_running"):
		_submit_viewer(position, false)


func _streaming_target(viewer_position: Vector3) -> Vector3:
	return viewer_position if streaming_follows_viewer else fixed_streaming_position


func _submit_viewer(position: Vector3, force: bool = false) -> void:
	var bounded := Vector3(
		clampf(position.x, WORLD_MIN.x, WORLD_MAX.x),
		clampf(position.y, WORLD_MIN.y, WORLD_MAX.y),
		clampf(position.z, WORLD_MIN.z, WORLD_MAX.z)
	)
	var distance := 0.0
	if _last_viewer_position != Vector3.INF:
		distance = bounded.distance_to(_last_viewer_position)
	if not force and _last_viewer_position != Vector3.INF and \
			distance < streaming_update_distance:
		return
	_viewer_revision += 1
	if terrain.call(
		"update_viewer",
		viewer_id,
		_viewer_revision,
		bounded,
		radius_chunks,
		maximum_lod
	):
		_last_viewer_position = bounded
		_streaming_position = bounded
	else:
		_set_status("viewer rejected: " + str(terrain.call("get_world_error")))


func submit_mining_at_aim(fill: bool = false, paint: bool = false) -> bool:
	if not terrain.call("is_world_running"):
		_set_status("mining ignored: world is not running")
		return false
	var hit := _raycast_terrain()
	if hit.is_empty():
		_set_status("mining ray missed terrain")
		return false
	var transaction: Object = terrain.call("begin_edit_transaction", 1)
	if transaction == null:
		_set_status("edit rejected: " + str(terrain.call("get_world_error")))
		return false
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
		return false
	_show_edit_marker(
		point,
		Color(0.95, 0.25, 0.12)
		if operation == "carve"
		else Color(0.20, 0.85, 1.0)
	)
	_set_status(operation + " submitted at " + str(point.round()))
	return true


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


func get_aim_status() -> String:
	return _aim_status


func get_streaming_position() -> Vector3:
	return _streaming_position


func _raycast_terrain() -> Dictionary:
	var origin := camera.global_position
	var direction := -camera.global_transform.basis.z
	var query := PhysicsRayQueryParameters3D.create(
		origin, origin + direction * aim_distance
	)
	return get_world_3d().direct_space_state.intersect_ray(query)


func _show_edit_marker(point: Vector3, color: Color) -> void:
	var marker := MeshInstance3D.new()
	marker.name = "WT_EditMarker"
	var sphere := SphereMesh.new()
	sphere.radius = 0.35
	sphere.height = 0.7
	marker.mesh = sphere
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = color
	material.emission_enabled = true
	material.emission = color
	marker.material_override = material
	marker.position = point
	add_child(marker)
	get_tree().create_timer(0.8).timeout.connect(marker.queue_free)
