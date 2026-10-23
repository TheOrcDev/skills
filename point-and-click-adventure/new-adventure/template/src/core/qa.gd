extends Node
## Scripted runs for builds and the editor. Run the game with
##   -- --qa=<scenario> --qa-out=/absolute/dir
## (in a browser build, add ?qa=<scenario> to the page URL) and it plays a
## sequence, saves screenshots, prints [qa] PASS/FAIL lines and a RESULT line,
## and quits with exit code 0 on success. Without --qa this node does nothing.
## A scenario named after a part in content/chapters.json plays that part's
## content/story/<part>_playthrough.gd. The other scenarios are in _run().

const TIMEOUT_SECONDS := 60.0
const LONG_TIMEOUT_SECONDS := 150.0
## Scenarios that need the long timeout without the opening.
const LONG_RUNS: Array[String] = ["vista", "journal", "saves", "menus"]
## Scenarios that need longer still, in seconds. A part's playthrough gets
## PART_TIMEOUT.
const PART_TIMEOUT := 900.0
const TIMEOUTS := {"greybox_clip": 360.0, "reveals": 300.0, "toolkit_reel": 360.0, "rooms": 900.0, "title": 150.0, "hero_anims": 300.0, "hero_reel": 300.0, "npc": 120.0}
## Scenarios that start from the opening instead of straight in the first room.
const WITH_OPENING: Array[String] = ["title", "perf", "reduced_motion", "skip", "toolkit_reel"]

var _out_dir := ""
var _scenario := ""
var _args := {}
var _failures: PackedStringArray = []
var _finished := false
var _samples := PackedFloat32Array()
var _gpu_samples := PackedFloat32Array()
var _cpu_samples := PackedFloat32Array()
## Each frame's script time (process and physics), to tell slow scripts from slow drawing.
var _script_samples := PackedFloat32Array()
var _sampling := false
## The step a scenario is on, named in the result if it times out.
var _at := ""


func _ready() -> void:
	var raw := OS.get_cmdline_user_args()
	if OS.has_feature("web"):
		var query = JavaScriptBridge.eval("window.location.search", true)
		if query is String and not query.is_empty():
			for pair in query.trim_prefix("?").split("&"):
				raw.append("--" + pair)
	for arg in raw:
		if arg.begins_with("--"):
			_args[arg.substr(2).get_slice("=", 0)] = arg.get_slice("=", 1) if "=" in arg else "true"
	if not _args.has("qa"):
		set_process(false)
		return
	_scenario = _args["qa"]
	# Scripted runs keep their saves apart from a player's, and run on the
	# default settings whatever the player chose.
	Saves.directory = "user://qa-saves"
	Journal.directory = "user://qa-journal"
	Settings.path = "user://qa-settings.cfg"
	Settings.reset({&"fullscreen": false})
	Menus.enabled = false
	_out_dir = _args.get("qa-out", OS.get_user_data_dir().path_join("qa"))
	DirAccess.make_dir_recursive_absolute(_out_dir)
	var timeout: float = TIMEOUTS.get(_scenario, PART_TIMEOUT if _is_part(_scenario) else LONG_TIMEOUT_SECONDS if _scenario in WITH_OPENING or _scenario in LONG_RUNS else TIMEOUT_SECONDS)
	get_tree().create_timer(timeout, true, false, true).timeout.connect(_finish.bind("timeout"))
	_run.call_deferred(_scenario)


## Scripted runs ignore the real mouse, so a stray click on the window cannot
## send the hero off script (scenarios drive input through Interaction directly).
func _input(event: InputEvent) -> void:
	if not _scenario.is_empty() and event is InputEventMouse:
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	# --force-draw: draw every frame even when other windows cover this one
	# (macOS stops drawing it), so the movie writer never records stale frames.
	if _args.has("force-draw"):
		RenderingServer.force_draw(false)
	if _sampling:
		_samples.append(delta)
		var viewport := get_viewport().get_viewport_rid()
		_cpu_samples.append(RenderingServer.viewport_get_measured_render_time_cpu(viewport) + RenderingServer.get_frame_setup_time_cpu())
		_gpu_samples.append(RenderingServer.viewport_get_measured_render_time_gpu(viewport))
		_script_samples.append((Performance.get_monitor(Performance.TIME_PROCESS) + Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)) * 1000.0)


## Whether a scripted run is playing; it starts straight into the game, without
## the start screen, unless it is the start screen's own run.
func running() -> bool:
	return not _scenario.is_empty() and _scenario != "title"


## Room scenarios start straight in the first room, without the opening.
func skips_opening() -> bool:
	return not _scenario.is_empty() and not _scenario in WITH_OPENING

const PLAYTHROUGH := "res://content/story/%s_playthrough.gd"


func _run(scenario: String) -> void:
	match scenario:
		"rooms":
			await _rooms()
		"npc":
			await _npc()
		"hero_anims":
			await _hero_anims()
		"hero_reel":
			await _hero_reel()
		"saves":
			await _saves()
		"reduced_motion":
			await _reduced_motion()
		"title":
			await _title()
		"menus":
			await _menus()
		"skip":
			await _skip()
		"perf":
			await _perf()
		"greybox_clip":
			await _part(&"greybox", false)
		"vista":
			await _vista()
		"reveals":
			await _reveals()
		"journal":
			await _journal()
		"toolkit_reel":
			await _toolkit_reel()
		"voice":
			await _voice()
		_:
			if _is_part(scenario):
				await _part(StringName(scenario))
			else:
				_failures.append("unknown scenario %s" % scenario)
	_finish("done")


