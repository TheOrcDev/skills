class_name IdleFidgets
extends Node
## Now and then, while its parent Actor stands idle and the game is not busy
## with a cutscene or a line, plays one of its fidget one-shots. A click to
## walk interrupts a fidget at once.

@export var fidgets: Array[StringName] = [&"fidget_a", &"fidget_b", &"look_around"]
## Seconds of uninterrupted idling before a fidget, picked at random in this range.
@export var interval := Vector2(9.0, 18.0):
	set(value):
		interval = value
		_reset()

var _actor: Actor
var _wait := 0.0


func _ready() -> void:
	_actor = get_parent() as Actor
	_reset()


func _process(delta: float) -> void:
	if _actor == null or fidgets.is_empty():
		return
	if not _actor.is_idle() or _busy():
		_reset()
		return
	_wait -= delta
	if _wait <= 0.0:
		_reset()
		_actor.play(fidgets.pick_random())


## Input is locked during cutscenes, lines and visions (the Interaction autoload,
## looked up at run time so scaffolds can build actors without autoloads).
func _busy() -> bool:
	var interaction := get_node_or_null(^"/root/Interaction")
	return interaction != null and interaction.locked > 0


func _reset() -> void:
	_wait = randf_range(interval.x, interval.y)
