extends Node
## The player's settings (docs/technical-plan.md §6.9, game-design.md §12), kept
## in `user://settings.cfg` apart from saves. Each one applies as soon as it is
## set, and the file is rewritten at the end of that frame.

signal changed(key: StringName)

const DEFAULT_PATH := "user://settings.cfg"
const SECTION := "settings"
## The audio bus each volume drives (audio-pipeline.md §7). Plan 003 creates the
## buses; until then the volumes are kept and apply once a bus exists.
const BUSES := {
	&"voice_volume": &"Voice",
	&"music_volume": &"Music",
	&"ambience_volume": &"Ambience",
	&"effects_volume": &"SFX",
}
const DEFAULTS := {
	&"voice_volume": 1.0,
	&"music_volume": 1.0,
	&"ambience_volume": 1.0,
	&"effects_volume": 1.0,
	&"subtitles": true,
	&"subtitle_size": 1.0,
	&"text_speed": 1.0,
	&"reduce_flashing": false,
	&"reduce_camera_motion": false,
	&"fullscreen": false,
	&"render_1080p": false,
}

var path := DEFAULT_PATH

## 0 to 1 each.
var voice_volume := 1.0:
	set(value):
		voice_volume = clampf(value, 0.0, 1.0)
		_changed(&"voice_volume")
var music_volume := 1.0:
	set(value):
		music_volume = clampf(value, 0.0, 1.0)
		_changed(&"music_volume")
var ambience_volume := 1.0:
	set(value):
		ambience_volume = clampf(value, 0.0, 1.0)
		_changed(&"ambience_volume")
var effects_volume := 1.0:
	set(value):
		effects_volume = clampf(value, 0.0, 1.0)
		_changed(&"effects_volume")
var subtitles := true:
	set(value):
		subtitles = value
		_changed(&"subtitles")
## Subtitle text size, as a multiple of the normal size.
var subtitle_size := 1.0:
	set(value):
		subtitle_size = clampf(value, 0.75, 1.75)
		_changed(&"subtitle_size")
## How fast text-only lines move on: 2 halves the time each stays up.
var text_speed := 1.0:
	set(value):
		text_speed = clampf(value, 0.5, 2.0)
		_changed(&"text_speed")
## Softens the flare as a vision opens.
var reduce_flashing := false:
	set(value):
		reduce_flashing = value
		_changed(&"reduce_flashing")
## Camera moves become cuts and crossfades: the opening's pull-back, the drift
## during a vision and the push into a close-up.
var reduce_camera_motion := false:
	set(value):
		reduce_camera_motion = value
		_changed(&"reduce_camera_motion")
var fullscreen := false:
	set(value):
		fullscreen = value
		_changed(&"fullscreen")
## Draws the game at 1920×1080 and scales it to the window, instead of at the
## window's own resolution. On a high-DPI screen that is up to 4× fewer pixels,
## for weaker GPUs.
var render_1080p := false:
	set(value):
		render_1080p = value
		_changed(&"render_1080p")

var _loading := false
var _save_queued := false


func _ready() -> void:
	load_settings()
	# Buses made later take the volumes already set.
	AudioServer.bus_layout_changed.connect(_apply_volumes)
	AudioServer.bus_renamed.connect(func(_bus: int, _old: StringName, _new: StringName) -> void: _apply_volumes())


## Reads the settings at `path`, or the defaults where it has none, and applies
## them all.
func load_settings() -> void:
	var file := ConfigFile.new()
	var found := file.load(path) == OK
	_loading = true
	for key: StringName in DEFAULTS:
		set(key, file.get_value(SECTION, key, default_of(key)) if found else default_of(key))
	_loading = false


## Every setting back to its default, applied and saved. `overrides` replaces
## some defaults, so a scripted run can keep its window.
func reset(overrides := {}) -> void:
	for key: StringName in DEFAULTS:
		set(key, overrides.get(key, default_of(key)))


## A setting's value before the player changes it. An exported desktop game
## starts fullscreen (technical-plan.md §4); the editor, tests and the browser
## start in a window.
static func default_of(key: StringName) -> Variant:
	if key == &"fullscreen":
		return OS.has_feature("template") and not OS.has_feature("web")
	return DEFAULTS[key]


func save() -> void:
	_save_queued = false
	var file := ConfigFile.new()
	for key: StringName in DEFAULTS:
		file.set_value(SECTION, key, get(key))
	file.save(path)


## Whether the command line asked for a window of its own (a size or a mode),
## or runs a QA scenario.
static func _window_given() -> bool:
	for arg in OS.get_cmdline_args():
		if arg in ["--resolution", "--windowed", "-w", "--fullscreen", "-f", "--maximized", "-m", "--position"]:
			return true
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--qa"):
			return true
	return false


func _apply_volumes() -> void:
	for key: StringName in BUSES:
		_apply(key)


func _changed(key: StringName) -> void:
	_apply(key)
	if not _loading and not _save_queued:
		_save_queued = true
		save.call_deferred()
	changed.emit(key)


func _apply(key: StringName) -> void:
	match key:
		&"reduce_flashing":
			Flashback.reduce_flashing = reduce_flashing
		&"fullscreen":
			# A browser only goes fullscreen from a click. At start-up, a window
			# asked for on the command line, or a scripted run's, is kept.
			var keep := _loading and (OS.has_feature("web") or _window_given())
			if DisplayServer.get_name() != "headless" and not keep:
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)
		&"render_1080p":
			get_tree().root.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT if render_1080p else Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
		_:
			if BUSES.has(key):
				var bus := AudioServer.get_bus_index(BUSES[key])
				if bus >= 0:
					AudioServer.set_bus_volume_linear(bus, get(key))

