# Polish passes (package_biped.py)

Provider clips are retargeted rotation-only onto a skeleton whose
proportions differ from the human the preset was captured on. Every pass
fixes one consequence in the package. Order matters. Every pass writes its
numbers into the receipt.

| Order | Flag | What it does | When |
|---|---|---|---|
| 1 | `--posture-relax Clip=k` | Blend spine, neck and head toward rest by k so a hunched preset keeps the head visible | Hunched idles and walks |
| 2 | `--leg-splay <rad>` | Swing each upper leg outward about the forward axis (sign from the rest pose, soles counter-rotated flat) so a wide body does not walk with thighs glued together | Brutes, short splayed legs |
| 3 | `--ground-clamp` | Per-frame hip lift so the lowest body vertex rests on the floor; rigid parts excluded; smoothed with an element-wise max so nothing sinks | Always on ground bipeds |
| 4 | `--plant-feet` | Horizontal hip shift so the mean planted-foot motion is one uniform treadmill; records the resulting nominal speed | Always for Locomotion |
| 5 | `--lock-feet` | Leg IK pins each planted ankle to that treadmill at the stance's lowest height with the sole and toe orientation of that frame, faded over 4 swing frames, then a second clamp; lowers the pelvis by a clip-wide constant when splayed legs cannot reach | Always for Locomotion; must follow plant-feet |
| 5a | `--forward-knee-hinges` | Lock Mixamo knees to a forward hinge during the foot lock (requires `--lock-feet`, two-bone Mixamo chains only) | Ankle drift on dense subframes |
| 6 | `--hand-guard` | After a hands-excluded clamp: a small hand penetration bends the elbow, a large one swings the whole arm about the shoulder in its own vertical plane, biased outward, then a final full clamp | Long arms, slams, deaths |
| 7 | `--post-lock-loop-blend N` / `--post-lock-cycle-correction` | Loop cleanup after the foot lock changed the poses | When the lock reopened a seam |
| 8 | `--loop-blend N` | Ease each looping clip's tail into its first pose over N frames | Always (6) |
| 9 | `--death-hold <s>` | Append a held final pose | Always (0.6; 1.5 for presets that reach the ground late) |

Grips: `--grip Part=bone,fraction,up|down` or the contract's rigidParts.
Shields stay rigid on the forearm without a grip. Check rigid parts in the
frames; they are outside the floor gate.

Robed bodies: set `calibration.soleWeightThreshold` to 0.85 so the hem does
not count as the sole.
