extends RefCounted
## The goals the hero's hints follow (src/systems/hints.gd), in order. A goal
## is current until its flag is set or its memory seen. Write a part's goals
## from its puzzle chart; these are the greybox chain's.

const GOALS: Array[Dictionary] = [
	{"goal": &"rag", "flag": &"greybox_rag_taken"},
	{"goal": &"word", "flag": &"greybox_knows_word"},
	{"goal": &"oil", "flag": &"greybox_oil_taken"},
	{"goal": &"hinges", "flag": &"greybox_gate_oiled"},
	{"goal": &"say_word", "flag": &"greybox_word_spoken"},
	{"goal": &"through", "flag": &"greybox_done"},
]
