class_name ActorBody
extends Node2D
## How an Actor looks. Subclasses play `<anim>_<dir>` animations; the Actor
## chooses names and mirroring through AnimNames.

signal animation_finished(anim: StringName)


func has_animation(_anim: StringName) -> bool:
	return false


## Whether `world` falls on the body as drawn now.
func contains_point(_world: Vector2) -> bool:
	return false


func play_animation(_anim: StringName, _flip: bool) -> void:
	pass


## Pixels per second the feet cover at scale 1 in the current animation, when
## it was rendered with one (walks). 0 leaves the Actor's walk_speed in charge.
func ground_speed() -> float:
	return 0.0


## Frames per second of the current animation, or 0 if it is not frame based.
func frame_rate() -> float:
	return 0.0


## True once each time a new frame shows. An Actor that steps with frames moves
## only then, so the planted foot stays put on the floor.
func consume_step() -> bool:
	return true


## Called by the Actor while one of its lines is being spoken.
func set_speaking(_on: bool) -> void:
	pass
