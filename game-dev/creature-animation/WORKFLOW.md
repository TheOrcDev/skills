# Workflow and environment

## Where to work
- Git checkout: an independent sparse clone of `git@github.com:TheOrcDev/finalstand.git` on `main` (the slim workspace has no `.git`; the board lives there). Never edit the shared gameplay-recovery checkout.
- Blender 4.5: `/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python <script> -- <args>`. Actions need an explicit `animation_data.action_slot`.
- Unity 6000.3.19f1 batch: `-executeMethod FinalStand.Editor.Art.GeneratedModelPrefabInstaller.InstallSubjectFromBatch -subjectId <id>` and `-runTests -testPlatform EditMode -testFilter FinalStand.Tests.Art.GeneratedModel` (both wrapped by `unity_install.py`). First import of a fresh checkout takes minutes; only one Unity per project at a time.
- FFmpeg has no drawtext; reels use Pillow via `/Users/orcdev/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.

## Pipeline stages (`pipeline.py`)
1. `author.py` — import FBX, redistribute Root weights, attach rigid parts, add jaw if calibrated, set up leg IK + sole solve, author clips, bake, save `<Folder>_Actions.blend` + `receipt.json` (contacts, IK residuals, worst penetration, final-frame diagnostics).
2. `export.py` — per-action FBXs (textures absolute, for review) + production multi-take FBX (takes = registry clip names), hashed `animation-manifest.json`.
3. `review.py` — fresh import per clip, per-frame metrics, traveling contact drift, renders over a checker floor (camera follows travel).
4. `reel.py` — labeled 3 s sections and full reel; `preview.json`.
5. `subject_report.py` — README with metrics, gates, status, notes.
6. `unity_install.py` — copy FBX, run installer, run tests, write `unity-integration.json` with rollback commit.

Iterate with `--trial <dir> --render keys`; build a contact sheet from `frames/` and look at it before trusting numbers. Diagnose with the receipt (`maxIkResidualBodyHeights`, `worstPenetration`, `finalFrame.lowestVertexGroup`) rather than guessing.

## Commit discipline
- One commit per slice/family with explicit paths: candidate dir, evidence files (not frames), the subject's FBX + meta, `Data/Presentation/Models/<Folder>`, `PF_<Folder>_*` prefabs, changed `.mat`, tooling, plan record.
- Revert Unity noise before committing: texture/model `.meta` whitespace rewrites, `Assets/DefaultNetworkPrefabs.asset`, `Assets/Settings/*`, `ProjectSettings/*` after builds. Never `git add -A`, stash, or reset over other agents' files.
- Fetch and rebase before pushing; push explicit slices; append the execution record to `plans/009-animal-creature-animation-rollout.md` and the board.

## Rat family special case
Gray Rat keeps the accepted Meshy 29-bone package (`rat_package.py` restores production scale and renames to registry semantics); Plague Rat and Rat King derive with `rat_variants.py`.
