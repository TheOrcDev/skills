# Pitfalls

Each one cost a rework. Read before blaming the mesh.

- **Weight transfer with a posed mesh.** Either mesh posed produces garbage weights. Unbind actions, set the armature to REST, then transfer.
- **Bone-parented rigid parts.** Blender pivots on the bone tail, FBX on the head. The part drifts after a round trip. Skin it 100% to one bone.
- **Weapon continuing the forearm.** Skinning it where the modeler left it seats nothing. Use a grip rule across the fist.
- **Rotation-only retargeting.** Provider presets push soles under the floor on other proportions, and each foot follows its own path. Clamp, plant, then lock, in that order.
- **Treadmill walks.** Preset walks imply 0.2 to 1.5 u/s; heroes move at 7. Record nominal speed, bind the rate at runtime, never scale keys.
- **Sinking deaths, hitching idles.** Provider defects. Death hold and loop blend in the package.
- **Ground clamp with long arms.** The clamp lifts the whole body to keep arms out of the floor. Hand guard first.
- **Empty jaw groups, torn sleeves.** Bone heat fails there. Force the region from the contract.
- **Root with skin weights.** Redistribute to the bones that own the region before authoring.
- **24 fps presets.** Resample by evaluating poses at 30 fps.
- **Mixamo knee twist.** Shows as 0.1 to 0.2 units of ankle drift on dense subframes. Forward knee hinges during the foot lock.
- **Judging the authoring scene.** Export, reimport into an empty scene, then measure and render.
- **Rigid parts and the floor gate.** They are excluded. Look at the frames; a `down` grip buried a club 15 cm while every gate passed.
- **Hidden parts in the review camera.** A staff behind the body, thighs glued together. Render front and side.
- **Quadruped presets.** Most providers offer only a walk. Author creature gaits.
- **Axis double-apply.** Blender is Z up, the export is Y up +Z forward. Verify the reimport, never rotate twice.
- **Actions in Blender 4.5.** They need an explicit action slot or nothing plays.
- **Passing gates as acceptance.** Screening only. The reviewer sees the reel.
- **Automatic LOD or compression on the proof mesh.** Off until the base is accepted.
