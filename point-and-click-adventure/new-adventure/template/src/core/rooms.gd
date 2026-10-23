extends Node
## Loads rooms, carries the player between them and plays the transition
## (docs/technical-plan.md §5.1). Rooms live as children of this node.

## The new room is in place, while the screen is still black.
signal room_changed(room: Room)
## The new room has faded in and input is free.
signal room_shown(room: Room)

const ROOM_PATH := "res://content/rooms/%s/%s.tscn"
const PLAYER_SCENE := "res://content/characters/hero/hero.tscn"
const FADE_SECONDS := 0.35

var current: Room
var player: Actor
## The marker the player entered the current room by.
var current_entry: StringName = &"default"
## Awaited with the new room while a fade keeps the screen black, for work
## that would otherwise stall the room's first moments (shader warm-up).
var while_black: Array[Callable] = []

var _fade: ColorRect


func _ready() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 100
	add_child(layer)
	_fade = ColorRect.new()
	_fade.color = Color.BLACK
	_fade.modulate.a = 0.0
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_fade)


## Changes to `room_id`, placing the player at the marker named `entry`.
## `transition` is "fade" or "none".
func goto(room_id: StringName, entry: StringName = &"default", transition: StringName = &"fade") -> void:
	var scene := load(ROOM_PATH % [room_id, room_id]) as PackedScene
	if scene == null:
		push_error("Room not found: %s" % room_id)
		return
	Interaction.locked += 1
	var fade := transition == &"fade"
	var from: StringName = current.room_id if current else &""
	if fade:
		if current:
			await _fade_to(1.0)
		else:
			_fade.modulate.a = 1.0
	_unload_current()
	var room := scene.instantiate() as Room
	if room.room_id == &"":
		room.room_id = room_id
	add_child(room)
	if player == null:
		player = (load(PLAYER_SCENE) as PackedScene).instantiate() as Actor
	room.actors.add_child(player)
	player.global_position = room.marker_position(entry)
	current = room
	current_entry = entry
	room._on_enter(from)
	room_changed.emit(room)
	# Let the navigation map take in the new walk area before anyone walks.
	await get_tree().physics_frame
	await get_tree().physics_frame
	if fade:
		for step in while_black:
			if is_instance_valid(room):
				await step.call(room)
		await _fade_to(0.0)
	Interaction.locked -= 1
	room._on_shown()
	room_shown.emit(room)


## Frees the current room and the player. Used by tests and by returning to the menu.
func clear() -> void:
	_unload_current()
	if player:
		player.free()
		player = null
	_fade.modulate.a = 0.0


func _unload_current() -> void:
	if current == null:
		return
	current._on_exit()
	if player and player.get_parent():
		player.get_parent().remove_child(player)
	remove_child(current)
	current.free()
	current = null


func _fade_to(alpha: float) -> void:
	var tween := create_tween()
	tween.tween_property(_fade, "modulate:a", alpha, FADE_SECONDS)
	await tween.finished
