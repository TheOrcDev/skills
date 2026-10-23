extends GutTest
## The greybox vista: the zoom stack pulls back at constant perceived speed
## about one fixed point, stays inside the outer ring, hands detail from ring to
## ring, and the opening, played by the cutscene runner, ends on black with its
## title shown. Holding Skip or Esc skips it; a short press does not.

const SCENE := "res://content/cutscenes/greybox_vista/greybox_vista.tscn"
const OPENING := preload("res://content/cutscenes/greybox_vista/opening.gd")
const VISTA := preload("res://content/cutscenes/greybox_vista/greybox_vista.tscn")

var _cutscene: Node2D
var _reveal: Reveal


func before_each() -> void:
	_cutscene = (load(SCENE) as PackedScene).instantiate()
	add_child_autofree(_cutscene)
	_reveal = _cutscene.get_node("Reveal") as Reveal
	# Only for the zoom maths: its camera must never take the view.
	_reveal.camera.enabled = false


func after_each() -> void:
	Engine.time_scale = 1.0
	await wait_until(func() -> bool: return Cutscenes.current == null, 10.0)
	Cutscenes.clear_fade()
	Settings.reduce_camera_motion = false
	if Rooms.current:
		Rooms.clear()
	GameState.reset()


func test_zoom_moves_in_log_space() -> void:
	assert_almost_eq(_reveal.zoom_at(0.0), _reveal.start_zoom, 0.0001)
	assert_almost_eq(_reveal.zoom_at(1.0), _reveal.end_zoom, 0.0001)
	assert_almost_eq(_reveal.zoom_at(0.5), sqrt(_reveal.start_zoom * _reveal.end_zoom), 0.0001, "halfway is the geometric mean")
	var ratio_a := _reveal.zoom_at(0.25) / _reveal.zoom_at(0.0)
	var ratio_b := _reveal.zoom_at(1.0) / _reveal.zoom_at(0.75)
	assert_almost_eq(ratio_a, ratio_b, 0.0001, "equal steps zoom by equal factors")


func test_pull_back_scales_about_a_fixed_point_inside_the_outer_ring() -> void:
	var pivot := _reveal.pivot()
	var screen_center := _reveal.view_size / 2.0
	var first := (pivot - _reveal.center_at(0.0)) * _reveal.zoom_at(0.0)
	for i in 21:
		var p := i / 20.0
		var zoom := _reveal.zoom_at(p)
		var center := _reveal.center_at(p)
		assert_almost_eq((pivot - center) * zoom, first, Vector2.ONE * 0.01, "the pivot keeps its screen place at %.2f" % p)
		var half := _reveal.view_size / (2.0 * zoom)
		assert_true(center.x - half.x >= -0.01 and center.x + half.x <= _reveal.world_size.x + 0.01, "inside ring 0 across at %.2f" % p)
		assert_true(center.y - half.y >= -0.01 and center.y + half.y <= _reveal.world_size.y + 0.01, "inside ring 0 down at %.2f" % p)
	assert_true(absf(first.x) < screen_center.x and absf(first.y) < screen_center.y, "the pivot is on screen")


func test_inner_rings_hand_over_detail() -> void:
	assert_eq(_reveal.ring_count(), 2)
	_reveal.progress = 0.0
	assert_true(_reveal.ring(1).visible, "close up, the inner ring adds detail")
	_reveal.progress = 1.0
	assert_false(_reveal.ring(1).visible, "pulled back, ring 0 alone")
	assert_true(_reveal.ring(0).visible)
	assert_eq(_reveal.camera.zoom, Vector2.ONE * _reveal.end_zoom)


func test_the_hero_keeps_their_vista_scale_when_facing() -> void:
	var hero := _cutscene.get_node("Reveal/Hero") as HeroBody
	var size := absf(hero.scale.y)
	assert_lt(size, 1.0, "the hero is smaller in the vista than in rooms")
	hero.play_animation(&"idle_r", true)
	assert_almost_eq(hero.scale.x, -size, 0.0001, "mirroring keeps the scale")
	hero.play_animation(&"idle_r", false)
	assert_almost_eq(hero.scale.x, size, 0.0001)


func test_the_opening_plays_to_black_and_finishes() -> void:
	Engine.time_scale = 8.0
	var opening := OPENING.new()
	watch_signals(Cutscenes)
	var peak := [0.0]
	var progress := [-1.0]
	var track := func() -> void:
		if is_instance_valid(opening.stage):
			peak[0] = maxf(peak[0], (opening.stage.get_node("Title/Card") as Control).modulate.a)
			progress[0] = opening.stage.reveal.progress
	get_tree().process_frame.connect(track)
	await Cutscenes.play(opening)
	get_tree().process_frame.disconnect(track)
	assert_gt(peak[0], 0.9, "the title card showed")
	assert_signal_emitted(Cutscenes, "finished")
	assert_eq(progress[0], 1.0, "pulled all the way back")


