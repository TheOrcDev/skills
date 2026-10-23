extends GutTest
## The greybox puzzle chain, played to the end along the
## player's mouse paths by GreyboxPlaythrough: every verb, an item
## combination, a dialogue choice and a flashback clue.


func before_each() -> void:
	GameState.reset()


func after_each() -> void:
	await wait_until(func() -> bool: return Interaction.locked == 0, 20.0)
	Interaction.inventory.close()
	Inventory.drop()
	Rooms.clear()
	GameState.reset()


func test_the_chain_plays_to_the_end() -> void:
	var run := GreyboxPlaythrough.new(get_tree(), func(ok: bool, what: String) -> void: assert_true(ok, what))
	var done := [false]
	var play := func() -> void:
		await run.run()
		done[0] = true
	play.call()
	await wait_until(func() -> bool: return done[0], 180.0)
	assert_true(done[0], "the chain finished")
	assert_eq(Rooms.current.room_id, &"greybox_courtyard")
