class_name InventoryPanel
extends CanvasLayer
## The inventory overlay (game-design.md §8–9): a band of the hero's smoke along
## the bottom of the screen with the carried items suspended in it.
## - Left-click an item to pick it up on the cursor; the band stays open, so a
##   left-click on another item combines the two, and on the held one puts it
##   back.
## - Right-click an item to examine it: a close-up and its look line.
## - A left click outside the band closes it, and a held item goes on to
##   whatever is under the cursor. A right click there closes it and drops the
##   item.

signal examined(item: ItemDef)

const BAND_HEIGHT := 230.0
const SLOT_SIZE := Vector2(132, 132)

var is_open := false

var _band: Control
var _slots: HBoxContainer
var _label: Label
var _closeup: TextureRect


func _ready() -> void:
	layer = 40
	_band = Control.new()
	_band.name = "Band"
	_band.set_anchors_preset(Control.PRESET_FULL_RECT)
	_band.mouse_filter = Control.MOUSE_FILTER_STOP
	_band.gui_input.connect(_on_backdrop_input)
	add_child(_band)
	var smoke := TextureRect.new()
	smoke.name = "Smoke"
	smoke.texture = _smoke_gradient()
	smoke.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	smoke.offset_top = -BAND_HEIGHT
	smoke.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	smoke.stretch_mode = TextureRect.STRETCH_SCALE
	smoke.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_band.add_child(smoke)
	_slots = HBoxContainer.new()
	_slots.name = "Slots"
	_slots.alignment = BoxContainer.ALIGNMENT_CENTER
	_slots.add_theme_constant_override(&"separation", 28)
	_slots.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_slots.offset_top = -BAND_HEIGHT + 40.0
	_slots.offset_bottom = -40.0
	_slots.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_band.add_child(_slots)
	_label = Label.new()
	_label.name = "Label"
	_label.add_theme_font_size_override(&"font_size", 30)
	_label.add_theme_color_override(&"font_outline_color", Color.BLACK)
	_label.add_theme_constant_override(&"outline_size", 10)
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_label.offset_top = -BAND_HEIGHT - 48.0
	_label.offset_bottom = -BAND_HEIGHT
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_band.add_child(_label)
	_closeup = TextureRect.new()
	_closeup.name = "Closeup"
	_closeup.custom_minimum_size = Vector2(420, 420)
	_closeup.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_closeup.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_closeup.set_anchors_preset(Control.PRESET_CENTER)
	_closeup.offset_left = -210.0
	_closeup.offset_top = -280.0
	_closeup.offset_right = 210.0
	_closeup.offset_bottom = 140.0
	_closeup.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_closeup.visible = false
	add_child(_closeup)
	_band.visible = false
	Inventory.changed.connect(_rebuild)


func open() -> void:
	_rebuild()
	is_open = true
	_band.visible = true
	_label.text = ""


func close() -> void:
	is_open = false
	_band.visible = false


func toggle() -> void:
	if is_open:
		close()
	else:
		open()


## The slot showing `id`, for tests and tutorials.
func slot_for(id: StringName) -> Control:
	for slot in _slots.get_children():
		if slot.get_meta(&"item") == id:
			return slot
	return null


func _rebuild() -> void:
	for slot in _slots.get_children():
		slot.queue_free()
	for item in Inventory.items():
		_slots.add_child(_make_slot(item))


func _make_slot(item: ItemDef) -> Control:
	var slot := TextureRect.new()
	slot.name = "Slot_%s" % item.id
	slot.set_meta(&"item", item.id)
	slot.custom_minimum_size = SLOT_SIZE
	slot.texture = item.icon if item.icon else _placeholder_icon()
	slot.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	slot.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	slot.mouse_filter = Control.MOUSE_FILTER_STOP
	slot.mouse_entered.connect(_on_hover.bind(item))
	slot.mouse_exited.connect(func() -> void: _label.text = "")
	slot.gui_input.connect(_on_slot_input.bind(item))
	return slot


func _on_hover(item: ItemDef) -> void:
	if Inventory.held and Inventory.held != item:
		_label.text = "Use %s with %s" % [Inventory.held.display_name, item.display_name]
	else:
		_label.text = item.display_name


func _on_slot_input(event: InputEvent, item: ItemDef) -> void:
	var click := event as InputEventMouseButton
	if click == null or not click.pressed:
		return
	get_viewport().set_input_as_handled()
	if click.button_index == MOUSE_BUTTON_LEFT:
		if Inventory.held and Inventory.held != item:
			var first := Inventory.held.id
			Inventory.drop()
			if Inventory.combine(first, item.id) == &"":
				close()
				await Say.fallback(&"combine")
		elif Inventory.held:
			Inventory.drop()
		else:
			Inventory.hold(item.id)
	elif click.button_index == MOUSE_BUTTON_RIGHT:
		_examine(item)


func _examine(item: ItemDef) -> void:
	close()
	_closeup.texture = item.icon if item.icon else _placeholder_icon()
	_closeup.visible = true
	examined.emit(item)
	if item.look_file != &"" and item.look_cue != &"":
		await Say.line(item.look_file, item.look_cue)
	else:
		await get_tree().create_timer(1.2).timeout
	_closeup.visible = false


func _on_backdrop_input(event: InputEvent) -> void:
	var click := event as InputEventMouseButton
	if click == null or not click.pressed:
		return
	get_viewport().set_input_as_handled()
	close()
	if click.button_index == MOUSE_BUTTON_RIGHT:
		Inventory.drop()
	elif click.button_index == MOUSE_BUTTON_LEFT and Inventory.held:
		Interaction.click_at(Interaction.world_at(click.position))


static func _smoke_gradient() -> Texture2D:
	var gradient := Gradient.new()
	gradient.set_color(0, Color(0.02, 0.02, 0.03, 0.0))
	gradient.set_color(1, Color(0.02, 0.02, 0.03, 0.92))
	gradient.add_point(0.35, Color(0.02, 0.02, 0.03, 0.7))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.fill_from = Vector2(0.5, 0.0)
	texture.fill_to = Vector2(0.5, 1.0)
	texture.width = 4
	texture.height = 64
	return texture


static func _placeholder_icon() -> Texture2D:
	var gradient := Gradient.new()
	gradient.set_color(0, Color(0.55, 0.58, 0.66, 1.0))
	gradient.set_color(1, Color(0.1, 0.1, 0.12, 0.0))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(0.5, 0.0)
	texture.width = 64
	texture.height = 64
	return texture
