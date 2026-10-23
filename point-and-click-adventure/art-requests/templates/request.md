# IMG-0000 — <title>

status: open
operator-approval: not-required
plan: <NNN>
requested: <YYYY-MM-DD> by Claude for plan <NNN>, slice <N>

`status` is one of open, delivered, revise, accepted, rejected or cancelled.
`operator-approval` is required or not-required. `plan` names the plan whose
image budget pays for this request.

## Purpose

Where this image is used in the game and what it has to do there. Name the
room, character or item id, and the request it is an edit of, if any.

## Generation

`tools/images/run.ts` reads this block.

```json
{
  "model": "codex/gpt-6.1-sol",
  "size": "2560x1440",
  "quality": "high",
  "n": 3,
  "background": "opaque",
  "references": [],
  "mask": null
}
```

- **`model`:** `codex/gpt-6.1-sol` sends the request to Sol through Codex,
  billed to the ChatGPT plan at $0. Sol returns its own fixed size (1672×941
  landscape, 1024×1536 portrait); `size` then only sets the shape. It can't
  take a mask. Gateway models: `openai/gpt-image-2.5-flare` for new images,
  `openai/gpt-image-2.5-sunburst` for edits, `openai/gpt-image-2` as the
  fallback.
- **`references`:** repository paths of input images. With references, the
  call is an edit; the image to edit comes first. Every path must exist.
- **`mask`:** optional, gateway only. A PNG with alpha, the same size as the
  first reference, transparent where the image may change.
- **`size`:** both sides multiples of 16, aspect between 1:3 and 3:1, no edge
  above 3840. Rooms use 2560×1440; NPCs 1440×2560; vista rings 3840×1280.
- **`quality`:** `medium` while exploring, `high` for finals, `max` only for
  hero images (gateway). Sol ignores it.
- **`n`:** 1 to 10 variants. Three for new images, two for edits.
- **`background`:** `opaque`, or `transparent` for cut-outs, character and
  item sheets and UI art.

## Prompt

The tool sends this text block verbatim. Start from the matching preamble in
`art-source/style/prompts/`.

```text
…
```

## Must have

- …

## Must not have

- …

## Acceptance criteria

Claude checks these.

- [ ] …

## Delivery

Written by `tools/images`. Files go to `art-source/raw/<ID>/`, unmodified, with
`receipt.json` next to them.

| Round | Date (UTC) | Files | Model | Size / quality | Cost (USD) |
|---|---|---|---|---|---|

## Review

Filled in by Claude and the operator. Write the pick as `**accepted: vN**`
(INDEX.md reads it), `**revise**` with numbered notes, or `**rejected**`.

| Round | Date (UTC) | Verdict | Notes |
|---|---|---|---|
