extends GutTest
## The hero drawn from their sprites (the stand-in, or the painted set): a
## complete set of monochrome frames with anchors, walking with planted feet at
## the frames' ground speed, mirroring to face left, and eyes that follow the
## anchors.

const SPRITES := "res://content/characters/hero/hero_sprites.tres"
const ANCHORS: Array[StringName] = [&"head", &"eye_l", &"eye_r", &"shoulder_l", &"shoulder_r", &"back", &"hand_l", &"hand_r", &"feet"]

var _hero: Actor
var _body: HeroBody


func before_each() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	_hero = Rooms.player
	_body = _hero.get_node("Body") as HeroBody


func after_each() -> void:
	Engine.time_scale = 1.0
	Rooms.clear()


func test_every_animation_has_mask_frames_and_anchors() -> void:
	var sprites := load(SPRITES) as CharacterSprites
	for base in ["idle", "walk", "look_around", "talk_a", "talk_b", "fidget_a", "fidget_b", "pickup_low", "pickup_high"]:
		for dir in ["r", "u", "d"]:
			var anim := StringName("%s_%s" % [base, dir])
			assert_true(sprites.frames.has_animation(anim), "%s exists" % anim)
			var count := sprites.frames.get_frame_count(anim)
			assert_gt(count, 0, "%s has frames" % anim)
			for anchor_name in ANCHORS:
				assert_eq((sprites.anchors[anim][anchor_name] as PackedVector2Array).size(), count, "%s: one %s per frame" % [anim, anchor_name])
			assert_eq((sprites.eyes[anim] as PackedByteArray).size(), count, "%s: eye flags per frame" % anim)
			var frame := sprites.frames.get_frame_texture(anim, 0) as AtlasTexture
			assert_eq(Vector2i(frame.get_size()), sprites.frame_size, "%s: trimmed frames keep the full frame size" % anim)
			var expected := Image.FORMAT_LA8 if sprites.shaded else Image.FORMAT_L8
			var image := frame.atlas.get_image()
			assert_true(image.get_format() == expected or image.is_compressed(), "%s: monochrome or GPU-compressed, never raw RGBA" % anim)
	assert_false(sprites.frames.get_animation_loop(&"look_around_r"), "the look-around is a one-shot")
	assert_between(float(sprites.ground_speed[&"walk_r"]), 250.0, 450.0, "a plausible rendered ground speed")


func test_walking_moves_one_frame_of_ground_per_new_frame() -> void:
	_hero.global_position = Vector2(700, 1000)
	await wait_physics_frames(2)
	_hero.walk_to(Vector2(1400, 1000))
	var xs: Array[float] = []
	var sample := func() -> void: xs.append(_hero.global_position.x)
	get_tree().physics_frame.connect(sample)
	await wait_seconds(1.0)
	get_tree().physics_frame.disconnect(sample)
	var expected := _body.ground_speed() * _hero.scale.y / _body.frame_rate()
	var moves := 0
	for i in range(1, xs.size()):
		var dx := xs[i] - xs[i - 1]
		if dx != 0.0:
			moves += 1
			assert_almost_eq(dx, expected, 0.5, "each step covers one frame of ground")
	assert_lt(moves, xs.size() / 2, "still between new frames")
	# One step per walk frame: 8 a second for an 8 fps walk.
	var rate := _body.frame_rate()
	assert_between(float(moves), rate - 2.0, rate + 2.0, "a step for each walk frame, %d a second" % rate)
	assert_eq(_body.sprite.animation, &"walk_r")
	_hero.stop()


func test_vertical_walking_is_slower_than_horizontal() -> void:
	_hero.global_position = Vector2(900, 930)
	await wait_physics_frames(2)
	_hero.walk_to(Vector2(900, 1070))
	await wait_physics_frames(30)
	var down := _hero.global_position.y - 930.0
	_hero.stop()
	_hero.global_position = Vector2(700, 1000)
	await wait_physics_frames(2)
	_hero.walk_to(Vector2(1400, 1000))
	await wait_physics_frames(30)
	var across := _hero.global_position.x - 700.0
	_hero.stop()
	assert_gt(down, 0.0)
	assert_lt(down, across * 0.8, "depth covers less of the screen")


