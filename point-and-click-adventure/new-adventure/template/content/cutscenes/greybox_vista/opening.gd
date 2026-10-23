extends RevealCutscene
## The sample opening: it opens close on the hero beyond the gate, pulls back
## across the zoom stack to the land, and shows the title. It starts and ends
## on black, ready for the first room. With Reduce camera motion the pull-back
## is one crossfade. A game points `opening` in src/core/main.tscn at its own.


func _init() -> void:
	super(&"greybox_opening", preload("res://content/cutscenes/greybox_vista/greybox_vista.tscn"))
	starts_on_black = true
	ends_on_black = true
	fade_in_seconds = 1.5
