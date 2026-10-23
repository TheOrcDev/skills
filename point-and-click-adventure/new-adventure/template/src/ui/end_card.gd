class_name EndCard
extends CanvasLayer
## A card of large spaced capitals over a smaller line, in the style of the
## title screen, shown over black at a part's end (for example where a demo
## stops).

var _card: VBoxContainer


func _init(heading: String, line: String) -> void:
	layer = 110
	_card = VBoxContainer.new()
	_card.set_anchors_preset(Control.PRESET_FULL_RECT)
	_card.alignment = BoxContainer.ALIGNMENT_CENTER
	_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card.modulate.a = 0.0
	add_child(_card)
	_card.add_child(_label(heading, 96, 30))
	_card.add_child(_label(line, 36, 8))


func _label(text: String, size: int, spacing: int) -> Label:
	var label := Label.new()
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var font := FontVariation.new()
	font.spacing_glyph = spacing
	label.add_theme_font_override(&"font", font)
	label.add_theme_font_size_override(&"font_size", size)
	label.add_theme_color_override(&"font_color", Color(0.9, 0.91, 0.94))
	return label


func fade_in() -> void:
	create_tween().tween_property(_card, ^"modulate:a", 1.0, 1.2)
