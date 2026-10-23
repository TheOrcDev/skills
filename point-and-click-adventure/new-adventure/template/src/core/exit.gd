class_name Exit
extends Hotspot
## A way out of the room (game-design.md §8). A click walks the hero there and
## leaves; a double-click leaves at once. Look falls back like any hotspot
## unless the room answers `look_<id>`.

@export var target_room: StringName
## The marker in the target room where the hero arrives.
@export var target_entry: StringName = &"default"
## Which way the exit cursor points: "left", "right", "up" or "down".
@export var direction: StringName = &"right"
## A story flag the way needs: until GameState has it, the exit
## doesn't lead anywhere and the room answers `locked_<id>()` instead.
@export var requires_flag: StringName = &""


func _init() -> void:
	default_verb = &"walk"


## Leaves after this verb has returned: changing rooms frees this exit, and a
## coroutine still running on it would never finish (Interaction would stay
## locked). Rooms is looked up by path so the room scaffold, which runs without
## autoloads, can still compile this class.
func on_walk() -> void:
	if not is_open():
		var room := Room.of(self)
		var answer := "locked_%s" % id
		if room and room.has_method(answer):
			await Callable(room, answer).call()
		return
	var rooms := get_node_or_null(^"/root/Rooms")
	if target_room != &"" and rooms:
		rooms.goto.call_deferred(target_room, target_entry, &"fade")


## Whether the way is open: no flag needed, or GameState has it. GameState is
## found by path, like Rooms, for the scaffolds.
func is_open() -> bool:
	if requires_flag == &"":
		return true
	var state := get_node_or_null(^"/root/GameState")
	return state != null and bool(state.get_flag(requires_flag))
