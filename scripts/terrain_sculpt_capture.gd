class_name WtSandboxTerrainSculptCapture
extends RefCounted

const SAMPLE_SCALE := 65536
const MAX_CAPTURE_REQUESTS := 15
const CAPTURE_TIMEOUT_FRAMES := 600

var _terrain: Node
var _single_request_ids: Dictionary = {}
var _single_results: Dictionary = {}
var _single_failures: Dictionary = {}
var _batch_request_ids: Dictionary = {}
var _batch_results: Dictionary = {}
var _batch_failures: Dictionary = {}


func configure(terrain: Node) -> void:
	_terrain = terrain
	_terrain.authoritative_sample_ready.connect(_on_single_ready)
	_terrain.authoritative_sample_failed.connect(_on_single_failed)
	if _terrain.has_signal("authoritative_samples_ready"):
		_terrain.authoritative_samples_ready.connect(_on_batch_ready)
	if _terrain.has_signal("authoritative_samples_failed"):
		_terrain.authoritative_samples_failed.connect(_on_batch_failed)


func capture_density_samples(center: Vector3, radius: float) -> Array[Dictionary]:
	var points := _sphere_grid_points(center, radius)
	if points.is_empty():
		return []
	if _terrain.has_method("request_authoritative_samples"):
		return await _capture_density_samples_batch(points)
	return await _capture_density_samples_single(points)


func _capture_density_samples_batch(points: Array[Vector3i]) -> Array[Dictionary]:
	var request_id: int = _terrain.call("request_authoritative_samples", points, 0)
	if request_id <= 0:
		return []
	_batch_request_ids[request_id] = true
	var elapsed_frames := 0
	while true:
		if _batch_results.has(request_id):
			var samples: Array = _batch_results[request_id]
			_discard_batch_request(request_id)
			return _samples_to_capture(points, samples)
		if _batch_failures.has(request_id):
			_discard_batch_request(request_id)
			return []
		elapsed_frames += 1
		if elapsed_frames > CAPTURE_TIMEOUT_FRAMES:
			_discard_batch_request(request_id)
			return []
		await _terrain.get_tree().process_frame
	return []


func _capture_density_samples_single(points: Array[Vector3i]) -> Array[Dictionary]:
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
			_single_request_ids[request_id] = true
			pending[request_id] = points[cursor]
			cursor += 1
		for request_id: int in pending.keys():
			if _single_results.has(request_id):
				var sample: RefCounted = _single_results[request_id]
				captured.append({
					"point": pending[request_id],
					"density": sample.call("get_density"),
				})
				_single_results.erase(request_id)
				pending.erase(request_id)
			elif _single_failures.has(request_id):
				_single_failures.erase(request_id)
				_discard_single_requests(pending)
				return []
		if cursor < points.size() or not pending.is_empty():
			elapsed_frames += 1
			if elapsed_frames > CAPTURE_TIMEOUT_FRAMES:
				_discard_single_requests(pending)
				return []
			await _terrain.get_tree().process_frame
	return captured


func _samples_to_capture(points: Array[Vector3i], samples: Array) -> Array[Dictionary]:
	if samples.size() != points.size():
		return []
	var captured: Array[Dictionary] = []
	for index in range(points.size()):
		var sample: RefCounted = samples[index]
		if sample == null or sample.call("get_grid_point") != points[index]:
			return []
		captured.append({
			"point": points[index],
			"density": sample.call("get_density"),
		})
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


func _discard_single_requests(requests: Dictionary) -> void:
	for request_id: int in requests:
		_single_request_ids.erase(request_id)
		_single_results.erase(request_id)
		_single_failures.erase(request_id)


func _discard_batch_request(request_id: int) -> void:
	_batch_request_ids.erase(request_id)
	_batch_results.erase(request_id)
	_batch_failures.erase(request_id)


func _on_single_ready(request_id: int, sample: RefCounted) -> void:
	if not _single_request_ids.has(request_id):
		return
	_single_request_ids.erase(request_id)
	_single_results[request_id] = sample


func _on_single_failed(request_id: int, error: String) -> void:
	if not _single_request_ids.has(request_id):
		return
	_single_request_ids.erase(request_id)
	_single_failures[request_id] = error


func _on_batch_ready(request_id: int, samples: Array) -> void:
	if not _batch_request_ids.has(request_id):
		return
	_batch_request_ids.erase(request_id)
	_batch_results[request_id] = samples


func _on_batch_failed(request_id: int, error: String) -> void:
	if not _batch_request_ids.has(request_id):
		return
	_batch_request_ids.erase(request_id)
	_batch_failures[request_id] = error
