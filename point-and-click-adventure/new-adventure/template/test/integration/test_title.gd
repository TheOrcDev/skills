extends GutTest
## The start screen: what it offers at launch and over a game, that
## the game pauses behind it, that Resume goes back, that New Game ends the game
## and asks for a new one, and that Continue picks the newest save.

const DIR := "user://test-title-saves"

var _directory := ""
var _listen: Callable


func before_each() -> void:
	_directory = Saves.directory
	Saves.directory = DIR
	_clear()
	GameState.reset()
	_listen = func(_id: String, _speaker: String, _text: String) -> void: Say.skip.call_deferred()
	Say.line_started.connect(_listen)


func after_each() -> void:
	if Menus.screen:
		Menus.screen.close()
	if Menus.title:
		Menus.title.close()
	await get_tree().process_frame
	get_tree().paused = false
	await wait_until(func() -> bool: return Interaction.locked == 0 and not Say.speaking, 10.0)
	Say.line_started.disconnect(_listen)
	Rooms.clear()
	_clear()
	Saves.directory = _directory
	Saves.autosave = false
	GameState.reset()


func _clear() -> void:
	if DirAccess.dir_exists_absolute(DIR):
		for file in DirAccess.get_files_at(DIR):
			DirAccess.remove_absolute(DIR.path_join(file))


func _ids() -> Array:
	return Menus.title.entries().map(func(entry: Array) -> StringName: return entry[0])


func _in_game() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	await wait_until(func() -> bool: return Interaction.locked == 0 and not Say.speaking, 10.0)


func test_at_launch_it_offers_a_new_game_and_no_continue_without_a_save() -> void:
	Menus.show_title()
	var ids := _ids()
	assert_eq(ids[0], &"new_game")
	assert_has(ids, &"load")
	assert_has(ids, &"settings")
	assert_does_not_have(ids, &"continue")
	assert_does_not_have(ids, &"save", "nothing to save before a game")
	assert_does_not_have(ids, &"resume")
	assert_false(get_tree().paused)
	assert_not_null(Menus.title.button(&"new_game"))


func test_continue_comes_first_once_there_is_a_save() -> void:
	await _in_game()
	Saves.save(2)
	Rooms.clear()
	Menus.show_title()
	assert_eq(_ids()[0], &"continue")


func test_continue_picks_the_newest_save() -> void:
	await _in_game()
	Saves.save(3)
	var older := FileAccess.get_file_as_string(Saves.path(3)).replace(str(Saves.read(3)["saved_at"]), "2020-01-01T00:00:00")
	var file := FileAccess.open(Saves.path(3), FileAccess.WRITE)
	file.store_string(older)
	file.close()
	Saves.save(5)
	assert_eq(Saves.latest_slot(), 5)
	_clear()
	assert_eq(Saves.latest_slot(), -1, "none once the saves are gone")


func test_over_a_game_it_pauses_it_and_offers_resume_and_save() -> void:
	await _in_game()
	assert_true(Menus.can_open())
	Menus.show_title(true)
	assert_true(get_tree().paused, "the game waits")
	assert_false(Menus.can_open(), "no bar over the start screen")
	var ids := _ids()
	assert_eq(ids.slice(0, 2), [&"resume", &"save"])
	Menus.choose_on_title(&"save")
	assert_true(Menus.screen is SlotsScreen and (Menus.screen as SlotsScreen).saving)
	(Menus.screen as SlotsScreen).pick(1)
	assert_true(Saves.has_save(1))
	assert_true(get_tree().paused, "still paused under the start screen after saving")
	Menus.choose_on_title(&"resume")
	await get_tree().process_frame
	assert_null(Menus.title)
	assert_false(get_tree().paused)
	assert_not_null(Rooms.current, "the game is where it was")


func test_the_bar_offers_the_main_menu() -> void:
	var ids := TopBar.ENTRIES.map(func(entry: Array) -> StringName: return entry[0])
	assert_has(ids, &"menu")


func test_new_game_ends_the_game_and_asks_for_a_new_one() -> void:
	await _in_game()
	GameState.set_flag(&"title_test")
	Menus.show_title(true)
	watch_signals(Menus)
	Menus.choose_on_title(&"new_game")
	assert_true(Menus.screen is MenuScreen, "a game in progress asks first")
	Menus.screen.close()
	await Menus.title.leave(Menus._new_game)
	assert_signal_emitted(Menus, "new_game_requested")
	assert_null(Rooms.current, "the old game is gone")
	assert_false(GameState.get_flag(&"title_test"), "the state starts over")
	assert_false(get_tree().paused)