## Whether `scenario` names a part that has a playthrough script.
func _is_part(scenario: String) -> bool:
	return not Chapters.part(StringName(scenario)).is_empty() and ResourceLoader.exists(PLAYTHROUGH % scenario)


## Plays a part's playthrough (content/story/<part>_playthrough.gd) from a fresh
## game state, with screenshots at its main moments. With `skip_lines` off the
## lines play at reading pace, for the movie writer:
##   --write-movie <file.avi> --fixed-fps 30 -- --qa=greybox_clip --force-draw
func _part(part_id: StringName, skip_lines := true) -> void:
	while Rooms.current == null:
		await get_tree().process_frame
	await _settle()
	GameState.reset()
	Rooms.player.get_node("IdleFidgets").set_process(skip_lines)
	var run := (load(PLAYTHROUGH % part_id) as GDScript).new(get_tree(), _check, _shot if skip_lines else Callable()) as Playthrough
	run.skip_lines = skip_lines
	await run.run()
	if not skip_lines:
		await get_tree().create_timer(2.0).timeout


## Waits for the start room to finish loading, skipping its arrival line, then
## switches to `room_id`.
func _enter(room_id: StringName) -> void:
	while Rooms.current == null:
		await get_tree().process_frame
	await _settle()
	if Rooms.current.room_id != room_id:
		await Rooms.goto(room_id, &"default", &"none")


## Every one of the hero's actions in every direction, in the start room: each
## is shot at its middle drawing and must play to its end. Also how much video
## memory the hero's sheets take.
func _hero_anims() -> void:
	await _enter(Chapters.parts()[0]["start"])
	var hero := Rooms.player
	hero.global_position = Rooms.current.marker_position(&"default")
	var body := hero.get_node("Body") as SpriteBody
	for facing: Array in [[AnimNames.Dir.R, "r"], [AnimNames.Dir.D, "d"], [AnimNames.Dir.U, "u"]]:
		hero.face(facing[0])
		await get_tree().create_timer(0.6).timeout
		await _shot("%s_idle" % facing[1])
		for base: StringName in [&"talk_a", &"talk_b", &"use", &"give", &"pickup_low", &"pickup_high", &"look_around", &"fidget_a", &"fidget_b", &"flare"]:
			_mark("%s %s" % [base, facing[1]])
			var anim := StringName("%s_%s" % [base, facing[1]])
			_check(body.has_animation(anim), "the hero has %s" % anim)
			var frames := body.sprite.sprite_frames
			var middle := frames.get_frame_count(anim) / 2 if frames.has_animation(anim) else 0
			var shot := [false]
			var on_frame := func() -> void:
				if not shot[0] and body.sprite.animation == anim and body.sprite.frame >= middle:
					shot[0] = true
					_shot("%s_%s" % [facing[1], base])
			body.frame_shown.connect(on_frame)
			if base in [&"talk_a", &"talk_b"]:
				body.play_animation(anim, false)
				await get_tree().create_timer(frames.get_frame_count(anim) / frames.get_animation_speed(anim) + 0.2).timeout
				hero.face(facing[0])
			else:
				await hero.play(base)
			body.frame_shown.disconnect(on_frame)
			_check(shot[0], "%s played past its middle" % anim)
	# The sheets' own data; Godot's monitor reads about 1.4 times this.
	var bytes := 0
	var seen := {}
	for anim in body.sprites.frames.get_animation_names():
		var atlas := (body.sprites.frames.get_frame_texture(anim, 0) as AtlasTexture).atlas
		if not seen.has(atlas):
			seen[atlas] = true
			bytes += atlas.get_image().get_data().size()
	print("[qa] the hero's sheets: %.1f MiB of texture data, %d animations" % [bytes / 1048576.0, body.sprites.frames.get_animation_names().size()])
	_check(bytes > 0 and bytes < 128 * 1048576, "the hero's frames fit 128 MiB")


## The hero as the player sees them, for the screen recording: walks in every
## direction across the start room, then talks, uses, gives, picks up low and
## high, looks around and flares. Record with
##   --write-movie <file.avi> --fixed-fps 30 -- --qa=hero_reel --force-draw
func _hero_reel() -> void:
	await _enter(Chapters.parts()[0]["start"])
	var hero := Rooms.player
	var body := hero.get_node("Body") as SpriteBody
	hero.get_node("IdleFidgets").set_process(false)
	hero.global_position = Vector2(560, 1000)
	hero.face(AnimNames.Dir.R)
	await get_tree().create_timer(1.5).timeout
	for target in [Vector2(1400, 1000), Vector2(1250, 840), Vector2(1000, 1040), Vector2(760, 1000)]:
		await hero.walk_to(target)
		await get_tree().create_timer(0.7).timeout
	for step: Array in [[AnimNames.Dir.D, &"talk_a"], [AnimNames.Dir.D, &"talk_b"], [AnimNames.Dir.R, &"use"], [AnimNames.Dir.R, &"give"],
			[AnimNames.Dir.R, &"pickup_low"], [AnimNames.Dir.D, &"pickup_high"], [AnimNames.Dir.D, &"look_around"], [AnimNames.Dir.R, &"fidget_b"],
			[AnimNames.Dir.D, &"flare"]]:
		hero.face(step[0])
		await get_tree().create_timer(0.5).timeout
		var anim := StringName("%s_%s" % [step[1], "d" if step[0] == AnimNames.Dir.D else "r"])
		if step[1] in [&"talk_a", &"talk_b"]:
			body.play_animation(anim, false)
			await get_tree().create_timer(2.0).timeout
			hero.face(step[0])
		else:
			await hero.play(step[1])
	await hero.walk_to(Vector2(400, 1000))
	await get_tree().create_timer(1.0).timeout


