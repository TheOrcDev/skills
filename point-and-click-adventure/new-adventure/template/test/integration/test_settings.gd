extends GutTest
## Settings: each applies as soon as it is set, they are
## written to their file and read back, and Reduce camera motion turns the
## close-up push and the vision drift into still crossfades.

const PATH := "user://test-settings-roundtrip.cfg"

var _path := ""


func before_each() -> void:
	_path = Settings.path
	Settings.path = PATH
	Settings.reset()


func after_each() -> void:
	if Closeups.current:
		await Closeups.close()
	await wait_until(func() -> bool: return Interaction.locked == 0, 10.0)
	Rooms.clear()
	Settings.reset()
	await wait_process_frames(1)
	DirAccess.remove_absolute(PATH)
	Settings.path = _path
	Settings.load_settings()


func test_settings_are_written_and_read_back() -> void:
	Settings.text_speed = 1.5
	Settings.subtitles = false
	Settings.voice_volume = 0.25
	await wait_process_frames(2)
	var file := ConfigFile.new()
	assert_eq(file.load(PATH), OK, "written at the end of the frame")
	assert_eq(file.get_value(Settings.SECTION, "text_speed"), 1.5)
	assert_eq(file.get_value(Settings.SECTION, "subtitles"), false)
	file.set_value(Settings.SECTION, "subtitle_size", 1.5)
	file.set_value(Settings.SECTION, "reduce_flashing", true)
	file.save(PATH)
	Settings.load_settings()
	assert_eq(Settings.subtitle_size, 1.5)
	assert_true(Settings.reduce_flashing)
	assert_true(Flashback.reduce_flashing, "applied as it was read")
	assert_eq(Settings.text_speed, 1.5, "the rest of the file still holds")


func test_lines_follow_text_speed_and_subtitle_settings() -> void:
	var text := "A line long enough to stay up for a few seconds."
	var normal := Say.line_seconds(text)
	Settings.text_speed = 2.0
	assert_almost_eq(Say.line_seconds(text), normal / 2.0, 0.001)
	Settings.subtitles = false
	Settings.subtitle_size = 1.5
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	var shown := []
	var listen := func(_id: String, _speaker: String, _text: String) -> void:
		shown.append([Say.subtitle.visible, Say.subtitle.get_theme_font_size(&"font_size")])
		Say.skip.call_deferred()
	Say.line_started.connect(listen)
	await Say.line(&"greybox", &"altar_look")
	Say.line_started.disconnect(listen)
	assert_false(shown.is_empty())
	assert_eq(shown[0], [false, 54], "hidden, and drawn at 1.5× when shown")


func test_volumes_drive_their_buses() -> void:
	var bus := AudioServer.get_bus_index(&"Voice")
	var made := bus < 0
	if made:
		AudioServer.add_bus()
		bus = AudioServer.get_bus_count() - 1
		AudioServer.set_bus_name(bus, &"Voice")
	Settings.voice_volume = 0.5
	assert_almost_eq(AudioServer.get_bus_volume_linear(bus), 0.5, 0.001)
	if made:
		AudioServer.remove_bus(bus)


func test_render_1080p_switches_how_the_game_is_drawn() -> void:
	Settings.render_1080p = true
	assert_eq(get_tree().root.content_scale_mode, Window.CONTENT_SCALE_MODE_VIEWPORT)
	Settings.render_1080p = false
	assert_eq(get_tree().root.content_scale_mode, Window.CONTENT_SCALE_MODE_CANVAS_ITEMS)


func test_reduce_camera_motion_keeps_the_camera_still() -> void:
	Settings.reduce_camera_motion = true
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	var altar := Rooms.current.hotspots.get_node("Altar") as Hotspot
	var closeup := Closeup.new()
	var hotspots := Node2D.new()
	hotspots.name = "Hotspots"
	closeup.add_child(hotspots)
	Closeups.open_node(closeup, altar)
	await wait_seconds(Closeups.SECONDS * 0.5)
	assert_null(Rooms.current.get_viewport().get_camera_2d(), "no camera push into a close-up")
	assert_eq(closeup.scale, Vector2.ONE, "the close-up crossfades in full screen")
	await wait_for_signal(Closeups.opened, 5.0)
	await Closeups.close()
	var room := Rooms.current
	Flashback.vision(&"test_memory", room, altar.focus_point(), func(c: CutsceneSteps) -> void:
		await c.wait(0.2))
	await wait_seconds(1.5)
	assert_null(room.get_viewport().get_camera_2d(), "no drift during a vision")
	await wait_for_signal(Flashback.vision_finished, 15.0)
