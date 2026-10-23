# <Game> — Cast

Status: draft <YYYY-MM-DD>. Follows `bible.md` and needs the same sign-off.

## Rules for every NPC

- **Look:** <how NPCs differ from the hero in value and colour>. Each reads by
  outline: hat, hood, tool, posture. One painting each, skinned to a few
  bones (`skinned-npc`).
- **Faces:** hooded, veiled, masked or turned away, so nobody needs lip
  sync. They act with posture and hands; their voice drives a small head or
  shoulder bend.
- **Names:** <whether NPCs are known by a role until something changes; how
  the subtitle and journal show the change>.
- **Animations:** `idle`, `talk_a` and `talk_b`, plus one signature action, in
  one facing that is mirrored as needed.
- **Voice:** every voice is distinct. The base direction below goes into
  casting; turning-point lines carry their own `[#vo=…]`.

## The hero

- **Who:** <one paragraph, from the bible>.
- **Voice brief:** age, timbre, accent, pace, attitude, and three sample
  lines.
- **Speaker name in dialogue files:** `<Hero>` (the hero actor's
  `speaker_name`, and `player` in `tools/audio/config.json`).

## The NPCs

### <Role>: part <N>, `<room_id>` (and `<room_id>`)

- **Wants:** <what they want from the hero; the puzzle it starts>.
- **Gives:** <the item, fact or memory they hand over, and for what>.
- **Silhouette:** <outline in one line: tall, short, hat, tool, posture>.
- **Voice:** <base direction: age, texture, pace, humour>.
- **Secret:** <what they know and hide; when it comes out>.
- **Turn:** <how they change by the end of their part>.
- **Signature action:** `<verb>` (for example `dig`, `light`, `wind`).
- **Speaker names:** `<Role>` (and `<Name>` once <condition>).

## Memory figures (flashbacks)

How people from the past are drawn and voiced, if they appear.

## Production order

| NPC | Part | Rooms | Painting request | Rig | Voice |
|---|---|---|---|---|---|
