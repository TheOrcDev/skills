extends Node
## Voiced lines (technical-plan.md §6.5). A line's audio is
## res://assets/audio/voice/en/<ID>.wav, which Godot imports as QOA (decision
## #41). It is loaded when it is said and played on the Voice bus, streamed in
## every build (the browser's Sample playback freezes on long clips, §7). Its
## loudness envelope, about 30 values a second computed offline by tools/audio
## `post`, says how loud the line is at each moment; the speaker's body follows
## it. A line without audio falls back to text timing in Say. Nothing analyses
## audio at runtime.
##
## A browser plays no sound until the player's first click, and until then the
## line's audio never starts: its position stands still. Such a line has
## stalled (stalled()), and Say gives it the time it would have had as text.

## Written by `post`: RATE (values a second) and LINES (ID → envelope bytes,
## 0–255, in base64).
const ENVELOPES_PATH := "res://assets/audio/voice/en/envelopes.gd"
## A playing line whose position stands still this long, over at least
## STALL_FRAMES frames (so one long frame doesn't count), has stalled.
const STALL_SECONDS := 0.5
const STALL_FRAMES := 6

## Where a line's audio is, by ID. Tests point it at fixtures.
var line_path := "res://assets/audio/voice/en/%s.wav"

var _player: AudioStreamPlayer
var _registered := {}
var _table := {}
var _table_rate := 30.0
var _envelope := PackedFloat32Array()
var _rate := 30.0
var _position := 0.0
var _moved_msec := 0
var _moved_frame := 0


func _ready() -> void:
	_player = AudioStreamPlayer.new()
	_player.name = "Player"
	_player.bus = &"Voice"
	_player.playback_type = AudioServer.PLAYBACK_TYPE_STREAM
	add_child(_player)
	load_envelopes(ENVELOPES_PATH)


## Reads the envelope table at `path`, if there is one.
func load_envelopes(path: String) -> void:
	_table = {}
	if not ResourceLoader.exists(path):
		return
	var constants := (load(path) as Script).get_script_constant_map()
	_table_rate = float(constants.get("RATE", 30))
	_table = constants.get("LINES", {})


## Whether the line `id` has audio.
func has_line(id: StringName) -> bool:
	return _registered.has(id) or ResourceLoader.exists(line_path % id)


## Starts the line `id`; false when it has no audio.
func play(id: StringName) -> bool:
	var stream: AudioStream = null
	if _registered.has(id):
		stream = _registered[id]["stream"]
		_envelope = _registered[id]["envelope"]
		_rate = _registered[id]["rate"]
	elif ResourceLoader.exists(line_path % id):
		stream = load(line_path % id)
		_envelope = PackedFloat32Array()
		for value in Marshalls.base64_to_raw(_table.get(id, "")):
			_envelope.append(value / 255.0)
		_rate = _table_rate
	if stream == null:
		return false
	_player.stream = stream
	_player.play()
	_position = 0.0
	_moved_msec = Time.get_ticks_msec()
	_moved_frame = Engine.get_process_frames()
	return true


func stop() -> void:
	_player.stop()


func is_playing() -> bool:
	return _player.playing


## Whether the line playing has stalled: its audio hasn't moved for
## STALL_SECONDS, so no sound is coming out.
func stalled() -> bool:
	if not _player.playing:
		return false
	var position := _player.get_playback_position()
	if position != _position:
		_position = position
		_moved_msec = Time.get_ticks_msec()
		_moved_frame = Engine.get_process_frames()
	return Time.get_ticks_msec() - _moved_msec > STALL_SECONDS * 1000.0 \
		and Engine.get_process_frames() - _moved_frame >= STALL_FRAMES


## How loud the line playing is now, 0–1, from its envelope; 0 when silent.
func level() -> float:
	if not _player.playing or _envelope.is_empty():
		return 0.0
	return _envelope[clampi(int(_player.get_playback_position() * _rate), 0, _envelope.size() - 1)]


## Makes the line `id` sayable without files: tests and previews.
func register(id: StringName, stream: AudioStream, envelope: PackedFloat32Array, rate := 30.0) -> void:
	_registered[id] = {"stream": stream, "envelope": envelope, "rate": rate}


func unregister(id: StringName) -> void:
	_registered.erase(id)
