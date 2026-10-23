extends SceneTree
## Creates the audio bus layout (audio-pipeline.md §7): Master, with
## Voice, Music, Ambience, SFX and UI sending to it. No bus effects. Saved through
## Godot as res://default_bus_layout.tres, which Godot loads at start-up.
##
##   tools/godot.sh --headless --script res://addons/adv_tools/new_bus_layout.gd

const BUSES: Array[StringName] = [&"Voice", &"Music", &"Ambience", &"SFX", &"UI"]
const PATH := "res://default_bus_layout.tres"


func _initialize() -> void:
	while AudioServer.bus_count > 1:
		AudioServer.remove_bus(AudioServer.bus_count - 1)
	for bus_name in BUSES:
		AudioServer.add_bus()
		var index := AudioServer.bus_count - 1
		AudioServer.set_bus_name(index, bus_name)
		AudioServer.set_bus_send(index, &"Master")
	var err := ResourceSaver.save(AudioServer.generate_bus_layout(), PATH)
	print("new_bus_layout: %s %s" % [PATH, error_string(err)])
	quit(0 if err == OK else 1)