## Shows an NPC (`--npc=<id>`) large over a grey backdrop and plays its
## motions : idle, each talk loop while "speaking", and each
## one-shot, with screenshots at their extremes. With `--room=<id>` it stands
## in that room at the marker named by `--marker` instead.
func _npc() -> void:
	var npc_id: String = _args.get("npc", "warden")
	var npc := (load("res://content/characters/%s/%s.tscn" % [npc_id, npc_id]) as PackedScene).instantiate() as Actor
	var stage := Node2D.new()
	if _args.has("room"):
		await Rooms.goto(StringName(_args["room"]), &"default", &"none")
		npc.position = Rooms.current.marker_position(StringName(_args.get("marker", "default")))
		Rooms.current.actors.add_child(npc)
	else:
		while Rooms.current == null:
			await get_tree().process_frame
		await _settle()
		Rooms.clear()
		var backdrop := ColorRect.new()
		backdrop.color = Color(0.36, 0.37, 0.4)
		backdrop.size = Vector2(1920, 1080)
		stage.add_child(backdrop)
		# The actor sets its own scale, so the stage is what's enlarged.
		var zoom := Node2D.new()
		zoom.scale = Vector2(2.2, 2.2)
		zoom.position = Vector2(960, 1050)
		stage.add_child(zoom)
		zoom.add_child(npc)
		get_tree().root.add_child(stage)
	var body := npc.get_node("Body") as RigBody
	_check(body != null, "%s has a RigBody" % npc_id)
	await get_tree().create_timer(0.6).timeout
	await _shot("%s_idle" % npc_id)
	for anim: String in body.motions:
		var motion: Dictionary = body.motions[anim]
		if anim == "idle":
			continue
		if motion.get("loop", true):
			body.play_animation(StringName(anim), false)
			body.set_speaking(true)
			for i in 3:
				await get_tree().create_timer(0.37).timeout
				await _shot("%s_%s_%d" % [npc_id, anim, i])
			body.set_speaking(false)
		else:
			var length := float(motion.get("length", 1.0))
			body.play_animation(StringName(anim), false)
			for i in 3:
				await get_tree().create_timer(length / 4.0).timeout
				await _shot("%s_%s_%d" % [npc_id, anim, i])
			await body.animation_finished
	npc.queue_free()
	stage.queue_free()


## Tours rooms: `--part=<id>` for a part's rooms with its story
## flags, or `--rooms=a,b`. Each room is shown now and, if it has a past, then,
## and every hotspot that isn't an exit is looked at and must answer with a line.
func _rooms() -> void:
	var rooms: Array[StringName] = []
	if _args.has("rooms"):
		for room in String(_args["rooms"]).split(","):
			rooms.append(StringName(room))
	else:
		var part := Chapters.part(StringName(_args.get("part", Chapters.parts()[0]["id"])))
		Chapters.start_state(part)
		for room: String in part.get("rooms", []):
			rooms.append(StringName(room))
	_check(not rooms.is_empty(), "there are rooms to tour")
	var listen := func(_id: String, _speaker: String, _text: String) -> void:
		Say.skip.call_deferred()
	Say.line_started.connect(listen)
	# The game's own start fades into its first room; let it land first.
	while Rooms.current == null:
		await get_tree().process_frame
	await _settle()
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	for room_id in rooms:
		_mark(String(room_id))
		# Load time (technical-plan §10): from the call to the room's first
		# drawn frame, with its textures uploaded.
		var started := Time.get_ticks_usec()
		await Rooms.goto(room_id, &"default", &"none")
		RenderingServer.force_draw(false)
		var load_ms := (Time.get_ticks_usec() - started) / 1000.0
		await _settle()
		_start_sampling()
		await get_tree().create_timer(1.0).timeout
		var frames := _stop_sampling()
		await _shot("%s_now" % room_id)
		var mib := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0
		print("[qa] VRAM %s %.1f MiB" % [room_id, mib])
		print("[qa] ROOM %s" % JSON.stringify({"room": room_id, "load_ms": snappedf(load_ms, 0.1), "video_mib": snappedf(mib, 0.1), "frames": frames}))
		_check(mib < 400.0, "%s stays under 400 MiB of video memory (%.0f)" % [room_id, mib])
		_check(load_ms < 1000.0, "%s loads in under 1 s (%.0f ms)" % [room_id, load_ms])
		# The Compatibility renderer reports no GPU time, so the budget is the
		# frame time itself.
		var p95_ms: float = frames.get("p95_ms", 0.0)
		_check(p95_ms < 16.7, "%s holds 60 fps (frame p95 %.1f ms)" % [room_id, p95_ms])
		if Rooms.current.get_node("Layers/Then").get_child_count() > 0:
			Rooms.current.set_era(&"then")
			await get_tree().create_timer(0.4).timeout
			await _shot("%s_then" % room_id)
			Rooms.current.set_era(&"now")
		for node in Rooms.current.hotspots.get_children():
			var hotspot := node as Hotspot
			if hotspot == null or hotspot is Exit or not hotspot.is_visible_in_tree():
				continue
			var spoken := [false]
			var heard := func(_id: String, _speaker: String, _text: String) -> void:
				spoken[0] = true
			Say.line_started.connect(heard)
			await hotspot.handle(&"look")
			await _settle()
			Say.line_started.disconnect(heard)
			_check(spoken[0] or Closeups.current != null, "%s/%s answers Look" % [room_id, hotspot.id])
			if Closeups.current:
				await Closeups.close()
	Say.line_started.disconnect(listen)


