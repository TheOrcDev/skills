class_name MenuScreen
extends CanvasLayer
## A page opened from the top bar: a veil of smoke over the
## paused game, a title, and the page's own content, built by `_build()`. Esc, a
## right-click or the ‹ glyph closes it.

signal closed

const IDLE := Color(0.72, 0.75, 0.82)
const LIT := Color(1.0, 1.0, 1.0)

var title := ""

var _closed := false


func _ready() -> void:
	layer = 70
	process_mode = Node.PROCESS_MODE_ALWAYS
	var veil := ColorRect.new()
	veil.name = "Veil"
	veil.color = Color(0.01, 0.01, 0.02, 0.86)
	veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	veil.mouse_filter = Control.MOUSE_FILTER_STOP
	veil.gui_input.connect(func(event: InputEvent) -> void:
		var click := event as InputEventMouseButton
		if click and click.pressed and click.button_index == MOUSE_BUTTON_RIGHT:
			veil.get_viewport().set_input_as_handled()
			close())
	add_child(veil)
	var heading := Label.new()
	heading.name = "Title"
	heading.text = title
	heading.add_theme_font_size_override(&"font_size", 56)
	heading.add_theme_color_override(&"font_outline_color", Color.BLACK)
	heading.add_theme_constant_override(&"outline_size", 12)
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	heading.set_anchors_preset(Control.PRESET_TOP_WIDE)
	heading.offset_top = 70.0
	heading.offset_bottom = 150.0
	heading.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(heading)
	var back := text_button("‹", 72, close)
	back.name = "Back"
	back.position = Vector2(34, 10)
	add_child(back)
	var content := VBoxContainer.new()
	content.name = "Content"
	content.alignment = BoxContainer.ALIGNMENT_CENTER
	content.set_anchors_preset(Control.PRESET_FULL_RECT)
	content.offset_top = 170.0
	content.offset_bottom = -80.0
	content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(content)
	_build(content)


func close() -> void:
	if _closed:
		return
	_closed = true
	closed.emit()
	queue_free()


## Fills the page. Subclasses add their controls to `content`.
func _build(_content: VBoxContainer) -> void:
	pass


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"ui_cancel"):
		get_viewport().set_input_as_handled()
		close()


## A line of pale text that lights under the cursor and runs `action` on a left
## click: the menus' button.
static func text_button(text: String, font_size: int, action: Callable) -> Label:
	var button := Label.new()
	button.text = text
	button.add_theme_font_size_override(&"font_size", font_size)
	button.add_theme_color_override(&"font_outline_color", Color.BLACK)
	button.add_theme_constant_override(&"outline_size", 10)
	button.mouse_filter = Control.MOUSE_FILTER_STOP
	button.modulate = IDLE
	button.mouse_entered.connect(func() -> void: button.modulate = LIT)
	button.mouse_exited.connect(func() -> void: button.modulate = IDLE)
	button.gui_input.connect(func(event: InputEvent) -> void:
		var click := event as InputEventMouseButton
		if click and click.pressed and click.button_index == MOUSE_BUTTON_LEFT:
			button.get_viewport().set_input_as_handled()
			action.call())
	return button


## Plain, centred text for a page.
static func text_line(text: String, font_size: int, color := IDLE) -> Label:
	var line := Label.new()
	line.text = text
	line.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	line.add_theme_font_size_override(&"font_size", font_size)
	line.add_theme_color_override(&"font_color", color)
	line.add_theme_color_override(&"font_outline_color", Color.BLACK)
	line.add_theme_constant_override(&"outline_size", 8)
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return line
