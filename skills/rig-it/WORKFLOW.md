# rig-it workflow

Blender 4.5 LTS headless. Every Blender script is invoked as

```sh
$RIG_IT_BLENDER --background --factory-startup --python-exit-code 1 --python scripts/<script>.py -- <args>
```

`pipeline.py` wraps export, review and reel (and author or package) into
versioned directories: `<work>/<subjectId>/v<N>/candidate` and `.../evidence`.
It refuses to overwrite a version.

## A. Contract and inspection

1. Copy `templates/rig-contract.json` (creature) or `templates/rig-contract.biped.json` (biped). Set `family`, `engineRig`, `requiredClips`, `source.model`, `source.textures`, `rigidParts`, `moveSpeedUnitsPerSecond`. Override calibration only where the species needs it (gait timing, attack type, death type, jaw).
2. `python3 scripts/contract.py rig-contract.json` prints the family, mode and every bone the tooling expects.
3. `inspect_model.py --input <model> --contract <json> --output inspect.json`. Fix missing bones, unweighted vertices, wrong facing or a floating floor before going further.

## B. Creature route (scaffold + authored clips)

1. `scaffold_rig.py --contract --input <clean mesh> --bind --output-blend --receipt`. Bone placement comes from the mesh bounds by family; add `calibration.landmarks` to pin joints where the silhouette disagrees with the default fractions. `--strip-existing-rig` rebuilds over a mesh that already carries a rig.
2. Read the receipt: unweighted before and after, fallback count, per-bone vertex counts. A bone with zero vertices is a bone in the wrong place.
3. `pipeline.py --contract --version N --source <rigged blend> --stage author --render keys`, look at the contact sheet, adjust calibration, repeat. Then `--stage all --render all`.

## C. Biped route (provider rig + preset motions)

1. `rig_input.py --contract --input <production fbx> --output <RigInput.glb>`: body only, rest pose, preview material from the production textures, rigid parts excluded. Refuses to overwrite a submitted input.
2. Provider rig. Meshy web: upload the GLB privately with texture and UV kept, Animate, Rig Humanoid at the model height, check markers (chin at the mouth, groin at the crotch), add one preset per semantic, download FBX with the Mixamo template, all added animations, with skin, 30 fps, one file per motion. mixamo.com: upload the GLB or FBX, auto-rig, download each motion as FBX with skin, in place off (the packager strips travel). Verify the added list before every download; adds fail silently.
3. Archive the raw export as immutable input. Unzip beside it.
4. `package_biped.py --contract --raw <dir> --production <fbx> --output <candidate> --map <rawSuffix>=<Semantic> ... [polish flags]`. Start with `--ground-clamp --plant-feet --lock-feet --loop-blend 6 --death-hold 0.6`; add `--posture-relax`, `--leg-splay`, `--hand-guard` when the frames or gates say so. Grips come from the contract's rigidParts.
5. `pipeline.py --stage export`, `--stage review --render all`, `--stage reel`.

## D. Review and iterate

- Read review.json before rendering everything (`--render none` is fast). Fix gate failures in the package or calibration, never in `gates.py`.
- Diagnose with the receipt (`maxIkResidualBodyHeights`, `worstPenetration`, `finalFrame.lowestVertexGroup`, pass records) rather than guessing.
- Render front and side views too: `review_clips.py --view front` and `--view side`.
- One version per attempt. Keep the passing version's frames out of git; the reels and review.json are the evidence.

## E. Engine

See [references/unity-import.md](references/unity-import.md). Import the production multi-take FBX, Humanoid or Generic per the contract, Apply Root Motion off, clips looped for Idle and Locomotion, Locomotion rate bound to move speed over nominal speed. Then run whatever tests the project has and send the reel.

## Environment

- `RIG_IT_BLENDER` (default `/Applications/Blender.app/Contents/MacOS/Blender`).
- `RIG_IT_PILLOW_PYTHON` for `reel.py` when the system Python lacks Pillow. ffmpeg on PATH or at `/opt/homebrew/bin/ffmpeg`.
- Actions in Blender 4.5 need an explicit `animation_data.action_slot`; `blender_common.bind_action` does it.

## Fixture

`scripts/fixtures/make_mixamo_fixture.py --output <dir>` builds a synthetic
Mixamo-skeleton biped with a rigid staff, a production FBX, five deliberately
flawed 24 fps raw clips and a contract, so the biped route can be exercised
without a provider account. On that fixture the v2 recipe
(`--ground-clamp --plant-feet --lock-feet --loop-blend 6 --death-hold 0.6
--hand-guard --posture-relax Idle=0.3 --post-lock-loop-blend 4
--post-lock-cycle-correction`) leaves two marginal gates: planted-sole drift
2.3% against 2%, and Death floor penetration 1.6% against 1%. The synthetic
walk has no real stance phase to lock, so treat the fixture as a smoke test
of the passes, not as proof of a clean package. Real provider exports are
where the passes were tuned and where they pass.
