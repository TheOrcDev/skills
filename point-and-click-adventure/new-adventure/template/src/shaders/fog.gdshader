// Drifting fog for the living-painting effect (docs/art-pipeline.md §5E).
// Two octaves of scrolling noise inside a vertical band, optionally thinned
// where the room's depth map says the scene is near (the walkable floor).
shader_type canvas_item;

uniform sampler2D noise_tex : repeat_enable, filter_linear;
uniform sampler2D depth_tex : filter_linear, hint_default_black;
uniform bool use_depth = false;
uniform vec4 fog_color : source_color = vec4(0.82, 0.84, 0.86, 1.0);
uniform float density = 0.35;
uniform vec2 velocity = vec2(0.008, 0.0);
uniform vec2 noise_scale = vec2(1.6, 0.9);
uniform float band_top = 0.45;
uniform float band_bottom = 0.95;
uniform float band_softness = 0.15;
uniform float near_cutoff = 0.45;

void fragment() {
	vec2 uv = UV;
	float n1 = texture(noise_tex, uv * noise_scale + TIME * velocity).r;
	float n2 = texture(noise_tex, uv * noise_scale * 1.9 - TIME * velocity * 1.7 + vec2(0.37, 0.11)).r;
	float n = n1 * 0.65 + n2 * 0.35;
	float band = smoothstep(band_top, band_top + band_softness, uv.y)
		* (1.0 - smoothstep(band_bottom - band_softness, band_bottom, uv.y));
	float far = 1.0;
	if (use_depth) {
		float d = texture(depth_tex, uv).r;
		far = 1.0 - smoothstep(near_cutoff * 0.6, near_cutoff, d);
	}
	float a = clamp(density * band * far * smoothstep(0.25, 0.85, n), 0.0, 1.0);
	COLOR = vec4(fog_color.rgb, a * fog_color.a);
}
