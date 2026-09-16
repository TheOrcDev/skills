# Body plans

Bone lists per family, as `scaffold_rig.py` builds them and `calibration.py`
expects them. Names are stable ASCII. `Root` is the stationary navigation
root in every family. Sole groups are the bones whose vertices count as the
contact patch.

## humanoid (25 bones, Unity Humanoid names, engineRig Humanoid)

```
Root
└── Hips
    ├── Spine → Chest → UpperChest → Neck → Head
    │   ├── LeftShoulder → LeftUpperArm → LeftLowerArm → LeftHand → Socket_Hand_L
    │   └── RightShoulder → RightUpperArm → RightLowerArm → RightHand → Socket_Hand_R
    ├── LeftUpperLeg → LeftLowerLeg → LeftFoot → LeftToes
    └── RightUpperLeg → RightLowerLeg → RightFoot → RightToes
```

Legs IK on the lower leg (2-bone chain), soles Foot + Toes. Sockets carry no
skin weight; equipment is skinned to the hand bone or seated with a grip.
Unity maps the Avatar with no rename table because the names are its own.

## mixamo-biped (provider skeleton, engineRig Humanoid)

`mixamorig:Hips, Spine, Spine1, Spine2, Neck, Head, HeadTop_End, Left/Right
Shoulder, Arm, ForeArm, Hand, HandMiddle1..4, UpLeg, Leg, Foot, ToeBase,
Toe_End` plus a `Root` the packager adds above `mixamorig:Hips`. Legs IK on
`mixamorig:LeftLeg` / `RightLeg`, soles Foot + ToeBase. Unity maps Humanoid
from `mixamorig:Hips` once the skeleton list is rebuilt from the model.

## quadruped (engineRig Generic)

```
Root
└── Spine → Head
    ├── Tail_01 → Tail_02 → Tail_03
    ├── Leg_L_Front_Upper → Leg_L_Front_Lower → Leg_L_Front_Foot   (x4: L/R, Front/Rear)
```

Optional `Jaw` (author_clips adds one when `calibration.addJaw` is set).
Gait trot or walk. IK on the lower leg, sole = foot.

## maw-quadruped (engineRig Generic)

Quadruped plus `Chest`, `Neck`, `Jaw_Upper` and `Jaw_Lower` under Head, and
`Back_Ridge_01..03`. Attack type `maw`, cast type `roar`. Walk gait with a
high duty factor for mass.

## hexapod (engineRig Generic)

```
Root
└── Thorax
    ├── Abdomen
    ├── Head
    │   ├── Mandible_L, Mandible_R
    │   ├── Antenna_L_01 → Antenna_L_02, Antenna_R_01 → Antenna_R_02
    ├── Leg_L_Front_Coxa → _Femur → _Tibia → _Tarsus   (x6: L/R, Front/Middle/Rear)
```

Alternating tripod gait. IK on the tibia (3-bone chain), sole Tarsus + Tibia.
Six-legged motion is required; a quadruped remap is a failure.

## octopod (engineRig Generic)

```
Root
└── Cephalothorax
    ├── Abdomen
    ├── Head → Fang_L, Fang_R
    ├── Leg_L_Front_Coxa → _Femur → _Tibia → _Tarsus   (x8: L/R, Front/FrontMiddle/RearMiddle/Rear)
```

Alternating tetrapod gait. Attack type `fang`, death type `curl`.

## winged-bat (engineRig Generic, mode air)

`Root → Spine → Chest → Head (Jaw, Ear_L, Ear_R)`, two four-bone wing arms
`Wing_{s}_Shoulder → UpperArm → Forearm → Wrist` with three membrane fingers
`Wing_{s}_Finger_01..03`, two three-bone legs `Leg_{s}_Upper → Lower → Foot`.
Locomotion is an in-place flap cycle; the engine supplies hover offset and
movement. Death lands and folds.

## winged-biped (engineRig Generic, mode air)

`Root → Pelvis → Spine → Chest → Neck_01 → Neck_02 → Head (Jaw)`, tail
`Tail_01..04`, wings as the bat but the wings are the only forelimbs, legs
`Leg_{s}_Thigh → Shin → Foot → Toe`. No separate arm chain.

## winged-humanoid (engineRig Generic, mode air)

Humanoid body chain `Root → Pelvis → Spine → Chest → Neck → Head`, two
clawed arms `Arm_{s}_Clavicle → Upper → Forearm → Hand`, two feathered back
wings `Wing_{s}_Shoulder → Upper → Forearm → Wrist` with `Wing_{s}_Primary_01..02`,
two taloned legs `Leg_{s}_Thigh → Shin → Ankle → Talon`, tail feathers
`Tail_Feathers_01..02`. Six limbs; keep arms and wings separate.

## Large bipeds

A large biped (ogre, troll, colossus) is a `humanoid` with
`calibration.proportions` overrides, or a `mixamo-biped` if the provider rig
holds. Exposed cores, rib cages or skull spikes are extra bones under Chest
or Head added through `calibration.extra` and weighted through
`forcedRegions`.

## Choosing engineRig

Humanoid only when the skeleton maps to Unity's Humanoid avatar (humanoid,
mixamo-biped). Everything else is Generic: clips bind by bone path, so the
hierarchy must not change between versions.
