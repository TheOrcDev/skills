---
name: voice-cast
description: Voices every spoken line of a point-and-click adventure with ElevenLabs and wires it to the subtitles. Extracts lines with static Dialogue Manager IDs and voice direction into a manifest, diffs them against a lock so unchanged lines never cost credits, posts masters to -18 LUFS 24 kHz mono WAV that Godot imports as QOA, and writes the loudness envelopes that drive a mouthless hero's eyes. Covers casting briefs, writing lines for TTS, the credit budget, and the runtime rules (a line holds for its audio, stalled audio falls back to text time, the browser needs a click). Use when the user wants to cast voices, generate or regenerate voice lines, add voice direction, post audio masters, fix lines that hang or play silent in the browser, size an ElevenLabs budget, or runs tools/audio extract, diff, report or post.
---

# voice-cast

Every line in the game is voiced. The script is the source of truth: a line
lives in a Dialogue Manager file with a static `[ID:…]`, and that ID names
its audio file, its manifest entry, its lock entry and its translation key.
Nothing is generated twice for the same text.

> **Proven in Past:** `extract`, `diff`, `report`, `post`, the envelope
> table and the runtime (Voice autoload, Say holding lines, stall fallback,
> browser click). **Not proven yet:** casting, generation (`voice`) and review
> (`check`). Past's plan 003 slice 2 waits on the ElevenLabs plan and credit
> ceiling. Those steps are written in
> [references/designed-process.md](references/designed-process.md) as the
> designed process, not a measured one. Run them on a small first batch and
> measure before any volume.

Read [RULES.md](RULES.md) before generating anything. Commands are in
[WORKFLOW.md](WORKFLOW.md).

## The loop

```
script ([ID:], [#vo=])  ->  extract  ->  manifest  ->  diff vs lock  ->  voice (new + changed only)
                                                                              |
   game line + envelope  <-  post  <-  masters  <-  check + operator listen  <-+
```

1. **Lines first.** Every spoken line has a static `[ID:…]` and, where it
   matters, direction as a tag: `[#vo=whispers]`. Direction never goes into
   the spoken text. `tools/test.sh`'s lint fails on a missing or duplicate ID.
2. **Extract.** `bun tools/audio/run.ts extract` reads `content/dialogue/**`
   into `audio-source/voice/manifest.json`: ID, speaker, text, direction,
   `file:line` and a text hash. Responses (`- text`) are spoken by the hero,
   named in `tools/audio/config.json` as `player`.
3. **Diff.** `bun tools/audio/run.ts diff` lists new, changed and orphaned
   lines against `audio-source/voice/lock.json`. Only those cost credits.
4. **Cast and generate** (designed, not proven): one Voice Design voice per
   character, one model per character, one request per line, cached by hash.
5. **Review** (designed): word match against the script, then the operator
   listens. Claude cannot hear.
6. **Post.** `bun tools/audio/run.ts post` trims each master (80 ms lead,
   200 ms tail), sets one gain to -18 LUFS capped at -1 dBTP, writes a 24 kHz
   mono WAV to `assets/audio/voice/en/<ID>.wav`, and writes the 30-a-second
   envelope table `assets/audio/voice/en/envelopes.gd`. Only changed masters
   are posted again.
7. **Import and play.** `tools/test.sh` (or the editor) imports the WAVs as
   QOA. `Voice.play(id)` streams the line on the Voice bus; `Say` holds the
   subtitle for it; the hero's body eases toward `Voice.level()`.
8. **Prove it** in both builds with the `voice` QA scenario
   (see [ship-check](../ship-check/SKILL.md)).

## Quick start

```sh
bun tools/audio/run.ts extract          # manifest from content/dialogue
bun tools/audio/run.ts diff             # what would cost credits
bun tools/audio/run.ts report           # credits used of the limit (needs ELEVENLABS_API_KEY)
# masters land in audio-source/voice/masters/<ID>.wav (generation: designed-process.md)
bun tools/audio/run.ts post             # game lines + envelopes.gd
tools/test.sh                           # imports as QOA, runs GUT and the lint
```

## Per-batch checklist

1. Every new line has an `[ID:…]`, a speaker that matches an actor's
   `speaker_name` or one of its `speaker_aliases`, and `[#vo=…]` on turning
   points.
2. `extract` runs clean (a repeated ID is an error) and `diff` shows only the
   lines you meant to change.
3. `report` before and after the batch, and spend stays under 80% of the
   operator's credit ceiling.
4. Masters are kept in `audio-source/voice/masters/` and never overwritten
   without a reason recorded in the lock.
5. `post` reports each line's seconds and gain; no line hits the -1 dBTP cap
   by surprise.
6. `tools/test.sh` passes, and `--qa=voice` passes in the exported desktop
   app and in Chrome.

## Do not

- Do not put emotion in the spoken text. It is read aloud. Use tags.
- Do not change an ID to regenerate a line. Change the text; the hash marks it.
- Do not use Voice Library voices for the cast. Owners can withdraw them.
- Do not mix models within one character.
- Do not request Opus. Godot cannot import it.
- Do not ship WAVs or loose audio files. The export carries QOA inside the pack.
- Do not analyse audio at runtime. Envelopes are computed offline.
- Do not print or commit `ELEVENLABS_API_KEY`. It lives in `.env`.

Next: [ship-check](../ship-check/SKILL.md) proves the voiced lines in both
builds.
