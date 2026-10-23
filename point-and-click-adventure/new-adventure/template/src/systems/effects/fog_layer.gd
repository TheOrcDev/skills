@tool
class_name FogLayer
extends ColorRect
## Drifting fog band over a room (src/shaders/fog.gdshader). With a depth
## texture, the fog thins where the scene is near, so the floor stays clear.

@export var fog_color := Color(0.82, 0.84, 0.86, 1.0)
@export_range(0.0, 1.0) var density := 0.35
@export var velocity := Vector2(0.008, 0.0)
@export var noise_scale := Vector2(1.6, 0.9)
@export_range(0.0, 1.0) var band_top := 0.45
@export_range(0.0, 1.0) var band_bottom := 0.95
@export_range(0.0, 0.5) var band_softness := 0.15
@export var depth_texture: Texture2D
@export_range(0.0, 1.0) var near_cutoff := 0.45
@export var noise_seed := 7


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	color = Color.WHITE
	var shader_material := ShaderMaterial.new()
	shader_material.shader = preload("res://src/shaders/fog.gdshader")
	shader_material.set_shader_parameter(&"noise_tex", Effects.noise_texture(noise_seed, 0.012))
	shader_material.set_shader_parameter(&"fog_color", fog_color)
	shader_material.set_shader_parameter(&"density", density)
	shader_material.set_shader_parameter(&"velocity", velocity)
	shader_material.set_shader_parameter(&"noise_scale", noise_scale)
	shader_material.set_shader_parameter(&"band_top", band_top)
	shader_material.set_shader_parameter(&"band_bottom", band_bottom)
	shader_material.set_shader_parameter(&"band_softness", band_softness)
	shader_material.set_shader_parameter(&"use_depth", depth_texture != null)
	if depth_texture:
		shader_material.set_shader_parameter(&"depth_tex", depth_texture)
	shader_material.set_shader_parameter(&"near_cutoff", near_cutoff)
	material = shader_material
