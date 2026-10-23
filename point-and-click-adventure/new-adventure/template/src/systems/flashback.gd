extends Node
## Flashbacks and the era grade (docs/technical-plan.md §6.1–6.2).
## A vision blooms the room's past out from an anchor point: the then
## background dissolves in over the now one, each era's effects and occluders
## crossfade, the grade turns warm, then the camera drifts while something
## plays, and finally the past drains back into the anchor. A vision is a
## cutscene (`Vision`), so a skip snaps every step to its end.

signal vision_started(origin: Vector2)
signal vision_finished(origin: Vector2)

const DISSOLVE := preload("res://src/shaders/memory_dissolve.gdshader")
const GRADE := preload("res://src/shaders/era_grade.gdshader")

## Softens the flare at the start of a vision (an accessibility setting).
var reduce_flashing := false
var transition_seconds := 3.2
var playing := false
## True while the hero plays inside a memory (enter_memory).
var in_memory := false

var _grade_material: ShaderMaterial
var _flare: Sprite2D
var _drift: Camera2D


func _ready() -> void:
	var grade_layer := CanvasLayer.new()
	grade_layer.layer = 10
	add_child(grade_layer)
	var grade := ColorRect.new()
	grade.set_anchors_preset(Control.PRESET_FULL_RECT)
	grade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_grade_material = ShaderMaterial.new()
	_grade_material.shader = GRADE
	_grade_material.set_shader_parameter(&"noise_tex", Effects.noise_texture(17, 0.9))
	grade.material = _grade_material
	grade_layer.add_child(grade)

	var flare_layer := CanvasLayer.new()
	flare_layer.layer = 11
	add_child(flare_layer)
	_flare = Sprite2D.new()
	_flare.texture = Effects.soft_dot()
	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_flare.material = additive
	_flare.modulate = Color(1.0, 0.95, 0.85, 0.0)
	flare_layer.add_child(_flare)

	Rooms.room_changed.connect(func(room: Room) -> void: set_grade(1.0 if room.era == &"then" else 0.0))
	Rooms.while_black.append(warm_up)
	# Noise textures generate on first use; start the dissolve's now so the first vision has it.
	Effects.noise_texture(23, 0.02)


func _process(_delta: float) -> void:
	_grade_material.set_shader_parameter(&"grain_offset", Vector2(randf(), randf()))


## 0 is the present's grade, 1 the past's.
func set_grade(value: float) -> void:
	_grade_material.set_shader_parameter(&"mix_then", value)


func get_grade() -> float:
	return float(_grade_material.get_shader_parameter(&"mix_then"))


## Film grain strength; 0 turns it off. The default is 0.04.
func set_grain(amount: float) -> void:
	_grade_material.set_shader_parameter(&"grain", amount)


## Draws the room's past once, unseen, so its shaders are compiled before the
## first vision. Browsers compile on first draw, which stalled a vision 141 ms.
func warm_up(room: Node) -> void:
	var then_layer := (room as Room).layers.get_node_or_null("Then") as CanvasItem
	if then_layer == null:
		return
	var shown: Array[CanvasItem] = [then_layer]
	for node in (room as Room).era_nodes():
		if node.is_in_group(&"era_then"):
			shown.append(node)
	var was_visible: Array[bool] = []
	for node in shown:
		was_visible.append(node.visible)
		node.visible = true
	var background := then_layer.get_node_or_null("Background") as Sprite2D
	if background:
		var dissolve := ShaderMaterial.new()
		dissolve.shader = DISSOLVE
		dissolve.set_shader_parameter(&"noise_tex", Effects.noise_texture(23, 0.02))
		dissolve.set_shader_parameter(&"progress", 0.5)
		background.material = dissolve
	# Visible through two whole frames, so both get drawn (headless runs draw nothing
	# and never post a draw, so this waits on process frames instead).
	await get_tree().process_frame
	await get_tree().process_frame
	if not is_instance_valid(room):
		return  # cleared while warming up
	if background:
		background.material = null
	for i in shown.size():
		shown[i].visible = was_visible[i]


## Plays the vision of the memory `id` in `room`, blooming from `origin` (room
## pixels), as a cutscene: skippable, and noted in GameState once it ends.
## `during` is awaited with the cutscene's steps while the past shows, as
## during.call(c); without it the past holds for a few seconds.
func vision(id: StringName, room: Room, origin: Vector2, during := Callable()) -> void:
	await Cutscenes.play(Vision.new(id, room, origin, during))


## Steps into the past of `room` for play (a playable memory, §6.1). The past
## blooms from `origin` as a short cutscene; then the hero walks the past's walk
## area and uses its hotspots until `done` holds (a flag name, or a callable
## returning true), and the past drains back. The room's ways out are shut
## meanwhile. Finishing records the memory `id`. Call it from a verb without
## await: the verb has to return before the player can act in the past.
func enter_memory(id: StringName, room: Room, origin: Vector2, done: Variant) -> void:
	await Cutscenes.play(StepsCutscene.new(&"", func(c: CutsceneSteps) -> void: await open_past(c, room, origin, false)))
	in_memory = true
	Journal.capture_when_drawn(id)
	var shut: Array[Hotspot] = []
	for node in room.hotspots.get_children():
		if node is Exit and node.visible:
			node.visible = false
			shut.append(node)
	while is_instance_valid(room) and not _met(done):
		await get_tree().process_frame
	if not is_instance_valid(room):
		in_memory = false
		return
	await Cutscenes.play(StepsCutscene.new(&"", func(c: CutsceneSteps) -> void: await close_past(c, room, origin)))
	for exit in shut:
		if is_instance_valid(exit):
			exit.visible = true
	in_memory = false
	GameState.remember(id)


