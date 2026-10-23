extends Closeup
## The notice board by the gate, up close: the house's order, and its seal.
## The order is written large, so seeing it counts as reading it.


func _on_shown() -> void:
	GameState.set_flag(&"greybox_notice_read")


func look_text() -> void:
	await Say.line(&"greybox", &"notice_text")


func look_seal() -> void:
	await Say.line(&"greybox", &"notice_seal")
