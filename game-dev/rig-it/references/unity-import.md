# Unity import

What Final Stand's installer does with the production multi-take FBX, written
so you can do it by hand or in an editor script.

## ModelImporter settings

- `animationType`: Human when the contract's engineRig is Humanoid, Generic otherwise. `avatarSetup`: CreateFromThisModel.
- `importAnimation` true, `animationCompression` Off, `resampleCurves` false. Compression hides seams the gates found.
- `materialImportMode` None; build the material from the textures you deployed (URP Lit: BaseColor, Normal, packed metallic-smoothness Mask).
- `isReadable` false, `meshCompression` Off, normals Import, tangents CalculateMikk.
- Clips: one per take, names equal the semantic clip names. Idle and Locomotion loop time on with loop pose off; one-shots do not loop. Bake root transform position and rotation into pose; Apply Root Motion off on the Animator.

## Humanoid avatar

- `humanoid` family: the scaffold's names are Unity's Humanoid names (Hips, LeftUpperLeg, Spine, Chest, UpperChest, Neck, Head, LeftShoulder, LeftUpperArm, LeftLowerArm, LeftHand, LeftToes and the right side). Set `humanDescription.human` explicitly to that list with default limits so the mapper does not guess.
- `mixamo-biped` family: the mapper detects `mixamorig:Hips` and maps the Humanoid bones to the Mixamo names; rebuild the importer's skeleton list from the model, the stored list may still name the old scaffold bones.
- The avatar must validate with no warnings. A Generic import of a Mixamo skeleton works (clips bind by path) but loses retargeting.

## Animator

- Parameters: `Speed` float, triggers for BasicAttack, Cast, Hit, Death. A 1D blend tree Idle to Locomotion on Speed, or a single Locomotion state whose playback rate is bound.
- Locomotion rate = `moveSpeed / nominalSpeedUnitsPerSecond` from the receipt, clamped (0.5 to 4). Set it on that state only. A global animator speed changes attack timing and is wrong.
- Hit interrupts attack and cast. Death is terminal until the object returns to its pool. Unsupported semantics return false at the driver instead of aliasing.
- Facing is set by gameplay; navigation owns world movement.

## Verification

- Play every clip on the installed prefab in a test scene at the gameplay camera distance. Rendered reels prove the package; the engine proves the install.
- Editor tests worth having: avatar validates, every required clip exists with the expected length and loop flag, root motion disabled, source FBX hash matches the receipt.

## Godot

Import the same FBX (or GLB via `export_fbx.py --glb`). Use a Skeleton3D with an AnimationPlayer; Root stays stationary; scale the Locomotion animation speed on the AnimationTree by move speed over nominal speed. Humanoid retargeting needs a BoneMap to the SkeletonProfileHumanoid; the `humanoid` family maps by name.
