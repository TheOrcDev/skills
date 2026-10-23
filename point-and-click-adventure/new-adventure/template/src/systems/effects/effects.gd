@tool
class_name Effects
extends RefCounted
## Shared, cached textures for the living-painting effects.

static var _noise_cache := {}
static var _dot: Texture2D
static var _eye: Texture2D
static var _painted_eye: Texture2D


## A seamless noise texture, generated once per (seed, frequency).
static func noise_texture(noise_seed: int, frequency: float) -> NoiseTexture2D:
	var key := "%d:%f" % [noise_seed, frequency]
	if _noise_cache.has(key):
		return _noise_cache[key]
	var noise := FastNoiseLite.new()
	noise.seed = noise_seed
	noise.frequency = frequency
	noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	noise.fractal_octaves = 4
	var texture := NoiseTexture2D.new()
	texture.width = 512
	texture.height = 512
	texture.seamless = true
	texture.noise = noise
	_noise_cache[key] = texture
	return texture


## A small soft round dot for particles.
static func soft_dot() -> Texture2D:
	if _dot:
		return _dot
	var gradient := Gradient.new()
	gradient.set_color(0, Color(1, 1, 1, 1))
	gradient.set_color(1, Color(1, 1, 1, 0))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(0.5, 0.0)
	texture.width = 16
	texture.height = 16
	_dot = texture
	return _dot


## A painted eye: a round white dot with a short soft glow, as Sol
## paints them.
static func painted_eye() -> Texture2D:
	if _painted_eye:
		return _painted_eye
	var gradient := Gradient.new()
	gradient.set_color(0, Color(1.0, 1.0, 1.0, 1.0))
	gradient.set_color(1, Color(0.85, 0.9, 1.0, 0.0))
	gradient.add_point(0.32, Color(1.0, 1.0, 1.0, 1.0))
	gradient.add_point(0.45, Color(0.92, 0.95, 1.0, 0.5))
	gradient.add_point(0.7, Color(0.85, 0.9, 1.0, 0.12))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(0.5, 0.0)
	texture.width = 64
	texture.height = 64
	_painted_eye = texture
	return _painted_eye


## An eye's glow: a white core with a soft cool halo, for additive sprites.
static func eye_glow() -> Texture2D:
	if _eye:
		return _eye
	var gradient := Gradient.new()
	gradient.set_color(0, Color(1.0, 1.0, 1.0, 1.0))
	gradient.set_color(1, Color(0.8, 0.85, 1.0, 0.0))
	gradient.add_point(0.16, Color(1.0, 1.0, 1.0, 1.0))
	gradient.add_point(0.3, Color(0.9, 0.93, 1.0, 0.45))
	gradient.add_point(0.55, Color(0.8, 0.85, 1.0, 0.12))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(0.5, 0.0)
	texture.width = 64
	texture.height = 64
	_eye = texture
	return _eye
