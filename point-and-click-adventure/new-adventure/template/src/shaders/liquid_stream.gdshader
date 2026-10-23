shader_type canvas_item;
// One thread of the hero's ink (docs/technical-plan.md §6.4), drawn into the
// Tendrils CanvasGroup, whose liquid.gdshader turns the amounts into a film.
// This only lays down how much ink is where: a soft profile across the line
// whose width swells and narrows in bulges that flow toward the tip, like ink
// pulsing down a current, frayed into fibres at the edges. Drawn on a Line2D with texture_mode STRETCH, so UV.x
// runs from the root (0) to the tip (1) and UV.y across the line.

uniform sampler2D noise_tex : repeat_enable, filter_linear;
uniform float seed = 0.0;
// How fast the bulges travel toward the tip.
uniform float flow = 0.3;
// How much the bulges swell and pinch the stream (0 even width).
uniform float swell = 0.4;

void fragment() {
	float across = abs(UV.y - 0.5) * 2.0;
	float n = texture(noise_tex, vec2(UV.x * 0.9 - TIME * flow + seed, seed * 0.61)).r;
	float width = mix(1.0, 0.3 + 1.1 * n, swell * smoothstep(0.1, 0.5, UV.x));
	// Fine fibres fray the edges, more toward the tip.
	float fibre = texture(noise_tex, vec2(UV.x * 6.0 - TIME * flow * 2.0 + seed * 3.1, UV.y * 1.5 + seed)).r;
	width *= 1.0 + (fibre - 0.5) * (0.4 + 0.8 * UV.x);
	COLOR.a *= 1.0 - smoothstep(width * 0.2, width, across);
}
