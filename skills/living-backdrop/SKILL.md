---
name: living-backdrop
description: Turn one still image into a living web backdrop - depth parallax that follows the pointer, a subject that breathes, and ambient wind, cloud drift, light and dust, in a single WebGL shader with a static poster fallback. Use when the user wants to animate a hero image, make a photo or AI artwork feel alive or 3D, add depth or parallax to a background, mentions a 2.5D or "living" image, or invokes /living-backdrop. Ships the asset pipeline (mask, inpaint, depth, upscale, pack) and a three.js component.
---

# Living Backdrop

One still image in. A hero that breathes out: the subject slides against the background with the pointer, swells and lifts on a breath cycle, grass moves, clouds creep, dust hangs in the light. One fullscreen quad, one shader, three textures. No video, no 3D model.

Four rules, each learned by shipping it:

1. **Two layers, not one depth map.** A single depth-displaced image smears at the subject's edge the moment it moves. Cut the subject out, paint it out of the background, and move them separately. Each layer still gets its own depth.
2. **Look at the mask, the plate and the depth map before writing any code.** Every later step inherits their quality. `build.sh` writes one `review.png` for exactly this.
3. **A poster renders first, and the canvas earns its place over it.** Server-rendered still, same framing to the pixel, all motion easing in from rest. Reduced motion, no WebGL, failed texture: the poster is the whole experience.
4. **You cannot judge motion from a backgrounded tab.** Automation tabs never fire `requestAnimationFrame`. Step frames by hand to check the shader, and say plainly that the live loop still needs human eyes. See [Verify](#verify).

## Fit check

Works when the image has a **clear foreground subject against a distant background** - a hand, a figure, a creature, a product - ideally one that leaves the frame at an edge (that edge becomes the breathing pivot).

Push back when: the subject fills over ~75% of the frame (nothing to slide against), it is a flat graphic or UI screenshot (no depth to find), or the user wants limbs to actually articulate (that is image-to-video, not this).

## 1. Build the assets

```bash
scripts/build.sh path/to/image.jpg public/images/hero /tmp/backdrop-work
```

Needs `uv`, ImageMagick, `avifenc`, `cwebp`. Models (~600 MB) download on first run. Takes a few minutes on a laptop. It prints the image **aspect**, a **suggested focus**, and output sizes - keep all three.

| Output | What it is |
|---|---|
| `scene-2560.avif`, `scene-1440.avif` | The untouched image (upscaled 2x when under 2400px). The subject layer is cut from this with the mask. |
| `bg-2560.avif`, `bg-1440.avif` | Same image with the subject inpainted away. |
| `maps.webp` | Lossless data map: **R** subject depth, **G** background depth, **B** subject mask. |
| `poster.jpg` | The still that renders first and stays under reduced motion. |

Then **open `review.png`** (source, mask / plate, background depth) and check:

- **Mask** - whole subject, including anything it holds. Wrong? Re-run with `MASK_MODEL=isnet-general-use` or `birefnet-general`.
- **Plate** - the middle of the hole will be mush. That is fine: parallax only ever reveals a ring a few dozen pixels wide around the silhouette. Judge the ring. If the ring is bad, ask the user for one generative-fill pass over the subject and re-run with `PLATE=path/to/plate.png`.
- **Depth** - near is bright. Subject clearly brighter than what is behind it, sky near black.

Commit the scripts' inputs or a README beside the assets so they can be regenerated. Report the real byte total to the user - do not quote a budget you did not measure.

## 2. Drop in the component

Copy [`templates/LivingBackdrop.tsx`](templates/LivingBackdrop.tsx). It needs `three` and nothing else. `createLivingBackdrop({ canvas }, options)` is framework-free; the React wrapper is at the bottom of the file. Match the host repo's lint and naming before committing.

Per-image values you must set - never ship the template defaults:

| Prop | How to pick it |
|---|---|
| `aspect` | Printed by `build.sh`. |
| `position` | Same meaning as CSS `object-position`, 0-1. Anchor on the subject so narrow viewports keep it. Share the value with the poster. |
| `pivot` | Where the subject **leaves the frame** (a wrist at the top edge, a torso at the bottom), from the top-left, 0-1. Breathing rotates and scales around it, so the far end of the subject moves most and the frame edge barely moves. |
| `focus` | Printed by `build.sh`. The depth that stays still; nearer slides one way, farther the other. |
| `glowOrigin` | The light source in the image. `glow={0}` if there is none. |

Ambient effects are masked by depth and position **inside the fragment shader**, tuned for a landscape: wind hits near depth in the lower frame, cloud warp hits far depth in the upper frame. For any other image, edit those two `smoothstep` masks or zero the prop. An effect that moves the wrong region is worse than no effect.

## 3. Integrate

**Poster first.** Render the poster in server HTML as the LCP image, with the canvas absolutely positioned over it. The canvas uses the same cover-fit maths as `object-fit: cover` + `object-position`, and the same `zoom` overscan, so apply both to the poster:

```tsx
<div className="relative overflow-hidden">
  <Image alt="" fill sizes="100vw" src="/images/hero/poster.jpg"
    loading="eager" fetchPriority="high" className="object-cover"
    style={{ objectPosition: `${x * 100}% ${y * 100}%`, transform: `scale(${zoom})` }} />
  <HeroBackdrop className="absolute inset-0" />
  {/* scrims go here, after the canvas */}
</div>
```

- **Lazy-load the canvas** in a small client wrapper (`next/dynamic` with `ssr: false`, or the framework's equivalent) so three.js stays off the critical path.
- **Shared constants live in a plain module.** A server component cannot read values exported from a `"use client"` file. Put `position` and `zoom` in their own file and import it from both sides.
- **Read the framework's current image docs first.** In Next 16 `priority` is deprecated; use `loading="eager"` + `fetchPriority="high"` or `preload`.
- **The wrapper needs a position and a size from the caller.** The canvas fills it. Do not let the component set its own `position`, it will override the caller's `absolute` and collapse to zero height.

**Legibility and theme.** Decide whether the artwork is dark or light, then pin everything on it to that theme's tokens in *both* site themes (a `dark` class on the wrapper with shadcn-style tokens). Put a gradient scrim behind the copy. Fade the artwork's bottom edge into the **pinned** token, not the page background - fading dark art into a light page reads as white fog.

**Mobile.** Do not full-bleed a landscape image in a portrait viewport: the subject either crops badly or buries the copy. Stack instead: copy on top, artwork as a `flex-1` block with a `min-height` underneath, a top fade joining them. The 1440px textures are picked automatically below `smallBelow`.

## 4. Tune

Start from the defaults and change one thing at a time. Motion this size is felt, not seen; if a visitor would describe it as "moving", halve it.

| Prop | Default | Too much looks like |
|---|---|---|
| `parallax` | 0.016 | Subject skating; smeared plate showing at the silhouette |
| `breath` / `breathPeriod` | 1 / 4.6s | Pumping, a balloon. Large subjects want 0.6-0.8 |
| `wind` | 1 | Jelly. The whole ground wobbling as a sheet |
| `clouds` | 1 | Heat haze |
| `glow` | 1 | A flickering bulb |
| `dust` | 36 | Snow |

The breath curve is quick in, slow out, short rest. Do not replace it with a sine; a sine reads as a machine.

## Verify

1. **Confirm the dev server is this project** before trusting a screenshot. Another app may already own the usual port; start your own on a spare one and stop it after.
2. **First dev load of the poster is slow** (the image optimiser is cold). A blank hero after a few seconds is not yet a bug; reload once.
3. **Step frames manually.** In a backgrounded tab `document.hidden` is true and rAF never fires, so the canvas stays paused at opacity 0 by design. Temporarily expose `frame`, `pointerTarget` and `uniforms` on `window`, then from the console: set the pointer, call `frame(0.1)` ~40 times to pass the intro, force the canvas opacity to 1, screenshot. Do it at **both pointer extremes** and zoom into the silhouette: no halo, no tearing, no smear. **Delete the hook before committing** and grep to prove it.
4. **Check narrow width in a same-origin iframe** if the window will not resize. Check both themes; restore any `localStorage` theme you set.
5. Run the repo's lint, typecheck, tests and production build.
6. **Report what you did not see.** Live loop, real frame rate, the poster-to-canvas fade and Lighthouse all need a foreground tab. Say so in the PR rather than implying it was checked.

More failure modes and their fixes: [references/pitfalls.md](references/pitfalls.md).
