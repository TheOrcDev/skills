# 001: Foundations, the kit's template as {{GAME_NAME}}

Status: TODO, written {{DATE}}. Owner: Claude. {{Say whether the operator
authorized commits and pushes for this plan.}}

## Goal

A reproducible Godot 4.7.2 project for {{GAME_NAME}}, set up from the
point-and-click-adventure kit's template. It runs the headless tests, exports a macOS build and
a browser build, and the greybox sample chain plays end to end in both.
Everything later builds on this.

## Where we stand

- {{What exists: an empty folder, reference concepts, an operator brief.}}
- Installed: {{the toolchain from the new-adventure skill's WORKFLOW.md §1}}.
- Not installed: {{anything missing}}.

## Slices

### Slice 0: Repository

1. `new_game.sh <dir> "{{GAME_NAME}}"` copies the template and the docs.
2. `git init -b main` and `git lfs install --local`, before the first commit.
3. Check `.gitattributes` (the LFS patterns in `technical-plan.md` §3) and
   `.gitignore` (`.godot/`, `build/`, `.env`, `node_modules/`, `.venv/`,
   `__pycache__/`, `.DS_Store`).
4. Add `origin` = `{{REPOSITORY_URL}}`, and check the account's LFS quota.
5. The operator writes `.env`. Agents never write `.env*` files.

### Slice 1: Engine and add-ons

1. Godot 4.7.2-stable and its export templates from the official release,
   checked against the release's SHA-512 sums.
2. `fetch_addons.sh`: Dialogue Manager 4.1.0 and GUT 9.7.1, checksums checked.
3. `tools/godot.sh --version` prints `4.7.2.stable`, and
   `tools/godot.sh --headless --import` finishes with no errors.

### Slice 2: Name and settings

1. `project.godot`: the name, the description, the boot splash colour.
2. Export presets: macOS (universal, ad-hoc signed for now) and Web
   (single-threaded). Executable names follow the game's name.
3. `web/shell.html`: a first loading screen in the game's style, or the kit's
   plain one until plan 002 has art.

### Slice 3: Tests and builds

1. `tools/test.sh` passes: import, GUT, lint.
2. `tools/build/export.sh macos`, then `--qa=greybox` in the app passes.
3. `tools/build/export.sh web`, `bun tools/build/serve.ts`, then
   `bun tools/build/browser-qa.ts greybox` passes with no console errors.
4. Evidence in `docs/qa/001/`.

### Slice 4: Docs

1. Fill the `{{PLACEHOLDER}}` prompts in `AGENTS.md`, `docs/game-design.md`,
   `docs/technical-plan.md` and `docs/decisions.md` with the operator: name,
   premise, tone, look, platforms, repository.
2. Keep the inherited decisions unless the operator changes one; a change is a
   new row, never an edit.

### Slice 5: Close-out

1. Record any deviation from the technical plan in it.
2. Mark this plan DONE in `plans/README.md`.
3. Post on the board, in UTC.
4. The operator plays the greybox chain as the macOS app and in the browser.

## STOP conditions

- A checksum does not match. Stop.
- The pinned Godot or add-on version is not available. Stop and report the
  options. Never change a pinned version without the operator.
- The browser build will not start in Chrome. Stop and diagnose before adding
  content.

## Definition of done

- `tools/godot.sh --version` reports 4.7.2.stable, the add-ons are pinned and
  recorded, the headless import is clean, and `tools/test.sh` passes.
- The greybox chain prints `RESULT PASS` in the exported macOS app and in
  Chrome.
- The docs name the game and its inherited decisions.

## Effort

S: one working session.

## Execution record

{{Filled in when done: commits, versions verified, test counts, QA results,
deviations.}}