## Frame times through the sample: the opening, the notice's close-up, walking
## the gatehouse, and the chapel window's vision, plus memory. With
## --uncapped, vsync is off so frame times show the real cost; otherwise they
## show what the display allows. Prints one "[qa] PERF {json}" line.
func _perf() -> void:
	if _args.has("uncapped"):
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	var report := {
		"platform": OS.get_name(),
		"adapter": RenderingServer.get_video_adapter_name(),
		"framebuffer": get_viewport().get_texture().get_size(),
		"vsync": DisplayServer.window_get_vsync_mode() != DisplayServer.VSYNC_DISABLED,
	}
	_mark("opening")
	_start_sampling()
	while Rooms.current == null:
		await get_tree().process_frame
	report["opening"] = _stop_sampling()
	var skip_lines := func(_id: String, _speaker: String, _text: String) -> void:
		get_tree().create_timer(1.2).timeout.connect(Say.skip)
	Say.line_started.connect(skip_lines)
	while Interaction.locked > 0:
		await get_tree().process_frame
	_mark("close-up")
	_start_sampling()
	Interaction.click_at((Rooms.current.hotspots.get_node("Notice") as Hotspot).focus_point())
	while Closeups.current == null or Closeups.busy:
		await get_tree().process_frame
	await get_tree().create_timer(1.0).timeout
	Closeups.close()
	while Closeups.current:
		await get_tree().process_frame
	report["closeup"] = _stop_sampling()
	_mark("walking")
	_start_sampling()
	for target in [Vector2(1400, 1000), Vector2(600, 1040), Vector2(1100, 880), Vector2(900, 1000)]:
		await Rooms.player.walk_to(target)
	report["walking"] = _stop_sampling()
	_mark("vision")
	await Rooms.goto(&"greybox_chapel", &"default", &"fade")
	await _settle()
	_start_sampling()
	await _use("Window", &"use")
	report["vision"] = _stop_sampling()
	Say.line_started.disconnect(skip_lines)
	report["memory_mib"] = {
		"textures": snappedf(Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0, 0.1),
		"video": snappedf(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0, 0.1),
		"static": snappedf(Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0, 0.1),
	}
	print("[qa] PERF %s" % JSON.stringify(report))


## Saving and loading in a running game. The first pass saves in the
## gatehouse, goes to the chapel, loads the save back and plays on a few
## seconds, as a player would. A later pass (browser-qa.ts adds qa-pass=<n> when
## it loads the page again) checks that the save outlived the reload: in the
## browser, user:// reaches IndexedDB a second or two after a write.
func _saves() -> void:
	await _enter(&"greybox_gate")
	print("[qa] user:// persists: %s; %s holds %s" % [OS.is_userfs_persistent(), Saves.directory,
		DirAccess.get_files_at(Saves.directory) if DirAccess.dir_exists_absolute(Saves.directory) else []])
	if _args.get("qa-pass", "1") != "1":
		var kept := Saves.read(1)
		_check(not kept.is_empty() and kept.get("flags", {}).get("qa_marker") == "kept", "the save outlived the reload")
		_check(FileAccess.file_exists(Saves.thumbnail_path(1)), "and so did its thumbnail")
		return
	for file in [Saves.path(1), Saves.thumbnail_path(1)]:
		DirAccess.remove_absolute(file)
	GameState.set_flag(&"qa_marker", "kept")
	Rooms.player.global_position = Vector2(1200, 905)
	await get_tree().create_timer(0.3).timeout
	_check(Saves.save(1) == OK, "slot 1 saved")
	_check(FileAccess.file_exists(Saves.thumbnail_path(1)), "with a thumbnail")
	GameState.set_flag(&"qa_marker", "changed")
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	var err: Error = await Saves.load_slot(1)
	_check(err == OK and Rooms.current.room_id == &"greybox_gate", "loading goes back to the gatehouse")
	_check(Rooms.player.global_position.distance_to(Vector2(1200, 905)) < 1.0, "the hero stands where they were saved")
	_check(GameState.get_flag(&"qa_marker") == "kept", "the flags are as saved")
	await get_tree().create_timer(0.5).timeout
	await _shot("01_loaded")
	await get_tree().create_timer(4.0).timeout


