class_name WtSandboxTerrainOverlay
extends CanvasLayer

@export var lab_path: NodePath
@export var terrain_path: NodePath
@export var viewer_path: NodePath
@export var visualizer_path: NodePath

var _lab: Node
var _terrain: Node3D
var _viewer: Node3D
var _visualizer: Node
var _panel: PanelContainer
var _label: Label
var _crosshair: Label
var _elapsed := 0.0


func _ready() -> void:
	_lab = get_node(lab_path)
	_terrain = get_node(terrain_path)
	_viewer = get_node(viewer_path)
	_visualizer = get_node(visualizer_path)
	_visualizer.visualization_changed.connect(_refresh)
	_panel = PanelContainer.new()
	_panel.position = Vector2(12, 12)
	_panel.custom_minimum_size = Vector2(440, 0)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_bottom", 10)
	_label = Label.new()
	_label.add_theme_font_size_override("font_size", 14)
	_label.add_theme_color_override("font_color", Color(0.92, 0.96, 1.0))
	_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	_label.add_theme_constant_override("shadow_offset_x", 1)
	_label.add_theme_constant_override("shadow_offset_y", 1)
	margin.add_child(_label)
	_panel.add_child(margin)
	add_child(_panel)
	_crosshair = Label.new()
	_crosshair.text = "+"
	_crosshair.add_theme_font_size_override("font_size", 26)
	_crosshair.add_theme_color_override("font_color", Color(1, 1, 1, 0.9))
	add_child(_crosshair)
	_crosshair.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_crosshair.position -= _crosshair.size * 0.5
	_refresh()


func _process(delta: float) -> void:
	_elapsed += delta
	if _elapsed < 0.25:
		return
	_elapsed = 0.0
	_refresh()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and 			not event.echo and event.keycode == KEY_F4:
		_panel.visible = not _panel.visible
		get_viewport().set_input_as_handled()


func _refresh() -> void:
	var metrics: Dictionary = _terrain.call("get_runtime_metrics")
	var fps := Engine.get_frames_per_second()
	var frame_ms := 1000.0 / maxf(float(fps), 1.0)
	var lod_counts: Dictionary = _visualizer.call("get_lod_counts")
	var recovery: Dictionary = _lab.call("get_recovery_policy")
	var position := _viewer.global_position
	var world_min: Vector3 = _lab.world_min
	var world_max: Vector3 = _lab.world_max
	var inside_map := (
		position.x >= world_min.x and position.x <= world_max.x
		and position.z >= world_min.z and position.z <= world_max.z
	)
	_label.text = (
		"World Transvoxel 1.0.4 Visual Sandbox\n" +
		"status: %s\n" % _lab.call("get_status") +
		"aim: %s\n" % _lab.call("get_aim_status") +
		"fps: %d  approximate frame: %.2f ms\n" % [fps, frame_ms] +
		"viewer: %s  speed: %.1f  map XZ: %s\n" % [
			str(position.round()),
			_viewer.call("get_movement_speed"),
			"inside" if inside_map else "OUTSIDE",
		] +
		"streaming anchor: %s\n" % str(
			_lab.call("get_streaming_position").round()
		) +
		"streaming policy: %s  max LOD %d  update distance %.1f\n" % [
			"follow viewer" if _lab.streaming_follows_viewer else "fixed full map",
			_lab.maximum_lod,
			_lab.streaming_update_distance,
		] +
		"orientation: +Y up; F2 wire box=boundary; orange terrain=ore\n" +
		"recovery: %s\n" % str(recovery.get("summary", "unknown")) +
		"world pages: %d  revision: %d\n" % [
			_terrain.call("get_world_page_count"),
			_terrain.call("get_world_revision"),
		] +
		"active/ready: %d/%d  retiring: %d  render: %d  collision: %d\n" % [
			int(metrics.get("active_chunk_records", 0)),
			int(metrics.get("fully_ready_chunk_records", 0)),
			int(metrics.get("pending_chunk_retirements", 0)),
			int(metrics.get("render_resources", 0)),
			int(metrics.get("collision_resources", 0)),
		] +
		"queues render/collision: %d / %d\n" % [
			int(metrics.get("queued_render", 0)),
			int(metrics.get("queued_collision", 0)),
		] +
		"mesh jobs/completions/transitions: %d / %d / %d\n" % [
			int(metrics.get("mesh_jobs", 0)),
			int(metrics.get("mesh_completions", 0)),
			int(metrics.get("transition_mesh_completions", 0)),
		] +
		"latency render/collision frames: %d / %d\n" % [
			int(metrics.get("render_latency_frames_maximum", 0)),
			int(metrics.get("collision_latency_frames_maximum", 0)),
		] +
		"view: %s  bounds: %s  LOD counts: %s\n" % [
			_visualizer.call("get_debug_mode_name"),
			str(_visualizer.call("get_bounds_visible")),
			str(lod_counts),
		] +
		"RMB mouse | WASD QE move | Shift fast | wheel speed\n" +
		"LMB carve | Shift+LMB construct rock | Ctrl+LMB paint ore\n" +
		"Ctrl+Z restore last committed carve at its original brush position\n" +
		"F1 view | F2 bounds | F3 collisions | F4 overlay | F5 reset camera"
	)
