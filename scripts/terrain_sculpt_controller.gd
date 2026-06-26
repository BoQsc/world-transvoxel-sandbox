class_name WtSandboxTerrainSculptController
extends RefCounted

const MODE_CARVE := "carve"
const MODE_CONSTRUCT := "construct rock"
const MODE_PAINT := "paint ore"
const MODE_RESTORE := "restore carve"
const SAMPLE_SCALE := 65536
const MAX_CAPTURE_REQUESTS := 15
const CAPTURE_TIMEOUT_FRAMES := 600

var _terrain: Node
var _radius := 2.0
var _strength := 6.0
var _construction_material := 3
var _ore_material := 4
var _committed_carves: Array[Dictionary] = []
var _pending: Dictionary = {}
var _capture_active := false
var _capture_request_ids: Dictionary = {}
var _sample_results: Dictionary = {}
var _sample_failures: Dictionary = {}


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
	_terrain.authoritative_sample_ready.connect(_on_sample_ready)
	_terrain.authoritative_sample_failed.connect(_on_sample_failed)


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
		var samples: Array[Dictionary] = await _capture_density_samples(point, _radius)
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


func _capture_density_samples(center: Vector3, radius: float) -> Array[Dictionary]:
	var points := _sphere_grid_points(center, radius)
	var captured: Array[Dictionary] = []
	var pending: Dictionary = {}
	var cursor := 0
	var elapsed_frames := 0
	while cursor < points.size() or not pending.is_empty():
		while cursor < points.size() and pending.size() < MAX_CAPTURE_REQUESTS:
			var request_id: int = _terrain.call(
				"request_authoritative_sample", points[cursor], 0
			)
			if request_id <= 0:
				break
			_capture_request_ids[request_id] = true
			pending[request_id] = points[cursor]
			cursor += 1
		for request_id: int in pending.keys():
			if _sample_results.has(request_id):
				var sample: RefCounted = _sample_results[request_id]
				captured.append({
					"point": pending[request_id],
					"density": sample.call("get_density"),
				})
				_sample_results.erase(request_id)
				pending.erase(request_id)
			elif _sample_failures.has(request_id):
				_sample_failures.erase(request_id)
				_discard_capture_requests(pending)
				return []
		if cursor < points.size() or not pending.is_empty():
			elapsed_frames += 1
			if elapsed_frames > CAPTURE_TIMEOUT_FRAMES:
				_discard_capture_requests(pending)
				return []
			await _terrain.get_tree().process_frame
	return captured


func _sphere_grid_points(center: Vector3, radius: float) -> Array[Vector3i]:
	var center_q := Vector3i(
		roundi(center.x * SAMPLE_SCALE),
		roundi(center.y * SAMPLE_SCALE),
		roundi(center.z * SAMPLE_SCALE)
	)
	var radius_q := roundi(radius * SAMPLE_SCALE)
	var minimum := Vector3i(
		floori(float(center_q.x - radius_q) / SAMPLE_SCALE),
		floori(float(center_q.y - radius_q) / SAMPLE_SCALE),
		floori(float(center_q.z - radius_q) / SAMPLE_SCALE)
	)
	var maximum := Vector3i(
		ceili(float(center_q.x + radius_q) / SAMPLE_SCALE),
		ceili(float(center_q.y + radius_q) / SAMPLE_SCALE),
		ceili(float(center_q.z + radius_q) / SAMPLE_SCALE)
	)
	var points: Array[Vector3i] = []
	for z in range(minimum.z, maximum.z + 1):
		for y in range(minimum.y, maximum.y + 1):
			for x in range(minimum.x, maximum.x + 1):
				var delta := Vector3i(
					x * SAMPLE_SCALE - center_q.x,
					y * SAMPLE_SCALE - center_q.y,
					z * SAMPLE_SCALE - center_q.z
				)
				if delta.length_squared() <= radius_q * radius_q:
					points.append(Vector3i(x, y, z))
	return points


func _discard_capture_requests(requests: Dictionary) -> void:
	for request_id: int in requests:
		_capture_request_ids.erase(request_id)
		_sample_results.erase(request_id)
		_sample_failures.erase(request_id)


func _on_sample_ready(request_id: int, sample: RefCounted) -> void:
	if not _capture_request_ids.has(request_id):
		return
	_capture_request_ids.erase(request_id)
	_sample_results[request_id] = sample


func _on_sample_failed(request_id: int, error: String) -> void:
	if not _capture_request_ids.has(request_id):
		return
	_capture_request_ids.erase(request_id)
	_sample_failures[request_id] = error


func _success(status: String, point: Vector3, mode: String) -> Dictionary:
	return {"ok": true, "status": status, "point": point, "mode": mode}


func _failure(status: String) -> Dictionary:
	return {"ok": false, "status": status}
