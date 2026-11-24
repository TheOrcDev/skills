# Short format video: editing workflow

House standard for cutting OrcDev vertical Shorts (Instagram Reels, TikTok, YouTube Shorts, X) in Remotion. After each batch, write down what worked, what was slow and what looked bad, then fold durable lessons back into this file.

The coordinator starts **one editor agent per video**. Editors only work inside that video's folder. They do not post, upload or send anything. The operator reviews and posts.

## Inputs

Each video has its own folder (`videorc/`, `grok-bot/`, `orcanva/`, …) with a `BRIEF.md`.

- `source/1.mp4`, `2.mp4`, … are the raw talking-head parts, 2160x3840 (9:16), recorded in Videorc. They play in numeric order and together are the whole video. They are typically symlinks into `~/Movies/Videorc/Recordings/`. Never modify, move or delete the originals.
- `transcript/N.txt` and `N.srt` are rough whisper.cpp transcripts. They contain mistakes (see spelling in [RULES.md](RULES.md)). Re-transcribe with word timestamps for captions.

**Check every source part for picture before planning the layout.** A tiny file compared with the other takes is a giveaway (black video, audio OK). One command finds it:

```bash
ffmpeg -i N.mp4 -vf blackdetect=d=0.1:pix_th=0.05 -an -f null -
```

A tighter check used on small files:

```bash
ffmpeg -i N.mp4 -vf "scale=270:480,blackdetect=d=0.03:pix_th=0.05" -an -f null -
```

This has shown up on the second-to-last-recorded short take in a batch. Workaround: make that part a full-screen visual voice-over. Do not plan a face-cam layout on a black take.

## Output

One finished vertical video per folder, saved to:

```
~/Movies/Short Format Videos/YYYY-MM-DD <Topic>.mp4
~/Movies/Short Format Videos/YYYY-MM-DD <Topic> cover.png
```

Never leave the only copy in `~/projects`. Editors write straight to that Movies folder.

- Video: 1080x1920, 30 fps, H.264 High yuv420p, AAC 48 kHz, loudness about -14 LUFS, faststart.
- Cover: 1080x1920 PNG, a frame with the same compact hook title as the open, usable as the Reel/TikTok/YouTube Short cover.
- `out/NOTES.md` lists every overlay used, every asset and where it came from.

Do not upload, post or send anything anywhere.

## Tooling

- Use Remotion (React) for the edit. Each video folder gets its own small Remotion project. Do not share `node_modules` across folders unless it just works.
- Render with Remotion's own headless shell (`npx remotion browser ensure`), not system Chrome (system Chrome produced mosaic/blank frames).
- ffmpeg and ffprobe are on the machine (on the house Mac, `/opt/homebrew/bin`). Bun and Node are installed.
- Remotion's bundler does not follow symlinks in `public/` (404 even with absolute links). Copy real files in: 1440x2560 CRF 12-14 proxies are sharp enough for 1080 output plus a 113% zoom, and they render faster than 4K. Originals stay untouched.
- Bundle once (`npx remotion bundle --out-dir work/bundle`) and render stills from that bundle (`renderStill`). Repeated `npx remotion still` per frame is slow. Contact sheets with ffmpeg `xstack` make review fast.

## Re-transcribe and silence cuts

Rough transcripts are not caption times. Word timestamps from a full take with leading or trailing silence drift a lot (`-ml 1` can spread a 2-6 s line across 0-8 s).

1. Extract 16 kHz mono wav: `ffmpeg -i N.mp4 -ar 16000 -ac 1 in.wav`.
2. Cut silences first, then transcribe the tightened audio. `silencedetect` settings that worked: noise around -38 to -48 dB, duration 0.1 to 0.15 s. Keep a little air so words do not clip (about 0.07 s before speech and 0.07 to 0.10 s after; merge gaps under 0.1 s). This matches the house rule of about 2-4 frames of air.
3. Transcribe the cut audio with whisper.cpp, for example:

```bash
whisper-cli -m ~/.cache/whisper-cpp/ggml-large-v3-turbo-q5_0.bin -f in.wav -ml 1 -oj
```

   If you use DTW (`-nfa -dtw large.v3.turbo -ojf`), flash attention must be off or `t_dtw` stays -1. `t_dtw` is roughly the word onset plus about 0.1 s, and it runs late on long sentence-final words. Check against an RMS envelope and hand-fix.
4. Anchor each spoken chunk to its silencedetect start and end. Only use whisper's relative word lengths inside a chunk. Re-transcribing the cut track is a cheap check that no word got clipped.

A working pattern is one EDL file (kept ranges in source frames plus word times). Build the voice track outside Remotion with ffmpeg `atrim` plus a short fade per piece (4 ms was used) plus `concat`, frame-aligned with the video segments, so captions and overlays keyed by word cannot drift when a cut moves.

## The style

### 1. Hook in the first second

Small, calm on-screen hook title from frame 0 to about the end of the first spoken sentence. Short (about 5-7 words), readable without sound. The spoken first line is also the hook, so the text can match it or sharpen it. This is not a giant ultra-bold blast, and it is not the same style as the 70-90 px Black captions. Standing numbers live in [RULES.md](RULES.md).

