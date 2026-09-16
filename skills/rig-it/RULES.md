# rig-it rules

Every rule here cost a rework somewhere. Engine-neutral unless it says Unity.

## Source and contract
- The production mesh, its textures and any provider export are immutable inputs. Every correction is a new versioned candidate. Never run a geometry-only cleanup over an animated FBX and call it an update.
- `rig-contract.json` is the only authority for family, engine rig type, required clips, rigid parts, sockets and move speed. Tooling reads it and never redefines it.
- Units are metres, 1 engine unit = 1 m. Y up and +Z forward in the export; origin on the ground plane at the gameplay pivot. Blender works Z up; verify the converted export, never double-apply axis rotations.
- Mesh and bone names are stable ASCII. No provider task ids in runtime names.

## Rig
- Keep the scaffold hierarchy across versions. Adding bones (`Jaw`, `GroundRoot`) is fine; renaming or dropping bones breaks the engine avatar and every installed clip.
- `Root` is a stationary navigation root. Its skin weights move to the bones that actually carry the region, proportionally to the vertex's other bones, else nearest bone segment. Body motion lives on the body bone (Hips, Spine, Thorax, Cephalothorax, Pelvis).
- Automatic weights are a starting point. Unweighted vertices get the nearest bone. Max 4 influences, normalized. Bone scales positive and finite.
- Bone heat leaves jaw groups empty and tears layered sleeves. Force the region in the contract (`calibration.forcedRegions`) rather than hand-painting in a file nobody can rerun.
- Sole patches (below the ankle) harden to the foot bone so contacts are rigid. A robed body weights its hem to the foot bones too; raise `soleWeightThreshold` (0.85) so the review and the foot lock measure the sole, not the hem.
- Rigid parts (weapons, shields, crowns) are skinned 100% to one bone, never bone-parented: Blender pivots on the bone tail and FBX on the head, so a bone-parented part drifts after a round trip. Parts that sit on a deforming surface (crown on a skull, egg sacs on an abdomen) take surface weights from the mesh under them.
- Seat held parts with a grip rule: the fist's principal axes give finger direction, palm normal and knuckle line; the shaft runs along the knuckle line with the point at `fraction` from the handle end at the fist centre. `up` keeps a hanging arm's weapon out of the floor. Skinning a weapon where the modeler left it makes the shaft continue the forearm.
- Provider skins are welded copies with fewer vertices. Transfer their weights onto the exact production body by nearest surface **with both meshes in rest pose**: unbind every action and set the armature to REST first, or the mapping is garbage. Record the max surface distance.

## Motion
- Base locomotion blends Idle and Locomotion; semantic one-shots are BasicAttack, Cast, Hit, Death. Death is terminal and holds. Hit may interrupt attack or cast; nothing interrupts death. Unsupported semantics return false at the driver; they never alias to another clip.
- Locomotion travels: stance moves the foot backward at exactly the implied speed; swing is a Hermite arc with matching end slopes and sine-squared clearance (see `motion.py`). Record nominal speed per clip in units/s and body heights/s. Never guess gameplay speed.
- Gaits per family: quadruped trot (diagonal pairs) or four-beat walk; hexapod alternating tripod; octopod alternating tetrapod; flyers flap with the beat kept above the ground; bipeds alternate. Stride is clamped to what every leg can reach with a small crouch.
- Idle: breathing, head look, tail/antenna/mandible secondary motion, continuous loop. BasicAttack: anticipation, strike, recovery; jaw opens at least 0.35 rad where a jaw exists and closes at the end; head yaw and twist at contact. Hit: directional recoil, feet planted. Death: quadruped collapse to the side, arthropod curl, flyer lands and folds, belly-resting bodies keel over; never returns toward idle.
- Provider presets are 24 fps. Resample to 30 by evaluating real poses, not by scaling keys. Strip horizontal root travel (knockback, death slide) so clips are in place; extract foot contacts from the walk so drift can be measured.
- Provider walks are treadmills far slower than gameplay (1.2 u/s vs 7.1). Record the nominal speed and bind the Locomotion playback rate at runtime to `moveSpeed / nominalSpeed`, clamped. Never a global animator speed.
- Providers retarget rotation only. On other leg proportions the human leg angles push the soles under the floor and each foot follows its own path, so no hip shift alone plants both feet. Polish passes run in this order: `--posture-relax`, `--ground-clamp`, `--plant-feet`, `--lock-feet`, then `--hand-guard` after a hands-excluded clamp, then `--loop-blend` and `--death-hold`. See [references/polish-passes.md](references/polish-passes.md).
- Brute proportions (short splayed legs, long arms) need `--leg-splay` and `--hand-guard`. Without the guard a ground clamp lifts the whole body to keep long arms out of the floor (an ogre hopped 40 cm at its slam).
- Imported Mixamo knees carry a twist discontinuity that shows as ankle drift on dense subframes. `--forward-knee-hinges` (requires `--lock-feet`) removed 0.1 to 0.2 units of drift.

## Gates and evidence
- Gates are screening, never acceptance. Thresholds in `gates.py`: floor penetration 1% h, posture drop 10% (Idle/Locomotion) and 30% (actions), loop seam 0.5% h with seam acceleration at most 1.6x interior, planted-sole drift 2% h while traveling, swing clearance 3% h, stationary root, unit body scale, death drop 15% h or keel-over, weapon open/closed, clips distinct, no frozen mesh. Change a threshold only with a recorded decision.
- Judge the reimported FBX, never the scene that authored it. Rigid parts are not in the floor gate; check them in the frames (a `down` grip put a club 15 cm under the floor while every gate passed).
- Evidence per version: review.json (every frame of every clip), frames, preview reels, receipt, and what the reviewer said. Track each clip as candidate, technical pass, visual review, accepted or rework. Variants are never accepted because their base passed.

## Providers and rights
- Upload only a derived body-only rig input that you own, with separate parts removed. Keep the license private; never publish to a provider community.
- Record every provider task: id, settings, cost, balance before and after. Quadruped libraries at most providers offer only a walk; the biped route is for bipeds.
