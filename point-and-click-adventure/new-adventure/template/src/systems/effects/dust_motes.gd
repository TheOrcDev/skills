@tool
class_name DustMotes
extends CPUParticles2D
## Slowly drifting motes: ash in the present, golden dust in the past
## (docs/art-pipeline.md §5E). CPU particles work in every build.

## Where motes appear, in room pixels.
@export var area := Rect2(200, 100, 1500, 800)
@export var mote_color := Color(0.9, 0.9, 0.92, 0.5)
@export var mote_count := 60
@export var drift := Vector2(6, -10)
@export var mote_size := 3.0


func _ready() -> void:
	amount = mote_count
	lifetime = 9.0
	preprocess = 9.0
	randomness = 0.6
	emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	position = area.get_center()
	emission_rect_extents = area.size / 2.0
	direction = drift.normalized() if drift != Vector2.ZERO else Vector2.UP
	spread = 60.0
	gravity = Vector2.ZERO
	initial_velocity_min = drift.length() * 0.4
	initial_velocity_max = drift.length() * 1.2
	scale_amount_min = mote_size * 0.5
	scale_amount_max = mote_size * 1.4
	color = mote_color
	texture = Effects.soft_dot()
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0))
	fade.set_color(1, Color(1, 1, 1, 0))
	fade.add_point(0.25, Color(1, 1, 1, 1))
	fade.add_point(0.75, Color(1, 1, 1, 1))
	color_ramp = fade
	emitting = true
