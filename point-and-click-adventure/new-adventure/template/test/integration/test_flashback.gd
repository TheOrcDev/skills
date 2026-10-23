extends GutTest
## A flashback vision in the greybox chapel: the past blooms in, holds, drains back,
## and the room, grade, input lock and camera end exactly as they started.

var _era_during_hold: StringName


func before_all() -> void:
	Engine.time_scale = 8.0


func after_all() -> void:
	Engine.time_scale = 1.0


func before_each() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")


func after_each() -> void:
	Rooms.clear()


func test_vision_shows_the_past_then_returns_to_the_present() -> void:
	var room := Rooms.current
	var origin := (room.hotspots.get_node("Window") as Hotspot).focus_point()
	await Flashback.vision(&"test_memory", room, origin, func(c: CutsceneSteps) -> void:
		_era_during_hold = room.era
		assert_true(Interaction.locked > 0, "input is locked during the vision")
		await c.wait(0.5))
	assert_eq(_era_during_hold, &"then", "the past is shown during the hold")
	assert_eq(room.era, &"now", "back in the present afterwards")
	assert_eq(Interaction.locked, 0, "input unlocked")
	assert_false(Flashback.playing)
	assert_null((room.get_node("Layers/Then/Background") as Sprite2D).material, "dissolve material removed")
	assert_false(room.get_node("Layers/Then").visible)
	for node in room.era_nodes() + room.get_node("Layers/Now").get_children():
		assert_eq((node as CanvasItem).modulate.a, 1.0, "%s opacity restored" % node.name)
	await wait_process_frames(2)
	assert_eq(room.get_viewport().get_canvas_transform(), Transform2D.IDENTITY, "drift camera removed")


func test_using_the_window_plays_the_vision() -> void:
	watch_signals(Flashback)
	var skip_lines := func(_id: String, _speaker: String, _text: String) -> void: Say.skip.call_deferred()
	Say.line_started.connect(skip_lines)
	(Rooms.current as Room).call(&"use_window")
	await wait_for_signal(Flashback.vision_finished, 40.0)
	Say.line_started.disconnect(skip_lines)
	assert_signal_emitted(Flashback, "vision_started")
	assert_signal_emitted(Flashback, "vision_finished")
	assert_eq(Rooms.current.era, &"now")
	await wait_until(func() -> bool: return Interaction.locked == 0, 5.0)
	assert_eq(Interaction.locked, 0)


func test_warm_up_draws_the_past_and_puts_everything_back() -> void:
	var room := Rooms.current
	await Flashback.warm_up(room)
	assert_false(room.get_node("Layers/Then").visible, "the past is hidden again")
	assert_null((room.get_node("Layers/Then/Background") as Sprite2D).material, "no dissolve left behind")
	for node in room.era_nodes():
		assert_eq(node.visible, node.is_in_group(&"era_now"), "%s back to its era's visibility" % node.name)


func test_a_fade_waits_for_the_warm_up_while_black() -> void:
	var seen := []
	var step := func(room: Room) -> void:
		seen.append(room.room_id)
		await get_tree().process_frame
	Rooms.while_black.append(step)
	await Rooms.goto(&"greybox_chapel", &"default", &"fade")
	Rooms.while_black.erase(step)
	assert_eq(seen, [&"greybox_chapel"], "steps run once with the new room")
	assert_true(Flashback.warm_up in Rooms.while_black, "the flashback warms up on every faded room change")


func test_the_hero_eyes_flare_as_the_vision_opens_and_settle_after() -> void:
	var body := Rooms.player.get_node("Body") as HeroBody
	var flared := [false]
	var watch := func(_origin: Vector2) -> void: flared[0] = body.eye_state == HeroBody.EyeState.FLARE
	Flashback.vision_started.connect(watch)
	await Flashback.vision(&"test_memory", Rooms.current, Vector2(200, 500), func(c: CutsceneSteps) -> void: await c.wait(0.3))
	Flashback.vision_started.disconnect(watch)
	assert_true(flared[0], "the eyes flare as the past opens")
	await wait_seconds(1.5)
	assert_eq(body.eye_state, HeroBody.EyeState.IDLE, "and settle once it has closed")


func test_the_memory_takes_the_hero_body_as_the_vision_opens() -> void:
	var body := Rooms.player.get_node("Body") as SpriteBody
	var playing := [&""]
	var watch := func(_origin: Vector2) -> void: playing[0] = body.sprite.animation
	Flashback.vision_started.connect(watch)
	await Flashback.vision(&"test_memory", Rooms.current, Vector2(200, 500), func(c: CutsceneSteps) -> void: await c.wait(0.3))
	Flashback.vision_started.disconnect(watch)
	assert_true(String(playing[0]).begins_with("flare_"), "the flare reaction plays, got %s" % playing[0])


func test_a_vision_records_its_memory() -> void:
	GameState.reset()
	await Flashback.vision(&"test_memory", Rooms.current, Vector2(200, 500), func(c: CutsceneSteps) -> void: await c.wait(0.2))
	assert_eq(Array(GameState.memories), [&"test_memory"])
	GameState.reset()


func test_a_skipped_vision_returns_to_the_present_at_once() -> void:
	GameState.reset()
	var room := Rooms.current
	var stood := Rooms.player.global_position
	Flashback.vision(&"test_memory", room, Vector2(200, 500), func(c: CutsceneSteps) -> void: await c.wait(5.0))
	await wait_for_signal(Flashback.vision_started, 5.0)
	await wait_process_frames(3)
	Cutscenes.skip()
	await wait_until(func() -> bool: return not Flashback.playing and Cutscenes.current == null, 3.0)
	assert_false(Flashback.playing, "over at once")
	assert_eq(room.era, &"now", "back in the present")
	assert_false(room.get_node("Layers/Then").visible)
	assert_null((room.get_node("Layers/Then/Background") as Sprite2D).material, "dissolve material removed")
	assert_eq(Rooms.player.global_position, stood, "the hero where they stood")
	assert_eq(Array(GameState.memories), [&"test_memory"], "the memory is still recorded")
	GameState.reset()


func test_a_playable_memory_lets_the_player_act_in_the_past_until_done() -> void:
	GameState.reset()
	var room := Rooms.current
	var exit := room.hotspots.get_node("ExitEast") as Hotspot
	Flashback.enter_memory(&"test_memory", room, Vector2(200, 500), &"test_memory_done")
	await wait_until(func() -> bool: return Flashback.in_memory and Interaction.locked == 0, 15.0)
	assert_eq(room.era, &"then", "the past is up, and the player can act")
	assert_false(exit.is_active(), "no way out of the room meanwhile")
	assert_false(Menus.can_open(), "and no menu, so no save inside the memory")
	GameState.set_flag(&"test_memory_done")
	await wait_until(func() -> bool: return not Flashback.in_memory, 15.0)
	assert_eq(room.era, &"now", "back in the present once done")
	assert_true(exit.is_active(), "the ways out are back")
	assert_eq(Array(GameState.memories), [&"test_memory"])
	GameState.reset()