## Reduce camera motion: the opening crossfades from the close shot to the
## vista instead of pulling back, and the notice's close-up crossfades in
## without a camera move.
func _reduced_motion() -> void:
	Settings.reduce_camera_motion = true
	var stage := await _opening_stage()
	var animation := stage.get_node("AnimationPlayer") as AnimationPlayer
	for moment: Array in [[3.0, "01_close_held"], [6.6, "02_crossfading"], [8.5, "03_vista"]]:
		while is_instance_valid(stage) and animation.current_animation_position < moment[0]:
			await get_tree().process_frame
		await _shot(moment[1])
	var reveal := stage.get_node("Reveal") as Reveal
	_check(is_equal_approx(reveal.camera.zoom.x, reveal.zoom_at(1.0)), "the view cut to the vista without travelling")
	await Rooms.room_shown
	await _settle()
	Interaction.click_at((Rooms.current.hotspots.get_node("Notice") as Hotspot).focus_point())
	while not Closeups.busy:
		await get_tree().process_frame
	await get_tree().create_timer(Closeups.SECONDS * 0.5).timeout
	_check(get_viewport().get_camera_2d() == null, "no camera push into the close-up")
	await _shot("04_closeup_crossfading")
	while Closeups.busy:
		await get_tree().process_frame
	await _shot("05_closeup_open")


## The start screen: at launch, its pages over it, New Game into the start
## room, the Main menu over the paused game, Resume, Save Game, and Load back
## into the game.
func _title() -> void:
	var start := StringName(Chapters.parts()[0]["start"])
	_mark("launch")
	while Menus.title == null:
		await get_tree().process_frame
	await get_tree().create_timer(2.5).timeout
	await _shot("01_title")
	var entries: Array = Menus.title.entries().map(func(entry: Array) -> String: return String(entry[0]))
	print("[qa] title entries %s" % [entries])
	_check(entries.has("new_game") and entries.has("load") and entries.has("settings"), "the start screen offers New Game, Load Game and Settings")
	_check(not entries.has("save") and not entries.has("resume"), "no Save Game or Resume before a game")
	_check(entries.has("continue") == (Saves.latest_slot() >= 0), "Continue only when there is a save")
	_check(Rooms.current == null and not get_tree().paused, "no game behind the start screen")
	Menus.choose_on_title(&"settings")
	await get_tree().create_timer(0.5).timeout
	await _shot("02_title_settings")
	Menus.screen.close()
	Menus.choose_on_title(&"load")
	await get_tree().create_timer(0.5).timeout
	await _shot("03_title_load")
	Menus.screen.close()
	_mark("new game")
	Menus.title.leave(Menus._new_game)
	while Cutscenes.current == null:
		await get_tree().process_frame
	await get_tree().create_timer(1.0).timeout
	Cutscenes.skip()
	while Rooms.current == null or Interaction.locked > 0:
		await get_tree().process_frame
	_check(Rooms.current.room_id == start, "New Game starts in %s" % start)
	_check(Menus.title == null, "the start screen is gone")
	await _settle()
	await get_tree().create_timer(1.0).timeout
	await _shot("04_start_room")
	_mark("main menu")
	await Menus.choose(&"menu")
	await get_tree().create_timer(1.0).timeout
	await _shot("05_title_in_game")
	_check(get_tree().paused, "the game pauses behind the Main menu")
	entries = Menus.title.entries().map(func(entry: Array) -> String: return String(entry[0]))
	_check(entries.has("resume") and entries.has("save"), "the Main menu offers Resume and Save Game")
	Menus.choose_on_title(&"resume")
	await get_tree().process_frame
	_check(Menus.title == null and not get_tree().paused, "Resume goes back to the game")
	await Menus.choose(&"menu")
	await get_tree().create_timer(0.5).timeout
	Menus.choose_on_title(&"save")
	await get_tree().create_timer(0.5).timeout
	await _shot("06_title_save")
	(Menus.screen as SlotsScreen).pick(6)
	_check(Saves.has_save(6), "Save Game saves")
	_check(Menus.title != null and get_tree().paused, "the Main menu stays after saving")
	Menus.choose_on_title(&"new_game")
	await get_tree().create_timer(0.5).timeout
	await _shot("07_title_new_game_confirm")
	Menus.screen.close()
	_mark("load")
	Menus.title.leave(Menus._load.bind(6))
	while Menus.title != null or Interaction.locked > 0:
		await get_tree().process_frame
	_check(Rooms.current != null and Rooms.current.room_id == start and not get_tree().paused, "Load Game goes back into the game")
	await get_tree().create_timer(1.0).timeout
	await _shot("08_loaded")


## The top bar and its pages, shot one by one in the start room.
func _menus() -> void:
	await _enter(Chapters.parts()[0]["start"])
	await get_tree().create_timer(0.5).timeout
	Menus.bar.open()
	await get_tree().create_timer(0.4).timeout
	await _shot("01_top_bar")
	Menus.bar.hide_now()
	var visible := Rooms.current.hotspots.get_children().filter(func(node: Node) -> bool: return node is Hotspot and (node as Hotspot).is_visible_in_tree()).size()
	_check(Menus.hotspots.reveal() == visible, "every visible hotspot is marked")
	await get_tree().create_timer(0.6).timeout
	await _shot("02_reveal_hotspots")
	Menus.hotspots.clear()
	for file in [Saves.path(1), Saves.thumbnail_path(1)]:
		DirAccess.remove_absolute(file)
	await Menus.choose(&"save")
	await get_tree().create_timer(0.3).timeout
	await _shot("03_save_page")
	(Menus.screen as SlotsScreen).pick(1)
	await Menus.choose(&"load")
	await get_tree().create_timer(0.3).timeout
	await _shot("04_load_page")
	Menus.screen.close()
	for page: Array in [[&"settings", "05_settings_page"], [&"journal", "06_journal_page"], [&"quit", "07_quit_page"]]:
		await Menus.choose(page[0])
		await get_tree().create_timer(0.3).timeout
		await _shot(page[1])
		Menus.screen.close()


