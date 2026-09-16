---
name: rig-it
description: Rig and animate game characters that actually hold up in-engine. Contract-driven Blender pipeline with body-plan scaffold rigs for creatures, Mixamo-skeleton packaging for bipeds, rest-pose weight transfer, rigid part seating, numeric gates on a fresh reimport, rendered review frames and reels, Unity Humanoid/Generic export. Use when the user wants to rig a character, skin a mesh, build an armature, author or fix Idle/Locomotion/Attack/Hit/Death clips, package Meshy or Mixamo animations onto a production mesh, stop feet sliding or sinking, get a rig into Unity or Godot, or mentions rigging, skinning, weights, IK, gait, Mixamo, Meshy rig, Humanoid avatar, or invokes /rig-it.
---

# rig-it

Rigging fails in chat because the model writes one script, gets an armature
that binds, and never sees that the elbow is wrong. This skill never lets you
judge a rig from the code that built it. Every rig and every clip goes through
a contract, a family route, verified weights, numeric gates on a fresh
reimport, and rendered frames you look at before anyone calls it done.

Read [RULES.md](RULES.md) before touching a mesh. Run
[WORKFLOW.md](WORKFLOW.md) commands as written. Family bone lists live in
[references/body-plans.md](references/body-plans.md).

## The loop

```
contract  ->  route  ->  rig + weights  ->  clips  ->  export  ->  fresh reimport
   ^                                                                    |
   |                        polish passes (never thresholds)   <--  gates + frames
```

1. **Contract first.** Write `rig-contract.json` (schema in
   [templates/](templates/rig-contract.json)): family, engine rig type,
   required clips, rigid parts with sockets, gameplay move speed. Tooling
   reads it; tooling never redefines it.
2. **Route by body plan, not by wish.**
   | Body | Route | Scripts |
   |---|---|---|
   | Biped that a Mixamo-template rigger accepts (Meshy, mixamo.com) | rig input, provider rig, preset motions, package onto the production mesh | `rig_input.py`, `package_biped.py` |
   | Quadruped, hexapod, octopod, flyer, maw, winged hybrid, humanoid the provider mangles | deterministic scaffold rig from bounds, bind, author contact-driven clips | `scaffold_rig.py`, `author_clips.py` |
3. **Weights are verified, not assumed.** Automatic weights are a starting
   point. Unweighted vertices fall back to the nearest bone. Max 4 influences,
   normalized. Sole patches harden to the foot bone. Provider weights
   transfer onto the production mesh with both meshes in rest pose.
4. **Stationary navigation root.** `Root` carries no skin weight and never
   moves. Body motion lives on the body bone. Root motion is off in engine.
5. **Rigid parts** are skinned 100% to one hand bone and seated with a grip
   rule. Never bone-parented (FBX pivots differ).
6. **Export, then judge the reimport.** `export_fbx.py` writes one FBX per
   clip plus the production multi-take FBX. `review_clips.py` reimports each
   clip into an empty scene, measures every frame on real vertices, renders
   frames over a checker floor with the camera following travel, and runs
   `gates.py`.
7. **Fix in the package, never in the thresholds.** Provider walks slide,
   deaths sink, idles hitch. `package_biped.py` polish passes fix those in
   order. Gate thresholds change only with a recorded decision.
8. **Reel to the reviewer.** `reel.py` cuts labeled 3 s sections. A passing
   gate is screening, not art acceptance. The human signs off, the model
   does not.

## Quick start

```sh
# 0. environment
export RIG_IT_BLENDER=/Applications/Blender.app/Contents/MacOS/Blender   # Blender 4.5 LTS
S=<path to this skill>/scripts

# 1. contract + inspect
cp $S/../templates/rig-contract.json wolf/rig-contract.json      # edit family, clips, source, speed
$RIG_IT_BLENDER --background --factory-startup --python-exit-code 1 --python $S/inspect_model.py -- \
  --input wolf/wolf.fbx --contract wolf/rig-contract.json --output wolf/inspect.json

# 2a. creature route: scaffold + bind, then author
$RIG_IT_BLENDER ... --python $S/scaffold_rig.py -- --contract wolf/rig-contract.json --input wolf/wolf.fbx \
  --bind --output-blend wolf/wolf-rigged.blend --receipt wolf/rig-receipt.json
python3 $S/pipeline.py --contract wolf/rig-contract.json --version 1 --source wolf/wolf-rigged.blend --stage all --render keys

# 2b. biped route: body-only rig input -> provider rig + presets -> package
$RIG_IT_BLENDER ... --python $S/rig_input.py -- --contract mage/rig-contract.json --input mage/mage.fbx --output mage/rig-input/Mage_RigInput.glb
#   (rig on Meshy or mixamo.com, download Mixamo-template FBXs with skin, one per motion)
python3 $S/pipeline.py --contract mage/rig-contract.json --version 1 --stage package --raw mage/raw \
  --package-args "--map Idle_02=Idle --map Walking=Locomotion --map Spell=BasicAttack --map Hit=Hit --map Dead=Death \
                  --ground-clamp --plant-feet --lock-feet --loop-blend 6 --death-hold 0.6"
python3 $S/pipeline.py --contract mage/rig-contract.json --version 1 --stage export
python3 $S/pipeline.py --contract mage/rig-contract.json --version 1 --stage review --render all
python3 $S/pipeline.py --contract mage/rig-contract.json --version 1 --stage reel
```

Iterate as `--version 2`, `3`. The pipeline refuses to overwrite a version;
earlier versions are the trail.

## Per-subject checklist

1. Contract written and `python3 scripts/contract.py rig-contract.json` prints the required bones.
2. `inspect_model.py` shows zero unweighted vertices, every required bone, every rigid part, +Z forward, feet on the ground plane.
3. Clips authored or packaged; receipt has contacts and nominal speed for Locomotion.
4. `review_clips.py` gates pass. Look at the frames from front and side, not only the review camera. Held parts hide behind bodies; legs pulled under hips read as glued.
5. Reel sent to the reviewer. Record the version, the passes used, and the findings.
6. Engine install per [references/unity-import.md](references/unity-import.md): Humanoid avatar validates or Generic import binds by path, Apply Root Motion off, Locomotion rate bound to `moveSpeed / nominalSpeed`.

## Do not

- Judge a rig from the scene that authored it. Export, reimport, then judge.
- Raise a gate threshold to pass. Fix the package.
- Bone-parent a weapon. Skin it to one bone.
- Transfer weights with either mesh posed.
- Fake gameplay speed with a global animator speed.
- Claim art acceptance from a technical pass.
- Upload assets you do not own to a rigging provider, or publish them there.
