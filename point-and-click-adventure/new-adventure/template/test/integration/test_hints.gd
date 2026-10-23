extends GutTest
## Hints: clicking the hero makes them think aloud about the current goal, the
## goal follows GameState progress, and asking again about the same goal gets
## a more direct line. Uses the greybox chain's goals.

const GOALS := "res://content/hints/goals.gd"

var _lines: Array = []
var _listen: Callable


func before_each() -> void:
	GameState.reset()
	_lines.clear()
	_listen = func(id: String, _speaker: String, _text: String) -> void:
		_lines.append(id)
		Say.skip.call_deferred()
	Say.line_started.connect(_listen)
	await Rooms.goto(&"greybox_gate", &"default", &"none")


func after_each() -> void:
	if Closeups.current:
		await Closeups.close()
	await wait_until(func() -> bool: return Interaction.locked == 0 and not Say.speaking, 10.0)
	Say.line_started.disconnect(_listen)
	Rooms.clear()
	GameState.reset()


func test_the_goal_follows_progress() -> void:
	var goals: Array[Dictionary] = (load(GOALS) as GDScript).GOALS
	assert_eq(Hints.current_goal(), &"rag")
	for goal in goals:
		assert_eq(Hints.current_goal(), goal["goal"])
		_complete(goal)
	assert_eq(Hints.current_goal(), &"", "every goal done")


func test_asking_again_gets_more_direct() -> void:
	for i in 3:
		await Hints.ask()
	assert_eq(_lines, ["HINT_RAG_1", "HINT_RAG_2", "HINT_RAG_2"], "the most direct line repeats")
	GameState.set_flag(&"greybox_rag_taken")
	_lines.clear()
	await Hints.ask()
	assert_eq(_lines, ["HINT_WORD_1"], "then the next goal's first line")
	for goal: Dictionary in (load(GOALS) as GDScript).GOALS:
		_complete(goal)
	_lines.clear()
	await Hints.ask()
	assert_eq(_lines, ["HINT_NONE_1"])


func test_every_goal_has_its_lines() -> void:
	var cues := (load(Say.DIALOGUE_PATH % Hints.DIALOGUE) as DialogueResource).get_cues()
	for goal: Dictionary in (load(GOALS) as GDScript).GOALS:
		assert_true(cues.has("%s_1" % goal["goal"]), "%s has a first hint" % goal["goal"])


func _complete(goal: Dictionary) -> void:
	if goal.has("flag"):
		GameState.set_flag(goal["flag"])
	else:
		GameState.remember(goal["memory"])


func test_clicking_the_hero_asks_them() -> void:
	# The legs, where nothing is behind them.
	var on_hero := Rooms.player.global_position + Vector2(0, -40) * Rooms.player.scale.y
	assert_true(Rooms.player.contains_point(on_hero), "a point on the hero's body")
	assert_false(Rooms.player.contains_point(Rooms.player.global_position + Vector2(400, -180)), "and one beside them")
	await Interaction.click_at(on_hero)
	assert_eq(_lines, ["HINT_RAG_1"])


func test_a_hotspot_behind_the_hero_still_takes_the_click() -> void:
	# The hero's head, in front of the notice: the notice opens, no hint.
	Rooms.player.global_position = Vector2(575, 900)
	await wait_physics_frames(2)
	var head := Rooms.player.global_position + Vector2(0, -440) * Rooms.player.scale.y
	assert_true(Rooms.player.contains_point(head), "a point on the hero's head")
	assert_true(Rect2(470, 380, 210, 180).has_point(head), "in front of the notice")
	Interaction.click_at(head)
	await wait_until(func() -> bool: return Closeups.current != null and not Closeups.busy, 10.0)
	assert_not_null(Closeups.current, "the notice took the click")
	assert_eq(_lines, [], "no hint")


func test_a_clue_seen_counts_as_read() -> void:
	Interaction.click_at((Rooms.current.hotspots.get_node("Notice") as Hotspot).focus_point())
	await wait_until(func() -> bool: return Closeups.current != null and not Closeups.busy, 10.0)
	assert_true(GameState.get_flag(&"greybox_notice_read"), "reading the notice at a glance")
