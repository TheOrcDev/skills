---
name: short-format-video
description: >-
  Run OrcDev short-format video end to end for YouTube Shorts, TikTok and
  Instagram Reels: format and voice, Notion script package, beat-by-beat shot
  list, Remotion edit (captions, hook placement, SFX, export), coordinator and
  editor setup, posting, Drive and Notion logging, 60-day repost. Use when
  writing a Short, Reel or TikTok, when cutting or captioning one, when posting
  or logging a Short, when starting a Shorts editor, or when the user invokes
  /short-format-video.
---

# Short Format Video

One skill for OrcDev Shorts, Reels and TikTok: voice, script package, shot list, Remotion edit, posting, logging and the 60-day repost.

Read [RULES.md](RULES.md) before writing a line or placing a pixel. Run [WORKFLOW.md](WORKFLOW.md) as written when cutting. Do not invent numbers or rules that are not in those files or this one.

A script package is **one document with two halves**:

1. **Spoken script**: the exact words OrcDev says to camera, beat by beat.
2. **Shot list / video script**: the same beats timed out with camera angle, framing, captions, on-screen graphics, B-roll and cut notes.

Both halves share the same beat numbers, so an editor (human or AI) can cut the video from this document plus the raw footage without asking a single question. If the shot list cannot be handed to a stranger with the footage and produce the video, it is not finished.

Videorc is the usual subject, but the recipe is product-agnostic. One tool or one idea per Short.

## The loop

```
Idea -> Draft package -> Ready -> Filmed
                                 |
                                 v
              coordinator starts one editor per video
                                 |
                                 v
              Remotion edit -> Movies folder + NOTES.md
                                 |
                                 v
              operator says "post this video" and yes
                                 |
                                 v
     YouTube / TikTok / IG trial / X  ->  Drive + Notion log  ->  +60 day remix
```

Notion Shorts DB status: `Idea` -> `Draft` -> `Ready` -> `Filmed` -> `Published`. Save new packages at **Draft**. Prefer updating an existing page on the same topic over creating a duplicate. Never publish or post without his explicit yes.

## Coordinator and editor

- **Coordinator** owns the queue and this skill. It does not cut footage. For each filmed Short it starts **one editor agent per video** (house default: Opus high). It collects the cut, prepares posting packaging when he says "post this video", and still waits for his yes.
- **Editor** works in that video's folder only, follows [WORKFLOW.md](WORKFLOW.md), writes the finished files to `~/Movies/Short Format Videos/`, and writes `out/NOTES.md`. Editors never post.
- House editing root: `~/projects/short-format-videos`. Coordinator space: Ghostex space named `Short Format Videos`.
- Do not post, upload or send a file until the operator says yes.

## 1. Gather the inputs

Collect these before writing. Ask when missing; if the user cannot answer, write the script anyway and list your assumptions in an `Assumptions` block at the top of the package so they can be corrected in one pass.

| Input | Why it matters |
|---|---|
| Product and the **exact URL** for this video | The CTA must send people to the right place |
| The **one claim** this Short is about | One Short, one idea. Multi-stream, recording, clipping: pick one |
| **Verified facts** for that claim (limits, price, tier, platforms) | Verified claims only, see [RULES.md](RULES.md) |
| Target length | Default 30 to 40 seconds. Range 15 to 50 seconds. Instagram Trial Reels best at 15 to 45 seconds |
| Footage available or plannable | Face cam, screen recordings, phone, outdoor, office |
| Series | `One-off` or `Update`. Nothing else |

Speaking pace is about 2.5 to 3 words per second. A 30-second Short is roughly 75 to 90 spoken words. Count the words and cut until the script fits the target.

If he says a topic was covered on a livestream, package it as the livestream segment cut and use that stream's Notion plan as source.

## 2. The four-beat arc

Every Short follows this arc, in this order, with nothing in front of the hook. Hard hook in the first second, then what it is and why it matters, 3-5 features or one clear point, short CTA. Show the tool within the first seconds.

