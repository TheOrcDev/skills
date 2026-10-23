@tool
class_name LightShafts
extends ColorRect
## A fan of softly flickering light shafts from a window
## (src/shaders/light_shafts.gdshader), drawn additively.

## The light source, in this rect's pixels.
@export var origin := Vector2(1465, 255)
## Direction of the fan in degrees: 180 is straight down, 225 down-left.
@export var aim := 205.0
@export var spread := 34.0
@export var beams := 6.0
@export_range(0.0, 1.0) var intensity := 0.16
@export var reach := 0.9
@export var shaft_color := Color(1, 1, 1, 1)
@export_range(0.0, 1.0) var flicker := 0.35
@export var noise_seed := 11


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	color = Color.WHITE
	var shader_material := ShaderMaterial.new()
	shader_material.shader = preload("res://src/shaders/light_shafts.gdshader")
	shader_material.set_shader_parameter(&"noise_tex", Effects.noise_texture(noise_seed, 0.05))
	shader_material.set_shader_parameter(&"origin", origin / size if size.x > 0.0 and size.y > 0.0 else Vector2(0.5, 0.2))
	shader_material.set_shader_parameter(&"aim", aim)
	shader_material.set_shader_parameter(&"spread", spread)
	shader_material.set_shader_parameter(&"beams", beams)
	shader_material.set_shader_parameter(&"intensity", intensity)
	shader_material.set_shader_parameter(&"reach", reach)
	shader_material.set_shader_parameter(&"color", shaft_color)
	shader_material.set_shader_parameter(&"flicker", flicker)
	shader_material.set_shader_parameter(&"aspect", size.x / size.y if size.y > 0.0 else 1.7778)
	material = shader_material
