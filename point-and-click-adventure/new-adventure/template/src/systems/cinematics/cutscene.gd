class_name Cutscene
extends RefCounted
## A scene the player watches (technical-plan.md §6.3). A subclass
## overrides run(c) and awaits steps on `c`; `Cutscenes.play()` runs it. A skip
## makes every step finish at once while this script's logic still runs, so a
## skipped scene leaves the world as a watched one does. Keep anything that
## changes the world in the script, never in animation keys, which a skip
## jumps over.

## The name it is known by, for rewatching from the journal.
var id: StringName


func run(_c: CutsceneSteps) -> void:
	pass