### Beat 1: Hook (0 to ~2 seconds)

Stop the scroll with curiosity. The line is a question or a claim the audience did not expect, ideally combining **did-you-know + free + a concrete, audience-relevant number or outcome**. "Did you know..." hooks work for Videorc feature Shorts.

Reference hook OrcDev likes:

> "Did you know you can go live on 5 platforms at once for free?"

Rules for the hook:

- **Face to camera**, tight or medium-close framing, eye contact from frame one.
- **Captions on** from the first word.
- Optional **pop-up icons that match the claim** while the line is spoken (for the hook above: Twitch, YouTube, X logos popping in one by one, timed to the words). Keep them at or below y 300. Nothing important above y 300. Icons sit beside or under the title, not wider than the title block.
- No greeting, no "hey guys", no logo sting, no music intro before the line. The hook is the first frame.
- Roughly a dozen words, one breath. Read it aloud: if it takes more than about 2 seconds at a natural pace, cut words until it does.
- On-screen hook title from frame 0 to about the end of the first spoken sentence (typically 1.5-2.5 s, fully landed at least 1.2 s). Max about 7 words.
- Keep the title small and calm: 56-68 px (hard cap 72, floor 52 px if needed to stay on one line), Medium or Semibold, sentence case or short Title Case. **Exactly one line.** If it would wrap, shorten the phrase (keep the meaning, no invented facts) or shrink the font slightly. Not Black, not ALL CAPS across the frame, not a full-width bar. Full numbers in [RULES.md](RULES.md).
- Width: max 864 px (80% of 1080). Side margins at least 108 px, prefer 120 px (x 120-960). Phones crop the left and right; no edge-to-edge text.
- Placement: one line above his head, just below y 300, never on his face or forehead. Nothing important above y 300. Clear of the bottom about 350 px and the right about 150 px. If the face fills the frame, scale the talking head down or open on a split so the hook has a clear gap above his hair.
- Entrance: fade plus a short rise, or fade plus scale 96% to 100%, 8-12 frames, ease-out. No slam, shake or bounce.

### Beat 2: Post-hook bridge (~2 to ~5 seconds)

Immediately after the hook, name the product and promise the how:

> "You can do this easily with this app."

or the direct version:

> "It's called Videorc, and it takes about a minute to set up."

This beat **reveals the product**: say the name, show the logo or the UI. The viewer now knows what they are watching and why to stay.

### Beat 3: Value (~5 seconds to ~5 seconds before the end)

Concrete proof points that back the hook. Pick **two to four** (or up to five features when that is the point), lead with the one that pays off the hook, and make each one visible on screen the moment it is spoken.

- Show, do not list: a destination getting added, the go-live button, the stream tiles.
- Punchy, spoken-language lines. One idea per sentence.
- Not a feature dump. Anything that does not serve this Short's one claim is cut and saved for another Short.
- Every proof point is a **verified fact** (see [RULES.md](RULES.md)).

### Beat 4: CTA (last 3 to 5 seconds)

One clear action, spoken **and** on screen:

> "Go to videorc.com and try it."

- Use the exact URL for this video. Never a vague "link in bio" when a URL fits. The edit may still show "Link in bio" / repo URL / site URL as on-screen text; the spoken line prefers the URL.
- Face to camera again for the close, so the video ends on a person, not a UI.
- End on his last line with the CTA visible. No long outro, no end card longer than about 1 s. A clean loop back to the hook is a plus.
- Optional soft second ask only if the platform rewards it ("follow for the next one"). The URL is always the primary CTA.

## 3. Attention rules for the shot list

These are mandatory. Every one of them must be visible in the shot list.

