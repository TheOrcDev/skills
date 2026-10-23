extends Node
## What the hero carries (docs/technical-plan.md §5.5). The list of item ids lives
## in GameState, so it saves with everything else; the item held on the cursor
## does not.

signal changed
signal held_changed(item: ItemDef)

const ITEM_PATH := "res://content/items/%s/%s.tres"

## The item on the cursor, waiting to be used on something, or null.
var held: ItemDef

var _defs := {}


func _ready() -> void:
	# A load or a new game replaces the list: nothing stays on the cursor.
	GameState.replaced.connect(func() -> void:
		drop()
		changed.emit())


func add(id: StringName) -> void:
	if not has(id):
		GameState.inventory.append(id)
		changed.emit()


func remove(id: StringName) -> void:
	if has(id):
		GameState.inventory.erase(id)
		if held and held.id == id:
			drop()
		changed.emit()


func has(id: StringName) -> bool:
	return id in GameState.inventory


## The carried items, in the order they were found.
func items() -> Array[ItemDef]:
	var result: Array[ItemDef] = []
	for id in GameState.inventory:
		var item := def(id)
		if item:
			result.append(item)
	return result


func hold(id: StringName) -> void:
	if has(id):
		held = def(id)
		held_changed.emit(held)


func drop() -> void:
	if held:
		held = null
		held_changed.emit(null)


## What `a` and `b` combine into, or &"" if they don't. Works either way round.
func combination(a: StringName, b: StringName) -> StringName:
	var first := def(a)
	var second := def(b)
	if first and first.combinations.has(b):
		return first.combinations[b]
	if second and second.combinations.has(a):
		return second.combinations[a]
	return &""


## Combines two carried items: both go and the result is added. Returns the
## result's id, or &"" when they don't combine.
func combine(a: StringName, b: StringName) -> StringName:
	var result := combination(a, b)
	if result == &"" or not has(a) or not has(b):
		return &""
	remove(a)
	remove(b)
	add(result)
	return result


## The ItemDef for `id`, loaded from content/items once, or registered by code.
func def(id: StringName) -> ItemDef:
	if not _defs.has(id):
		var path := ITEM_PATH % [id, id]
		_defs[id] = load(path) as ItemDef if ResourceLoader.exists(path) else null
	return _defs[id]


## Makes `item` known without a resource file (tests and generated items).
func register(item: ItemDef) -> void:
	_defs[item.id] = item
