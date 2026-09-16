# Plan: `rig-it`, a game character rigging and animation skill

Status: BUILT 2026-09-16 (slices 0 to 5 done; slice 6, the stranger-mesh proof, still open). Source of truth for the method: the Final Stand
pipeline (`TheOrcDev/finalstand`, plans 008, 009, 011, 013, 016 and the six
project-local skills under `.claude/skills/`). Target: a portable skill in
this repo, installable with `npx skills add TheOrcDev/skills --skill rig-it`
and `npx shadcn@latest add TheOrcDev/skills/rig-it`.

## Why past models hit the wall, and what Final Stand did instead

A model asked to "rig this character" writes one bpy script, gets an armature
that technically binds, and has no way to see that the elbow is wrong. Final
Stand got 19 of 30 units to production animation by never letting the model
judge its own rig from code. Every rig and clip goes through:

1. A written contract per subject (rig class, required bones, clips, rigid
   parts and sockets, gameplay move speed, budgets), so the model builds to a
   spec instead of guessing.
2. A body-plan route, not one generic route: Meshy humanoid rig plus preset
   motions for bipeds; deterministic Blender scaffold rigs plus contact-driven
   gait authoring for quadrupeds, arthropods, flyers and hybrids.
3. Weights that are verified, not assumed: automatic weights are a starting
   point, unweighted vertices fall back to the nearest bone, sole patches are
   hardened to the foot bone, jaws and sleeves get forced regions when bone
   heat fails, and provider weights are transferred onto the production mesh
   with both meshes in rest pose.
4. A stationary navigation root with body motion beneath it; root motion off;
   rigid weapons skinned 100% to one hand bone and seated with a grip rule.
5. Numeric gates on a fresh reimport: floor penetration, planted-sole drift at
   the recorded nominal speed, loop seam, region collapse, death drop, swing
   clearance, stationary root, unit scale.
6. Rendered frames from more than one camera, contact sheets and labeled
   reels, looked at before any number is trusted.
7. Polish passes that fix provider defects in the package, never by loosening
   thresholds: ground clamp, plant feet, lock feet, posture relax, leg splay,
   hand guard, loop blend, death hold.
8. Engine install plus tests as the last gate, and a receipt for every step.

The skill packages that loop. The loop is the deliverable; the scripts are
how the loop runs without a human in it.

## Scope decisions (defaults chosen, flip any)

| Decision | Default | Alternative |
|---|---|---|
| Name | `rig-it` (matches `cut-it`) | `bone-it`, `game-rig` |
| Engine | Unity first-class (Humanoid avatar, Mecanim, root motion off), export contract generic FBX/GLB with Godot notes | Unity only |
| Scripts | Bundled Blender 4.5 headless scripts, generalized from Final Stand | Docs-only skill pointing at project tooling |
| Biped rig source | Any Mixamo-template skeleton: Meshy web rig (documented Chrome workflow) or mixamo.com free auto-rig; packager does not care which | Meshy only |
| Contract file | `rig-contract.json` per subject, schema shipped in the skill | Reuse Final Stand `subjects.json` shape verbatim |
| Runtime speed binding | Documented as an engine-side requirement with the Unity pattern; not automated | Ship a Unity C# snippet |

## Skill layout

```
skills/rig-it/
  SKILL.md                 route picker, contract, the verify loop, do-nots
  RULES.md                 every learned rule, engine-neutral wording
  WORKFLOW.md              headless Blender invocation, Meshy/Mixamo steps, Unity install
  references/
    body-plans.md          bone lists per family with Unity Humanoid mapping and sockets
    gaits.md               footfall sequences, stance/swing contract, nominal speed
    gates.md               thresholds table, what each catches, evidence layout
    polish-passes.md       each pass, its order, when it is needed, what it records
    unity-import.md        Humanoid mapping from mixamorig, Generic import, controller, rate binding
    pitfalls.md            sharp edges (below)
  templates/
    rig-contract.json      subject contract schema with a filled biped and quadruped example
  scripts/                 Blender 4.5, --background --factory-startup --python-exit-code 1
    inspect_model.py       hierarchy, bounds, facing, parts, unweighted verts, rest pose report
    scaffold_rig.py        body-plan scaffold from bounds and optional landmarks
    bind_weights.py        automatic + nearest-bone fallback + normalize + sole hardening + forced regions
    transfer_weights.py    provider skin to production mesh, rest pose enforced, max distance recorded
    seat_parts.py          rigid parts: 100% hand-bone skin, grip seating (bone, fraction, up|down)
    author_clips.py        semantic clip set on a scaffold rig with contact-driven gait
    polish_clips.py        ground-clamp, plant-feet, lock-feet, posture-relax, leg-splay, hand-guard, loop-blend, death-hold
    gate_clips.py          fresh reimport, per-frame metrics, PASS/FAIL JSON
    render_review.py       front/side/hero frames over a checker floor, contact sheet, reel
    export_fbx.py          multi-take FBX, Y-up +Z-forward, metres, receipt with hashes
```

