class_name TopBar
extends CanvasLayer
## The bar along the top edge (game-design.md §9). Pushing the
## cursor against the top of the screen slides it down on a band of smoke, with
## Journal, Save, Load, Settings, Reveal hotspots, Main menu and Quit; it slides away once
## the cursor leaves it. A browser page cannot quit, so the web build has no
## Quit.

signal chosen(id: StringName)

const HEIGHT := 100.0
## How close to the top edge the cursor must come.
const EDGE := 6.0
const SLIDE_SECONDS := 0.18
const ENTRIES := [
	[&"journal", "Journal"],
	[&"save", "Save"],
	[&"load", "Load"],
	[&"settings", "Settings"],
	[&"hotspots", "Reveal hotspots"],
	[&"menu", "Main menu"],
	[&"quit", "Quit"],
]

var is_open := false

var _band: Control
var _slide: Tween


func _ready() -> void:
	layer = 65
	_band = Control.new()
	_band.name = "Band"
	_band.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_band.offset_bottom = HEIGHT
	_band.position.y = -HEIGHT
	_band.mouse_filter = Control.MOUSE_FILTER_STOP
	_band.visible = false
	_band.gui_input.connect(func(event: InputEvent) -> void:
		var click := event as InputEventMouseButton
		if click and click.pressed and click.button_index == MOUSE_BUTTON_RIGHT:
			_band.get_viewport().set_input_as_handled()
			close())
	add_child(_band)
	var smoke := TextureRect.new()
	smoke.name = "Smoke"
	smoke.texture = InventoryPanel._smoke_gradient()
	smoke.flip_v = true
	smoke.set_anchors_preset(Control.PRESET_FULL_RECT)
	smoke.offset_bottom = 40.0
	smoke.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	smoke.stretch_mode = TextureRect.STRETCH_SCALE
	smoke.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_band.add_child(smoke)
	var row := HBoxContainer.new()
	row.name = "Entries"
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override(&"separation", 72)
	row.set_anchors_preset(Control.PRESET_FULL_RECT)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_band.add_child(row)
	for entry: Array in ENTRIES:
		if entry[0] == &"quit" and OS.has_feature("web"):
			continue
		var button := MenuScreen.text_button(entry[1], 34, choose.bind(entry[0]))
		button.name = String(entry[0]).capitalize()
		row.add_child(button)


## Follows the cursor: the bar comes down at the top edge while `allowed`, and
## goes once the cursor has left it or it is no longer allowed.
func follow(mouse: Vector2, allowed: bool) -> void:
	if not is_open and allowed and mouse.y <= EDGE:
		open()
	elif is_open and (not allowed or mouse.y > HEIGHT + 30.0):
		close()


func open() -> void:
	is_open = true
	_band.visible = true
	_slide_to(0.0)


func close() -> void:
	if not is_open:
		return
	is_open = false
	_slide_to(-HEIGHT)


## Gone at once, as when a page opens over it.
func hide_now() -> void:
	is_open = false
	if _slide:
		_slide.kill()
	_band.position.y = -HEIGHT
	_band.visible = false


func choose(id: StringName) -> void:
	hide_now()
	chosen.emit(id)


func _slide_to(y: float) -> void:
	if _slide:
		_slide.kill()
	_slide = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	_slide.tween_property(_band, ^"position:y", y, SLIDE_SECONDS)
	if y < 0.0:
		_slide.tween_callback(func() -> void: _band.visible = false)
