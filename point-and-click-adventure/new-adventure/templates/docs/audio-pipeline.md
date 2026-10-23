# {{GAME_NAME}}: Audio Pipeline (ElevenLabs)

Status: draft, {{DATE}}. Inherited from the point-and-click-adventure kit. ElevenLabs'
prices, models and terms change: re-check them before spending money and
before release, and record the date checked here.

## 1. Scope

- **Voice:** every spoken line, for every character.
- **Sound effects:** one-shots (footsteps, doors, items, UI), ambience loops,
  and transition stingers.
- **Music:** each area's theme ({{twice, for the present and the past, if the
  game has two states}}), stingers, title and menu themes, credits.

## 2. Plan, licence and cost (decide before the voice spike)

The operator picks the plan and sets the credit ceiling. Facts as Past found
them on 2026-10-09, to be re-checked:

| Plan | Price / month | Credits / month | Notes |
|---|---|---|---|
| Free | $0 | 10k | Non-commercial; output must credit ElevenLabs |
| Starter | $6 | 30k | Commercial licence starts here |
| Creator | $22 | 121k | Professional voice cloning |
| Pro | $99 | 600k | 44.1 kHz PCM output |
| Scale | $299 | 1.8M | 3 seats |
| Business | $990 | 6M | 10 seats |

- Text-to-speech costs about one credit per character. Sound effects cost about
  40 credits per second.
- **Estimate:** {{N}} lines at ~70 characters each, plus about 50% for
  retakes. Past's script came to 1,069 lines and about 69 minutes.
- **Music** in a game is allowed on self-serve plans only under the indie
  limits, and a company needs Scale or Business. Whether the operator publishes
  as an individual or a company sets the tier.
- **Sound effects** may not ship as isolated files: ship audio only inside
  Godot's packed data.
- **Voices:** cast with our own Voice Design voices, which live in our
  account. Library voices can be withdrawn by their owners.
- **Disclosure:** stores such as Steam ask about AI content. The manifests and
  receipts are the record.

## 3. Tooling: `tools/audio` (Bun + TypeScript)

Run from the repository root, so Bun loads `.env`.

| Command | Status in the kit | Does |
|---|---|---|
| `extract` | built | Reads every spoken line in `content/dialogue` (its `[ID:…]`, speaker, text and `[#vo=…]` direction) into `audio-source/voice/manifest.json` |
| `diff` | built | Lists what generation would make: lines new or changed against `audio-source/voice/lock.json` |
| `report` | built | Credits used and the limit, from the subscription endpoint. Needs `ELEVENLABS_API_KEY`. |
| `post [--force]` | built | Masters in `audio-source/voice/masters/` into the game's lines (§4.5) and the envelope table. Only changed masters are posted again. Needs `ffmpeg`. |
| `cast`, `voice`, `sfx`, `music`, `check`, `lint` | to be built in the voice spike | Casting previews, generation within the plan's concurrency, transcription check, audio lint |

- **Cache rule:** each request is hashed (endpoint + model + voice + settings +
  text), and the same hash never calls the API twice unless `--force` is
  passed. HTTP 429 backs off and retries.
- **Limits:** `tools/audio/config.json` holds the player character's speaker
  name and the plan tier, which sets how many requests run at once.
- **Tests:** `cd tools/audio && bun test` (no test touches the network).

## 4. Voice

### 4.1 Casting

- Each character gets a written brief: age, timbre, accent, pace, attitude and
  three sample lines. Base directions live in `docs/story/cast.md`.
- Voice Design previews, two or three prompts per character. The operator
  picks; the voice is saved to our account with its id, model, settings and
  design prompt in `audio-source/voices.json`.
- **Model per character:** locked after a blind A/B on the same ten lines.
  Never mix models within one character.
- {{THE_HERO_BRIEF}}

### 4.2 Writing lines for TTS

- Delivery goes in bracket audio tags such as `[whispers]` and `[sighs]`.
  Emotion written as narration gets spoken aloud.
- Invented names use a pronunciation dictionary or IPA.
- Direction is a Dialogue Manager tag on the line (`[#vo=whispers]`), never
  spoken text. `extract` turns tags into audio tags or settings.
