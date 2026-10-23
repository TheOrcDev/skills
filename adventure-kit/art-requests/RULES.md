# art-requests rules

Each rule cost Past a rework or saved it one. Numbers are Past's.

## Lineage

1. **Every image starts as a request file.** No prompt is sent from a chat or
   a scratch script. Why: 184 requests later, any picture in the game still
   traces to its prompt, model, references and cost, and can be regenerated.
2. **Raws are never edited, renamed or deleted.** `art-source/raw/IMG-####/`
   holds what the model returned, byte for byte, with `receipt.json`. All
   processing writes to `art-source/work/`; shipping files go into the Godot
   project. Why: the receipts hold sha256 hashes of every file and reference,
   and they back any AI-content disclosure a store asks for.
3. **A new round continues the numbering.** Round 2 of a request that made v1
   to v3 writes v4 onward. The tool refuses to overwrite a file. Why: the
   rejected variants are the trail that explains the accepted one.
4. **A failed or unusable round stays.** Mark it in the Review table; never
   remove its files.
5. **Accepted pictures that other requests reference get a stable copy.**
   Style keys go to `art-source/style/<name>.png` and landmark crops to
   `art-source/style/landmarks/`. Requests reference the copy or the raw path,
   never a work file that may change.
6. **The heading is `# IMG-#### — title`, with that dash.** The parser and
   `index.ts` read it. The verdict is written as `**accepted: vN**` in the
   Review table, because `index.ts` reads the last one to fill INDEX.md.

## Engines

7. **Sol makes most images.** `"model": "codex/gpt-6.1-sol"` runs
   `codex exec` in a read-only sandbox; the tool copies the PNGs Codex saved
   under `~/.codex/generated_images/<thread>/` into `raw/` untouched. Why: in
   Past, 336 of 360 generations came from Sol at $0, and its then-edits all
   aligned on the first round (p90 1.02 to 2.35 px).
8. **Sol's size is fixed.** Landscape is 1672×941 and portrait 1024×1536,
   whatever `size` says. Rooms upscale 1.15× with Lanczos to 1920×1080. Plan
   for it; do not fight it.
9. **Sol takes no mask.** A request with a mask runs on the gateway, or the
   tool throws.
10. **The gateway covers what Sol can't:** masks, exact sizes (3:1 vista rings
    at 3840×1280), and anything Sol fails twice. Flare makes new images and
    Sunburst makes edits (Past decision #28: Flare gave the more playable open
    floor; Sunburst held the reference composition closer).
11. **Sol may return fewer images than asked.** The tool records a `count`
    warning in the receipt. Review what came back; ask again only if nothing
    passes.
12. **Sol does exactly what the instructions say and nothing else.** It gets
    the prompt verbatim, makes `n` calls and writes no files. Do not ask it to
    edit, crop or organise anything.

## Money

13. **Every plan has an image budget in `tools/images/budgets.json`, in USD.**
    `run.ts` estimates high before calling and refuses when spent plus the
    estimate would pass 80% of the budget. At that point, stop and report to
    the operator. Why: the operator sets budgets, and an agent loop can spend
    fast.
14. **A $0 request needs no budget.** A plan without one can still run Sol
    requests, as long as it has spent nothing (Past plan 010: 25 Sol requests,
    75 images, $0).
15. **Never regenerate an accepted asset without a reason** written in the new
    request's Purpose.
16. **The ledger is the source of truth for spend.** `art-source/raw/ledger.json`
    gets one entry per call, with `costSource`: `gateway` (billed figure),
    `tokens`, `estimate` or `plan` (Sol). `budget.ts` reads it.
17. **Use a dedicated gateway key per game.** A Vercel OIDC token lasts 12
    hours and bills whichever project it came from; `check.ts` shows when it
    expires. A game's own `AI_GATEWAY_API_KEY` removes both problems.

## Review

18. **Claude accepts its recommended variant and writes down why.** The
    operator reviews results and can overrule any pick (Past decision #29).
    `operator-approval: required` means "show the operator the result", not
    "wait".
19. **The note names what the others got wrong.** For example: "v1 has the
    widest, lightest floor across the lower third and the door clear on the
    left. v2 crowds the foreground; v3 darkens the left edge." The next
    request learns from it.
20. **Measure before judging by eye where a number exists.** Then-edits pass
    `adv-art align` at p90 ≤ 3 px or go to a revise round. Picks between
    variants go on a contact sheet.
21. **A revise round lists numbered notes**, changes the prompt to address
    them, and keeps the same request ID. A different purpose is a new request.

## Project hygiene

22. **Scratch lives outside the project.** The Sol engine copies references to
    the system temp folder. Why: Sol's scratch copies once landed inside Past
    and Godot imported them, taking the browser pack from 143 MB to 304 MB.
23. **`art-source/` carries a `.gdignore`.** Godot must never import raws.
24. **Decide on Git LFS before volume art.** A Sol raw is about 3.5 MB; 50
    rooms came to 1.7 GB of raws in Past.
25. **Secrets live in `.env` and are never printed.** Bun loads it when the
    tools run from the repository root.
26. **Rebuild `INDEX.md` after every review.** It is generated; never edit it
    by hand. Past kept its board short by moving the request list there.
