# Cleanup and export workflow

Run from the real checkout with a working Blender executable. Inspect script arguments before use. Example variables below must identify the actual subject, manifest, immutable input and a new working directory:

```sh
FS_BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
FS_SUBJECT=giant_ant
FS_MANIFEST=ArtSource/3D/Meshy/manifest.json
FS_WORK=ArtSource/3D/Meshy/Working/giant_ant/cleanup-v2
```

For roster subjects use `ArtSource/3D/Roster/manifest.json` and the subject's own working path. Set `FS_INPUT` to the exact FBX or GLB from its recorded task. Do not use an arbitrary wildcard to pick a provider file.

## Raw audit and geometry cleanup

```sh
"$FS_BLENDER" --background --factory-startup --python-exit-code 1 --python tools/3d/audit_model.py -- --input "$FS_INPUT" --subject "$FS_SUBJECT" --manifest "$FS_MANIFEST" --output "$FS_WORK/raw-audit.json"
"$FS_BLENDER" --background --factory-startup --python-exit-code 1 --python tools/3d/prepare_cleanup_model.py -- --input "$FS_INPUT" --subject "$FS_SUBJECT" --manifest "$FS_MANIFEST" --output-blend "$FS_WORK/cleaned.blend" --receipt "$FS_WORK/cleanup-receipt.json"
"$FS_BLENDER" --background --factory-startup --python-exit-code 1 --python tools/3d/render_model_previews.py -- --input "$FS_WORK/cleaned.blend" --output-directory "$FS_WORK/previews" --material-mode source
```

`prepare_cleanup_model.py` also accepts a provider FBX ZIP; the audit tool accepts model files, not ZIPs. Keep the untouched archive and record which member is used. Its default triangle target is the contract midpoint; use `--target-triangles` only with an explicit in-budget target.

Inspect the source and cleaned model from front/back/left/right/hero views. Receipts report operations and measurements; use the raw audit to explain defects rather than accepting arbitrary repair magnitudes. Recompute body/equipment bounds after separation and verify grounded scale visually.

## Rigging handoff

Hand the cleaned scene and its material/equipment constraints to the relevant animation skill. Do not label scaffold/stub clips production-ready. Animation-only updates should follow that skill's versioned export route instead of rebuilding an accepted mesh from raw geometry.

## Export after the rig and clips are ready

Set `FS_SCENE` to the verified final animated blend. Set `FS_EXPORT` to a new candidate directory. Load the blend explicitly; these exporters operate on the open scene:

```sh
"$FS_BLENDER" --background "$FS_SCENE" --python-exit-code 1 --python tools/3d/export_accepted_model.py -- --subject "$FS_SUBJECT" --manifest "$FS_MANIFEST" --output-fbx "$FS_EXPORT/$FS_SUBJECT.fbx" --texture-directory "$FS_EXPORT/textures" --receipt "$FS_EXPORT/export-receipt.json"
"$FS_BLENDER" --background "$FS_SCENE" --python-exit-code 1 --python tools/3d/export_accepted_glb.py -- --subject "$FS_SUBJECT" --manifest "$FS_MANIFEST" --output-glb "$FS_EXPORT/$FS_SUBJECT.glb" --receipt "$FS_EXPORT/glb-export-receipt.json"
```

Reimport each export with `audit_model.py --accepted`. Only add `--coordinate-contract-confirmed` and `--root-motion-disabled` after checking those properties; they are attestations, not fixes. Verify missing/duplicate clips, loop/root behavior, bones, transforms, UVs, topology, textures and material limits. Use the animation pipeline's per-frame gates for deformation and contact behavior.

For the accepted-package deployment route, `deploy_accepted_model.py` expects `<subject>.fbx`, `textures/`, `accepted-audit.json`, `export-receipt.json` and `cleanup-report.json`. The cleanup report must truthfully attest the final output hashes under `acceptedOutputs`; the preparer's intermediate receipt is not a substitute. Keep raw, cleanup, export and visual acceptance evidence distinct.

If cleanup/export tooling changes, run its existing relevant tests, starting with `tools.tests.test_3d_asset_contract` and the changed tool's tests. For an asset-only change, audit and render the actual artifacts. Stage only the claimed accepted/working files and evidence when requested; append the slice result to the board.
