shader_type spatial;
render_mode cull_back, depth_draw_opaque;

uniform int debug_mode : hint_range(0, 2) = 0;
uniform float pattern_scale : hint_range(0.01, 2.0) = 0.16;
uniform float surface_grain_strength : hint_range(0.0, 1.0) = 0.0;
uniform float lod_level = 0.0;

varying float material_id;
varying vec3 world_position;

vec3 material_color(float id) {
	if (id < 1.5) return vec3(0.18, 0.42, 0.12);
	if (id < 2.5) return vec3(0.34, 0.20, 0.10);
	if (id < 3.5) return vec3(0.20, 0.22, 0.24);
	if (id < 4.5) return vec3(0.65, 0.30, 0.08);
	return vec3(0.12, 0.14, 0.18);
}

vec3 lod_color(float lod) {
	if (lod < 0.5) return vec3(0.12, 0.78, 0.28);
	if (lod < 1.5) return vec3(0.12, 0.42, 0.95);
	if (lod < 2.5) return vec3(0.92, 0.62, 0.08);
	return vec3(0.82, 0.12, 0.65);
}

void vertex() {
	material_id = UV2.x;
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float resolved_material = floor(material_id + 0.5);
	vec3 base = material_color(resolved_material);
	if (debug_mode == 2) {
		base = lod_color(lod_level);
	} else if (debug_mode == 0 && surface_grain_strength > 0.0) {
		vec3 weights = pow(abs(NORMAL), vec3(4.0));
		weights /= max(weights.x + weights.y + weights.z, 0.0001);
		float px = sin(world_position.y * pattern_scale) *
			cos(world_position.z * pattern_scale * 0.77);
		float py = sin(world_position.x * pattern_scale * 0.81) *
			cos(world_position.z * pattern_scale);
		float pz = sin(world_position.x * pattern_scale) *
			cos(world_position.y * pattern_scale * 0.73);
		float grain = dot(vec3(px, py, pz), weights);
		base *= 1.0 + grain * 0.11 * surface_grain_strength;
	}
	ALBEDO = base;
	ROUGHNESS = resolved_material > 3.5 && resolved_material < 4.5 ? 0.55 : 0.92;
	METALLIC = resolved_material > 3.5 && resolved_material < 4.5 ? 0.22 : 0.0;
}
