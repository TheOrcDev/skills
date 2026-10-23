class_name VerbCoin
extends CanvasLayer
## The verb coin (game-design.md §9): a ring of smoke that opens where the
## player holds the mouse on a hotspot, with three glyphs: an eye (Look), a hand
## (Use, covering take, open and push) and a speech wisp (Talk; the hero has no
## mouth). Moving over a glyph lights it; releasing there picks that verb.

const VERBS: Array[StringName] = [&"look", &"use", &"talk"]
## Glyph offsets from the centre, in viewport pixels: left, top, right.
const OFFSETS := {&"look": Vector2(-78, 6), &"use": Vector2(0, -74), &"talk": Vector2(78, 6)}
const GLYPH_RADIUS := 34.0
const RING_RADIUS := 112.0

var is_open := false
## The glyph under the cursor, or &"".
var highlighted: StringName = &""

var _canvas: Control
var _center := Vector2.ZERO
var _opened_at := 0.0


func _ready() -> void:
	layer = 45
	_canvas = Control.new()
	_canvas.name = "Coin"
	_canvas.set_anchors_preset(Control.PRESET_FULL_RECT)
	_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas.draw.connect(_draw_coin)
	_canvas.visible = false
	add_child(_canvas)


func open(at: Vector2) -> void:
	_center = at
	is_open = true
	highlighted = &""
	_opened_at = Time.get_ticks_msec() / 1000.0
	_canvas.visible = true
	_canvas.queue_redraw()


## Closes the coin and returns the verb under the cursor, or &"" to cancel.
func close() -> StringName:
	var verb := highlighted
	is_open = false
	highlighted = &""
	_canvas.visible = false
	return verb


func point_at(screen: Vector2) -> void:
	if not is_open:
		return
	highlighted = verb_at(screen)
	_canvas.queue_redraw()


## The verb whose glyph contains `screen`, or &"".
func verb_at(screen: Vector2) -> StringName:
	for verb in VERBS:
		if screen.distance_to(glyph_position(verb)) <= GLYPH_RADIUS * 1.25:
			return verb
	return &""


func glyph_position(verb: StringName) -> Vector2:
	var offset: Vector2 = OFFSETS[verb]
	return _center + offset


func _process(_delta: float) -> void:
	if is_open:
		_canvas.queue_redraw()


func _draw_coin() -> void:
	var t := Time.get_ticks_msec() / 1000.0
	var grow := clampf((t - _opened_at) / 0.12, 0.0, 1.0)
	var c := _center
	# A drifting ring of smoke: overlapping soft discs.
	for i in 18:
		var a := TAU * i / 18.0 + t * 0.35
		var wobble := sin(t * 1.7 + i * 1.3) * 7.0
		var point := c + Vector2(cos(a), sin(a)) * (RING_RADIUS * grow + wobble)
		_canvas.draw_circle(point, 26.0 * grow, Color(0.02, 0.02, 0.03, 0.22))
	_canvas.draw_circle(c, RING_RADIUS * 0.92 * grow, Color(0.02, 0.02, 0.03, 0.55))
	if grow < 0.2:
		return  # the glyphs appear once the ring has opened (tiny polygons fail to triangulate)
	for verb in VERBS:
		var lit := verb == highlighted
		var offset: Vector2 = OFFSETS[verb]
		var p := c + offset * grow
		_canvas.draw_circle(p, GLYPH_RADIUS * grow, Color(0.85, 0.88, 0.96, 0.22 if lit else 0.08))
		var ink := Color(0.93, 0.95, 1.0, 1.0 if lit else 0.7)
		match verb:
			&"look":
				_draw_eye(p, grow, ink)
			&"use":
				_draw_hand(p, grow, ink)
			&"talk":
				_draw_wisp(p, grow, ink, t)


func _draw_eye(p: Vector2, s: float, ink: Color) -> void:
	var lid := PackedVector2Array()
	for i in 17:
		var x := -1.0 + i / 8.0
		lid.append(p + Vector2(x * 22.0, -sin((x + 1.0) * PI / 2.0) * 11.0) * s)
	for i in 17:
		var x := 1.0 - i / 8.0
		lid.append(p + Vector2(x * 22.0, sin((x + 1.0) * PI / 2.0) * 11.0) * s)
	_canvas.draw_polyline(lid, ink, 3.0 * s, true)
	_canvas.draw_circle(p, 6.5 * s, ink)


func _draw_hand(p: Vector2, s: float, ink: Color) -> void:
	_canvas.draw_rect(Rect2(p + Vector2(-11, -2) * s, Vector2(22, 18) * s), ink)
	for i in 4:
		var x := -10.5 + i * 7.0
		var height: float = [14.0, 18.0, 17.0, 13.0][i]
		_canvas.draw_rect(Rect2(p + Vector2(x, -2.0 - height) * s, Vector2(5.0, height) * s), ink)
	var thumb := PackedVector2Array([p + Vector2(-11, 4) * s, p + Vector2(-19, -6) * s, p + Vector2(-15, -9) * s, p + Vector2(-9, -1) * s])
	_canvas.draw_colored_polygon(thumb, ink)


func _draw_wisp(p: Vector2, s: float, ink: Color, t: float) -> void:
	var curl := PackedVector2Array()
	for i in 28:
		var a := i / 27.0 * TAU * 1.35
		var r := (4.0 + i * 0.75) * s
		curl.append(p + Vector2(cos(a + t * 0.8), sin(a + t * 0.8)) * r)
	_canvas.draw_polyline(curl, ink, 3.0 * s, true)
