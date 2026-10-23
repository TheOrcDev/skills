extends GutTest
## Dialogue choices: the allowed responses are offered, the pick is spoken by
## The hero and the conversation follows it, and an exhausted option (guarded by
## a GameState flag) is gone the next time round.

const CONVERSATION := "res://test/fixtures/choices.dialogue"

var _lines: Array = []
var _offers: Array = []


func before_each() -> void:
	await Rooms.goto(&"greybox_chapel", &"default", &"none")
	GameState.set_flag(&"test_asked_who", false)
	_lines.clear()
	_offers.clear()


func after_each() -> void:
	Rooms.clear()


func test_choices_branch_and_exhausted_options_go() -> void:
	var listen := func(id: String, _speaker: String, _text: String) -> void:
		_lines.append(id)
		Say.skip.call_deferred()
	Say.line_started.connect(listen)
	var picker := func() -> void:
		while Say.speaking:
			if Say.choices.is_open:
				var labels := []
				for child in Say.choices.get_node("Band/Choices").get_children():
					if not child.is_queued_for_deletion():
						labels.append(child.text)
				_offers.append(labels)
				Say.choices.pick(0)
			await get_tree().process_frame
	var resource := load(CONVERSATION) as DialogueResource
	picker.call_deferred()
	await Say.run(resource, "start")
	Say.line_started.disconnect(listen)
	assert_eq(_offers, [["Who are you?", "Goodbye."], ["Goodbye."]], "the used question is gone the second time")
	assert_eq(_lines, ["TEST_KEEPER_ASK", "TEST_UNKNOWN_WHO", "TEST_KEEPER_WHO", "TEST_KEEPER_ASK", "TEST_UNKNOWN_BYE", "TEST_KEEPER_BYE"])
	assert_true(GameState.get_flag(&"test_asked_who"))
	assert_eq(Interaction.locked, 0, "input free after the conversation")
