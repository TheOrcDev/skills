extends GutTest
## ScaleZones: linear depth scaling between the far and near lines.

var zones: ScaleZones


func before_each() -> void:
	zones = ScaleZones.new()
	zones.far_y = 900.0
	zones.far_scale = 0.5
	zones.near_y = 1100.0
	zones.near_scale = 1.0


func after_each() -> void:
	zones.free()


func test_scale_on_the_lines_and_between() -> void:
	assert_almost_eq(zones.scale_at(900.0), 0.5, 0.0001)
	assert_almost_eq(zones.scale_at(1100.0), 1.0, 0.0001)
	assert_almost_eq(zones.scale_at(1000.0), 0.75, 0.0001)


func test_scale_is_clamped_outside_the_lines() -> void:
	assert_almost_eq(zones.scale_at(400.0), 0.5, 0.0001)
	assert_almost_eq(zones.scale_at(2000.0), 1.0, 0.0001)


func test_equal_lines_use_the_near_scale() -> void:
	zones.far_y = 1000.0
	zones.near_y = 1000.0
	assert_almost_eq(zones.scale_at(1000.0), 1.0, 0.0001)
