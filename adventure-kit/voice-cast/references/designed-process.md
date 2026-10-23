# Casting, generation and review: the designed process

**Status: designed, not proven.** This is the process from Past's audio
pipeline design (`docs/audio-pipeline.md` §3 to §4) and plan 003 slices 2, 3,
4, 6. Past built and tested the parts around it (`extract`, `diff`,
`report`, `post`, the request-hash cache, the client with concurrency and
backoff, and the runtime), but the casting, `voice` and `check` steps have
not run on real lines: plan 003 slice 2 waits on the ElevenLabs plan and the
credit ceiling. Treat every number here as a starting guess.

**STOP before volume.** Run one small measured batch first: the casting
rounds, then ten lines per character on each candidate model. Record credits
per line and per minute of voice, the failure rate of the word match, and
first-line latency in the browser. Report to the operator with a tier
recommendation. Stay under the operator's credit ceiling throughout, and stop
at 80% of it.

The commands below (`ids`, `cast`, `voice`, `check`, `lint`, `sfx`,
`music`) are the designed command set. They do not exist in the template
yet. Building each one is part of the first voice plan.

## Commands (designed)

| Command | Does |
|---|---|
| `ids` | Gives every line that lacks one a static `[ID:…]`. IDs never change once given. |
| `cast` | Runs Voice Design previews from a casting brief, builds a local listening page with blind labels, and saves the operator's pick to `audio-source/voices.json` with voice id, model, settings, design prompt and date |
| `voice` | Generates the new and changed lines (manifest minus lock) within the tier's concurrency. Writes master WAVs with metadata and updates the lock. |
| `check` | Transcribes each new line and compares it with the script: added, dropped or garbled words, plus duration against text length, leading and trailing silence, clipping and loudness |
| `lint` | Every manifest line has audio and an envelope, nothing is orphaned, durations make sense |
| `sfx`, `music` | Generate from sheets (`audio-source/sfx/*.yaml`, `audio-source/music/*.yaml`): prompt, duration, loop flag, seed |

## 1. Casting

1. **A written brief per character:** age, timbre, accent, pace, attitude,
   and three sample lines. Keep it in `audio-source/casting/<speaker>/brief.md`.
   Example shape for a hero:

   > A man in his late thirties. A low, soft baritone, close to the
   > microphone, slightly breathy. Calm, wry and understated, with dry humour
   > over unease. Neutral accent. Slow, with small pauses while he decides
   > what he thinks.

2. **Voice Design** gives three previews per prompt. Run two or three prompts
   per character. The operator picks one from a listening page with blind
   labels, and the voice is saved to the operator's account (not the Voice
   Library, whose voices can be withdrawn).
3. **Three rounds with no voice that works is a STOP.** Offer the
   alternative: an actor and professional voice cloning, which needs the
   actor's consent and verification.
4. Every NPC voice is distinct. A character with two names gets one voice
   mapped from both.

## 2. Model A/B

Ten lines per character covering neutral, a wry joke, a whisper, fear,
sorrow, a long sentence and an invented name. Generate each on every
candidate model, with tags or settings to suit the model. The operator picks
a model per character from blind labels. Record whether the model accepts
request stitching (`previous_text`, `next_text`). Do not assume the newest
model wins: designed voices can be less performative on it, and it may drop
style and speed controls.

## 3. Writing lines for TTS

- Delivery goes in bracket audio tags where the model supports them
  (`[whispers]`, `[sighs]`, `[laughs]`). `extract` turns `[#vo=…]` into those
  tags, or into settings on models without tags.
- Invented names use a pronunciation dictionary (up to three per request) or
  IPA where the model accepts it.
- Keep lines short enough to subtitle; split long speeches into several IDs.

## 4. Generation

- **Default:** one request per line, with neighbouring lines as stitching
  context where the model supports it.
- **Fixed-order scenes** with several speakers (cutscenes, visions) can use
  text-to-dialogue with timestamps and split the result per line by its voice
  segments. Compare it with per-line generation on one six-line scene and let
  the operator pick the default.
- **Format:** WAV/PCM masters, or 44.1 kHz MP3 at 192 kbps. Never Opus.
- **Record per line** in the lock: model, voice id, settings, seed, request
  id, date, text hash.
- **Cache:** hash of endpoint, model, voice, settings and text. The same hash
  never calls the API twice without `--force`.
- Generate in batches, ideally overnight for thousands of lines; 429s back
  off.

## 5. Review

1. **Automated (`check`)**: word match plus duration, silence, clipping and
   loudness. Regenerate flagged lines with the setting or text adjusted, and
   record the reason in the lock.
2. **The operator listens** on a local review page grouped by scene, marks
   retakes, and always hears the key story lines.
3. More than 5% of a batch failing the word match is a STOP.

## 6. Sound effects and music (designed)

- One sheet per area. One-shots get 4 to 6 variants (the game picks at
  random; browser Sample playback can ignore pitch, so variety comes from
  variants). Ambience is a 20 to 30 s loop with random one-shots on top.
- Music per area in two arrangements when the game has two eras: the second
  either from the same composition plan with different styles, or conditioned
  on a slice of the first so the melody carries over.
- Loudness starting targets: music -23 LUFS, ambience -28 LUFS.
- Check the licence: music in a game has indie revenue limits, and sound
  effects may not ship as isolated files (only inside the Godot pack).

## 7. Report at the end of the first batch

- Credits per slice, per line, per minute of voice, per area.
- The recommended tier for production.
- Word-match failure rate per model.
- First-line latency and any crackle in the browser build.
- Open licence questions for the provider.
