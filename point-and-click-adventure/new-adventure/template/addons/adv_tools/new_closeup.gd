extends SceneTree
## Creates a close-up view's scene from a JSON spec, saved through
## Godot so resource IDs stay valid: a Closeup root with the close-up's script
## (content/closeups/<id>/<id>.gd, if it exists), a Background sprite and one
## Hotspot per spec entry. Import the art first.
##
##   tools/godot.sh --headless --script res://addons/adv_tools/new_closeup.gd -- <id> <spec.json> [--replace]


func _initialize() -> void:
	var args := Array(OS.get_cmdline_user_args())
	var replace := args.has("--replace")
	args.erase("--replace")
	if args.size() < 2:
		printerr("usage: new_closeup.gd -- <id> <spec.json> [--replace]")
		quit(2)
		return
	var id: String = args[0]
	var path := "res://content/closeups/%s/%s.tscn" % [id, id]
	if FileAccess.file_exists(path) and not replace:
		print("new_closeup: keeping %s (use --replace)" % path)
		quit(0)
		return
	var spec: Variant = JSON.parse_string(FileAccess.get_file_as_string(args[1]))
	if not spec is Dictionary:
		printerr("new_closeup: cannot read %s" % args[1])
		quit(1)
		return
	var root := Closeup.new()
	root.name = id.to_pascal_case()
	root.closeup_id = StringName(id)
	var script_path := "res://content/closeups/%s/%s.gd" % [id, id]
	if ResourceLoader.exists(script_path):
		root.set_script(load(script_path))
		root.closeup_id = StringName(id)
	var background := Sprite2D.new()
	background.name = "Background"
	background.centered = false
	background.texture = load(spec["background"])
	_add(root, background, root)
	var hotspots := Node2D.new()
	hotspots.name = "Hotspots"
	_add(root, hotspots, root)
	for entry: Dictionary in spec["hotspots"]:
		var hotspot := Hotspot.new()
		hotspot.name = String(entry["id"]).to_pascal_case()
		hotspot.id = StringName(entry["id"])
		hotspot.display_name = entry.get("name", entry["id"])
		hotspot.default_verb = StringName(entry.get("default_verb", "look"))
		_add(hotspots, hotspot, root)
		var shape := CollisionPolygon2D.new()
		shape.name = "Shape"
		var points := PackedVector2Array()
		for point: Array in entry["polygon"]:
			points.append(Vector2(point[0], point[1]))
		shape.polygon = points
		_add(hotspot, shape, root)
	var packed := PackedScene.new()
	var err := packed.pack(root)
	if err == OK:
		err = ResourceSaver.save(packed, path)
	root.free()
	print("new_closeup: %s %s" % [path, error_string(err)])
	quit(0 if err == OK else 1)


func _add(parent: Node, child: Node, owner_node: Node) -> void:
	parent.add_child(child)
	child.owner = owner_node
