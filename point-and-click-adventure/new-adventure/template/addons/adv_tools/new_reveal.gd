extends SceneTree
## Builds a pull-back reveal cutscene (docs/technical-plan.md §6.3) from a
## reveal spec written by its art build script (for example
## `tools/adv-art reveal`). The scene has the zoom-stack rings
## in a Reveal, the hero standing in the vista, a title card, and an
## AnimationPlayer whose "reveal" animation holds, pulls back with ease in and
## out, then shows and hides the title. The scene's script is <name>.gd beside
## the output if there is one, or RevealStage. An existing scene is kept unless
## --replace is given.
##
##   tools/godot.sh --headless --script res://addons/adv_tools/new_reveal.gd -- \
##       --spec=art-source/work/reveal/greybox_vista/reveal_spec.json \
##       --out=res://content/cutscenes/greybox_vista/greybox_vista.tscn \
##       --title="BEYOND THE GATE" --place="The greybox" [--replace]

const UNKNOWN_SPRITES := "res://content/characters/hero/hero_sprites.tres"
## Timeline in seconds: hold on the opening frame, pull back, title in, title out, end.
const HOLD := 1.5
const PULL_END := 11.0
const TITLE_IN := 9.5
const TITLE_OUT := 12.6
const LENGTH := 13.8


func _initialize() -> void:
	var args := {}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--"):
			var key := arg.substr(2).get_slice("=", 0)
			args[key] = arg.substr(arg.find("=") + 1) if "=" in arg else "true"
	if not args.has("spec") or not args.has("out"):
		printerr("new_reveal: needs --spec=<file> and --out=<res path>")
		quit(1)
		return
	var out: String = args["out"]
	if FileAccess.file_exists(out) and not args.has("replace"):
		print("new_reveal: keeping %s (use --replace)" % out)
		quit(0)
		return
	var spec_path: String = args["spec"]
	if not spec_path.is_absolute_path():
		spec_path = ProjectSettings.globalize_path("res://").path_join(spec_path)
	var spec = JSON.parse_string(FileAccess.get_file_as_string(spec_path))
	if not spec is Dictionary:
		printerr("new_reveal: cannot read %s" % spec_path)
		quit(1)
		return
	var root := _build(spec, out, args.get("title", ""), args.get("place", ""))
	var packed := PackedScene.new()
	var err := packed.pack(root)
	if err == OK:
		err = ResourceSaver.save(packed, out)
	root.free()
	print("new_reveal: %s %s" % [out, error_string(err)])
	quit(0 if err == OK else 1)


func _build(spec: Dictionary, out: String, title_text: String, place_text: String) -> Node2D:
	var root := Node2D.new()
	root.name = out.get_file().get_basename().to_pascal_case()
	var script_path := out.get_basename() + ".gd"
	# Loaded by path when the scaffold runs: autoload names resolve only then.
	root.set_script(load(script_path if ResourceLoader.exists(script_path) else "res://src/systems/cinematics/reveal_stage.gd"))

	var reveal := Reveal.new()
	reveal.name = "Reveal"
	reveal.start_zoom = spec["start"]["zoom"]
	reveal.start_center = _vec(spec["start"]["center"])
	reveal.end_zoom = spec["end"]["zoom"]
	reveal.end_center = _vec(spec["end"]["center"])
	reveal.world_size = _vec(spec["world_size"])
	reveal.feather = spec["feather"]
	_add(root, reveal, root)
	for i in spec["rings"].size():
		var entry: Dictionary = spec["rings"][i]
		var ring := Sprite2D.new()
		ring.name = "Ring%d" % i
		ring.texture = load(entry["texture"])
		ring.centered = false
		ring.position = _vec(entry["position"])
		ring.scale = Vector2.ONE * float(entry["scale"])
		if i > 0:
			ring.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		_add(reveal, ring, root)

	var sprites := load(UNKNOWN_SPRITES) as CharacterSprites
	var hero := HeroBody.new()
	hero.name = "Hero"
	hero.sprites = sprites
	hero.position = _vec(spec["hero"]["feet"])
	hero.scale = Vector2.ONE * float(spec["hero"]["height"]) / sprites.character_px
	_add(reveal, hero, root)

	var title_layer := CanvasLayer.new()
	title_layer.name = "Title"
	title_layer.layer = 55
	_add(root, title_layer, root)
	var card := VBoxContainer.new()
	card.name = "Card"
	card.set_anchors_preset(Control.PRESET_CENTER)
	card.grow_horizontal = Control.GROW_DIRECTION_BOTH
	card.grow_vertical = Control.GROW_DIRECTION_BOTH
	card.alignment = BoxContainer.ALIGNMENT_CENTER
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_add(title_layer, card, root)
	# 132 px spaced capitals fit a short name like PAST; longer area titles
	# shrink to stay inside the 1920 px screen, spacing with them.
	var title_size := mini(132, floori((1680.0 / maxi(title_text.length(), 1) - 20.0) / 0.78))
	_add(card, _label("Name", title_text, title_size, roundi(34.0 * title_size / 132.0)), root)
	_add(card, _label("Place", place_text, 40, 10), root)

	var player := AnimationPlayer.new()
	player.name = "AnimationPlayer"
	var library := AnimationLibrary.new()
	library.add_animation(&"reveal", _reveal_animation())
	player.add_animation_library(&"", library)
	_add(root, player, root)
	return root


func _reveal_animation() -> Animation:
	var animation := Animation.new()
	animation.length = LENGTH
	var pull := animation.add_track(Animation.TYPE_VALUE)
	animation.track_set_path(pull, ^"Reveal:progress")
	animation.track_insert_key(pull, 0.0, 0.0)
	var start_key := animation.track_insert_key(pull, HOLD, 0.0)
	animation.track_set_key_transition(pull, start_key, -2.0)
	animation.track_insert_key(pull, PULL_END, 1.0)
	var calls := animation.add_track(Animation.TYPE_METHOD)
	animation.track_set_path(calls, ^".")
	animation.track_insert_key(calls, TITLE_IN, {"method": &"show_title", "args": []})
	animation.track_insert_key(calls, TITLE_OUT, {"method": &"hide_title", "args": []})
	return animation


func _label(label_name: String, text: String, size: int, spacing: int) -> Label:
	var label := Label.new()
	label.name = label_name
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# No base font: a FontVariation falls back to the default font, which then
	# stays out of the saved scene.
	var font := FontVariation.new()
	font.spacing_glyph = spacing
	label.add_theme_font_override(&"font", font)
	label.add_theme_font_size_override(&"font_size", size)
	label.add_theme_color_override(&"font_color", Color(0.9, 0.91, 0.94))
	label.add_theme_color_override(&"font_shadow_color", Color(0, 0, 0, 0.7))
	label.add_theme_constant_override(&"shadow_offset_y", 4)
	return label


func _add(parent: Node, child: Node, owner_node: Node) -> void:
	parent.add_child(child)
	child.owner = owner_node


func _vec(value: Array) -> Vector2:
	return Vector2(value[0], value[1])
