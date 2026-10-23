extends Room
## Beyond the greybox gate. Reaching it finishes the sample puzzle chain. The
## way on shows the land beyond as a discovery reveal, the milestone shows the
## same land as it was (a memory vista), and the warden is the sample NPC: one
## painting skinned to a few bones.

const VISTA := preload("res://content/cutscenes/greybox_vista/greybox_vista.tscn")


func _on_enter(_from: StringName) -> void:
	GameState.set_flag(&"greybox_done")


func look_warden() -> void:
	await Say.line(&"greybox", &"warden_look")


func talk_warden() -> void:
	await Say.line(&"greybox", &"warden_talk")
	var warden := actors.get_node_or_null(^"Warden") as Actor
	if warden:
		await warden.play(&"nod")


func look_path() -> void:
	await Say.line(&"greybox", &"path_look")


func use_path() -> void:
	await Say.line(&"greybox", &"path_use")
	await Cutscenes.play(rewatch_greybox_vista())


func look_milestone() -> void:
	await Say.line(&"greybox", &"milestone_look")


func use_milestone() -> void:
	await Say.line(&"greybox", &"milestone_use")
	await Cutscenes.play(rewatch_greybox_milestone())


## The reveal and the memory vista, for using the path and the milestone, and
## for watching them again from the journal.
func rewatch_greybox_vista() -> RevealCutscene:
	return RevealCutscene.new(&"greybox_vista", VISTA)


func rewatch_greybox_milestone() -> RevealCutscene:
	return RevealCutscene.new(&"greybox_milestone", VISTA, &"then")
