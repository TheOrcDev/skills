class_name Hotspot
extends Area2D
## Something in a room the player can look at or use. Its outline is one or
## more CollisionPolygon2D children; hit tests are geometric, so no physics
## frame is needed. A verb is answered by `on_<verb>()` on a Hotspot subclass,
## or by `<verb>_<id>()` on the room script.

@export var id: StringName = &""
@export var display_name := ""
## "" for both eras, otherwise "now" or "then".
@export var era: StringName = &""
@export var default_verb: StringName = &"look"
## Where the hero stands to interact, relative to this node.
@export var walk_offset := Vector2.ZERO
## Higher wins where hotspots overlap.
@export var pick_priority := 0


func _ready() -> void:
	monitoring = false
	monitorable = false
	input_pickable = false


func is_active() -> bool:
	if not visible:
		return false
	if era == &"":
		return true
	var room := Room.of(self)
	return room == null or room.era == era


func contains_point(world_point: Vector2) -> bool:
	for child in get_children():
		var shape := child as CollisionPolygon2D
		if shape and not shape.disabled and Geometry2D.is_point_in_polygon(shape.to_local(world_point), shape.polygon):
			return true
	return false


func walk_point() -> Vector2:
	return global_position + walk_offset


## The centre of the outline in world coordinates; actors face this point.
func focus_point() -> Vector2:
	var total := Vector2.ZERO
	var count := 0
	for child in get_children():
		var shape := child as CollisionPolygon2D
		if shape:
			for point in shape.polygon:
				total += shape.to_global(point)
				count += 1
	return total / count if count > 0 else global_position


## Runs `verb` on this hotspot. Returns false when nothing handles it. A verb
## that changes rooms must return before the room goes (call Rooms.goto
## deferred, as Exit does), because leaving frees this hotspot and its room.
func handle(verb: StringName, args: Array = []) -> bool:
	var method := "on_%s" % verb
	var target: Object = self if has_method(method) else null
	if target == null:
		# The scene that owns this hotspot answers: a close-up, or the room.
		var scene: Node = Closeup.of(self) if Closeup.of(self) else Room.of(self)
		method = "%s_%s" % [verb, id]
		if scene and scene.has_method(method):
			target = scene
	if target == null:
		return false
	await Callable(target, method).callv(args)
	return true
