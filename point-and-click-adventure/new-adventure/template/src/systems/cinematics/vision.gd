class_name Vision
extends Cutscene
## A cinematic flashback (technical-plan.md §6.1). The past
## blooms out of an anchor, holds while `during` plays, and drains back. It is
## a cutscene named by its memory id, so it can be skipped (back in the present
## at once, the hero where they stood) and rewatched. Finishing it, watched or
## skipped, records the memory in GameState.

## How long the past holds when nothing plays during it.
const HOLD := 6.0

var room: Room
var origin: Vector2
## Awaited as during.call(c) while the past shows; empty holds it for HOLD.
var during: Callable


func _init(memory: StringName, in_room: Room, anchor: Vector2, while_past := Callable()) -> void:
	id = memory
	room = in_room
	origin = anchor
	during = while_past


func run(c: CutsceneSteps) -> void:
	await Flashback.open_past(c, room, origin)
	Journal.capture_when_drawn(id)
	if during.is_valid():
		await during.call(c)
	else:
		await c.wait(HOLD)
	await Flashback.close_past(c, room, origin)
	GameState.remember(id)
