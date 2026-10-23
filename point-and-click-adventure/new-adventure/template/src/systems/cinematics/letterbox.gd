class_name Letterbox
extends CanvasLayer
## Black 2.39:1 bars for non-interactive sequences (docs/technical-plan.md §6.3).

const RATIO := 2.39

var amount := 0.0:
	set(value):
		amount = value
		_layout()

var _top: ColorRect
var _bottom: ColorRect
var _tween: Tween


func _ready() -> void:
	layer = 50
	_top = _bar()
	_bottom = _bar()
	_layout()


## Slides the bars in; 0 seconds snaps them.
func show_bars(seconds := 0.6) -> void:
	await _slide(1.0, seconds)


func hide_bars(seconds := 0.6) -> void:
	await _slide(0.0, seconds)


## The height of each bar when fully in, in viewport pixels.
func bar_height() -> float:
	var view := get_viewport().get_visible_rect().size
	return maxf(0.0, (view.y - view.x / RATIO) / 2.0)


func _slide(target: float, seconds: float) -> void:
	if _tween:
		_tween.kill()
	if seconds <= 0.0:
		amount = target
		return
	_tween = create_tween()
	_tween.tween_property(self, ^"amount", target, seconds).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	await _tween.finished


func _bar() -> ColorRect:
	var bar := ColorRect.new()
	bar.color = Color.BLACK
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bar)
	return bar


func _layout() -> void:
	if _top == null:
		return
	var view := get_viewport().get_visible_rect().size
	var height := bar_height() * amount
	_top.position = Vector2.ZERO
	_top.size = Vector2(view.x, height)
	_bottom.position = Vector2(0.0, view.y - height)
	_bottom.size = Vector2(view.x, height)
