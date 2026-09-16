"""Generate a synthetic Mixamo-skeleton biped to exercise rig_input.py and package_biped.py.

Usage (Blender):
  Blender --background --factory-startup --python-exit-code 1 --python fixtures/make_mixamo_fixture.py -- \
      --output <dir>

Writes:
  <dir>/Models/Fixture/fixture.fbx           production model: body + rigid Fixture_Staff, rest pose, no animation
  <dir>/Models/Fixture/Textures/*.png         a basecolor and a normal map so rig_input.py finds textures
  <dir>/raw/Fixture_<Preset>_withSkin.fbx     one 24 fps clip per semantic on the mixamorig:* skeleton with skin
  <dir>/rig-contract.json                     a mixamo-biped contract pointing at the production model

The motion is crude and deliberately flawed the way provider presets are: the
walk is a treadmill with uneven stance speed, the idle dips under the floor,
Dead ends below the floor, and no loop returns exactly to its first pose. That
is what the packager passes exist to fix.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import blender_common as bc  # noqa: E402
from motion import foot_cycle  # noqa: E402

FPS = 24
UP = Vector((0, 0, 1))

# name: (head, tail, parent) in Blender Z-up metres; forward is +Y
BONES = [
    ('mixamorig:Hips', (0, 0, 0.95), (0, 0, 1.05), None),
    ('mixamorig:Spine', (0, 0, 1.05), (0, 0, 1.18), 'mixamorig:Hips'),
    ('mixamorig:Spine1', (0, 0, 1.18), (0, 0, 1.32), 'mixamorig:Spine'),
    ('mixamorig:Spine2', (0, 0, 1.32), (0, 0, 1.46), 'mixamorig:Spine1'),
    ('mixamorig:Neck', (0, 0, 1.46), (0, 0, 1.56), 'mixamorig:Spine2'),
    ('mixamorig:Head', (0, 0, 1.56), (0, 0, 1.70), 'mixamorig:Neck'),
    ('mixamorig:HeadTop_End', (0, 0, 1.70), (0, 0, 1.80), 'mixamorig:Head'),
]
for side, sign in (('Left', 1.0), ('Right', -1.0)):
    x = sign
    BONES += [
        (f'mixamorig:{side}Shoulder', (x * 0.05, 0, 1.44), (x * 0.18, 0, 1.42), 'mixamorig:Spine2'),
        (f'mixamorig:{side}Arm', (x * 0.18, 0, 1.42), (x * 0.38, 0, 1.22), f'mixamorig:{side}Shoulder'),
        (f'mixamorig:{side}ForeArm', (x * 0.38, 0, 1.22), (x * 0.56, 0, 1.03), f'mixamorig:{side}Arm'),
        (f'mixamorig:{side}Hand', (x * 0.56, 0, 1.03), (x * 0.63, 0, 0.96), f'mixamorig:{side}ForeArm'),
        (f'mixamorig:{side}HandMiddle1', (x * 0.63, 0, 0.96), (x * 0.66, 0, 0.93), f'mixamorig:{side}Hand'),
        (f'mixamorig:{side}HandMiddle2', (x * 0.66, 0, 0.93), (x * 0.685, 0, 0.905), f'mixamorig:{side}HandMiddle1'),
        (f'mixamorig:{side}HandMiddle3', (x * 0.685, 0, 0.905), (x * 0.705, 0, 0.885), f'mixamorig:{side}HandMiddle2'),
        (f'mixamorig:{side}HandMiddle4', (x * 0.705, 0, 0.885), (x * 0.72, 0, 0.87), f'mixamorig:{side}HandMiddle3'),
        (f'mixamorig:{side}UpLeg', (x * 0.10, 0, 0.92), (x * 0.11, 0, 0.50), 'mixamorig:Hips'),
        (f'mixamorig:{side}Leg', (x * 0.11, 0, 0.50), (x * 0.12, 0, 0.08), f'mixamorig:{side}UpLeg'),
        (f'mixamorig:{side}Foot', (x * 0.12, 0, 0.08), (x * 0.12, 0.12, 0.02), f'mixamorig:{side}Leg'),
        (f'mixamorig:{side}ToeBase', (x * 0.12, 0.12, 0.02), (x * 0.12, 0.22, 0.01), f'mixamorig:{side}Foot'),
        (f'mixamorig:{side}Toe_End', (x * 0.12, 0.22, 0.01), (x * 0.12, 0.26, 0.01), f'mixamorig:{side}ToeBase'),
    ]
NON_WEIGHT = {'mixamorig:HeadTop_End', 'mixamorig:LeftToe_End', 'mixamorig:RightToe_End',
              'mixamorig:LeftHandMiddle4', 'mixamorig:RightHandMiddle4'}


def cylinder(a: Vector, b: Vector, radius: float, verts: int = 24, rings: int = 4) -> bpy.types.Object:
    axis = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=axis.length, location=(a + b) * 0.5)
    obj = bpy.context.active_object
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = UP.rotation_difference(axis.normalized())
    # add rings so joints can bend
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=rings)
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj


def sphere(center: Vector, radius: float) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=radius, location=center)
    return bpy.context.active_object


def build_body() -> bpy.types.Object:
    V = Vector
    parts = [
        cylinder(V((0, 0, 0.84)), V((0, 0, 1.48)), 0.17, 32, 6),   # torso
        sphere(V((0, 0, 1.65)), 0.13),                              # head
        cylinder(V((0, 0, 1.46)), V((0, 0, 1.58)), 0.06, 16, 2),   # neck
    ]
    for x in (1.0, -1.0):
        parts += [
            cylinder(V((x * 0.18, 0, 1.42)), V((x * 0.38, 0, 1.22)), 0.06, 16, 4),
            cylinder(V((x * 0.38, 0, 1.22)), V((x * 0.56, 0, 1.03)), 0.05, 16, 4),
            cylinder(V((x * 0.56, 0, 1.03)), V((x * 0.70, 0, 0.89)), 0.045, 12, 3),
            cylinder(V((x * 0.10, 0, 0.92)), V((x * 0.11, 0, 0.50)), 0.09, 20, 6),
            cylinder(V((x * 0.11, 0, 0.50)), V((x * 0.12, 0, 0.08)), 0.07, 20, 6),
            cylinder(V((x * 0.12, -0.05, 0.03)), V((x * 0.12, 0.24, 0.03)), 0.045, 12, 3),
        ]
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    body = bpy.context.active_object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    body.name = 'Fixture_Body'
    body.data.name = 'Fixture_Body'
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    return body


def build_armature() -> bpy.types.Object:
    armature = bpy.data.armatures.new('Armature')
    rig = bpy.data.objects.new('Armature', armature)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, head, tail, parent in BONES:
        bone = armature.edit_bones.new(name)
        bone.head, bone.tail = head, tail
        if parent:
            bone.parent = armature.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    return rig


def segment_distance(p: Vector, a: Vector, b: Vector) -> float:
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length


def skin(body: bpy.types.Object, rig: bpy.types.Object) -> None:
    """Nearest-two-bone weights with a smooth falloff: deterministic, never leaves a vertex unweighted."""
    segments = [(b.name, rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local)
                for b in rig.data.bones if b.name not in NON_WEIGHT]
    groups = {name: body.vertex_groups.new(name=name) for name, _, _ in segments}
    for b in rig.data.bones:
        if b.name in NON_WEIGHT:
            body.vertex_groups.new(name=b.name)
    for v in body.data.vertices:
        p = body.matrix_world @ v.co
        scored = sorted(((segment_distance(p, a, b), name) for name, a, b in segments))[:2]
        (d0, n0), (d1, n1) = scored
        blend = max(0.0, 1.0 - (d1 - d0) / 0.06)  # only blend when two bones are nearly as close
        w1 = 0.5 * blend
        groups[n0].add([v.index], 1.0 - w1, 'REPLACE')
        if w1 > 0:
            groups[n1].add([v.index], w1, 'REPLACE')
    body.parent = rig
    modifier = body.modifiers.new('Armature', 'ARMATURE')
    modifier.object = rig


def build_staff() -> bpy.types.Object:
    # a thin shaft continuing the right forearm, the way a modeler tends to leave it (grip seating fixes it)
    a, b = Vector((-0.60, 0.0, 0.99)), Vector((-0.86, 0.0, 0.72))
    obj = cylinder(a, b + (b - a) * 2.5, 0.02, 12, 6)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.name = 'Fixture_Staff'
    obj.data.name = 'Fixture_Staff'
    return obj


def write_textures(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name, colour, colorspace in (('Fixture_BaseColor', (0.55, 0.35, 0.2, 1.0), 'sRGB'),
                                     ('Fixture_Normal', (0.5, 0.5, 1.0, 1.0), 'Non-Color')):
        image = bpy.data.images.new(name, 64, 64)
        image.pixels = list(colour) * (64 * 64)
        image.filepath_raw = str(folder / f'{name}.png')
        image.file_format = 'PNG'
        image.save()


def key_direct(rig, name: str, frames: int, poser) -> None:
    """Key a clip by setting pose values per frame through `poser(frame_index, t)`."""
    scene = bpy.context.scene
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = action
    if action.slots:
        rig.animation_data.action_slot = action.slots[0]
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
    for f in range(frames):
        scene.frame_set(f + 1)
        bc.clear_pose(rig)
        poser(f, f / max(frames - 1, 1))
        for bone in rig.pose.bones:
            bone.keyframe_insert('location', frame=f + 1, group=bone.name)
            bone.keyframe_insert('rotation_quaternion', frame=f + 1, group=bone.name)
    rig.animation_data.action = None


def rot(bone, axis: str, radians: float) -> None:
    bone.rotation_quaternion = bone.rotation_quaternion @ Quaternion(Vector({'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}[axis]), radians)


def walk_clip(rig, body) -> None:
    """IK-driven treadmill walk baked to keys: uneven stance speed, slight lift asymmetry."""
    scene = bpy.context.scene
    frames = FPS + 1  # one second cycle, duplicated endpoint
    stride, duty, clearance = 0.5, 0.6, 0.09
    targets = {}
    for side, phase0 in (('Left', 0.0), ('Right', 0.5)):
        target = bpy.data.objects.new(f'IK_{side}', None)
        scene.collection.objects.link(target)
        ik = rig.pose.bones[f'mixamorig:{side}Leg'].constraints.new('IK')
        ik.target, ik.chain_count, ik.use_stretch, ik.iterations = target, 2, False, 300
        targets[side] = (target, ik, phase0)
    rest_ankle = {side: (rig.matrix_world @ rig.data.bones[f'mixamorig:{side}Leg'].tail_local).copy() for side in ('Left', 'Right')}
    hips = rig.pose.bones['mixamorig:Hips']
    samples = []
    for f in range(frames):
        t = f / (frames - 1)
        scene.frame_set(f + 1)
        bc.clear_pose(rig)
        hips.location = Vector((0, -0.02 * (1 - math.cos(4 * math.pi * t)), 0))  # bone-local Y is world up
        rot(rig.pose.bones['mixamorig:Spine'], 'Z', 0.06 * math.sin(2 * math.pi * t))
        rot(rig.pose.bones['mixamorig:LeftArm'], 'X', 0.4 * math.sin(2 * math.pi * t))
        rot(rig.pose.bones['mixamorig:RightArm'], 'X', -0.4 * math.sin(2 * math.pi * t))
        for side, (target, _, phase0) in targets.items():
            along, lift, planted = foot_cycle(t + phase0, duty, stride, clearance)
            along += 0.025 * math.sin(2 * math.pi * ((t + phase0) % 1.0) / duty) if planted else 0.0  # uneven stance speed
            target.location = rest_ankle[side] + Vector((0, along, lift))
        bpy.context.view_layer.update()
        samples.append(bc.bake_pose_sample(rig))
    for side, (target, ik, _) in targets.items():
        rig.pose.bones[f'mixamorig:{side}Leg'].constraints.remove(ik)
        bpy.data.objects.remove(target, do_unlink=True)
    bc.write_action(rig, 'Walking', samples)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    out = args.output.resolve()
    models = out / 'Models' / 'Fixture'
    raw = out / 'raw'
    models.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    body = build_body()
    rig = build_armature()
    skin(body, rig)
    staff = build_staff()
    write_textures(models / 'Textures')
    material = bpy.data.materials.new('Fixture_Material')
    material.use_nodes = True
    tex = material.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images['Fixture_BaseColor']
    material.node_tree.links.new(tex.outputs['Color'], material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    for obj in (body, staff):
        obj.data.materials.append(material)
    # ---- production model: rest, no animation, body + staff, no armature
    bc.export_fbx(models / 'fixture.fbx', [body, staff], bake_anim=False)
    # ---- clips
    hips = rig.pose.bones['mixamorig:Hips']

    def idle(f, t):
        hips.location = Vector((0, -0.015 - 0.012 * math.sin(2 * math.pi * t), 0))  # dips under the floor
        rot(rig.pose.bones['mixamorig:Spine1'], 'X', 0.03 * math.sin(2 * math.pi * t))
        rot(rig.pose.bones['mixamorig:Head'], 'Z', 0.08 * math.sin(2 * math.pi * t * 0.5))  # does not loop cleanly

    def attack(f, t):
        arm, fore = rig.pose.bones['mixamorig:RightArm'], rig.pose.bones['mixamorig:RightForeArm']
        swing = -0.9 if t < 0.35 else 1.6 * math.sin(math.pi * (t - 0.35) / 0.65) - 0.9 * (1 - (t - 0.35) / 0.65)
        rot(arm, 'X', swing)
        rot(fore, 'X', 0.6 * math.sin(math.pi * t))
        rot(rig.pose.bones['mixamorig:Spine'], 'Z', -0.25 * math.sin(math.pi * t))

    def hit(f, t):
        k = math.sin(math.pi * t)
        rot(rig.pose.bones['mixamorig:Spine1'], 'X', -0.5 * k)
        rot(rig.pose.bones['mixamorig:Head'], 'X', -0.3 * k)
        hips.location = Vector((0, 0, 0.08 * k))  # bone-local Z is world back

    def dead(f, t):
        k = min(1.0, t / 0.7)
        s = k * k * (3 - 2 * k)
        rot(hips, 'X', -1.55 * s)
        hips.location = Vector((0, -0.84 * s, 0.3 * s))  # lands about 5 cm below the floor
        rot(rig.pose.bones['mixamorig:RightArm'], 'X', 1.3 * s)  # the right arm ends up through the floor (hand guard)

    key_direct(rig, 'Idle', 2 * FPS + 1, idle)
    walk_clip(rig, body)
    key_direct(rig, 'Attack', FPS + 1, attack)
    key_direct(rig, 'Hit', int(0.6 * FPS) + 1, hit)
    key_direct(rig, 'Dead', int(1.2 * FPS) + 1, dead)
    written = {}
    for preset in ('Idle', 'Walking', 'Attack', 'Hit', 'Dead'):
        action = bpy.data.actions[preset]
        bc.bind_action(rig, action)
        scene.frame_start, scene.frame_end = 1, int(action.frame_range[1])
        path = raw / f'Fixture_{preset}_withSkin.fbx'
        bc.export_fbx(path, [rig, body], bake_anim=True, bake_anim_use_nla_strips=False)
        written[preset] = {'path': path.as_posix(), 'frames': int(action.frame_range[1])}
        rig.animation_data.action = None
    contract = {
        'schemaVersion': 1, 'subjectId': 'fixture', 'displayName': 'Fixture', 'family': 'mixamo-biped',
        'engineRig': 'Humanoid', 'requiredClips': ['Idle', 'Locomotion', 'BasicAttack', 'Hit', 'Death'],
        'source': {'model': 'Models/Fixture/fixture.fbx', 'textures': 'Models/Fixture/Textures'},
        'rigidParts': [{'object': 'Fixture_Staff', 'bone': 'mixamorig:RightHand', 'grip': {'fraction': 0.4, 'direction': 'up'}}],
        'moveSpeedUnitsPerSecond': 5.0,
        'presets': {'Idle': 'Idle', 'Locomotion': 'Walking', 'BasicAttack': 'Attack', 'Hit': 'Hit', 'Death': 'Dead'},
    }
    (out / 'rig-contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    print(json.dumps({'production': (models / 'fixture.fbx').as_posix(), 'bodyVertices': len(body.data.vertices),
                      'staffVertices': len(staff.data.vertices), 'raw': written, 'contract': (out / 'rig-contract.json').as_posix()}))


if __name__ == '__main__':
    main()
