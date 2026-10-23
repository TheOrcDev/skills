shader_type canvas_item;
// Soft edges for an image laid over another: an inner ring of a pull-back
// reveal (docs/technical-plan.md §6.3) melting into the ring outside it, and a
// close-up pushing in over its room. Matches the feather of
// tools/art adv_art.rings: a smoothstep over `feather` of the shorter side.

uniform float feather = 0.08;

void fragment() {
	vec2 size = 1.0 / TEXTURE_PIXEL_SIZE;
	vec2 px = UV * size;
	float edge = min(min(px.x, size.x - px.x), min(px.y, size.y - px.y));
	COLOR.a *= smoothstep(0.0, feather * min(size.x, size.y), edge);
}
