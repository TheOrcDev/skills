# Creature animation rules

## Source and rig
- Production source is `Assets/_Project/Art/Models/Generated/<Folder>/<subject>.fbx` plus its `Textures/`. Raw provider exports are immutable; every correction is a new versioned candidate under `ArtSource/3D/Meshy/Working/<subject>/animation-009/actions-v<N>/`.
- Keep the scaffold hierarchy (Unity rebuilds the avatar/controller/prefab on install). Adding bones (`Jaw`, `GroundRoot`) is fine; renaming or dropping bones is not.
- `Root` is a stationary navigation root: its skin weights move to the bones that actually carry the region (proportionally to the vertex's other bones, else nearest bone segment). Body motion lives on the body bone (`Spine`/`Thorax`/`Cephalothorax`/`Pelvis`).
- Sole patches (below the ankle) are hardened to the foot bone so contacts are rigid; strays elsewhere keep their weights.
- Rigid parts (crown, egg sacs) get surface weights from the mesh they sit on, never bone parenting (FBX pivots differ).
- Variants use their own accepted mesh and textures at the registry scale; weights transfer from the base rig by nearest surface.

## Locomotion
- Gaits per family: quadruped trot (diagonal pairs) or four-beat walk; hexapod alternating tripod; octopod alternating tetrapod; flyers flap with the beat kept above the ground. Stride is clamped to what every leg can reach (asymmetric reach around the rest ankle) with a small crouch.
- Foot cycle: stance moves the foot backward at exactly the implied speed; swing is a Hermite arc with matching end slopes and sine-squared clearance.
- Nominal speed is recorded per clip (units/s and body heights/s); no guessed gameplay speeds.

## Actions
- Idle: breathing, head look, tail/antenna/mandible secondary motion, continuous loop.
- BasicAttack: anticipation → strike → recovery; jaw opens ≥0.35 rad where a jaw exists and closes at the end; head yaw + twist at contact; contact marker is metadata only.
- Hit: directional recoil, feet planted (flyers dip and jolt wings).
- Death: quadruped collapse (legs splay, upper legs fold across, body sinks, roll onto the side); arthropod curl (legs fold up, body sinks, roll); flyer landing (wings droop by geometry to the ground, legs fold, head slumps as far as the ground allows); keel-over for bodies whose belly already rests on the floor. Death never returns toward idle and holds its final pose.
- Cast: keep the gameplay-defined telegraph (Broodmother spawn, Devourer roar); never change gameplay timing or damage.

## Gates (screening, not acceptance) — `gates.py`
floor penetration ≤1% h (per-vertex allowance: a vertex may sink to the feet plane or its own rest depth), region collapse ≤10% (Idle/Locomotion) / ≤30% (actions), loop seam ≤0.5% h with seam acceleration ≤1.6× interior, planted sole drift ≤2% h while traveling, swing clearance ≥3% h, stationary root, unit body scale, death drop ≥15% h or keel-over (≥0.5 rad, ≤10% rise) or flyer wings-down-and-still, weapon open/closed, clips distinct. Thresholds change only with an operator entry on the board.

## Evidence and status
- `docs/visual-qa/animation-quality/plan-009/<subject>/v<N>/`: `review.json` (every frame of every reimported clip), `preview/` (3 s per clip at 30 fps, loops without duplicate endpoint, one-shots hold), `README.md`, `unity-integration.json`, `unity/editmode-results.xml`. Frames stay untracked.
- Track each clip as candidate → technical-pass → visual-review → accepted/rework; native install and operator acceptance are separate columns. Variants are never accepted because their base passed.

## Coordination and spend
- Read and append to `docs/visual-qa/3d-gate/agent-coordination.md` (slim workspace) before and after every slice; claim paths outside your ownership.
- Meshy: only with a recorded ceiling; every transaction appended to `ArtSource/3D/Meshy/proof-ledger.json` with task id and balance before/after. Local Blender authoring costs nothing.
