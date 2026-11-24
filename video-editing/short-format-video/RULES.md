# Short format video rules

Standing format, voice and fact rules for every OrcDev Short (YouTube Shorts, TikTok, Instagram Reels, X). Script packaging and the shot list live in [SKILL.md](SKILL.md). The Remotion edit lives in [WORKFLOW.md](WORKFLOW.md).

## Length and shape

- Explainer Shorts: 30-40 seconds, allowed range 15-50 seconds. Instagram Trial Reels work best at 15-45 seconds.
- One tool or one idea per Short. Show the tool within the first seconds.
- Hard hook in the first second. Then "what it is and why it matters", 3-5 features or one clear point, short CTA.
- No slow intro, no logo sting, no fade in. Frame 0 must already be interesting.
- Speaking pace is about 2.5 to 3 words per second. A 30-second Short is roughly 75 to 90 spoken words. Count the words and cut until the script fits the target.
- On-screen hook title is small, calm and inside the central 80% of the frame. Not a giant full-width blast. Numbers below.

## On-screen hook title

The burned-in title at the start of the video. Separate from the spoken hook, from word-synced captions, and from the YouTube / TikTok / Reels title. It must read as small and calm. Giant ultra-bold all-caps across the phone is not the house style.

All numbers below are for the 1080x1920 canvas.

- **Width:** max 80% of the frame (864 px). Side margins at least 108 px. Prefer 120 px, so glyphs sit inside x 120-960. No full-width, no edge-to-edge, no line that hugs the frame. Phones crop the left and right; wide titles get cut.
- **Size:** 56-68 px. Hard cap 72 px. Readable at arm's length, not a third of the frame tall.
- **Weight and case:** Medium or Semibold (500-600). Never Black, ExtraBold or Ultra for this title. Sentence case, or short Title Case. Not a full-line ALL CAPS blast. One keyword may use the accent color; the rest stays the same weight.
- **Lines:** 1-2 lines. 3 only if every line still has about 3-5 words. About 3-5 words per line. Whole title about 5-7 words.
- **Placement:** upper-middle safe zone. Top of the block, plate included, at y 320-380. Bottom of the block by y 560. Never above y 300. Never into the bottom about 350 px (platform caption and music bar) or the right about 150-192 px (like/share rail). Overlapping hair is fine. Cover frames must also sit inside Instagram's 3:4 crop (about y 240-1680).
- **Box vs stroke:** white or near-white type. Either a 2-3 px dark stroke plus a soft shadow, or a small rounded plate (padding 16-24 px, fill about 45-65% black). Fit the plate to the words. Not a full-width bar. Not a thick slam outline.
- **On screen:** from frame 0 through the first spoken sentence, typically 1.5-2.5 s. Fully landed for at least 1.2 s. Fade off in 4-8 frames at the Beat 1 hard cut. Do not leave it up for the rest of the video.
- **Entrance:** fade plus an 8-16 px rise, or fade plus scale 96% to 100%, 8-12 frames at 30 fps, ease-out. No slam, shake, bounce, 3D flip or overshoot spring.

Platform UI to stay clear of (organic Shorts, Reels and TikTok inherit the same chrome as the published ad overlays):

- Top: YouTube 288 px, Reels 269 px (14%), TikTok 240 px. House floor is y 300.
- Bottom: YouTube and Reels 672 px (35%), TikTok 660 px. Captions already sit above this.
- Right: YouTube 192 px; TikTok's like/share rail about 300 px from y 840 down; Reels 65 px plus the button column. The hook title lives in the upper band so it misses that rail, but it still keeps 150 px off the right edge.
- Sides: TikTok 120 px; some phones crop 9:16 to fill a taller screen. That is why the title is capped at 80% width with 108-120 px side margins.

Word-synced captions stay 70-90 px heavy sans in the lower-middle safe zone. Do not restyle them to match this title, and do not put this title in the caption slot.

## Voice

- Casual talk-to-camera voice, contractions, plain words.
- No hustle-bro or stadium-speech lines (for example "Builders build. Use it.").
- Never use the word "honest" anywhere, including "to be honest with you".
- No em dashes in titles, scripts, on-screen text, descriptions or posts.
- Titles are hooky but not misleading. Nothing the sources do not support. No invented numbers, quotes or links. Use `[VERIFY]` or `[ADD LINK]` placeholders for unknowns.
- Every Short gets its own unique hooky title for that specific tool. Never use "Open Source Tool That Feels Illegal to Be Free" or "Feels Illegal To Be Free" on a Short; that series line is only for long-form compilations. Do not open a Short with a series line.
- "Did you know..." hooks work for Videorc feature Shorts.
- Captions on social posts: plain keyword captions, no hashtags.

## Names and branding

- Say Videorc (his recording and streaming app), never OBS. Never show OBS.
- shadcn is a system, not a library.
- When TanStack AI comes up, include the Neon TanStack AI adapter link (he built it). If the URL is not verified, use `[ADD LINK]`.
- Add a "not sponsored" disclosure when Neon tech is mentioned (he works at Neon).
- Only "OrcDev" as branding on screen.
- Spell product names correctly. Whisper mistakes never ship. House corrections:
  - "VideoOrg", "Video work", "videorg" = **Videorc**
  - "grogbot", "Grokbot" = **Grok Bot**
  - "potato" = **poteto** (Lauren, on the Grok Bot team, @poteto on X)
  - "Orcanva" (correct), "Neon Realtime" (correct product name)
  - "OrcDev" is the creator

## Verified claims

- Check every claim against the official source (blog, docs, npm, GitHub releases, official X posts). Mark anything unconfirmed `[VERIFY]`. Note where a tip or digest differs from the source.
- Only use facts from the brief, the transcript, the official site or repo, or what the operator confirmed. Do not invent numbers, features or quotes. If something cannot be verified, leave it out.
- Only state limits, prices and features that are verified for this product today. If the operator has not confirmed a fact, ask, or drop the claim.
- Videorc multi-stream goes to a maximum of five destinations. Say five. Not seven, not "unlimited", not "as many as you want".
- Never call a Premium feature free. If a proof point sits behind the paid tier, say so or leave it out of a "free" Short.
- "Free" means a real free tier with the feature in it. Check watermarks, time limits and caps before saying "no watermark" or "no limits".
- Round numbers up in the hook only if the number is true. "5 platforms" is true for Videorc. "10 platforms" is not.
- If a fact changes (a limit goes up, a feature moves tiers), the fact wins over this document. Update the script, then update this skill.

## Posting

- Never post, upload or send a Short without the operator's explicit yes. He says "post this video", gets the packaging, says yes; then it gets posted.
- Editors never post. The coordinator does not post either until that yes.
- Save Shorts in the Notion Shorts database with Status Draft. Prefer updating an existing page on the same topic over creating a duplicate.
- If he says a topic was covered on a livestream, package it as the livestream segment cut and use that stream's Notion plan as source.
