---
name: unity-asset-integration
description: Installs and verifies Final Stand 3D model packages or animation updates through the repository's Unity importers, presentation profiles and prefab installers. Use when deploying an accepted model, wiring its materials or presentation, validating imported clips, or checking that an installed unit appears correctly in gameplay.
---

# Unity asset integration

Install the exact validated artifact and prove that Unity uses it correctly. Read [WORKFLOW.md](WORKFLOW.md) for the two supported installation routes and their verification commands.

## Select the route

- Read the coordination board and claim the subject's exact model, material, data, prefab and evidence paths, including any shared catalog changes. Use the actual Git checkout and inspect dirty state before installation.
- Read `ArtSource/3D/Roster/subjects.json`, the applicable generated manifest, `GeneratedModelImportRules.cs` and `GeneratedModelPrefabInstaller.cs`. Derive paths and rig type from those contracts; subject IDs and display-folder names differ.
- For a complete new accepted package, use `tools/3d/deploy_accepted_model.py` followed by the subject installer.
- For an animation-only candidate produced by the existing creature/humanoid pipeline, use `tools/3d/animation_quality/creatures/unity_install.py` with its subject, plan and version. It replaces the production FBX while retaining textures and verifies exact imported clip coverage.
- These routes target roster models. Terrain and VFX use their own installers and plan contracts; do not route unrelated assets through a unit installer.

## Integration checks

1. Verify source hashes and fresh technical audits before copying. Record the current production hash/commit and preserve any uncommitted overlapping work before replacement. Missing or stale evidence returns to cleanup/export rather than being patched to say PASS.
2. Coordinate exclusive use of the Unity project. Resolve the editor from `ProjectSettings/ProjectVersion.txt` and the installed toolchain. Wait for another agent's editor rather than terminating it or removing its lock.
3. Let repository import rules enforce scale, axis conversion, rig/avatar mapping, exact clip names/ranges, loop flags, root motion and texture settings. Inspect Unity's imported result, not only the source file.
4. Use the material builder's channel mapping: Base Color is color data; masks are linear data; normal textures require normal-map import. Do not infer that every packed provider texture already matches the shader's mask layout.
5. Verify the generated animation profile, controller, visual profile, model prefab and death echo reference the intended version. Preserve existing ability-animation and locomotion-rate integrations when rerunning the installer.
6. Verify gameplay binding independently of the isolated gate prefab. Preserve network identity, gameplay components, pooling behavior and the existing sprite fallback policy. Do not change stats or abilities as a side effect of an art install.
7. Run focused native tests and inspect the actual model at gameplay distance for orientation, feet/ground contact, texture appearance, equipment sockets, action readability and death/reset behavior.

## Completion evidence

Report deployed hashes, source and installed versions, Unity exit codes, test totals/failures, clip coverage and visual captures. A successful file copy is not a successful Unity import; a technical import PASS is not operator art acceptance.

Keep `source validated`, `installed`, `tests passed` and `operator review` distinct in the current plan's evidence schema. Commit only owned or claimed paths, inspect generated `.meta` changes, and leave unrelated Unity settings untouched. Record the slice outcome on the board.
