# voice-cast rules

Each rule has its reason and, where Past measured it, the evidence. Rules
marked *designed* come from Past's audio pipeline design and have not yet run
on real generation.

## Lines and IDs

1. **Every spoken line has a static `[ID:…]` that never changes.** The ID
   names the audio file, the manifest entry, the lock entry and the
   translation key. Past's `extract` found exactly one manifest line per
   `[ID:` in the content (73 at first, 1,069 at the end of the story).
2. **IDs are unique across the whole game.** `extract` throws on a repeated
   ID, and the content lint fails on one. Past once reused cue names across
   chapters and broke the hints file.
3. **Voice direction is a Dialogue Manager tag, `[#vo=whispers]`.** Checked
   against Dialogue Manager 4.1.0; read in the game with
   `get_tag_value("vo")`. Emotion written as narration gets spoken aloud.
4. **Turning-point lines always carry direction.** Every other line inherits
   its character's base direction from the cast doc. Past directed its 39
   turning-point lines and left the rest to the base direction.
5. **Text changes keep the ID.** The manifest stores a hash of speaker, text
   and direction. A changed hash marks the line for regeneration under the
   same ID; `diff` lists it as changed.
6. **Responses are spoken by the hero.** A `- text` line has no speaker, so
   `extract` uses the `player` name in `tools/audio/config.json`.
7. **A renamed character keeps one voice.** When a character speaks under
   two names (a role, then a returned name), both names map to the same
   voice. In the game, `Actor.speaker_aliases` lets either name find the
   actor. Past had six NPCs like this.

## Cost and budget

8. **Unchanged lines never cost credits.** `diff` is the bill. Each request
   is hashed (endpoint, model, voice, settings, text) and the same hash never
   calls the API twice without `--force` (*designed* for `voice`; the cache
   is built and tested).
9. **The operator sets a credit ceiling per plan. Stop at 80% and report.**
   Run `report` before and after every batch.
10. **Measure a small first batch before volume** (*designed*). Credits per
    line, per minute of voice and per area, then the tier for production.
    Past's script came to 1,069 lines, about 69 minutes of voice.
11. **Concurrency follows the plan tier:** 2, 3, 5, 10, 15, 15 for Free
    through Business. HTTP 429 backs off and honours `Retry-After`. Past's
    tests caught a missing `Retry-After` header being read as "retry at once".
12. **The licence shapes the pipeline.** Commercial use starts at Starter.
    Music in a game has indie limits. Sound effects may not ship as isolated
    files. Re-read the terms before spending and before release.

## Casting and generation (designed)

13. **Cast with your own Voice Design voices, never library voices.** Library
    voices can be withdrawn by their owners, and then no new lines can be
    made.
14. **Lock one model per character** after a blind A/B on the same ten lines.
    Never mix models within a character.
15. **Masters are the truth.** Seeds are best effort and models drift without
    version pinning. Keep the masters, and keep a five-line re-test set per
    voice to run before production resumes after a pause.
16. **Request WAV/PCM masters** (24 kHz on Creator, 44.1 kHz on Pro) or
    44.1 kHz MP3 at 192 kbps. Never Opus.
17. **Claude cannot hear.** Every batch gets an automated word match against
    the script plus duration, silence, clipping and loudness checks, and the
    operator listens to key story lines. More than 5% failing the word match
    is a STOP: fix model, settings or text before generating more.

## Post

18. **One gain per line to -18 LUFS, never past -1 dBTP.** A line whose peaks
    reach the ceiling first comes out a little quieter: a 4.6 s test line in
    Past with peaks at -1.9 dBTP came out at -19 LUFS.
19. **Trim to 80 ms before the first speech and 200 ms after the last,** padded
    with silence where the master has less, with 5 ms fades so a cut through
    breath never clicks.
20. **Voice ships as 24 kHz mono 16-bit WAV, imported as QOA.** About 77 kbps,
    decoded by Godot in every build, cheap to decode on the browser's main
    thread. No Vorbis encoder was needed. The export carries the QOA, never
    the WAV.
21. **Envelopes are computed offline.** 30 values a second, each window's RMS
    mapped from -45 dBFS (0) to -12 dBFS (1), as bytes, all in one table
    (`envelopes.gd`: `RATE` and `LINES`, ID to base64). One file, not
    thousands. Every platform gets the same result.
22. **`post` only redoes what changed.** `audio-source/voice/post.json` keeps
    each master's hash and the settings' hash. A changed setting remakes
    every line.

## Runtime

23. **A voiced line holds until its audio ends. A click skips it and stops
    the audio.**
24. **Stalled audio falls back to text time.** A playing line whose position
    stands still for 0.5 s, over at least 6 frames, has stalled. Its audio is
    stopped so it cannot start late, and the line keeps the time it would
    have had as text. Past's first browser run waited forever: Chrome plays
    no sound before a click, so the audio never started.
25. **The browser needs a click before sound.** The loading shell ends with a
    click that starts the engine, so the first line is heard. QA runs pass
    `--autoplay-policy=no-user-gesture-required` instead.
26. **In the browser, voice and music stream.** `playback_type = Stream`.
    Sample mode decodes a whole clip on the main thread the first time it
    plays (a freeze on long clips) and never frees decoded audio (about
    350 to 384 KB per second played). Short effects stay on Sample, decoded
    during loading.
27. **The browser mixes on the main thread.** A frame longer than the audio
    buffer holds the sound back. Past measured a 1 s line held 1.09 to 1.13 s
    warm and up to 2.01 s on a cold load under heavy machine load.
28. **Nothing depends on bus effects.** Filtered or reverberant variants are
    rendered offline; ducking under voice is a volume tween.
29. **A line without audio uses text timing** and the lint reports it. The
    hero's body flickers at a syllable rate instead of following an envelope.
30. **A mouthless hero gets no lip sync.** The voice envelope drives the eyes
    (glow, flare). Lip sync only for a character that shows a mouth.
