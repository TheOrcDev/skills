extends GutTest
## The inventory: carrying, holding, dropping and combining items, kept in
## GameState so it saves with everything else.


func _item(id: StringName, combinations := {}) -> ItemDef:
	var item := ItemDef.new()
	item.id = id
	item.display_name = String(id).capitalize()
	item.combinations = combinations
	Inventory.register(item)
	return item


func before_each() -> void:
	GameState.inventory.clear()
	Inventory.drop()
	_item(&"rope")
	_item(&"hook", {&"rope": &"grapple"})
	_item(&"grapple")


func test_add_remove_and_order() -> void:
	watch_signals(Inventory)
	Inventory.add(&"rope")
	Inventory.add(&"hook")
	Inventory.add(&"rope")
	assert_eq(GameState.inventory, [&"rope", &"hook"] as Array[StringName], "no duplicates, order kept")
	assert_eq(Inventory.items().map(func(i: ItemDef) -> StringName: return i.id), [&"rope", &"hook"])
	assert_signal_emit_count(Inventory, "changed", 2)
	Inventory.remove(&"rope")
	assert_false(Inventory.has(&"rope"))
	assert_true(Inventory.has(&"hook"))


func test_hold_and_drop() -> void:
	Inventory.add(&"rope")
	Inventory.hold(&"hook")
	assert_null(Inventory.held, "only carried items can be held")
	Inventory.hold(&"rope")
	assert_eq(Inventory.held.id, &"rope")
	Inventory.remove(&"rope")
	assert_null(Inventory.held, "losing the item drops it")


func test_combining_works_either_way_round() -> void:
	Inventory.add(&"rope")
	Inventory.add(&"hook")
	assert_eq(Inventory.combination(&"rope", &"hook"), &"grapple")
	assert_eq(Inventory.combination(&"hook", &"rope"), &"grapple")
	assert_eq(Inventory.combination(&"rope", &"grapple"), &"", "not everything combines")
	assert_eq(Inventory.combine(&"rope", &"hook"), &"grapple")
	assert_eq(GameState.inventory, [&"grapple"] as Array[StringName], "both parts become the result")
