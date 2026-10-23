extends SceneTree
## Builds an NPC scene from art-source/work/characters/<id>/npc_spec.json,
## written by `tools/adv-art npc`:
##
##   tools/godot.sh --headless --script res://addons/adv_tools/new_npc.gd -- <spec.json>
##
## The scene is an Actor whose body is a RigBody: the painting as a Polygon2D,
## meshed on a grid inside its alpha and skinned to a Skeleton2D. Each vertex
## follows the bones nearest it (inverse distance to each bone's segment), so
## the feet stay planted on the base bone and the head and arms bend. Import
## the painting first (tools/godot.sh --headless --import).

## Weight falloff: higher keeps each part on its own bone.
const FALLOFF := 4.0
## Distance (texture pixels) added before the falloff, which softens joints.
const SOFTEN := 6.0

var _root: Node


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		printerr("usage: new_npc.gd -- <npc_spec.json>")
		quit(2)
		return
	var spec: Variant = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not spec is Dictionary:
		printerr("Could not read spec %s" % args[0])
		quit(2)
		return
	quit(0 if create_npc(spec) == OK else 1)


func create_npc(spec: Dictionary) -> Error:
	var npc_id: String = spec["id"]
	var texture := load(spec["texture"]) as Texture2D
	if texture == null:
		printerr("Painting missing or not imported: %s" % spec["texture"])
		return ERR_FILE_NOT_FOUND
	var image := texture.get_image()
	if image.is_compressed():
		image.decompress()
	var feet := _point(spec["feet"])
	var scale_factor := float(spec["texture_scale"])

	var actor := Actor.new()
	_root = actor
	actor.name = npc_id.to_pascal_case()
	actor.speaker_name = spec["speaker"]
	actor.speaker_aliases = PackedStringArray(spec.get("aliases", []))
	var tint: Array = spec.get("subtitle_color", [0.9, 0.9, 0.9])
	actor.subtitle_color = Color(tint[0], tint[1], tint[2])
	actor.speech_offset = (_point(spec["speech"]) - feet) * scale_factor
	actor.talk_animations = [&"talk_a", &"talk_b"]

	var body := _add(actor, RigBody.new(), "Body") as RigBody
	body.motions = spec.get("motions", {})
	var outline := PackedVector2Array()
	for point: Array in spec["outline"]:
		outline.append((_point(point) - feet) * scale_factor)
	body.outline = outline
	var rig := _add(body, Node2D.new(), "Rig") as Node2D
	rig.position = -feet * scale_factor
	rig.scale = Vector2(scale_factor, scale_factor)
	var skeleton := _add(rig, Skeleton2D.new(), "Skeleton") as Skeleton2D

	# Bones, each aimed along its segment, placed in its parent's space.
	# The scene isn't in the tree, so each bone's rig-space transform is kept here.
	var bones := {}
	var segments := {}
	var rig_space := {}
	for bone_spec: Dictionary in spec["bones"]:
		var from := _point(bone_spec["from"])
		var to := _point(bone_spec["to"])
		var parent_name: String = bone_spec["parent"]
		var parent: Node = skeleton if parent_name.is_empty() else bones[parent_name]
		var bone := _add(parent, Bone2D.new(), bone_spec["name"]) as Bone2D
		var world := Transform2D((to - from).angle(), from)
		rig_space[bone_spec["name"]] = world
		bone.transform = world if parent_name.is_empty() else (rig_space[parent_name] as Transform2D).affine_inverse() * world
		bone.set_autocalculate_length_and_angle(false)
		bone.set_length(from.distance_to(to))
		bone.set_bone_angle(0.0)
		bone.rest = bone.transform
		bones[bone_spec["name"]] = bone
		segments[bone_spec["name"]] = [from, to]

	# The mesh: grid points inside the painting's alpha, two triangles a cell.
	var painting := _add(rig, Polygon2D.new(), "Painting") as Polygon2D
	painting.texture = texture
	var step := int(spec.get("grid", 28))
	var size := image.get_size()
	var columns := ceili(float(size.x) / step) + 1
	var rows := ceili(float(size.y) / step) + 1
	var index := {}
	var vertices := PackedVector2Array()
	var triangles := []
	for row in rows - 1:
		for column in columns - 1:
			var x0 := mini(column * step, size.x)
			var y0 := mini(row * step, size.y)
			var x1 := mini((column + 1) * step, size.x)
			var y1 := mini((row + 1) * step, size.y)
			if not _covers(image, x0, y0, x1, y1):
				continue
			var cell: Array[int] = []
			for corner: Vector2i in [Vector2i(x0, y0), Vector2i(x1, y0), Vector2i(x1, y1), Vector2i(x0, y1)]:
				if not index.has(corner):
					index[corner] = vertices.size()
					vertices.append(Vector2(corner))
				cell.append(index[corner])
			triangles.append(PackedInt32Array([cell[0], cell[1], cell[2]]))
			triangles.append(PackedInt32Array([cell[0], cell[2], cell[3]]))
	painting.polygon = vertices
	painting.uv = vertices
	painting.polygons = triangles
	painting.internal_vertex_count = vertices.size()
	painting.skeleton = painting.get_path_to(skeleton)

	# Skin: each vertex follows its nearest bones.
	var weights := {}
	for bone_name: String in segments:
		weights[bone_name] = PackedFloat32Array()
		weights[bone_name].resize(vertices.size())
	for i in vertices.size():
		var total := 0.0
		var raw := {}
		for bone_name: String in segments:
			var segment: Array = segments[bone_name]
			var closest := Geometry2D.get_closest_point_to_segment(vertices[i], segment[0], segment[1])
			var weight := 1.0 / pow(vertices[i].distance_to(closest) + SOFTEN, FALLOFF)
			raw[bone_name] = weight
			total += weight
		for bone_name: String in segments:
			weights[bone_name][i] = raw[bone_name] / total
	for bone_name: String in segments:
		painting.add_bone(skeleton.get_path_to(bones[bone_name]), weights[bone_name])

	var scene_path := "res://content/characters/%s/%s.tscn" % [npc_id, npc_id]
	var packed := PackedScene.new()
	var err := packed.pack(actor)
	if err == OK:
		err = ResourceSaver.save(packed, scene_path)
	print("new_npc %s: %s (%d vertices, %d triangles, %d bones)" % [scene_path, error_string(err), vertices.size(), triangles.size(), bones.size()])
	actor.free()
	return err


## Whether any of the cell's corners, edge midpoints or centre is painted.
func _covers(image: Image, x0: int, y0: int, x1: int, y1: int) -> bool:
	var w := image.get_width() - 1
	var h := image.get_height() - 1
	for x in [x0, (x0 + x1) / 2, x1]:
		for y in [y0, (y0 + y1) / 2, y1]:
			if image.get_pixel(mini(x, w), mini(y, h)).a > 0.03:
				return true
	return false


func _add(parent: Node, node: Node, node_name: String) -> Node:
	node.name = node_name
	parent.add_child(node)
	node.owner = _root
	return node


func _point(value: Array) -> Vector2:
	return Vector2(float(value[0]), float(value[1]))
