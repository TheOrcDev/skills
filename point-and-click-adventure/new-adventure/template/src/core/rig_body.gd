class_name RigBody
extends ActorBody
## A painted character deformed by a Skeleton2D (decision
## #49): one painting from the image tool, skinned to a few bones by
## addons/adv_tools/new_npc.gd, and animated by procedural motions instead of
## rendered frames. The NPCs use it.
##
## `motions` maps an animation name to its motion:
## - a loop: {"loop": true, "bones": {bone: [degrees, hertz, phase]},
##   "voice": {bone: degrees}}. Each bone sways by a sine; while the actor
##   speaks, "voice" bends bones by the line's loudness (Voice.level(), or a
##   lively stand-in for a line without audio);
## - a one-shot: {"loop": false, "length": seconds, "keys": {bone:
##   [[seconds, degrees], …]}}, eased between keys, ending with
##   animation_finished.
## Bones are named children of Skeleton; their rest pose is the painting's.

## Animation name → motion, as above.
@export var motions := {}
## Unscaled painting outline, for clicks, in this node's space.
@export var outline := PackedVector2Array()

var _skeleton: Skeleton2D
var _bones := {}
var _rest := {}
var _anim: StringName = &""
var _time := 0.0
var _speaking := false
var _voice := 0.0


func _ready() -> void:
	_skeleton = get_node_or_null("Rig/Skeleton") as Skeleton2D
	if _skeleton:
		for bone in _skeleton.find_children("*", "Bone2D", true, false):
			_bones[StringName(bone.name)] = bone
			_rest[StringName(bone.name)] = (bone as Bone2D).rest.get_rotation()


func has_animation(anim: StringName) -> bool:
	return motions.has(String(anim))


func contains_point(world: Vector2) -> bool:
	return outline.size() > 2 and Geometry2D.is_point_in_polygon(to_local(world), outline)


func play_animation(anim: StringName, flip: bool) -> void:
	scale.x = -absf(scale.x) if flip else absf(scale.x)
	if anim == _anim and _motion().get("loop", true):
		return
	_anim = anim
	_time = 0.0


func set_speaking(on: bool) -> void:
	_speaking = on


func _motion() -> Dictionary:
	return motions.get(String(_anim), {})


func _process(delta: float) -> void:
	_time += delta
	var motion := _motion()
	var target := 0.0
	if _speaking:
		# Found by path: the scaffolds compile this script without autoloads.
		var voice := get_node_or_null(^"/root/Voice")
		target = voice.level() if voice and voice.is_playing() else 0.35 + 0.35 * sin(_time * 9.0) * sin(_time * 3.7)
	_voice = lerpf(_voice, clampf(target, 0.0, 1.0), clampf(delta * 12.0, 0.0, 1.0))
	for bone_name: StringName in _bones:
		var degrees := 0.0
		if motion.get("loop", true):
			var sway: Array = motion.get("bones", {}).get(String(bone_name), [])
			if sway.size() == 3:
				degrees += float(sway[0]) * sin(TAU * float(sway[1]) * _time + float(sway[2]))
			degrees += float(motion.get("voice", {}).get(String(bone_name), 0.0)) * _voice
		else:
			degrees += _keyed(motion.get("keys", {}).get(String(bone_name), []), _time)
		(_bones[bone_name] as Bone2D).rotation = _rest[bone_name] + deg_to_rad(degrees)
	if not motion.get("loop", true) and _time >= float(motion.get("length", 0.0)):
		var finished := _anim
		_anim = &""
		animation_finished.emit(finished)


## The keyed angle at `time`, eased between keys.
static func _keyed(keys: Array, time: float) -> float:
	if keys.is_empty():
		return 0.0
	if time <= float(keys[0][0]):
		return float(keys[0][1])
	for i in range(1, keys.size()):
		if time <= float(keys[i][0]):
			var span := float(keys[i][0]) - float(keys[i - 1][0])
			var weight := ease((time - float(keys[i - 1][0])) / span, -2.0) if span > 0.0 else 1.0
			return lerpf(float(keys[i - 1][1]), float(keys[i][1]), weight)
	return float(keys[-1][1])
