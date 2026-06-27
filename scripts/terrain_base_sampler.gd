class_name WtSandboxTerrainBaseSampler
extends RefCounted

const FINITE_SHELL_SOLID_SAMPLES := 3

static func l4_sample(point: Vector3i) -> Dictionary:
	return terrain_sample(point, 2048, 64)


static func terrain_sample(point: Vector3i, horizontal_cells: int, vertical_cells: int) -> Dictionary:
	var x := point.x
	var y := point.y
	var z := point.z
	var scale := float(horizontal_cells) / 128.0
	var height := _terrain_height(x, z)
	var density := float(y) - height
	var cave_margin := FINITE_SHELL_SOLID_SAMPLES < x and \
		x < horizontal_cells - FINITE_SHELL_SOLID_SAMPLES and \
		FINITE_SHELL_SOLID_SAMPLES < y and \
		FINITE_SHELL_SOLID_SAMPLES < z and \
		z < horizontal_cells - FINITE_SHELL_SOLID_SAMPLES
	if cave_margin and y < height - 6.0:
		var cave := sin(float(x) * 0.112) + sin(float(y) * 0.137) + \
			cos(float(z) * 0.104) + 0.55 * sin(float(x + z) * 0.071)
		if cave > 2.28:
			density = maxf(density, (cave - 2.28) * 9.0)
	if cave_margin:
		density = maxf(density, _chamber_void_density(x, y, z, scale))
		density = maxf(density, _tunnel_void_density(x, y, z, horizontal_cells, scale))
	var boundary_distance := mini(mini(mini(x, horizontal_cells - x), y), mini(z, horizontal_cells - z))
	var boundary_density := 0.5 - float(boundary_distance)
	if boundary_density >= density:
		density = boundary_density
	return {"density": density, "material": _material(x, y, z, density, height)}


static func sphere_grid_points(center: Vector3, radius: float) -> Array[Vector3i]:
	var points: Array[Vector3i] = []
	var minimum := Vector3i(floori(center.x - radius), floori(center.y - radius), floori(center.z - radius))
	var maximum := Vector3i(ceili(center.x + radius), ceili(center.y + radius), ceili(center.z + radius))
	for z in range(minimum.z, maximum.z + 1):
		for y in range(minimum.y, maximum.y + 1):
			for x in range(minimum.x, maximum.x + 1):
				var point := Vector3i(x, y, z)
				if Vector3(point).distance_squared_to(center) <= radius * radius:
					points.append(point)
	return points


static func _terrain_height(x: int, z: int) -> float:
	var broad := 7.0 * sin(float(x) * 0.047) + 5.0 * cos(float(z) * 0.053)
	var local := 2.0 * sin(float(x) * 0.091 + 0.7 * cos(float(z) * 0.037))
	var mound := 3.0 * sin(float(x) * 0.023) * cos(float(z) * 0.031)
	return 34.0 + broad + local + mound


static func _chamber_void_density(x: int, y: int, z: int, scale: float) -> float:
	var dx := (float(x) - 40.0 * scale) / 9.0
	var dy := (float(y) - 18.0) / 6.0
	var dz := (float(z) - 40.0 * scale) / 9.0
	return (1.0 - sqrt(dx * dx + dy * dy + dz * dz)) * 7.0


static func _tunnel_void_density(x: int, y: int, z: int, horizontal_cells: int, scale: float) -> float:
	if x < 16.0 * scale or x > float(horizontal_cells) - 16.0 * scale:
		return -1.0e30
	var center_y := 15.0 + 2.5 * sin(float(x) * 0.083)
	var center_z := 88.0 * scale + 9.0 * sin(float(x) * 0.047)
	var dy := float(y) - center_y
	var dz := float(z) - center_z
	return (4.2 - sqrt(dy * dy + dz * dz)) * 1.8


static func _underground_material(x: int, y: int, z: int) -> int:
	var rock_field := sin(float(x) * 0.071 + float(y) * 0.043) + \
		cos(float(z) * 0.067 - float(y) * 0.051) + \
		0.65 * sin(float(x + y + z) * 0.039)
	return 5 if rock_field > 0.55 else 3


static func _material(x: int, y: int, z: int, density: float, height: float) -> int:
	if density >= 0.0:
		return 0
	var depth := height - float(y)
	if depth < 2.2:
		return 1
	var material := 2
	if depth < 8.0:
		material = 2
	else:
		material = _underground_material(x, y, z)
	if depth <= 7.0:
		return material
	var dy := float(y) - (18.0 + 5.0 * sin(float(x) * 0.078))
	var dz := float(z) - (64.0 + 20.0 * sin(float(x) * 0.043))
	return 4 if dy * dy + dz * dz < 5.0 else material
