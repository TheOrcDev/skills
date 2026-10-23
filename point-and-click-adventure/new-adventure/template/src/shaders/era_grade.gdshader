// One full-screen grade over every room (docs/technical-plan.md §7): a cold
// lift/gain and stronger vignette for the present, a warm one for the past,
// and film grain, which also hides 8-bit banding in the fog.
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform sampler2D noise_tex : repeat_enable, filter_nearest;
uniform vec2 grain_offset = vec2(0.0);
uniform float mix_then : hint_range(0.0, 1.0) = 0.0;
uniform vec3 lift_now = vec3(0.0, 0.008, 0.022);
uniform vec3 gain_now = vec3(0.95, 0.97, 1.02);
uniform vec3 lift_then = vec3(0.02, 0.01, 0.0);
uniform vec3 gain_then = vec3(1.04, 1.0, 0.94);
uniform float vignette_now = 0.5;
uniform float vignette_then = 0.28;
uniform float grain = 0.04;
uniform float aspect = 1.7778;

void fragment() {
	vec3 c = texture(screen_tex, SCREEN_UV).rgb;
	vec3 lift = mix(lift_now, lift_then, mix_then);
	vec3 gain = mix(gain_now, gain_then, mix_then);
	c = lift + c * (gain - lift);
	vec2 p = (UV - 0.5) * vec2(aspect, 1.0);
	float vignette = smoothstep(0.5, 1.2, length(p)) * mix(vignette_now, vignette_then, mix_then);
	c *= 1.0 - vignette;
	float n = texture(noise_tex, SCREEN_UV * vec2(aspect, 1.0) * 6.0 + grain_offset).r - 0.5;
	c += n * grain;
	COLOR = vec4(clamp(c, 0.0, 1.0), 1.0);
}
