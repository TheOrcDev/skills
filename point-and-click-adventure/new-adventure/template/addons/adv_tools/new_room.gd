extends SceneTree
## Creates a room's folder, script and scene with the standard structure in
## docs/technical-plan.md §5.1, saved through Godot so resource IDs stay valid.
##
##   tools/godot.sh --headless --script res://addons/adv_tools/new_room.gd -- <room_id> [spec.json] [--replace]
##
## The optional JSON spec describes the room; see
## art-source/work/rooms/greybox_chapel/room_spec.json and the paint-room
## skill's room-json reference for every field:
## layers per era, walk areas per era, scale zones, markers, hotspots,
## occluders (y-sorted cut-outs, optionally era-tagged) and effects (instances
## of effect classes such as FogLayer with property values). Import new art
## first (tools/godot.sh --headless --import). `--replace` overwrites an
## existing scene; the room script is never overwritten.

const ROOM_SIZE := Vector2(1920, 1080)

var _root: Node


func _initialize() -> void:
	var args := Array(OS.get_cmdline_user_args())
	var replace := args.has("--replace")
	args.erase("--replace")
	if args.is_empty():
		printerr("usage: new_room.gd -- <room_id> [spec.json] [--replace]")
		quit(2)
		return
	var spec := {}
	if args.size() > 1:
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(args[1]))
		if not parsed is Dictionary:
			printerr("Could not read spec %s" % args[1])
			quit(2)
			return
		spec = parsed
	quit(0 if create_room(args[0], spec, replace) == OK else 1)


func create_room(room_id: String, spec: Dictionary, replace := false) -> Error:
	var dir := "res://content/rooms/%s" % room_id
	var scene_path := dir.path_join("%s.tscn" % room_id)
	var script_path := dir.path_join("%s.gd" % room_id)
	if FileAccess.file_exists(scene_path) and not replace:
		printerr("%s already exists (pass --replace to regenerate it)" % scene_path)
		return ERR_ALREADY_EXISTS
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir))
	if not FileAccess.file_exists(script_path):
		var file := FileAccess.open(script_path, FileAccess.WRITE)
		file.store_string("extends Room\n## %s. Hotspot verbs are methods named <verb>_<hotspot_id>.\n" % spec.get("display_name", room_id))
		file.close()

	_root = Node2D.new()
	_root.name = room_id.to_pascal_case()
	_root.set_script(ResourceLoader.load(script_path, "", ResourceLoader.CACHE_MODE_IGNORE))
	_root.set(&"room_id", StringName(room_id))
	_root.set(&"display_name", spec.get("display_name", ""))

	var layers := _add(_root, Node2D.new(), "Layers")
	var era_layers := {"now": _add(layers, Node2D.new(), "Now"), "then": _add(layers, Node2D.new(), "Then")}
	var walk_areas := _add(_root, Node2D.new(), "WalkAreas")
	var era_walks := {"now": _add(walk_areas, NavigationRegion2D.new(), "Now"), "then": _add(walk_areas, NavigationRegion2D.new(), "Then")}
	era_walks["then"].enabled = false
	var zones := _add(_root, ScaleZones.new(), "ScaleZones") as ScaleZones
	var hotspots := _add(_root, Node2D.new(), "Hotspots")
	_add(_root, Node2D.new(), "Exits")
	var markers := _add(_root, Node2D.new(), "Markers")
	var actors := _add(_root, Node2D.new(), "Actors")
	actors.y_sort_enabled = true
	var foreground := _add(_root, Node2D.new(), "Foreground")
	_add(_root, Node2D.new(), "Cinematics")

	var err := OK
	var layer_spec: Dictionary = spec.get("layers", {})
	if spec.has("background"):
		layer_spec["now"] = [{"name": "Background", "texture": spec["background"]}] + Array(layer_spec.get("now", []))
	for era: String in layer_spec:
		for entry: Dictionary in layer_spec[era]:
			var sprite := _add(era_layers[era], Sprite2D.new(), entry.get("name", "Background")) as Sprite2D
			sprite.centered = false
			sprite.position = _point(entry.get("position", [0, 0]))
			sprite.texture = load(entry["texture"])
			if sprite.texture == null:
				printerr("Layer texture is missing or not imported: %s" % entry["texture"])
				err = ERR_FILE_NOT_FOUND

	var walk_spec: Dictionary = spec.get("walk", {})
	if spec.has("walk_now"):
		walk_spec["now"] = spec["walk_now"]
	for era: String in walk_spec:
		if err == OK:
			err = _bake_walk_area(era_walks[era], _points(walk_spec[era]))

	var zone_spec: Dictionary = spec.get("scale_zones", {})
	for key: String in ["far_y", "far_scale", "near_y", "near_scale"]:
		if zone_spec.has(key):
			zones.set(key, float(zone_spec[key]))

	var marker_spec: Dictionary = spec.get("markers", {"default": [960, 1000]})
	for marker_name: String in marker_spec:
		var marker := _add(markers, Marker2D.new(), marker_name) as Marker2D
		marker.position = _point(marker_spec[marker_name])

	for hotspot_spec: Dictionary in spec.get("hotspots", []):
		var node: Hotspot = Exit.new() if hotspot_spec.has("exit") else Hotspot.new()
		var hotspot := _add(hotspots, node, String(hotspot_spec["id"]).to_pascal_case()) as Hotspot
		if hotspot is Exit:
			var exit_spec: Dictionary = hotspot_spec["exit"]
			hotspot.target_room = StringName(exit_spec["room"])
			hotspot.target_entry = StringName(exit_spec.get("entry", "default"))
			hotspot.direction = StringName(exit_spec.get("direction", "right"))
			hotspot.requires_flag = StringName(exit_spec.get("requires_flag", ""))
		hotspot.id = StringName(hotspot_spec["id"])
		hotspot.display_name = hotspot_spec.get("name", hotspot_spec["id"])
		hotspot.default_verb = StringName(hotspot_spec.get("default_verb", "walk" if hotspot is Exit else "look"))
		hotspot.era = StringName(hotspot_spec.get("era", ""))
		hotspot.walk_offset = _point(hotspot_spec["walk_to"])
		hotspot.pick_priority = int(hotspot_spec.get("pick_priority", 0))
		var shape := _add(hotspot, CollisionPolygon2D.new(), "Shape") as CollisionPolygon2D
		shape.polygon = _points(hotspot_spec["polygon"])

	# Occluders: cut-outs drawn over actors standing behind their baseline (y-sort).
	for occluder_spec: Dictionary in spec.get("occluders", []):
		var rect: Array = occluder_spec["rect"]
		var baseline := float(occluder_spec.get("baseline", float(rect[1]) + float(rect[3])))
		var occluder := _add(actors, Sprite2D.new(), occluder_spec["name"]) as Sprite2D
		occluder.centered = false
		occluder.position = Vector2(float(rect[0]), baseline)
		occluder.offset = Vector2(0, float(rect[1]) - baseline)
		occluder.texture = load(occluder_spec["texture"])
		_tag_era(occluder, occluder_spec.get("era", ""))
		if occluder.texture == null:
			printerr("Occluder texture is missing or not imported: %s" % occluder_spec["texture"])
			err = ERR_FILE_NOT_FOUND

	# NPCs: character scenes placed among the actors, standing at
	# their feet position, optionally facing left and only in one era.
	for npc_spec: Dictionary in spec.get("npcs", []):
		var npc_scene := load(npc_spec["scene"]) as PackedScene
		if npc_scene == null:
			printerr("NPC scene is missing: %s" % npc_spec["scene"])
			err = ERR_FILE_NOT_FOUND
			continue
		var npc := npc_scene.instantiate()
		npc.name = npc_spec.get("name", npc.name)
		actors.add_child(npc)
		npc.owner = _root
		npc.position = _point(npc_spec["position"])
		if npc_spec.get("facing", "right") == "left":
			npc.set(&"facing", AnimNames.Dir.L)
		_tag_era(npc, npc_spec.get("era", ""))

	for effect_spec: Dictionary in spec.get("effects", []):
		var effect := _instantiate(effect_spec["type"])
		if effect == null:
			printerr("Unknown effect type %s" % effect_spec["type"])
			err = ERR_INVALID_PARAMETER
			continue
		var era: String = effect_spec.get("era", "")
		var parent: Node = foreground if effect_spec.get("layer", "background") == "foreground" or era == "" else era_layers[era]
		_add(parent, effect, effect_spec.get("name", effect_spec["type"]))
		if parent == foreground:
			_tag_era(effect, era)
		if effect is Control:
			var rect: Array = effect_spec.get("rect", [0, 0, ROOM_SIZE.x, ROOM_SIZE.y])
			(effect as Control).position = Vector2(float(rect[0]), float(rect[1]))
			(effect as Control).size = Vector2(float(rect[2]), float(rect[3]))
		var properties: Dictionary = effect_spec.get("properties", {})
		for property: String in properties:
			effect.set(property, _convert(properties[property], effect.get(property)))

	if err == OK:
		var packed := PackedScene.new()
		err = packed.pack(_root)
		if err == OK:
			err = ResourceSaver.save(packed, scene_path)
	print("new_room %s: %s" % [scene_path, error_string(err)])
	_root.free()
	return err


