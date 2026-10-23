class_name CutsceneSteps
extends RefCounted
## The steps a cutscene awaits. Each plays as written until
## the scene is skipped; then the step under way and every later one finish at
## once with the same end state:
## - walks put the actor where the walk would have ended;
## - lines run through without holding, so their mutations still happen;
## - waits end, and fades snap to their target;
## - animations stop, and shots jump to their last frame.

signal skipped

var skipping := false

var _tree: SceneTree
var _fade: ColorRect


func _init(tree: SceneTree, fade: ColorRect) -> void:
	_tree = tree
	_fade = fade


## Makes the step under way and every later one finish at once.
func skip() -> void:
	if skipping:
		return
	skipping = true
	Say.fast_forward = true
	Say.skip()
	skipped.emit()


## Walks `actor` to the reachable point nearest `point`.
func walk(actor: Actor, point: Vector2) -> void:
	if not skipping:
		var done := [false]
		var go := func() -> void:
			await actor.walk_to(point)
			done[0] = true
		go.call()
		while not done[0] and not skipping:
			await _tree.process_frame
	if skipping:
		actor.stop()
		actor.global_position = NavigationServer2D.map_get_closest_point(actor.get_world_2d().navigation_map, point)


func face(actor: Actor, point: Vector2) -> void:
	actor.face_point(point)


## Plays a one-shot animation such as `pickup_low`.
func anim(actor: Actor, base: StringName) -> void:
	if skipping:
		return
	var done := [false]
	var go := func() -> void:
		await actor.play(base)
		done[0] = true
	go.call()
	while not done[0] and not skipping:
		await _tree.process_frame
	if skipping:
		actor.stop()


## Runs a dialogue cue (content/dialogue/<file>.dialogue).
func say(file: StringName, cue: StringName) -> void:
	await Say.line(file, cue)


func wait(seconds: float) -> void:
	var timer := _tree.create_timer(seconds)
	while timer.time_left > 0.0 and not skipping:
		await _tree.process_frame


## Plays `animation` on `player`: a camera path, a title card.
func shot(player: AnimationPlayer, animation: StringName) -> void:
	if not skipping:
		player.play(animation)
		await _tree.process_frame
		while player.is_playing() and player.current_animation == animation and not skipping:
			await _tree.process_frame
	if skipping:
		if player.current_animation != animation:
			player.play(animation)
		player.seek(player.get_current_animation_length(), true)


## Fades the screen to black (`alpha` 1) or back (0).
func fade(alpha: float, seconds: float) -> void:
	if not skipping and seconds > 0.0:
		var tween := _fade.create_tween()
		tween.tween_property(_fade, ^"modulate:a", alpha, seconds)
		while tween.is_running() and not skipping:
			await _tree.process_frame
		tween.kill()
	_fade.modulate.a = alpha


func era(room: Room, value: StringName) -> void:
	room.set_era(value)
