extends SceneTree
const WORLD_ROOT := "res://artifacts/scale_ladder/L4/world"
const WORLD_PATH := WORLD_ROOT + "/world.wtworld"
const JOURNAL_PATH := WORLD_ROOT + "/world.wtedit"
const TIMEOUT_FRAMES := 3600
const ACTIVE_CHUNK_CAPACITY := 1024
var _scene_root: Node
var _terrain: Node
var _samples: Dictionary = {}
var _sample_failures: Dictionary = {}
func _initialize() -> void:
	call_deferred("_run")
func _run() -> void:
	if not FileAccess.file_exists(WORLD_PATH):
		return _fail("L4 world missing; run python tools/scale_ladder.py --level L4 --force")
	if FileAccess.file_exists(JOURNAL_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(JOURNAL_PATH))
	var started := Time.get_ticks_msec()
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
	var terrain_node: Node = _scene_root.get_node("Terrain")
	var config: Resource = terrain_node.get("configuration").duplicate(true)
	config.set("active_chunk_capacity", ACTIVE_CHUNK_CAPACITY)
	terrain_node.set("configuration", config)
	var viewer: Node3D = _scene_root.get_node("Viewer")
	viewer.set("input_enabled", false)
	viewer.position = Vector3(256.0, 56.0, 256.0)
	root.add_child(_scene_root)
	var terrain: Node = terrain_node
	_terrain = terrain
	terrain.authoritative_sample_ready.connect(_on_sample_ready)
	terrain.authoritative_sample_failed.connect(_on_sample_failed)
	if not await _wait_for_world(terrain):
		return _fail("L4 world did not become ready")
	var startup_ms := Time.get_ticks_msec() - started
	viewer.emit_signal("position_changed", viewer.global_position)
	var settle_started := Time.get_ticks_msec()
	if not await _wait_for_settled_resources(terrain):
		return _fail("L4 center streaming did not settle")
	var settle_ms := Time.get_ticks_msec() - settle_started
	if not await _audit_density_signs(terrain):
		return
	var positions: Array[Vector3] = [
		Vector3(256.0, 56.0, 256.0),
		Vector3(512.0, 56.0, 512.0),
		Vector3(768.0, 56.0, 768.0),
		Vector3(1024.0, 56.0, 1024.0),
		Vector3(1280.0, 56.0, 1280.0),
		Vector3(1536.0, 56.0, 1536.0),
		Vector3(1792.0, 56.0, 1792.0),
	]
	var offsets: Array[Vector3] = [
		Vector3.ZERO,
		Vector3(10.0, 0.0, 0.0),
		Vector3(-10.0, 0.0, 0.0),
		Vector3(0.0, 0.0, 10.0),
		Vector3(0.0, 0.0, -10.0),
	]
	var min_render := 999999
	var min_collision := 999999
	var max_retiring := 0
	for step in range(positions.size()):
		viewer.global_position = positions[step]
		viewer.emit_signal("position_changed", viewer.global_position)
		if not await _wait_for_settled_resources(terrain):
			return _fail("L4 staged movement did not settle at step " + str(step))
		var metrics: Dictionary = terrain.get_runtime_metrics()
		min_render = mini(min_render, terrain.get_rendered_chunk_count())
		min_collision = mini(min_collision, terrain.get_collision_chunk_count())
		max_retiring = maxi(max_retiring, int(metrics.get("pending_chunk_retirements", 0)))
		for offset in offsets:
			var probe := positions[step] + offset
			if not _probe_render_and_collision(terrain, probe):
				return _fail("L4 render/collision probe failed at " + str(probe))
	var edit_started := Time.get_ticks_msec()
	var edit_delta := await _audit_edit_latency(terrain)
	if is_nan(edit_delta):
		return
	var edit_ms := Time.get_ticks_msec() - edit_started
	if not terrain.stop_world():
		return _fail("L4 world stop was rejected")
	for _frame in range(TIMEOUT_FRAMES):
		if terrain.get_world_state_name() == "stopped":
			print(
				"WT_SANDBOX_L4_RUNTIME_PASS startup_ms=%d settle_ms=%d positions=%d probes=%d min_render=%d min_collision=%d edit_ms=%d edit_delta=%.1f max_retiring=%d active_capacity=%d"
				% [
					startup_ms,
					settle_ms,
					positions.size(),
					positions.size() * offsets.size(),
					min_render,
					min_collision,
					edit_ms,
					edit_delta,
					max_retiring,
					ACTIVE_CHUNK_CAPACITY,
				]
			)
			_scene_root.queue_free()
			if FileAccess.file_exists(JOURNAL_PATH):
				DirAccess.remove_absolute(ProjectSettings.globalize_path(JOURNAL_PATH))
			quit(0)
			return
		await process_frame
	_fail("L4 world did not stop after runtime audit")
func _audit_density_signs(terrain: Node) -> bool:
	var below := await _query_sample(terrain, Vector3i(1024, 20, 1024))
	var above := await _query_sample(terrain, Vector3i(1024, 60, 1024))
	var boundary := await _query_sample(terrain, Vector3i(0, 12, 546))
	var inner := await _query_sample(terrain, Vector3i(1, 12, 546))
	if below == null or above == null or boundary == null or inner == null:
		_fail("L4 density sign queries failed")
		return false
	if below.get_density() >= 0.0 or above.get_density() <= 0.0:
		_fail("L4 center density signs are inconsistent")
		return false
	if boundary.get_density() <= 0.0 or inner.get_density() >= 0.0:
		_fail("L4 finite boundary density is inconsistent")
		return false
	return true
