class_name ChoiceList
extends CanvasLayer
## Dialogue choices (game-design.md §9): the allowed responses as lines of pale
## text on a band of smoke near the bottom of the screen. Hovering lights a line;
## clicking it picks it. Mouse only.

signal picked(index: int)

const LINE_HEIGHT := 54.0

var is_open := false

var _band: Control
var _list: VBoxContainer


func _ready() -> void:
	layer = 61
	_band = Control.new()
	_band.name = "Band"
	_band.set_anchors_preset(Control.PRESET_FULL_RECT)
	_band.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_band.visible = false
	add_child(_band)
	var smoke := TextureRect.new()
	smoke.name = "Smoke"
	smoke.texture = InventoryPanel._smoke_gradient()
	smoke.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	smoke.offset_top = -340.0
	smoke.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	smoke.stretch_mode = TextureRect.STRETCH_SCALE
	smoke.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_band.add_child(smoke)
	_list = VBoxContainer.new()
	_list.name = "Choices"
	_list.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_list.offset_left = 220.0
	_list.offset_right = -220.0
	_list.offset_top = -300.0
	_list.offset_bottom = -40.0
	_list.alignment = BoxContainer.ALIGNMENT_END
	_list.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_band.add_child(_list)


## Shows `texts` and waits for one to be picked; returns its index.
func choose(texts: PackedStringArray) -> int:
	for child in _list.get_children():
		child.queue_free()
	for i in texts.size():
		_list.add_child(_make_line(texts[i], i))
	is_open = true
	_band.visible = true
	var index: int = await picked
	is_open = false
	_band.visible = false
	return index


## The index of the choice reading `text`, or -1 (tests and scripted runs).
func index_of(text: String) -> int:
	var lines := _list.get_children().filter(func(line: Node) -> bool: return not line.is_queued_for_deletion())
	for i in lines.size():
		if (lines[i] as Label).text == text:
			return i
	return -1


## Picks choice `index` as a click would (tests, accessibility hooks).
func pick(index: int) -> void:
	if is_open:
		picked.emit(index)


func _make_line(text: String, index: int) -> Label:
	var line := Label.new()
	line.name = "Choice%d" % index
	line.text = text
	line.custom_minimum_size.y = LINE_HEIGHT
	line.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	line.add_theme_font_size_override(&"font_size", 34)
	line.add_theme_color_override(&"font_outline_color", Color.BLACK)
	line.add_theme_constant_override(&"outline_size", 10)
	line.mouse_filter = Control.MOUSE_FILTER_STOP
	line.modulate = Color(0.72, 0.75, 0.82)
	line.mouse_entered.connect(func() -> void: line.modulate = Color(1.0, 1.0, 1.0))
	line.mouse_exited.connect(func() -> void: line.modulate = Color(0.72, 0.75, 0.82))
	line.gui_input.connect(func(event: InputEvent) -> void:
		var click := event as InputEventMouseButton
		if click and click.pressed and click.button_index == MOUSE_BUTTON_LEFT:
			get_viewport().set_input_as_handled()
			pick(index))
	return line
