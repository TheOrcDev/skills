---
name: talking-head-intro
description: >-
  Overlay explainer visuals on a recorded talking-head hook or intro, about
  10-20 seconds, for a Long or a Short. Transcribe first, one visual per
  spoken line appearing when it is said, official brand assets, never a name
  before he says it, source resolution preserved. Use when editing a
  talking-head intro, adding intro overlays, or the user invokes
  /talking-head-intro.
---

# Talking Head Intro

Add clean explainer overlays to a recorded talking-head hook or intro, usually 10-20 seconds, in the source orientation. The picture and the voice stay the original take. Only a transparent overlay goes on top.

This is not [intro-video](../../skills/intro-video/SKILL.md), which builds Remotion brand films and reels from scratch with remocn and ASR captions. This is not [excalidraw-drawing](../excalidraw-drawing/SKILL.md), which draws a diagram onto an on-screen board. This is not a full Shorts cut: do not crop to 9:16, do not add the vertical hook band, and do not change the length with silence cuts.

## When to use

- A talking-head hook or intro for a Long or a Short, typically 10-20 seconds.
- He says "add intro overlays", "edit this intro", or invokes `/talking-head-intro`.
- The footage is already recorded, usually in Videorc. You are decorating the take, not rewriting or recutting it.

## Rules