func test_facing_left_mirrors_the_body_and_its_anchors() -> void:
	_hero.face(AnimNames.Dir.R)
	await wait_process_frames(2)
	var feet_x := _hero.global_position.x
	assert_gt(_body.to_global(_body.anchor(&"eye_r")).x, feet_x + 10.0, "eyes ahead when facing right")
	_hero.face(AnimNames.Dir.L)
	await wait_process_frames(2)
	assert_eq(_body.sprite.animation, &"idle_r", "left reuses the right-facing frames")
	assert_eq(_body.scale.x, -1.0)
	assert_lt(_body.to_global(_body.anchor(&"eye_r")).x, feet_x - 10.0, "eyes ahead when facing left")
	assert_true((_body.sprite.material as ShaderMaterial).get_shader_parameter(&"mirrored"), "the rim light knows")


func test_eyes_show_only_when_they_face_the_camera() -> void:
	var eye_l := _body.get_node("EyeL") as Sprite2D
	var eye_r := _body.get_node("EyeR") as Sprite2D
	_hero.face(AnimNames.Dir.D)
	await wait_process_frames(2)
	assert_true(eye_l.visible and eye_r.visible, "both eyes facing the camera")
	_hero.face(AnimNames.Dir.U)
	await wait_process_frames(2)
	assert_false(eye_l.visible or eye_r.visible, "no eyes from behind")
	_hero.face(AnimNames.Dir.R)
	await wait_process_frames(2)
	assert_ne(eye_l.visible, eye_r.visible, "one eye in profile")
	assert_eq(eye_r.position, _body.anchor(&"eye_r"), "eyes sit on their anchors")


func test_speaking_pulses_the_eyes() -> void:
	_hero.set_speaking(true)
	await wait_seconds(0.5)
	assert_gt(_body.voice_level, 0.2, "voice stand-in while speaking")
	_hero.set_speaking(false)
	await wait_seconds(0.6)
	assert_almost_eq(_body.voice_level, 0.0, 0.01, "quiet afterwards")


func test_one_shot_finishes_and_returns_to_idle() -> void:
	Engine.time_scale = 8.0
	_hero.face(AnimNames.Dir.D)
	await _hero.play(&"look_around")
	assert_eq(_body.sprite.animation, &"idle_d")
	assert_true(_body.sprite.is_playing())


func test_walking_fires_a_step_on_each_heel_strike() -> void:
	var sprites := load(SPRITES) as CharacterSprites
	for dir in ["r", "u", "d"]:
		var anim := StringName("walk_%s" % dir)
		var steps := 0
		for frame in sprites.frames.get_frame_count(anim):
			steps += sprites.events_at(anim, frame).count(&"step")
		assert_eq(steps, 2, "%s has a step for each foot" % anim)
	var heard := []
	var listen := func(anim: StringName, event: StringName) -> void: heard.append([anim, event])
	_body.animation_event.connect(listen)
	_hero.global_position = Vector2(700, 1000)
	await wait_physics_frames(2)
	_hero.walk_to(Vector2(1500, 1000))
	await wait_seconds(1.0)
	_hero.stop()
	_body.animation_event.disconnect(listen)
	var steps_heard := heard.filter(func(e: Array) -> bool: return e[1] == &"step").size()
	assert_between(steps_heard, 2, 3, "about two steps a second")