func _audit_edit_latency(terrain: Node) -> float:
	var point := Vector3i(1792, 16, 1792)
	var before := await _query_sample(terrain, point)
	if before == null:
		_fail("L4 pre-edit sample failed")
		return NAN
	var revision_before: int = terrain.get_world_revision()
	var mesh_jobs_before := int(terrain.get_runtime_metrics().get("mesh_jobs", 0))
	var transaction: Object = terrain.begin_edit_transaction(401)
	if transaction == null or not transaction.add_density_sphere(
		Vector3(point), 3.0, 6.0
	) or not terrain.commit_edit_transaction(transaction):
		_fail("L4 edit submission failed")
		return NAN
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = terrain.get_runtime_metrics()
		if terrain.get_world_revision() > revision_before and \
				int(metrics.get("mesh_jobs", 0)) > mesh_jobs_before and \
				await _wait_for_settled_resources(terrain):
			var after := await _query_sample(terrain, point)
			if after == null:
				_fail("L4 post-edit sample failed")
				return NAN
			var delta: float = after.get_density() - before.get_density()
			if absf(delta - 6.0) > 0.001:
				_fail("L4 edit density delta mismatch: " + str(delta))
				return NAN
			return delta
		await process_frame
	_fail("L4 edit did not commit and settle")
	return NAN
func _probe_render_and_collision(terrain: Node, probe: Vector3) -> bool:
	var origin := Vector3(probe.x, 60.0, probe.z)
	var ray := PhysicsRayQueryParameters3D.create(origin, Vector3(probe.x, 0.0, probe.z))
	var collision_hit: Dictionary = terrain.get_world_3d().direct_space_state.intersect_ray(ray)
	return not collision_hit.is_empty() and _render_ray_hit(terrain, origin, Vector3.DOWN)
func _render_ray_hit(terrain: Node, origin: Vector3, direction: Vector3) -> bool:
	for child in terrain.get_children():
		if not child is MeshInstance3D or not child.name.begins_with("WT_Render_"):
			continue
		var bounds: AABB = child.global_transform * child.get_aabb()
		if origin.x < bounds.position.x or origin.x > bounds.end.x or \
				origin.z < bounds.position.z or origin.z > bounds.end.z:
			continue
		var arrays: Array = child.mesh.surface_get_arrays(0)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		for triangle in range(0, indices.size(), 3):
			var a: Vector3 = child.global_transform * vertices[indices[triangle]]
			var b: Vector3 = child.global_transform * vertices[indices[triangle + 1]]
			var c: Vector3 = child.global_transform * vertices[indices[triangle + 2]]
			var edge_ab := b - a
			var edge_ac := c - a
			var h := direction.cross(edge_ac)
			var determinant := edge_ab.dot(h)
			if determinant >= -0.000001:
				continue
			var inverse := 1.0 / determinant
			var offset := origin - a
			var u := inverse * offset.dot(h)
			var q := offset.cross(edge_ab)
			var v := inverse * direction.dot(q)
			if u >= 0.0 and v >= 0.0 and u + v <= 1.0 and \
					inverse * edge_ac.dot(q) > 0.0:
				return true
	return false
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
		if terrain.get_world_state_name() == "failed":
			print("WT_SANDBOX_L4_RUNTIME_METRICS " + str(terrain.get_runtime_metrics()))
			return false
		await process_frame
	return false
func _wait_for_settled_resources(terrain: Node) -> bool:
	var ready_since_ms := -1
	for _frame in range(TIMEOUT_FRAMES):
		var metrics: Dictionary = terrain.get_runtime_metrics()
		if terrain.get_world_state_name() == "failed":
			print("WT_SANDBOX_L4_RUNTIME_METRICS " + str(metrics))
			return false
		if terrain.get_rendered_chunk_count() > 0 and terrain.get_collision_chunk_count() > 0 and \
				int(metrics.get("queued_render", 0)) == 0 and int(metrics.get("queued_collision", 0)) == 0 and \
				int(metrics.get("mesh_jobs", 0)) == int(metrics.get("mesh_completions", -1)) and \
				int(metrics.get("fully_ready_chunk_records", -1)) == int(metrics.get("active_chunk_records", 0)) and \
				int(metrics.get("pending_chunk_retirements", 0)) == 0:
			if ready_since_ms < 0:
				ready_since_ms = Time.get_ticks_msec()
			elif Time.get_ticks_msec() - ready_since_ms >= 300:
				return true
		else:
			ready_since_ms = -1
		await process_frame
	return false
func _on_sample_ready(request_id: int, sample: RefCounted) -> void:
	_samples[request_id] = sample
func _on_sample_failed(request_id: int, error: String) -> void:
	_sample_failures[request_id] = error
func _fail(message: String) -> void:
	push_error("WT_SANDBOX_L4_RUNTIME_FAIL: " + message)
	if _terrain != null:
		print("WT_SANDBOX_L4_RUNTIME_METRICS " + str(_terrain.get_runtime_metrics()))
	if _scene_root != null:
		_scene_root.queue_free()
	quit(1)
