extends Node
## The journal's memory (technical-plan.md §6.7). It keeps a
## still of each memory, captured the first time it is seen and kept in
## `directory` beside the saves, and it plays seen cutscenes again. What the
## journal shows is listed in content/journal/entries.gd.

const ENTRIES := preload("res://content/journal/entries.gd")
const STILL := Vector2i(640, 360)

var directory := "user://journal"


func still_path(id: StringName) -> String:
	return directory.path_join("%s.png" % id)


## Keeps a still of the memory `id` from the screen as it is now, unless it has
## one already. `picture` stands in for the screen (tests).
func capture(id: StringName, picture: Image = null) -> void:
	if FileAccess.file_exists(still_path(id)):
		return
	var image := picture if picture else Saves.screen_image()
	if image == null:
		return
	image = image.duplicate() as Image
	image.resize(STILL.x, STILL.y, Image.INTERPOLATE_BILINEAR)
	DirAccess.make_dir_recursive_absolute(directory)
	image.save_png(still_path(id))


## The same, a frame later, once the screen has drawn what is showing now.
func capture_when_drawn(id: StringName) -> void:
	if FileAccess.file_exists(still_path(id)) or DisplayServer.get_name() == "headless":
		return
	await get_tree().process_frame
	capture(id)


## The still of the memory `id`, or null.
func still(id: StringName) -> Texture2D:
	if not FileAccess.file_exists(still_path(id)):
		return null
	var image := Image.load_from_file(still_path(id))
	return ImageTexture.create_from_image(image) if image and not image.is_empty() else null


## The memories seen that have a journal page, in the order seen.
func memories() -> Array[StringName]:
	var result: Array[StringName] = []
	for id in GameState.memories:
		if ENTRIES.MEMORIES.has(id):
			result.append(id)
	return result


## The cutscenes seen that can be watched again, in the order seen.
func rewatchable() -> Array[StringName]:
	var result: Array[StringName] = []
	for id in GameState.cutscenes_seen:
		if ENTRIES.REWATCH.has(id):
			result.append(id)
	return result


## Plays the cutscene `id` again, going to its room if it has one, and puts
## everything back afterwards: the room, where the hero stood, and GameState.
## So watching again never changes the game.
func rewatch(id: StringName) -> void:
	var entry: Dictionary = ENTRIES.REWATCH.get(id, {})
	if entry.is_empty() or Rooms.current == null:
		return
	var state := GameState.to_dict()
	var back_room := Rooms.current.room_id
	var back_entry := Rooms.current_entry
	var back_at := Rooms.player.global_position
	var cutscene: Cutscene
	if entry.has("script"):
		cutscene = (load(entry["script"]) as GDScript).new()
		if cutscene is RevealCutscene:
			(cutscene as RevealCutscene).starts_on_black = false
	else:
		if Rooms.current.room_id != entry["room"]:
			await Rooms.goto(entry["room"], &"default", &"fade")
		cutscene = Rooms.current.call(StringName("rewatch_%s" % id))
	await Cutscenes.play(cutscene)
	if Rooms.current.room_id != back_room or Cutscenes.fade_amount() > 0.0:
		Rooms.room_changed.connect(func(_room: Room) -> void: Rooms.player.global_position = back_at, CONNECT_ONE_SHOT)
		Rooms.goto(back_room, back_entry, &"fade")
		Cutscenes.clear_fade()
		await Rooms.room_shown
	GameState.from_dict(state)