## A vision's way into the past, as cutscene steps; a playable memory keeps the
## camera still (no `drift`).
func open_past(c: CutsceneSteps, room: Room, origin: Vector2, drift := true) -> void:
	playing = true
	_hero_reacts(true)
	vision_started.emit(origin)
	await _transition(c, room, origin, true)
	room.set_era(&"then")
	_drift = _start_drift(room, origin) if drift else null


## A vision's way back to the present, as cutscene steps.
func close_past(c: CutsceneSteps, room: Room, origin: Vector2) -> void:
	await _end_drift(c, _drift)
	_drift = null
	_hero_reacts(false)
	await _transition(c, room, origin, false)
	room.set_era(&"now")
	playing = false
	vision_finished.emit(origin)


## The hero's eyes flare as a vision opens and as it closes; as it opens, the
## memory also takes the hero's body (the flare one-shot, if they have it).
func _hero_reacts(into_past: bool) -> void:
	var player := Rooms.player
	if player == null:
		return
	var body := player.get_node_or_null("Body")
	if body and body.has_method(&"flare"):
		body.flare(1.6 if into_past else 1.0)
	if into_past:
		player.play(&"flare")


func _transition(c: CutsceneSteps, room: Room, origin: Vector2, into_past: bool) -> void:
	var now_layer := room.layers.get_node("Now") as CanvasItem
	var then_layer := room.layers.get_node("Then") as CanvasItem
	var then_background := then_layer.get_node("Background") as Sprite2D
	now_layer.visible = true
	then_layer.visible = true

	var dissolve := ShaderMaterial.new()
	dissolve.shader = DISSOLVE
	dissolve.set_shader_parameter(&"noise_tex", Effects.noise_texture(23, 0.02))
	dissolve.set_shader_parameter(&"origin", origin / then_background.texture.get_size())
	then_background.material = dissolve

	var now_nodes := _crossfading(room, now_layer, &"era_now")
	var then_nodes := _crossfading(room, then_layer, &"era_then")
	var fading_in := then_nodes if into_past else now_nodes
	var fading_out := now_nodes if into_past else then_nodes
	var start := 0.0 if into_past else 1.0
	var end := 1.0 - start
	dissolve.set_shader_parameter(&"progress", start)
	for node in fading_in + fading_out:
		node.visible = true
	for node in fading_in:
		node.modulate.a = 0.0
	if into_past and not c.skipping:
		_flash(room, origin)

	var tween := create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_method(func(value: float) -> void: dissolve.set_shader_parameter(&"progress", value), start, end, transition_seconds)
	tween.tween_method(set_grade, start, end, transition_seconds)
	for node in fading_in:
		tween.tween_property(node, "modulate:a", 1.0, transition_seconds)
	for node in fading_out:
		tween.tween_property(node, "modulate:a", 0.0, transition_seconds)
	await _finish(c, tween)

	then_background.material = null
	for node in fading_in + fading_out:
		node.modulate.a = 1.0


## An era's effects (everything in its layer but the background) plus its era-tagged nodes.
func _crossfading(room: Room, layer: Node, group: StringName) -> Array[CanvasItem]:
	var nodes: Array[CanvasItem] = []
	for child in layer.get_children():
		if child is CanvasItem and child.name != &"Background":
			nodes.append(child)
	for node in room.era_nodes():
		if node.is_in_group(group):
			nodes.append(node)
	return nodes


func _flash(room: Room, origin: Vector2) -> void:
	_flare.position = room.get_global_transform_with_canvas() * origin
	_flare.scale = Vector2.ONE * 4.0
	var peak := 0.35 if reduce_flashing else 0.9
	var tween := create_tween().set_parallel(true)
	tween.tween_property(_flare, "scale", Vector2.ONE * 60.0, 1.1).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(_flare, "modulate:a", peak, 0.25)
	tween.chain().tween_property(_flare, "modulate:a", 0.0, 0.85)


## A slow push towards the anchor while the past shows; none with Reduce camera
## motion.
func _start_drift(room: Room, origin: Vector2) -> Camera2D:
	if Settings.reduce_camera_motion:
		return null
	var camera := Camera2D.new()
	camera.position = Vector2(960, 540)
	room.add_child(camera)
	camera.make_current()
	var toward := Vector2(960, 540).lerp(origin, 0.08)
	var tween := camera.create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(camera, "zoom", Vector2.ONE * 1.05, 10.0)
	tween.tween_property(camera, "position", toward, 10.0)
	camera.set_meta(&"drift", tween)
	return camera


func _end_drift(c: CutsceneSteps, camera: Camera2D) -> void:
	if camera == null or not is_instance_valid(camera):
		return
	(camera.get_meta(&"drift") as Tween).kill()
	var tween := camera.create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(camera, "zoom", Vector2.ONE, 1.0)
	tween.tween_property(camera, "position", Vector2(960, 540), 1.0)
	await _finish(c, tween)
	camera.queue_free()


static func _met(done: Variant) -> bool:
	if done is Callable:
		return bool((done as Callable).call())
	return bool(GameState.get_flag(StringName(str(done))))


## Waits for `tween`; once the scene is skipped, steps it straight to its end,
## so every property lands where the watched run leaves it.
func _finish(c: CutsceneSteps, tween: Tween) -> void:
	while tween.is_running() and not c.skipping:
		await get_tree().process_frame
	if tween.is_running():
		tween.custom_step(3600.0)
