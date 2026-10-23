extends Room
## The greybox chapel. The oil flask sits on the shelf, and the altar's
## carving has burned away. Touching the altar steps into the chapel's past (a
## playable memory), where the carving is still whole and gives the word of
## the house. Touching the window plays a vision of the chapel as it was.


func _on_enter(_from: StringName) -> void:
	_show_state()


func look_altar() -> void:
	await Say.line(&"greybox", &"altar_look")


func use_altar() -> void:
	await Say.line(&"greybox", &"altar_touch")
	var altar := hotspots.get_node(^"Altar") as Hotspot
	Flashback.enter_memory(&"greybox_altar", self, altar.focus_point(), &"greybox_knows_word")


## In the past only.
func look_carving() -> void:
	await Say.line(&"greybox", &"altar_past")
	GameState.set_flag(&"greybox_knows_word")
	GameState.learn(&"greybox_mercy")


func look_flask() -> void:
	await Say.line(&"greybox", &"flask_look_shelf")


func use_flask() -> void:
	await Rooms.player.play(&"pickup_high")
	Inventory.add(&"oil")
	GameState.set_flag(&"greybox_oil_taken")
	_show_state()
	await Say.line(&"greybox", &"flask_take")


func look_window() -> void:
	await Say.line(&"greybox", &"window_look")


func use_window() -> void:
	await Cutscenes.play(rewatch_greybox_window())


## The window's vision, for touching it and for watching it again.
func rewatch_greybox_window() -> Vision:
	var window := hotspots.get_node(^"Window") as Hotspot
	return Vision.new(&"greybox_window", self, window.focus_point(), func(c: CutsceneSteps) -> void:
		await c.wait(1.0)
		await c.say(&"greybox", &"window_memory")
		await c.wait(0.8))


func _show_state() -> void:
	var taken := bool(GameState.get_flag(&"greybox_oil_taken"))
	layers.get_node(^"Now/Flask").visible = not taken
	hotspots.get_node(^"Flask").visible = not taken
