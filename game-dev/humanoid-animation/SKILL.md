---
name: humanoid-animation
description: Produce production animation sets for Final Stand humanoid heroes and enemies from Meshy's humanoid rig and preset motion library (Plan 011 route), then package, gate, preview and install them. Use when animating a humanoid subject (Thorgrim, Sylra, Ignis, Seraphine, Malachar, Rhazgar, skeletons, necromancer, ogres, trolls, demon vanguard, bone colossus), choosing Meshy presets for Idle/Locomotion/BasicAttack/Cast/Hit/Death, rigging a biped on Meshy, or when the user mentions humanoid animation, Mixamo, preset motions, Plan 011 or the Malachar pilot.
---

# Humanoid animation (Plan 011 route)

Meshy humanoid rig + preset motions → packaged onto the exact production mesh →
Plan 009 gates, reels, Unity Humanoid install → operator review. Read
[RULES.md](RULES.md) first; follow [WORKFLOW.md](WORKFLOW.md) step by step.
Creature (non-humanoid) work uses the `creature-animation` skill instead.

## Quick start (Malachar pilot shape)

```sh
# 1. body-only rig input (separate parts excluded)
Blender --background --factory-startup --python-exit-code 1 --python tools/3d/animation_quality/creatures/humanoid_rig_input.py -- \
  --input Assets/_Project/Art/Models/Generated/Malachar/malachar.fbx \
  --output ArtSource/3D/Meshy/Working/malachar/animation-011/Malachar_Plan010_RigInput.glb --exclude Malachar_Staff
# 2. Meshy in Chrome: upload (Private, keep texture/UV) → Animate → Rig Humanoid (height = model height) → add presets → Download
#    (fbx, Mixamo template, Animation: All Added, Single file off, With Skin, 30 fps) → archive the zip under ArtSource/3D/Meshy/Raw/<subject>/animation-011/
# 3. package + gates + reel
Blender ... --python tools/3d/animation_quality/creatures/humanoid_package.py -- --subject malachar --raw <unzipped dir> \
  --production Assets/.../malachar.fbx --output ArtSource/3D/Meshy/Working/malachar/animation-011/actions-v1 \
  --map Idle_02=Idle --map Walking=Locomotion --map mage_soell_cast=BasicAttack --map mage_soell_cast_3=Cast --map Hit_Reaction=Hit --map Dead=Death \
  --part Malachar_Staff=mixamorig:RightHand \
  --ground-clamp --plant-feet --lock-feet --posture-relax Idle=0.5 --posture-relax Locomotion=0.5   # polish passes, see RULES.md
# brute shape (ogre): add --grip Ogre_Club=mixamorig:RightHand,0.2,up --leg-splay 0.35 --hand-guard
# always: --loop-blend 6 --death-hold 0.6 (1.5 for Fall Down); sword: --grip Skeleton_Sword=mixamorig:RightHand,0.15,up; shield: --part Skeleton_Shield=mixamorig:LeftForeArm
python3 tools/3d/animation_quality/creatures/pipeline.py --subject malachar --version 1 --plan 011 --stage export
python3 tools/3d/animation_quality/creatures/pipeline.py --subject malachar --version 1 --plan 011 --stage review --render all
python3 tools/3d/animation_quality/creatures/pipeline.py --subject malachar --version 1 --plan 011 --stage reel
python3 tools/3d/animation_quality/creatures/unity_install.py --subject malachar --version 1 --plan 011
```

## Checklist per subject

1. Contract from `ArtSource/3D/Roster/subjects.json` (Cast only for casters); calibration entry in `calibration.py` derived from `MESHY_HUMANOID` with the subject's rigid parts.
2. Rig input: body only, rest A-pose, production textures as preview; weapons/quivers/pauldron props excluded and named for re-attachment.
3. Meshy rig with markers checked (chin, shoulders, elbows, wrists, groin at the crotch, knees, ankles); record task, cost, balance in the ledger.
4. One preset per semantic chosen for the role (see RULES.md); record exact preset names in the plan record.
5. Package, gate, reel; fix what the gates flag with the packager passes (`--ground-clamp`, `--plant-feet`, `--lock-feet`, `--posture-relax`, `--hand-guard`), never with thresholds. Non-human proportions (ogre: short splayed legs, long arms) need `--leg-splay` and `--hand-guard` too; upright heroes may need only the clamp.
6. Look at the frames from more than the review camera (front and side) before sending a reel: a held part can hide behind the body, and legs pulled under the hips read as glued together. Seat weapons with `--grip Part=bone,fraction,up|down` (the shaft crosses the fist, never continues the forearm); `up` avoids floor contact when the arm hangs.
6. Unity install through the project installer (Humanoid avatar from the Mixamo skeleton), generated-model EditMode tests, reel sent to the operator, commit with explicit paths.

## Do not

- Upload raw provider assets or anything but the derived body-only rig input; never publish to the Meshy community (Private license).
- Treat a technical pass as art acceptance, or reuse a preset for a role it does not read as (a sword swing is not a staff cast).
- Commit Unity meta/settings noise or another agent's dirty files; push through a separate worktree when the shared checkout is dirty.
