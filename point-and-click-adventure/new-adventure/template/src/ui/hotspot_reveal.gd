class_name HotspotReveal
extends CanvasLayer
## Reveal hotspots (game-design.md §12): for a few seconds,
## marks everything the player can use right now, in the room or the open
## close-up. Things get the hotspot ring and ways out the exit arrow, each with
## its name.

const SECONDS := 2.6
const FADE := 0.3

var _markers: Control
var _fading: Tween


func _ready() -> void:
	layer = 55
	_markers = Control.new()
	_markers.name = "Markers"
	_markers.set_anchors_preset(Control.PRESET_FULL_RECT)
	_markers.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_markers)


## Marks the active hotspots and returns how many there are.
func reveal() -> int:
	clear()
	var spots: Array[Hotspot] = []
	var scene: Node = Closeups.current if Closeups.current else Rooms.current
	if scene == null:
		return 0
	for node in scene.get_node(^"Hotspots").get_children():
		var hotspot := node as Hotspot
		if hotspot and hotspot.is_active():
			spots.append(hotspot)
	# A close-up's hotspots are in screen pixels; a room's go through its camera.
	var to_screen := Transform2D.IDENTITY if Closeups.current else get_viewport().get_canvas_transform()
	for hotspot in spots:
		_markers.add_child(_marker(hotspot, to_screen * hotspot.focus_point()))
	_markers.modulate.a = 0.0
	_fading = create_tween()
	_fading.tween_property(_markers, ^"modulate:a", 1.0, FADE)
	_fading.tween_interval(SECONDS - 2.0 * FADE)
	_fading.tween_property(_markers, ^"modulate:a", 0.0, FADE)
	_fading.tween_callback(clear)
	return spots.size()


## The markers on screen now.
func markers() -> Array[Node]:
	return _markers.get_children()


func clear() -> void:
	if _fading:
		_fading.kill()
		_fading = null
	for marker in _markers.get_children():
		_markers.remove_child(marker)
		marker.queue_free()


func _marker(hotspot: Hotspot, at: Vector2) -> Control:
	var exit := hotspot as Exit
	var kind := StringName("exit_%s" % exit.direction) if exit else &"hotspot"
	var marker := Control.new()
	marker.name = String(hotspot.id).to_pascal_case()
	marker.position = at
	marker.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var icon := TextureRect.new()
	icon.texture = Cursors.texture_for(kind)
	icon.position = -icon.texture.get_size()
	icon.scale = Vector2(2, 2)
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	marker.add_child(icon)
	var label := MenuScreen.text_line(hotspot.display_name, 28, Color(0.95, 0.95, 0.95))
	label.custom_minimum_size.x = 300
	# Centred under the mark, but kept on screen.
	var view := get_viewport().get_visible_rect().size
	label.position = Vector2(clampf(-150.0, 12.0 - at.x, view.x - 312.0 - at.x), 34)
	marker.add_child(label)
	return marker
