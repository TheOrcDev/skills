# art-requests workflow

Run everything from the repository root, so Bun loads `.env`.

## 0. Once per machine and per game

```sh
codex --version                       # Sol needs the Codex CLI, signed in on a ChatGPT plan
cd tools/images && bun install && bun test && cd ../..   # tests use a fake codex and a fake model; no network
bun tools/images/check.ts             # gateway: models listed, credential set, credits; spends nothing
```

- `.env` holds `AI_GATEWAY_API_KEY` (the operator writes it). Without it,
  only Sol requests run.
- Put the plan's budget in `tools/images/budgets.json` (shape in
  [templates/budgets.json](templates/budgets.json)): plan id to USD. Only the
  operator sets a budget. A plan with only $0 Sol requests needs no entry.
- Check `art-source/.gdignore` exists, and decide on Git LFS for
  `art-source/raw/**/*.png` before volume art.

## 1. Write requests

**From specs** (the normal way once the preambles exist):

```sh
bun tools/images/new-request.ts art-source/work/specs/<batch>.json
```

- One spec or an array; see [templates/specs.json](templates/specs.json).
  Fields: `slug`, `title`, `kind`, `purpose`, `requested`, `references`, and
  optionally `n`, `model`, `size`, `background`, `fields`, `prompt`, `must`,
  `mustNot`, `criteria`, `plan`.
- `kind` names a preamble in `art-source/style/prompts/` (`now`, `then`,
  `closeup`, `npc`, `items`) whose `{field}` placeholders come from `fields`.
  Every placeholder must be given. `kind: "raw"` sends `prompt` as written.
- Defaults: Sol, `2560x1440`, `quality: high`, `n` 3 (2 for `then`),
  transparent background for `npc` and `items`.
- It takes the next free IMG number, writes
  `art-source/requests/IMG-####-<slug>.md` and validates it, so every
  reference must already exist. Write a then-spec only after its now image is
  accepted.
- Set `plan` in every spec.
- Generated requests say `operator-approval: not-required`. For a style key
  or a hero design round, change that line to `required` before running.
- The sample's IMG numbers and paths are placeholders: point references at
  the real accepted raws or `art-source/style/` copies.

**By hand:** copy [templates/request.md](templates/request.md) to
`art-source/requests/IMG-####-<slug>.md`, take the next number after the
highest in the folder, and fill every section.

## 2. Run

```sh
bun tools/images/run.ts IMG-0042 --dry-run   # what it would call, pricing, budget verdict; exits 3 if over
bun tools/images/run.ts IMG-0042
```

What it writes:
- `art-source/raw/IMG-0042/IMG-0042-v1.png` … untouched;
- `art-source/raw/IMG-0042/receipt.json`: one entry per round with model,
  size, quality, n, background, prompt, reference and file hashes, usage,
  cost and its source, warnings, and provider metadata (Sol: thread id and
  pixel sizes);
- one entry in `art-source/raw/ledger.json`;
- a Delivery row in the request and `status: delivered`.

Exit codes: 2 bad request or wrong status, 3 over budget, 4 no usable gateway
credential.

Sol takes about 40 s an image. Run requests in the background in batches; in
Past, Sol generated batch N+1 while Claude built the rooms of batch N.

## 3. Review

```sh
tools/adv-art sheet --out build/review/IMG-0042.jpg --columns 3 \
  art-source/raw/IMG-0042/IMG-0042-v1.png:v1 art-source/raw/IMG-0042/IMG-0042-v2.png:v2 \
  art-source/raw/IMG-0042/IMG-0042-v3.png:v3
# then-edits: measure each variant against the accepted now image
tools/adv-art align --fixed art-source/raw/IMG-0041/IMG-0041-v1.png \
  --moving art-source/raw/IMG-0042/IMG-0042-v1.png --report build/review/IMG-0042-v1-align.json
```

Look at the sheet; read each acceptance criterion; for edits, `align` exits
non-zero above p90 3 px.

## 4. Record the verdict

Append to the Review table (UTC timestamps):

```
| 1 | 2026-11-02T10:15Z | **accepted: v2** | Claude's pick. v2 ... ; v1 ... ; v3 ... |
```

Then set `status: accepted`. For a revise round:

```
| 1 | 2026-11-02T10:15Z | **revise** | 1. Floor too dark behind the walk line. 2. Door cropped at the right edge. |
```

Set `status: revise`, change the prompt to answer each note, and run again.
The next round's files continue the numbering. Use `rejected` when no round
will help, and say why.

When `operator-approval: required`, show the operator the sheet with your
pick; record their answer as a second row if they overrule.

## 5. After accepting

- Style keys and landmark crops: copy into `art-source/style/` (and
  `art-source/style/landmarks/`).
- Rebuild the index: `bun tools/images/index.ts`.
- Spend so far: `bun tools/images/budget.ts`. At 80% of a budget, `run.ts`
  refuses; stop and report to the operator.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `is "delivered"; set "status: revise"` | A round already ran | Review it first, then set `revise` for another round |
| `Sol can't take a mask` | A mask with a `codex/` model | Use `openai/gpt-image-2.5-sunburst` |
| `Sol generated no images` | Codex refused or timed out | Read `codex-events.jsonl` in the run's work folder under the system temp folder (`$TMPDIR/*-sol/IMG-####-*/`); retry once; after two failures use the gateway |
| `count` warning in the receipt | Sol made fewer than `n` | Review what came; ask again only if none pass |
| `VERCEL_OIDC_TOKEN: EXPIRED` | A pulled OIDC token lasts 12 h | Pull a fresh one, or give the game its own `AI_GATEWAY_API_KEY` |
| `file not found: <reference>` | A reference path is wrong or not accepted yet | Fix the path; write edits only after their source is accepted |
| The browser pack grew by hundreds of MB | Image scratch inside the project | Keep scratch in the system temp folder; check `.gdignore` files |