- **Text changes:** the lock file stores a hash of each line's text. When the
  text behind an ID changes, the line is marked for regeneration, and the ID
  stays the same.

### 4.3 Generation

- One request per line by default, with neighbouring lines as context where the
  model supports it. Fixed-order scenes with several speakers can use the
  dialogue endpoint and split by voice segments.
- Request a WAV/PCM master, or 44.1 kHz MP3 at 192 kbps. Never Opus: Godot
  cannot import it.
- Record per line: model, voice id, settings, seed, request id, date, text
  hash.
- **Masters are the truth.** Models drift and cannot be pinned. Each voice keeps
  a five-line re-test set, run before production resumes after a pause.

### 4.4 Review

Claude cannot hear, so review has two layers:

1. **Automated:** word match against the script, duration against text length,
   silence, clipping and loudness. Flagged lines are regenerated with the
   reason recorded.
2. **Operator listening:** a local review page per batch. Key story lines
   always get a listen.

### 4.5 Post-processing (`post`)

1. Trim silence: keep 80 ms before the first speech and 200 ms after the last,
   and fade the cuts.
2. Normalise loudness with one gain per line: voice −18 LUFS, music −23 LUFS,
   ambience −28 LUFS, never past −1 dBTP.
3. **Voice:** 24 kHz mono 16-bit WAV, `assets/audio/voice/en/<ID>.wav`. Godot
   imports it as QOA (about 77 kbps) and decodes it cheaply in every build. The
   WAV never ships.
4. **Envelope:** 30 loudness values per second (RMS from −45 dBFS to −12 dBFS,
   as bytes), all in one table, `assets/audio/voice/en/envelopes.gd`. It drives
   a mouthless character's eyes and the NPCs' talk bends.
5. `audio-source/voice/post.json` records each master's hash, the settings'
   hash, the loudness, the gain and the envelope, so only changes are posted
   again.

## 5. Sound effects

- One sheet per area: id, prompt, duration (0.5–30 s), loop flag, variants.
- One-shots such as footsteps get 4–6 variants, picked at random.
- Ambience is a 20–30 s loop with random one-shots on top.

## 6. Music

- Composition plans with tempo and key in the style text. {{For two-state
  games: the second arrangement reuses the composition plan with other styles,
  or is conditioned on a slice of the first theme.}}
- Loops: inpainting, or `post` crossfades the tail into the head.

## 7. Mix and runtime

- **Buses:** Master → Voice, Music, Ambience, SFX, UI, each with a Settings
  slider.
- **Ducking** under voice is a volume tween in code, not a bus effect.
- Any filtered or reverberant variant is rendered offline, so both builds sound
  the same.
- **The browser build:** voice and music use `playback_type = Stream`; short
  effects stay on Sample and are decoded during loading; pitch variety comes
  from pre-rendered variants (`technical-plan.md` §7).
- A line holds for its audio, and never for audio that stalls for 0.5 s.

## 8. Folder layout

```
audio-source/          # masters and data: LFS, never imported by Godot (.gdignore)
  voices.json          # speaker → voice id, model, settings, design prompt
  voice/manifest.json  # from `extract` (keyed by Dialogue Manager ID)
  voice/lock.json      # ID → take, settings, request id, text hash
  voice/masters/<id>.wav (+ .json metadata)
  voice/post.json      # from `post`
  casting/<speaker>/   # previews and briefs
  sfx/*.yaml, sfx/masters/…
  music/*.yaml, music/masters/…
```

## 9. Lip sync, only if a character shows a mouth

Rhubarb Lip Sync, the Montreal Forced Aligner, or a Godot baked-lipsync
plugin. Choose one when the need appears; a mouthless hero needs none.

## 10. Risks

| Risk | Mitigation |
|---|---|
| Model drift | Archive the masters, lock the model per character, run the re-test set |
| Terms change | Re-read the music and SFX terms before release; get written confirmation where unclear |
| Claude cannot listen | The automated check plus operator listening sessions |
| Thousands of lines hit concurrency limits | Queue with backoff, batch overnight |
