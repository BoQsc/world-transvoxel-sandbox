class_name WtSandboxFlyCamera
extends Node3D

signal position_changed(position: Vector3)

@export_range(1.0, 500.0, 1.0) var movement_speed := 24.0
@export_range(1.0, 10.0, 0.1) var fast_multiplier := 4.0
@export_range(0.01, 1.0, 0.01) var mouse_sensitivity := 0.12
@export var input_enabled := true
@export var position_bounds_enabled := true
@export var position_min := Vector3(0.001, 0.001, 0.001)
@export var position_max := Vector3(127.999, 63.999, 127.999)

var _pitch_degrees := -18.0
var _yaw_degrees := 0.0
var _initial_transform := Transform3D.IDENTITY


func _ready() -> void:
	_initial_transform = global_transform
	_yaw_degrees = rotation_degrees.y
	_pitch_degrees = rotation_degrees.x
	input_enabled = input_enabled and \
		not OS.get_cmdline_user_args().has("--disable-player-input")
	set_process(input_enabled)
	set_process_unhandled_input(input_enabled)
	if input_enabled:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	position_changed.emit(global_position)


func _process(delta: float) -> void:
	var movement := Vector3.ZERO
	if Input.is_key_pressed(KEY_W):
		movement -= global_transform.basis.z
	if Input.is_key_pressed(KEY_S):
		movement += global_transform.basis.z
	if Input.is_key_pressed(KEY_A):
		movement -= global_transform.basis.x
	if Input.is_key_pressed(KEY_D):
		movement += global_transform.basis.x
	if Input.is_key_pressed(KEY_Q):
		movement -= Vector3.UP
	if Input.is_key_pressed(KEY_E):
		movement += Vector3.UP
	if movement.is_zero_approx():
		return
	var speed := movement_speed
	if Input.is_key_pressed(KEY_SHIFT):
		speed *= fast_multiplier
	global_position += movement.normalized() * speed * delta
	if position_bounds_enabled:
		global_position = Vector3(
			clampf(global_position.x, position_min.x, position_max.x),
			clampf(global_position.y, position_min.y, position_max.y),
			clampf(global_position.z, position_min.z, position_max.z)
		)
	position_changed.emit(global_position)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and \
			Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_yaw_degrees -= event.relative.x * mouse_sensitivity
		_pitch_degrees = clampf(
			_pitch_degrees - event.relative.y * mouse_sensitivity,
			-89.0,
			89.0
		)
		rotation_degrees = Vector3(_pitch_degrees, _yaw_degrees, 0.0)
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_RIGHT and event.pressed:
			Input.mouse_mode = (
				Input.MOUSE_MODE_VISIBLE
				if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED
				else Input.MOUSE_MODE_CAPTURED
			)
			get_viewport().set_input_as_handled()
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			movement_speed = minf(movement_speed * 1.25, 500.0)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			movement_speed = maxf(movement_speed / 1.25, 1.0)
	elif event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed and event.keycode == KEY_F5:
		reset_view()
		get_viewport().set_input_as_handled()


func get_movement_speed() -> float:
	return movement_speed


func reset_view() -> void:
	global_transform = _initial_transform
	_yaw_degrees = rotation_degrees.y
	_pitch_degrees = rotation_degrees.x
	position_changed.emit(global_position)
