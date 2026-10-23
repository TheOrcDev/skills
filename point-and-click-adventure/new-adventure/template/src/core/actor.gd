class_name Actor
extends Node2D
## A character that walks the room's navigation mesh, faces where it goes,
## scales with depth and plays `<anim>_<dir>` animations on its ActorBody
## child. The origin is at the feet.

signal _walk_done(walk_id: int, completed: bool)
signal _one_shot_ended

## The name this actor speaks under in .dialogue files, for example "the hero".
@export var speaker_name := ""
## Other names the same actor speaks under, for example the real name an NPC
## remembers.
@export var speaker_aliases: PackedStringArray = []
## Pixels per second at scale 1, unless the body's walk was rendered with its
## own ground speed. Farther away (smaller) is slower on screen.
@export var walk_speed := 320.0
## Moving up or down the screen is moving in depth, which crosses less of the
## screen: vertical speed is this fraction of horizontal speed.
@export_range(0.1, 1.0) var depth_speed := 1.0
## Move only when the body shows a new frame, a frame's worth of ground at a
## time, so the planted foot never slides (classic adventure-game stepping).
@export var step_with_frames := false
@export var diagonals := false
## Base animations to cycle through, one per line, while the actor speaks
## standing still, for example [&"talk_a", &"talk_b"]. Empty keeps idle.
@export var talk_animations: Array[StringName] = []
@export var subtitle_color := Color(0.92, 0.92, 0.92)
## Where subtitles sit, relative to the feet, at scale 1.
@export var speech_offset := Vector2(0, -440)

var facing: AnimNames.Dir = AnimNames.Dir.D
var is_walking: bool:
	get:
		return not _path.is_empty()

var _body: ActorBody
var _base_anim: StringName = &"idle"
var _path := PackedVector2Array()
var _walk_id := 0
var _speaking := false
var _talk_base: StringName = &""
var _talk_count := 0
var _one_shot: StringName = &""


func _ready() -> void:
	for child in get_children():
		if child is ActorBody:
			_body = child
			_body.animation_finished.connect(_on_body_finished)
			break
	_apply_animation()


## Whether `world` is on the actor as drawn now.
func contains_point(world: Vector2) -> bool:
	return _body != null and _body.contains_point(world)


## Walks to the reachable point nearest `target`. Returns true on arrival and
## false if another walk or stop() interrupted it.
func walk_to(target: Vector2) -> bool:
	_interrupt()
	_end_one_shot()
	_walk_id += 1
	var my_id := _walk_id
	await _navigation_ready()
	var map := get_world_2d().navigation_map
	var destination := NavigationServer2D.map_get_closest_point(map, target)
	_path = NavigationServer2D.map_get_path(map, global_position, destination, true)
	while not _path.is_empty() and _path[0].distance_to(global_position) < 1.0:
		_path.remove_at(0)
	if _path.is_empty():
		return my_id == _walk_id
	_set_base_animation(&"walk")
	var completed := false
	while true:
		var result: Array = await _walk_done
		if result[0] == my_id:
			completed = result[1]
			break
	return completed


func stop() -> void:
	_interrupt()
	_set_base_animation(&"idle")


func face(dir: AnimNames.Dir) -> void:
	if dir != facing:
		facing = dir
		_apply_animation()


func face_point(point: Vector2) -> void:
	face(AnimNames.dir_from_vector(point - global_position, diagonals))


## Plays a one-shot animation such as `pickup_low` and waits for it to end or
## be interrupted (by a walk or another one-shot). Never use it for looping
## animations; they do not finish.
func play(base: StringName) -> void:
	if _body == null:
		return
	var choice := AnimNames.resolve(base, facing, _body.has_animation)
	if choice.is_empty():
		push_warning("%s has no animation %s" % [name, base])
		return
	_end_one_shot()
	_one_shot = choice.name
	_body.play_animation(choice.name, choice.flip)
	await _one_shot_ended
	# Resume from the tree, not from this actor's own signal, so the caller may
	# free the actor straight away.
	if is_inside_tree():
		await get_tree().process_frame


## True while standing still with nothing to do: not walking, speaking or
## playing a one-shot.
func is_idle() -> bool:
	return _path.is_empty() and not _speaking and _one_shot == &""


## Say calls this around each line the actor speaks, so the body can act it.
func set_speaking(on: bool) -> void:
	if _body:
		_body.set_speaking(on)
	if on == _speaking:
		return
	_speaking = on
	if on and not talk_animations.is_empty():
		_talk_base = talk_animations[_talk_count % talk_animations.size()]
		_talk_count += 1
	_apply_animation()


## Where this actor's subtitles sit, in world coordinates.
func speech_position() -> Vector2:
	return to_global(speech_offset)


func _process(_delta: float) -> void:
	var room := Room.of(self)
	var s := room.scale_at(global_position.y) if room else 1.0
	scale = Vector2(s, s)


func _physics_process(delta: float) -> void:
	if _path.is_empty():
		return
	var speed := walk_speed
	if _body and _body.ground_speed() > 0.0:
		speed = _body.ground_speed()
	# Ground to cover this tick, in pixels at the current scale.
	var ground := speed * scale.y * delta
	if step_with_frames and _body and _body.frame_rate() > 0.0:
		if not _body.consume_step():
			return
		ground = speed * scale.y / _body.frame_rate()
	while ground > 0.0 and not _path.is_empty():
		var to_next := _path[0] - global_position
		var distance := to_next.length()
		if distance > 0.5:
			face(AnimNames.dir_from_vector(to_next, diagonals))
		var factor := 1.0
		if distance > 0.001:
			factor = maxf(Vector2(to_next.x, to_next.y * depth_speed).length() / distance, 0.05)
		var reach := ground * factor
		if distance <= reach:
			global_position = _path[0]
			_path.remove_at(0)
			ground -= distance / factor
		else:
			global_position += to_next / distance * reach
			ground = 0.0
	if _path.is_empty():
		_set_base_animation(&"idle")
		_walk_done.emit(_walk_id, true)


func _interrupt() -> void:
	if not _path.is_empty():
		_path.clear()
		_walk_done.emit(_walk_id, false)


## The navigation map syncs on physics frames; a freshly loaded room needs one.
func _navigation_ready() -> void:
	var map := get_world_2d().navigation_map
	for i in 10:
		if NavigationServer2D.map_get_iteration_id(map) > 0:
			return
		await get_tree().physics_frame


func _set_base_animation(base: StringName) -> void:
	if base != _base_anim:
		_base_anim = base
		_apply_animation()


func _on_body_finished(anim: StringName) -> void:
	if anim == _one_shot:
		_end_one_shot()


func _end_one_shot() -> void:
	if _one_shot == &"":
		return
	_one_shot = &""
	_apply_animation()
	_one_shot_ended.emit()


func _apply_animation() -> void:
	if _body == null or _one_shot != &"":
		return
	var base := _base_anim
	if base == &"idle" and _speaking and _talk_base != &"":
		base = _talk_base
	var choice := AnimNames.resolve(base, facing, _body.has_animation)
	if choice.is_empty():
		choice = AnimNames.resolve(&"idle", facing, _body.has_animation)
	if not choice.is_empty():
		_body.play_animation(choice.name, choice.flip)
