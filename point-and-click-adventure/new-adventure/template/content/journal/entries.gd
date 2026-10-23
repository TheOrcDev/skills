extends RefCounted
## What the journal shows (src/ui/journal_screen.gd). A game replaces these
## with its own memories, facts and rewatchable cutscenes; the greybox entries
## are the sample chain's.

## The name the "Who am I?" page shows. A game whose hero learns their name
## can return it from a flag here.
static func hero_name() -> String:
	return "Hero"


## A page per memory: its title and the cue of its one line in
## content/dialogue/journal.dialogue.
const MEMORIES := {
	&"greybox_window": {"title": "The chapel at noon", "cue": &"greybox_window"},
	&"greybox_altar": {"title": "Mercy", "cue": &"greybox_altar"},
	&"greybox_milestone": {"title": "The road as it was", "cue": &"greybox_milestone"},
}

## What the hero can learn about themselves, for the "Who am I?" page.
const FACTS := {
	&"greybox_mercy": "The word that opens the gate was carved by someone who believed in mercy.",
}

## Cutscenes that can be watched again: a title, and either the script that
## makes them or the room whose rewatch_<id>() does.
const REWATCH := {
	&"greybox_opening": {"title": "The land beyond the gate", "script": "res://content/cutscenes/greybox_vista/opening.gd"},
	&"greybox_window": {"title": "The chapel at noon", "room": &"greybox_chapel"},
	&"greybox_vista": {"title": "The land beyond", "room": &"greybox_courtyard"},
	&"greybox_milestone": {"title": "The road as it was", "room": &"greybox_courtyard"},
}
