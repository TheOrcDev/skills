class_name RevealStage
extends Node2D
## The stage of a pull-back reveal (technical-plan.md §6.3), as new_reveal.gd
## builds it: the zoom stack in a Reveal with the hero standing in it, the title
## card, and an AnimationPlayer whose "reveal" animation pulls back and shows
## the title. A RevealCutscene plays it.

## Reduce camera motion: when, on the animation's clock, the close shot
## crossfades to the vista (the middle of the pull-back), and for how long.
const CUT_AT := 6.0
const CROSSFADE := 1.6

@onready var reveal: Reveal = $Reveal
@onready var hero: HeroBody = $Reveal/Hero
@onready var animation: AnimationPlayer = $AnimationPlayer
@onready var title: Control = $Title/Card


func _ready() -> void:
	title.modulate.a = 0.0
	hero.play_animation(&"idle_r", false)


## Called from the animation.
func show_title() -> void:
	create_tween().tween_property(title, ^"modulate:a", 1.0, 1.4)


## Called from the animation.
func hide_title() -> void:
	create_tween().tween_property(title, ^"modulate:a", 0.0, 1.0)


## Reduce camera motion: the view holds the close shot, then at the middle of
## the move crossfades once to the vista instead of travelling. Call it before
## the animation starts.
func crossfade_to_vista(c: CutsceneSteps) -> void:
	reveal.hold = true
	await get_tree().process_frame
	while animation.current_animation_position < CUT_AT and not c.skipping:
		await get_tree().process_frame
	if c.skipping:
		return
	var still := _snapshot()
	reveal.show_at(1.0)
	if still:
		var tween := create_tween()
		tween.tween_property(still, ^"modulate:a", 0.0, CROSSFADE)
		await tween.finished
		still.get_parent().queue_free()


## The screen as it is now, held on top of everything but the fade.
func _snapshot() -> TextureRect:
	if DisplayServer.get_name() == "headless":
		return null
	var image := get_viewport().get_texture().get_image()
	if image == null or image.is_empty():
		return null
	var layer := CanvasLayer.new()
	layer.layer = 94
	add_child(layer)
	var still := TextureRect.new()
	still.texture = ImageTexture.create_from_image(image)
	still.set_anchors_preset(Control.PRESET_FULL_RECT)
	still.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	still.stretch_mode = TextureRect.STRETCH_SCALE
	still.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(still)
	return still
