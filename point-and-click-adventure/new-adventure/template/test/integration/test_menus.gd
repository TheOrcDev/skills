extends GutTest
## The top bar and its pages: the bar comes down at the top
## edge only while the player is free, a page pauses the game, the save and load
## pages work their slots, the settings page changes settings, and Reveal
## hotspots marks what can be used.

const DIR := "user://test-menu-saves"

var _directory := ""
var _listen: Callable


func before_each() -> void:
	_directory = Saves.directory
	Saves.directory = DIR
	_clear()
	GameState.reset()
	_listen = func(_id: String, _speaker: String, _text: String) -> void: Say.skip.call_deferred()
	Say.line_started.connect(_listen)
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	await _until_free()


func after_each() -> void:
	if Menus.screen:
		Menus.screen.close()
	Menus.bar.hide_now()
	Menus.hotspots.clear()
	await _until_free()
	Say.line_started.disconnect(_listen)
	Rooms.clear()
	_clear()
	Saves.directory = _directory
	GameState.reset()
	Settings.reset()


func _until_free() -> void:
	await wait_until(func() -> bool: return Interaction.locked == 0 and not Say.speaking, 10.0)


func _clear() -> void:
	if DirAccess.dir_exists_absolute(DIR):
		for file in DirAccess.get_files_at(DIR):
			DirAccess.remove_absolute(DIR.path_join(file))


func test_the_bar_comes_down_at_the_top_edge_while_the_player_is_free() -> void:
	assert_true(Menus.can_open())
	Menus.bar.follow(Vector2(960, 300), Menus.can_open())
	assert_false(Menus.bar.is_open, "not away from the edge")
	Menus.bar.follow(Vector2(960, 2), Menus.can_open())
	assert_true(Menus.bar.is_open, "at the edge")
	Menus.bar.follow(Vector2(960, 60), Menus.can_open())
	assert_true(Menus.bar.is_open, "while the cursor is on it")
	Menus.bar.follow(Vector2(960, 400), Menus.can_open())
	assert_false(Menus.bar.is_open, "gone once the cursor leaves")
	Interaction.locked += 1
	assert_false(Menus.can_open(), "not while input is locked")
	Interaction.locked -= 1


func test_a_page_pauses_the_game_until_it_closes() -> void:
	await Menus.choose(&"settings")
	assert_true(get_tree().paused)
	assert_true(Menus.screen is SettingsScreen)
	assert_false(Menus.can_open(), "no bar over a page")
	Menus.screen.close()
	assert_false(get_tree().paused)
	assert_null(Menus.screen)


func test_the_save_page_saves_and_asks_before_saving_over() -> void:
	await Menus.choose(&"save")
	(Menus.screen as SlotsScreen).pick(2)
	assert_true(Saves.has_save(2))
	assert_null(Menus.screen, "the page closes once saved")
	GameState.set_flag(&"menu_test")
	await Menus.choose(&"save")
	var page := Menus.screen as SlotsScreen
	page.pick(2)
	assert_eq(page.armed, 2, "a used slot waits for a second click")
	assert_false(Saves.read(2).get("flags", {}).has("menu_test"))
	page.pick(2)
	assert_true(Saves.read(2).get("flags", {}).has("menu_test"), "saved over on the second click")


func test_the_load_page_loads_used_slots_only() -> void:
	Rooms.player.global_position = Vector2(1200, 1000)
	assert_eq(Saves.save(3), OK)
	await Rooms.goto(&"greybox_gate", &"default", &"none")
	await _until_free()
	await Menus.choose(&"load")
	var page := Menus.screen as SlotsScreen
	page.pick(4)
	assert_eq(Menus.screen, page, "an empty slot does nothing")
	page.pick(3)
	assert_null(Menus.screen)
	await wait_for_signal(Saves.loaded, 10.0)
	assert_eq(Rooms.current.room_id, &"greybox_chapel")
	assert_eq(Rooms.player.global_position, Vector2(1200, 1000))


func test_the_settings_page_changes_settings() -> void:
	await Menus.choose(&"settings")
	var page := Menus.screen as SettingsScreen
	page.cycle(&"reduce_camera_motion")
	assert_true(Settings.reduce_camera_motion)
	assert_eq(page.value_line(&"reduce_camera_motion").text, "On")
	page.cycle(&"text_speed")
	assert_eq(Settings.text_speed, 1.5, "Normal moves on to Fast")
	page.slider(&"music_volume").value = 0.4
	assert_almost_eq(Settings.music_volume, 0.4, 0.001)


func test_reveal_hotspots_marks_what_can_be_used() -> void:
	assert_eq(Menus.hotspots.reveal(), 4, "the altar, the flask, the window and the way out")
	assert_eq(Menus.hotspots.markers().size(), 4)
	await wait_seconds(HotspotReveal.SECONDS + 0.3)
	assert_eq(Menus.hotspots.markers().size(), 0, "gone after a few seconds")