- **Transcribe first.** Word onsets come from a transcript of this take. Do not start placing graphics from memory of the topic, or from a script that was not spoken.
- **One explainer visual per spoken line.** The visual must explain the line, not just name it. A logo plus a two-word label is usually too thin. A small diagram of who talks to whom, or an official mark for a platform word, is an explanation. A first pass that only dropped a logo and a short label was rejected as too minimal, and not really explaining.
- **Nothing appears before its cue.** Each group starts on, or one frame after, the onset of the word it explains. Sub-elements inside a group wait for the word that names them. A group may leave before the next one arrives. Groups never overlap.
- **Never reveal a name before it is said.** Only show a product or feature name in the moment he says it, and only the words he actually says in this clip. If he says "Vercel" and never says "Board", put the official Vercel logo only. "Vercel Board" must not appear as text or as a lockup. Check every on-screen word against this clip's transcript, not against the video's topic.
- **Official brand assets only.** Take logos from the official press kit (for Vercel: [vercel.com/geist/brands](https://vercel.com/geist/brands)). Never redraw, recolor, outline, rotate, stretch, or recreate a wordmark in type. For an open-source mention, use the official GitHub mark (white on dark), not a redrawn cat.
- **Stay in the negative space.** Keep every overlay off his face, hair, hands, mic and shirt mark. Measure keep-out zones on the actual frames of this take, including a raised hand mid-line, and shift a group up or down to clear it. Look at a contact sheet before you place anything.
- **Do not change the footage.** No zooms, cuts, crops, grade or speed change. Overlay only. Copy the audio untouched. Frame 0 is the raw video: no sting, no fade in. Keep the last second clean picture.
- **Match the source resolution.** If the recording is 3840x2160, the deliverable is 3840x2160. Do not ship a 1080p file from a 4K source. You may author the overlay in 1920x1080 units and render at 2x (`--scale=2`), the same way [excalidraw-drawing](../excalidraw-drawing/SKILL.md) does. Keep the source frame rate, frame count and length.
- **Do not put specific timings in the brief.** Describe the speech cue and the placement rule ("starts on the word Vercel", "sits in the empty left field, clear of a raised hand"). Re-measure word onsets for every new take. Do not copy timestamps from a previous video as hard rules.
- **Never post or upload.** Editors never publish.

## Map each line to a visual

Read the transcript and split it into the spoken lines. Design one group for each line, and build the group in the order he says it.

Examples from a Vercel hook. Reuse the mapping idea, not the specific graphics, unless those words are actually said:

| Spoken line | Visual that explains it |
|---|---|
| "Vercel just shipped" | Official Vercel logotype only. No product name he has not said. |
| "a new open source project" | Official GitHub mark, plus short labels such as "Open source" / "New project" |
| "how you talk to your AI agents" | You <-> agent chat: a "You" avatar, your message bubble, the agent, its reply, each appearing on the word that names it |
| "how your AI agents talk to each other" | Agent nodes with links that draw on, then small message bubbles travelling between them |

Other lines follow the same idea: a logo on a name drop, an official mark on a platform word, a small who-talks-to-whom diagram for a relationship. Do not invent quotes inside bubbles; use abstract text bars. Do not show pricing, "Experimental", or any other product he does not name in this clip.

One group on screen at a time. Lots of negative space. If a graphic does not explain the line, leave it out. Clean and tasteful, but dense enough that the line is pictured, not just labelled.

## Craft

Defaults that should travel from one intro to the next. Adjust placement to the framing of this take.

### Type

- One family: Geist Sans (variable). No second font.
- Main labels: Semibold 600 at 46 px in 1080p units. Secondary and diagram labels: Medium 500 at 28-30 px. Letter spacing -2%.
- Sentence case ("Open source", "New project", "You", "AI agent").
- One colour: near-white `#F2F2F2` for type, icons, bubbles and links. Hierarchy comes from size and opacity (secondary label about 72%, links about 45%, text bars inside bubbles about 60%), never from a second colour.
- No plates, strokes, shadows or glows on a dark set.

### Motion

- Enter: fade 0 to 100% plus scale 96% to 100%, 12 frames, ease-out cubic, each element from its own anchor.
- Leave: the group leaves as one, a 9-frame fade with a barely visible 100% to 98.5% settle, ease-in-out.
- Diagrams build in speech order inside the group. Links may draw on; a small looping message along a link is fine if it stays quiet.
- Exits sit in natural pauses and finish before the next line's first word.

### Placement

- On a take where he sits mid-frame and the left is empty black, left-anchor groups in that field (around x 150 in 1080p units, staying inside roughly x 150-560) and centre logo groups on a y that lines up with his face.
- This is a starting point, not a template to paste. Measure the leftmost bright pixels of his head and hands per line, then move the group so it never touches him, the mic or the shirt mark.
- Official logos at about 4-5% of frame height (marks up to about 7% square), with clear space at least the symbol height. If the logotype is on screen alone during a name drop, nothing else shares that beat.

### Sound

- Picture and voice stay the original take. Stream-copy the audio when you composite so it stays in sync.
- SFX are optional. If you use any, keep them at about 25% volume, well under his voice. No SFX is a valid choice.

## Workflow

Copy this checklist and tick it off:

```
- [ ] 1 Probe the video and measure keep-out zones
- [ ] 2 Transcribe and mark word onsets
- [ ] 3 Map each spoken line to an explaining visual
- [ ] 4 Place groups in the negative space of this take
- [ ] 5 Check stills over the real footage
- [ ] 6 Render the overlay at source resolution, composite, verify
- [ ] 7 Export a cover
- [ ] 8 Write NOTES.md and report. Do not post.
```

**1 Probe.** Run `ffprobe` for size, fps, duration and frame count. Make a contact sheet and look at frames across the take, including any raised hand. Record keep-out zones (face, hair, hands, mic, shirt mark, light rays you should not cover). Convert measurements to 1080p units if you author that way.

**2 Transcribe.** Get word-level timings for this take (windowed whisper, or whisper run on each speech island, checked against an amplitude envelope). Whole-file whisper times can drift when the take has silence at both ends. Write the spoken lines in order. A cue fires on the first word of the line it explains. Where an onset falls between frames, round up, never down. Re-measure for every new take.

**3 Map.** One group per line, as above. List every on-screen word and confirm it is said in this clip, from that word on.

**4 Place.** Build the overlay as a transparent Remotion layer. Official SVGs placed as the file, unaltered. Generic person, agent, bubble and link glyphs may be simple line icons in the same line weight, as long as they are not fake brand marks.

**5 Check.** Composite stills over the real frames, including the frame where his hand is highest and the first visible frame of each group. Nothing may touch him. No group may start before its word. No forbidden name on any frame.

**6 Render and composite.** Render only the overlay (transparent ProRes 4444 is fine). Composite in ffmpeg over the source, at the source width and height, with `-c:a copy`. Encode the finish as H.264 High `yuv420p`, AAC 48 kHz (copied), `faststart`. Confirm: same frame count and length as the source, audio cross-correlation at 0 ms, clean frames (no overlay) at a high PSNR against the source, and each group's first visible frame on or after its word onset.

**7 Cover.** Export a cover PNG at the same resolution as the video, taken from a strong overlay frame that still clears his face. When the output is `<n>-edited.mp4`, the cover is `<n>-edited cover.png`.

**8 Notes and report.** Update `NOTES.md` with the speech cues, the visuals, placement rules, assets used, and any lesson from a revision. Do not write specific timestamps as rules to copy next time. Report the output paths, what appears on each line, and how to rebuild. Do not post.

## Output

When the source lives in `~/Movies/Videorc/recordings/` as `<n>.mp4` (for example `1.mp4`), write:

- `~/Movies/Videorc/recordings/<n>-edited.mp4`
- `~/Movies/Videorc/recordings/<n>-edited cover.png`

Keep a project folder (brief, NOTES, assets, render scripts) under `~/projects/short-format-videos/` if that is the working root, but the deliverable must land in recordings. Do not leave the only copy inside the project folder. Say Videorc, never OBS.

## NOTES.md

Record what an editor should reuse, not a list of clocks:

- Speech cue table: the bolded starting word and the visual for each group.
- Font, motion and placement defaults actually used.
- Official asset paths and press-kit URLs.
- Keep-out measurements for this take, including hand clearance.
- Lessons from review (what was too minimal, which name appeared too early).
- How to rebuild.

## House rules

- No em dashes in briefs, notes or on-screen type.
- Do not use the banned filler word from the house voice rules.
- Do not show "free" unless he says it and the claim is verified.
- Nobody posts, uploads or publishes without an explicit yes from OrcDev.
