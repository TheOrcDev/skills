extends GutTest
## Saves: a slot keeps the whole state and where the hero
## stands, loading puts both back, the autosave follows room changes once a
## game runs, older saves are migrated, and saves this build cannot read are
## refused without touching the game.

const DIR := "user://test-saves"

var _directory := ""
var _listen: Callable


func before_each() -> void:
	_directory = Saves.directory
	Saves.directory = DIR
	_clear()
	GameState.reset()
	_listen = func(_id: String, _speaker: String, _text: String) -> void: Say.skip.call_deferred()
	Say.line_started.connect(_listen)
	await Rooms.goto(&"greybox_gate", &"default", &"none")
	await _until_free()


func after_each() -> void:
	await _until_free()
	Saves.autosave = false
	Say.line_started.disconnect(_listen)
	Rooms.clear()
	_clear()
	Saves.directory = _directory
	GameState.reset()


func _until_free() -> void:
	await wait_until(func() -> bool: return Interaction.locked == 0 and not Say.speaking, 10.0)


func _clear() -> void:
	if DirAccess.dir_exists_absolute(DIR):
		for file in DirAccess.get_files_at(DIR):
			DirAccess.remove_absolute(DIR.path_join(file))


func _write(slot: int, text: String) -> void:
	DirAccess.make_dir_recursive_absolute(DIR)
	var file := FileAccess.open(Saves.path(slot), FileAccess.WRITE)
	file.store_string(text)
	file.close()


func test_a_slot_keeps_the_state_and_where_the_hero_stands() -> void:
	GameState.set_flag(&"door_open")
	GameState.set_flag(&"visits", 3)
	GameState.set_flag(&"name_guess", "Halden")
	GameState.inventory.assign([&"key", &"letter"])
	GameState.room_state(&"greybox_gate")[&"lantern"] = "lit"
	GameState.remember(&"greybox_window")
	GameState.hints[&"gate"] = 2
	Rooms.player.global_position = Vector2(1200, 905)
	assert_eq(Saves.save(1), OK)
	assert_true(Saves.has_save(1))
	GameState.reset()
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	assert_eq(await Saves.load_slot(1), OK)
	assert_eq(Rooms.current.room_id, &"greybox_gate")
	assert_eq(Rooms.player.global_position, Vector2(1200, 905), "the hero stands where they were saved")
	assert_true(GameState.get_flag(&"door_open"))
	assert_true(GameState.get_flag(&"visits") == 3, "numbers come back")
	assert_eq(GameState.get_flag(&"name_guess"), "Halden")
	assert_eq(Array(GameState.inventory), [&"key", &"letter"])
	assert_eq(GameState.room_state(&"greybox_gate").get(&"lantern"), "lit")
	assert_eq(Array(GameState.memories), [&"greybox_window"])
	assert_true(GameState.hints.get(&"gate") == 2)


func test_loading_empties_the_cursor() -> void:
	GameState.inventory.assign([&"key"])
	assert_eq(Saves.save(1), OK)
	Inventory.held = ItemDef.new()
	assert_eq(await Saves.load_slot(1), OK)
	assert_null(Inventory.held)


func test_the_autosave_follows_room_changes_once_a_game_runs() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	await wait_process_frames(3)
	assert_false(Saves.has_save(Saves.AUTOSAVE), "no autosave before a game starts")
	Saves.autosave = true
	await Rooms.goto(&"greybox_gate", &"from_chapel", &"none")
	await wait_until(func() -> bool: return Saves.has_save(Saves.AUTOSAVE), 5.0)
	var data := Saves.read(Saves.AUTOSAVE)
	assert_eq(data.get("room"), "greybox_gate")
	assert_eq(data.get("entry"), "from_chapel")


func test_a_version_1_save_is_migrated() -> void:
	_write(2, JSON.stringify({"save_version": 1, "flags": {"door_open": true}, "inventory": ["key"]}))
	var data := Saves.read(2)
	assert_eq(int(data.get("save_version", 0)), GameState.SAVE_VERSION)
	assert_eq(data.get("memories"), [])
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	assert_eq(await Saves.load_slot(2), OK)
	assert_eq(Rooms.current.room_id, Saves.first_room(), "a save that names no room resumes in the first room")
	assert_true(GameState.get_flag(&"door_open"))
	assert_eq(Array(GameState.inventory), [&"key"])


func test_saves_this_build_cannot_read_are_refused() -> void:
	_write(3, JSON.stringify({"save_version": GameState.SAVE_VERSION + 1, "room": "greybox_chapel"}))
	_write(4, "not a save")
	assert_eq(Saves.read(3), {}, "a save from a newer build")
	assert_eq(Saves.read(4), {}, "a broken file")
	assert_eq(await Saves.load_slot(3), ERR_FILE_UNRECOGNIZED)
	assert_eq(await Saves.load_slot(5), ERR_FILE_NOT_FOUND)
	assert_eq(Rooms.current.room_id, &"greybox_gate", "the game is untouched")
