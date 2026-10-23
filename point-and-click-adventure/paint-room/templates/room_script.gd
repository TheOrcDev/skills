extends Room
## The harbour steps (atlas H2). Hotspot verbs are methods named
## <verb>_<hotspot_id>; the lines are in content/dialogue/harbour/steps.dialogue.

const DIALOGUE := &"harbour/steps"


## Loaded, not yet shown: put the room in the state the flags leave it.
func _on_enter(_from: StringName) -> void:
	_show_state()


## After a save loads, instead of _on_enter and _on_shown.
func _on_restore() -> void:
	_show_state()


## Visible: a first-visit line.
func _on_shown() -> void:
	if not GameState.get_flag(&"harbour_steps_arrived"):
		GameState.set_flag(&"harbour_steps_arrived")
		await Say.line(DIALOGUE, &"arrival")


func look_keeper() -> void:
	await Say.line(DIALOGUE, &"keeper_look")


func talk_keeper() -> void:
	await Say.line(DIALOGUE, &"keeper_talk")


func look_tide_board() -> void:
	await Closeups.open(&"tide_ledger", hotspots.get_node(^"TideBoard") as Hotspot)


func look_bollard() -> void:
	await Say.line(DIALOGUE, &"bollard_look")


## The bollard's default verb is use: take the rope tied to it.
func use_bollard() -> void:
	if Inventory.has(&"rope") or GameState.get_flag(&"rope_taken"):
		await Say.line(DIALOGUE, &"bollard_empty")
		return
	await Rooms.player.play(&"pickup_low")
	Inventory.add(&"rope")
	GameState.set_flag(&"rope_taken")
	await Say.line(DIALOGUE, &"rope_take")


## An inventory item used on the bollard.
func item_bollard(item: ItemDef) -> void:
	if item.id != &"grapnel":
		await Say.fallback(&"item")
		return
	await Rooms.player.play(&"use")
	Inventory.remove(&"grapnel")
	GameState.set_flag(&"customs_unlocked")
	await Say.line(DIALOGUE, &"grapnel_thrown")


## Past only (era "then" in room.json).
func look_ship() -> void:
	await Say.line(DIALOGUE, &"ship_look")


## The customs door is an exit that needs "customs_unlocked"; until then a
## click on it runs this.
func locked_customs_door() -> void:
	await Say.line(DIALOGUE, &"customs_locked")


## Props and hotspots as the flags leave them. A prop from room.json "props"
## is the layer Layers/Now/<Name>.
func _show_state() -> void:
	var taken := bool(GameState.get_flag(&"crate_taken"))
	var crate := layers.get_node_or_null(^"Now/Crate") as CanvasItem
	if crate:
		crate.visible = not taken
	var spot := hotspots.get_node_or_null(^"Crate") as CanvasItem
	if spot:
		spot.visible = not taken
