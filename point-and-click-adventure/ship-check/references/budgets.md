# Budgets

Past's budgets, measured in its plans 002 to 010. A new game starts from
these and records any change as a decision.

| Metric | Desktop | Browser |
|---|---|---|
| Frame rate at 1080p | 60 fps (frame p95 under 16.7 ms) on the target Mac and a 2020-era integrated GPU | 60 fps in Chrome on the target Mac |
| Video memory per room | 400 MiB or less, with both eras, the hero and the room's NPCs loaded | Same |
| Room load | 1 s or less (background thread) | 2 s or less (no threads) |
| Download | No hard cap; aim for 4 GB or less | Pack of 150 MB or less for a demo, plus about 10 MB of engine (gzip) |
| Peak memory | | 1 GiB or less of the 2 GiB wasm cap |
| Hero frames | 128 MiB or less of video memory | Same |
| Voice | QOA mono 24 kHz, about 77 kbps | Same |

## Reference numbers

- A full-screen 1920×1080 RGBA8 layer is 7.9 MiB of video memory; a 4096²
  texture is 64 MiB (85 MiB with mipmaps). Textures stay at 4096 px per side
  or less.
- Past's 52 rooms measured 102 to 144 MiB each, loads of 38 to 258 ms and
  frame p95 of 8.3 to 16.7 ms, after the hero was repacked as trimmed grey +
  alpha painted frames (26.5 MiB of texture data for the hero).
- Before that, the rendered hero's untrimmed RGBA frames would have been about
  200 MiB; trimmed alpha masks measured 21.4 MiB for nine animations.
- The web engine `.wasm` is 39.5 MB raw, about 10 MB gzipped, 6.9 MB with
  Brotli.
- Voice comes out about 6 MB per 10 minutes as QOA.
- itch.io caps a browser game at 200 MB per file, 500 MB in total and 1,000
  files. Vercel caps an upload at 100 MB on Hobby and 1 GB on Pro.
- A web build that ships the whole game makes every play download the whole
  pack. Past's grew from 52.6 MB to about 259 MB when it did.

## Where budgets are enforced

| Budget | Check |
|---|---|
| Room video memory, load, frame p95 | `--qa=rooms`, per room |
| Whole-route frame times and memory | `--qa=perf` |
| Web pack contents | `export.sh web` (excluded parts) and `pck_list.py --sizes` |
| Hero frames | the pack step's report and `--qa=hero_anims` |
| Image spend | `tools/images` ledger (see art-requests) |
| Voice credits | `bun tools/audio/run.ts report` (see voice-cast) |
