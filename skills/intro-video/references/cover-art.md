# Cover art

Thumbnails and cover frames for vertical video. Canvas 1080×1920.

Each platform overlays its own chrome on the cover. Guess the safe area wrong
and the type is buried under the UI.

| Platform | Type treatment | Keep clear |
|---|---|---|
| YouTube Shorts | outlined type, no plate | bottom ~470px |
| TikTok / Instagram | sticker plates behind the type | bottom ~480px **and** right ~200px |

The right-hand column on TikTok/Instagram is the action rail (avatar, like,
comment, share). YouTube Shorts has no right-side rail, so full width is
usable there.

- Same type stack as captions: Inter 800, white, 13px black stroke,
  `paint-order: stroke fill`.
- Keyword in `#FFD93D`.
- Render as a still composition, not a one-frame video.
- Real logos only — npm icon packs or the product's own GitHub repo.
