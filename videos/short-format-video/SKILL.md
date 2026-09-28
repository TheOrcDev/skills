---
name: short-format-video
description: Write short-format video scripts (TikTok, Instagram Reels, YouTube Shorts) as one package with two halves, the spoken script and an editor-ready beat-by-beat shot list (camera angle, captions, on-screen graphics, B-roll, cuts), plus the standing OrcDev packaging (four titles, description, X post, tags). Every Short runs Hook, post-hook bridge, Value, CTA. Use when writing a Short, Reel, TikTok, or any sub-60-second product video script, when the user asks for a spoken script plus shot list, when marketing Videorc or another product in short form, or invokes /short-format-video.
---

# Short Format Video

Write a short-format video as **one document with two halves**:

1. **Spoken script**: the exact words OrcDev says to camera, beat by beat.
2. **Shot list / video script**: the same beats timed out with camera angle, framing,
   captions, on-screen graphics, B-roll and cut notes.

Both halves share the same beat numbers, so an editor (human or AI) can cut the video
from this document plus the raw footage without asking a single question. If the shot
list cannot be handed to a stranger with the footage and produce the video, it is not
finished.

The format below is mandatory for **every** Short written with this skill. Videorc is
the usual subject, but the recipe is product-agnostic.

## 1. Gather the inputs

Collect these before writing. Ask when missing; if the user cannot answer, write the
script anyway and list your assumptions in an `Assumptions` block at the top of the
package so they can be corrected in one pass.

