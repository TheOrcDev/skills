extends Node
## Mouse input for play: hover labels, walking, running hotspot verbs and the
## inventory (docs/game-design.md §8).
## - A left click on a hotspot runs its default verb, or uses the held item on it.
## - Holding the left button on a hotspot opens the verb coin; releasing over a
##   glyph runs that verb.
## - A right click opens the inventory, or drops the held item.
## - A click on the hero asks them for a hint, where nothing usable is
##   behind them: a hotspot they stand in front of still takes its clicks.

signal interacted(hotspot: Hotspot, verb: StringName)

## Above zero, play input is ignored (transitions, dialogue, cutscenes).
var locked := 0
var hovered: Hotspot
## The cursor is on the hero, who gives a hint when clicked.
var over_player := false
var inventory: InventoryPanel
var coin: VerbCoin

## How long the left button must be held on a hotspot to open the verb coin.
const COIN_HOLD_SECONDS := 0.3

var _press_hotspot: Hotspot
var _press_world := Vector2.ZERO
var _press_screen := Vector2.ZERO
var _press_held := 0.0

var _label: Label


func _ready() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 50
	add_child(layer)
	_label = Label.new()
	_label.add_theme_font_size_override(&"font_size", 30)
	_label.add_theme_color_override(&"font_color", Color(0.95, 0.95, 0.95))
	_label.add_theme_color_override(&"font_outline_color", Color.BLACK)
	_label.add_theme_constant_override(&"outline_size", 10)
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_label.visible = false
	layer.add_child(_label)
	inventory = InventoryPanel.new()
	inventory.name = "InventoryPanel"
	add_child(inventory)
	coin = VerbCoin.new()
	coin.name = "VerbCoin"
	add_child(coin)
	Inventory.held_changed.connect(_on_held_changed)


func _exit_tree() -> void:
	# Let go of the drawn cursor while the renderer can still free it.
	Input.set_custom_mouse_cursor(null)


func _unhandled_input(event: InputEvent) -> void:
	var mouse := event as InputEventMouse
	if mouse == null or Rooms.current == null:
		return
	var world := world_at(mouse.position)
	if event is InputEventMouseMotion:
		if coin.is_open:
			coin.point_at(mouse.position)
		else:
			var hotspot := hotspot_at(world)
			if hotspot == null and _on_player(world):
				_hover_player(mouse.position)
			else:
				_set_hovered(hotspot, mouse.position)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if locked == 0 or coin.is_open:
			get_viewport().set_input_as_handled()
			if event.pressed and event.double_click:
				double_click_at(world)
			elif event.pressed:
				press_at(world, mouse.position)
			else:
				release_at(world, mouse.position)
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT:
		if locked == 0:
			get_viewport().set_input_as_handled()
			right_click()


## A double-click on an exit leaves at once, without the walk.
func double_click_at(world: Vector2) -> void:
	var exit := hotspot_at(world) as Exit
	if exit == null or locked > 0:
		return
	if not exit.is_open():
		use(exit, &"walk")
		return
	_press_hotspot = null
	Rooms.player.stop()
	await Rooms.goto(exit.target_room, exit.target_entry, &"fade")


## The left button goes down. On a hotspot (with no item held) the action waits
## for the release, to tell a click from a hold; anywhere else it acts at once.
func press_at(world: Vector2, screen: Vector2) -> void:
	if locked > 0:
		return
	var hotspot := hotspot_at(world)
	if hotspot == null or Inventory.held:
		click_at(world)
		return
	_press_hotspot = hotspot
	_press_world = world
	_press_screen = screen
	_press_held = 0.0


## The left button comes up: picks the coin's verb, or runs the default verb
## after a short click.
func release_at(world: Vector2, screen: Vector2) -> void:
	if coin.is_open:
		coin.point_at(screen)
		var verb := coin.close()
		var hotspot := _press_hotspot
		_press_hotspot = null
		if verb != &"" and hotspot:
			await use(hotspot, verb)
		return
	if _press_hotspot:
		_press_hotspot = null
		click_at(_press_world)


func _process(delta: float) -> void:
	if _press_hotspot and not coin.is_open:
		_press_held += delta
		if _press_held >= COIN_HOLD_SECONDS:
			_label.visible = false
			coin.open(_press_screen)


## A right click: closes the inventory (dropping a held item), drops the held
## item, backs out of a close-up, or opens the inventory.
func right_click() -> void:
	if inventory.is_open:
		inventory.close()
		Inventory.drop()
	elif Inventory.held:
		Inventory.drop()
	elif Closeups.current:
		Closeups.close()
	else:
		inventory.open()


