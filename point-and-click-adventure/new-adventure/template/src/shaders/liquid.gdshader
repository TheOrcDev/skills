shader_type canvas_item;
render_mode unshaded;
// The hero's ink (docs/technical-plan.md §6.4), on the Tendrils CanvasGroup,
// after IMG-0003 v1: fine threads like ink let into water. The threads are
// drawn first into the group's buffer as amounts of ink; this softens that
// amount a little and maps it to a dark film, so thin threads stay translucent,
// threads that crowd together near his back thicken into one opaque sheet, and
// they never darken where they cross. A slow ripple moves the film, and its
// edges catch a faint cold light, so the ink still reads over dark stone.

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform sampler2D noise_tex : repeat_enable, filter_linear;
// The softening, in screen pixels.
uniform float radius = 2.5;
// Amounts of ink from transparent to fully opaque.
uniform float thin = 0.02;
uniform float thick = 0.75;
// The densest the film gets.
uniform float opacity = 0.85;
uniform vec4 ink : source_color = vec4(0.012, 0.012, 0.018, 1.0);
uniform vec4 edge_color : source_color = vec4(0.80, 0.84, 0.95, 1.0);
uniform float edge_light = 0.1;
// How far the ripple moves the film, in screen pixels.
uniform float ripple = 1.5;
// The group's position on screen, so the ripple travels with him.
uniform vec2 origin = vec2(0.0);

// The ink within `radius`: a disc of 13 taps.
float amount(vec2 uv, vec2 px) {
	vec2 r = radius * px;
	float a = texture(screen_texture, uv).a * 0.16;
	for (int i = 0; i < 6; i++) {
		float angle = float(i) * 1.0472;
		a += texture(screen_texture, uv + vec2(cos(angle), sin(angle)) * r * 0.5).a * 0.08;
		a += texture(screen_texture, uv + vec2(cos(angle + 0.5236), sin(angle + 0.5236)) * r).a * 0.06;
	}
	return a;
}

void fragment() {
	vec2 px = SCREEN_PIXEL_SIZE;
	vec2 at = (FRAGCOORD.xy - origin) * 0.004;
	vec2 warp = texture(noise_tex, at + vec2(TIME * 0.03, -TIME * 0.06)).rg - 0.5;
	float a = amount(SCREEN_UV + warp * ripple * px, px);
	float film = smoothstep(thin, thick, a);
	// Brightest where the film is half formed: the edges of threads and sheet.
	float rim = clamp(film * (1.0 - film) * 4.0, 0.0, 1.0);
	COLOR = vec4(mix(ink.rgb, edge_color.rgb, rim * edge_light), film * opacity * ink.a);
}
