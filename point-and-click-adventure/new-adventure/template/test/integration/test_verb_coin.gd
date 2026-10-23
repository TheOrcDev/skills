extends GutTest
## The verb coin: a short click on a hotspot runs its default verb, holding
## opens the coin, releasing over a glyph runs that verb, and releasing
## elsewhere cancels.

var _lines: Array = []
var _listen: Callable


func before_each() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	_lines.clear()
	_listen = func(id: String, _speaker: String, _text: String) -> void:
		_lines.append(id)
		Say.skip.call_deferred()
	Say.line_started.connect(_listen)


func after_each() -> void:
	Say.line_started.disconnect(_listen)
	if Interaction.coin.is_open:
		Interaction.coin.close()
	Rooms.clear()


func _altar() -> Vector2:
	return (Rooms.current.hotspots.get_node("Altar") as Hotspot).focus_point()


func _until_quiet() -> void:
	await wait_until(func() -> bool: return Interaction.locked == 0 and not Say.speaking and not Rooms.player.is_walking, 15.0)


func test_a_short_click_runs_the_default_verb() -> void:
	Interaction.press_at(_altar(), Vector2(1400, 600))
	await wait_process_frames(2)
	Interaction.release_at(_altar(), Vector2(1400, 600))
	assert_false(Interaction.coin.is_open, "no coin for a short click")
	await wait_until(func() -> bool: return not _lines.is_empty(), 15.0)
	assert_eq(_lines, ["GB_ALTAR_LOOK_1"], "looked at the altar")
	await _until_quiet()


func test_holding_opens_the_coin_and_a_glyph_picks_the_verb() -> void:
	Interaction.press_at(_altar(), Vector2(1400, 600))
	await wait_seconds(Interaction.COIN_HOLD_SECONDS + 0.1)
	assert_true(Interaction.coin.is_open, "held long enough: the coin opens")
	var talk := Interaction.coin.glyph_position(&"talk")
	Interaction.coin.point_at(talk)
	assert_eq(Interaction.coin.highlighted, &"talk", "the speech glyph lights up")
	Interaction.release_at(_altar(), talk)
	assert_false(Interaction.coin.is_open)
	await wait_until(func() -> bool: return not _lines.is_empty(), 15.0)
	assert_true(String(_lines[0]).begins_with("CORE_FALLBACK_TALK"), "talking to the altar has no answer, got %s" % _lines)
	await _until_quiet()


func test_releasing_off_the_glyphs_cancels() -> void:
	Interaction.press_at(_altar(), Vector2(1400, 600))
	await wait_seconds(Interaction.COIN_HOLD_SECONDS + 0.1)
	assert_true(Interaction.coin.is_open)
	Interaction.release_at(_altar(), Vector2(1400, 900))
	await wait_seconds(0.5)
	assert_false(Interaction.coin.is_open)
	assert_true(_lines.is_empty(), "nothing happens")
	assert_false(Rooms.player.is_walking, "and the hero stays put")
