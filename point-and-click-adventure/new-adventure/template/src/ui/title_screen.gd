class_name TitleScreen
extends CanvasLayer
## The start screen: a room's painting, softly blurred, with fog drifting
## across it, the title, and the game's menu down the left.
## At launch it offers Continue (the newest save), New Game, Load Game, Settings
## and Quit. Opened from the top bar's Main menu, the game waits paused behind
## it, and it offers Resume and Save Game as well. The browser demo cannot
## quit, so it has no Quit.

## A menu entry was chosen; `Menus` runs it.
signal chosen(id: StringName)

## The painting behind the menu: point it at the game's most telling room.
const ART := "res://content/rooms/greybox_gate/art/bg_now.png"
## How far the painting is shrunk before it is scaled back up: the blur.
const BLUR_DIVISOR := 8
const DRIFT_SECONDS := 28.0
const FADE_SECONDS := 0.8

## True when a game is paused behind the screen.
var in_game := false
## What Save Game keeps as its thumbnail: the game as it was before the screen
## opened.
var picture: Image

var _black: ColorRect
var _entries: VBoxContainer
var _leaving := false


func _ready() -> void:
	layer = 68
	process_mode = Node.PROCESS_MODE_ALWAYS
	var backdrop := ColorRect.new()
	backdrop.color = Color.BLACK
	backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	backdrop.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(backdrop)
	var painting := TextureRect.new()
	painting.name = "Painting"
	painting.texture = blurred(load(ART) as Texture2D)
	painting.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	painting.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	painting.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	painting.set_anchors_preset(Control.PRESET_FULL_RECT)
	painting.mouse_filter = Control.MOUSE_FILTER_IGNORE
	painting.modulate = Color(0.78, 0.79, 0.84)
	add_child(painting)
	_drift(painting)
	for fog: Array in [[21, 0.32, Vector2(0.006, 0.0), Vector2(1.4, 0.8), 0.35, 0.8], [23, 0.26, Vector2(-0.009, 0.0), Vector2(2.2, 1.1), 0.55, 1.0]]:
		var layer_fog := FogLayer.new()
		layer_fog.noise_seed = fog[0]
		layer_fog.density = fog[1]
		layer_fog.velocity = fog[2]
		layer_fog.noise_scale = fog[3]
		layer_fog.band_top = fog[4]
		layer_fog.band_bottom = fog[5]
		layer_fog.fog_color = Color(0.82, 0.84, 0.88)
		layer_fog.set_anchors_preset(Control.PRESET_FULL_RECT)
		add_child(layer_fog)
	var shade := TextureRect.new()
	shade.name = "Shade"
	shade.texture = _shade()
	shade.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	shade.stretch_mode = TextureRect.STRETCH_SCALE
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	var column := VBoxContainer.new()
	column.name = "Column"
	column.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	column.offset_left = 150.0
	column.offset_right = 900.0
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	column.add_theme_constant_override(&"separation", 70)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(column)
	column.add_child(_title())
	_entries = VBoxContainer.new()
	_entries.name = "Entries"
	_entries.add_theme_constant_override(&"separation", 14)
	_entries.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(_entries)
	for entry: Array in entries():
		var button := MenuScreen.text_button(entry[1], 46, _choose.bind(entry[0]))
		button.name = String(entry[0]).to_pascal_case()
		_entries.add_child(button)
	_black = ColorRect.new()
	_black.name = "Black"
	_black.color = Color.BLACK
	_black.set_anchors_preset(Control.PRESET_FULL_RECT)
	_black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_black)
	create_tween().tween_property(_black, ^"color:a", 0.0, FADE_SECONDS * (0.5 if in_game else 2.0))
	Cursors.show_for(null)


## The entries this screen offers, as [id, text], in order.
func entries() -> Array:
	var list := []
	if in_game:
		list.append([&"resume", "Resume"])
		list.append([&"save", "Save Game"])
	elif Saves.latest_slot() >= 0:
		list.append([&"continue", "Continue"])
	list.append([&"new_game", "New Game"])
	list.append([&"load", "Load Game"])
	list.append([&"settings", "Settings"])
	if not OS.has_feature("web"):
		list.append([&"quit", "Quit"])
	return list


## The button for entry `id`, or null, for tests.
func button(id: StringName) -> Control:
	return _entries.get_node_or_null(NodePath(String(id).to_pascal_case())) as Control


## Fades to black, runs `then` while the screen is still black, and goes.
func leave(then: Callable = Callable()) -> void:
	if _leaving:
		return
	_leaving = true
	_black.mouse_filter = Control.MOUSE_FILTER_STOP
	var tween := create_tween()
	tween.tween_property(_black, ^"color:a", 1.0, FADE_SECONDS)
	await tween.finished
	if then.is_valid():
		await then.call()
	# Whatever comes next puts up its own black in its first frame.
	await get_tree().process_frame
	queue_free()


## Closes at once, back to the paused game.
func close() -> void:
	_leaving = true
	queue_free()


func _choose(id: StringName) -> void:
	if not _leaving:
		chosen.emit(id)


## `texture` shrunk by BLUR_DIVISOR and scaled back to half size: a soft blur
## made once, which costs nothing per frame (the browser demo included).
static func blurred(texture: Texture2D) -> Texture2D:
	var image := texture.get_image()
	if image == null:
		return texture
	image = image.duplicate() as Image
	if image.is_compressed():
		image.decompress()
	var full := image.get_size()
	image.resize(maxi(1, full.x / BLUR_DIVISOR), maxi(1, full.y / BLUR_DIVISOR), Image.INTERPOLATE_LANCZOS)
	image.resize(full.x / 2, full.y / 2, Image.INTERPOLATE_CUBIC)
	return ImageTexture.create_from_image(image)


## A slow drift and zoom across the painting, back and forth, for as long as the
## screen is up.
func _drift(painting: Control) -> void:
	painting.pivot_offset = Vector2(960, 540)
	painting.scale = Vector2.ONE * 1.06
	var tween := painting.create_tween().set_loops().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(painting, ^"position", Vector2(-40, -12), DRIFT_SECONDS)
	tween.parallel().tween_property(painting, ^"scale", Vector2.ONE * 1.1, DRIFT_SECONDS)
	tween.tween_property(painting, ^"position", Vector2.ZERO, DRIFT_SECONDS)
	tween.parallel().tween_property(painting, ^"scale", Vector2.ONE * 1.06, DRIFT_SECONDS)


## The game's name (application/config/name) in spaced capitals.
func _title() -> Label:
	var label := Label.new()
	label.name = "Title"
	label.text = String(ProjectSettings.get_setting("application/config/name", "")).to_upper()
	var font := FontVariation.new()
	font.spacing_glyph = 40
	label.add_theme_font_override(&"font", font)
	label.add_theme_font_size_override(&"font_size", 150)
	label.add_theme_color_override(&"font_color", Color(0.9, 0.91, 0.94))
	label.add_theme_color_override(&"font_shadow_color", Color(0, 0, 0, 0.7))
	label.add_theme_constant_override(&"shadow_offset_y", 5)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label


## Darkness from the left edge, so the menu reads over the painting, and a
## little at the top and bottom.
static func _shade() -> GradientTexture2D:
	var gradient := Gradient.new()
	gradient.set_color(0, Color(0.0, 0.0, 0.02, 0.82))
	gradient.set_color(1, Color(0.0, 0.0, 0.02, 0.0))
	gradient.add_point(0.42, Color(0.0, 0.0, 0.02, 0.45))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.width = 256
	texture.height = 4
	texture.fill_from = Vector2(0, 0)
	texture.fill_to = Vector2(0.8, 0)
	return texture
