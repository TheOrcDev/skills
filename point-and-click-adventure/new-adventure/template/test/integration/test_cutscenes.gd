extends GutTest
## The cutscene runner: steps run in order with input locked
## and the letterbox bars in, and a skip makes the step under way and every
## later one finish at once, leaving the world as a watched run does.

const DESTINATION := Vector2(1400, 1010)


class Walkabout extends Cutscene:
	var reached: Array[String] = []

	func run(c: CutsceneSteps) -> void:
		reached.append("start")
		await c.walk(Rooms.player, DESTINATION)
		reached.append("walked")
		await c.say(&"greybox", &"altar_look")
		await c.wait(1.0)
		GameState.set_flag(&"walkabout_done")
		await c.fade(0.6, 0.5)
		await c.fade(0.0, 0.5)
		reached.append("end")


func before_each() -> void:
	GameState.reset()
	await Rooms.goto(&"greybox_chapel", &"default", &"none")


func after_each() -> void:
	await wait_until(func() -> bool: return Cutscenes.current == null and Interaction.locked == 0, 30.0)
	Rooms.clear()
	GameState.reset()


func _end() -> Vector2:
	return NavigationServer2D.map_get_closest_point(Rooms.player.get_world_2d().navigation_map, DESTINATION)


func test_a_watched_cutscene_runs_its_steps_with_input_locked() -> void:
	var scene := Walkabout.new()
	var locked := [false]
	var bars := [0.0]
	var watch := func() -> void:
		locked[0] = locked[0] or Interaction.locked > 0
		bars[0] = maxf(bars[0], Cutscenes.letterbox.amount)
	get_tree().process_frame.connect(watch)
	await Cutscenes.play(scene)
	get_tree().process_frame.disconnect(watch)
	assert_eq(scene.reached, ["start", "walked", "end"] as Array[String])
	assert_true(locked[0], "input was locked")
	assert_gt(bars[0], 0.9, "the bars came in")
	assert_eq(Interaction.locked, 0, "and input is free again")
	assert_true(GameState.get_flag(&"walkabout_done"))
	assert_lt(Rooms.player.global_position.distance_to(_end()), 2.0)


func test_a_skipped_cutscene_ends_as_a_watched_one() -> void:
	var scene := Walkabout.new()
	var started := Time.get_ticks_msec()
	Cutscenes.play(scene)
	await wait_seconds(0.3)
	Cutscenes.skip()
	await wait_for_signal(Cutscenes.finished, 5.0)
	assert_lt(Time.get_ticks_msec() - started, 2500, "skipping is quick")
	assert_eq(scene.reached, ["start", "walked", "end"] as Array[String], "the script ran to its end")
	assert_true(GameState.get_flag(&"walkabout_done"), "its logic still ran")
	assert_lt(Rooms.player.global_position.distance_to(_end()), 2.0, "the hero stands where the walk ends")
	assert_false(Say.fast_forward, "lines hold again afterwards")
	assert_eq(Interaction.locked, 0)


## The world a run leaves: every saved part of GameState but play time, and
## where the hero stands.
func _world() -> Dictionary:
	var state := GameState.to_dict()
	state.erase("play_seconds")
	state["unknown_at"] = Rooms.player.global_position.round()
	return state


func test_skipped_and_watched_runs_leave_the_same_world() -> void:
	await Cutscenes.play(Walkabout.new())
	var watched := _world()
	GameState.reset()
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	Cutscenes.play(Walkabout.new())
	await wait_seconds(0.3)
	Cutscenes.skip()
	await wait_until(func() -> bool: return Cutscenes.current == null, 5.0)
	assert_eq(_world(), watched)

