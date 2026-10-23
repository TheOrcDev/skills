class_name Chapters
extends RefCounted
## The game's parts (a prologue, chapters) and the rooms in each, from
## content/chapters.json. A part's `flags` are the story flags a
## player holds on reaching its start, used to start QA mid-game.

const PATH := "res://content/chapters.json"

static var _parts: Array = []


static func parts() -> Array:
	if _parts.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		_parts = (parsed as Dictionary).get("parts", []) if parsed is Dictionary else []
	return _parts


static func part(id: StringName) -> Dictionary:
	for entry: Dictionary in parts():
		if StringName(entry["id"]) == id:
			return entry
	return {}


## The part a room belongs to, or an empty dictionary.
static func part_of(room_id: StringName) -> Dictionary:
	for entry: Dictionary in parts():
		if String(room_id) in entry["rooms"]:
			return entry
	return {}


## Every room in every part, in story order.
static func all_rooms() -> Array[StringName]:
	var rooms: Array[StringName] = []
	for entry: Dictionary in parts():
		for room: String in entry["rooms"]:
			rooms.append(StringName(room))
	return rooms


## Whether a room ships in this build: the browser build carries only the parts
## marked "web" (since #56 that is every part).
static func in_build(room_id: StringName) -> bool:
	return ResourceLoader.exists(Rooms.ROOM_PATH % [room_id, room_id])


## Gives GameState what a player holds on reaching `part`'s start: its story
## flags, memories and carried items (for QA and tests that start mid-game).
static func start_state(part: Dictionary) -> void:
	var state: Node = (Engine.get_main_loop() as SceneTree).root.get_node(^"GameState")
	var inventory: Node = (Engine.get_main_loop() as SceneTree).root.get_node(^"Inventory")
	for flag: String in part.get("flags", []):
		state.set_flag(StringName(flag))
	for memory: String in part.get("memories", []):
		state.remember(StringName(memory))
	for item: String in part.get("items", []):
		if not inventory.has(StringName(item)):
			inventory.add(StringName(item))

