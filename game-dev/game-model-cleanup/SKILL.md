---
name: game-model-cleanup
description: Converts Final Stand provider meshes into budgeted, textured and verifiable game-model candidates using the existing Blender tooling. Use when repairing geometry, reducing polygons, separating equipment, correcting materials, normalizing transforms or preparing accepted exports; animation authoring uses the existing animation skills.
---

# Game model cleanup

Preserve the subject's identity while making its geometry and materials suitable for the production contract. Read [WORKFLOW.md](WORKFLOW.md) for the Blender commands and the distinction between cleanup and accepted export.

## Establish the source

- Read the coordination board, claim the exact output/tool paths, and use a Git checkout containing the subject's inputs and tooling. Inspect dirty state before any replacement.
- Start from a recorded provider candidate or the approved base of a local variant. Verify its source hashes and rejection/repair decisions. Raw provider exports remain immutable.
- Resolve budgets, required bones/clips, equipment and rig type through `ArtSource/3D/Roster/subjects.json` and the applicable generated manifest. The original three proof contracts remain under `ArtSource/3D/Meshy/manifest.json` until their governing plan closes.
- Prefer the source format with verified geometry and texture fidelity. A provider FBX ZIP may be cleaner than GLB, but compare their audits rather than assuming one is always superior.
- Never run the geometry-only cleanup preparer over an already animated production FBX as a routine update: it imports a fresh mesh scene and is not an animation-preserving round trip.

## Cleanup decisions

1. Audit the unmodified source. Inspect disconnected islands, duplicated internal surfaces, degenerate/non-manifold faces, UV seams, material assignments and transforms alongside multi-angle renders.
2. Save each repair attempt to a new working version. Use `prepare_cleanup_model.py` for the existing supported route and derive its target triangle count from the subject contract.
3. Distinguish coincident GLB vertices at UV/hard-normal seams from genuinely open geometry. The preparer welds appropriate GLB duplicates before bounded repair; do not fill thousands of seam edges as if they were holes or erase intentional anatomical openings.
4. Reduce geometry with silhouette and joint deformation in mind. Keep paws, fingers, jaws, wing membranes, mandibles and weapon grips readable. Meeting a polygon budget alone is insufficient.
5. Separate socketed equipment without inventing replacement anatomy. If the requested repair requires remodelling beyond the permitted scope, retain the rejected source and record the required exception; existing authorized repair decisions still apply.
6. Preserve UVs and texture channel meaning. Bake or resize copies to the contracted material/texture limits; inspect organic versus stone/metal surface identity under source-material lighting. Record any painted or procedural correction.
7. Normalize the export to metres, ground origin, Y-up and +Z forward with stable names and identity scale. Blender's working axes differ; verify the converted export rather than double-applying axis rotations.

## Finish the correct stage

A cleaned mesh is ready for rigging, not automatically a fully accepted animated unit. Use [humanoid-animation](../humanoid-animation/SKILL.md) or [creature-animation](../creature-animation/SKILL.md) for the required rig and clips. For local variants, preserve and validate the approved base rig/clip relationship.

After rig/animation work, export and independently reimport the exact FBX and GLB. Validate the active contract without weakening thresholds or passing evidence-confirmation flags by assumption. Keep technical PASS distinct from operator visual acceptance.

Deliver the versioned blend, source lineage, cleanup measurements, texture hashes, exports and fresh audits to [unity-asset-integration](../unity-asset-integration/SKILL.md). Preserve unresolved defects in the handoff instead of marking a partial package accepted.