## Skipping the opening: the Skip button shows, fills as it is held, and the
## opening fast-forwards to the first room.
func _skip() -> void:
	await _opening_stage()
	await get_tree().create_timer(2.0).timeout
	Cutscenes.skip_button.press()
	await get_tree().create_timer(SkipButton.HOLD_SECONDS * 0.6).timeout
	await _shot("01_skip_held")
	var started := Time.get_ticks_msec()
	await Rooms.room_changed
	_check(Time.get_ticks_msec() - started < 4000, "the opening fast-forwards to the first room")
	await _settle()
	await _shot("02_in_the_first_room")


## Waits for the opening's reveal stage to show and returns it.
func _opening_stage() -> RevealStage:
	var stage: RevealStage = null
	while stage == null:
		await get_tree().process_frame
		for node in get_tree().current_scene.get_children():
			if node is RevealStage:
				stage = node
	return stage


## The discovery reveal and the memory vista , in the greybox
## courtyard: using the way on pulls back over the land beyond, and using the
## milestone shows the same land in the past.
func _vista() -> void:
	await _enter(&"greybox_courtyard")
	var skip_lines := func(_id: String, _speaker: String, _text: String) -> void: Say.skip.call_deferred()
	Say.line_started.connect(skip_lines)
	for use: Array in [["Path", "01_reveal_close", "02_reveal_pulling_back", "03_reveal_vista"],
			["Milestone", "04_vista_close", "05_vista_pulling_back", "06_vista_in_the_past"]]:
		var spot := Rooms.current.hotspots.get_node(String(use[0])) as Hotspot
		Interaction.press_at(spot.focus_point(), spot.focus_point())
		await get_tree().create_timer(Interaction.COIN_HOLD_SECONDS + 0.1).timeout
		Interaction.coin.point_at(Interaction.coin.glyph_position(&"use"))
		Interaction.release_at(spot.focus_point(), Interaction.coin.glyph_position(&"use"))
		while Cutscenes.current == null or not Cutscenes.current is CutsceneSteps:
			await get_tree().process_frame
		var stage: RevealStage = null
		while stage == null:
			await get_tree().process_frame
			stage = get_tree().current_scene.get_node_or_null("GreyboxVista") as RevealStage
		for moment: Array in [[2.0, use[1]], [7.0, use[2]], [12.0, use[3]]]:
			while is_instance_valid(stage) and stage.animation.current_animation_position < moment[0]:
				await get_tree().process_frame
			await _shot(moment[1])
		await _settle()
	Say.line_started.disconnect(skip_lines)
	_check(Cutscenes.fade_amount() == 0.0 and get_viewport().get_canvas_transform() == Transform2D.IDENTITY, "the courtyard shows as it was")
	_check(&"greybox_milestone" in GameState.memories, "the memory vista is remembered")
	await _shot("07_back_in_the_courtyard")
	print("[qa] video memory in the courtyard, the vista loaded: %.1f MiB" % (Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0))


## Plays every discovery reveal in content/chapters.json's parts (or
## `--reveals=a,b`), with shots at its close start, mid pull-back and full
## vista.
func _reveals() -> void:
	await _enter(Chapters.parts()[0]["start"])
	var ids: PackedStringArray = []
	if _args.has("reveals"):
		ids = String(_args["reveals"]).split(",")
	else:
		for part: Dictionary in Chapters.parts():
			for id: String in part.get("cutscenes", []):
				if ResourceLoader.exists("res://content/cutscenes/%s/%s.tscn" % [id, id]):
					ids.append(id)
	_check(not ids.is_empty(), "there are reveals to play")
	for reveal_id in ids:
		_mark(reveal_id)
		var scene := load("res://content/cutscenes/%s/%s.tscn" % [reveal_id, reveal_id]) as PackedScene
		Cutscenes.play(RevealCutscene.new(StringName(reveal_id), scene))
		var stage: RevealStage = null
		while stage == null:
			await get_tree().process_frame
			stage = get_tree().current_scene.get_node_or_null(NodePath(reveal_id.to_pascal_case())) as RevealStage
		for moment: Array in [[2.0, "1_close"], [7.0, "2_pulling_back"], [11.5, "3_vista"]]:
			while is_instance_valid(stage) and stage.animation.current_animation_position < moment[0]:
				await get_tree().process_frame
			await _shot("%s_%s" % [reveal_id, moment[1]])
		while Cutscenes.current != null:
			await get_tree().process_frame
		await _settle()
		_check(Cutscenes.fade_amount() == 0.0, "%s returns to the room" % reveal_id)


