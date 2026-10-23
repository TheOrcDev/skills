extends SceneTree
## Builds a CharacterSprites resource from a sprite manifest written by the art
## tools (`tools/adv-art pack`): one SpriteFrames animation per
## `<anim>_<dir>` at its own frame rate, trimmed frames restored to the full
## render frame through AtlasTexture margins, and the per-frame anchors. Import
## the sheets first (tools/godot.sh --headless --import).
##
##   tools/godot.sh --headless --script res://addons/adv_tools/import_sprites.gd -- \
##       --manifest=art-source/work/characters/hero/hero_sprites.json \
##       --out=res://content/characters/hero/hero_sprites.tres

const EYE_KEY := "eyes_visible"


func _initialize() -> void:
	var args := {}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--") and "=" in arg:
			args[arg.substr(2).get_slice("=", 0)] = arg.get_slice("=", 1)
	if not args.has("manifest") or not args.has("out"):
		printerr("import_sprites: needs --manifest=<file> and --out=<res path>")
		quit(1)
		return
	var manifest_path: String = args["manifest"]
	if not manifest_path.is_absolute_path():
		manifest_path = ProjectSettings.globalize_path("res://").path_join(manifest_path)
	var manifest = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if not manifest is Dictionary:
		printerr("import_sprites: cannot read %s" % manifest_path)
		quit(1)
		return
	var sprites := _build(manifest)
	if sprites == null:
		quit(1)
		return
	var err := ResourceSaver.save(sprites, args["out"])
	print("import_sprites: %s %s (%d animations)" % [args["out"], error_string(err), sprites.frames.get_animation_names().size()])
	quit(0 if err == OK else 1)


func _build(manifest: Dictionary) -> CharacterSprites:
	var sprites := CharacterSprites.new()
	sprites.frame_size = Vector2i(manifest["frame_size"][0], manifest["frame_size"][1])
	sprites.character_px = manifest["character_px"]
	sprites.shaded = manifest.get("channels", "alpha") == "grey_alpha"
	sprites.painted = manifest.get("style", "") == "painted"
	var expected := Image.FORMAT_LA8 if sprites.shaded else Image.FORMAT_L8
	var frames := SpriteFrames.new()
	frames.remove_animation(&"default")
	for key: String in manifest["animations"]:
		var entry: Dictionary = manifest["animations"][key]
		var anim := StringName(key)
		var sheet := load(entry["sheet"]) as Texture2D
		if sheet == null:
			printerr("import_sprites: %s: sheet %s is not imported" % [key, entry["sheet"]])
			return null
		var image := sheet.get_image()
		if image.get_format() != expected and not image.is_compressed():
			printerr("import_sprites: %s: sheet is format %s, expected %s or GPU-compressed" % [key, image.get_format(), expected])
			return null
		frames.add_animation(anim)
		frames.set_animation_speed(anim, entry["fps"])
		frames.set_animation_loop(anim, entry["loop"])
		for frame: Dictionary in entry["frames"]:
			var region: Array = frame["region"]
			var offset: Array = frame["offset"]
			var atlas := AtlasTexture.new()
			atlas.atlas = sheet
			atlas.region = Rect2(region[0], region[1], region[2], region[3])
			atlas.margin = Rect2(offset[0], offset[1], sprites.frame_size.x - region[2], sprites.frame_size.y - region[3])
			frames.add_frame(anim, atlas)
		var points := {}
		var eyes := PackedByteArray()
		for anchors: Dictionary in entry["anchors"]:
			for anchor_name: String in anchors:
				if anchor_name == EYE_KEY:
					continue
				var key_name := StringName(anchor_name)
				if not points.has(key_name):
					points[key_name] = PackedVector2Array()
				points[key_name].append(Vector2(anchors[anchor_name][0], anchors[anchor_name][1]))
			eyes.append(int(anchors[EYE_KEY][0]) | int(anchors[EYE_KEY][1]) << 1)
		sprites.anchors[anim] = points
		sprites.eyes[anim] = eyes
		var frame_events := {}
		for event: Dictionary in entry.get("events", []):
			var index := int(event["frame"])
			if not frame_events.has(index):
				frame_events[index] = []
			frame_events[index].append(StringName(event["name"]))
		if not frame_events.is_empty():
			sprites.events[anim] = frame_events
		if entry.has("ground_px_per_second"):
			sprites.ground_speed[anim] = float(entry["ground_px_per_second"])
	sprites.frames = frames
	return sprites
