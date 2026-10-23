extends Node
## Entry point: shows the start screen, and on New Game plays the opening
## cutscene (if any), then starts the game in `start_room`. A scripted QA run skips the start screen and starts at once.

## A Cutscene script, played before the first room, that ends on black; empty
## for none.
@export_file("*.gd") var opening := "res://content/cutscenes/greybox_vista/opening.gd"
@export var start_room: StringName = &"greybox_gate"
@export var start_entry: StringName = &"default"


func _ready() -> void:
	Menus.new_game_requested.connect(_start)
	if Qa.running():
		_start.call_deferred()
	else:
		Menus.show_title.call_deferred()


func _start() -> void:
	if not opening.is_empty() and not Qa.skips_opening():
		await Cutscenes.play((load(opening) as GDScript).new() as Cutscene)
	Saves.autosave = true
	Rooms.goto(start_room, start_entry, &"fade")
	# The room's own fade now covers the screen, so the opening's black can go.
	Cutscenes.clear_fade()
