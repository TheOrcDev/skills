class_name SpriteBody
extends ActorBody
## An ActorBody drawn from a rendered CharacterSprites set. The origin is at
## the feet. Facing left mirrors the whole node, so children placed at anchors
## (eyes, held items) mirror with it.

## Emitted when the sprite shows a new frame, after the frame has changed.
signal frame_shown
## Emitted when a frame with an event shows, for example "step" on a heel strike.
signal animation_event(anim: StringName, event: StringName)

@export var sprites: CharacterSprites

var sprite: AnimatedSprite2D
var flipped := false
## The item in hand, or null (see hold()).
var held: Sprite2D

var _stepped_frame := -1
var _last_event_frame := Vector2i(-1, -1)  # (animation's hash, frame), so a frame fires once


func _ready() -> void:
	sprite = AnimatedSprite2D.new()
	sprite.name = "Sprite"
	sprite.centered = false
	sprite.sprite_frames = sprites.frames
	sprite.animation_finished.connect(func() -> void: animation_finished.emit(sprite.animation))
	sprite.frame_changed.connect(frame_shown.emit)
	sprite.frame_changed.connect(_fire_events)
	add_child(sprite)
	frame_shown.connect(_place_held)


## Whether `world` falls on the frame showing now: its trimmed box, not the
## whole render frame around it.
func contains_point(world: Vector2) -> bool:
	var texture := sprite.sprite_frames.get_frame_texture(sprite.animation, sprite.frame)
	if texture == null:
		return false
	var rect := Rect2(sprite.offset, texture.get_size())
	var atlas := texture as AtlasTexture
	if atlas:
		rect = Rect2(sprite.offset + atlas.margin.position, atlas.region.size)
	return rect.has_point(sprite.to_local(world))


func has_animation(anim: StringName) -> bool:
	return sprites != null and sprites.frames.has_animation(anim)


func play_animation(anim: StringName, flip: bool) -> void:
	flipped = flip
	scale.x = absf(scale.x) * (-1.0 if flip else 1.0)
	if anim == sprite.animation and sprite.is_playing():
		return
	# Turning mid-walk keeps the stride where it was instead of restarting it.
	var keep_phase := sprite.is_playing() and _base(anim) == _base(sprite.animation)
	var phase := (sprite.frame + sprite.frame_progress) / maxf(1.0, sprite.sprite_frames.get_frame_count(sprite.animation))
	sprite.play(anim)
	sprite.offset = -sprites.anchor(anim, &"feet", 0)
	if keep_phase:
		var position_in := phase * sprite.sprite_frames.get_frame_count(anim)
		sprite.set_frame_and_progress(int(position_in), fmod(position_in, 1.0))
		_stepped_frame = sprite.frame
		_last_event_frame = Vector2i(hash(anim), sprite.frame)
	else:
		_stepped_frame = -1
		_fire_events()
	frame_shown.emit()


func ground_speed() -> float:
	return sprites.ground_speed.get(sprite.animation, 0.0)


func frame_rate() -> float:
	return sprite.sprite_frames.get_animation_speed(sprite.animation) * absf(sprite.speed_scale)


func consume_step() -> bool:
	if sprite.frame == _stepped_frame:
		return false
	_stepped_frame = sprite.frame
	return true


## Shows `texture` in `hand` (an anchor such as "hand_r"), following it frame
## by frame and mirroring with the body, until release(). `size` scales the
## texture; `offset` shifts it from the anchor, in this node's space.
func hold(texture: Texture2D, hand: StringName = &"hand_r", size := 1.0, offset := Vector2.ZERO) -> Sprite2D:
	release()
	held = Sprite2D.new()
	held.name = "Held"
	held.texture = texture
	held.scale = Vector2.ONE * size
	held.set_meta(&"hand", hand)
	held.set_meta(&"offset", offset)
	add_child(held)
	_place_held()
	return held


func release() -> void:
	if held:
		held.queue_free()
		held = null


## Where `anchor_name` is in the current frame, in this node's space.
func anchor(anchor_name: StringName) -> Vector2:
	return sprites.anchor(sprite.animation, anchor_name, sprite.frame) + sprite.offset


func eye_visible(eye: int) -> bool:
	return sprites.eye_visible(sprite.animation, sprite.frame, eye)


## The facing suffix of the current animation: "r", "u", "d" and so on.
func view() -> String:
	return String(sprite.animation).get_slice("_", String(sprite.animation).get_slice_count("_") - 1)


func _place_held() -> void:
	if held == null:
		return
	held.position = anchor(held.get_meta(&"hand")) + held.get_meta(&"offset")
	# A hand is in front of the body except from behind, where the body hides it.
	var in_front := view() != "u"
	move_child(held, sprite.get_index() + (1 if in_front else 0))


func _fire_events() -> void:
	var key := Vector2i(hash(sprite.animation), sprite.frame)
	if key == _last_event_frame:
		return
	_last_event_frame = key
	for event: StringName in sprites.events_at(sprite.animation, sprite.frame):
		animation_event.emit(sprite.animation, event)


func _base(anim: StringName) -> String:
	var text := String(anim)
	return text.substr(0, text.rfind("_"))
