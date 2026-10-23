class_name Reveal
extends Node2D
## A pull-back reveal (docs/technical-plan.md §6.3). The Ring0, Ring1, … Sprite2D
## children are nested rings, each a 2× detail repaint of the centre of the ring
## outside it, placed in ring 0's pixels. As `progress` runs from 0 to 1 the
## camera pulls back from the start view to the end view:
## - the zoom moves in log space, so the perceived speed stays constant;
## - the view scales about one fixed point, so the pull-back never seems to pan;
## - the view stays inside ring 0;
## - each inner ring fades out once the ring outside it shows enough detail.

const FEATHER := preload("res://src/shaders/ring_feather.gdshader")

## Zoom (screen pixels per ring-0 pixel) and view centre (ring-0 pixels) at the
## start and the end.
@export var start_zoom := 2.4
@export var start_center := Vector2(906, 670)
@export var end_zoom := 0.75
@export var end_center := Vector2(1536, 536)
## Ring 0's size in its own pixels.
@export var world_size := Vector2(3072, 1072)
## The part of the screen the view must fill: the 2.39:1 band inside the letterbox.
@export var view_size := Vector2(1920, 803)
## Edge fade of the inner rings, as a fraction of the shorter side.
@export var feather := 0.08
## An inner ring fades out while its on-screen scale drops from `fade_from` to `fade_to`.
@export var fade_from := 0.6
@export var fade_to := 0.4
@export_range(0.0, 1.0) var progress := 0.0:
	set(value):
		progress = value
		if camera and not hold:
			_apply(progress)

var camera: Camera2D
## While set, `progress` no longer moves the view: a cutscene cuts between views
## with show_at() instead (Reduce camera motion).
var hold := false

var _rings: Array[Sprite2D] = []


func _ready() -> void:
	for child in get_children():
		if child is Sprite2D and child.name.begins_with("Ring"):
			_rings.append(child)
	_rings.sort_custom(func(a: Sprite2D, b: Sprite2D) -> bool: return a.scale.x > b.scale.x)
	for i in range(1, _rings.size()):
		var material := ShaderMaterial.new()
		material.shader = FEATHER
		material.set_shader_parameter(&"feather", feather)
		_rings[i].material = material
	camera = Camera2D.new()
	camera.name = "Camera"
	add_child(camera)
	_apply(progress)


func zoom_at(p: float) -> float:
	return exp(lerpf(log(start_zoom), log(end_zoom), p))


## The world point that keeps its place on screen for the whole pull-back.
func pivot() -> Vector2:
	return (start_center * start_zoom - end_center * end_zoom) / (start_zoom - end_zoom)


func center_at(p: float) -> Vector2:
	var zoom := zoom_at(p)
	var center := pivot() - (pivot() - start_center) * start_zoom / zoom
	var half := view_size / (2.0 * zoom)
	return Vector2(
		clampf(center.x, half.x, world_size.x - half.x),
		clampf(center.y, half.y, world_size.y - half.y))


func ring_count() -> int:
	return _rings.size()


func ring(index: int) -> Sprite2D:
	return _rings[index]


## Shows the view at `p`, whatever `progress` says.
func show_at(p: float) -> void:
	_apply(p)


func _apply(p: float) -> void:
	var zoom := zoom_at(p)
	camera.zoom = Vector2(zoom, zoom)
	camera.position = center_at(p)
	for i in range(1, _rings.size()):
		var on_screen := zoom * _rings[i].scale.x
		_rings[i].modulate.a = clampf(inverse_lerp(fade_to, fade_from, on_screen), 0.0, 1.0)
		_rings[i].visible = _rings[i].modulate.a > 0.0
