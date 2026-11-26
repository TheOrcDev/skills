# Short format video rules

Standing format, voice and fact rules for every OrcDev Short (YouTube Shorts, TikTok, Instagram Reels, X). Script packaging and the shot list live in [SKILL.md](SKILL.md). The Remotion edit lives in [WORKFLOW.md](WORKFLOW.md).

## Length and shape

- Explainer Shorts: 30-40 seconds, allowed range 15-50 seconds. Instagram Trial Reels work best at 15-45 seconds.
- One tool or one idea per Short. Show the tool within the first seconds.
- Hard hook in the first second. Then "what it is and why it matters", 3-5 features or one clear point, short CTA.
- No slow intro, no logo sting, no fade in. Frame 0 must already be interesting.
- Speaking pace is about 2.5 to 3 words per second. A 30-second Short is roughly 75 to 90 spoken words. Count the words and cut until the script fits the target.
- On-screen hook title is **one short line**, small and calm, inside the central 80% of the frame, and never on his face or forehead. Not a giant full-width blast, and not a 2-line stack across his forehead. Numbers below.

## On-screen hook title

The burned-in title at the start of the video. Separate from the spoken hook, from word-synced captions, and from the YouTube / TikTok / Reels title. It must read as small and calm. Giant ultra-bold all-caps across the phone is not the house style.

All numbers below are for the 1080x1920 canvas.

- **Width:** max 80% of the frame (864 px). Side margins at least 108 px. Prefer 120 px, so glyphs sit inside x 120-960. No full-width, no edge-to-edge, no line that hugs the frame. Phones crop the left and right; wide titles get cut.
- **Size:** 56-68 px. Hard cap 72 px. Readable at arm's length, not a third of the frame tall.
- **Weight and case:** Medium or Semibold (500-600). Never Black, ExtraBold or Ultra for this title. Sentence case, or short Title Case. Not a full-line ALL CAPS blast. One keyword may use the accent color; the rest stays the same weight.
- **Lines:** **Exactly one line.** Never wrap to 2 or more lines. If the phrase does not fit, rewrite it to a shorter punchy line that keeps the same meaning (no invented facts) and/or shrink the font slightly (stay in the 56-68 px band if you can; do not drop below 52 px). About 3-6 words is typical.
- **Placement:** upper-middle safe zone, **above his head, never on his face or forehead.** Never above y 300. Start the block just below y 300 (typically y 310-360). A one-line plate is short, so the bottom should stay well above his hair. Measure the top of his hair / forehead on the actual hook frames and leave a clear gap. If the face fills the frame and hair starts near or above y 300, scale and anchor the talking head down (or open on a split with the visual on top) so there is room for the hook between y 300 and the top of his hair. **Do not place the hook across his forehead**, even if that would fall inside the old y 320-560 box. Never into the bottom about 350 px (platform caption and music bar) or the right about 150-192 px (like/share rail). Cover frames use the same one-line hook, still clear of his face, and inside Instagram's 3:4 crop (about y 240-1680).
- **Box vs stroke:** white or near-white type. Either a 2-3 px dark stroke plus a soft shadow, or a small rounded plate (padding 16-24 px, fill about 45-65% black). Fit the plate to the words. Not a full-width bar. Not a thick slam outline.
- **On screen:** from frame 0 through the first spoken sentence, typically 1.5-2.5 s. Fully landed for at least 1.2 s. Fade off in 4-8 frames at the Beat 1 hard cut. Do not leave it up for the rest of the video.
- **Entrance:** fade plus an 8-16 px rise, or fade plus scale 96% to 100%, 8-12 frames at 30 fps, ease-out. No slam, shake, bounce, 3D flip or overshoot spring.

Platform UI to stay clear of (organic Shorts, Reels and TikTok inherit the same chrome as the published ad overlays):

- Top: YouTube 288 px, Reels 269 px (14%), TikTok 240 px. House floor is y 300.
- Bottom: YouTube and Reels 672 px (35%), TikTok 660 px. Captions already sit above this.
- Right: YouTube 192 px; TikTok's like/share rail about 300 px from y 840 down; Reels 65 px plus the button column. The hook title lives in the upper band so it misses that rail, but it still keeps 150 px off the right edge.
- Sides: TikTok 120 px; some phones crop 9:16 to fill a taller screen. That is why the title is capped at 80% width with 108-120 px side margins.

Word-synced captions are defined below. Do not restyle them to match this title, and do not put this title in the caption slot.

## Talking-head framing

On a 1080x1920 canvas, the talking head stays at scale 0.72-0.78 for the whole video, not only the hook. Anchor it to the bottom edge and feather the edges (`mask-image`, about 13% sides and 15% top) into a `#07090a` background so the seam does not show.

- Punch-ins stay on that base: ease up to about 0.82-0.90. Never jump to 1.04-1.125. That tight crop puts his hair at the top of the frame and drops the hook or CTA onto his forehead.
- Hook, captions and CTA never go on his face, hair, forehead or eyes. The Ghostex hook is the reference: one-line hook just below y 300, with captions (and later the CTA) in the clear space, often in the gap above his hair or under the chin / on the chest.
- Measure the raw take before you lock the scale. Tight takes (hair around y 130-190 in a 1080x1920 fit, about 6-9% down) need 0.72-0.78 so the hook can sit below y 300. From the next batch the camera moves back (about arm's length, 60-80 cm, hair about 15-20% down in the raw). A looser raw may need less scale-down and can support different, wider layouts. Recalibrate from the measured headroom. Do not copy an old scale blindly.

## Burned-in captions

Plain white TikTok-style captions, not a colored karaoke highlight.

- Type: bold sans (about 64-80 px on 1080 wide), all white. A 2-3 px dark stroke plus a soft shadow for legibility. No fill plate.
- No colored active-word highlight, no green, no amber, no yellow on the spoken word. Every word in the chunk is the same white.
- Chunks: short, 1-3 words or one short line. One line only. Synced to word timestamps.
- Placement: in the safe area, never on his face, hair, forehead, eyes, nose or mouth. On a full talking-head, follow the Ghostex hook layout: during the open, captions can sit in the gap between the hook title and his hair; later they sit under the chin or on the chest (lower-middle safe zone, still above the bottom about 350 px). On a split, sit them at the seam, never on the eyes. Keep 150 px off the right rail.
- These sizes and colors are for the caption track only. The opening hook title stays 56-68 px Medium/Semibold, as above.

## No overlay on his face

- **No overlay may cover his face.** This is not only the hook title. CTA cards, "Link in description" plates, offer chips, logos, captions, badges, and any other graphic must stay clear of his hair, forehead, eyes, nose and mouth.
- Always measure the face and hair on the actual frames of that shot. Stay on the 0.72-0.78 talking-head scale (punch-ins only to about 0.82-0.90) so the old upper band (y 320-560) is usually clear of his hair. If a graphic would still sit on his forehead or eyes, move it below the chin / onto the chest (still inside safe lanes), or scale the head down so there is a clear gap, the same as the hook treatment.
- Still never above y 300, still inside 80% width, still clear of the bottom and right rails.

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