## The journal: after reading the notice up close and seeing the chapel
## window's vision, its pages show what the hero learned, the memory's still
## and line, and the scenes to watch again.
func _journal() -> void:
	await _enter(&"greybox_gate")
	var skip_lines := func(_id: String, _speaker: String, _text: String) -> void: Say.skip.call_deferred()
	Say.line_started.connect(skip_lines)
	Interaction.click_at((Rooms.current.hotspots.get_node("Notice") as Hotspot).focus_point())
	while Closeups.current == null or Closeups.busy:
		await get_tree().process_frame
	await Interaction.click_at((Closeups.current.hotspots.get_node("Text") as Hotspot).focus_point())
	await _settle()
	await Closeups.close()
	_check(GameState.get_flag(&"greybox_notice_read"), "seeing the notice counts as reading it")
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	await _settle()
	await _use("Window", &"use")
	await _settle()
	Say.line_started.disconnect(skip_lines)
	_check(&"greybox_window" in GameState.memories, "the window's vision is remembered")
	_check(FileAccess.file_exists(Journal.still_path(&"greybox_window")), "the memory's still was kept")
	await Menus.choose(&"journal")
	await get_tree().create_timer(0.3).timeout
	await _shot("01_who_am_i")
	await (Menus.screen as JournalScreen).show_memory(&"greybox_window")
	await get_tree().create_timer(0.3).timeout
	await _shot("02_the_chapel_at_noon")
	Menus.screen.close()


## The cinematic toolkit as a reel for the movie writer: the opening skipped
## partway, the chapel window's vision, the altar's playable memory, the
## courtyard's reveal (skipped halfway) and memory vista, and the journal.
## Lines play at reading pace. Record with
##   --write-movie <file.avi> --fixed-fps 30 -- --qa=toolkit_reel --force-draw
func _toolkit_reel() -> void:
	await _opening_stage()
	Rooms.room_shown.connect(func(_room: Room) -> void: Rooms.player.get_node("IdleFidgets").set_process(false), CONNECT_ONE_SHOT)
	await get_tree().create_timer(5.0).timeout
	Cutscenes.skip_button.press()
	await Rooms.room_shown
	await _settle(false)
	await get_tree().create_timer(0.8).timeout
	await Rooms.goto(&"greybox_chapel", &"default", &"fade")
	await _settle(false)
	await get_tree().create_timer(0.6).timeout
	await _use("Window", &"use")
	await _settle(false)
	await get_tree().create_timer(0.8).timeout
	await _use("Altar", &"use")
	await _settle(false)
	await Rooms.player.walk_to(Vector2(600, 960))
	await get_tree().create_timer(0.6).timeout
	await Interaction.click_at((Rooms.current.hotspots.get_node("Carving") as Hotspot).focus_point())
	while Flashback.in_memory:
		await get_tree().process_frame
	await _settle(false)
	await get_tree().create_timer(0.8).timeout
	await Rooms.goto(&"greybox_courtyard", &"default", &"fade")
	await _settle(false)
	_use("Path", &"use")
	while Cutscenes.current == null or get_tree().current_scene.get_node_or_null("GreyboxVista") == null:
		await get_tree().process_frame
	await get_tree().create_timer(6.0).timeout
	Cutscenes.skip()
	await _settle(false)
	await get_tree().create_timer(0.6).timeout
	await _use("Milestone", &"use")
	await _settle(false)
	await get_tree().create_timer(0.8).timeout
	await Menus.choose(&"journal")
	await get_tree().create_timer(2.5).timeout
	for id in [&"greybox_window", &"greybox_milestone"]:
		await (Menus.screen as JournalScreen).show_memory(id)
		await get_tree().create_timer(3.0).timeout
	Menus.screen.close()
	await get_tree().create_timer(1.0).timeout


## Holds the button on a hotspot until the verb coin opens, and lets go over
## `verb`; returns once the verb has run.
func _use(hotspot_name: String, verb: StringName) -> void:
	var world := (Rooms.current.hotspots.get_node(hotspot_name) as Hotspot).focus_point()
	Interaction.press_at(world, get_viewport().get_canvas_transform() * world)
	await get_tree().create_timer(Interaction.COIN_HOLD_SECONDS + 0.1).timeout
	var glyph := Interaction.coin.glyph_position(verb)
	Interaction.coin.point_at(glyph)
	await Interaction.release_at(world, glyph)


