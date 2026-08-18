---
name: intro-video
description: Build Remotion intro, reel, and brand-film videos with remocn and ASR-timed captions. Use when making an intro, reel, Shorts thumbnail, product demo film, or when the user mentions caption timing, remocn video, or invokes /intro-video. Caption times must come from ASR — never estimate.
---

# Intro Video

Build Remotion intros, reels, and brand films with remocn. Load the remocn skill for components. This skill owns captions, audio, intros, and render.

Three rules, each learned by shipping the wrong video:

1. **Caption timing comes from ASR. Never estimate from character counts or energy-based pause detection.** Estimating ran 1.1–1.9s late on a ~20s reel. That is a wrong video.
2. **Trim the silence off both ends of the VO before ASR.** See [Audio](#audio).
3. **Overlays live in the empty top-left, not across the frame,** unless the user asks otherwise. See [Overlays](#overlays).

## Inputs

Ask for both before any caption work:

- **Script** — spelling. ASR mishears proper nouns ("GROG", "MIND CRAFT").
- **Voice audio** (or a video that already has the VO).

Script gives spelling. ASR gives timing. Map script words onto ASR timestamps; keep the times.

## Audio

**Trim the dead air off both ends before anything else.** Raw VO arrives with
silence at the head and tail. Ship it untrimmed and the video opens on a still
frame with no voice and ends hanging on nothing.

Order matters: **trim first, then ASR.** ASR timestamps are relative to the file
you feed it. Trim afterwards and every caption is offset by the length of the
head silence.

Measure the real boundaries — do not guess a fixed number:

```bash
ffmpeg -i voice.wav -af silencedetect=noise=-40dB:d=0.15 -f null - 2>&1 \
  | grep silence_
```

Read the first `silence_end` (voice starts) and the last `silence_start`
(voice ends), then cut to those with a small margin so consonants survive:

```bash
ffmpeg -i voice.wav -ss <start-0.05> -to <end+0.10> -c:a pcm_s16le voice-trim.wav
```

Confirm with `ffprobe -show_entries format=duration` before moving on. Then run
ASR on `voice-trim.wav`, and use that same file in the composition — the
timings only line up against the file they were measured from.

- `-40dB` suits a clean close-mic recording. Noisy room, raise toward `-30dB`.
- Leave ~0.05s ahead of the first word and ~0.10s after the last. A hard zero cut clips plosives and sounds truncated.
- Normalise to −16 LUFS **after** trimming.
- ~0.2s crossfade at clip joins. Build the whole track in **one** ffmpeg filtergraph so frame counts match exactly.

## ASR

```bash
python3 scripts/asr.py voice-trim.wav --fps 30 --out captions.json
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
- **Logos:** real assets only — npm icon packs or the product's own GitHub repo. Never redraw.

## Overlays

**Animations, logo lockups, code cards, stat callouts and every other overlay
go in the empty space in the top-left. Never across the whole screen** — unless
the user explicitly asks for full-screen.

A full-bleed animation covers the speaker and fights the captions. The top-left
is empty on nearly every talking-head frame, so that is where an overlay reads
without hiding anything.

Look at an actual frame first and put the overlay in the empty corner you see
there. Where the subject genuinely sits left, mirror the box to the top-right.
Starting points:

| | Vertical 1080×1920 | Landscape 1920×1080 |
|---|---|---|
| Box origin | x 60, y 200 | x 80, y 80 |
| Box size | ~560 × 560 | ~680 × 420 |
| Max scale | ~50% of width | ~35% of width |

- Keep the overlay clear of the caption band at the bottom and, on vertical, of the right-hand action rail.
- Animate **in place** — scale/fade/slide within the box. Do not let a transition sweep across the full frame on the way in.
- One overlay at a time. Two competing corners is worse than none.
- Full-screen is legitimate for a deliberate cutaway or end card. That is a different beat, not an overlay — cut to it, do not lay it over the speaker.

## Render

- Pin `typescript@5`. TS7 drops `ts.sys` and breaks Remotion's bundler.
- `@/` needs a webpack alias in `remotion.config.ts`.
- If Chrome Headless Shell cannot download, extract Chromium from `@sparticuz/chromium` (brotli).
- Render **150–225 frame chunks**, concat, then mux audio. Full renders blow tool timeouts.
- Concurrency 1 on a single core.
- If `remocn.dev` 403s, pull components from the remocn GitHub repo `registry-artifacts/` instead of `shadcn add`. npm, PyPI, and GitHub release assets work.
- Frame format **JPEG, quality 95**. PNG at 4K is ~30MB/frame — a 200-frame chunk needs ~6GB of temp space and fails silently when the disk runs out. Check `df -h /` and clear `out/` first.
- **A chunk that overruns leaves a truncated file with no error.** `ffprobe` the frame count after every chunk before concatenating.

### 4K

Render the 1920×1080 composition with `--scale=2`. It stays 1920×1080
logically but rasterizes at 2× device pixels, so captions, lockups and
vignettes come out natively sharp. Do **not** build a separate 4K composition.

```bash
npx remotion render src/index.ts <Comp> out/kN.mp4 \
  --codec=h264 --crf=17 --muted --scale=2 --frames=A-B
```

Concat the chunks, then mux the audio.

- Re-cut every source asset at native 4K first.
- ~74 frames per chunk over talking-head footage. Drop to ~40 over cutaways that are themselves 4K video — compositing 4K over a decoding 4K clip is much slower.
- 1080p plus an ffmpeg lanczos upscale takes ~4 min against ~1 hour for true 4K. Offer it, but confirm before switching.

## Cover art

Safe areas differ per platform and the wrong guess buries the type. See
`references/cover-art.md`.