## Pitfalls the skill must carry (each cost Final Stand a rework)

- Weight transfer with either mesh posed produces garbage. Unbind actions and set the armature to REST first.
- Bone parenting rigid parts breaks across FBX because pivots differ. Skin the part 100% to one bone.
- Skinning a weapon where the modeler left it makes the shaft continue the forearm. Seat it across the fist with a grip rule.
- Meshy retargets rotation only. Other leg proportions push soles under the floor, and no hip shift alone plants both feet. Clamp, plant, then lock, in that order.
- Preset walks are treadmills far slower than gameplay speed. Record nominal speed and bind the Locomotion rate at runtime. Never a global animator speed.
- Death presets sink through the floor and idles do not loop. Fix in the package.
- A ground clamp with long arms lifts the whole body. Run the hand guard first.
- Bone heat leaves jaw groups empty and tears layered sleeves. Force the region.
- The `Root` bone must not carry skin weights. Redistribute to the bones that own the region.
- Presets are 24 fps. Resample to 30 by evaluating poses, not by scaling keys.
- Imported Mixamo knees carry a twist discontinuity. Opt-in knee hinges removed 0.1 to 0.2 unit ankle drift.
- A passing gate is not art acceptance. The reviewer sees the reel; the model does not sign off.
- Judge the reimported FBX, never the scene that authored it.

## Slices

### Slice 0: recover the source tooling (blocked on a clone)
`~/projects/finalstand` is the slim workspace from 2026-09-06 with no git and
no `ArtSource/3D/Roster`, and the temp animation checkout is sparse. The
generalization targets exist only on GitHub:
`tools/3d/animation_quality/creatures/{author,gates,calibration,export,pipeline,humanoid_rig_input,humanoid_package,review,reel}.py`,
`tools/3d/{build_custom_rigs,author_custom_animations,asset_contract,audit_model,export_accepted_model,render_model_previews}.py`.

```sh
git clone --filter=blob:none --sparse git@github.com:TheOrcDev/finalstand.git /private/tmp/finalstand-rig-source
cd /private/tmp/finalstand-rig-source && git sparse-checkout set tools .claude/skills docs/3d-unit-production-contract.md plans
```

### Slice 1: docs first (SKILL.md, RULES.md, WORKFLOW.md, references)
Merge the humanoid and creature RULES into one engine-neutral rule set.
Replace Final Stand paths, plan numbers, agent names and the coordination
board with contract-file references. Write body-plans.md from
`asset_contract.py` required-bone lists and `build_custom_rigs.py` builders:
humanoid 25-bone with `Socket_Hand_L/R`, quadruped, hexapod, octopod, winged
bat, winged biped, maw quadruped, large biped, winged humanoid. Write
gates.md from `gates.py` thresholds. Verifiable: a fresh agent given only the
skill can state the route, required bones and clips for a wolf and a mage.

### Slice 2: inspect, gate, render (the loop without authoring)
Port `review.py`, `gates.py`, `render_model_previews.py` into
`inspect_model.py`, `gate_clips.py`, `render_review.py`. Contract-driven, no
subject registry. Verifiable: run against any Final Stand production FBX and
reproduce its recorded PASS/FAIL and drift numbers.

### Slice 3: biped route (Mixamo-skeleton packager and polish)
Port `humanoid_rig_input.py` and `humanoid_package.py` into
`transfer_weights.py`, `seat_parts.py`, `polish_clips.py`, `export_fbx.py`.
Document the Meshy Chrome workflow and the mixamo.com fallback in
WORKFLOW.md. Verifiable: the Malachar raw export repackaged through the skill
passes the same gates as actions-v2.

### Slice 4: creature route (scaffold and authored gait)
Port `build_custom_rigs.py` and `author_custom_animations.py` into
`scaffold_rig.py`, `bind_weights.py`, `author_clips.py`, with families as
data instead of one function per subject. This is the largest slice (2,200
plus 2,400 lines to generalize). Verifiable: wolf and giant ant scaffold,
bind, author, gate and render with results matching their v-latest receipts.

### Slice 5: Unity reference and registry
unity-import.md from `GeneratedModelPrefabInstaller` behaviour: Humanoid
mapping from `mixamorig:Hips`, Generic import when the contract says so,
Apply Root Motion off, locomotion rate = moveSpeed / nominalSpeed clamped.
Add the `registry.json` item and the README section in the repo voice.
Verifiable: `npx skills add` and `npx shadcn add` both install it.

### Slice 6: prove it on a stranger
Rig one character that is not from Final Stand (a free CC0 mesh) end to end
with only the skill. Every place the agent had to read Final Stand code is a
gap in the skill.

## Effort

| Slice | Estimate |
|---|---|
| 0 | 15 min |
| 1 | 3 h |
| 2 | 4 h |
| 3 | 6 h |
| 4 | 10 h |
| 5 | 2 h |
| 6 | 3 h |

Slices 1, 2 and 5 already give a usable docs-plus-verify skill. Slices 3 and
4 make it do the rigging.
