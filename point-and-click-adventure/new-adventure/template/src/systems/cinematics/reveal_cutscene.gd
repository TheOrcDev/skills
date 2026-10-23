class_name RevealCutscene
extends Cutscene
## A discovery reveal as a cutscene (technical-plan.md §6.3).
## It plays a RevealStage scene built by new_reveal.gd: fade in, pull back (with
## its title, if any), fade out. Letterbox, skipping and the Reduce camera
## motion crossfade come with the runner and the stage. With `era` "then" it is
## a memory vista, under the past's warm grade while it plays, and finishing it
## records the memory `id`. In the middle of play it fades out of the room and
## back; the opening instead starts and ends on black.

var stage_scene: PackedScene
var era: StringName = &"now"
var starts_on_black := false
var ends_on_black := false
var fade_in_seconds := 1.0
var fade_out_seconds := 1.0
## The stage while the reveal plays (QA and tests look at it).
var stage: RevealStage


func _init(name: StringName, scene: PackedScene, in_era: StringName = &"now") -> void:
	id = name
	stage_scene = scene
	era = in_era


func run(c: CutsceneSteps) -> void:
	if not starts_on_black:
		await c.fade(1.0, 0.6)
	var tree := Engine.get_main_loop() as SceneTree
	stage = stage_scene.instantiate()
	# Under the main scene in the game (QA looks for it there); tests have none.
	(tree.current_scene if tree.current_scene else tree.root).add_child(stage)
	stage.reveal.camera.make_current()
	Flashback.set_grade(1.0 if era == &"then" else 0.0)
	await c.fade(1.0, 0.0)
	c.fade(0.0, fade_in_seconds)
	if Settings.reduce_camera_motion:
		stage.crossfade_to_vista(c)
	await c.shot(stage.animation, &"reveal")
	if era == &"then":
		Journal.capture_when_drawn(id)
	await c.fade(1.0, fade_out_seconds)
	# A freed camera leaves the view where it was; hand it back to the room's.
	var view := stage.get_viewport()
	stage.reveal.camera.enabled = false
	stage.queue_free()
	view.canvas_transform = Transform2D.IDENTITY
	var room := Rooms.current
	Flashback.set_grade(1.0 if room and room.era == &"then" else 0.0)
	if not ends_on_black:
		await c.fade(0.0, 0.6)
	if era == &"then":
		GameState.remember(id)