func test_a_held_item_follows_the_hand() -> void:
	_hero.face(AnimNames.Dir.R)
	await wait_process_frames(2)
	var item := _body.hold(Effects.soft_dot())
	assert_eq(item.position, _body.anchor(&"hand_r"), "in the right hand")
	assert_gt(item.get_index(), _body.sprite.get_index(), "in front of the hero")
	_hero.walk_to(_hero.global_position + Vector2(400, 0))
	await wait_seconds(0.4)
	assert_eq(item.position, _body.anchor(&"hand_r"), "still in hand as the walk frames change")
	_hero.stop()
	_hero.face(AnimNames.Dir.U)
	await wait_process_frames(2)
	assert_lt(item.get_index(), _body.sprite.get_index(), "behind the hero when they face away")
	_body.release()
	await wait_process_frames(1)
	assert_false(is_instance_valid(item), "released")
	assert_null(_body.held)


func test_speaking_while_standing_plays_the_talk_loops_in_turn() -> void:
	_hero.face(AnimNames.Dir.D)
	_hero.set_speaking(true)
	await wait_process_frames(2)
	assert_eq(_body.sprite.animation, &"talk_a_d", "first line: right-hand talk")
	_hero.set_speaking(false)
	await wait_process_frames(2)
	assert_eq(_body.sprite.animation, &"idle_d", "idle between lines")
	_hero.set_speaking(true)
	await wait_process_frames(2)
	assert_eq(_body.sprite.animation, &"talk_b_d", "second line: both hands")
	_hero.walk_to(_hero.global_position + Vector2(300, 0))
	await wait_physics_frames(3)
	assert_eq(_body.sprite.animation, &"walk_r", "walking wins over talking")
	_hero.stop()
	await wait_process_frames(2)
	assert_eq(_body.sprite.animation, &"talk_b_r", "still talking once the hero stops")
	_hero.set_speaking(false)


func test_a_walk_interrupts_a_one_shot_and_releases_its_caller() -> void:
	var finished := [false]
	var run := func() -> void:
		await _hero.play(&"look_around")
		finished[0] = true
	run.call()
	await wait_process_frames(2)
	assert_false(_hero.is_idle(), "busy during the one-shot")
	_hero.walk_to(_hero.global_position + Vector2(300, 0))
	await wait_process_frames(2)
	assert_true(finished[0], "the caller of play() is released")
	assert_eq(_body.sprite.animation, &"walk_r")
	_hero.stop()
	await wait_process_frames(1)
	assert_true(_hero.is_idle())


func test_idle_fidgets_play_now_and_then_but_not_while_busy() -> void:
	var fidgets := _hero.get_node("IdleFidgets") as IdleFidgets
	_hero.face(AnimNames.Dir.D)
	fidgets.interval = Vector2(0.2, 0.3)
	await wait_seconds(0.6)
	var playing := String(_body.sprite.animation)
	assert_true(playing.begins_with("fidget_") or playing.begins_with("look_around"), "a fidget after a while idle, got %s" % playing)
	_hero.walk_to(_hero.global_position + Vector2(200, 0))
	await wait_physics_frames(3)
	assert_eq(_body.sprite.animation, &"walk_r", "a walk cuts the fidget short")
	_hero.stop()
	Interaction.locked += 1
	fidgets.interval = Vector2(0.2, 0.3)
	await wait_seconds(0.6)
	Interaction.locked -= 1
	assert_true(String(_body.sprite.animation).begins_with("idle_"), "no fidgets while a cutscene or line holds the input")


func test_pickups_grab_once_then_return_to_idle() -> void:
	Engine.time_scale = 8.0
	for base in [&"pickup_low", &"pickup_high"]:
		var grabs := []
		var listen := func(_anim: StringName, event: StringName) -> void:
			if event == &"grab":
				grabs.append(base)
		_body.animation_event.connect(listen)
		_hero.face(AnimNames.Dir.R)
		await _hero.play(base)
		_body.animation_event.disconnect(listen)
		assert_eq(grabs.size(), 1, "%s grabs exactly once" % base)
		assert_eq(_body.sprite.animation, &"idle_r", "back to idle after %s" % base)

