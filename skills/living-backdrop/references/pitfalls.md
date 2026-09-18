# Pitfalls

Each of these cost time on the first build. Symptom first, then cause and fix.

## Assets

**Subject edge shears or wobbles under parallax.**
Depth estimators blur across silhouettes, so the subject's edge pixels carry half-background depth and move at a different rate from its interior. `pack.py` fixes this by trusting only the eroded interior of the mask and extending that depth outward. If you hand-make a depth map, do the same.

**Layers slide at unrelated speeds.**
The two depth maps were normalised separately. Normalise both against one shared min/max (`pack.py` does).

**Fine texture swims (grass, leaves, fur).**
High-frequency depth detail displaces neighbouring pixels by different amounts. Blur the background depth; you want the shape of the terrain, not the blades.

**Coloured fringe or dark halo around the subject.**
A cut-out PNG with alpha gets its hidden RGB discarded by lossy encoders, and linear filtering then blends the edge toward black. Do not ship a cut-out. Ship the untouched image plus a mask channel: edge pixels then blend toward the *original* background colour, which is what was there anyway.

**Depth or mask channels look contaminated by each other.**
The data map was saved lossy. Chroma subsampling mixes R, G and B. `maps.webp` must be lossless (or PNG).

**Inpainted plate looks terrible.**
Judge only the ring around the silhouette; the interior is never revealed. A dilated hole keeps subject-coloured fringe out of the fill. If the ring itself is bad, one manual generative fill beats fighting the model.

**Soft hero on retina.**
Sources under ~2400px get a Real-ESRGAN 2x. It sharpens, it does not invent detail; a 1024px source will still look soft full-bleed. Tell the user.

## Shader and component

**Image renders upside down.**
The template loads `ImageBitmap`s, which three.js uploads unflipped, and works in top-left image coordinates throughout so that `position`, `pivot` and `glowOrigin` match CSS. If you swap in `TextureLoader`, set `flipY = false` or every coordinate inverts.

**Stretched pixels at the frame edge.**
Parallax sampled past the image. The `zoom` overscan (1.04) exists for this. Raise it if you raise `parallax`, and mirror it on the poster.

**Canvas is there but has zero height.**
An inline `position: relative` on the wrapper beat the caller's `absolute inset-0` class. The wrapper takes its position and size from the caller.

**Visible jump when the canvas fades in.**
Either the poster framing does not match (different `object-position` or missing `scale`), or motion started at full strength. Every uniform is multiplied by an intro ramp so frame zero is the still image.

**Colours shift between poster and canvas.**
Textures are sampled and written without colour-space conversion on purpose (`colorSpaceConversion: "none"`, no `colorspace_fragment`), so the canvas matches the `<img>` exactly. Adding sRGB decoding to one side breaks the match.

**Breathing moves the frame edge.**
The pivot is not on the edge where the subject exits. Move it onto (or just beyond) that edge.

## Integration

**`priority` warning or no preload in Next 16.**
Deprecated. `loading="eager"` with `fetchPriority="high"`, or `preload`.

**Build error importing constants into a server component.**
They were exported from a `"use client"` module. Move them to a plain `.ts` file.

**White fog at the bottom of the hero in light theme.**
The bottom fade used the page background token. Fade into the pinned (dark) token inside the pinned wrapper and let the section end on a clean edge.

**Copy collides with the artwork on phones.**
An absolutely positioned artwork block with a fixed `svh` height ignores how tall the copy is. Put the artwork in normal flow under the copy with `flex-1` and a `min-height`.

**Moving a heavy canvas elsewhere on the page.**
If the hero previously held another WebGL piece (a model viewer), lazy-load it where it lands, or three.js stays in the first bundle and the split bought nothing.

## Performance

One quad and ~40 points cost almost nothing on the GPU. The real costs are texture bytes and decode:

- Cap pixel ratio at 1.5. Nobody can see 2x on a slowly moving photo.
- `ImageBitmapLoader` decodes off the main thread; a 2560px AVIF on `TextureLoader` janks the first frame.
- Serve the 1440px pair to small screens. No mipmaps; the image is never minified much.
- Pause on `IntersectionObserver` exit and on `document.hidden`. Close bitmaps and dispose on unmount.
- Do not request device-orientation for parallax on phones. The iOS permission prompt is not worth it; the idle drift covers touch.
