class_name SkipButton
extends CanvasLayer
## The Skip control for cutscenes (game-design.md §8, technical-plan.md §6.3).
## Moving the mouse shows "Skip" in the corner for a few seconds. Pressing and
## holding it fills a ring, and after 0.6 s it fires `skipped`. Esc skips at
## once. A click alone never skips, so nobody loses a scene by accident.

signal skipped

const HOLD_SECONDS := 0.6
## How long the button stays after the mouse stops moving.
const SHOWN_SECONDS := 2.5
const FADE_SECONDS := 0.25
const RING_RADIUS := 26.0

var _button: Control
var _ring: Control
## Seconds the button has been held, or -1 when it is not pressed.
var _held := -1.0
var _shown_for := 0.0
var _fired := false


func _ready() -> void:
	layer = 90
	_button = HBoxContainer.new()
	_button.name = "Button"
	_button.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_button.offset_left = -250.0
	_button.offset_top = -130.0
	_button.offset_right = -60.0
	_button.offset_bottom = -60.0
	_button.alignment = BoxContainer.ALIGNMENT_END
	_button.add_theme_constant_override(&"separation", 18)
	_button.mouse_filter = Control.MOUSE_FILTER_STOP
	_button.modulate.a = 0.0
	_button.visible = false
	_button.gui_input.connect(_on_button_input)
	_button.mouse_exited.connect(release)
	add_child(_button)
	var label := MenuScreen.text_line("Skip", 36, Color(0.9, 0.91, 0.94))
	label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_button.add_child(label)
	_ring = Control.new()
	_ring.name = "Ring"
	_ring.custom_minimum_size = Vector2.ONE * RING_RADIUS * 2.0 + Vector2(8, 8)
	_ring.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ring.draw.connect(_draw_ring)
	_button.add_child(_ring)


func _process(delta: float) -> void:
	if _held >= 0.0:
		_held += delta
		_shown_for = SHOWN_SECONDS
		_ring.queue_redraw()
		if _held >= HOLD_SECONDS:
			fire()
	_shown_for = maxf(_shown_for - delta, 0.0)
	var target := 1.0 if _shown_for > 0.0 and not _fired else 0.0
	_button.modulate.a = move_toward(_button.modulate.a, target, delta / FADE_SECONDS)
	_button.visible = _button.modulate.a > 0.0


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		reveal()
	elif event.is_action_pressed(&"ui_cancel"):
		get_viewport().set_input_as_handled()
		fire()


## Ready for another scene: hidden, not held, not fired.
func reset() -> void:
	_fired = false
	_held = -1.0
	_shown_for = 0.0
	_button.modulate.a = 0.0
	_button.visible = false


## Shows the button for a few seconds, as moving the mouse does.
func reveal() -> void:
	_shown_for = SHOWN_SECONDS


## The button goes down, as a left press on it does.
func press() -> void:
	if not _fired:
		reveal()
		_held = 0.0


## The button comes up before the hold is done: nothing happens.
func release() -> void:
	_held = -1.0
	_ring.queue_redraw()


func fire() -> void:
	if _fired:
		return
	_fired = true
	_held = -1.0
	skipped.emit()


func _on_button_input(event: InputEvent) -> void:
	var click := event as InputEventMouseButton
	if click and click.button_index == MOUSE_BUTTON_LEFT:
		get_viewport().set_input_as_handled()
		if click.pressed:
			press()
		else:
			release()


func _draw_ring() -> void:
	var center := _ring.size / 2.0
	_ring.draw_arc(center, RING_RADIUS, 0.0, TAU, 48, Color(0.72, 0.75, 0.82, 0.35), 3.0, true)
	if _held > 0.0:
		var sweep := TAU * clampf(_held / HOLD_SECONDS, 0.0, 1.0)
		_ring.draw_arc(center, RING_RADIUS, -PI / 2.0, -PI / 2.0 + sweep, 48, Color(1, 1, 1, 0.95), 4.0, true)
