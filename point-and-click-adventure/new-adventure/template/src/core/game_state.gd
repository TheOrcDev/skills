extends Node
## The whole game's state in one versioned dictionary (docs/technical-plan.md
## §5.7). `Saves` writes it to disk, with where the hero stands, and reads it
## back. Dialogue variables are flags too: a flag holds a bool, a number or text.

## Emitted when the whole state is replaced: a save loaded or a new game.
signal replaced

## 1: flags and the inventory. 2: the full state.
## 3: facts and the cutscenes seen, for the journal.
const SAVE_VERSION := 3

var flags := {}
## Carried item ids, in the order found (see the Inventory autoload).
var inventory: Array[StringName] = []
## What rooms keep between visits, by room id (see room_state()).
var room_states := {}
## The memories the hero has seen, in the order they saw them.
var memories: Array[StringName] = []
## Hint progress by puzzle id.
var hints := {}
## What the hero has learned about themselves, in the order learned, for the
## journal's "Who am I?" page.
var facts: Array[StringName] = []
## The cutscenes played so far, watched or skipped, for rewatching.
var cutscenes_seen: Array[StringName] = []
var play_seconds := 0.0


func _process(delta: float) -> void:
	play_seconds += delta


func set_flag(flag: StringName, value: Variant = true) -> void:
	flags[flag] = value


func get_flag(flag: StringName, default: Variant = false) -> Variant:
	return flags.get(flag, default)


## The state `room_id` keeps between visits; rooms add to it as they like.
func room_state(room_id: StringName) -> Dictionary:
	if not room_states.has(room_id):
		room_states[room_id] = {}
	return room_states[room_id]


## Notes that the hero has seen the memory `id`.
func remember(id: StringName) -> void:
	if not id in memories:
		memories.append(id)


## Notes that the hero has learned the fact `id` about themselves.
func learn(id: StringName) -> void:
	if not id in facts:
		facts.append(id)


## Notes that the cutscene `id` has played.
func saw_cutscene(id: StringName) -> void:
	if id != &"" and not id in cutscenes_seen:
		cutscenes_seen.append(id)


## Back to the state of a new game.
func reset() -> void:
	from_dict({})


## The state as plain values that JSON keeps: text keys, lists, numbers.
func to_dict() -> Dictionary:
	var rooms := {}
	for room_id: StringName in room_states:
		rooms[String(room_id)] = _text_keys(room_states[room_id])
	return {
		"save_version": SAVE_VERSION,
		"flags": _text_keys(flags),
		"inventory": Array(inventory).map(func(id: StringName) -> String: return String(id)),
		"room_states": rooms,
		"memories": Array(memories).map(func(id: StringName) -> String: return String(id)),
		"hints": _text_keys(hints),
		"facts": Array(facts).map(func(id: StringName) -> String: return String(id)),
		"cutscenes_seen": Array(cutscenes_seen).map(func(id: StringName) -> String: return String(id)),
		"play_seconds": play_seconds,
	}


## Takes the state from a dictionary like to_dict() makes, at SAVE_VERSION
## (`Saves` migrates older ones first). Missing parts start empty.
func from_dict(data: Dictionary) -> void:
	flags = _name_keys(data.get("flags", {}))
	inventory.assign(Array(data.get("inventory", [])).map(func(id: Variant) -> StringName: return StringName(str(id))))
	room_states = {}
	var rooms: Dictionary = data.get("room_states", {})
	for room_id: Variant in rooms:
		room_states[StringName(str(room_id))] = _name_keys(rooms[room_id])
	memories.assign(Array(data.get("memories", [])).map(func(id: Variant) -> StringName: return StringName(str(id))))
	hints = _name_keys(data.get("hints", {}))
	facts.assign(Array(data.get("facts", [])).map(func(id: Variant) -> StringName: return StringName(str(id))))
	cutscenes_seen.assign(Array(data.get("cutscenes_seen", [])).map(func(id: Variant) -> StringName: return StringName(str(id))))
	play_seconds = float(data.get("play_seconds", 0.0))
	replaced.emit()


static func _text_keys(values: Dictionary) -> Dictionary:
	var result := {}
	for key: Variant in values:
		result[str(key)] = values[key]
	return result


static func _name_keys(values: Dictionary) -> Dictionary:
	var result := {}
	for key: Variant in values:
		result[StringName(str(key))] = values[key]
	return result
