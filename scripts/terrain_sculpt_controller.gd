class_name WtSandboxTerrainSculptController
extends RefCounted

const Capture = preload("res://scripts/terrain_sculpt_capture.gd")
const MODE_CARVE := "carve"
const MODE_CONSTRUCT := "construct rock"
const MODE_PAINT := "paint ore"
const MODE_RESTORE := "restore carve"

var _terrain: Node
var _radius := 2.0
var _strength := 6.0
var _construction_material := 3
var _ore_material := 4
var _capture := Capture.new()
var _committed_carves: Array[Dictionary] = []
var _pending: Dictionary = {}
var _capture_active := false


func configure(
		terrain: Node,
		radius: float,
		strength: float,
		construction_material: int,
		ore_material: int
) -> void:
	_terrain = terrain
	_radius = radius
	_strength = strength
	_construction_material = construction_material
	_ore_material = ore_material
	_capture.configure(_terrain)


func submit(point: Vector3, mode: String) -> Dictionary:
	if _terrain == null or not _terrain.call("is_world_running"):
		return _failure("sculpt ignored: world is not running")
	if not _pending.is_empty():
		return _failure("sculpt ignored: another edit is still pending")
	if _capture_active:
		return _failure("sculpt ignored: carve restoration capture is still pending")
	var record := {
		"center": point,
		"radius": _radius,
		"density_value": _strength,
	}
	if mode == MODE_CARVE:
		var base_revision: int = _terrain.call("get_world_revision")
		_capture_active = true
		var samples: Array[Dictionary] = await _capture.capture_density_samples(
			point, _radius
		)
		_capture_active = false
		if samples.is_empty():
			return _failure("carve rejected: exact restoration capture failed")
		if _terrain.call("get_world_revision") != base_revision:
			return _failure("carve rejected: world changed during restoration capture")
		record["samples"] = samples
	var transaction: Object = _terrain.call("begin_edit_transaction", 1)
	if transaction == null:
		return _failure("sculpt rejected: " + str(_terrain.call("get_world_error")))
	var command_ok := false
	if mode == MODE_CARVE:
		command_ok = transaction.call(
			"add_density_sphere", point, _radius, _strength
		)
	elif mode == MODE_CONSTRUCT:
		command_ok = transaction.call(
			"add_density_sphere", point, _radius, -_strength
		) and transaction.call(
			"paint_material_sphere", point, _radius, _construction_material
		)
	elif mode == MODE_PAINT:
		command_ok = transaction.call(
			"paint_material_sphere", point, _radius, _ore_material
		)
	else:
		return _failure("sculpt rejected: unknown operation")
	if not command_ok:
		return _failure("sculpt rejected: " + str(transaction.call("get_error")))
	_pending = {"kind": mode, "record": record}
	if not _terrain.call("commit_edit_transaction", transaction):
		_pending = {}
		return _failure("sculpt rejected: " + str(transaction.call("get_error")))
	return _success(mode + " submitted at " + str(point.round()), point, mode)


func restore_last_carve() -> Dictionary:
	if _terrain == null or not _terrain.call("is_world_running"):
		return _failure("restore ignored: world is not running")
	if not _pending.is_empty():
		return _failure("restore ignored: another edit is still pending")
	if _committed_carves.is_empty():
		return _failure("restore ignored: no committed carve is available")
	var record: Dictionary = _committed_carves.pop_back()
	var transaction: Object = _terrain.call("begin_edit_transaction", 1)
	if transaction == null:
		_committed_carves.append(record)
		return _failure("restore rejected: " + str(_terrain.call("get_world_error")))
	var command_ok := true
	for sample: Dictionary in record["samples"]:
		var point: Vector3 = Vector3(sample["point"])
		if not transaction.call(
			"set_density_box", point, point, float(sample["density"])
		):
			command_ok = false
			break
	if not command_ok:
		_committed_carves.append(record)
		return _failure("restore rejected: " + str(transaction.call("get_error")))
	_pending = {"kind": MODE_RESTORE, "record": record}
	if not _terrain.call("commit_edit_transaction", transaction):
		_pending = {}
		_committed_carves.append(record)
		return _failure("restore rejected: " + str(transaction.call("get_error")))
	return _success(
		"restore submitted at " + str((record["center"] as Vector3).round()),
		record["center"],
		MODE_RESTORE
	)


func edit_committed() -> String:
	if _pending.is_empty():
		return "edit"
	var kind := str(_pending["kind"])
	if kind == MODE_CARVE:
		_committed_carves.append(_pending["record"])
	elif kind == MODE_CONSTRUCT:
		# Construction changes density after older captures were taken. Discard
		# those snapshots instead of offering a stale, destructive restoration.
		_committed_carves.clear()
	_pending = {}
	return kind


func edit_failed() -> String:
	if _pending.is_empty():
		return "edit"
	var kind := str(_pending["kind"])
	if kind == MODE_RESTORE:
		_committed_carves.append(_pending["record"])
	_pending = {}
	return kind


func get_restorable_carve_count() -> int:
	return _committed_carves.size()


func _success(status: String, point: Vector3, mode: String) -> Dictionary:
	return {"ok": true, "status": status, "point": point, "mode": mode}


func _failure(status: String) -> Dictionary:
	return {"ok": false, "status": status}
