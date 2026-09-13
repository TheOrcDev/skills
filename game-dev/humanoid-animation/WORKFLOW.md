# Workflow: Meshy humanoid presets to production

## A. Rig input
`humanoid_rig_input.py --input <production fbx> --output ArtSource/3D/Meshy/Working/<subject>/animation-011/<Folder>_Plan010_RigInput.glb --exclude <Part>...`
writes a body-only GLB (scaffold armature/weights removed, preview material from production textures) plus a JSON receipt. Refuses to overwrite a submitted input.

## B. Meshy (Chrome, `mcp__claude-in-chrome__*`)
0. Several subjects: upload and rig them all first (rigs run server-side in parallel), then add presets and download one at a time. The first Upload click after a page load opens nothing; a fresh tile shows an empty viewer until the page is reloaded and the tile clicked again; verify the Added list before every download (an add can silently fail).
1. `workspace?sidebar=animate` → Upload → drop the GLB via the dialog's `input type=file` (use `file_upload` on that ref; never click the picker), name it, Keep Original Texture and UV on, License Private, Continue. Verify with the asset search (name) that a tile exists; the first upload can silently produce nothing — repeat it.
2. Wait for the asset tile, select it, Rig → Humanoid → Next → Height = model height in metres → Next → check the markers (move the groin marker to the crotch, the chin to the mouth) → Confirm. Rig completes in ~2 min; a progress bar stuck at 90% is stale — reload the page and search the asset.
3. Preset choice per role, ogre reference: Combat Idle (exports as `Combat_Stance`), Slow Orc Walk, Heavy Hammer Swing, Hit Reaction, Dying Backwards. The rig auto-adds Walking and Running; leave them out of the `--map`.
4. Library search per semantic (idle / walking / running / mage spell cast / attack / hit reaction / dead). Click a card to preview on the rigged model, hover it and press its "+ Add" (use `find` for the Add button ref; the plain "Idle" card refuses, "Idle 1" works). Verify the Added tab with the search cleared.
5. Download (green button in the viewer toolbar): Format fbx, Skeleton template Mixamo, Rigged Character off, Animation All Added, Single file off, With Skin, 30 fps. The zip lands in `~/Downloads/Meshy_AI_<name>_biped.zip`; move it to `ArtSource/3D/Meshy/Raw/<subject>/animation-011/<label>/` and unzip beside it. Downloads need the operator's go-ahead.

## C. Package
`humanoid_package.py` (see SKILL.md): maps raw file suffixes to registry semantics, builds one rig with all clips, resamples to 30 fps, strips root travel, extracts walk contacts, transfers weights to the production body in rest pose, attaches parts, saves `<Folder>_Actions.blend` + `receipt.json`.

## D. Gates, reel, install, commit
- `pipeline.py --plan 011 --stage export|review|reel`, then `subject_report.py --plan 011` and `unity_install.py --plan 011`.
- Unity: `GeneratedModelPrefabInstaller.ApplyExplicitHumanoidMapping` detects `mixamorig:Hips` and maps the Humanoid bones to the Mixamo names, rebuilding the importer's skeleton list from the model (the stored list still names the scaffold bones). If another agent's Unity batch holds the project (`Temp/UnityLockfile`, "another Unity instance"), wait; never kill it.
- Iterate versions (`actions-vN`) for each polish attempt; the packager refuses to overwrite. Keep only the passing version's frames out of git; earlier versions are the iteration trail in the plan record.
- Read the review before rendering everything (`--render none` is fast); fix gate failures in the package, not in the thresholds.
- Send the reel to the operator; record preset names, costs and findings in `plans/011-humanoid-animation-meshy-presets.md`; commit candidate, evidence (not frames), Unity outputs and tooling with explicit paths; push from a clean worktree if the shared checkout carries someone else's edits.
