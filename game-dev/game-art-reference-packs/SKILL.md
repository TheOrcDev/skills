---
name: game-art-reference-packs
description: Creates and validates Final Stand concept turnarounds and deterministic four-view upload packs with source lineage. Use when preparing or correcting front, left, back and right references for a unit or a Meshy generation request; provider transactions belong to meshy-asset-production.
---

# Game art reference packs

Produce four unambiguous views of the same subject, with complete anatomy and equipment, plus a review contact sheet and verifiable source hashes. Read [WORKFLOW.md](WORKFLOW.md) for the preparation commands and output locations.

## Resolve the contract

- Read the repository coordination board before editing; claim paths outside the agent's ownership. Work from a real Git checkout containing the source images, not a slim workspace that only mirrors documentation.
- Resolve the exact subject in `ArtSource/3D/Roster/subjects.json`: source type, rig class, anatomy, equipment, surface identity and turnaround lineage. A Blender variant may reuse its base instead of requiring new references.
- The three original proof subjects retain `ArtSource/3D/Meshy/manifest.json` and Plan 002A governance until that plan closes. Other unit packs use `tools/prepare_roster_reference_packs.py` and its generated roster manifest. Follow recorded plan decisions rather than an old status paragraph.
- Reuse accepted references first. If new bitmap art is needed, use the available image-generation skill/tool and preserve its exact prompt, source references, output and hash. Skill invocation alone does not authorize a new provider spend.
- These preparers understand unit contracts. For terrain, props or VFX, first locate that plan's reference schema and tooling; do not invent a roster entry just to use a unit preparer.

## Reference decisions

1. Keep front, left, back and right views consistent in proportions, palette, limb count, equipment handedness and rest pose. Use a neutral backdrop with clean figure boundaries and no neighboring subjects in upload images.
2. Include complete feet, ears, horns, tails, wing tips and weapon heads. Keep long silhouettes within their own panel and leave margin around the extremities.
3. Distinguish actual materials: organic hide, fur, feathers and keratin should not acquire stone or metal surfaces unless the contract calls for them. Preserve small identity cues visible at the gameplay camera.
4. Derive the pack with the repository preparer. The standard unit output is four 1024-square PNGs. Do not hand-edit generated PNGs to bypass the source record or checker.
5. Inspect all four crops and the contact sheet visually. Segmentation can assign crossing wings or weapons to the wrong panel; use the registry's crop overrides when needed, then regenerate.
6. Mirror a side only when the subject is actually symmetric and its contract permits it. Asymmetric armor, shields, weapons and markings need a true opposite view.
7. Record technical readiness separately from operator art approval. A successful checksum check does not approve a new identity or anatomy change.

## Handoff

Deliver the subject ID, applicable manifest, four numbered views, contact sheet, receipt template, source hashes and review result. Call out unresolved cropping or identity issues. The upload mapping is Main → front, Left → left, Back → back, Right → right.

Continue with [meshy-asset-production](../meshy-asset-production/SKILL.md) only when generation is part of the user's request and its budget is authorized. The identity sheet and contact sheet are review aids, not multi-view uploads.
