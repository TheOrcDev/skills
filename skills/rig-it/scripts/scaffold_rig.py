"""Build a deterministic family scaffold rig on a mesh and optionally bind it.

Usage (Blender 4.5):
  Blender --background --factory-startup --python-exit-code 1 --python scaffold_rig.py -- \
      --contract rig-contract.json --input model.fbx|model.glb|model.blend \
      --output-blend out.blend --receipt out.json [--bind] [--strip-existing-rig]

Bone placement is driven by the deformable mesh bounds (the same fractions
the production builders use) and by the family in the contract:

  quadruped, maw-quadruped -> quadruped builder (maw adds Neck/Chest, the jaw pair and ridges)
  hexapod -> six-leg builder      octopod -> eight-leg builder
  winged-bat -> bat builder       winged-biped -> wyvern builder
  winged-humanoid -> harpy builder
  humanoid -> 25-bone Unity Humanoid scaffold with Socket_Hand_L/R
  mixamo-biped -> refused: that family is rigged by a provider and packaged, not scaffolded

`calibration.landmarks` ({boneName: {head:[x,y,z], tail:[x,y,z]}} in world
units) overrides the bounds placement per bone after the build.
`calibration.proportions.large: true` widens the humanoid scaffold for brutes.

--bind: automatic (bone heat) weights, nearest-bone fallback for every
unweighted vertex, `calibration.forcedRegions` (full weight for a box of the
bounds when heat leaves a region empty), max-4-influence normalisation, sole
hardening under each ankle, and rigid parts skinned 100% to their contract
bone. A scaffold is a starting point: deformation, joint placement and clips
still need review on the real mesh.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import blender_common as bc  # noqa: E402
import calibration as cal  # noqa: E402
import contract as contract_module  # noqa: E402

BUILDER_FAMILIES = ('quadruped', 'maw-quadruped', 'hexapod', 'octopod', 'winged-bat', 'winged-biped',
                    'winged-humanoid', 'humanoid')


def parse_arguments() -> argparse.Namespace:
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output-blend', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--bind', action='store_true', help='bind the mesh to the scaffold')
    parser.add_argument('--strip-existing-rig', action='store_true',
                        help='drop any armature, armature modifier and vertex groups from the source before building')
    return parser.parse_args(arguments)


# ----------------------------------------------------------------------------
# bone builders (bounds fractions)
# ----------------------------------------------------------------------------
def add_edit_bone(
    armature: bpy.types.Armature,
    name: str,
    head: tuple[float, float, float],
    tail: tuple[float, float, float],
    *,
    parent: bpy.types.EditBone | None = None,
    connected: bool = False,
) -> bpy.types.EditBone:
    bone = armature.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.parent = parent
    bone.use_connect = connected and parent is not None
    return bone


def build_giant_ant_bones(
    armature: bpy.types.Armature,
    minimum: Vector,
    maximum: Vector,
) -> list[str]:
    size = maximum - minimum
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    ground = minimum.z
    body_z = ground + size.z * 0.55
    length = max(size.y, 0.1)
    width = max(size.x, 0.1)
    height = max(size.z, 0.1)
    created: dict[str, bpy.types.EditBone] = {}

    created["Root"] = add_edit_bone(
        armature,
        "Root",
        (center_x, center_y, ground),
        (center_x, center_y, body_z),
    )
    created["Thorax"] = add_edit_bone(
        armature,
        "Thorax",
        (center_x, center_y - length * 0.06, body_z),
        (center_x, center_y + length * 0.12, body_z),
        parent=created["Root"],
    )
    created["Abdomen"] = add_edit_bone(
        armature,
        "Abdomen",
        (center_x, center_y - length * 0.04, body_z),
        (center_x, center_y - length * 0.34, body_z + height * 0.02),
        parent=created["Thorax"],
    )
    created["Head"] = add_edit_bone(
        armature,
        "Head",
        (center_x, center_y + length * 0.08, body_z),
        (center_x, center_y + length * 0.31, body_z + height * 0.03),
        parent=created["Thorax"],
    )

    for side_name, sign in (("L", 1.0), ("R", -1.0)):
        created[f"Mandible_{side_name}"] = add_edit_bone(
            armature,
            f"Mandible_{side_name}",
            (center_x + sign * width * 0.03, center_y + length * 0.27, body_z),
            (center_x + sign * width * 0.14, center_y + length * 0.42, body_z - height * 0.03),
            parent=created["Head"],
        )
        antenna_1 = add_edit_bone(
            armature,
            f"Antenna_{side_name}_01",
            (center_x + sign * width * 0.05, center_y + length * 0.3, body_z + height * 0.06),
            (center_x + sign * width * 0.13, center_y + length * 0.46, body_z + height * 0.14),
            parent=created["Head"],
        )
        add_edit_bone(
            armature,
            f"Antenna_{side_name}_02",
            tuple(antenna_1.tail),
            (center_x + sign * width * 0.2, center_y + length * 0.58, body_z + height * 0.1),
            parent=antenna_1,
            connected=True,
        )

    rows = (("Front", 0.16), ("Middle", 0.0), ("Rear", -0.16))
    for row_name, y_fraction in rows:
        base_y = center_y + length * y_fraction
        for side_name, sign in (("L", 1.0), ("R", -1.0)):
            prefix = f"Leg_{side_name}_{row_name}"
            coxa = add_edit_bone(
                armature,
                f"{prefix}_Coxa",
                (center_x + sign * width * 0.08, base_y, body_z),
                (center_x + sign * width * 0.24, base_y + length * y_fraction * 0.15, body_z + height * 0.03),
                parent=created["Thorax"],
            )
            femur = add_edit_bone(
                armature,
                f"{prefix}_Femur",
                tuple(coxa.tail),
                (center_x + sign * width * 0.43, base_y + length * y_fraction * 0.25, body_z - height * 0.08),
                parent=coxa,
                connected=True,
            )
            tibia = add_edit_bone(
                armature,
                f"{prefix}_Tibia",
                tuple(femur.tail),
                (center_x + sign * width * 0.52, base_y + length * y_fraction * 0.32, ground + height * 0.08),
                parent=femur,
                connected=True,
            )
            add_edit_bone(
                armature,
                f"{prefix}_Tarsus",
                tuple(tibia.tail),
                (center_x + sign * width * 0.57, base_y + length * y_fraction * 0.38, ground + height * 0.01),
                parent=tibia,
                connected=True,
            )
    return sorted(bone.name for bone in armature.edit_bones)


def build_quadruped_bones(
    armature: bpy.types.Armature,
    minimum: Vector,
    maximum: Vector,
) -> list[str]:
    size = maximum - minimum
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    ground = minimum.z
    body_z = ground + max(size.z, 0.1) * 0.55
    length = max(size.y, 0.1)
    width = max(size.x, 0.1)
    created: dict[str, bpy.types.EditBone] = {}
    created["Root"] = add_edit_bone(
        armature,
        "Root",
        (center_x, center_y, ground),
        (center_x, center_y, body_z),
    )
    created["Spine"] = add_edit_bone(
        armature,
        "Spine",
        (center_x, center_y + length * 0.2, body_z),
        (center_x, center_y - length * 0.18, body_z + size.z * 0.08),
        parent=created["Root"],
    )
    created["Head"] = add_edit_bone(
        armature,
        "Head",
        tuple(created["Spine"].tail),
        (center_x, center_y - length * 0.38, body_z + size.z * 0.02),
        parent=created["Spine"],
        connected=True,
    )
    tail_1 = add_edit_bone(
        armature,
        "Tail_01",
        tuple(created["Spine"].head),
        (center_x, center_y + length * 0.45, body_z - size.z * 0.05),
        parent=created["Spine"],
    )
    tail_2 = add_edit_bone(
        armature,
        "Tail_02",
        tuple(tail_1.tail),
        (center_x, center_y + length * 0.7, body_z - size.z * 0.12),
        parent=tail_1,
        connected=True,
    )
    add_edit_bone(
        armature,
        "Tail_03",
        tuple(tail_2.tail),
        (center_x, center_y + length * 0.92, ground + size.z * 0.08),
        parent=tail_2,
        connected=True,
    )
    for row_name, y_fraction in (("Front", -0.18), ("Rear", 0.18)):
        for side_name, sign in (("L", 1.0), ("R", -1.0)):
            prefix = f"Leg_{side_name}_{row_name}"
            upper = add_edit_bone(
                armature,
                f"{prefix}_Upper",
                (center_x + sign * width * 0.12, center_y + length * y_fraction, body_z),
                (center_x + sign * width * 0.28, center_y + length * y_fraction, body_z - size.z * 0.18),
                parent=created["Spine"],
            )
            lower = add_edit_bone(
                armature,
                f"{prefix}_Lower",
                tuple(upper.tail),
                (center_x + sign * width * 0.32, center_y + length * y_fraction, ground + size.z * 0.08),
                parent=upper,
                connected=True,
            )
            add_edit_bone(
                armature,
                f"{prefix}_Foot",
                tuple(lower.tail),
                (center_x + sign * width * 0.34, center_y + length * (y_fraction - 0.06), ground + size.z * 0.02),
                parent=lower,
                connected=True,
            )
    return sorted(bone.name for bone in armature.edit_bones)


def build_spider_bones(
    armature: bpy.types.Armature,
    minimum: Vector,
    maximum: Vector,
) -> list[str]:
    size = maximum - minimum
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    ground = minimum.z
    body_z = ground + max(size.z, 0.1) * 0.56
    length = max(size.y, 0.1)
    width = max(size.x, 0.1)
    height = max(size.z, 0.1)
    created: dict[str, bpy.types.EditBone] = {}

    created["Root"] = add_edit_bone(
        armature,
        "Root",
        (center_x, center_y, ground),
        (center_x, center_y, body_z),
    )
    created["Cephalothorax"] = add_edit_bone(
        armature,
        "Cephalothorax",
        (center_x, center_y - length * 0.06, body_z),
        (center_x, center_y + length * 0.15, body_z + height * 0.02),
        parent=created["Root"],
    )
    created["Abdomen"] = add_edit_bone(
        armature,
        "Abdomen",
        (center_x, center_y - length * 0.04, body_z),
        (center_x, center_y - length * 0.36, body_z + height * 0.04),
        parent=created["Cephalothorax"],
    )
    created["Head"] = add_edit_bone(
        armature,
        "Head",
        (center_x, center_y + length * 0.11, body_z),
        (center_x, center_y + length * 0.3, body_z - height * 0.02),
        parent=created["Cephalothorax"],
    )
    for side_name, sign in (("L", 1.0), ("R", -1.0)):
        created[f"Fang_{side_name}"] = add_edit_bone(
            armature,
            f"Fang_{side_name}",
            (
                center_x + sign * width * 0.04,
                center_y + length * 0.26,
                body_z - height * 0.02,
            ),
            (
                center_x + sign * width * 0.11,
                center_y + length * 0.39,
                body_z - height * 0.12,
            ),
            parent=created["Head"],
        )

    rows = (
        ("Front", 0.22),
        ("FrontMiddle", 0.08),
        ("RearMiddle", -0.08),
        ("Rear", -0.22),
    )
    for row_name, y_fraction in rows:
        base_y = center_y + length * y_fraction
        for side_name, sign in (("L", 1.0), ("R", -1.0)):
            prefix = f"Leg_{side_name}_{row_name}"
            coxa = add_edit_bone(
                armature,
                f"{prefix}_Coxa",
                (center_x + sign * width * 0.08, base_y, body_z),
                (
                    center_x + sign * width * 0.23,
                    base_y + length * y_fraction * 0.14,
                    body_z + height * 0.04,
                ),
                parent=created["Cephalothorax"],
            )
            femur = add_edit_bone(
                armature,
                f"{prefix}_Femur",
                tuple(coxa.tail),
                (
                    center_x + sign * width * 0.43,
                    base_y + length * y_fraction * 0.28,
                    body_z + height * 0.08,
                ),
                parent=coxa,
                connected=True,
            )
            tibia = add_edit_bone(
                armature,
                f"{prefix}_Tibia",
                tuple(femur.tail),
                (
                    center_x + sign * width * 0.58,
                    base_y + length * y_fraction * 0.4,
                    ground + height * 0.1,
                ),
                parent=femur,
                connected=True,
            )
            add_edit_bone(
                armature,
                f"{prefix}_Tarsus",
                tuple(tibia.tail),
                (
                    center_x + sign * width * 0.66,
                    base_y + length * y_fraction * 0.5,
                    ground + height * 0.015,
                ),
                parent=tibia,
                connected=True,
            )
    return sorted(bone.name for bone in armature.edit_bones)


def build_bat_bones(
    armature: bpy.types.Armature,
    minimum: Vector,
    maximum: Vector,
) -> list[str]:
    size = maximum - minimum
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    ground = minimum.z
    body_z = ground + max(size.z, 0.1) * 0.58
    length = max(size.y, 0.1)
    width = max(size.x, 0.1)
    height = max(size.z, 0.1)
    created: dict[str, bpy.types.EditBone] = {}

    created["Root"] = add_edit_bone(
        armature,
        "Root",
        (center_x, center_y, ground),
        (center_x, center_y, body_z),
    )
    created["Spine"] = add_edit_bone(
        armature,
        "Spine",
        (center_x, center_y - length * 0.16, body_z - height * 0.08),
        (center_x, center_y + length * 0.08, body_z + height * 0.08),
        parent=created["Root"],
    )
    created["Chest"] = add_edit_bone(
        armature,
        "Chest",
        tuple(created["Spine"].tail),
        (center_x, center_y + length * 0.18, body_z + height * 0.16),
        parent=created["Spine"],
        connected=True,
    )
    created["Head"] = add_edit_bone(
        armature,
        "Head",
        tuple(created["Chest"].tail),
        (center_x, center_y + length * 0.34, body_z + height * 0.2),
        parent=created["Chest"],
        connected=True,
    )
    for side_name, sign in (("L", 1.0), ("R", -1.0)):
        created[f"Ear_{side_name}"] = add_edit_bone(
            armature,
            f"Ear_{side_name}",
            (
                center_x + sign * width * 0.05,
                center_y + length * 0.29,
                body_z + height * 0.2,
            ),
            (
                center_x + sign * width * 0.12,
                center_y + length * 0.33,
                body_z + height * 0.4,
            ),
            parent=created["Head"],
        )
    created["Jaw"] = add_edit_bone(
        armature,
        "Jaw",
        (
            center_x,
            center_y + length * 0.29,
            body_z + height * 0.15,
        ),
        (
            center_x,
            center_y + length * 0.41,
            body_z + height * 0.08,
        ),
        parent=created["Head"],
    )

    for side_name, sign in (("L", 1.0), ("R", -1.0)):
        prefix = f"Wing_{side_name}"
        shoulder = add_edit_bone(
            armature,
            f"{prefix}_Shoulder",
            (
                center_x + sign * width * 0.06,
                center_y + length * 0.08,
                body_z + height * 0.12,
            ),
            (
                center_x + sign * width * 0.22,
                center_y + length * 0.11,
                body_z + height * 0.15,
            ),
            parent=created["Chest"],
        )
        upper = add_edit_bone(
            armature,
            f"{prefix}_UpperArm",
            tuple(shoulder.tail),
            (
                center_x + sign * width * 0.4,
                center_y + length * 0.15,
                body_z + height * 0.12,
            ),
            parent=shoulder,
            connected=True,
        )
        forearm = add_edit_bone(
            armature,
            f"{prefix}_Forearm",
            tuple(upper.tail),
            (
                center_x + sign * width * 0.57,
                center_y + length * 0.08,
                body_z + height * 0.08,
            ),
            parent=upper,
            connected=True,
        )
        wrist = add_edit_bone(
            armature,
            f"{prefix}_Wrist",
            tuple(forearm.tail),
            (
                center_x + sign * width * 0.68,
                center_y + length * 0.02,
                body_z + height * 0.05,
            ),
            parent=forearm,
            connected=True,
        )
        for finger_index, (y_fraction, z_fraction) in enumerate(
            ((0.32, 0.0), (0.1, -0.05), (-0.16, -0.12)),
            start=1,
        ):
            add_edit_bone(
                armature,
                f"{prefix}_Finger_{finger_index:02d}",
                tuple(wrist.tail),
                (
                    center_x + sign * width * (0.79 + finger_index * 0.015),
                    center_y + length * y_fraction,
                    body_z + height * z_fraction,
                ),
                parent=wrist,
            )

        leg_prefix = f"Leg_{side_name}"
        upper_leg = add_edit_bone(
            armature,
            f"{leg_prefix}_Upper",
            (
                center_x + sign * width * 0.08,
                center_y - length * 0.12,
                body_z - height * 0.08,
            ),
            (
                center_x + sign * width * 0.16,
                center_y - length * 0.21,
                body_z - height * 0.24,
            ),
            parent=created["Spine"],
        )
        lower_leg = add_edit_bone(
            armature,
            f"{leg_prefix}_Lower",
            tuple(upper_leg.tail),
            (
                center_x + sign * width * 0.2,
                center_y - length * 0.26,
                ground + height * 0.08,
            ),
            parent=upper_leg,
            connected=True,
        )
        add_edit_bone(
            armature,
            f"{leg_prefix}_Foot",
            tuple(lower_leg.tail),
            (
                center_x + sign * width * 0.24,
                center_y - length * 0.18,
                ground + height * 0.015,
            ),
            parent=lower_leg,
            connected=True,
        )
    return sorted(bone.name for bone in armature.edit_bones)


def build_devourer_bones(
    armature: bpy.types.Armature,
    minimum: Vector,
    maximum: Vector,
) -> list[str]:
    size = maximum - minimum
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    ground = minimum.z
    body_z = ground + max(size.z, 0.1) * 0.52
    length = max(size.y, 0.1)
    width = max(size.x, 0.1)
    height = max(size.z, 0.1)
    created: dict[str, bpy.types.EditBone] = {}

    created["Root"] = add_edit_bone(
        armature,
        "Root",
        (center_x, center_y, ground),
        (center_x, center_y, body_z),
    )
    created["Spine"] = add_edit_bone(
        armature,
        "Spine",
        (center_x, center_y + length * 0.24, body_z),
        (center_x, center_y - length * 0.04, body_z + height * 0.08),
        parent=created["Root"],
    )
    created["Chest"] = add_edit_bone(
        armature,
        "Chest",
        tuple(created["Spine"].tail),
        (center_x, center_y - length * 0.16, body_z + height * 0.08),
        parent=created["Spine"],
        connected=True,
    )
    created["Neck"] = add_edit_bone(
        armature,
        "Neck",
        tuple(created["Chest"].tail),
        (center_x, center_y - length * 0.25, body_z + height * 0.05),
        parent=created["Chest"],
        connected=True,
    )
    created["Head"] = add_edit_bone(
        armature,
        "Head",
        tuple(created["Neck"].tail),
        (center_x, center_y - length * 0.43, body_z + height * 0.03),
        parent=created["Neck"],
        connected=True,
    )
    created["Jaw_Upper"] = add_edit_bone(
        armature,
        "Jaw_Upper",
        (
            center_x,
            center_y - length * 0.3,
            body_z - height * 0.015,
        ),
        (
            center_x,
            center_y - length * 0.5,
            body_z + height * 0.035,
        ),
        parent=created["Head"],
    )
    created["Jaw_Lower"] = add_edit_bone(
        armature,
        "Jaw_Lower",
        (
            center_x,
            center_y - length * 0.3,
            body_z - height * 0.17,
        ),
        (
            center_x,
            center_y - length * 0.5,
            body_z - height * 0.34,
        ),
        parent=created["Head"],
    )

    for ridge_index, y_fraction in enumerate((0.16, 0.03, -0.1), start=1):
        add_edit_bone(
            armature,
            f"Back_Ridge_{ridge_index:02d}",
            (
                center_x,
                center_y + length * y_fraction,
                body_z + height * 0.1,
            ),
            (
                center_x,
                center_y + length * y_fraction,
                body_z + height * (0.25 + ridge_index * 0.025),
            ),
            parent=created["Spine"],
        )

    for row_name, y_fraction in (("Front", -0.14), ("Rear", 0.2)):
        for side_name, sign in (("L", 1.0), ("R", -1.0)):
            prefix = f"Leg_{side_name}_{row_name}"
            upper = add_edit_bone(
                armature,
                f"{prefix}_Upper",
                (
                    center_x + sign * width * 0.12,
                    center_y + length * y_fraction,
                    body_z - height * 0.02,
                ),
                (
                    center_x + sign * width * 0.27,
                    center_y + length * y_fraction,
                    body_z - height * 0.2,
                ),
                parent=created["Spine"],
            )
            lower = add_edit_bone(
                armature,
                f"{prefix}_Lower",
                tuple(upper.tail),
                (
                    center_x + sign * width * 0.31,
                    center_y + length * y_fraction,
                    ground + height * 0.09,
                ),
                parent=upper,
                connected=True,
            )
            add_edit_bone(
                armature,
                f"{prefix}_Foot",
                tuple(lower.tail),
                (
                    center_x + sign * width * 0.35,
                    center_y + length * (y_fraction - 0.08),
                    ground + height * 0.015,
                ),
                parent=lower,
                connected=True,
            )
    return sorted(bone.name for bone in armature.edit_bones)


def build_wyvern_bones(
    armature: bpy.types.Armature,
    minimum: Vector,
    maximum: Vector,
) -> list[str]:
    size = maximum - minimum
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    ground = minimum.z
    body_z = ground + max(size.z, 0.1) * 0.5
    length = max(size.y, 0.1)
    width = max(size.x, 0.1)
    height = max(size.z, 0.1)
    created: dict[str, bpy.types.EditBone] = {}

    created["Root"] = add_edit_bone(
        armature,
        "Root",
        (center_x, center_y, ground),
        (center_x, center_y, body_z),
    )
    created["Pelvis"] = add_edit_bone(
        armature,
        "Pelvis",
        (center_x, center_y - length * 0.18, body_z),
        (center_x, center_y - length * 0.04, body_z + height * 0.06),
        parent=created["Root"],
    )
    created["Spine"] = add_edit_bone(
        armature,
        "Spine",
        tuple(created["Pelvis"].tail),
        (center_x, center_y + length * 0.1, body_z + height * 0.14),
        parent=created["Pelvis"],
        connected=True,
    )
    created["Chest"] = add_edit_bone(
        armature,
        "Chest",
        tuple(created["Spine"].tail),
        (center_x, center_y + length * 0.19, body_z + height * 0.18),
        parent=created["Spine"],
        connected=True,
    )
    neck_1 = add_edit_bone(
        armature,
        "Neck_01",
        tuple(created["Chest"].tail),
        (center_x, center_y + length * 0.28, body_z + height * 0.27),
        parent=created["Chest"],
        connected=True,
    )
    neck_2 = add_edit_bone(
        armature,
        "Neck_02",
        tuple(neck_1.tail),
        (center_x, center_y + length * 0.38, body_z + height * 0.3),
        parent=neck_1,
        connected=True,
    )
    created["Head"] = add_edit_bone(
        armature,
        "Head",
        tuple(neck_2.tail),
        (center_x, center_y + length * 0.5, body_z + height * 0.28),
        parent=neck_2,
        connected=True,
    )
    created["Jaw"] = add_edit_bone(
        armature,
        "Jaw",
        (
            center_x,
            center_y + length * 0.41,
            body_z + height * 0.23,
        ),
        (
            center_x,
            center_y + length * 0.55,
            body_z + height * 0.17,
        ),
        parent=created["Head"],
    )

    tail_parent = created["Pelvis"]
    tail_head = tuple(created["Pelvis"].head)
    for tail_index, y_fraction in enumerate((-0.36, -0.56, -0.76, -0.94), start=1):
        tail = add_edit_bone(
            armature,
            f"Tail_{tail_index:02d}",
            tail_head,
            (
                center_x,
                center_y + length * y_fraction,
                ground + height * (0.32 - tail_index * 0.045),
            ),
            parent=tail_parent,
            connected=tail_index > 1,
        )
        tail_parent = tail
        tail_head = tuple(tail.tail)

    for side_name, sign in (("L", 1.0), ("R", -1.0)):
        wing_prefix = f"Wing_{side_name}"
        shoulder = add_edit_bone(
            armature,
            f"{wing_prefix}_Shoulder",
            (
                center_x + sign * width * 0.06,
                center_y + length * 0.1,
                body_z + height * 0.16,
            ),
            (
                center_x + sign * width * 0.22,
                center_y + length * 0.13,
                body_z + height * 0.22,
            ),
            parent=created["Chest"],
        )
        upper = add_edit_bone(
            armature,
            f"{wing_prefix}_UpperArm",
            tuple(shoulder.tail),
            (
                center_x + sign * width * 0.42,
                center_y + length * 0.17,
                body_z + height * 0.2,
            ),
            parent=shoulder,
            connected=True,
        )
        forearm = add_edit_bone(
            armature,
            f"{wing_prefix}_Forearm",
            tuple(upper.tail),
            (
                center_x + sign * width * 0.6,
                center_y + length * 0.09,
                body_z + height * 0.13,
            ),
            parent=upper,
            connected=True,
        )
        wrist = add_edit_bone(
            armature,
            f"{wing_prefix}_Wrist",
            tuple(forearm.tail),
            (
                center_x + sign * width * 0.72,
                center_y + length * 0.03,
                body_z + height * 0.08,
            ),
            parent=forearm,
            connected=True,
        )
        for finger_index, (y_fraction, z_fraction) in enumerate(
            ((0.34, 0.08), (0.12, -0.02), (-0.16, -0.12)),
            start=1,
        ):
            add_edit_bone(
                armature,
                f"{wing_prefix}_Finger_{finger_index:02d}",
                tuple(wrist.tail),
                (
                    center_x + sign * width * (0.84 + finger_index * 0.015),
                    center_y + length * y_fraction,
                    body_z + height * z_fraction,
                ),
                parent=wrist,
            )

        leg_prefix = f"Leg_{side_name}"
        thigh = add_edit_bone(
            armature,
            f"{leg_prefix}_Thigh",
            (
                center_x + sign * width * 0.11,
                center_y - length * 0.14,
                body_z,
            ),
            (
                center_x + sign * width * 0.22,
                center_y - length * 0.22,
                body_z - height * 0.2,
            ),
            parent=created["Pelvis"],
        )
        shin = add_edit_bone(
            armature,
            f"{leg_prefix}_Shin",
            tuple(thigh.tail),
            (
                center_x + sign * width * 0.25,
                center_y - length * 0.14,
                ground + height * 0.1,
            ),
            parent=thigh,
            connected=True,
        )
        foot = add_edit_bone(
            armature,
            f"{leg_prefix}_Foot",
            tuple(shin.tail),
            (
                center_x + sign * width * 0.27,
                center_y + length * 0.02,
                ground + height * 0.04,
            ),
            parent=shin,
            connected=True,
        )
        add_edit_bone(
            armature,
            f"{leg_prefix}_Toe",
            tuple(foot.tail),
            (
                center_x + sign * width * 0.29,
                center_y + length * 0.14,
                ground + height * 0.015,
            ),
            parent=foot,
            connected=True,
        )
    return sorted(bone.name for bone in armature.edit_bones)


def build_harpy_bones(
    armature: bpy.types.Armature,
    minimum: Vector,
    maximum: Vector,
) -> list[str]:
    size = maximum - minimum
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    ground = minimum.z
    height = max(size.z, 0.1)
    width = max(size.x, 0.1)
    length = max(size.y, 0.1)
    pelvis_z = ground + height * 0.4
    chest_z = ground + height * 0.68
    created: dict[str, bpy.types.EditBone] = {}

    created["Root"] = add_edit_bone(
        armature,
        "Root",
        (center_x, center_y, ground),
        (center_x, center_y, pelvis_z),
    )
    created["Pelvis"] = add_edit_bone(
        armature,
        "Pelvis",
        (center_x, center_y - length * 0.04, pelvis_z),
        (center_x, center_y + length * 0.02, pelvis_z + height * 0.08),
        parent=created["Root"],
    )
    created["Spine"] = add_edit_bone(
        armature,
        "Spine",
        tuple(created["Pelvis"].tail),
        (center_x, center_y + length * 0.04, chest_z),
        parent=created["Pelvis"],
        connected=True,
    )
    created["Chest"] = add_edit_bone(
        armature,
        "Chest",
        tuple(created["Spine"].tail),
        (center_x, center_y + length * 0.08, chest_z + height * 0.08),
        parent=created["Spine"],
        connected=True,
    )
    created["Neck"] = add_edit_bone(
        armature,
        "Neck",
        tuple(created["Chest"].tail),
        (center_x, center_y + length * 0.13, chest_z + height * 0.14),
        parent=created["Chest"],
        connected=True,
    )
    created["Head"] = add_edit_bone(
        armature,
        "Head",
        tuple(created["Neck"].tail),
        (center_x, center_y + length * 0.23, ground + height * 0.94),
        parent=created["Neck"],
        connected=True,
    )
    tail_1 = add_edit_bone(
        armature,
        "Tail_Feathers_01",
        tuple(created["Pelvis"].head),
        (center_x, center_y - length * 0.25, pelvis_z - height * 0.05),
        parent=created["Pelvis"],
    )
    add_edit_bone(
        armature,
        "Tail_Feathers_02",
        tuple(tail_1.tail),
        (center_x, center_y - length * 0.43, pelvis_z - height * 0.1),
        parent=tail_1,
        connected=True,
    )

    for side_name, sign in (("L", 1.0), ("R", -1.0)):
        arm_prefix = f"Arm_{side_name}"
        clavicle = add_edit_bone(
            armature,
            f"{arm_prefix}_Clavicle",
            (
                center_x + sign * width * 0.04,
                center_y + length * 0.07,
                chest_z + height * 0.05,
            ),
            (
                center_x + sign * width * 0.16,
                center_y + length * 0.08,
                chest_z + height * 0.04,
            ),
            parent=created["Chest"],
        )
        upper_arm = add_edit_bone(
            armature,
            f"{arm_prefix}_Upper",
            tuple(clavicle.tail),
            (
                center_x + sign * width * 0.25,
                center_y + length * 0.12,
                chest_z - height * 0.08,
            ),
            parent=clavicle,
            connected=True,
        )
        forearm = add_edit_bone(
            armature,
            f"{arm_prefix}_Forearm",
            tuple(upper_arm.tail),
            (
                center_x + sign * width * 0.3,
                center_y + length * 0.19,
                chest_z - height * 0.2,
            ),
            parent=upper_arm,
            connected=True,
        )
        add_edit_bone(
            armature,
            f"{arm_prefix}_Hand",
            tuple(forearm.tail),
            (
                center_x + sign * width * 0.33,
                center_y + length * 0.27,
                chest_z - height * 0.26,
            ),
            parent=forearm,
            connected=True,
        )

        wing_prefix = f"Wing_{side_name}"
        shoulder = add_edit_bone(
            armature,
            f"{wing_prefix}_Shoulder",
            (
                center_x + sign * width * 0.03,
                center_y - length * 0.01,
                chest_z + height * 0.04,
            ),
            (
                center_x + sign * width * 0.2,
                center_y - length * 0.04,
                chest_z + height * 0.13,
            ),
            parent=created["Chest"],
        )
        wing_upper = add_edit_bone(
            armature,
            f"{wing_prefix}_Upper",
            tuple(shoulder.tail),
            (
                center_x + sign * width * 0.42,
                center_y - length * 0.03,
                chest_z + height * 0.16,
            ),
            parent=shoulder,
            connected=True,
        )
        wing_forearm = add_edit_bone(
            armature,
            f"{wing_prefix}_Forearm",
            tuple(wing_upper.tail),
            (
                center_x + sign * width * 0.62,
                center_y - length * 0.1,
                chest_z + height * 0.08,
            ),
            parent=wing_upper,
            connected=True,
        )
        wrist = add_edit_bone(
            armature,
            f"{wing_prefix}_Wrist",
            tuple(wing_forearm.tail),
            (
                center_x + sign * width * 0.74,
                center_y - length * 0.16,
                chest_z,
            ),
            parent=wing_forearm,
            connected=True,
        )
        primary_1 = add_edit_bone(
            armature,
            f"{wing_prefix}_Primary_01",
            tuple(wrist.tail),
            (
                center_x + sign * width * 0.84,
                center_y - length * 0.25,
                chest_z - height * 0.08,
            ),
            parent=wrist,
            connected=True,
        )
        add_edit_bone(
            armature,
            f"{wing_prefix}_Primary_02",
            tuple(primary_1.tail),
            (
                center_x + sign * width * 0.9,
                center_y - length * 0.34,
                chest_z - height * 0.15,
            ),
            parent=primary_1,
            connected=True,
        )

        leg_prefix = f"Leg_{side_name}"
        thigh = add_edit_bone(
            armature,
            f"{leg_prefix}_Thigh",
            (
                center_x + sign * width * 0.08,
                center_y - length * 0.04,
                pelvis_z,
            ),
            (
                center_x + sign * width * 0.14,
                center_y - length * 0.07,
                ground + height * 0.2,
            ),
            parent=created["Pelvis"],
        )
        shin = add_edit_bone(
            armature,
            f"{leg_prefix}_Shin",
            tuple(thigh.tail),
            (
                center_x + sign * width * 0.15,
                center_y + length * 0.02,
                ground + height * 0.08,
            ),
            parent=thigh,
            connected=True,
        )
        ankle = add_edit_bone(
            armature,
            f"{leg_prefix}_Ankle",
            tuple(shin.tail),
            (
                center_x + sign * width * 0.17,
                center_y + length * 0.12,
                ground + height * 0.04,
            ),
            parent=shin,
            connected=True,
        )
        add_edit_bone(
            armature,
            f"{leg_prefix}_Talon",
            tuple(ankle.tail),
            (
                center_x + sign * width * 0.19,
                center_y + length * 0.25,
                ground + height * 0.015,
            ),
            parent=ankle,
            connected=True,
        )
    return sorted(bone.name for bone in armature.edit_bones)


def build_humanoid_bones(
    armature: bpy.types.Armature,
    minimum: Vector,
    maximum: Vector,
    *,
    large: bool,
) -> list[str]:
    size = maximum - minimum
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    ground = minimum.z
    height = max(size.z, 0.1)
    width = max(size.x, 0.1)
    length = max(size.y, 0.1)
    breadth = 1.12 if large else 1.0
    hips_z = ground + height * (0.42 if large else 0.46)
    chest_z = ground + height * (0.7 if large else 0.72)
    created: dict[str, bpy.types.EditBone] = {}

    created["Root"] = add_edit_bone(
        armature,
        "Root",
        (center_x, center_y, ground),
        (center_x, center_y, hips_z),
    )
    created["Hips"] = add_edit_bone(
        armature,
        "Hips",
        (center_x, center_y - length * 0.03, hips_z),
        (center_x, center_y + length * 0.01, hips_z + height * 0.08),
        parent=created["Root"],
    )
    created["Spine"] = add_edit_bone(
        armature,
        "Spine",
        tuple(created["Hips"].tail),
        (center_x, center_y + length * 0.02, hips_z + height * 0.17),
        parent=created["Hips"],
        connected=True,
    )
    created["Chest"] = add_edit_bone(
        armature,
        "Chest",
        tuple(created["Spine"].tail),
        (center_x, center_y + length * 0.04, chest_z),
        parent=created["Spine"],
        connected=True,
    )
    created["UpperChest"] = add_edit_bone(
        armature,
        "UpperChest",
        tuple(created["Chest"].tail),
        (center_x, center_y + length * 0.06, chest_z + height * 0.08),
        parent=created["Chest"],
        connected=True,
    )
    created["Neck"] = add_edit_bone(
        armature,
        "Neck",
        tuple(created["UpperChest"].tail),
        (center_x, center_y + length * 0.1, chest_z + height * 0.14),
        parent=created["UpperChest"],
        connected=True,
    )
    created["Head"] = add_edit_bone(
        armature,
        "Head",
        tuple(created["Neck"].tail),
        (center_x, center_y + length * 0.16, ground + height * 0.95),
        parent=created["Neck"],
        connected=True,
    )

    for anatomical, socket_side, sign in (
        ("Left", "L", 1.0),
        ("Right", "R", -1.0),
    ):
        shoulder = add_edit_bone(
            armature,
            f"{anatomical}Shoulder",
            (
                center_x + sign * width * 0.04,
                center_y + length * 0.04,
                chest_z + height * 0.05,
            ),
            (
                center_x + sign * width * 0.15 * breadth,
                center_y + length * 0.04,
                chest_z + height * 0.04,
            ),
            parent=created["UpperChest"],
        )
        upper_arm = add_edit_bone(
            armature,
            f"{anatomical}UpperArm",
            tuple(shoulder.tail),
            (
                center_x + sign * width * 0.3 * breadth,
                center_y + length * 0.06,
                chest_z - height * 0.02,
            ),
            parent=shoulder,
            connected=True,
        )
        lower_arm = add_edit_bone(
            armature,
            f"{anatomical}LowerArm",
            tuple(upper_arm.tail),
            (
                center_x + sign * width * 0.43 * breadth,
                center_y + length * 0.1,
                chest_z - height * 0.09,
            ),
            parent=upper_arm,
            connected=True,
        )
        hand = add_edit_bone(
            armature,
            f"{anatomical}Hand",
            tuple(lower_arm.tail),
            (
                center_x + sign * width * 0.51 * breadth,
                center_y + length * 0.14,
                chest_z - height * 0.12,
            ),
            parent=lower_arm,
            connected=True,
        )
        add_edit_bone(
            armature,
            f"Socket_Hand_{socket_side}",
            tuple(hand.tail),
            (
                center_x + sign * width * 0.57 * breadth,
                center_y + length * 0.17,
                chest_z - height * 0.13,
            ),
            parent=hand,
            connected=True,
        )

        upper_leg = add_edit_bone(
            armature,
            f"{anatomical}UpperLeg",
            (
                center_x + sign * width * 0.09 * breadth,
                center_y - length * 0.03,
                hips_z,
            ),
            (
                center_x + sign * width * 0.1 * breadth,
                center_y - length * 0.02,
                ground + height * 0.24,
            ),
            parent=created["Hips"],
        )
        lower_leg = add_edit_bone(
            armature,
            f"{anatomical}LowerLeg",
            tuple(upper_leg.tail),
            (
                center_x + sign * width * 0.1 * breadth,
                center_y + length * 0.02,
                ground + height * 0.07,
            ),
            parent=upper_leg,
            connected=True,
        )
        foot = add_edit_bone(
            armature,
            f"{anatomical}Foot",
            tuple(lower_leg.tail),
            (
                center_x + sign * width * 0.1 * breadth,
                center_y + length * 0.14,
                ground + height * 0.035,
            ),
            parent=lower_leg,
            connected=True,
        )
        add_edit_bone(
            armature,
            f"{anatomical}Toes",
            tuple(foot.tail),
            (
                center_x + sign * width * 0.1 * breadth,
                center_y + length * 0.24,
                ground + height * 0.015,
            ),
            parent=foot,
            connected=True,
        )
    return sorted(bone.name for bone in armature.edit_bones)


# ----------------------------------------------------------------------------
# scene preparation
# ----------------------------------------------------------------------------
def load_input(path: Path) -> None:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in ('.fbx', '.blend'):
        bc.load_source(path, use_anim=False)
    elif suffix in ('.glb', '.gltf'):
        bc.fresh_scene()
        bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    else:
        raise RuntimeError(f'Unsupported input {path}')


def strip_existing_rig() -> dict:
    removed = {'armatures': [], 'modifiers': 0, 'vertexGroups': 0, 'actions': 0}
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH':
            world = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = world
            for modifier in list(obj.modifiers):
                if modifier.type == 'ARMATURE':
                    obj.modifiers.remove(modifier)
                    removed['modifiers'] += 1
            removed['vertexGroups'] += len(obj.vertex_groups)
            obj.vertex_groups.clear()
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'ARMATURE':
            removed['armatures'].append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type == 'EMPTY' and not obj.children:
            bpy.data.objects.remove(obj, do_unlink=True)
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)
        removed['actions'] += 1
    return removed


def mesh_objects() -> list[bpy.types.Object]:
    return sorted((o for o in bpy.context.scene.objects if o.type == 'MESH'), key=lambda o: o.name)


def world_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    corners = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    if not corners:
        raise RuntimeError('cannot build a rig without mesh geometry')
    minimum = Vector(tuple(min(p[axis] for p in corners) for axis in range(3)))
    maximum = Vector(tuple(max(p[axis] for p in corners) for axis in range(3)))
    return minimum, maximum


def create_armature(row: dict, minimum: Vector, maximum: Vector) -> tuple[bpy.types.Object, list[str]]:
    family = row['family']
    calibration = row['calibration']
    if family not in BUILDER_FAMILIES:
        raise RuntimeError(f'family {family!r} has no scaffold builder (mixamo-biped is packaged from a provider rig)')
    name = row['folder']
    data = bpy.data.armatures.new(f'{name}_Armature')
    rig = bpy.data.objects.new(f'{name}_Rig', data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        if family == 'hexapod':
            names = build_giant_ant_bones(data, minimum, maximum)
        elif family == 'octopod':
            names = build_spider_bones(data, minimum, maximum)
        elif family == 'winged-bat':
            names = build_bat_bones(data, minimum, maximum)
        elif family == 'maw-quadruped':
            names = build_devourer_bones(data, minimum, maximum)
        elif family == 'winged-biped':
            names = build_wyvern_bones(data, minimum, maximum)
        elif family == 'winged-humanoid':
            names = build_harpy_bones(data, minimum, maximum)
        elif family == 'humanoid':
            large = bool(calibration.get('proportions', {}).get('large', False))
            names = build_humanoid_bones(data, minimum, maximum, large=large)
        else:
            names = build_quadruped_bones(data, minimum, maximum)
        applied = apply_landmarks(data, calibration.get('landmarks') or {})
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
    rig['rigit_landmarksApplied'] = json.dumps(applied)
    return rig, names


def apply_landmarks(armature: bpy.types.Armature, landmarks: dict) -> list[str]:
    """Move named bones to explicit world positions ({bone: {head: [..], tail: [..]}})."""
    applied = []
    for bone_name, spec in landmarks.items():
        bone = armature.edit_bones.get(bone_name)
        if bone is None:
            raise RuntimeError(f'landmark for unknown bone {bone_name}')
        if 'head' in spec:
            bone.head = Vector(spec['head'])
        if 'tail' in spec:
            bone.tail = Vector(spec['tail'])
        applied.append(bone_name)
    return applied


# ----------------------------------------------------------------------------
# binding
# ----------------------------------------------------------------------------
def bind_automatic(rig: bpy.types.Object, meshes: list[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action='DESELECT')
    for mesh in meshes:
        mesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    result = bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    if 'FINISHED' not in result:
        raise RuntimeError(f'automatic armature binding failed: {result}')


def distance_to_segment(point: Vector, start: Vector, end: Vector) -> float:
    segment = end - start
    length_squared = segment.length_squared
    if length_squared <= 1e-12:
        return (point - start).length
    amount = max(0.0, min(1.0, (point - start).dot(segment) / length_squared))
    return (point - (start + segment * amount)).length


def deform_candidates(rig: bpy.types.Object, root: str) -> list:
    return [b for b in rig.data.bones if b.name != root and not b.name.startswith('Socket_')]


def count_unweighted(meshes: list[bpy.types.Object]) -> int:
    return sum(1 for mesh in meshes for v in mesh.data.vertices if sum(g.weight for g in v.groups) <= 1e-6)


def bind_unweighted_vertices_to_nearest_bone(rig: bpy.types.Object, meshes: list[bpy.types.Object], root: str) -> int:
    """Give closed, disconnected details (teeth, buckles, floating tufts) a deterministic fallback weight."""
    candidates = deform_candidates(rig, root)
    if not candidates:
        raise RuntimeError('rig has no deform bones for fallback weighting')
    rig_inverse = rig.matrix_world.inverted()
    weighted = 0
    for mesh in meshes:
        for vertex in mesh.data.vertices:
            if sum(g.weight for g in vertex.groups) > 1e-6:
                continue
            point = rig_inverse @ (mesh.matrix_world @ vertex.co)
            nearest = min(candidates, key=lambda bone: distance_to_segment(point, bone.head_local, bone.tail_local))
            group = mesh.vertex_groups.get(nearest.name) or mesh.vertex_groups.new(name=nearest.name)
            group.add([vertex.index], 1.0, 'REPLACE')
            weighted += 1
    return weighted


def force_regions(rig: bpy.types.Object, meshes: list[bpy.types.Object], regions: list[dict],
                  minimum: Vector, maximum: Vector) -> dict[str, int]:
    """Assign full weight inside a box of the bounds to one bone (or split a box between two bones by height).

    Region spec: {"bones": ["Jaw_Lower"] or ["Jaw_Lower", "Jaw_Upper"], "box": {"x": [0.3, 0.7], "y": [0.0, 0.3],
    "z": [0.0, 0.4]}, "onlyIfEmpty": true}. Fractions are of the deformable bounds on each axis (x lateral,
    y forward axis of the file, z up). With two bones the box is split at its z midpoint: lower bone below,
    upper bone above. `onlyIfEmpty` (default true) skips the region when its bones already own vertices.
    """
    counts: dict[str, int] = {}
    extent = maximum - minimum
    rig_inverse = rig.matrix_world.inverted()
    for region in regions:
        bones = region['bones']
        if not 1 <= len(bones) <= 2:
            raise RuntimeError(f'forcedRegions entry needs one or two bones: {region}')
        for bone in bones:
            if rig.data.bones.get(bone) is None:
                raise RuntimeError(f'forcedRegions names unknown bone {bone}')
        box = region['box']
        lo = Vector(tuple(minimum[a] + extent[a] * box.get(axis, [0.0, 1.0])[0] for a, axis in enumerate('xyz')))
        hi = Vector(tuple(minimum[a] + extent[a] * box.get(axis, [0.0, 1.0])[1] for a, axis in enumerate('xyz')))
        split_z = (lo.z + hi.z) * 0.5
        if region.get('onlyIfEmpty', True):
            owned = 0
            for mesh in meshes:
                for bone in bones:
                    group = mesh.vertex_groups.get(bone)
                    if group is None:
                        continue
                    owned += sum(1 for v in mesh.data.vertices if any(g.group == group.index and g.weight > 0.5 for g in v.groups))
            if owned:
                for bone in bones:
                    counts[bone] = counts.get(bone, 0)
                continue
        for mesh in meshes:
            selected = {bone: [] for bone in bones}
            for vertex in mesh.data.vertices:
                point = mesh.matrix_world @ vertex.co
                if not (lo.x <= point.x <= hi.x and lo.y <= point.y <= hi.y and lo.z <= point.z <= hi.z):
                    continue
                if len(bones) == 1:
                    selected[bones[0]].append(vertex.index)
                else:
                    selected[bones[0] if point.z < split_z else bones[1]].append(vertex.index)
            for bone, ids in selected.items():
                if not ids:
                    continue
                for group in mesh.vertex_groups:
                    group.remove(ids)
                target = mesh.vertex_groups.get(bone) or mesh.vertex_groups.new(name=bone)
                target.add(ids, 1.0, 'REPLACE')
                counts[bone] = counts.get(bone, 0) + len(ids)
    return counts


def normalize_deform_weights(rig: bpy.types.Object, meshes: list[bpy.types.Object], *, maximum_influences: int = 4) -> dict[str, int]:
    """Clamp, trim to the strongest influences, and normalise every vertex for deterministic engine export."""
    bone_names = {bone.name for bone in rig.data.bones if bone.use_deform}
    corrected_vertices = 0
    trimmed_influences = 0
    maximum_before = 0
    for mesh in meshes:
        for vertex in mesh.data.vertices:
            influences = []
            for element in list(vertex.groups):
                group = mesh.vertex_groups[element.group]
                if group.name not in bone_names or element.weight <= 0.0:
                    continue
                influences.append((group, min(1.0, max(0.0, float(element.weight)))))
            influences.sort(key=lambda item: (-item[1], item[0].name))
            maximum_before = max(maximum_before, len(influences))
            discarded = influences[maximum_influences:]
            kept = influences[:maximum_influences]
            for group, _weight in discarded:
                group.remove([vertex.index])
            trimmed_influences += len(discarded)
            total = sum(weight for _group, weight in kept)
            if total <= 1e-12:
                continue
            normalized = [(group, weight / total) for group, weight in kept]
            changed = bool(discarded) or any(abs(group.weight(vertex.index) - weight) > 1e-6 for group, weight in normalized)
            for group, weight in normalized:
                group.add([vertex.index], weight, 'REPLACE')
            if changed:
                corrected_vertices += 1
    return {'maximumInfluencesBefore': maximum_before, 'maximumInfluencesAfter': maximum_influences,
            'trimmedInfluences': trimmed_influences, 'correctedVertices': corrected_vertices}


def harden_soles(rig: bpy.types.Object, mesh: bpy.types.Object, calibration: dict, height: float) -> dict[str, int]:
    """Give each foot's underside full weight to its sole bone so contacts do not blend with the shin."""
    if calibration['mode'] != 'ground' or not calibration.get('hardenSoles', True):
        return {}
    counts = {}
    for spec in calibration['legs']:
        if rig.data.bones.get(spec['ik']) is None:
            continue
        ankle_z = (rig.matrix_world @ rig.data.bones[spec['ik']].tail_local).z + height * 0.02
        sole = bc.sole_vertices(mesh, spec['sole'], max_z=ankle_z, threshold=0.05)
        primary = mesh.vertex_groups.get(spec['sole'][0]) or mesh.vertex_groups.new(name=spec['sole'][0])
        count = 0
        for index in sole:
            vertex = mesh.data.vertices[index]
            if (mesh.matrix_world @ vertex.co).z > ankle_z:
                continue
            others = [g.group for g in vertex.groups if g.group != primary.index]
            for group_index in others:
                mesh.vertex_groups[group_index].remove([index])
            primary.add([index], 1.0, 'REPLACE')
            count += 1
        counts[spec['id']] = count
    return counts


