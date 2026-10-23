extends GutTest
## The inventory overlay driven with synthetic mouse input: open and close,
## pick an item onto the cursor, drop it, combine two items, and use a held
## item on a hotspot that has no answer for it.


func _item(id: StringName, combinations := {}) -> void:
	var item := ItemDef.new()
	item.id = id
	item.display_name = String(id).capitalize()
	item.combinations = combinations
	Inventory.register(item)


func before_each() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	GameState.inventory.clear()
	Inventory.drop()
	Interaction.inventory.close()
	_item(&"rope")
	_item(&"hook", {&"rope": &"grapple"})
	_item(&"grapple")
	Inventory.add(&"rope")
	Inventory.add(&"hook")


func after_each() -> void:
	Interaction.inventory.close()
	Inventory.drop()
	GameState.inventory.clear()
	Rooms.clear()


func _press(button: MouseButton, at: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = button
	event.position = at
	event.global_position = at
	event.pressed = true
	get_viewport().push_input(event)
	var release := event.duplicate() as InputEventMouseButton
	release.pressed = false
	get_viewport().push_input(release)
	await wait_process_frames(2)


## Clicks an item slot directly: GUT's own runner panel covers the bottom of
## the headless screen, so pushed events there never reach the slots.
func _click_slot(id: StringName, button := MOUSE_BUTTON_LEFT) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = button
	event.pressed = true
	Interaction.inventory.slot_for(id).gui_input.emit(event)
	await wait_process_frames(2)


func test_right_click_opens_and_closes_the_inventory() -> void:
	await _press(MOUSE_BUTTON_RIGHT, Vector2(960, 400))
	assert_true(Interaction.inventory.is_open, "a right click opens it")
	await _press(MOUSE_BUTTON_RIGHT, Vector2(960, 400))
	assert_false(Interaction.inventory.is_open, "a right click outside the items closes it")


func test_pick_an_item_then_drop_it() -> void:
	Interaction.inventory.open()
	await wait_process_frames(2)
	await _click_slot(&"rope")
	assert_eq(Inventory.held.id if Inventory.held else &"", &"rope", "the rope is on the cursor")
	assert_true(Interaction.inventory.is_open, "the inventory stays open for a second item")
	await _click_slot(&"rope")
	assert_null(Inventory.held, "clicking the held item puts it back")
	await _click_slot(&"rope")
	await _press(MOUSE_BUTTON_RIGHT, Vector2(960, 400))
	assert_null(Inventory.held, "a right click drops it")
	assert_false(Interaction.inventory.is_open, "and closes the inventory")
	await _press(MOUSE_BUTTON_RIGHT, Vector2(960, 400))
	assert_true(Interaction.inventory.is_open, "with nothing held, a right click opens it again")


func test_combining_two_items_in_the_inventory() -> void:
	Interaction.inventory.open()
	await wait_process_frames(2)
	await _click_slot(&"rope")
	await _click_slot(&"hook")
	assert_eq(GameState.inventory, [&"grapple"] as Array[StringName], "rope and hook become a grapple")
	assert_null(Inventory.held)


func test_a_held_item_on_a_hotspot_without_an_answer_falls_back() -> void:
	Inventory.hold(&"rope")
	var statue := Rooms.current.hotspots.get_node("Window") as Hotspot
	var lines := []
	var listen := func(id: String, _speaker: String, _text: String) -> void:
		lines.append(id)
		Say.skip.call_deferred()
	Say.line_started.connect(listen)
	await Interaction.click_at(statue.focus_point())
	Say.line_started.disconnect(listen)
	assert_eq(lines.size(), 1)
	assert_true(String(lines[0]).begins_with("CORE_FALLBACK_ITEM"), "a dry fallback, got %s" % lines)
	assert_null(Inventory.held, "the item goes back to the inventory")
