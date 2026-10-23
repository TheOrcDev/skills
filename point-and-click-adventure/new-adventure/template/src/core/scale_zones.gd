@tool
class_name ScaleZones
extends Node2D
## Depth scaling for a room: actors are drawn at `far_scale` on the far line and
## at `near_scale` on the near line, linearly in between and clamped outside.
## The editor draws both lines so they can be tuned against the background.

@export var far_y := 900.0:
	set(value):
		far_y = value
		queue_redraw()
@export var far_scale := 0.6:
	set(value):
		far_scale = value
		queue_redraw()
@export var near_y := 1080.0:
	set(value):
		near_y = value
		queue_redraw()
@export var near_scale := 1.0:
	set(value):
		near_scale = value
		queue_redraw()


func scale_at(y: float) -> float:
	if is_equal_approx(near_y, far_y):
		return near_scale
	var t := clampf((y - far_y) / (near_y - far_y), 0.0, 1.0)
	return lerpf(far_scale, near_scale, t)


func _draw() -> void:
	if not Engine.is_editor_hint():
		return
	var width := float(ProjectSettings.get_setting("display/window/size/viewport_width", 1920))
	draw_line(Vector2(0, far_y), Vector2(width, far_y), Color(0.3, 0.8, 1.0, 0.9), 3.0)
	draw_line(Vector2(0, near_y), Vector2(width, near_y), Color(1.0, 0.6, 0.2, 0.9), 3.0)