- **Hard cut or angle change right after the hook sentence.** The first sentence is one shot. The moment it ends, cut to a different angle, framing, or B-roll. This is the single biggest retention move on TikTok and Reels. Document it explicitly in the cut notes of Beat 1 to Beat 2.
- **Document every angle change.** No two consecutive beats share the exact same camera setup without a reason written in the cut notes. Typical rotation: face cam A (centre, medium-close), face cam B (off-axis or punch-in), screen UI, B-roll.
- **Captions on every beat.** Word-by-word or 2 to 4 word chunks, keyword emphasised, kept inside the safe area. State the caption style once at the top of the shot list. Safe area on 1080x1920: nothing important above y 300 (TikTok/Reels cover the top about 250 px), clear of the bottom about 350 px and the right about 150 px. Full-head captions sit roughly y 1150-1450; split-layout captions sit at the seam, not on the eyes.
- **Graphics match the spoken line.** If he says "Twitch, YouTube and X", those three logos appear on those three words. If he says "five destinations", five destination pills appear. If he says "free", a `FREE` badge appears. Nothing on screen that the audio does not mention, and nothing mentioned that the screen does not show.
- **B-roll where it helps.** Use it to break up talking-head time, to cover a jump cut, or to make an abstract line concrete. B-roll ideas that fit OrcDev's channel:
  - Orc at the computer, typing, clicking go-live
  - Orc on the phone talking, walking, outdoors
  - Office wide shot, over-the-shoulder on the monitor
  - Funny or exaggerated alternate positions: leaning into the lens, arms crossed, pointing at a pop-up that appears next to his head
  - Clean screen recordings of the product UI (always mark the exact screen)
- **Mark A-roll versus B-roll on every beat.** `A-roll` is OrcDev's face speaking on camera. `B-roll` is anything cut over the voice. Never leave a beat unmarked.
- **Hook and CTA are A-roll.** Everything in between can be either.

## 4. Package format

Produce the whole package in this order, with these exact headings. Do not skip a section; if a section does not apply, write `None` under it and say why. B-roll/editor prompts have **no timings**; timings live only in the shot list.

```markdown
# <Working title> (Short)

**Product:** <name> · **URL:** <exact url> · **Series:** One-off | Update
**Target length:** <n>s · **Word count:** <n>

## Assumptions
<only if inputs were missing; otherwise omit this section>

## Titles
1. Question: <title>
2. Bold: <title>
3. Hooky: <title>
4. Ragebait: <title>
Recommended: #<n>, because <one line>

## Thumbnail / cover text
<short on-image text + visual concept>

## Framework
Hook, post-hook bridge, Value, CTA

## Hook
<the exact first sentence>

## Script (spoken)
Beat 1 (Hook): <line>
Beat 2 (Bridge): <line>
Beat 3 (Value): <line(s)>
Beat 4 (CTA): <line>

## Shot list / video script
Captions: <style note, e.g. 2-4 word chunks, white, black stroke, keyword amber, bottom-centre inside safe area. Opening hook title: one line, 56-68 px Semibold, max 864 px wide, above his head and never above y 300, never on his forehead>
Aspect: 9:16, 1080x1920

| # | Time | VO line | Camera | Graphics / captions | B-roll | Cut notes |
|---|------|---------|--------|---------------------|--------|-----------|

## B-roll
<numbered editor prompts with no timings: what to shoot or capture, where it is used (beat #)>

## CTA
<spoken line + what is on screen>

## Description
<YouTube description: first line is the hook, source links, URL on its own line, then the default footer>

## X Post
<one ready-to-post post, plain keyword caption, no hashtags>

## YouTube Tags
<comma-separated, 10 to 20 tags>
```

Save it in the Notion Shorts database at Status Draft. Report back: Notion link, recommended title, corrections and `[VERIFY]` items, in a short message.

### Titles

Exactly four, Title Case, in this order, then mark one Recommended:

1. **Question**: the hook rephrased as a question. ("Can you really stream to 5 platforms for free?")
2. **Bold**: a flat, confident statement. ("Stream to 5 platforms at once. Free.")
3. **Hooky**: curiosity gap without lying. ("The free multistream trick most streamers miss")
4. **Ragebait**: deliberately over the line so the user can see the edge. Mark it as such; it exists for calibration and is rarely the pick.