def per_bone_vertex_counts(meshes: list[bpy.types.Object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for mesh in meshes:
        names = {g.index: g.name for g in mesh.vertex_groups}
        for vertex in mesh.data.vertices:
            for g in vertex.groups:
                if g.weight > 0.01:
                    counts[names[g.group]] = counts.get(names[g.group], 0) + 1
    return dict(sorted(counts.items()))


def bone_rest_pose(rig: bpy.types.Object) -> dict[str, dict[str, list[float]]]:
    return {bone.name: {'head': [round(float(v), 6) for v in bone.head_local],
                        'tail': [round(float(v), 6) for v in bone.tail_local]}
            for bone in sorted(rig.data.bones, key=lambda item: item.name)}


# ----------------------------------------------------------------------------
def main() -> int:
    arguments = parse_arguments()
    row = contract_module.load(arguments.contract)
    calibration = row['calibration']
    load_input(arguments.input)
    stripped = strip_existing_rig() if arguments.strip_existing_rig else None
    if [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']:
        raise RuntimeError('scene already contains an armature; pass --strip-existing-rig to rebuild')
    meshes = mesh_objects()
    rigid_names = [part['object'] for part in row.get('rigidParts', [])]
    missing = [name for name in rigid_names if bpy.data.objects.get(name) is None]
    if missing:
        raise RuntimeError(f'rigid parts not found in scene: {missing}')
    deformable = [m for m in meshes if m.name not in rigid_names]
    if not deformable:
        raise RuntimeError('scene contains no deformable mesh after excluding rigid parts')
    minimum, maximum = world_bounds(deformable)
    height = max(maximum.z - minimum.z, 1e-6)
    rig, bones = create_armature(row, minimum, maximum)
    errors = cal.validate(calibration, set(bones))
    receipt = {
        'schemaVersion': 1, 'subjectId': row['subjectId'], 'family': row['family'],
        'blenderVersion': bpy.app.version_string,
        'input': {'path': Path(arguments.input).as_posix(), 'sha256': bc.sha256(arguments.input)},
        'strippedExistingRig': stripped,
        'bounds': {'minimum': list(minimum), 'maximum': list(maximum)},
        'rigObject': rig.name, 'boneCount': len(bones), 'bones': bones,
        'landmarksApplied': json.loads(rig['rigit_landmarksApplied']),
        'boneRestPose': bone_rest_pose(rig),
        'calibrationErrors': errors,
        'deformableMeshes': [m.name for m in deformable],
        'bound': arguments.bind,
        'acceptanceStatus': 'SCAFFOLD_ONLY_REQUIRES_WEIGHT_AND_ANIMATION_REVIEW',
    }
    if arguments.bind:
        for mesh in deformable:
            mesh.vertex_groups.clear()
        bind_automatic(rig, deformable)
        receipt['unweightedAfterAutomatic'] = count_unweighted(deformable)
        receipt['fallbackWeightedVertices'] = bind_unweighted_vertices_to_nearest_bone(rig, deformable, calibration['root'])
        receipt['forcedRegions'] = force_regions(rig, deformable, calibration.get('forcedRegions') or [], minimum, maximum)
        receipt['normalizedWeights'] = normalize_deform_weights(rig, deformable)
        main_mesh = max(deformable, key=lambda m: len(m.data.vertices))
        receipt['hardenedSoleVertices'] = harden_soles(rig, main_mesh, calibration, height)
        receipt['unweightedAfterBind'] = count_unweighted(deformable)
        attachments = []
        for part in row.get('rigidParts', []):
            obj = bpy.data.objects[part['object']]
            if rig.data.bones.get(part['bone']) is None:
                raise RuntimeError(f"rigid part {part['object']} names unknown bone {part['bone']}")
            bc.skin_rigid_to_bone(obj, rig, part['bone'])
            attachments.append({'object': obj.name, 'bone': part['bone']})
        receipt['rigidParts'] = attachments
        receipt['perBoneVertexCounts'] = per_bone_vertex_counts(deformable)
        receipt['bonesWithoutVertices'] = [b for b in bones if b not in receipt['perBoneVertexCounts']
                                           and b != calibration['root'] and not b.startswith('Socket_')]
    output_blend = arguments.output_blend.resolve()
    output_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_blend), check_existing=False)
    receipt['outputBlend'] = {'path': output_blend.as_posix(), 'sha256': bc.sha256(output_blend)}
    bc.write_json(arguments.receipt.resolve(), receipt)
    summary = {k: receipt.get(k) for k in ('subjectId', 'family', 'boneCount', 'calibrationErrors', 'unweightedAfterAutomatic',
                                           'fallbackWeightedVertices', 'unweightedAfterBind', 'bonesWithoutVertices', 'hardenedSoleVertices')}
    print(json.dumps(summary))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
