class_name WtSandboxTerrainVisualizer
extends Node

signal visualization_changed

@export var terrain_path: NodePath
@export var terrain_material: ShaderMaterial
@export var bounds_visible := true

var _terrain: Node
var _debug_mode := 0
var _lod_counts: Dictionary = {}
var _chunk_lods: Dictionary = {}


func _ready() -> void:
	_terrain = get_node(terrain_path)
	_terrain.child_entered_tree.connect(_on_terrain_child_entered)
	_terrain.child_exiting_tree.connect(_on_terrain_child_exiting)
	for child in _terrain.get_children():
		_configure_child.call_deferred(child)


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.keycode == KEY_F1:
		_debug_mode = (_debug_mode + 1) % 3
		terrain_material.set_shader_parameter("debug_mode", _debug_mode)
		visualization_changed.emit()
		get_viewport().set_input_as_handled()
	elif event.keycode == KEY_F2:
		bounds_visible = not bounds_visible
		for child in _terrain.get_children():
			var bounds := child.get_node_or_null("WT_DebugBounds")
			if bounds != null:
				bounds.visible = bounds_visible
		visualization_changed.emit()
		get_viewport().set_input_as_handled()
	elif event.keycode == KEY_F3:
		get_tree().debug_collisions_hint = not get_tree().debug_collisions_hint
		visualization_changed.emit()
		get_viewport().set_input_as_handled()


func _on_terrain_child_entered(child: Node) -> void:
	_configure_child.call_deferred(child)


func _configure_child(child: Node) -> void:
	if not is_instance_valid(child) or 			not child is MeshInstance3D or 			not child.name.begins_with("WT_Render_"):
		return
	var instance_id := child.get_instance_id()
	if _chunk_lods.has(instance_id):
		return
	var lod := int(String(child.name).get_slice("_L", 1))
	child.material_override = terrain_material
	child.set_instance_shader_parameter("lod_level", float(lod))
	if child.get_node_or_null("WT_DebugBounds") == null:
		child.add_child(_create_bounds(lod))
	_chunk_lods[instance_id] = lod
	_lod_counts[lod] = int(_lod_counts.get(lod, 0)) + 1


func _on_terrain_child_exiting(child: Node) -> void:
	var instance_id := child.get_instance_id()
	if not _chunk_lods.has(instance_id):
		return
	var lod: int = _chunk_lods[instance_id]
	_chunk_lods.erase(instance_id)
	var remaining := int(_lod_counts.get(lod, 1)) - 1
	if remaining <= 0:
		_lod_counts.erase(lod)
	else:
		_lod_counts[lod] = remaining


func _create_bounds(lod: int) -> MeshInstance3D:
	var extent := float(16 << lod)
	var corners := [
		Vector3(0, 0, 0), Vector3(extent, 0, 0),
		Vector3(extent, extent, 0), Vector3(0, extent, 0),
		Vector3(0, 0, extent), Vector3(extent, 0, extent),
		Vector3(extent, extent, extent), Vector3(0, extent, extent),
	]
	var edges := [
		[0, 1], [1, 2], [2, 3], [3, 0],
		[4, 5], [5, 6], [6, 7], [7, 4],
		[0, 4], [1, 5], [2, 6], [3, 7],
	]
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.no_depth_test = true
	material.albedo_color = (
		Color(0.20, 0.95, 0.35, 0.8)
		if lod == 0
		else Color(0.20, 0.55, 1.0, 0.8)
	)
	var mesh := ImmediateMesh.new()
	mesh.surface_begin(Mesh.PRIMITIVE_LINES, material)
	for edge in edges:
		mesh.surface_add_vertex(corners[edge[0]])
		mesh.surface_add_vertex(corners[edge[1]])
	mesh.surface_end()
	var instance := MeshInstance3D.new()
	instance.name = "WT_DebugBounds"
	instance.mesh = mesh
	instance.visible = bounds_visible
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return instance


func get_debug_mode_name() -> String:
	return ["surface", "materials", "lod"][_debug_mode]


func get_bounds_visible() -> bool:
	return bounds_visible


func get_configured_chunk_count() -> int:
	return _chunk_lods.size()


func get_lod_counts() -> Dictionary:
	return _lod_counts.duplicate(true)
