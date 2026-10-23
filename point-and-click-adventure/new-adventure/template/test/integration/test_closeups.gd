extends GutTest
## Close-up views: opening pushes in from the clicked hotspot until the view
## fills the screen, its hotspots take the clicks with no walking, and a right
## click backs out and leaves the room as it was.

var _lines: Array = []
var _listen: Callable


func before_each() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	_lines.clear()
	_listen = func(id: String, _speaker: String, _text: String) -> void:
		_lines.append(id)
		Say.skip.call_deferred()
	Say.line_started.connect(_listen)


func after_each() -> void:
	Say.line_started.disconnect(_listen)
	if Closeups.current:
		await Closeups.close()
	Rooms.clear()


func _closeup() -> Closeup:
	var closeup := Closeup.new()
	closeup.closeup_id = &"test_view"
	var background := Sprite2D.new()
	background.name = "Background"
	background.centered = false
	background.texture = Effects.soft_dot()
	background.scale = Vector2(120, 67.5)
	closeup.add_child(background)
	var hotspots := Node2D.new()
	hotspots.name = "Hotspots"
	closeup.add_child(hotspots)
	var detail := Hotspot.new()
	detail.id = &"detail"
	detail.display_name = "Detail"
	var shape := CollisionPolygon2D.new()
	shape.polygon = PackedVector2Array([Vector2(800, 400), Vector2(1100, 400), Vector2(1100, 600), Vector2(800, 600)])
	detail.add_child(shape)
	hotspots.add_child(detail)
	return closeup


func test_opening_pushes_in_and_fills_the_screen() -> void:
	var altar := Rooms.current.hotspots.get_node("Altar") as Hotspot
	var closeup := _closeup()
	watch_signals(Closeups)
	await Closeups.open_node(closeup, altar)
	assert_signal_emitted(Closeups, "opened")
	assert_eq(Closeups.current, closeup)
	assert_almost_eq(closeup.scale, Vector2.ONE, Vector2.ONE * 0.001, "fills the screen")
	assert_almost_eq(closeup.position, Vector2.ZERO, Vector2.ONE * 0.5)
	var camera := Rooms.current.get_viewport().get_camera_2d()
	assert_not_null(camera, "the room's camera pushed in")
	assert_gt(camera.zoom.x, 1.5)
	assert_eq(Interaction.locked, 0, "input is free inside the close-up")


func test_close_up_hotspots_take_clicks_without_walking() -> void:
	await Closeups.open_node(_closeup(), Rooms.current.hotspots.get_node("Altar") as Hotspot)
	var start := Rooms.player.global_position
	assert_eq(Interaction.hotspot_at(Vector2(950, 500)).id, &"detail", "screen-space hotspots")
	assert_null(Interaction.hotspot_at(Vector2(200, 900)), "nothing of the room shows through")
	await Interaction.click_at(Vector2(950, 500))
	assert_eq(_lines.size(), 1)
	assert_true(String(_lines[0]).begins_with("CORE_FALLBACK_LOOK"), "the detail answers, got %s" % _lines)
	await Interaction.click_at(Vector2(200, 900))
	assert_eq(Rooms.player.global_position, start, "no walking in a close-up")


func test_a_right_click_backs_out() -> void:
	await Closeups.open_node(_closeup(), Rooms.current.hotspots.get_node("Altar") as Hotspot)
	watch_signals(Closeups)
	Interaction.right_click()
	await wait_for_signal(Closeups.closed, 5.0)
	assert_signal_emitted(Closeups, "closed")
	assert_null(Closeups.current)
	await wait_process_frames(2)
	assert_eq(Rooms.current.get_viewport().get_canvas_transform(), Transform2D.IDENTITY, "the room's camera is back")
	assert_false(Interaction.inventory.is_open, "the right click did not open the inventory")
	assert_eq(Interaction.locked, 0)
