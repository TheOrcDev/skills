// Soft light shafts fanning from a window, with a slow flicker
// (docs/art-pipeline.md §5E). Drawn additively over the background.
shader_type canvas_item;
render_mode blend_add;

uniform sampler2D noise_tex : repeat_enable, filter_linear;
uniform vec2 origin = vec2(0.76, 0.24);      // UV of the light source
uniform float aim = 200.0;                    // degrees, 180 = straight down, 225 = down-left
uniform float spread = 34.0;                  // degrees, total width of the fan
uniform float beams = 6.0;
uniform float intensity = 0.16;
uniform float reach = 0.9;                    // in UV units of the rect height
uniform vec4 color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float flicker = 0.35;
uniform float aspect = 1.7778;

void fragment() {
	vec2 p = UV - origin;
	p.x *= aspect;
	float r = length(p);
	float ang = degrees(atan(p.x, -p.y));     // 0 = up, 180 = down
	float rel = mod(ang - aim + 540.0, 360.0) - 180.0;
	float inside = 1.0 - smoothstep(spread * 0.4, spread * 0.5, abs(rel));
	// Beams: a soft comb across the fan, each beam breathing on its own.
	float k = (rel / spread + 0.5) * beams;
	float comb = pow(max(0.0, sin(k * 3.14159265)), 6.0);
	float lane = floor(k);
	float breathe = texture(noise_tex, vec2(lane * 0.173, TIME * 0.025)).r;
	float shimmer = 1.0 - flicker + flicker * breathe;
	float along = smoothstep(0.02, 0.12, r) * (1.0 - smoothstep(reach * 0.55, reach, r));
	float dust = 0.75 + 0.25 * texture(noise_tex, UV * vec2(3.0, 6.0) + vec2(0.0, -TIME * 0.01)).r;
	float a = intensity * inside * comb * shimmer * along * dust;
	COLOR = vec4(color.rgb * a, a);
}
