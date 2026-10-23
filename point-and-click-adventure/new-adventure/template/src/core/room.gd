class_name Room
extends Node2D
## One playable location. Room scenes follow the structure in
## docs/technical-plan.md §5.1 and are created with
## addons/adv_tools/new_room.gd. A room script extends this class and answers
## hotspot verbs with methods named `<verb>_<hotspot_id>`, for example
## `func look_statue() -> void`.

@export var room_id: StringName = &""
@export var display_name := ""

## "now" or "then". Nodes named Now and Then under Layers and WalkAreas follow it.
var era: StringName = &"now"

@onready var layers: Node2D = $Layers
@onready var walk_areas: Node2D = $WalkAreas
@onready var scale_zones: ScaleZones = $ScaleZones
@onready var hotspots: Node2D = $Hotspots
@onready var markers: Node2D = $Markers
@onready var actors: Node2D = $Actors


## The Room a node belongs to, or null.
static func of(node: Node) -> Room:
	var current := node
	while current:
		if current is Room:
			return current
		current = current.get_parent()
	return null


func _ready() -> void:
	set_era(era)


func scale_at(y: float) -> float:
	return scale_zones.scale_at(y) if scale_zones else 1.0


func marker_position(marker_name: StringName) -> Vector2:
	var marker := markers.get_node_or_null(NodePath(marker_name)) as Node2D
	return marker.global_position if marker else global_position


## Shows one era's layers and activates its walk area. Other era-specific
## nodes (occluders, foreground effects) are in the groups `era_now` and
## `era_then`. Hotspots tagged with an era check it themselves (Hotspot.is_active).
func set_era(new_era: StringName) -> void:
	era = new_era
	var era_node := String(new_era).capitalize()
	for group: Node in [layers, walk_areas]:
		for child in group.get_children():
			if child.name != &"Now" and child.name != &"Then":
				continue
			var on: bool = child.name == era_node
			if child is NavigationRegion2D:
				child.enabled = on
			elif child is CanvasItem:
				child.visible = on
	for node in era_nodes():
		node.visible = node.is_in_group(StringName("era_%s" % new_era))


## Era-tagged nodes outside Layers and WalkAreas.
func era_nodes() -> Array[CanvasItem]:
	var result: Array[CanvasItem] = []
	for node in find_children("*", "CanvasItem", true, false):
		if node.is_in_group(&"era_now") or node.is_in_group(&"era_then"):
			result.append(node)
	return result


## Called after the room is loaded and the player placed, before it is shown.
func _on_enter(_from: StringName) -> void:
	pass


## Called once the room is visible and input is unlocked.
func _on_shown() -> void:
	pass


## Called just before the room is freed.
func _on_exit() -> void:
	pass


## Called instead of _on_enter/_on_shown after a save is loaded.
func _on_restore() -> void:
	pass
