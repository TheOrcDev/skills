class_name StepsCutscene
extends Cutscene
## A cutscene whose steps are a callable, body.call(c): for short scripted
## stretches such as a playable memory's way in and out.

var body: Callable


func _init(name: StringName, steps: Callable) -> void:
	id = name
	body = steps


func run(c: CutsceneSteps) -> void:
	await body.call(c)
