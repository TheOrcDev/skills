extends SceneTree
## Creates the core scenes: the entry scene res://src/core/main.tscn and
## the hero, res://content/characters/hero/hero.tscn, drawn from their
## sprites (build those first with import_sprites.gd). Existing scenes
## are kept unless named with --replace.
##
##   tools/godot.sh --headless --script res://addons/adv_tools/scaffold_core.gd [-- --replace=main,hero]

const MAIN := "res://src/core/main.tscn"
const HERO := "res://content/characters/hero/hero.tscn"
const HERO_SPRITES := "res://content/characters/hero/hero_sprites.tres"

var _replace: PackedStringArray = []


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--replace="):
			_replace = arg.get_slice("=", 1).split(",")
	var ok := _save(MAIN, _make_main, "main" in _replace)
	ok = _save(HERO, _make_hero, "hero" in _replace) and ok
	quit(0 if ok else 1)


func _save(path: String, make: Callable, replace: bool) -> bool:
	if FileAccess.file_exists(path) and not replace:
		print("scaffold_core: keeping %s" % path)
		return true
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
	var root: Node = make.call()
	var packed := PackedScene.new()
	var err := packed.pack(root)
	if err == OK:
		err = ResourceSaver.save(packed, path)
	root.free()
	print("scaffold_core: %s %s" % [path, error_string(err)])
	return err == OK


func _make_main() -> Node:
	var main := Node.new()
	main.name = "Main"
	main.set_script(load("res://src/core/main.gd"))
	return main


func _make_hero() -> Node:
	var hero := Actor.new()
	hero.name = "Hero"
	hero.speaker_name = "Hero"
	hero.subtitle_color = Color(0.86, 0.89, 0.96)
	hero.speech_offset = Vector2(0, -520)
	hero.depth_speed = 0.6
	hero.step_with_frames = true
	hero.talk_animations = [&"talk_a", &"talk_b"]
	var body := HeroBody.new()
	body.name = "Body"
	body.sprites = load(HERO_SPRITES)
	hero.add_child(body)
	body.owner = hero
	var fidgets := IdleFidgets.new()
	fidgets.name = "IdleFidgets"
	hero.add_child(fidgets)
	fidgets.owner = hero
	return hero
