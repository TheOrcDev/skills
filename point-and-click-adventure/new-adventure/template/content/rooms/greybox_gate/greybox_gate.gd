extends Room
## The greybox gatehouse, where the sample puzzle chain starts. The gate is
## rusted shut, and the gatekeeper lets it open only for the word of the house.
## The rag on the hook is the first thing to take, and the notice opens a
## close-up.

## Loaded with the room, under the fade, so the push-in starts without a hitch.
const NOTICE := preload("res://content/closeups/greybox_notice/greybox_notice.tscn")


func _on_enter(_from: StringName) -> void:
	_show_state()


func look_gatekeeper() -> void:
	await Say.line(&"greybox", &"gatekeeper_look")


func talk_gatekeeper() -> void:
	await Say.line(&"greybox", &"gatekeeper_talk")


func look_notice() -> void:
	await Closeups.open_node(NOTICE.instantiate() as Closeup, hotspots.get_node("Notice") as Hotspot)


func look_gate() -> void:
	await Say.line(&"greybox", &"gate_look")


func use_gate() -> void:
	if not GameState.get_flag(&"greybox_gate_oiled"):
		await Say.line(&"greybox", &"gate_rusted")
	elif not GameState.get_flag(&"greybox_word_spoken"):
		await Say.line(&"greybox", &"gate_unheard")
	else:
		GameState.set_flag(&"greybox_gate_open")
		_show_state()
		await Say.line(&"greybox", &"gate_opens")


func item_gate(item: ItemDef) -> void:
	if item.id != &"oiled_rag":
		await Say.fallback(&"item")
		return
	await Rooms.player.play(&"use")
	Inventory.remove(&"oiled_rag")
	GameState.set_flag(&"greybox_gate_oiled")
	await Say.line(&"greybox", &"gate_oiled")


func look_rag() -> void:
	await Say.line(&"greybox", &"rag_look_hook")


func use_rag() -> void:
	await Rooms.player.play(&"pickup_high")
	Inventory.add(&"rag")
	GameState.set_flag(&"greybox_rag_taken")
	_show_state()
	await Say.line(&"greybox", &"rag_take")


## The room as the flags leave it: the rag gone once taken, the gate open.
func _show_state() -> void:
	var taken := bool(GameState.get_flag(&"greybox_rag_taken"))
	layers.get_node(^"Now/Rag").visible = not taken
	hotspots.get_node(^"Rag").visible = not taken
	var open := bool(GameState.get_flag(&"greybox_gate_open"))
	layers.get_node(^"Now/Gate").visible = not open
	hotspots.get_node(^"Gate").visible = not open
	hotspots.get_node(^"Beyond").visible = open
