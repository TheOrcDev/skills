extends Node
## The hero's hints (game-design.md §8 and §10). Clicked, the hero
## thinks aloud about the current goal, more directly each time they are asked
## about the same one. The goals and their order are in content/hints/goals.gd.
## The lines are the cues `<goal>_1`, `<goal>_2` … in
## content/dialogue/hints.dialogue, and `none` once every goal is done.

const GOALS := preload("res://content/hints/goals.gd")
const DIALOGUE := &"hints"


## The first goal not yet done, or &"" once all are.
func current_goal() -> StringName:
	for goal: Dictionary in GOALS.GOALS:
		if not _done(goal):
			return goal["goal"]
	return &""


## The hero thinks aloud about the current goal.
func ask() -> void:
	var goal := current_goal()
	if goal == &"":
		await Say.line(DIALOGUE, &"none")
		return
	var asked := int(GameState.hints.get(goal, 0)) + 1
	GameState.hints[goal] = asked
	await Say.line(DIALOGUE, cue_for(goal, asked))


## The cue for asking about `goal` the `asked`-th time; the most direct one
## once the lines run out.
func cue_for(goal: StringName, asked: int) -> StringName:
	var cues := (load(Say.DIALOGUE_PATH % DIALOGUE) as DialogueResource).get_cues()
	var step := asked
	while step > 1 and not cues.has("%s_%d" % [goal, step]):
		step -= 1
	return StringName("%s_%d" % [goal, step])


static func _done(goal: Dictionary) -> bool:
	if goal.has("flag"):
		return bool(GameState.get_flag(goal["flag"]))
	if goal.has("memory"):
		return goal["memory"] in GameState.memories
	return false
