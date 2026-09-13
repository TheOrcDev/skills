# Unity model installation workflow

Run in the real Unity checkout. Before installing, inspect the exact generated outputs and scope in `Assets/_Project/Editor/Art/GeneratedModelPrefabInstaller.cs`. It may update shared presentation/catalog data as well as the subject; coordinate those paths first.

## Route A: complete accepted package

Choose the subject and applicable manifest. Example for an original proof subject:

```sh
python3 tools/3d/deploy_accepted_model.py --subject giant_ant --manifest ArtSource/3D/Meshy/manifest.json
python3 tools/3d/deploy_accepted_model.py --subject giant_ant --manifest ArtSource/3D/Meshy/manifest.json --check
```

Use `ArtSource/3D/Roster/manifest.json` for roster subjects. The first command validates and writes the canonical model folder; `--check` verifies an already deployed payload and receipt, not a preview of a first deployment. It requires matching accepted audit, export and cleanup-report hashes and the supported BaseColor/Normal/Mask texture set. Resolve packing through the existing material tooling before deployment.

Set `FS_UNITY` to the installed editor matching the project, `FS_PROJECT` to this checkout, `FS_SUBJECT` to the subject ID and `FS_EVIDENCE` to its claimed evidence directory. Create that directory before invoking Unity. Import new sources in a completed editor process before sealing the clips in a second process, avoiding stale cached take ranges:

```sh
"$FS_UNITY" -batchmode -nographics -projectPath "$FS_PROJECT" -quit -logFile "$FS_EVIDENCE/source-import.log"
"$FS_UNITY" -batchmode -nographics -projectPath "$FS_PROJECT" -quit -executeMethod FinalStand.Editor.Art.GeneratedModelPrefabInstaller.InstallSubjectFromBatch -subjectId "$FS_SUBJECT" -logFile "$FS_EVIDENCE/install.log"
"$FS_UNITY" -batchmode -nographics -projectPath "$FS_PROJECT" -runTests -testPlatform EditMode -testFilter FinalStand.Tests.Art.GeneratedModel -testResults "$FS_EVIDENCE/editmode-results.xml" -logFile "$FS_EVIDENCE/editmode.log"
```

Inspect each process result before continuing. Check the installer completion message, compilation/import errors and actual XML test totals/result. An exit code alone does not establish that the intended tests ran.

## Route B: animation candidate update

Use the plan and version that actually passed its animation review. Examples of the supported invocation shape:

```sh
python3 tools/3d/animation_quality/creatures/unity_install.py --subject wolf --version 2 --plan 009
python3 tools/3d/animation_quality/creatures/unity_install.py --subject malachar --version 9 --plan 011
```

These are examples, not instructions to roll a subject back to those versions. Inspect the active plan and candidate receipts before selecting a version. `FINALSTAND_UNITY` overrides the wrapper's editor path when needed. Do not use `--skip-tests` to claim an installation verified.

The wrapper reads `Working/<subject>/animation-<plan>/actions-v<version>/exports/animation-manifest.json`, verifies the FBX hash, copies it to production, imports in separate Unity processes and writes `unity-integration.json` under the matching plan evidence directory. Inspect its clip coverage checks against the manifest: exact names, full frame span and loop flags. Preserve the previous source, including uncommitted edits; a recorded historical commit alone cannot recover uncommitted work.

## Gameplay and visual verification

The model installer creates both `PF_<Folder>_Model.prefab` and `PF_<Folder>_3DGate.prefab`. Check which prefab the production hero/enemy uses; proving only the gate prefab is insufficient for a gameplay install.

`GeneratedModelGameplayPrefabInstaller.InstallFromBatch` installs the shipping bindings as a group and can update mission pools. Inspect its full scope before using it for a single-subject request. Reuse an existing binding when possible and coordinate any broader changes.

Render with the current plan's capture tooling in a graphics-capable editor/player, using the normal gameplay camera. Verify intended Animator states and action transitions, equipment, ground contact, death echo, pooled reuse and sprite fallback where applicable. Use relevant existing PlayMode tests when those bindings or behaviors changed. Do not launch a competing Unity process to capture while installation/tests are running.

Inspect the final diff and hashes. Keep required asset metadata and intended catalog changes; exclude unrelated settings/import noise without resetting another agent's files. Record technical and operator-review outcomes separately before committing the requested slice.