On a 1080x1920 frame:

- Font 56-68 px, hard cap 72 px. Medium or Semibold (500-600), never Black, ExtraBold or Ultra.
- Sentence case or short Title Case. Not a full-line ALL CAPS blast. One keyword may take the accent color.
- Max 2 lines (3 only with about 3-5 words on each). About 3-5 words per line.
- Max block width 864 px (80% of 1080). Side margins at least 108 px; prefer 120 px so the glyphs sit inside x 120-960. No full-width, no edge-to-edge.
- Top of the block (plate included) at y 320-380, bottom by y 560. Never above y 300: TikTok's For You tabs and Reels' header cover the top about 250 px; YouTube's vertical overlay keeps the top 288 px clear. Overlapping his forehead/hair is fine.
- Keep clear of the bottom about 350 px (TikTok / Reels / Shorts caption and music; published overlays reserve 660-672 px) and the right about 150-192 px (like/share rail; TikTok's rail is about 300 px from y 840 down).
- The same y 300 floor applies to every overlay (CTA, title pills, logos, chips). Nothing important above y 300. CTA pills at the end sit in this same upper safe band (y 320-560), not a full-width title bar.
- Contrast: 2-3 px dark stroke plus a soft shadow, or a small rounded plate (padding 16-24 px, about 45-65% black) fitted to the words. Not a full-width bar.
- Entrance: fade plus an 8-16 px rise, or fade plus scale 96% to 100%, 8-12 frames at 30 fps, ease-out. No slam, shake, bounce or overshoot spring.
- Hold through the first spoken sentence, typically 1.5-2.5 s, fully landed at least 1.2 s. Fade off 4-8 frames at the Beat 1 hard cut.

The face often fills the frame (head top about y 180 at 1080x1920), so a compact top-third title still sits over the hair. A split layout (visual on top) at frame 0 gives the hook a clean area. Instagram's profile grid crops covers to 3:4 (about y 240 to 1680), so keep the cover title in the same y 320-560 band.

Measure placement on the final file, not only in CSS. Drawing guide lines at y 300, y 560, x 120 and x 960 on extracted frames (`drawbox`) makes width and height violations obvious.

### 2. Tight pacing

Cut every silence, breath gap, false start and dead air between and inside parts. Join the parts seamlessly. Use subtle punch-in zooms (100% to about 108-115%) on talking-head stretches every few seconds so the frame never feels static. The final cut should feel fast but natural, not robotic. List pauses can be cut down to about 0.1 s and still sound natural.

### 3. Captions that work

Burned-in, word-by-word or 2-4 word chunks synced to word timestamps. Keep each chunk to one line. At 80 px Montserrat Black that is about 14-15 characters per 780 px; greedy split by length plus phrase-break markers in the EDL. Big (about 70-90 px on 1080 wide), heavy sans-serif, white with a thick dark stroke/shadow, the currently spoken word highlighted in an accent color (Videorc green or a bright yellow). These sizes are for the word-synced caption track only. Do not use them on the opening hook title (that stays 56-68 px Medium/Semibold, see section 1).

Caption y depends on layout:

- Full-head shots: lower-middle safe zone, roughly y 1150-1450 on 1920. Captions at about y 1310 sit just under the chin.
- Split layouts: captions at the seam (top-anchored around y 968-1060), never in the 1150-1450 zone (that covers the eyes).

Clear of the platform UI at the bottom (about 350 px) and the right-side buttons (about 150 px). Spell product names correctly. Never show whisper mistakes.

### 4. Show, do not just tell

Whenever he explains a thing (a feature, a product, a step), the screen must show it: real screenshots or screen recordings of the actual product/site, product logos, simple animated UI mockups, icons, checkmarks, counters. Layout options:

- Split: visual on the top about 55%, his face cam on the bottom about 45%.
- Full-screen visual with a small circular face cam bubble.
- Pop-in logo/icon over the talking head for quick name drops.

Return to the full talking head for emotional lines, the hook payoff and the CTA.

Get real visuals: capture the live website with Playwright (headless Chrome, 1080x1920 or desktop 1440 wide then framed), the GitHub repo page, official logos. Animate them (slide/scale in with springs, scroll a screenshot, highlight a region with a box or arrow). Landing-page assets in the product repo are often real studio output and can be reused. Do not record edits on someone's public design (that would change live content). Guests cannot create designs on hosted product apps, so do not plan a capture that needs a guest account.

Readable screenshots: a 1800 px wide app screenshot shrunk to 1000 px is unreadable on a phone. Cut it into one card per control and pop each in on its word. For GitHub, start the repo view at about 640 CSS px wide, then zoom to about 480 px around the target control. GitHub's Star button when logged out is an `<a>` whose text is like `Star560 (560)`, so `/^Star\b/` misses it. Match `/^Star(\d|\s|$)/` on `a` elements with y < 400.

x.com returns 403 to headless Chrome. Render a post through `https://platform.twitter.com/embed/Tweet.html?id=<id>`. For an avatar, use `unavatar.io/x/<handle>`.

### 5. Logos on name drops

Every time a brand is named, show its logo at that moment. Use official logos: brand press kits or Simple Icons (https://simpleicons.org, `simple-icons` npm) rendered as SVG. Videorc logo: from https://videorc.com or the local Videorc site repo. The Grok Bot logo is not in Simple Icons; take the mark's inline SVG from https://x.ai/bot.

### 6. Sound

His voice is the priority and must stay clean and loud. Sound effects (pings, pops, whooshes on movement/transitions) must be very quiet: about 20-30% of their original level (around -12 dB), clearly underneath his voice. Keep one `SFX_GAIN` constant (0.25, -12 dB, was the fix when v1 SFX were too loud). Optional quiet music bed only if original or synthesized; never use licensed tracks.

Check SFX with numbers, not only by ear:

- Render voice-only and SFX-only stems (a `stem` prop that mutes the other). Remotion rejects a CRF for wav, so make `Config.setCrf` conditional when `--codec=wav`.
- Compare peaks at the final loudnorm gain. Compare effect against voice only while he speaks: in the pauses at cuts an effect is alone and would fail a moment-by-moment check for no reason.
- An unmuted `OffthreadVideo` plus an `<Audio>` of the same file puts the voice in the mix twice (+6 dB). Measure the real voice gain (fit render = k * source), do not assume 1.
- When measuring short windows, trim the decoded WAV (`atrim`). `-ss` before `-i` on AAC is not sample-accurate.
- If a Short has no SFX (voice only), say so. Do not apply "SFX too loud" feedback to a video with no `<Audio>` effect layers.

### 7. Ending

End on his last line with the CTA visible (for example "Link in bio" / repo URL / site URL as text). No long outro, no end card longer than about 1 s. A clean loop back to the hook is a plus.

## Safe-zone layouts that worked

Use these as starting geometry, then measure on extracted frames.

- Talking head scaled to 0.86-0.9, anchored to the bottom, edges feathered (`mask-image`, 13% sides and 15% top) into a `#07090a` background. The recording background is near-black, so the seam does not show. Under 10% feather leaves a faint box edge.
- Split: face cam at 0.78 scale with the eyes around y 1255 under a 960 px panel, or visual panel 0 to 1000 with eyes around y 1380 (face scale at least 1 so the sides stay covered). Moving everything below y 300 costs the split about 200 px; wrap existing mockups in `translateY(170px) scale(0.85)` with `transform-origin: 540px 300px`, then grow the panel and push seam captions and face cam down about 50 px. Check connectors and titles again afterwards.
- Full-screen visuals: plan them for y 300 to 1200 from the start. y 1450 to 1570 was left empty on one pass; use it for a bigger visual or a second label.
- Hub-and-spoke: hub at y about 725 with radius about 330 so the top tile clears 300 and the bottom tiles clear captions at 1160.

## Remotion gotchas

- Never call hooks (`spring`, `useSpringAt`) after an early `return null`. `remotion still` will not catch it (each still is a fresh render); the full render fails with React error #310.
- `OffthreadVideo` that only shows mid-composition must sit inside a `<Sequence from=...>`, otherwise it plays from the composition's frame, not from the scene start.
- `<Still>` plus `OffthreadVideo trimBefore` rendered source frame 0, not the trimmed frame. For the cover, extract the frame with ffmpeg in prep and use `<Img>`.
- Do not touch other video folders. Do not commit to or push any repo except this video's Remotion project.

## Final ffmpeg pass

Remotion's AAC output was about 43 ms late (2 x 1024 samples = 2048 samples at 48 kHz) against the picture. Check it by cross-correlating the render's audio against the source (or against a pre-built voice wav), not by eye. Fix it in every final ffmpeg pass:

```
atrim=start_sample=2048,asetpts=PTS-STARTPTS,...,apad=whole_dur=D,atrim=end=D
```

with `D` from ffprobe. Read duration with `-of default=nw=1:nk=1`, not `csv=p=0` (csv adds a trailing comma). Do not use `apad` with `-shortest` alone: that produced a 66 s audio stream on a 25 s video.

After x264, min/max luma is useless (ringing around stroked text gives 0/255). Compare percentiles of the raw Y plane. `scale=in_range=full:out_range=tv,format=yuv420p` maps full-range Remotion output (0-255) to TV range.

## Before you call it finished

- Run ffprobe on the output.
- Check A/V sync with the 2048-sample cross-correlation, not by eye.
- Look at several extracted frames: hook frame, a caption frame, each visual overlay, the last frame. Draw y 300, y 560, x 120 and x 960 guides on the hook frame. The title block must sit inside that box, at 56-68 px, not filling it.
- Confirm the cover hook sits inside the Instagram 3:4 crop (about y 240 to 1680) and in the same y 320-560 band as the in-video title.
- Confirm SFX stems (or confirm there are no SFX).
- Confirm spelling of every on-screen product name.
- Write `out/NOTES.md`.
- Copy the mp4 and cover PNG to `~/Movies/Short Format Videos/` as `YYYY-MM-DD <Topic>.mp4` and `YYYY-MM-DD <Topic> cover.png`.
- Stop. Do not post.
