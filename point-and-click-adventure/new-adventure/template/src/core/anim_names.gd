class_name AnimNames
extends RefCounted
## Picks the animation to play for a base name and a facing, following the
## `<anim>_<dir>` convention in docs/technical-plan.md §5.3. Left-facing
## directions fall back to their right-facing mirror, diagonals fall back to
## their horizontal then vertical neighbour, and the bare name comes last.

enum Dir { R, L, U, D, UR, UL, DR, DL }

const SUFFIX := {
	Dir.R: "r", Dir.L: "l", Dir.U: "u", Dir.D: "d",
	Dir.UR: "ur", Dir.UL: "ul", Dir.DR: "dr", Dir.DL: "dl",
}

## Candidates per facing, in order. A pair is [direction, flip_horizontally].
const FALLBACKS := {
	Dir.R: [[Dir.R, false]],
	Dir.L: [[Dir.L, false], [Dir.R, true]],
	Dir.U: [[Dir.U, false]],
	Dir.D: [[Dir.D, false]],
	Dir.UR: [[Dir.UR, false], [Dir.R, false], [Dir.U, false]],
	Dir.UL: [[Dir.UL, false], [Dir.UR, true], [Dir.L, false], [Dir.R, true], [Dir.U, false]],
	Dir.DR: [[Dir.DR, false], [Dir.R, false], [Dir.D, false]],
	Dir.DL: [[Dir.DL, false], [Dir.DR, true], [Dir.L, false], [Dir.R, true], [Dir.D, false]],
}


## The facing for a movement or look vector (screen space, +y is down).
## With `diagonals` off, the dominant axis wins.
static func dir_from_vector(v: Vector2, diagonals := false) -> Dir:
	if v.is_zero_approx():
		return Dir.D
	if diagonals:
		var octant := wrapi(roundi(v.angle() / (PI / 4.0)), 0, 8)
		return [Dir.R, Dir.DR, Dir.D, Dir.DL, Dir.L, Dir.UL, Dir.U, Dir.UR][octant]
	if absf(v.x) >= absf(v.y):
		return Dir.R if v.x > 0.0 else Dir.L
	return Dir.D if v.y > 0.0 else Dir.U


static func is_left(dir: Dir) -> bool:
	return dir == Dir.L or dir == Dir.UL or dir == Dir.DL


## Returns {"name": StringName, "flip": bool} for the best available animation,
## or an empty Dictionary if none fits. `has` is a Callable(StringName) -> bool.
static func resolve(base: StringName, dir: Dir, has: Callable) -> Dictionary:
	for candidate: Array in FALLBACKS[dir]:
		var anim_name := StringName("%s_%s" % [base, SUFFIX[candidate[0]]])
		if has.call(anim_name):
			return {"name": anim_name, "flip": candidate[1]}
	if has.call(base):
		return {"name": base, "flip": is_left(dir)}
	return {}
