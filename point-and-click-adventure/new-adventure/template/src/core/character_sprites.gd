class_name CharacterSprites
extends Resource
## A character's rendered sprite set (docs/technical-plan.md §6.4), built by
## addons/adv_tools/import_sprites.gd from the art tools' manifest: the frames,
## and for every frame where the eyes, shoulders, back, hands and feet are.

## One animation per `<anim>_<dir>`. Every frame is an AtlasTexture whose margin
## restores the trimmed region to the full render frame.
@export var frames: SpriteFrames
## The render frame in pixels; anchors are in this space.
@export var frame_size := Vector2i(400, 576)
## How tall the character stands in the frame at scale 1.
@export var character_px := 480
## True when frames keep the render's shading (grey + alpha, LA8); false for
## flat silhouettes (an alpha mask, L8).
@export var shaded := false
## True for Sol's painted frames: grey + alpha drawn as they are,
## not a render to darken.
@export var painted := false
## animation -> {anchor -> PackedVector2Array with one point per frame}.
@export var anchors := {}
## animation -> PackedByteArray with one entry per frame: bit 0 is set when the
## left eye faces the camera, bit 1 when the right eye does.
@export var eyes := {}
## animation -> pixels per second the feet cover at scale 1 (walks only).
@export var ground_speed := {}
## animation -> {frame -> Array of event names}: footsteps, the moment of a grab.
@export var events := {}


func anchor(anim: StringName, anchor_name: StringName, frame: int) -> Vector2:
	var points: PackedVector2Array = anchors[anim][anchor_name]
	return points[clampi(frame, 0, points.size() - 1)]


func eye_visible(anim: StringName, frame: int, eye: int) -> bool:
	var flags: PackedByteArray = eyes[anim]
	return (flags[clampi(frame, 0, flags.size() - 1)] >> eye) & 1 == 1


## The events on `frame` of `anim`, if any.
func events_at(anim: StringName, frame: int) -> Array:
	return events.get(anim, {}).get(frame, [])
