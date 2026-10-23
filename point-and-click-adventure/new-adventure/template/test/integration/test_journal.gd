extends GutTest
## The journal: older saves gain its fields, the runner notes the cutscenes
## seen, a memory's still is kept once, the page lists what was seen and
## learned under the hero's name, and watching again changes nothing: not
## GameState, not the room, not where the hero stands.

const DIR := "user://test-journal"

var _directory := ""
var _listen: Callable


func before_each() -> void:
	_directory = Journal.directory
	Journal.directory = DIR
	_clear()
	GameState.reset()
	_listen = func(_id: String, _speaker: String, _text: String) -> void: Say.skip.call_deferred()
	Say.line_started.connect(_listen)


func after_each() -> void:
	Engine.time_scale = 1.0
	if Menus.screen:
		Menus.screen.close()
	await wait_until(func() -> bool: return Cutscenes.current == null and Interaction.locked == 0, 30.0)
	Say.line_started.disconnect(_listen)
	Cutscenes.clear_fade()
	if Rooms.current:
		Rooms.clear()
	_clear()
	Journal.directory = _directory
	GameState.reset()


func _clear() -> void:
	if DirAccess.dir_exists_absolute(DIR):
		for file in DirAccess.get_files_at(DIR):
			DirAccess.remove_absolute(DIR.path_join(file))


func test_version_2_saves_gain_the_journal_fields() -> void:
	var data := Saves.migrate({"save_version": 2, "flags": {}, "memories": ["greybox_window"]})
	assert_eq(int(data["save_version"]), GameState.SAVE_VERSION)
	assert_eq(data["facts"], [])
	assert_eq(data["cutscenes_seen"], [])


func test_the_runner_notes_the_cutscenes_seen() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	await Cutscenes.play(StepsCutscene.new(&"test_scene", func(c: CutsceneSteps) -> void: await c.wait(0.1)))
	await Cutscenes.play(StepsCutscene.new(&"", func(c: CutsceneSteps) -> void: await c.wait(0.1)))
	assert_eq(Array(GameState.cutscenes_seen), [&"test_scene"], "scenes without a name are not kept")


func test_a_memory_still_is_kept_once() -> void:
	var first := Image.create(64, 36, false, Image.FORMAT_RGB8)
	first.fill(Color.WHITE)
	var second := Image.create(64, 36, false, Image.FORMAT_RGB8)
	second.fill(Color.BLACK)
	Journal.capture(&"test_memory", first)
	Journal.capture(&"test_memory", second)
	var kept := Journal.still(&"test_memory").get_image()
	assert_eq(kept.get_size(), Journal.STILL)
	assert_gt(kept.get_pixel(10, 10).v, 0.9, "the first sight is the one kept")


func test_the_journal_lists_what_was_seen_and_learned() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	GameState.remember(&"greybox_window")
	GameState.remember(&"test_memory_without_a_page")
	GameState.learn(&"greybox_mercy")
	GameState.saw_cutscene(&"greybox_opening")
	assert_eq(Journal.memories(), [&"greybox_window"] as Array[StringName])
	assert_eq(Journal.rewatchable(), [&"greybox_opening"] as Array[StringName])
	await Menus.choose(&"journal")
	var journal := Menus.screen as JournalScreen
	var texts := _texts(journal)
	for expected in ["Who am I?", "The chapel at noon", "Watch again", "The land beyond the gate", "Name: Hero"]:
		assert_has(texts, expected)
	assert_true(texts.any(func(t: String) -> bool: return t.begins_with("The word that opens the gate")), "the fact learned")
	await journal.show_memory(&"greybox_window")
	var line := journal.page().get_node("Line") as Label
	assert_string_contains(line.text, "full of light", "the memory's line")


func test_watching_again_changes_nothing() -> void:
	Engine.time_scale = 8.0
	await Rooms.goto(&"greybox_courtyard", &"default", &"none")
	Rooms.player.global_position = Vector2(700, 950)
	GameState.saw_cutscene(&"greybox_vista")
	GameState.saw_cutscene(&"greybox_window")
	GameState.set_flag(&"test_mark", "before")
	var before := GameState.to_dict()
	before.erase("play_seconds")
	for id in [&"greybox_vista", &"greybox_window"]:
		await Journal.rewatch(id)
		await wait_until(func() -> bool: return Interaction.locked == 0, 10.0)
		var after := GameState.to_dict()
		after.erase("play_seconds")
		assert_eq(after, before, "%s left GameState as it was" % id)
		assert_eq(Rooms.current.room_id, &"greybox_courtyard", "%s came back to the courtyard" % id)
		assert_eq(Rooms.player.global_position, Vector2(700, 950), "%s left the hero where they stood" % id)
		assert_eq(Cutscenes.fade_amount(), 0.0)


func _texts(node: Node) -> Array[String]:
	var texts: Array[String] = []
	for label in node.find_children("*", "Label", true, false):
		texts.append((label as Label).text)
	return texts
