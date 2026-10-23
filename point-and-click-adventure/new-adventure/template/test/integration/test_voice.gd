extends GutTest
## Voiced lines: a line with audio holds until its audio
## ends, not for its text's time; a click stops it; the speaker's level follows
## the line's envelope, and the hero's body follows that; a line without audio,
## or whose audio stalls, keeps text timing; and a line's audio and envelope
## come from the files `post` writes.

const FIXTURE := preload("res://test/fixtures/voice.dialogue")
const FIRST_LINE := "A voiced test line, long enough that as text alone it would stay up for a good few seconds."

## Whether this test holds the audio server's lock.
var _locked := false
var _line_path := ""


## One second of a quiet tone, made in memory.
func _tone(seconds: float) -> AudioStreamWAV:
	var rate := 22050
	var count := int(seconds * rate)
	var data := PackedByteArray()
	data.resize(count * 2)
	for i in count:
		data.encode_s16(i * 2, int(sin(i * TAU * 220.0 / rate) * 6000.0))
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = rate
	wav.data = data
	return wav


func before_each() -> void:
	var rising := PackedFloat32Array()
	for i in 30:
		rising.append(i / 29.0)
	Voice.register(&"TEST_VOICE_1", _tone(1.0), rising)
	_line_path = Voice.line_path
	await Rooms.goto(&"greybox_chapel", &"default", &"none")


func after_each() -> void:
	if _locked:
		AudioServer.unlock()
		_locked = false
	Voice.stop()
	Say.skip()
	await wait_until(func() -> bool: return not Say.speaking, 15.0)
	Voice.unregister(&"TEST_VOICE_1")
	Voice.line_path = _line_path
	Voice.load_envelopes(Voice.ENVELOPES_PATH)
	Rooms.clear()


func test_a_voiced_line_holds_for_its_audio() -> void:
	var times := {}
	var started := func(id: String, _speaker: String, _text: String) -> void: times[id] = Time.get_ticks_msec()
	Say.line_started.connect(started)
	await Say.run(FIXTURE, "start")
	Say.line_started.disconnect(started)
	var held: float = (times["TEST_VOICE_2"] - times["TEST_VOICE_1"]) / 1000.0
	assert_almost_eq(held, 1.0, 0.4, "held for the audio's 1 s, not the text's %.1f s" % Say.line_seconds(FIRST_LINE))
	assert_false(Voice.has_line(&"TEST_VOICE_2"), "the second line has no audio and kept text timing")


func test_a_click_stops_the_voice() -> void:
	Say.run(FIXTURE, "start")
	await wait_until(func() -> bool: return Voice.is_playing(), 3.0)
	assert_true(Voice.is_playing())
	Say.skip()
	await wait_process_frames(2)
	assert_false(Voice.is_playing(), "skipping the line stops its audio")


func test_the_level_follows_the_envelope_and_the_hero_follows_the_level() -> void:
	var body := Rooms.player.get_node("Body")
	Say.run(FIXTURE, "start")
	await wait_until(func() -> bool: return Voice.is_playing(), 3.0)
	await wait_seconds(0.25)
	var early := Voice.level()
	await wait_seconds(0.45)
	var later := Voice.level()
	assert_gt(later, early, "the envelope rises through the line")
	assert_almost_eq(body.voice_level, later, 0.2, "the hero's voice level follows it")


func test_a_line_whose_audio_stalls_keeps_text_timing() -> void:
	# A browser before the player's first click mixes nothing, so the audio's
	# position stands still. Holding the audio server's lock does the same here.
	var times := {}
	var started := func(id: String, _speaker: String, _text: String) -> void: times[id] = Time.get_ticks_msec()
	Say.line_started.connect(started)
	AudioServer.lock()
	_locked = true
	await Say.run(FIXTURE, "start")
	AudioServer.unlock()
	_locked = false
	Say.line_started.disconnect(started)
	var held: float = (times["TEST_VOICE_2"] - times["TEST_VOICE_1"]) / 1000.0
	assert_almost_eq(held, Say.line_seconds(FIRST_LINE), 0.4, "held for the text's time, not stuck on the silent audio")
	assert_false(Voice.is_playing(), "and the stalled audio was stopped, so it can't start late")


func test_a_line_plays_from_the_files_post_writes() -> void:
	# Made by post's own functions from a made-up master: a tone that swells for
	# 1 s, with the 80 ms lead and 200 ms tail, so 1.28 s in all.
	Voice.line_path = "res://test/fixtures/voice/%s.wav"
	Voice.load_envelopes("res://test/fixtures/voice/envelopes.gd")
	assert_eq((load(Voice.line_path % "TEST_FILE_1") as AudioStreamWAV).format, AudioStreamWAV.FORMAT_QOA, "Godot imports the WAV as QOA")
	var started := Time.get_ticks_msec()
	Say.run(FIXTURE, "file")
	await wait_until(func() -> bool: return Voice.is_playing(), 3.0)
	await wait_seconds(0.3)
	var early := Voice.level()
	await wait_seconds(0.6)
	var later := Voice.level()
	assert_gt(early, 0.0, "the table has the line's envelope")
	assert_gt(later, early, "and it swells with the audio")
	await wait_until(func() -> bool: return not Say.speaking, 5.0)
	assert_almost_eq((Time.get_ticks_msec() - started) / 1000.0, 1.28, 0.4, "held for the file's 1.28 s")
