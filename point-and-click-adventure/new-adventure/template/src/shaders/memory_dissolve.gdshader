// The flashback bloom (docs/technical-plan.md §6.2): the past's background is
// revealed from `origin` outwards along a noisy front with a warm glowing edge
// and a small ripple. progress 0 hides it, 1 shows all of it.
shader_type canvas_item;

uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform vec2 origin = vec2(0.12, 0.4);
uniform sampler2D noise_tex : repeat_enable, filter_linear;
uniform float edge_width = 0.09;
uniform float noise_amount = 0.22;
uniform float ripple = 0.006;
uniform float aspect = 1.7778;
uniform vec4 edge_color : source_color = vec4(1.0, 0.9, 0.62, 1.0);
uniform float edge_glow = 0.75;

void fragment() {
	vec2 d = UV - origin;
	d.x *= aspect;
	float dist = length(d);
	float n = texture(noise_tex, UV * vec2(3.0, 1.7)).r;
	float far_corner = length(vec2(max(origin.x, 1.0 - origin.x) * aspect, max(origin.y, 1.0 - origin.y)));
	float front = progress * (far_corner + edge_width + noise_amount);
	float v = dist + n * noise_amount;
	float reveal = 1.0 - smoothstep(front - edge_width, front, v);
	float edge = smoothstep(front - edge_width, front - edge_width * 0.5, v)
		* (1.0 - smoothstep(front - edge_width * 0.5, front, v));
	vec2 push = dist > 0.0001 ? normalize(d) / vec2(aspect, 1.0) : vec2(0.0);
	vec4 tex = texture(TEXTURE, UV + push * edge * ripple);
	vec3 col = mix(tex.rgb, edge_color.rgb, clamp(edge * edge_glow, 0.0, 1.0));
	COLOR = vec4(col, tex.a * max(reveal, edge * edge_glow));
}