| Input | Why it matters |
|---|---|
| Product and the **exact URL** for this video | The CTA must send people to the right place |
| The **one claim** this Short is about | One Short, one idea. Multi-stream, recording, clipping: pick one |
| **Verified facts** for that claim (limits, price, tier, platforms) | Honest claims only, see [Honesty rules](#5-honesty-rules) |
| Target length | Default 25 to 40 seconds. Hard ceiling 60 seconds |
| Footage available or plannable | Face cam, screen recordings, phone, outdoor, office |
| Series | `One-off` or `Update`. Nothing else |

Speaking pace is about 2.5 to 3 words per second. A 30-second Short is roughly 75 to 90
spoken words. Count the words and cut until the script fits the target.

## 2. The four-beat arc

Every Short follows this arc, in this order, with nothing in front of the hook.

### Beat 1: Hook (0 to ~2 seconds)

Stop the scroll with curiosity. The line is a question or a claim the audience did not
expect, ideally combining **did-you-know + free + a concrete, audience-relevant number
or outcome**.

Reference hook OrcDev likes:

> "Did you know you can go live on 5 platforms at once for free?"

Rules for the hook:

- **Face to camera**, tight or medium-close framing, eye contact from frame one.
- **Captions on** from the first word.
- Optional **pop-up icons that match the claim** while the line is spoken (for the
  hook above: Twitch, YouTube, X logos popping in one by one, timed to the words).
- No greeting, no "hey guys", no logo sting, no music intro before the line. The hook
  is the first frame.
- Roughly a dozen words, one breath. Read it aloud: if it takes more than about 2
  seconds at a natural pace, cut words until it does.

### Beat 2: Post-hook bridge (~2 to ~5 seconds)

Immediately after the hook, name the product and promise the how:

> "You can do this easily with this app."

or the direct version:

> "It's called Videorc, and it takes about a minute to set up."

This beat **reveals the product**: say the name, show the logo or the UI. The viewer
now knows what they are watching and why to stay.

### Beat 3: Value (~5 seconds to ~5 seconds before the end)

Concrete proof points that back the hook. Pick **two to four**, lead with the one that
pays off the hook, and make each one visible on screen the moment it is spoken.

- Show, do not list: a destination getting added, the go-live button, the stream tiles.
- Punchy, spoken-language lines. One idea per sentence.
- Not a feature dump. Anything that does not serve this Short's one claim is cut and
  saved for another Short.
- Every proof point is a **verified fact** (see [Honesty rules](#5-honesty-rules)).

### Beat 4: CTA (last 3 to 5 seconds)

One clear action, spoken **and** on screen:

> "Go to videorc.com and try it."

- Use the exact URL for this video. Never a vague "link in bio" when a URL fits.
- Face to camera again for the close, so the video ends on a person, not a UI.
- End card or destination pill with the URL. Hold it on screen for at least 2 seconds.
- Optional soft second ask only if the platform rewards it ("follow for the next one").
  The URL is always the primary CTA.

## 3. Attention rules for the shot list

These are mandatory. Every one of them must be visible in the shot list.

- **Hard cut or angle change right after the hook sentence.** The first sentence is
  one shot. The moment it ends, cut to a different angle, framing, or B-roll. This is
  the single biggest retention move on TikTok and Reels. Document it explicitly in the
  cut notes of Beat 1 to Beat 2.
- **Document every angle change.** No two consecutive beats share the exact same
  camera setup without a reason written in the cut notes. Typical rotation: face cam
  A (centre, medium-close), face cam B (off-axis or punch-in), screen UI, B-roll.
- **Captions on every beat.** Word-by-word or 2 to 4 word chunks, keyword emphasised,
  kept inside the safe area (clear of the bottom action bar and the right-hand button
  column on vertical video). State the caption style once at the top of the shot list.
- **Graphics match the spoken line.** If he says "Twitch, YouTube and X", those three
  logos appear on those three words. If he says "five destinations", five destination
  pills appear. If he says "free", a `FREE` badge appears. Nothing on screen that the
  audio does not mention, and nothing mentioned that the screen does not show.
- **B-roll where it helps.** Use it to break up talking-head time, to cover a jump cut,
  or to make an abstract line concrete. B-roll ideas that fit OrcDev's channel:
  - Orc at the computer, typing, clicking go-live
  - Orc on the phone talking, walking, outdoors
  - Office wide shot, over-the-shoulder on the monitor
  - Funny or exaggerated alternate positions: leaning into the lens, arms crossed,
    pointing at a pop-up that appears next to his head
  - Clean screen recordings of the product UI (always mark the exact screen)
- **Mark A-roll versus B-roll on every beat.** `A-roll` is OrcDev's face speaking on
  camera. `B-roll` is anything cut over the voice. Never leave a beat unmarked.
- **Hook and CTA are A-roll.** Everything in between can be either.

## 4. Package format

Produce the whole package in this order, with these exact headings. Do not skip a
section; if a section does not apply, write `None` under it and say why.

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
4. Too hooky / ragebait: <title>
Recommended: #<n>, because <one line>

## Hook
<the exact first sentence>

## Script (spoken)
Beat 1 (Hook): <line>
Beat 2 (Bridge): <line>
Beat 3 (Value): <line(s)>
Beat 4 (CTA): <line>

## Shot list / video script
Captions: <style note, e.g. 2-4 word chunks, white, black stroke, keyword amber, bottom-centre inside safe area>
Aspect: 9:16, 1080x1920

| # | Time | VO line | Camera | Graphics / captions | B-roll | Cut notes |
|---|------|---------|--------|---------------------|--------|-----------|

## B-roll plan
<numbered list: what to shoot or capture, where it is used (beat #), and duration needed>

## CTA
<spoken line + what is on screen>

## Description
<platform description, first line carries the hook, URL on its own line>

## X Post
<one post, under 280 characters, URL included>

## YouTube Tags
<comma-separated, 10 to 20 tags>
```

### Titles

Exactly four, in this order, then mark one Recommended:

1. **Question**: the hook rephrased as a question. ("Can you really stream to 5 platforms for free?")
2. **Bold**: a flat, confident statement. ("Stream to 5 platforms at once. Free.")
3. **Hooky**: curiosity gap without lying. ("The free multistream trick most streamers miss")
4. **Too hooky / ragebait**: deliberately over the line so the user can see the edge.
   Mark it as such; it exists for calibration and is rarely the pick.

Recommended is usually #2 or #3. Write one line on why.

### Shot list columns

Each row is one beat or one shot inside a beat. Split a beat into several rows when
the camera changes mid-beat.

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

- **Description**: first line repeats the hook, second block says what the video shows,
  URL alone on its own line, then two or three hashtags at most.
- **X Post**: one post, spoken-voice, under 280 characters, hook first, URL last. No
  hashtag pile.
- **YouTube Tags**: comma-separated, 10 to 20, mix of product name, the claim, the
  platforms named, and the category (`multistream, live streaming, videorc, ...`).

### Series

`Series` is `One-off` or `Update`. **Never use the old "Illegal to Be Free" Shorts
series line** or any variant of it in titles, hooks, descriptions or tags.

## 5. Honesty rules

Short-form rewards exaggeration. This skill does not. A claim that the product cannot
back gets the video reported, the comments hostile, and the trust gone.

- Only state limits, prices and features that are **verified for this product today**.
  If the user has not confirmed a fact, ask, or drop the claim.
- **Videorc multi-stream goes to a maximum of five destinations.** Say five. Not seven,
  not "unlimited", not "as many as you want".
- **Never call a Premium feature free.** If a proof point sits behind the paid tier, say
  so or leave it out of a "free" Short.
- "Free" means a real free tier with the feature in it. Check watermarks, time limits
  and caps before saying "no watermark" or "no limits".
- Round numbers up in the hook only if the number is true. "5 platforms" is true for
  Videorc. "10 platforms" is not.
- If a fact changes (a limit goes up, a feature moves tiers), the fact wins over this
  document. Update the script, then update this skill.

## 6. Mini example: Videorc multi-stream

A complete package at roughly 30 seconds, showing the arc and a shot list an editor can
cut from. Facts used: Videorc multistreams to up to five destinations on the free tier,
no watermark, at videorc.com. Confirm these still hold before shooting.

```markdown
# Go Live on 5 Platforms for Free (Short)

**Product:** Videorc · **URL:** videorc.com · **Series:** One-off
**Target length:** 30s · **Word count:** 63 (leaves room for the UI beats to breathe)

## Titles
1. Question: Can You Really Go Live on 5 Platforms at Once for Free?
2. Bold: Stream to 5 Platforms at Once. Free.
3. Hooky: The Free Multistream Setup Most Streamers Don't Know About
4. Too hooky / ragebait: Streamers Are Paying Every Month for Something That's Free
Recommended: #2. It is the hook as a promise, and it fits on one line of a Shorts thumbnail.

## Hook
Did you know you can go live on 5 platforms at once for free?

## Script (spoken)
Beat 1 (Hook): Did you know you can go live on 5 platforms at once for free?
Beat 2 (Bridge): You can do this easily with this app. It's called Videorc.
Beat 3 (Value): Add your destinations, Twitch, YouTube, X, whatever you stream on, up to five of them. Hit go live once, and you're live everywhere. No watermark, and the free plan actually covers this.
Beat 4 (CTA): Go to videorc.com and try it.

## Shot list / video script
Captions: 2-4 word chunks, white with black stroke, keyword in amber, bottom-centre inside safe area, on from frame one.
Aspect: 9:16, 1080x1920

| # | Time | VO line | Camera | Graphics / captions | B-roll | Cut notes |
|---|------|---------|--------|---------------------|--------|-----------|
| 1 | 0.0-2.2 | Did you know you can go live on 5 platforms at once for free? | A-roll, face cam A, centre, medium-close, eye contact | Captions on. Twitch, YouTube, X logos pop in top-left, one per beat of "5 platforms"; `FREE` badge pops on "free" | None | **Hard cut** to face cam B the moment "free" lands |
| 2 | 2.2-5.0 | You can do this easily with this app. It's called Videorc. | A-roll, face cam B, off-axis 30 degrees, waist-up, punched in 15% | Videorc logo slides in beside head on "Videorc" | None | Whip to screen UI |
| 3a | 5.0-11.0 | Add your destinations, Twitch, YouTube, X, whatever you stream on, up to five of them. | B-roll | Destination pills appear on the UI as each platform is named; counter `5 / 5` fills on "up to five" | Screen: Videorc destinations panel, adding each platform | Cut on the fifth pill to B-roll |
| 3b | 11.0-16.0 | Hit go live once, and you're live everywhere. | B-roll | Caption keyword `ONCE` in amber. Five live tiles light up on "everywhere" | Orc at desk, over-the-shoulder, clicks Go Live, then screen recording of stream tiles going live | Cut to face cam A on "everywhere" |
| 3c | 16.0-24.0 | No watermark, and the free plan actually covers this. | A-roll, face cam A, centre, medium-close | `NO WATERMARK` strike-through badge; `FREE PLAN` pill on "free plan" | Optional 1s insert: clean stream output, no watermark corner | Punch-in 10% on "actually" for emphasis |
| 4 | 24.0-30.0 | Go to videorc.com and try it. | A-roll, face cam B, waist-up, small lean toward the lens | End card: `videorc.com` centred pill, hold 3s after VO ends | None | Hold, fade out on the URL |

## B-roll plan
1. Screen recording, Videorc destinations panel: add Twitch, YouTube, X and two more. Clean 1080x1920 crop or 16:9 letterboxed. Needed: 8s. Used in 3a.
2. Orc at desk, over-the-shoulder, clicking Go Live. Needed: 3s. Used in 3b.
3. Screen recording, stream tiles switching to live. Needed: 4s. Used in 3b.
4. Clean stream output showing no watermark in any corner. Needed: 2s. Used in 3c (optional).
5. Face cam A (centre) and face cam B (off-axis) recorded for the whole script so any line can be cut from either angle.

## CTA
Spoken: "Go to videorc.com and try it." On screen: `videorc.com` pill, held 3 seconds after the line.

## Description
Did you know you can go live on 5 platforms at once for free?

Videorc lets you add up to five destinations, Twitch, YouTube, X and more, and go live everywhere with one click. No watermark on the free plan.

videorc.com

#multistream #livestreaming #videorc

## X Post
You can go live on 5 platforms at once. For free. No watermark.

Add your destinations, hit go live once, you're everywhere.

videorc.com

## YouTube Tags
videorc, multistream, multistreaming, go live on multiple platforms, stream to twitch and youtube, live streaming app, free multistream, streaming setup, restream alternative, streamyard alternative, twitch, youtube live, x live, content creator tools, streamer tips, how to multistream, live stream to 5 platforms
```

## 7. Before you hand it off

Run this list. Any `no` means the package is not done.

- [ ] First spoken word is the hook. Nothing before it.
- [ ] Hook reads aloud in about 2 seconds, face to camera, captions on, graphics match the claim.
- [ ] Hard cut or angle change immediately after the hook sentence, written in the cut notes.
- [ ] Bridge names the product within 5 seconds.
- [ ] Value beats are two to four verified proof points, each visible on screen when spoken.
- [ ] CTA speaks the exact URL and shows it on screen for at least 2 seconds.
- [ ] Every shot list row has a time, VO line, `A-roll`/`B-roll` mark, camera, graphics, B-roll and cut note.
- [ ] Captions planned on every beat, inside the safe area.
- [ ] Exactly four titles in order Question / Bold / Hooky / Too hooky-ragebait, one marked Recommended.
- [ ] Description, X Post and comma-separated YouTube Tags present.
- [ ] Series is `One-off` or `Update`. No "Illegal to Be Free" anywhere.
- [ ] Every claim is true today. Videorc multi-stream says five. No Premium feature called free.
- [ ] Word count fits the target length at 2.5 to 3 words per second.
