---
name: intro-video
description: Build Remotion intro, reel, and brand-film videos with remocn and ASR-timed captions. Use when making an intro, reel, Shorts thumbnail, product demo film, or when the user mentions caption timing, remocn video, or invokes /intro-video. Caption times must come from ASR — never estimate.
---

# Intro Video

Build Remotion intros, reels, and brand films with remocn. Load the remocn skill for components. This skill owns captions, audio, intros, and render.

**Caption timing comes from ASR. Never estimate from character counts or energy-based pause detection.** Estimating ran 1.1–1.9s late on a ~20s reel. That is a wrong video.

## Inputs

Ask for both before any caption work:

- **Script** — spelling. ASR mishears proper nouns ("GROG", "MIND CRAFT").
- **Voice audio** (or a video that already has the VO).

Script gives spelling. ASR gives timing. Map script words onto ASR timestamps; keep the times.

## ASR

```bash
python3 scripts/asr.py voice.wav --fps 30 --out captions.json
```

Uses `sherpa-onnx` from PyPI and a zipformer model from **GitHub release assets** (allowlisted). Whisper weights on Azure/HuggingFace are often blocked — do not start there. The script downloads the model on first run.

Drive every caption `from` / `durationInFrames` from that JSON. 2–4 words on screen. Keyword in amber.

```tsx
<Sequence from={startFrame} durationInFrames={endFrame - startFrame}>
  <Caption text={phrase} keyword={keyword} />
</Sequence>
```

## Craft

| | Vertical 1080×1920 | Landscape 1920×1080 |
|---|---|---|
| Font | Inter 800, 70px | Inter 800, 58px |
| Fill | white | white |
| Stroke | 13px black, `paint-order: stroke fill` | same |
| Keyword | `#FFD93D` | same |
| Max width | 790 (clears the Reels button column) | — |
| Over footage | plate behind the text | same |

- **Opening clip:** vignette + Ken Burns `1.0 → 1.09`, origin `50% 42%`.
- **Audio:** −16 LUFS. Trim ~0.12s head / ~0.16s tail. ~0.2s at clip joins. Build the track in **one** ffmpeg filtergraph so frame counts match exactly.
- **Logos:** real assets only — npm icon packs or the product's own GitHub repo. Never redraw.

## Render

- Pin `typescript@5`. TS7 drops `ts.sys` and breaks Remotion's bundler.
- `@/` needs a webpack alias in `remotion.config.ts`.
- If Chrome Headless Shell cannot download, extract Chromium from `@sparticuz/chromium` (brotli).
- Render **150–225 frame chunks**, concat, then mux audio. Full renders blow tool timeouts.
- Concurrency 1 on a single core.
- If `remocn.dev` 403s, pull components from the remocn GitHub repo `registry-artifacts/` instead of `shadcn add`. npm, PyPI, and GitHub release assets work.