## Voice playback, with a tone made in memory until real lines exist: the
## Voice bus is there, a voiced line holds for its audio, its level follows the
## line's envelope and the hero's body follows the level. In the browser it
## checks streamed playback; browser-qa.ts lets the page play sound before a
## click, as a player's first click does.
func _voice() -> void:
	await _enter(&"greybox_chapel")
	_check(AudioServer.get_bus_index(&"Voice") >= 0, "the Voice bus exists")
	var rate := 22050
	var data := PackedByteArray()
	data.resize(rate * 2)
	for i in rate:
		data.encode_s16(i * 2, int(sin(i * TAU * 220.0 / rate) * 6000.0))
	var tone := AudioStreamWAV.new()
	tone.format = AudioStreamWAV.FORMAT_16_BITS
	tone.mix_rate = rate
	tone.data = data
	var rising := PackedFloat32Array()
	for i in 30:
		rising.append(i / 29.0)
	Voice.register(&"GB_ALTAR_LOOK_1", tone, rising)
	# The line's level and the hero's, at their highest, and the longest frame:
	# the browser build mixes sound between frames, so long ones hold it back.
	var peaks := [0.0, 0.0, 0, Time.get_ticks_msec()]
	var body := Rooms.player.get_node("Body")
	var track := func() -> void:
		peaks[0] = maxf(peaks[0], Voice.level())
		peaks[1] = maxf(peaks[1], body.voice_level)
		var now := Time.get_ticks_msec()
		if Say.speaking:
			peaks[2] = maxi(peaks[2], now - peaks[3])
		peaks[3] = now
	get_tree().process_frame.connect(track)
	var id: String = await _click_for_line((Rooms.current.hotspots.get_node("Altar") as Hotspot).focus_point())
	var started := Time.get_ticks_msec()
	await Say.line_finished
	var held := (Time.get_ticks_msec() - started) / 1000.0
	get_tree().process_frame.disconnect(track)
	_check(id == "GB_ALTAR_LOOK_1", "the altar's line plays voiced")
	_check(absf(held - 1.0) < 0.4, "it held for its audio's 1 s (%.2f s; longest frame %d ms)" % [held, peaks[2]])
	_check(peaks[0] > 0.7, "its audio played through the envelope (level peak %.2f)" % peaks[0])
	_check(peaks[1] > 0.7, "the hero's voice level followed it (peak %.2f)" % peaks[1])
	await _settle()
	Voice.unregister(&"GB_ALTAR_LOOK_1")


## Waits until the player can act again: no transition, line or close-up move
## running. With `skip`, lines being spoken are cut short.
func _settle(skip := true) -> void:
	while Interaction.locked > 0 or Say.speaking or Closeups.busy:
		if skip and Say.speaking:
			Say.skip()
		await get_tree().process_frame


## Clicks `world` and returns the id of the first line that starts (a close-up's
## hotspots answer at once, before an await on the signal could catch it).
func _click_for_line(world: Vector2) -> String:
	var ids: Array[String] = []
	var collect := func(id: String, _speaker: String, _text: String) -> void: ids.append(id)
	Say.line_started.connect(collect)
	Interaction.click_at(world)
	while ids.is_empty():
		await get_tree().process_frame
	Say.line_started.disconnect(collect)
	return ids[0]


func _start_sampling() -> void:
	_samples.clear()
	_cpu_samples.clear()
	_gpu_samples.clear()
	_script_samples.clear()
	_sampling = true


## Frame time (mean, 95th percentile, worst and when it happened), frames over
## 1/60 s, and the renderer's own CPU and GPU time per frame, all in ms.
func _stop_sampling() -> Dictionary:
	_sampling = false
	var count := _samples.size()
	if count == 0:
		return {"frames": 0}
	var total := 0.0
	var slow := 0
	var worst := 0
	for i in count:
		total += _samples[i]
		if _samples[i] > 1.0 / 58.0:
			slow += 1
		if _samples[i] > _samples[worst]:
			worst = i
	var worst_at := 0.0
	for i in worst:
		worst_at += _samples[i]
	return {
		"frames": count,
		"seconds": snappedf(total, 0.01),
		"mean_ms": snappedf(total / count * 1000.0, 0.01),
		"p95_ms": snappedf(_percentile(_samples, 0.95) * 1000.0, 0.01),
		"max_ms": snappedf(_samples[worst] * 1000.0, 0.01),
		"max_at_s": snappedf(worst_at, 0.01),
		"over_60fps_budget": slow,
		"render_cpu_p95_ms": snappedf(_percentile(_cpu_samples, 0.95), 0.01),
		# The worst frame's own script and render times; what's left of it is
		# waiting (GPU, the browser, loading).
		"worst_script_ms": snappedf(_script_samples[worst], 0.01) if worst < _script_samples.size() else 0.0,
		"worst_render_cpu_ms": snappedf(_cpu_samples[worst], 0.01) if worst < _cpu_samples.size() else 0.0,
		"render_gpu_p95_ms": snappedf(_percentile(_gpu_samples, 0.95), 0.01),
	}


func _percentile(values: PackedFloat32Array, fraction: float) -> float:
	if values.is_empty():
		return 0.0
	var sorted := values.duplicate()
	sorted.sort()
	return sorted[mini(int(sorted.size() * fraction), sorted.size() - 1)]


## Notes the step a scenario starts, with the time since launch.
func _mark(step: String) -> void:
	_at = step
	print("[qa] at %s (%.1f s)" % [step, Time.get_ticks_msec() / 1000.0])


func _check(ok: bool, what: String) -> void:
	print("[qa] %s %s" % ["PASS" if ok else "FAIL", what])
	if not ok:
		_failures.append(what)


func _shot(shot_name: String) -> void:
	# Draw now rather than await the next frame: macOS stops drawing a window that
	# other windows cover, and the post-draw signal would never come.
	RenderingServer.force_draw(false)
	var path := _out_dir.path_join("%s.png" % shot_name)
	var err := get_viewport().get_texture().get_image().save_png(path)
	_check(err == OK, "screenshot %s" % path)


func _finish(reason: String) -> void:
	if _finished:
		return
	_finished = true
	if reason == "timeout":
		_failures.append("timed out" + (" at %s" % _at if not _at.is_empty() else ""))
	print("[qa] RESULT %s %s" % ["PASS" if _failures.is_empty() else "FAIL", ", ".join(_failures)])
	get_tree().quit(0 if _failures.is_empty() else 1)
