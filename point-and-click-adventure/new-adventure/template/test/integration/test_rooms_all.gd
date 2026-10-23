extends GutTest
## Every room in content/chapters.json: it loads as a Room,
## has a baked walk area and a default marker, every hotspot answers Look, and
## every exit leads to a room that exists, onto a marker it has. Every room
## folder is in the registry, apart from the development rooms.

const DEV_ROOMS := ["sandbox", "greybox_gate", "greybox_chapel", "greybox_courtyard"]


func _scene(room_id: StringName) -> PackedScene:
	return load(Rooms.ROOM_PATH % [room_id, room_id]) as PackedScene


func test_every_room_folder_is_registered() -> void:
	var registered := Chapters.all_rooms()
	for room_id in DirAccess.get_directories_at("res://content/rooms"):
		if room_id in DEV_ROOMS:
			continue
		assert_true(StringName(room_id) in registered, "%s is in content/chapters.json" % room_id)
	var seen := {}
	for room_id in registered:
		assert_false(seen.has(room_id), "%s is listed once" % room_id)
		seen[room_id] = true


func test_every_part_starts_in_one_of_its_rooms() -> void:
	for part: Dictionary in Chapters.parts():
		if not part["rooms"].is_empty():
			assert_true(part["start"] in part["rooms"], "%s starts in one of its rooms" % part["id"])


func test_every_room_is_whole() -> void:
	for room_id in Chapters.all_rooms():
		var scene := _scene(room_id)
		assert_not_null(scene, "%s loads" % room_id)
		if scene == null:
			continue
		var room := scene.instantiate() as Room
		assert_not_null(room, "%s is a Room" % room_id)
		if room == null:
			continue
		var walk := room.get_node_or_null("WalkAreas/Now") as NavigationRegion2D
		assert_true(walk != null and walk.navigation_polygon != null and walk.navigation_polygon.get_polygon_count() > 0, "%s has a walk area" % room_id)
		assert_not_null(room.get_node_or_null("Markers/default"), "%s has a default marker" % room_id)
		for node in room.get_node("Hotspots").get_children():
			if node is Exit:
				_check_exit(room_id, node as Exit)
			elif node is Hotspot:
				var hotspot := node as Hotspot
				assert_true(room.has_method("look_%s" % hotspot.id), "%s/%s answers Look" % [room_id, hotspot.id])
				if hotspot.default_verb != &"look":
					assert_true(room.has_method("%s_%s" % [hotspot.default_verb, hotspot.id]), "%s/%s answers its default verb" % [room_id, hotspot.id])
		room.free()


func _check_exit(room_id: StringName, exit: Exit) -> void:
	var target := _scene(exit.target_room)
	assert_not_null(target, "%s/%s leads to %s" % [room_id, exit.id, exit.target_room])
	if target == null:
		return
	var other := target.instantiate()
	assert_not_null(other.get_node_or_null("Markers/%s" % exit.target_entry), "%s has the marker %s for %s/%s" % [exit.target_room, exit.target_entry, room_id, exit.id])
	other.free()
