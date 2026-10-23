extends SceneTree
## Creates inventory items from a JSON list, saved through Godot as
## content/items/<id>/<id>.tres. Each entry has an id, a name and an icon
## (res:// path), and optionally look_file, look_cue and combinations (other
## item id -> the item they make). Import the icons first.
##
##   tools/godot.sh --headless --script res://addons/adv_tools/new_item.gd -- <items.json>


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		printerr("usage: new_item.gd -- <items.json>")
		quit(2)
		return
	var list: Variant = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not list is Array:
		printerr("new_item: cannot read %s" % args[0])
		quit(1)
		return
	var failed := false
	for entry: Dictionary in list:
		var item := ItemDef.new()
		item.id = StringName(entry["id"])
		item.display_name = entry.get("name", entry["id"])
		if entry.has("icon"):
			item.icon = load(entry["icon"])
		item.look_file = StringName(entry.get("look_file", ""))
		item.look_cue = StringName(entry.get("look_cue", ""))
		var combinations := {}
		var made: Dictionary = entry.get("combinations", {})
		for other: String in made:
			combinations[StringName(other)] = StringName(made[other])
		item.combinations = combinations
		var path := "res://content/items/%s/%s.tres" % [item.id, item.id]
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
		var err := ResourceSaver.save(item, path)
		print("new_item %s: %s" % [path, error_string(err)])
		failed = failed or err != OK
	quit(1 if failed else 0)
