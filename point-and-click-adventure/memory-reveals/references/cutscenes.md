# Cutscenes

A cutscene is a `Cutscene` script whose `run(c)` awaits steps on a
`CutsceneSteps`. `Cutscenes.play(cutscene)` locks input, brings in the
letterbox, arms the Skip button and returns when `run` does.

| Step | Does |
|---|---|
| `await c.walk(actor, point)` | Walks there; skipped, teleports |
| `await c.face(actor, point)` | Turns to face a point |
| `await c.anim(actor, &"use")` | Plays a one-shot to its end; skipped, seeks to the end |
| `await c.say(&"<dialogue file>", &"<cue>")` | Says a cue; skipped, stops the line |
| `await c.wait(seconds)` | Holds; skipped, returns at once |
| `await c.shot(animation_player, &"<animation>")` | Plays a camera or effect animation; skipped, jumps to its end and passes over its method keys |
| `await c.fade(alpha, seconds)` | Fades to or from black; stays where it ends |
| `await c.era(room, &"then")` | Switches the room's era |

A cutscene the journal can replay:

```gdscript
class_name HarbourOpening
extends Cutscene


func _init() -> void:
	id = &"harbour_opening"


func run(c: CutsceneSteps) -> void:
	var hero := Rooms.player
	await c.fade(0.0, 1.0)
	await c.walk(hero, Vector2(900, 900))
	await c.say(&"harbour", &"opening_line")
	GameState.set_flag(&"harbour_arrived")  # world changes go here, never in keys
	await c.fade(1.0, 0.8)
```

Play it from a room with `await Cutscenes.play(HarbourOpening.new())`, or
before the first room by naming its script in `main.gd`'s `opening`.

## Visions

```gdscript
func use_statue() -> void:
	await Cutscenes.play(rewatch_statue_hand())


## The statue's vision, for touching it and for watching it again.
func rewatch_statue_hand() -> Vision:
	var statue := hotspots.get_node("Statue") as Hotspot
	return Vision.new(&"statue_hand", self, statue.focus_point(), func(c: CutsceneSteps) -> void:
		await c.wait(1.5)
		await c.say(&"harbour", &"statue_memory")
		await c.wait(1.0))
```

Without `during`, the past holds for 6 s.

## Playable memories

```gdscript
func use_altar() -> void:
	await Say.line(&"chapel", &"altar_touch")
	var altar := hotspots.get_node(^"Altar") as Hotspot
	Flashback.enter_memory(&"chapel_altar", self, altar.focus_point(), &"knows_word")


## In the past only: an era-tagged hotspot.
func look_carving() -> void:
	await Say.line(&"chapel", &"carving_past")
	GameState.set_flag(&"knows_word")
```

`done` is a flag name or a callable returning true. When it holds, the past
drains back and the memory is recorded.

## Reveals

```gdscript
const REVEAL := preload("res://content/cutscenes/harbour_reveal/harbour_reveal.tscn")


func _on_shown() -> void:
	if not &"harbour_reveal" in GameState.memories:
		await Cutscenes.play(rewatch_harbour_reveal())


func rewatch_harbour_reveal() -> RevealCutscene:
	return RevealCutscene.new(&"harbour_reveal", REVEAL)


## The same pull-back in the past's grade: a memory vista.
func rewatch_harbour_as_it_was() -> RevealCutscene:
	return RevealCutscene.new(&"harbour_as_it_was", REVEAL, &"then")
```
