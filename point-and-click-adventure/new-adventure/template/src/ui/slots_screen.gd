class_name SlotsScreen
extends MenuScreen
## The save and load pages: each slot as a card with its
## thumbnail, the room, and when it was saved. Saving over a used slot takes a
## second click. The load page starts with the autosave, and empty slots cannot
## be picked.

## A slot was saved into, or chosen to load.
signal picked(slot: int)

const CARD_SIZE := Vector2(320, 180)

## True for the save page, false for the load page.
var saving := true
## What a save made here keeps as its thumbnail: the game as it was before the
## menu opened.
var picture: Image
## The used slot waiting for a second click to be saved over, or -1.
var armed := -1

var _cards := {}


func _build(content: VBoxContainer) -> void:
	var grid := GridContainer.new()
	grid.name = "Slots"
	grid.columns = 3 if saving else 4
	grid.add_theme_constant_override(&"h_separation", 48)
	grid.add_theme_constant_override(&"v_separation", 40)
	grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(grid)
	var slots: Array[int] = []
	if not saving:
		slots.append(Saves.AUTOSAVE)
	for slot in range(1, Saves.SLOTS + 1):
		slots.append(slot)
	for slot in slots:
		var card := _card(slot)
		_cards[slot] = card
		grid.add_child(card)


## Saves into `slot` or loads it, as a click on its card does.
func pick(slot: int) -> void:
	if saving:
		if Saves.has_save(slot) and armed != slot:
			armed = slot
			_note(slot, "Click again to save over it")
			return
		Saves.save(slot, picture)
	elif not Saves.has_save(slot) or Saves.read(slot).is_empty():
		return
	picked.emit(slot)
	close()


## The card for `slot`, for tests.
func card(slot: int) -> Control:
	return _cards.get(slot)


func _card(slot: int) -> Control:
	var data := Saves.read(slot)
	var card := VBoxContainer.new()
	card.name = "Slot%d" % slot
	card.add_theme_constant_override(&"separation", 6)
	card.mouse_filter = Control.MOUSE_FILTER_STOP
	var usable := saving or not data.is_empty()
	card.modulate = IDLE if usable else Color(0.45, 0.47, 0.52)
	var picture_rect := TextureRect.new()
	picture_rect.name = "Picture"
	picture_rect.custom_minimum_size = CARD_SIZE
	picture_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	picture_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	picture_rect.texture = Saves.thumbnail(slot) if not data.is_empty() else null
	picture_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var frame := Panel.new()
	frame.custom_minimum_size = CARD_SIZE
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.04, 0.04, 0.06, 0.7)
	style.set_border_width_all(2)
	style.border_color = Color(0.72, 0.75, 0.82, 0.35)
	frame.add_theme_stylebox_override(&"panel", style)
	frame.add_child(picture_rect)
	card.add_child(frame)
	card.add_child(text_line("Autosave" if slot == Saves.AUTOSAVE else "Slot %d" % slot, 30, Color.WHITE))
	var detail := text_line(_describe(data), 24)
	detail.name = "Detail"
	card.add_child(detail)
	if usable:
		card.mouse_entered.connect(func() -> void: card.modulate = LIT)
		card.mouse_exited.connect(func() -> void: card.modulate = IDLE)
		card.gui_input.connect(func(event: InputEvent) -> void:
			var click := event as InputEventMouseButton
			if click and click.pressed and click.button_index == MOUSE_BUTTON_LEFT:
				card.get_viewport().set_input_as_handled()
				pick(slot))
	return card


func _note(slot: int, text: String) -> void:
	var detail := _cards[slot].get_node(^"Detail") as Label
	detail.text = text


## "Gatehouse · 10 Oct 23:46 · 1:05 played", in local time.
static func _describe(data: Dictionary) -> String:
	if data.is_empty():
		return "Empty"
	var parts: PackedStringArray = []
	if not str(data.get("room_name", "")).is_empty():
		parts.append(str(data["room_name"]))
	var saved_at := str(data.get("saved_at", ""))
	if not saved_at.is_empty():
		var bias: int = Time.get_time_zone_from_system().get("bias", 0)
		var when := Time.get_datetime_dict_from_unix_time(Time.get_unix_time_from_datetime_string(saved_at) + bias * 60)
		parts.append("%d %s %02d:%02d" % [when.day, ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][when.month - 1], when.hour, when.minute])
	var minutes := floori(float(data.get("play_seconds", 0.0)) / 60.0)
	parts.append("%d:%02d played" % [floori(minutes / 60.0), minutes % 60])
	return " · ".join(parts)