func _add(parent: Node, node: Node, node_name: String) -> Node:
	node.name = node_name
	parent.add_child(node)
	node.owner = _root
	return node


func _tag_era(node: Node, era: String) -> void:
	if era != "":
		node.add_to_group(StringName("era_%s" % era), true)


## A new instance of a global script class, for example "FogLayer".
func _instantiate(type_name: String) -> Node:
	for entry: Dictionary in ProjectSettings.get_global_class_list():
		if entry["class"] == type_name:
			return load(entry["path"]).new()
	return null


## Converts a JSON value to the type of the property it is assigned to.
func _convert(value: Variant, current: Variant) -> Variant:
	if value is String and String(value).begins_with("res://"):
		return load(value)
	match typeof(current):
		TYPE_COLOR:
			return Color(value) if value is String else Color(value[0], value[1], value[2], value[3] if value.size() > 3 else 1.0)
		TYPE_VECTOR2:
			return Vector2(value[0], value[1])
		TYPE_RECT2:
			return Rect2(value[0], value[1], value[2], value[3])
		TYPE_INT:
			return int(value)
		TYPE_FLOAT:
			return float(value)
	return value


## Bakes the outline into the region's navigation polygon. The outline is also
## kept on the polygon, so the editor can re-bake after edits.
func _bake_walk_area(region: NavigationRegion2D, outline: PackedVector2Array) -> Error:
	var polygon := NavigationPolygon.new()
	polygon.agent_radius = 0.0
	polygon.add_outline(outline)
	var source := NavigationMeshSourceGeometryData2D.new()
	source.add_traversable_outline(outline)
	NavigationServer2D.bake_from_source_geometry_data(polygon, source)
	if polygon.get_polygon_count() == 0:
		printerr("The walk area did not bake; check the outline %s" % outline)
		return ERR_INVALID_DATA
	region.navigation_polygon = polygon
	return OK


func _point(pair: Array) -> Vector2:
	return Vector2(float(pair[0]), float(pair[1]))


func _points(pairs: Array) -> PackedVector2Array:
	var points := PackedVector2Array()
	for pair: Array in pairs:
		points.append(_point(pair))
	return points
