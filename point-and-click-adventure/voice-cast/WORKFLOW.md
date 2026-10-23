# voice-cast workflow

Run every command from the repository root, so Bun loads `.env`.

## 0. Setup, once

1. The operator picks the ElevenLabs plan, sets a credit ceiling for the
   plan doing the voice work, and writes `ELEVENLABS_API_KEY=` into `.env`.
   Claude never writes, prints or commits `.env`.
2. Set the hero's speaker name and the plan tier in `tools/audio/config.json`:

   ```json
   { "player": "Hero", "tier": "creator" }
   ```

   `tier` sets how many requests run at once (free 2, starter 3, creator 5,
   pro 10, scale 15, business 15).
3. `audio-source/` holds masters and data. It carries a `.gdignore` so Godot
   never imports it. Put it in Git LFS before the first master lands.
4. Check the tools: `bun --version`, `ffmpeg -version` (post needs it).
5. Run the tool's tests. None touches the network; one runs ffmpeg.

   ```sh
   (cd tools/audio && bun test)
   ```

## 1. Write the lines

In `content/dialogue/**/*.dialogue` (Dialogue Manager 4):

```
~ altar_look

Hero: A cold altar. Someone scrubbed it recently. [ID:GB_ALTAR_LOOK_1]
Hero: Not recently enough. [#vo=whispers] [ID:GB_ALTAR_LOOK_2]
- What was here? [ID:GB_ALTAR_ASK]

=> END
```

- `Speaker: text` is a line; `- text` is a response, spoken by `player`;
  `% text` is one of several random lines.
- `[ID:…]` is static. `[#vo=…]` is the direction, placed after the text and
  before the ID. Tags split on commas: in `[#vo=tired, low]` only `tired` is
  the `vo` value, and `low` becomes a separate tag. Use one phrase without
  commas, or hyphens.
- The speaker must match an actor's `speaker_name` or `speaker_aliases`, so
  the subtitle sits over the right character.

Then:

```sh
tools/test.sh        # the lint fails on a missing or duplicate ID
```

## 2. Extract and diff

```sh
bun tools/audio/run.ts extract
# extract: N lines -> audio-source/voice/manifest.json
bun tools/audio/run.ts diff
# diff: A new, C changed, R removed, U unchanged
#   voice <ID>     (would generate)
#   orphan <ID>    (in the lock, no longer in the script)
```

The manifest entry per line: `id`, `speaker`, `text`, `direction`, `line`,
`file`, `textHash`. The size of the next batch is the `voice` rows.

## 3. Check the credits

```sh
bun tools/audio/run.ts report
# report: <tier>, <used> of <limit> credits used, resets <date>
```

Estimate the batch: about one credit per character of text on the current
TTS models (check the pricing page), plus about 50% for retakes. If the batch
would pass 80% of the ceiling, stop and report to the operator.

## 4. Cast, generate and review (designed, not proven)

Follow [references/designed-process.md](references/designed-process.md). Its
first run is a small measured batch: ten lines per character on the
candidate models, credits recorded, before any volume.

The output this skill needs from it: one master per line at
`audio-source/voice/masters/<ID>.wav`, and a lock entry per line in
`audio-source/voice/lock.json` with at least `textHash` (plus model, voice
id, settings, seed, request id and date).

## 5. Post

```sh
bun tools/audio/run.ts post            # only changed masters
bun tools/audio/run.ts post --force    # every master again
#   <ID>: 1.84 s at -3.2 dB
# post: M made, K unchanged -> assets/audio/voice/en
```

It writes:

| File | What |
|---|---|
| `assets/audio/voice/en/<ID>.wav` | 24 kHz mono 16-bit, trimmed, -18 LUFS, capped at -1 dBTP |
| `assets/audio/voice/en/envelopes.gd` | `RATE` (30) and `LINES`: ID to envelope bytes in base64 |
| `audio-source/voice/post.json` | per line: master hash, settings hash, seconds, measured loudness, gain, envelope |

A line whose master is gone leaves the table; the lint reports its WAV.

## 6. Import and test

```sh
tools/test.sh                          # imports the WAVs as QOA, GUT, lint
```

Then prove it in the builds (see [ship-check](../ship-check/WORKFLOW.md)):

```sh
tools/build/export.sh macos
build/macos/<Game>.app/Contents/MacOS/<Game> -- --qa=voice --qa-out=$PWD/docs/qa/<plan>/voice
tools/build/export.sh web && bun tools/build/serve.ts &
bun tools/build/browser-qa.ts voice
```

The `voice` scenario registers a 1 s tone with a rising envelope, clicks a
hotspot, and checks that the line held for about its audio (within 0.4 s),
that `Voice.level()` peaked above 0.7, and that the hero's `voice_level`
followed it. It prints the longest frame while the line played.

## Runtime reference

| Piece | Behaviour |
|---|---|
| `Voice.play(id)` | Loads `res://assets/audio/voice/en/<ID>.wav` when said, streams it on the Voice bus, reads its envelope; false when the line has no audio |
| `Voice.level()` | 0 to 1 at the playback position, from the envelope |
| `Voice.stalled()` | True when the position stood still 0.5 s over at least 6 frames |
| `Voice.register(id, stream, envelope)` | Makes a line sayable without files, for tests and previews |
| `Say` | Holds a voiced line until its audio ends; a click skips and stops it; a stalled line keeps text time; no audio means text time |
| Buses | Master with Voice, Music, Ambience, SFX, UI (`default_bus_layout.tres`, written by `addons/adv_tools/new_bus_layout.gd`) |

## Folder layout

```
audio-source/                 # LFS, .gdignore, never imported
  voices.json                 # speaker -> voice id, model, settings, design prompt (designed)
  casting/<speaker>/          # briefs and Voice Design previews (designed)
  cache/                      # request-hash cache
  voice/manifest.json         # extract
  voice/lock.json             # ID -> take, settings, request id, text hash
  voice/masters/<ID>.wav      # the truth
  voice/post.json             # post
assets/audio/voice/en/        # in the Godot project: <ID>.wav (imported as QOA), envelopes.gd
```
