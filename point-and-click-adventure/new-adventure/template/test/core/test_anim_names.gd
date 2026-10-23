extends GutTest
## AnimNames: facing from vectors and the `<anim>_<dir>` fallbacks
## (docs/technical-plan.md §5.3).


func _has(names: Array) -> Callable:
	return func(anim: StringName) -> bool: return anim in names


func test_left_mirrors_right_when_no_left_exists() -> void:
	var choice := AnimNames.resolve(&"walk", AnimNames.Dir.L, _has([&"walk_r", &"walk_u", &"walk_d"]))
	assert_eq(choice.name, &"walk_r")
	assert_true(choice.flip)


func test_a_real_left_animation_wins() -> void:
	var choice := AnimNames.resolve(&"walk", AnimNames.Dir.L, _has([&"walk_l", &"walk_r"]))
	assert_eq(choice.name, &"walk_l")
	assert_false(choice.flip)


func test_down_right_falls_back_to_right() -> void:
	var choice := AnimNames.resolve(&"idle", AnimNames.Dir.DR, _has([&"idle_r", &"idle_d"]))
	assert_eq(choice.name, &"idle_r")
	assert_false(choice.flip)


func test_up_left_falls_back_to_mirrored_right() -> void:
	var choice := AnimNames.resolve(&"idle", AnimNames.Dir.UL, _has([&"idle_r", &"idle_u"]))
	assert_eq(choice.name, &"idle_r")
	assert_true(choice.flip)


func test_up_has_no_sideways_fallback() -> void:
	assert_true(AnimNames.resolve(&"idle", AnimNames.Dir.U, _has([&"idle_r"])).is_empty())


func test_bare_name_comes_last_and_mirrors_for_left() -> void:
	var choice := AnimNames.resolve(&"pickup", AnimNames.Dir.L, _has([&"pickup"]))
	assert_eq(choice.name, &"pickup")
	assert_true(choice.flip)


func test_dir_from_vector_four_way() -> void:
	assert_eq(AnimNames.dir_from_vector(Vector2(1, 0.3)), AnimNames.Dir.R)
	assert_eq(AnimNames.dir_from_vector(Vector2(-1, 0.2)), AnimNames.Dir.L)
	assert_eq(AnimNames.dir_from_vector(Vector2(0.2, 1)), AnimNames.Dir.D)
	assert_eq(AnimNames.dir_from_vector(Vector2(0.1, -1)), AnimNames.Dir.U)
	assert_eq(AnimNames.dir_from_vector(Vector2.ZERO), AnimNames.Dir.D)


func test_dir_from_vector_eight_way() -> void:
	assert_eq(AnimNames.dir_from_vector(Vector2(1, 1), true), AnimNames.Dir.DR)
	assert_eq(AnimNames.dir_from_vector(Vector2(-1, -1), true), AnimNames.Dir.UL)
	assert_eq(AnimNames.dir_from_vector(Vector2(-1, 1), true), AnimNames.Dir.DL)
	assert_eq(AnimNames.dir_from_vector(Vector2(1, -1), true), AnimNames.Dir.UR)
