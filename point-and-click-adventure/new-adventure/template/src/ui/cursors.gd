@tool
class_name Cursors
extends RefCounted
## The mouse cursor's shapes (game-design.md §9), drawn once in code: a small
## pale dot for walking, a ring over hotspots, and an arrow over exits pointing
## the way out.

const SIZE := 48

static var _cache := {}


## Shows the cursor for hovering `hotspot` (null: walking).
static func show_for(hotspot: Hotspot) -> void:
	var kind := &"walk"
	if hotspot is Exit:
		kind = StringName("exit_%s" % (hotspot as Exit).direction)
	elif hotspot:
		kind = &"hotspot"
	show(kind)


## Shows the cursor `kind`: "walk", "hotspot" or "exit_<direction>".
static func show(kind: StringName) -> void:
	Input.set_custom_mouse_cursor(texture_for(kind), Input.CURSOR_ARROW, Vector2(SIZE, SIZE) / 2.0)


static func texture_for(kind: StringName) -> Texture2D:
	if not _cache.has(kind):
		_cache[kind] = ImageTexture.create_from_image(_draw(kind))
	return _cache[kind]


static func _draw(kind: StringName) -> Image:
	var image := Image.create(SIZE, SIZE, false, Image.FORMAT_RGBA8)
	var center := Vector2(SIZE, SIZE) / 2.0
	for y in SIZE:
		for x in SIZE:
			var p := Vector2(x + 0.5, y + 0.5) - center
			var a := 0.0
			match kind:
				&"walk":
					a = 1.0 - smoothstep(2.5, 4.5, p.length())
				&"hotspot":
					var ring := absf(p.length() - 13.0)
					a = maxf(1.0 - smoothstep(1.2, 2.6, ring), 1.0 - smoothstep(2.0, 3.5, p.length()))
				_:
					a = _arrow(p, String(kind).trim_prefix("exit_"))
			image.set_pixel(x, y, Color(0.92, 0.94, 1.0, a))
	return image


## An arrowhead pointing `direction`, as coverage at point `p` (from the centre).
static func _arrow(p: Vector2, direction: String) -> float:
	var q := p
	match direction:
		"left":
			q = Vector2(-p.x, p.y)
		"up":
			q = Vector2(-p.y, p.x)
		"down":
			q = Vector2(p.y, -p.x)
	# Pointing right: a chevron of two strokes meeting at x = 12.
	var stroke := minf(absf(q.y - (q.x - 12.0)), absf(q.y + (q.x - 12.0))) / 1.414
	var inside := q.x > -2.0 and q.x < 12.5
	var shaft := absf(q.y) < 2.0 and q.x > -14.0 and q.x < 10.0
	return maxf(1.0 - smoothstep(1.5, 3.0, stroke) if inside else 0.0, 1.0 if shaft else 0.0)