func test_holding_skip_fast_forwards_the_opening() -> void:
	var opening := OPENING.new()
	var progress := [-1.0]
	Cutscenes.finished.connect(func(_id: StringName) -> void: progress[0] = opening.stage.reveal.progress, CONNECT_ONE_SHOT)
	var started := Time.get_ticks_msec()
	Cutscenes.play(opening)
	await wait_process_frames(2)
	Cutscenes.skip_button.press()
	await wait_until(func() -> bool: return Cutscenes.current == null, 5.0)
	assert_lt(Time.get_ticks_msec() - started, 4000, "skipped well under its 14 s")
	assert_eq(progress[0], 1.0, "a skipped opening ends where a watched one does")


func test_a_short_press_does_not_skip_but_esc_does() -> void:
	Cutscenes.play(OPENING.new())
	await wait_process_frames(2)
	var skipped := [false]
	Cutscenes.current.skipped.connect(func() -> void: skipped[0] = true)
	Cutscenes.skip_button.press()
	await wait_seconds(SkipButton.HOLD_SECONDS * 0.5)
	Cutscenes.skip_button.release()
	await wait_seconds(SkipButton.HOLD_SECONDS)
	assert_false(skipped[0], "let go too soon")
	var esc := InputEventAction.new()
	esc.action = &"ui_cancel"
	esc.pressed = true
	Input.parse_input_event(esc)
	await wait_process_frames(2)
	assert_true(skipped[0], "Esc skips")
	await wait_until(func() -> bool: return Cutscenes.current == null, 5.0)


## The world a reveal in the middle of play leaves behind.
func _after_reveal() -> Dictionary:
	await wait_process_frames(2)
	return {
		"room": Rooms.current.room_id,
		"fade": Cutscenes.fade_amount(),
		"grade": Flashback.get_grade(),
		"view": Rooms.current.get_viewport().get_canvas_transform(),
		"memories": Array(GameState.memories),
	}


func test_a_reveal_in_play_returns_to_the_room_and_a_skip_ends_alike() -> void:
	Engine.time_scale = 8.0
	await Rooms.goto(&"greybox_courtyard", &"default", &"none")
	await Cutscenes.play(RevealCutscene.new(&"test_vista", VISTA))
	var watched: Dictionary = await _after_reveal()
	assert_eq(watched["room"], &"greybox_courtyard")
	assert_eq(watched["fade"], 0.0, "the room shows again")
	assert_eq(watched["view"], Transform2D.IDENTITY, "the reveal's camera is gone")
	Cutscenes.play(RevealCutscene.new(&"test_vista", VISTA))
	await wait_process_frames(10)
	Cutscenes.skip()
	await wait_until(func() -> bool: return Cutscenes.current == null, 5.0)
	assert_eq(await _after_reveal(), watched, "a skipped reveal ends as a watched one")


func test_a_memory_vista_plays_under_the_past_grade() -> void:
	Engine.time_scale = 8.0
	await Rooms.goto(&"greybox_courtyard", &"default", &"none")
	var peak := [0.0]
	var track := func() -> void: peak[0] = maxf(peak[0], Flashback.get_grade())
	get_tree().process_frame.connect(track)
	await Cutscenes.play(RevealCutscene.new(&"test_vista", VISTA, &"then"))
	get_tree().process_frame.disconnect(track)
	assert_eq(peak[0], 1.0, "the past's grade while it plays")
	assert_eq(Flashback.get_grade(), 0.0, "the present's again after")
	assert_eq(Array(GameState.memories), [&"test_vista"], "and it is remembered")


func test_reduce_camera_motion_cuts_instead_of_travelling() -> void:
	Engine.time_scale = 8.0
	Settings.reduce_camera_motion = true
	await Rooms.goto(&"greybox_courtyard", &"default", &"none")
	var scene := RevealCutscene.new(&"test_vista", VISTA)
	var zooms := {}
	var track := func() -> void:
		if is_instance_valid(scene.stage):
			zooms[snappedf(scene.stage.reveal.camera.zoom.x, 0.001)] = true
	get_tree().process_frame.connect(track)
	await Cutscenes.play(scene)
	get_tree().process_frame.disconnect(track)
	assert_eq(zooms.size(), 2, "only the close shot and the vista, got %s" % [zooms.keys()])