Recommended is usually #2 or #3. Write one line on why. Every Short gets its own unique hooky title for that specific tool. Never use "Feels Illegal To Be Free" or any variant on a Short.

### Shot list columns

Each row is one beat or one shot inside a beat. Split a beat into several rows when the camera changes mid-beat.

| Column | What goes in it |
|---|---|
| `#` | Beat number, sub-shots as `3a`, `3b` |
| `Time` | Start to end in seconds, `0.0-2.0`. Estimates are fine, but every row has one |
| `VO line` | The exact words spoken over this shot, verbatim from the Script section |
| `Camera` | `A-roll` or `B-roll`, then angle and framing: `A-roll, face cam A, centre, medium-close` |
| `Graphics / captions` | Caption text if it differs from VO, plus every overlay with its trigger word: `Twitch/YouTube/X logos pop in on each name` |
| `B-roll` | The specific clip: `Screen: Videorc destinations panel, adding YouTube` or `None` |
| `Cut notes` | What happens at the end of this row: `Hard cut to face cam B`, `Punch-in 15%`, `Whip to UI` |

### Description, X Post, Tags

- **Description**: first line repeats the hook, then what the video shows, real source links, URL alone on its own line, then the [default footer](#8-default-description-footer). No hashtag pile. Captions on social posts are plain keyword captions, no hashtags.
- **X Post**: one post, spoken-voice, under 280 characters, hook first, URL last. No hashtags. Posted from @orcdev when he says yes.
- **YouTube Tags**: comma-separated, 10 to 20, mix of product name, the claim, the platforms named, and the category (`multistream, live streaming, videorc, ...`).

### Series

`Series` is `One-off` or `Update`. **Never use the old "Illegal to Be Free" Shorts series line** or any variant of it in titles, hooks, descriptions or tags.

## 5. Verified claims (Videorc)

See [RULES.md](RULES.md) for the full fact rules. For Videorc Shorts, confirm these still hold before shooting:

- Videorc multi-stream goes to a maximum of **five** destinations. Say five.
- Never call a Premium feature free.
- "Free" means a real free tier with the feature in it. Check watermarks, time limits and caps before saying "no watermark" or "no limits".
- Say Videorc, never OBS. Never show OBS.

## 6. Mini example: Videorc multi-stream

A complete package at roughly 30 seconds, showing the arc and a shot list an editor can cut from. Facts used: Videorc multistreams to up to five destinations on the free tier, no watermark, at videorc.com. Confirm these still hold before shooting.

```markdown
# Go Live on 5 Platforms for Free (Short)

**Product:** Videorc · **URL:** videorc.com · **Series:** One-off
**Target length:** 30s · **Word count:** 63 (leaves room for the UI beats to breathe)

## Titles
1. Question: Can You Really Go Live on 5 Platforms at Once for Free?
2. Bold: Stream to 5 Platforms at Once. Free.
3. Hooky: The Free Multistream Setup Most Streamers Don't Know About
4. Ragebait: Streamers Are Paying Every Month for Something That's Free
Recommended: #2. It is the hook as a promise, and it fits on one line of a Shorts thumbnail.

## Thumbnail / cover text
Text: "5 platforms. Free." Visual: face cam with a compact one-line hook title (above his head, never above y 300, never on his forehead, max 864 px wide) and destination logos under it.

## Framework
Hook, post-hook bridge, Value, CTA

## Hook
Did you know you can go live on 5 platforms at once for free?

## Script (spoken)
Beat 1 (Hook): Did you know you can go live on 5 platforms at once for free?
Beat 2 (Bridge): You can do this easily with this app. It's called Videorc.
Beat 3 (Value): Add your destinations, Twitch, YouTube, X, whatever you stream on, up to five of them. Hit go live once, and you're live everywhere. No watermark, and the free plan actually covers this.
Beat 4 (CTA): Go to videorc.com and try it.

## Shot list / video script
Captions: 2-4 word chunks, white with black stroke, keyword in amber, on from frame one. Full-head at y 1150-1450; split at the seam. Nothing above y 300. Clear of bottom ~350 px and right ~150 px. Opening hook title is separate: one line, 56-68 px Semibold, max 864 px wide, above his head and never on his forehead.
Aspect: 9:16, 1080x1920

| # | Time | VO line | Camera | Graphics / captions | B-roll | Cut notes |
|---|------|---------|--------|---------------------|--------|-----------|
| 1 | 0.0-2.2 | Did you know you can go live on 5 platforms at once for free? | A-roll, face cam A, centre, medium-close, eye contact | Captions on. Compact one-line hook title (56-68 px Semibold, max 864 px wide, above his head, never above y 300, never on his forehead). Twitch, YouTube, X logos pop in on "5 platforms"; `FREE` badge pops on "free" | None | **Hard cut** to face cam B the moment "free" lands |
| 2 | 2.2-5.0 | You can do this easily with this app. It's called Videorc. | A-roll, face cam B, off-axis 30 degrees, waist-up, punched in 15% | Videorc logo slides in beside head on "Videorc" | None | Whip to screen UI |
| 3a | 5.0-11.0 | Add your destinations, Twitch, YouTube, X, whatever you stream on, up to five of them. | B-roll | Destination pills appear on the UI as each platform is named; counter `5 / 5` fills on "up to five" | Screen: Videorc destinations panel, adding each platform | Cut on the fifth pill to B-roll |
| 3b | 11.0-16.0 | Hit go live once, and you're live everywhere. | B-roll | Caption keyword `ONCE` in amber. Five live tiles light up on "everywhere" | Orc at desk, over-the-shoulder, clicks Go Live, then screen recording of stream tiles going live | Cut to face cam A on "everywhere" |
| 3c | 16.0-24.0 | No watermark, and the free plan actually covers this. | A-roll, face cam A, centre, medium-close | `NO WATERMARK` strike-through badge; `FREE PLAN` pill on "free plan" | Optional 1s insert: clean stream output, no watermark corner | Punch-in 10% on "actually" for emphasis |
| 4 | 24.0-30.0 | Go to videorc.com and try it. | A-roll, face cam B, waist-up, small lean toward the lens | CTA: `videorc.com` pill in the upper safe band (y 320-560), visible on the last line | None | End on the last line. No end card longer than ~1s |

## B-roll
1. Screen recording, Videorc destinations panel: add Twitch, YouTube, X and two more. Clean 1080x1920 crop or 16:9 letterboxed. Used in 3a.
2. Orc at desk, over-the-shoulder, clicking Go Live. Used in 3b.
3. Screen recording, stream tiles switching to live. Used in 3b.
4. Clean stream output showing no watermark in any corner. Used in 3c (optional).
5. Face cam A (centre) and face cam B (off-axis) recorded for the whole script so any line can be cut from either angle.

## CTA
Spoken: "Go to videorc.com and try it." On screen: `videorc.com` pill, visible on the last line.

## Description
Did you know you can go live on 5 platforms at once for free?

Videorc lets you add up to five destinations, Twitch, YouTube, X and more, and go live everywhere with one click. No watermark on the free plan.

videorc.com

━━━━━━━━━━━━━━━━━━
🎬 Recorded and edited with Videorc, my free recording and multistreaming app: https://videorc.com

📬 Get my newsletter: new tools, builds and behind the scenes, straight to your inbox: https://orcdev.com

🐦 X: https://x.com/orcdev

## X Post
You can go live on 5 platforms at once. For free. No watermark.

Add your destinations, hit go live once, you're everywhere.

videorc.com

## YouTube Tags
videorc, multistream, multistreaming, go live on multiple platforms, stream to twitch and youtube, live streaming app, free multistream, streaming setup, restream alternative, streamyard alternative, twitch, youtube live, x live, content creator tools, streamer tips, how to multistream, live stream to 5 platforms
```

## 7. Editing, files and naming

The cut is [WORKFLOW.md](WORKFLOW.md). Short version for anyone dispatching an editor:

- Remotion (React), one project per video folder. Headless shell via `npx remotion browser ensure`, not system Chrome.
- Compact one-line hook title from frame 0: 56-68 px Medium/Semibold, max 864 px wide, above his head and never above y 300, never on his forehead, subtle fade-in. Word-synced captions. Screenshots, animations and logos over explaining parts. SFX at about 20-30% volume (around -12 dB), well under his voice.
- Export 1080x1920, 30 fps, H.264 High yuv420p, AAC 48 kHz, about -14 LUFS, faststart. Cover PNG 1080x1920.
- Finished files go to `~/Movies/Short Format Videos/` as `YYYY-MM-DD Topic.mp4` and `YYYY-MM-DD Topic cover.png`. Never leave the only copy in `~/projects`.
- "This one too" style thumbnail shots need the real thumbnail from OrcDev before the edit.

## 8. Default description footer

Every YouTube video and Short ends with this footer:

```
━━━━━━━━━━━━━━━━━━
🎬 Recorded and edited with Videorc, my free recording and multistreaming app: https://videorc.com

📬 Get my newsletter: new tools, builds and behind the scenes, straight to your inbox: https://orcdev.com

🐦 X: https://x.com/orcdev
```

## 9. Distribution

He says "post this video", gets the packaging, says yes; then it gets posted. Never post without his yes.

- **YouTube Shorts** (YouTube Studio): always set the `cover.png` as custom thumbnail, add tags, Paid promotion = No, Altered/AI content = No. Description ends with the default footer. Scheduling default 9:00 Europe/Madrid, one per day.
- **TikTok** (TikTok Studio upload): Everyone, comments on, AI-generated and branded-content toggles off, custom cover.
- **Instagram**: post as a Trial Reel first. Clear win at about 24h, then go public; otherwise wait to 72h before going public. Instagram Trial Reels best at 15-45s.
- **X**: posted from @orcdev. A crosspost bot then fans X out to Threads, LinkedIn and Facebook (never post those directly).
- Save every Short to the Google Drive **Shorts** folder named `YYYY-MM-DD Topic.mp4` and log it in the Notion Shorts Distribution tracker: YouTube/IG/TikTok links, first posted, repost due +60 days.

### 60-day repost

Every about 60 days, lightly remix (zoom, mirror, crop or new hook), Instagram trial again, then public everywhere again. Log the new first-posted date and the next +60 due date.

## 10. Before you hand the script off

Run this list. Any `no` means the package is not done.

- [ ] First spoken word is the hook. Nothing before it.
- [ ] Hook reads aloud in about 2 seconds, face to camera, captions on, graphics match the claim. On-screen hook title is one short line, 56-68 px, max 80% width, above his head, never above y 300, and never on his face or forehead.
- [ ] Hard cut or angle change immediately after the hook sentence, written in the cut notes.
- [ ] Bridge names the product within 5 seconds. Tool is on screen in the first seconds.
- [ ] Value beats are two to four verified proof points (or one clear point / 3-5 features), each visible on screen when spoken.
- [ ] CTA speaks the exact URL and shows it on screen. No end card longer than about 1 s.
- [ ] Every shot list row has a time, VO line, `A-roll`/`B-roll` mark, camera, graphics, B-roll and cut note.
- [ ] Captions planned on every beat, inside the safe area.
- [ ] Exactly four titles in order Question / Bold / Hooky / Ragebait, one marked Recommended. Thumbnail/cover text and Framework present.
- [ ] Description (with default footer), X Post (no hashtags) and comma-separated YouTube Tags present.
- [ ] Series is `One-off` or `Update`. No "Illegal to Be Free" anywhere.
- [ ] Every claim is true today. Videorc multi-stream says five. No Premium feature called free.
- [ ] Word count fits the target length at 2.5 to 3 words per second. Target is 30-40s (range 15-50s).
- [ ] No em dashes. The banned word from [RULES.md](RULES.md) does not appear.
- [ ] Status Draft in Notion. Report: Notion link, recommended title, corrections, `[VERIFY]` items.
