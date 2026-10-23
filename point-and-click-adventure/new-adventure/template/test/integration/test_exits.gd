extends GutTest
## Exits: a click walks the hero to the exit and changes rooms, a double-click
## leaves at once, and the cursor takes a shape for walking, hotspots and exits.

var _exit: Exit


func before_each() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	_exit = Exit.new()
	_exit.name = "ToSandbox"
	_exit.id = &"to_courtyard"
	_exit.display_name = "Way out"
	_exit.target_room = &"greybox_courtyard"
	_exit.direction = &"left"
	_exit.position = Vector2(470, 1000)
	var shape := CollisionPolygon2D.new()
	shape.polygon = PackedVector2Array([Vector2(-40, -60), Vector2(40, -60), Vector2(40, 40), Vector2(-40, 40)])
	_exit.add_child(shape)
	Rooms.current.hotspots.add_child(_exit)


func after_each() -> void:
	await wait_until(func() -> bool: return Interaction.locked == 0, 10.0)
	Rooms.clear()


func test_exits_walk_by_default() -> void:
	assert_eq(_exit.default_verb, &"walk")


func test_a_click_walks_there_and_leaves() -> void:
	watch_signals(Rooms)
	Interaction.click_at(_exit.focus_point())
	await wait_for_signal(Rooms.room_changed, 20.0)
	assert_signal_emitted(Rooms, "room_changed")
	assert_eq(Rooms.current.room_id, &"greybox_courtyard")
	await wait_until(func() -> bool: return Interaction.locked == 0, 10.0)
	assert_eq(Interaction.locked, 0, "input is free again in the new room")


func test_a_double_click_leaves_at_once() -> void:
	Rooms.player.global_position = Vector2(1600, 1040)
	await wait_physics_frames(2)
	watch_signals(Rooms)
	var started := Time.get_ticks_msec()
	Interaction.double_click_at(_exit.focus_point())
	await wait_for_signal(Rooms.room_changed, 5.0)
	assert_eq(Rooms.current.room_id, &"greybox_courtyard")
	assert_lt(Time.get_ticks_msec() - started, 2000, "no walk across the nave first")


func test_cursor_shapes() -> void:
	for kind in [&"walk", &"hotspot", &"exit_left", &"exit_right", &"exit_up", &"exit_down"]:
		var image := Cursors.texture_for(kind).get_image()
		var covered := 0
		for y in image.get_height():
			for x in image.get_width():
				if image.get_pixel(x, y).a > 0.5:
					covered += 1
		assert_gt(covered, 10, "%s draws something" % kind)
	# On the upper arm of the arrowhead: the right arrow has it, the left does not.
	var right := Cursors.texture_for(&"exit_right").get_image()
	var left := Cursors.texture_for(&"exit_left").get_image()
	assert_true(right.get_pixel(28, 16).a > 0.5, "the right arrow's head")
	assert_false(left.get_pixel(28, 16).a > 0.5, "is not on the left arrow")
