extends Node
## Save slots (docs/technical-plan.md §5.7): JSON at `<directory>/slot_<n>.json`
## with a thumbnail beside it as `slot_<n>.png`. A save is GameState plus where
## The hero is: the room, the entry they came in by, their position and the room's
## era. Slot 0 is the autosave, written each time a room is shown, but only
## once main.gd has started a game, so tests and tools never write one. Older
## saves are migrated by `save_version` as they are read.

signal saved(slot: int)
signal loaded(slot: int)

const AUTOSAVE := 0
## Manual slots are 1 to SLOTS.
const SLOTS := 6
const THUMBNAIL := Vector2i(320, 180)

var directory := "user://saves"
var autosave := false


func _ready() -> void:
	Rooms.room_shown.connect(_on_room_shown)


func path(slot: int) -> String:
	return directory.path_join("slot_%d.json" % slot)


func thumbnail_path(slot: int) -> String:
	return directory.path_join("slot_%d.png" % slot)


func has_save(slot: int) -> bool:
	return FileAccess.file_exists(path(slot))


## The game as a save: GameState plus where the hero is.
func snapshot() -> Dictionary:
	var data := GameState.to_dict()
	data["saved_at"] = Time.get_datetime_string_from_system(true)
	var room := Rooms.current
	if room:
		data["room"] = String(room.room_id)
		data["room_name"] = room.display_name
		data["entry"] = String(Rooms.current_entry)
		data["era"] = String(room.era)
		if Rooms.player:
			data["position"] = [Rooms.player.global_position.x, Rooms.player.global_position.y]
	return data


## Writes `slot`, with `picture` as its thumbnail, or the screen as it is now.
func save(slot: int, picture: Image = null) -> Error:
	DirAccess.make_dir_recursive_absolute(directory)
	var file := FileAccess.open(path(slot), FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(JSON.stringify(snapshot(), "\t"))
	file.close()
	var image := picture if picture else screen_image()
	if image:
		image = image.duplicate() as Image
		image.resize(THUMBNAIL.x, THUMBNAIL.y, Image.INTERPOLATE_BILINEAR)
		image.save_png(thumbnail_path(slot))
	saved.emit(slot)
	return OK


## The slot saved most recently, the autosave included, or -1 if there is no
## save this build can read: what the start screen's Continue loads.
func latest_slot() -> int:
	var latest := -1
	var latest_at := ""
	for slot in range(AUTOSAVE, SLOTS + 1):
		var data := read(slot)
		if data.is_empty():
			continue
		var saved_at := str(data.get("saved_at", ""))
		if latest < 0 or saved_at > latest_at:
			latest = slot
			latest_at = saved_at
	return latest


## The picture saved with `slot`, or null.
func thumbnail(slot: int) -> Texture2D:
	if not FileAccess.file_exists(thumbnail_path(slot)):
		return null
	var image := Image.load_from_file(thumbnail_path(slot))
	return ImageTexture.create_from_image(image) if image and not image.is_empty() else null


## The screen as last drawn, or null where there is none (headless runs).
func screen_image() -> Image:
	if DisplayServer.get_name() == "headless":
		return null
	var texture := get_viewport().get_texture()
	var image := texture.get_image() if texture else null
	return image if image and not image.is_empty() else null


## The save in `slot`, migrated to this build's version; empty if there is
## none or it cannot be read.
func read(slot: int) -> Dictionary:
	if not has_save(slot):
		return {}
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(path(slot))) != OK:
		return {}
	return migrate(json.data) if json.data is Dictionary else {}


## Brings a save up to GameState.SAVE_VERSION, one `_migrate_from_<n>` step at a
## time. Empty if it is not a save, or comes from a newer build.
func migrate(data: Dictionary) -> Dictionary:
	var version := int(data.get("save_version", 0))
	if version < 1 or version > GameState.SAVE_VERSION:
		return {}
	while version < GameState.SAVE_VERSION:
		data = call("_migrate_from_%d" % version, data)
		version += 1
		data["save_version"] = version
	return data


## Loads `slot`: the state first, then its room, with the hero where they were.
func load_slot(slot: int) -> Error:
	var data := read(slot)
	if data.is_empty():
		return ERR_FILE_UNRECOGNIZED if has_save(slot) else ERR_FILE_NOT_FOUND
	await restore(data)
	loaded.emit(slot)
	return OK


## Puts the game in the state `data` describes (a migrated save).
func restore(data: Dictionary) -> void:
	if Closeups.current:
		await Closeups.close()
	GameState.from_dict(data)
	var era := StringName(str(data.get("era", "now")))
	var position: Variant = data.get("position")
	# Placed while the screen is still black, before the room fades in.
	Rooms.room_changed.connect(func(room: Room) -> void:
		if room.era != era:
			room.set_era(era)
		if position is Array and position.size() == 2:
			Rooms.player.global_position = Vector2(position[0], position[1]), CONNECT_ONE_SHOT)
	await Rooms.goto(StringName(str(data.get("room", first_room()))), StringName(str(data.get("entry", "default"))), &"fade")


## 1 → 2: version 1 held flags and the inventory; the rest starts empty, and
## with no room named the game resumes in the first room.
func _migrate_from_1(data: Dictionary) -> Dictionary:
	data.merge({"room_states": {}, "memories": [], "hints": {}, "play_seconds": 0.0})
	return data


## 2 → 3: the journal's facts and the cutscenes seen start empty.
func _migrate_from_2(data: Dictionary) -> Dictionary:
	data.merge({"facts": [], "cutscenes_seen": []})
	return data


func _on_room_shown(_room: Room) -> void:
	if not autosave:
		return
	# Let the room draw once without the fade, for the thumbnail.
	await get_tree().process_frame
	await get_tree().process_frame
	save(AUTOSAVE)


## Where a save that names no room resumes: the first part's start room.
static func first_room() -> StringName:
	return StringName(Chapters.parts()[0]["start"])