## The world point under the screen point `screen`: room pixels, or in a
## close-up its own screen pixels.
func world_at(screen: Vector2) -> Vector2:
	return screen if Closeups.current else get_viewport().get_canvas_transform().affine_inverse() * screen


## A left click at a world position: use the hotspot there, or walk.
func click_at(world: Vector2) -> void:
	if locked > 0 or Rooms.current == null or Rooms.player == null:
		return
	var hotspot := hotspot_at(world)
	if hotspot == null and _on_player(world):
		await Hints.ask()
		return
	if hotspot and Inventory.held:
		await use_item(hotspot, Inventory.held)
	elif hotspot:
		await use(hotspot, hotspot.default_verb)
	elif Closeups.current == null:
		Rooms.player.walk_to(world)


## Walks the player to the hotspot, faces it and runs the verb, or a fallback line.
func use(hotspot: Hotspot, verb: StringName) -> void:
	if not await _approach(hotspot):
		return
	locked += 1
	_label.visible = false
	var handled: bool = await hotspot.handle(verb)
	if not handled:
		await Say.fallback(verb)
	locked -= 1
	interacted.emit(hotspot, verb)


## Walks the player to the hotspot and uses `item` on it: the hotspot's
## `on_item(item)` or the room's `item_<id>(item)`, or a fallback line.
func use_item(hotspot: Hotspot, item: ItemDef) -> void:
	if not await _approach(hotspot):
		return
	Inventory.drop()
	locked += 1
	_label.visible = false
	var handled: bool = await hotspot.handle(&"item", [item])
	if not handled:
		await Say.fallback(&"item")
	locked -= 1
	interacted.emit(hotspot, &"item")


## Walks the player to a room hotspot and faces it; close-up hotspots are at
## hand. Returns false if the walk was interrupted.
func _approach(hotspot: Hotspot) -> bool:
	if Closeup.of(hotspot):
		return true
	var player := Rooms.player
	var arrived: bool = await player.walk_to(hotspot.walk_point())
	if arrived:
		player.face_point(hotspot.focus_point())
	return arrived


func hotspot_at(world: Vector2) -> Hotspot:
	if Closeups.current:
		return Closeups.current.hotspot_at(world)
	if Rooms.current == null:
		return null
	var best: Hotspot = null
	for node in Rooms.current.hotspots.get_children():
		var hotspot := node as Hotspot
		if hotspot and hotspot.is_active() and hotspot.contains_point(world):
			if best == null or hotspot.pick_priority > best.pick_priority:
				best = hotspot
	return best


## Whether `world` is on the hero in the room (not in a close-up, and not with an
## item on the cursor, which is meant for something else). Callers check for a
## hotspot first: one behind the hero wins.
func _on_player(world: Vector2) -> bool:
	return Closeups.current == null and not Inventory.held and Rooms.player != null and Rooms.player.contains_point(world)


func _hover_player(screen: Vector2) -> void:
	if not over_player:
		over_player = true
		hovered = null
		Cursors.show(&"hotspot")
	_show_label(Rooms.player.speaker_name, screen)


func _set_hovered(hotspot: Hotspot, screen: Vector2) -> void:
	if (hotspot != hovered or over_player) and not Inventory.held:
		Cursors.show_for(hotspot)
	over_player = false
	hovered = hotspot
	if hotspot == null:
		_label.visible = false
		return
	var text := hotspot.display_name
	if Inventory.held:
		text = "Use %s on %s" % [Inventory.held.display_name, hotspot.display_name]
	_show_label(text, screen)


func _show_label(text: String, screen: Vector2) -> void:
	_label.visible = locked == 0
	if not _label.visible:
		return
	_label.text = text
	_label.reset_size()
	var view := get_viewport().get_visible_rect().size
	_label.position = Vector2(
		clampf(screen.x - _label.size.x / 2.0, 10.0, view.x - _label.size.x - 10.0),
		clampf(screen.y - _label.size.y - 40.0, 10.0, view.y - _label.size.y - 10.0))


## The held item rides on the cursor.
func _on_held_changed(item: ItemDef) -> void:
	if item and item.icon:
		var image := item.icon.get_image()
		if image:
			image.resize(64, 64)
			Input.set_custom_mouse_cursor(ImageTexture.create_from_image(image), Input.CURSOR_ARROW, Vector2(8, 8))
			return
	Cursors.show_for(hovered)

