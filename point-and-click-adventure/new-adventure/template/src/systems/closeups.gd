extends Node
## Opens and closes close-up views. Opening pushes in: the room's
## camera glides towards the hotspot and zooms until a screen-shaped frame round
## it fills the screen, while the close-up, pinned over that frame with soft
## edges, fades in, so the detail grows out of the thing clicked. Closing is the
## same move reversed. With Reduce camera motion the close-up simply crossfades
## in, full screen. While a close-up is open, Interaction sends clicks to its
## hotspots; a right-click, Esc or the back glyph closes it.

signal opened(closeup: Closeup)
signal closed(closeup_id: StringName)

const PATH := "res://content/closeups/%s/%s.tscn"
const SECONDS := 0.9
## The close-up's soft edge while it moves, as a share of its shorter side.
const FEATHER := 0.22
const FEATHER_SHADER := preload("res://src/shaders/ring_feather.gdshader")

var current: Closeup
var busy := false

var _layer: CanvasLayer
var _back: Label
## The frame round the hotspot, in room pixels: the screen's shape, inside the
## room. Rooms are one screen, so these are screen pixels before the push.
var _frame := Rect2()
var _camera: Camera2D
var _feather: ShaderMaterial
## No camera move for this close-up: it crossfades in place.
var _still := false


func _ready() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 30
	add_child(_layer)
	_back = Label.new()
	_back.name = "Back"
	_back.text = "‹"
	_back.add_theme_font_size_override(&"font_size", 72)
	_back.add_theme_color_override(&"font_outline_color", Color.BLACK)
	_back.add_theme_constant_override(&"outline_size", 12)
	_back.position = Vector2(34, 10)
	_back.mouse_filter = Control.MOUSE_FILTER_STOP
	_back.visible = false
	_back.gui_input.connect(func(event: InputEvent) -> void:
		var click := event as InputEventMouseButton
		if click and click.pressed and click.button_index == MOUSE_BUTTON_LEFT:
			get_viewport().set_input_as_handled()
			close())
	_layer.add_child(_back)


## Opens the close-up `id` from `from` (the hotspot clicked, for the push-in).
func open(id: StringName, from: Hotspot = null) -> void:
	var scene := load(PATH % [id, id]) as PackedScene
	if scene == null:
		push_error("Close-up not found: %s" % id)
		return
	await open_node(scene.instantiate() as Closeup, from)


## Opens an already built close-up (tests and generated views).
func open_node(closeup: Closeup, from: Hotspot = null) -> void:
	if current or busy:
		closeup.free()
		return
	busy = true
	Interaction.locked += 1
	var view := get_viewport().get_visible_rect().size
	_frame = _frame_round(from) if from else Rect2(view * 0.375, view * 0.25)
	_layer.add_child(closeup)
	current = closeup
	_still = Settings.reduce_camera_motion
	_camera = null if _still else _make_camera()
	_soften(closeup, not _still)
	_step(0.0)
	await _push(0.0, 1.0)
	_soften(closeup, false)
	closeup.position = Vector2.ZERO
	closeup.scale = Vector2.ONE
	_back.visible = true
	Interaction.locked -= 1
	busy = false
	closeup._on_shown()
	opened.emit(closeup)


func close() -> void:
	if current == null or busy:
		return
	busy = true
	Interaction.locked += 1
	_back.visible = false
	var closeup := current
	_soften(closeup, not _still)
	await _push(1.0, 0.0)
	if is_instance_valid(_camera):
		_camera.queue_free()
	_camera = null
	var id := closeup.closeup_id
	current = null
	closeup.queue_free()
	Interaction.locked -= 1
	busy = false
	closed.emit(id)


func _unhandled_input(event: InputEvent) -> void:
	if current == null or busy:
		return
	if event.is_action_pressed(&"ui_cancel"):
		get_viewport().set_input_as_handled()
		close()


func _push(from_t: float, to_t: float) -> void:
	var tween := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_method(_step, from_t, to_t, SECONDS)
	await tween.finished


## One moment of the push, from t = 0 (the room as it was, the close-up an
## invisible frame over the hotspot) to t = 1 (the frame fills the screen and
## the close-up covers it). The zoom grows evenly to the eye, the frame's centre
## glides straight to the screen's centre, and the close-up stays on the frame.
func _step(t: float) -> void:
	if _still:
		current.position = Vector2.ZERO
		current.scale = Vector2.ONE
		current.modulate.a = t
		return
	var view := get_viewport().get_visible_rect().size
	var zoom := pow(view.x / _frame.size.x, t)
	var offset := _frame.get_center() - view / 2.0
	if is_instance_valid(_camera):
		_camera.zoom = Vector2.ONE * zoom
		# Puts the frame's centre at view / 2 + offset * (1 - t) on screen.
		_camera.position = view / 2.0 + offset * (1.0 - (1.0 - t) / zoom)
		_camera.force_update_scroll()
	var size := _frame.size * zoom
	current.position = view / 2.0 + offset * (1.0 - t) - size / 2.0
	current.scale = size / view
	current.modulate.a = smoothstep(0.1, 0.7, t)
	if _feather:
		_feather.set_shader_parameter(&"feather", maxf(FEATHER * (1.0 - smoothstep(0.55, 1.0, t)), 0.001))


## A camera for the push, at rest where it sees the room as it is without one.
func _make_camera() -> Camera2D:
	var room := Rooms.current
	if room == null:
		return null
	var camera := Camera2D.new()
	camera.position = get_viewport().get_visible_rect().size / 2.0
	room.add_child(camera)
	camera.make_current()
	return camera


## Soft edges on the close-up's background while it moves; none once it is open.
func _soften(closeup: Closeup, on: bool) -> void:
	var background := closeup.get_node_or_null(^"Background") as CanvasItem
	if background == null:
		return
	if on and background.material == null:
		_feather = ShaderMaterial.new()
		_feather.shader = FEATHER_SHADER
		background.material = _feather
	elif not on and _feather and background.material == _feather:
		background.material = null
		_feather = null


## The frame the push starts on: a rectangle with the screen's shape round the
## hotspot's outline, kept inside the room so the camera never shows past it.
func _frame_round(hotspot: Hotspot) -> Rect2:
	var rect := Rect2(hotspot.focus_point(), Vector2.ZERO)
	for child in hotspot.get_children():
		var shape := child as CollisionPolygon2D
		if shape:
			for point in shape.polygon:
				rect = rect.expand(shape.to_global(point))
	var view := get_viewport().get_visible_rect().size
	var aspect := view.x / view.y
	var width := clampf(maxf(rect.size.x, rect.size.y * aspect), 160.0, view.x)
	var size := Vector2(width, width / aspect)
	return Rect2((rect.get_center() - size / 2.0).clamp(Vector2.ZERO, view - size), size)
