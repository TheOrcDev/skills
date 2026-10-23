---
name: art-requests
description: Generates every game image through a request file, so each picture traces back to its prompt, model, references and cost. Runs GPT-6.1 Sol through Codex (free on a ChatGPT plan) or GPT Image through the Vercel AI Gateway, keeps raws immutable, writes receipts and a spend ledger, refuses to pass a plan's budget, and records which variant won and why. Use when the user wants a background, a then-edit, a close-up, an NPC painting, an item sheet, a model sheet, animation paintings or UI art; when running, reviewing, revising or accepting an IMG-#### request; when checking image spend or budgets; or when they mention tools/images, Sol, Codex images, gpt-image, the gateway, receipts or the ledger.
---

# art-requests

An image model makes pretty pictures. A game needs pictures it can trace,
repeat and pay for. This skill never generates an image outside a request
file: the request holds the purpose, the prompt and the acceptance criteria,
the tool writes the raws and the receipt, and the review table says which
variant won and why.

Read [RULES.md](RULES.md) before the first request. Run
[WORKFLOW.md](WORKFLOW.md) commands as written, from the repository root.

## The loop

```
spec or template -> request (status: open) -> run -> raws + receipt + ledger + Delivery row
                                                                 |
          accepted: vN  <-  review against the criteria  <-------+
                                  |
                                  +-> status: revise, numbered notes -> run again (v4, v5 ...)
```

1. **Write the request.** From a spec and a shared preamble
   (`bun tools/images/new-request.ts specs.json`, schema in
   [templates/specs.json](templates/specs.json)), or by hand from
   [templates/request.md](templates/request.md) for one-offs.
2. **Pick the engine** in the Generation block's `model`.
3. **Dry-run** to see the cost and the budget check, then **run**.
4. **Review** the variants against the acceptance criteria. Measure what can
   be measured (`adv-art align` for then-edits, a contact sheet for picks).
5. **Record the verdict** in the Review table: `**accepted: vN**` with why,
   or `**revise**` with numbered notes and `status: revise`.
6. **Rebuild the index**: `bun tools/images/index.ts`.

## Engines

| | Sol | Gateway |
|---|---|---|
| `model` | `codex/gpt-6.1-sol` | `openai/gpt-image-2.5-flare` (new images), `openai/gpt-image-2.5-sunburst` (edits), `openai/gpt-image-2` (fallback) |
| Size | Fixed by Sol: landscape came back 1672×941 and portrait 1024×1536 in Past. `size` only sets the shape | Exact: multiples of 16, aspect 1:3 to 3:1, edges up to 3840 |
| Mask | No | Yes |
| Cost | $0 on the operator's ChatGPT plan | Billed per token, about $0.028 for a medium 2560×1440 image |
| Use for | Rooms, then-edits, close-ups, NPCs, item sheets, model sheets, painted animation | Masks, exact sizes such as 3:1 vista rings, and anything Sol fails twice |

## Quick start

```sh
bun tools/images/new-request.ts art-source/work/specs/area-1.json   # prints IMG-#### slug per spec
bun tools/images/run.ts IMG-0012 --dry-run                          # cost estimate and budget check
bun tools/images/run.ts IMG-0012                                    # raws, receipt, ledger, Delivery row
tools/adv-art sheet --out build/review/IMG-0012.jpg --columns 3 \
  art-source/raw/IMG-0012/IMG-0012-v1.png:v1 art-source/raw/IMG-0012/IMG-0012-v2.png:v2
# edit the Review table: | 1 | <UTC> | **accepted: v1** | why v1, what the others got wrong |
# then set status: accepted
bun tools/images/index.ts
```

## Statuses

| Status | Means | Set by |
|---|---|---|
| `open` | Written, never run | The writer |
| `delivered` | A round ran; review pending | `run.ts` |
| `revise` | Reviewed, another round wanted; notes say what to change | Claude |
| `accepted` | One variant passes; the Review row names it as `**accepted: vN**` | Claude, or the operator |
| `rejected` | Nothing usable and no further rounds | Claude, or the operator |
| `cancelled` | Never run, no longer needed | Claude |

`run.ts` only runs `open` or `revise` requests.

## Per-request checklist

1. Purpose names where the image is used in the game and what it must do there.
2. `plan` names the plan that pays; `tools/images/budgets.json` has its budget, or the request costs $0.
3. References exist on disk (the parser refuses missing files); edits list the image to edit first.
4. Prompt comes from the matching preamble in `art-source/style/prompts/`, or says why not.
5. Must have, must not have and acceptance criteria are concrete enough to check.
6. Dry run passes the budget check.
7. Review row written with the pick and the reason; status updated; index rebuilt.
8. Accepted style keys and landmark crops copied into `art-source/style/` (never moved out of `raw/`).

## Next

- The first images of a game: [look-gate](../look-gate/SKILL.md).
- Rooms from accepted images: [paint-room](../paint-room/SKILL.md).
- NPC paintings: [skinned-npc](../skinned-npc/SKILL.md). Hero sheets: [painted-hero](../painted-hero/SKILL.md).
