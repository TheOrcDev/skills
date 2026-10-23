extends Node
## Plays cutscenes (technical-plan.md §6.3). While one plays, input is
## locked and the letterbox bars are in, and the Skip button (held 0.6 s) or
## Esc skips it.

signal started(id: StringName)
signal finished(id: StringName)

const BARS_SECONDS := 0.5

## The steps of the scene playing, or null.
var current: CutsceneSteps
var letterbox: Letterbox
var skip_button: SkipButton

var _fade: ColorRect


func _ready() -> void:
	letterbox = Letterbox.new()
	letterbox.name = "Letterbox"
	add_child(letterbox)
	var layer := CanvasLayer.new()
	layer.layer = 95
	add_child(layer)
	_fade = ColorRect.new()
	_fade.name = "Fade"
	_fade.color = Color.BLACK
	_fade.modulate.a = 0.0
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_fade)
	skip_button = SkipButton.new()
	skip_button.name = "SkipButton"
	skip_button.skipped.connect(skip)
	skip_button.process_mode = Node.PROCESS_MODE_DISABLED
	add_child(skip_button)


## Plays `cutscene` and returns once it has ended, watched or skipped. The fade
## stays where the script left it, so a scene can end on black before a room
## change.
func play(cutscene: Cutscene) -> void:
	if current:
		push_error("Cutscene %s asked to play over another" % cutscene.id)
		return
	current = CutsceneSteps.new(get_tree(), _fade)
	Interaction.locked += 1
	started.emit(cutscene.id)
	letterbox.show_bars(BARS_SECONDS)
	skip_button.reset()
	skip_button.process_mode = Node.PROCESS_MODE_INHERIT
	await cutscene.run(current)
	skip_button.process_mode = Node.PROCESS_MODE_DISABLED
	skip_button.reset()
	Say.fast_forward = false
	letterbox.hide_bars(0.0 if current.skipping else BARS_SECONDS)
	GameState.saw_cutscene(cutscene.id)
	current = null
	Interaction.locked -= 1
	finished.emit(cutscene.id)


## How far the runner's fade is down: 0 clear, 1 black.
func fade_amount() -> float:
	return _fade.modulate.a


## Drops the runner's fade at once. Call it under another cover, such as a
## room change that starts on black, after a scene that ended on black.
func clear_fade() -> void:
	_fade.modulate.a = 0.0


## Skips the cutscene playing.
func skip() -> void:
	if current:
		current.skip()
