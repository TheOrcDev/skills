class_name Playthrough
extends RefCounted
## Plays a puzzle chain through the paths a player's mouse takes: clicks for
## default verbs, the verb coin for the others, inventory slots, dialogue
## choices and exits (shared by every part's playthrough
## ). Subclasses write run(); a GUT test and a QA scenario each
## run it.

## Called as check.call(ok, what) after each step that must have worked.
var check: Callable
## Called as await shot.call(name) at the chain's main moments, or not at all.
var shot: Callable
## Lines are cut short as they start; off, they play at reading pace (for a
## recording).
var skip_lines := true
## The ids of the lines spoken so far.
var lines: Array[String] = []

var _tree: SceneTree
var _listen: Callable


func _init(tree: SceneTree, on_check: Callable, on_shot := Callable()) -> void:
	_tree = tree
	check = on_check
	shot = on_shot


func run() -> void:
	pass


## Starts noting (and, with skip_lines, cutting short) every line spoken.
func _start_listening() -> void:
	_listen = func(id: String, _speaker: String, _text: String) -> void:
		lines.append(id)
		if skip_lines:
			Say.skip.call_deferred()
	Say.line_started.connect(_listen)


func _stop_listening() -> void:
	if _listen.is_valid() and Say.line_started.is_connected(_listen):
		Say.line_started.disconnect(_listen)


## Uses the inventory item `id` on a hotspot: picked in the band, then a click
## outside it on the hotspot.
func _give(id: StringName, hotspot_name: String) -> void:
	Interaction.right_click()
	await _tree.process_frame
	await _click_slot(id)
	await _click_outside(_tree.root.get_canvas_transform() * _spot(hotspot_name).focus_point())
	await _settle()


## Walks into `room` by double-clicking an exit; checks it arrived.
func _spot(hotspot_name: String) -> Hotspot:
	return Rooms.current.hotspots.get_node(hotspot_name) as Hotspot


## A left click on a hotspot: The hero walks there and runs its default verb.
func _click(hotspot_name: String) -> void:
	await Interaction.click_at(_spot(hotspot_name).focus_point())
	await _settle()


## A click on someone: the talk starts, and its choices are picked next with
## _choose (a conversation holds the player until it ends, so no settling).
func _talk(hotspot_name: String) -> void:
	Interaction.click_at(_spot(hotspot_name).focus_point())


## Holds the button on a hotspot until the verb coin opens, then lets go over
## `verb`.
func _verb(hotspot_name: String, verb: StringName) -> void:
	var world := _spot(hotspot_name).focus_point()
	Interaction.press_at(world, _tree.root.get_canvas_transform() * world)
	await _tree.create_timer(Interaction.COIN_HOLD_SECONDS + 0.1).timeout
	check.call(Interaction.coin.is_open, "the verb coin opens on %s" % hotspot_name)
	var glyph := Interaction.coin.glyph_position(verb)
	Interaction.coin.point_at(glyph)
	await Interaction.release_at(world, glyph)
	await _settle()


## Picks the dialogue choice reading `text` once the choices show.
func _choose(text: String, shot_name := "") -> void:
	while not Say.choices.is_open:
		await _tree.process_frame
	var index := Say.choices.index_of(text)
	check.call(index >= 0, "the choice \"%s\" is offered" % text)
	if not shot_name.is_empty():
		await _shot(shot_name)
	Say.choices.pick(maxi(index, 0))


func _leave(exit_name: String, room: StringName) -> void:
	Interaction.double_click_at(_spot(exit_name).focus_point())
	await Rooms.room_changed
	await _settle()
	check.call(Rooms.current.room_id == room, "into %s" % room)


## A left click on an item in the open inventory.
func _click_slot(id: StringName) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	Interaction.inventory.slot_for(id).gui_input.emit(event)
	await _tree.process_frame


## A left click outside the open inventory's band, at `screen`.
func _click_outside(screen: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	event.position = screen
	Interaction.inventory.get_node(^"Band").gui_input.emit(event)
	await _tree.process_frame


func _shot(shot_name: String) -> void:
	if shot.is_valid():
		await shot.call(shot_name)


## Waits until the hero stands still and the player could act again.
func _settle() -> void:
	await _tree.process_frame
	while Interaction.locked > 0 or Say.speaking or Rooms.player.is_walking or Closeups.busy:
		await _tree.process_frame

## A click on a close-up's hotspot.
func _closeup_click(hotspot_name: String) -> void:
	await Interaction.click_at((Closeups.current.hotspots.get_node(hotspot_name) as Hotspot).focus_point())
	await _settle()


## Backs out of the open close-up.
func _close() -> void:
	Interaction.right_click()
	while Closeups.current != null or Closeups.busy:
		await _tree.process_frame
	await _settle()


## Waits until the memory has been recorded and its cutscene has ended.
func _until_memory(memory: StringName) -> void:
	while not memory in GameState.memories or Cutscenes.current != null:
		await _tree.process_frame
	await _settle()
	check.call(memory in GameState.memories, "the memory %s" % memory)
