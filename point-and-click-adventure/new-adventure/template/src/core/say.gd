extends Node
## Speaks Dialogue Manager lines over the speaking actor (docs/technical-plan.md
## §5.6): text above the speaker, held until its voice ends (Voice), or for a
## time based on its length and the player's text speed when it has no audio,
## and skipped with a left click. Settings can hide the text or change its
## size. When a line offers responses, the allowed ones are shown as choices;
## the player's pick is spoken by the player and the conversation follows it.

signal line_started(static_id: String, speaker: String, text: String)
signal line_finished(static_id: String)

const DIALOGUE_PATH := "res://content/dialogue/%s.dialogue"
const FONT_SIZE := 36

var speaking := false
## Set while a skipped cutscene runs through: lines don't hold, so a dialogue
## still runs its mutations but takes no time.
var fast_forward := false
var choices: ChoiceList
## The line on screen.
var subtitle: Label
var _skip := false


func _ready() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 60
	add_child(layer)
	subtitle = Label.new()
	subtitle.add_theme_font_size_override(&"font_size", FONT_SIZE)
	subtitle.add_theme_color_override(&"font_outline_color", Color.BLACK)
	subtitle.add_theme_constant_override(&"outline_size", 12)
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	subtitle.custom_minimum_size.x = 900.0
	subtitle.mouse_filter = Control.MOUSE_FILTER_IGNORE
	subtitle.visible = false
	layer.add_child(subtitle)
	choices = ChoiceList.new()
	choices.name = "Choices"
	add_child(choices)


## Runs a cue from content/dialogue/<file>.dialogue.
func line(file: StringName, cue: StringName) -> void:
	var resource := load(DIALOGUE_PATH % file) as DialogueResource
	if resource == null:
		push_error("Dialogue not found: %s" % file)
		return
	await run(resource, String(cue))


## One of the hero's dry answers when nothing handles a verb.
func fallback(verb: StringName) -> void:
	await line(&"core", StringName("fallback_%s" % verb))


func run(resource: DialogueResource, cue: String) -> void:
	speaking = true
	Interaction.locked += 1
	var current: DialogueLine = await DialogueManager.get_next_dialogue_line(resource, cue)
	while current != null:
		if not current.text.is_empty():
			await _speak(current.static_id, current.character, current.text)
		if current.responses.is_empty():
			current = await DialogueManager.get_next_dialogue_line(resource, current.next_id)
			continue
		var allowed: Array = current.responses.filter(func(r: DialogueResponse) -> bool: return r.is_allowed)
		if allowed.is_empty():
			break
		var texts := PackedStringArray()
		for response: DialogueResponse in allowed:
			texts.append(response.text)
		var pick := 0
		if fast_forward:
			push_warning("A skipped cutscene's dialogue offered choices; the first was taken")
		else:
			pick = await choices.choose(texts)
		var response: DialogueResponse = allowed[pick]
		await _speak(response.static_id, response.character if not response.character.is_empty() else _player_name(), response.text)
		current = await DialogueManager.get_next_dialogue_line(resource, response.next_id)
	subtitle.visible = false
	Interaction.locked -= 1
	speaking = false


## Ends the line on screen now, as a click does.
func skip() -> void:
	_skip = true


func _unhandled_input(event: InputEvent) -> void:
	if speaking and event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		get_viewport().set_input_as_handled()
		skip()


func _speak(static_id: String, speaker: String, text: String) -> void:
	var actor := _actor_named(speaker)
	subtitle.text = text
	subtitle.add_theme_font_size_override(&"font_size", roundi(FONT_SIZE * Settings.subtitle_size))
	subtitle.add_theme_color_override(&"font_color", actor.subtitle_color if actor else Color.WHITE)
	subtitle.reset_size()
	_place_over(actor)
	subtitle.visible = Settings.subtitles
	if actor:
		actor.set_speaking(true)
	line_started.emit(static_id, speaker, text)
	if Voice.play(StringName(static_id)):
		await _hold_voice(text)
	else:
		await _hold(line_seconds(text))
	if is_instance_valid(actor):
		actor.set_speaking(false)
	line_finished.emit(static_id)


## How long a line without voice stays up, at the player's text speed.
func line_seconds(text: String) -> float:
	return clampf(1.2 + text.length() * 0.055, 2.0, 9.0) / Settings.text_speed


## Who speaks the player's choices: the player actor, or the hero.
func _player_name() -> String:
	return Rooms.player.speaker_name if Rooms.player else "Hero"


## Waits `seconds` of game time (so Engine.time_scale applies) or until skipped.
func _hold(seconds: float) -> void:
	_skip = false
	var elapsed := 0.0
	while not _skip and not fast_forward and elapsed < seconds:
		await get_tree().process_frame
		elapsed += get_process_delta_time()


## Waits for the voiced line to end, or until skipped (which stops it). If its
## audio stalls, as in a browser before the player's first click, the line
## keeps the time it would have had as text.
func _hold_voice(text: String) -> void:
	_skip = false
	var elapsed := 0.0
	var stalled := false
	while not _skip and not fast_forward and (Voice.is_playing() or (stalled and elapsed < line_seconds(text))):
		if not stalled and Voice.stalled():
			stalled = true
			Voice.stop()
		await get_tree().process_frame
		elapsed += get_process_delta_time()
	Voice.stop()


func _actor_named(speaker: String) -> Actor:
	if Rooms.current == null:
		return null
	for child in Rooms.current.actors.get_children():
		if child is Actor and (child.speaker_name == speaker or speaker in child.speaker_aliases):
			return child
	return null


func _place_over(actor: Actor) -> void:
	var view := get_viewport().get_visible_rect().size
	var anchor := Vector2(view.x / 2.0, 160.0)
	if Closeups.current:
		# The room and its speakers are hidden behind a close-up: speak from below.
		anchor = Vector2(view.x / 2.0, view.y - 110.0)
	elif actor:
		anchor = actor.get_global_transform_with_canvas() * actor.speech_offset
	subtitle.position = Vector2(
		clampf(anchor.x - subtitle.size.x / 2.0, 20.0, view.x - subtitle.size.x - 20.0),
		clampf(anchor.y - subtitle.size.y, 20.0, view.y - subtitle.size.y - 20.0))
