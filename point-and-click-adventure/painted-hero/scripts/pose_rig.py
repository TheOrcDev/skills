"""The hero's pose rig: a mannequin built from a CC0 human base mesh, rigged,
keyframed and rendered as 2D frames with per-frame anchors. Its renders are
the pose guides Sol paints over (see ../SKILL.md) and the source of every
animation's timing, events and ground speed. Run headless:

  $BLENDER -b --disable-autoexec -P pose_rig.py -- \
      --base-mesh <path>/body_male_realistic.blend \
      --out art-source/work/characters/hero/rig \
      [--anims walk,idle,...  (default: all)] [--dirs r,u,d] [--fps 12] \
      [--config hero_rig.json] [--blend art-source/work/characters/hero/hero.blend] [--preview]

`--base-mesh` may also come from the HERO_BASE_MESH environment variable.

Motion is keyed at 24 fps; any output rate samples it (between keys too), so
a walk can be compared at 8, 12 and 15 fps from the same keys.

The body is Blender Studio's CC0 realistic male base mesh (Human Base Meshes
v1.4.1): broadened a little at the shoulders, scaled to HEIGHT, its face
smoothed into a plain skull. It is rigged with named bones and automatic
weights; motion is keyframed here over a slightly hunched stance. Frames are
lit EEVEE renders on transparency (near-black skin, cold rim lights from
behind), plus anchors.json with per-frame pixel positions of the head, eyes,
shoulders, upper back, hands and feet. Run Blender with --disable-autoexec,
as the base mesh is a downloaded file.

`--config` takes a JSON object; every key is optional:

  height           metres the hero stands (1.85)
  frame_size       [w, h] render frame in pixels (448, 672)
  character_px     pixels the hero stands in the frame at scale 1 (480)
  camera_center_z  metres; the camera's aim height (1.1)
  tilt_deg         degrees the orthographic camera looks down (10)
  power            metres each side the shoulders and arms move out (0.03)
  inflate          metres the body swells along its normals (0.004)
  multires_level   sculpt detail baked in, 0-2 (2)
  smooth_head      melt the face and ears into a plain skull (true)
  stance           {bone: [swing, tilt, twist]} degrees under every motion,
                   replacing the default stance for the bones it names
  stance_lift      metres the hips sit lower in the stance (-0.004)
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler, Vector

# Defaults; configure() replaces them from --config before anything is built.
HEIGHT = 1.85
FRAME = (448, 672)  # sprite frame in pixels, with headroom for a raised arm
CHARACTER_PX = 480  # how tall the hero is in the frame at scale 1
CAMERA_CENTER_Z = 1.1  # metres; the frame reaches about 0.2 m below the feet
TILT_DEG = 10.0
CYCLE = 24  # walk cycle length in 24 fps frames (one second)
ORTHO_SCALE = HEIGHT * FRAME[1] / CHARACTER_PX

# The base mesh's height, and how it is reshaped: its shoulders and arms move
# out and it swells a little for a sturdier build, then it is scaled from its
# 1.687 m to HEIGHT. Its sculpted muscle is kept as a multires modifier until
# finish_body bakes it in.
BASE_MESH = Path()
BASE_HEIGHT = 1.687
SCALE = HEIGHT / BASE_HEIGHT
POWER = 0.03  # metres each side the shoulders, upper torso and arms move out
INFLATE = 0.004  # metres the body swells along its normals
MULTIRES_LEVEL = 2
SMOOTH_HEAD = True
LEG_LENGTH = 0.85  # hip to ankle, metres, at HEIGHT

# Bones on the base mesh in its A-pose: name -> (head, tail, parent), metres in
# its own space before POWER and SCALE. Measured on gridded front and side views.
BASE_BONES = {
    "hips": ((0, 0.03, 0.92), (0, 0.035, 1.05), None),
    "spine": ((0, 0.035, 1.05), (0, 0.04, 1.22), "hips"),
    "chest": ((0, 0.04, 1.22), (0, 0.03, 1.42), "spine"),
    "neck": ((0, 0.025, 1.43), (0, 0.0, 1.53), "chest"),
    "head": ((0, 0.0, 1.53), (0, -0.005, 1.69), "neck"),
}
for s_, sign in ((".L", 1), (".R", -1)):
    BASE_BONES.update({
        "shoulder" + s_: ((0.03 * sign, -0.02, 1.4), (0.17 * sign, 0.0, 1.38), "chest"),
        "upper_arm" + s_: ((0.18 * sign, 0.0, 1.37), (0.3 * sign, 0.035, 1.07), "shoulder" + s_),
        "forearm" + s_: ((0.3 * sign, 0.035, 1.07), (0.375 * sign, -0.06, 0.86), "upper_arm" + s_),
        "hand" + s_: ((0.375 * sign, -0.06, 0.86), (0.43 * sign, -0.08, 0.72), "forearm" + s_),
        "thigh" + s_: ((0.09 * sign, 0.02, 0.88), (0.11 * sign, 0.0, 0.44), "hips"),
        "shin" + s_: ((0.11 * sign, 0.0, 0.44), (0.175 * sign, 0.045, 0.075), "thigh" + s_),
        "foot" + s_: ((0.175 * sign, 0.045, 0.075), (0.19 * sign, -0.12, 0.02), "shin" + s_),
    })


def _smoothstep(a: float, b: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def shape(co: Vector) -> Vector:
    """A base-mesh point moved to the hero's build: shoulders, upper torso and
    the arms hanging from them shift outwards by POWER, then everything scales."""
    ax = abs(co.x)
    torso = _smoothstep(0.05, 0.17, ax) * _smoothstep(1.02, 1.2, co.z) * (1.0 - _smoothstep(1.42, 1.52, co.z))
    arm = _smoothstep(0.2, 0.25, ax) * _smoothstep(0.55, 0.65, co.z) * (1.0 - _smoothstep(1.25, 1.35, co.z))
    shift = math.copysign(POWER * max(torso, arm), co.x)
    return Vector((co.x + shift, co.y, co.z)) * SCALE


BONES = {name: (tuple(shape(Vector(head))), tuple(shape(Vector(tail))), parent) for name, (head, tail, parent) in BASE_BONES.items()}


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def activate(obj) -> None:
    for other in bpy.context.view_layer.objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def skin_material():
    """Near-black skin with a fibrous, smoky bump that catches the rim lights."""
    material = bpy.data.materials.new("HeroSkin")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1.0)
    shader.inputs["Roughness"].default_value = 0.5
    shader.inputs["Specular IOR Level"].default_value = 0.4
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 45.0
    noise.inputs["Detail"].default_value = 10.0
    noise.inputs["Roughness"].default_value = 0.65
    noise.inputs["Distortion"].default_value = 2.0
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.002
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    # The fibrous bump fades out on the smooth skull.
    head = nodes.new("ShaderNodeAttribute")
    head.attribute_name = "head_mask"
    strength = nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY_ADD"
    strength.inputs[1].default_value = -0.25
    strength.inputs[2].default_value = 0.25
    links.new(head.outputs["Fac"], strength.inputs[0])
    links.new(strength.outputs["Value"], bump.inputs["Strength"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    # Hands and feet lose their sheen, so toes and fingers do not glint.
    ends = nodes.new("ShaderNodeAttribute")
    ends.attribute_name = "extremity_mask"
    sheen = nodes.new("ShaderNodeMath")
    sheen.operation = "MULTIPLY_ADD"
    sheen.inputs[1].default_value = -0.34
    sheen.inputs[2].default_value = 0.4
    links.new(ends.outputs["Fac"], sheen.inputs[0])
    links.new(sheen.outputs["Value"], shader.inputs["Specular IOR Level"])
    return material


def _smooth_head(mesh, weights, iterations: int = 60, factor: float = 0.6) -> None:
    """Laplacian smoothing of the vertices, each pulled towards its neighbours'
    mean by `factor` × its weight, `iterations` times (numpy, once at build)."""
    count = len(mesh.vertices)
    co = np.empty(count * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    edges = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get("vertices", edges)
    a, b = edges[0::2], edges[1::2]
    degree = np.bincount(np.concatenate([a, b]), minlength=count).astype(np.float64)[:, None]
    pull = (weights * factor)[:, None]
    active = weights > 0.0
    for _ in range(iterations):
        total = np.zeros_like(co)
        np.add.at(total, a, co[b])
        np.add.at(total, b, co[a])
        mean = total / np.maximum(degree, 1.0)
        co[active] += (mean[active] - co[active]) * pull[active]
    mesh.vertices.foreach_set("co", co.ravel())
    mesh.update()


def build_body():
    """Loads the base mesh and its eyes and shapes them to the hero's build at
    the base level (the sculpted muscle stays a multires modifier until
    finish_body). Returns (body, [eye_l, eye_r]); the eyes only mark where the
    glows go."""
    with bpy.data.libraries.load(str(BASE_MESH), link=False) as (source, target):
        target.objects = [name for name in source.objects if name.startswith("GEO-body_male_realistic")]
    for obj in target.objects:
        bpy.context.scene.collection.objects.link(obj)
    # World matrices of freshly loaded children are stale until the scene updates.
    bpy.context.view_layer.update()
    body = bpy.data.objects["GEO-body_male_realistic"]
    eyes = [bpy.data.objects["GEO-body_male_realistic.eye.L"], bpy.data.objects["GEO-body_male_realistic.eye.R"]]
    for eye in eyes:
        world = eye.matrix_world.translation.copy()
        eye.parent = None
        eye.location = shape(world)
        eye.scale = (SCALE, SCALE, SCALE)
        eye.hide_render = True
    mesh = body.data
    count = len(mesh.vertices)
    co = np.empty(count * 3, dtype=np.float64)
    normals = np.empty(count * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", co)
    mesh.vertices.foreach_get("normal", normals)
    co = (co + normals * INFLATE).reshape(-1, 3)
    mesh.vertices.foreach_set("co", np.array([shape(Vector(v)) for v in co], dtype=np.float64).ravel())
    mesh.update()
    return body, eyes


def finish_body(body) -> None:
    """After binding (weights come from the light base mesh): bakes the sculpted
    muscle in, melts the face and ears into a smooth skull (SMOOTH_HEAD), and
    gives it the skin."""
    activate(body)
    for modifier in list(body.modifiers):
        if modifier.type == "MULTIRES":
            modifier.levels = MULTIRES_LEVEL
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    mesh = body.data
    count = len(mesh.vertices)
    co = np.empty(count * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", co)
    z = co.reshape(-1, 3)[:, 2]
    neck_z, crown_z = 1.47 * SCALE, 1.55 * SCALE
    head = np.clip((z - neck_z) / (crown_z - neck_z), 0.0, 1.0)
    head = head * head * (3.0 - 2.0 * head)
    if SMOOTH_HEAD:
        _smooth_head(mesh, head, iterations=140, factor=0.8)
    mask = mesh.attributes.new("head_mask", "FLOAT", "POINT")
    mask.data.foreach_set("value", head.astype(np.float32))
    # Hands (beyond the wrists in the A-pose rest) and feet (below the ankles).
    xyz = co.reshape(-1, 3)
    ax = np.abs(xyz[:, 0])
    feet = np.clip((0.16 - xyz[:, 2]) / 0.1, 0.0, 1.0)
    hands = np.clip((ax - 0.39 * SCALE) / (0.04 * SCALE), 0.0, 1.0) * (xyz[:, 2] < 1.05 * SCALE)
    ends = mesh.attributes.new("extremity_mask", "FLOAT", "POINT")
    ends.data.foreach_set("value", np.maximum(feet, hands).astype(np.float32))
    body.data.materials.clear()
    body.data.materials.append(skin_material())
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))


def build_rig():
    armature = bpy.data.armatures.new("HeroRig")
    rig = bpy.data.objects.new("HeroRig", armature)
    bpy.context.collection.objects.link(rig)
    activate(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    for name, (head, tail, _) in BONES.items():
        bone = armature.edit_bones.new(name)
        bone.head, bone.tail = Vector(head), Vector(tail)
        bone.roll = 0.0
    for name, (_, _, parent) in BONES.items():
        if parent:
            armature.edit_bones[name].parent = armature.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for bone in rig.pose.bones:
        bone.rotation_mode = "XYZ"
    return rig


def bind(body, eyes, rig) -> None:
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    for eye in eyes:
        world = eye.matrix_world.copy()
        eye.parent = rig
        eye.parent_type = "BONE"
        eye.parent_bone = "head"
        eye.matrix_world = world


class Poser:
    """Sets bone rotations in 'anatomical' terms, whatever each bone's local axes are.
    swing(bone, deg): positive moves the bone's tail forward (towards -Y) in the side plane.
    tilt(bone, deg): positive moves the tail towards the character's left (+X).
    twist(bone, deg): rotation about the bone's own length."""

    def __init__(self, rig):
        self.rig = rig
        self.signs: dict[tuple[str, int], float] = {}
        for bone in rig.pose.bones:
            for axis in (0, 2):
                self.signs[(bone.name, axis)] = self._probe(bone, axis)

    def _tail(self, bone) -> Vector:
        bpy.context.view_layer.update()
        return self.rig.matrix_world @ bone.tail

    def _probe(self, bone, axis: int) -> float:
        rest = self._tail(bone)
        bone.rotation_euler[axis] = 0.3
        moved = self._tail(bone) - rest
        bone.rotation_euler[axis] = 0.0
        bpy.context.view_layer.update()
        if axis == 0:  # swing: forward is -Y; for a bone pointing forward already, use -Z (down) as "forward"
            primary = -moved.y if abs(moved.y) >= abs(moved.z) else -moved.z
        else:  # tilt: towards +X
            primary = moved.x if abs(moved.x) >= 1e-6 else -moved.y
        return 1.0 if primary >= 0 else -1.0

    def pose(self, name: str, swing: float = 0.0, tilt: float = 0.0, twist: float = 0.0) -> None:
        """Sets a bone's rotation on top of the stance (STANCE)."""
        base_swing, base_tilt, base_twist = STANCE.get(name, (0.0, 0.0, 0.0))
        bone = self.rig.pose.bones[name]
        bone.rotation_euler = Euler((
            math.radians(swing + base_swing) * self.signs[(name, 0)],
            math.radians(twist + base_twist),
            math.radians(tilt + base_tilt) * self.signs[(name, 2)],
        ))

    def lift(self, name: str, up: float) -> None:
        """Moves a bone along world Z (used for the hips' bob); bones here point up, so local Y is world Z."""
        self.rig.pose.bones[name].location = (0.0, up + (STANCE_LIFT if name == "hips" else 0.0), 0.0)

    def key(self, frame: int) -> None:
        for bone in self.rig.pose.bones:
            bone.keyframe_insert("rotation_euler", frame=frame)
            bone.keyframe_insert("location", frame=frame)

    def reset(self) -> None:
        """Back to the stance."""
        for bone in self.rig.pose.bones:
            self.pose(bone.name)
            bone.location = (0, 0, 0)
        self.lift("hips", 0.0)


ARMS_IN_WALK = 4.0  # the rest pose holds the arms slightly out; walking tucks them in a little


# The stance under every motion, added to whatever each pose sets: head pushed
# forward, a slight hunch, elbows bent and held off the broad back, hands
# curled, knees soft. bone: (swing, tilt, twist) in degrees.
STANCE = {
    "chest": (6, 0, 0), "neck": (12, 0, 0), "head": (-9, 0, 0),
    # The base mesh's A-pose holds the arms about 20° out and the feet apart.
    "upper_arm.L": (0, -11, 0), "upper_arm.R": (0, 11, 0),
    "thigh.L": (3, -5, 0), "thigh.R": (3, 5, 0),
    **{bone + side: values for side in (".L", ".R") for bone, values in (
        ("forearm", (12, 0, 0)), ("hand", (10, 0, 0)), ("shin", (-6, 0, 0)), ("foot", (3, 0, 0)))},
}
STANCE_LIFT = -0.004


def configure(config: dict, base_mesh: Path) -> None:
    """Applies --config over the defaults and derives what depends on them."""
    global HEIGHT, FRAME, CHARACTER_PX, CAMERA_CENTER_Z, TILT_DEG, ORTHO_SCALE, BASE_MESH, SCALE
    global POWER, INFLATE, MULTIRES_LEVEL, SMOOTH_HEAD, LEG_LENGTH, BONES, STANCE_LIFT
    known = {"height", "frame_size", "character_px", "camera_center_z", "tilt_deg", "power", "inflate",
             "multires_level", "smooth_head", "stance", "stance_lift"}
    unknown_keys = set(config) - known
    if unknown_keys:
        raise SystemExit(f"pose_rig: unknown config keys {sorted(unknown_keys)}")
    leg_ratio = LEG_LENGTH / HEIGHT
    HEIGHT = float(config.get("height", HEIGHT))
    FRAME = tuple(int(v) for v in config.get("frame_size", FRAME))
    CHARACTER_PX = int(config.get("character_px", CHARACTER_PX))
    CAMERA_CENTER_Z = float(config.get("camera_center_z", CAMERA_CENTER_Z))
    TILT_DEG = float(config.get("tilt_deg", TILT_DEG))
    POWER = float(config.get("power", POWER))
    INFLATE = float(config.get("inflate", INFLATE))
    MULTIRES_LEVEL = int(config.get("multires_level", MULTIRES_LEVEL))
    SMOOTH_HEAD = bool(config.get("smooth_head", SMOOTH_HEAD))
    STANCE_LIFT = float(config.get("stance_lift", STANCE_LIFT))
    for bone, values in config.get("stance", {}).items():
        if bone not in BASE_BONES:
            raise SystemExit(f"pose_rig: stance names an unknown bone {bone!r}")
        STANCE[bone] = tuple(float(v) for v in values)
    ORTHO_SCALE = HEIGHT * FRAME[1] / CHARACTER_PX
    SCALE = HEIGHT / BASE_HEIGHT
    LEG_LENGTH = leg_ratio * HEIGHT
    BASE_MESH = base_mesh
    BONES = {name: (tuple(shape(Vector(head))), tuple(shape(Vector(tail))), parent) for name, (head, tail, parent) in BASE_BONES.items()}


def base_pose(p: Poser) -> None:
    p.reset()


def make_action(rig, name: str):
    action = bpy.data.actions.new(name)
    rig.animation_data_create()
    rig.animation_data.action = action
    return action


def walk(p: Poser) -> None:
    """A 24-frame (one second) walk cycle: contact, down, passing, up for each leg."""
    keys = {
        # frame: (thigh_R, shin_R, foot_R, thigh_L, shin_L, foot_L, hips_up)
        0: (24, 4, -12, -20, 12, 18, -0.005),
        3: (16, 22, 0, -12, 40, 14, -0.025),
        6: (2, 6, 0, 8, 62, 8, 0.0),
        9: (-14, 4, 18, 24, 32, -8, 0.015),
    }
    for frame, (tr, sr, fr, tl, sl, fl, up) in keys.items():
        for offset, mirror in ((0, False), (12, True)):
            base_pose(p)
            t_r, s_r, f_r, t_l, s_l, f_l = (tl, sl, fl, tr, sr, fr) if mirror else (tr, sr, fr, tl, sl, fl)
            p.pose("thigh.R", swing=t_r)
            p.pose("shin.R", swing=-s_r)
            p.pose("foot.R", swing=-f_r)
            p.pose("thigh.L", swing=t_l)
            p.pose("shin.L", swing=-s_l)
            p.pose("foot.L", swing=-f_l)
            # Arms swing against the legs; the chest counter-rotates a little.
            arm = (t_l - t_r) * 0.4
            p.pose("upper_arm.R", swing=arm, tilt=ARMS_IN_WALK)
            p.pose("upper_arm.L", swing=-arm, tilt=-ARMS_IN_WALK)
            p.pose("forearm.R", swing=16 + max(0.0, arm) * 0.9)
            p.pose("forearm.L", swing=16 + max(0.0, -arm) * 0.9)
            p.pose("spine", swing=4)
            p.pose("chest", twist=(t_r - t_l) * 0.12)
            p.pose("head", swing=-2)
            p.lift("hips", up)
            p.key(frame + offset)
    base_pose(p)
    # Close the loop: frame 24 equals frame 0.
    _copy_frame(p, 0, CYCLE)


def _copy_frame(p: Poser, source: int, target: int) -> None:
    bpy.context.scene.frame_set(source)
    for bone in p.rig.pose.bones:
        rot, loc = bone.rotation_euler.copy(), bone.location.copy()
        bone.rotation_euler, bone.location = rot, loc
    p.key(target)


def idle(p: Poser) -> None:
    """A two-second breathing loop with a slight sway."""
    for frame, (breath, sway) in {0: (0, 0), 12: (1, 0.5), 24: (0, 1), 36: (1, 0.5), 48: (0, 0)}.items():
        base_pose(p)
        p.pose("chest", swing=-1.5 * breath)
        p.pose("spine", swing=1.0 + 0.5 * breath, tilt=0.8 * (sway - 0.5))
        p.pose("head", swing=-1.0 + 0.6 * breath)
        p.pose("upper_arm.L", tilt=1.5 * breath)
        p.pose("upper_arm.R", tilt=-1.5 * breath)
        p.lift("hips", 0.004 * breath)
        p.key(frame)


def look_around(p: Poser) -> None:
    """Three seconds: looks to his left, then right, then back."""
    for frame, turn in {0: 0, 12: 35, 24: 35, 40: -35, 56: -35, 72: 0}.items():
        base_pose(p)
        p.pose("head", twist=turn * 0.7, swing=-1)
        p.pose("neck", twist=turn * 0.3)
        p.pose("chest", twist=turn * 0.15)
        p.key(frame)


def _breathe(p: Poser, breath: float) -> None:
    """The idle's breathing, layered under other standing motions."""
    p.pose("chest", swing=-1.5 * breath)
    p.pose("spine", swing=1.0 + 0.5 * breath)
    p.lift("hips", 0.004 * breath)


def _at(keys: dict, frame: float) -> tuple:
    """Linear interpolation of a {frame: (values…)} table at `frame`."""
    frames = sorted(keys)
    for a, b in zip(frames, frames[1:]):
        if a <= frame <= b:
            t = (frame - a) / (b - a)
            return tuple(x + (y - x) * t for x, y in zip(keys[a], keys[b]))
    return keys[frames[-1]]


def talk_a(p: Poser) -> None:
    """Two seconds of talking with the right hand: it rises to the chest, beats
    twice on the words with the palm turning open, then settles; the head nods
    into it and the left arm answers a little."""
    keys = {
        # frame: (upper arm swing, forearm swing, hand twist, hand swing, head swing, head tilt, chest twist, breath)
        0: (0, 6, 0, 0, -1, 0, 0, 0),
        7: (24, 70, 30, -15, -3, 0, 5, 0.6),
        14: (20, 60, 45, -25, 2, -2, 4, 1),
        21: (24, 72, 35, -12, -2, 2, 5, 0.8),
        30: (18, 58, 40, -20, 1, 0, 3, 0.5),
        40: (6, 24, 10, 0, 0, 0, 1, 0.2),
        48: (0, 6, 0, 0, -1, 0, 0, 0),
    }
    for frame, (arm, forearm, twist, wrist, head, tilt, chest, breath) in keys.items():
        base_pose(p)
        _breathe(p, breath)
        p.pose("upper_arm.R", swing=arm, tilt=-4 * breath)
        p.pose("forearm.R", swing=forearm)
        p.pose("hand.R", swing=wrist, twist=twist)
        p.pose("upper_arm.L", swing=-3 * breath)
        p.pose("forearm.L", swing=6 + 6 * breath)
        p.pose("chest", swing=-1.5 * breath, twist=chest)
        p.pose("head", swing=head, tilt=tilt)
        p.key(frame)


def talk_b(p: Poser) -> None:
    """Two seconds of talking with both hands: they open outwards, palms up, as
    if weighing the question, and sink back. The left hand moves less and a beat
    later than the right, and the head tilts."""
    right = {
        # frame: (upper arm swing, upper arm out, forearm swing, hand twist)
        0: (0, 0, 6, 0), 10: (14, 10, 55, 35), 22: (16, 12, 60, 40), 34: (6, 4, 26, 12), 48: (0, 0, 6, 0),
    }
    left = {
        0: (0, 0, 6, 0), 13: (10, 8, 45, 28), 25: (12, 9, 50, 34), 37: (4, 3, 20, 8), 48: (0, 0, 6, 0),
    }
    rest = {
        # frame: (head swing, head tilt, breath)
        0: (-1, 0, 0), 12: (-2, 4, 0.7), 24: (2, 3, 1), 36: (0, -1, 0.3), 48: (-1, 0, 0),
    }
    for frame in sorted(set(right) | set(left) | set(rest)):
        r_arm, r_out, r_fore, r_twist = _at(right, frame)
        l_arm, l_out, l_fore, l_twist = _at(left, frame)
        head, tilt, breath = _at(rest, frame)
        base_pose(p)
        _breathe(p, breath)
        p.pose("upper_arm.R", swing=r_arm, tilt=-r_out)
        p.pose("forearm.R", swing=r_fore)
        p.pose("hand.R", twist=r_twist)
        p.pose("upper_arm.L", swing=l_arm, tilt=l_out)
        p.pose("forearm.L", swing=l_fore)
        p.pose("hand.L", twist=-l_twist)
        p.pose("head", swing=head, tilt=tilt)
        p.key(frame)


def fidget_a(p: Poser) -> None:
    """Two seconds: shifts his weight onto one leg, the other knee easing, and
    looks down at the floor, then back."""
    keys = {
        # frame: (spine tilt, hips down, relaxed knee, head swing, head tilt, breath)
        0: (0, 0, 0, -1, 0, 0),
        12: (5, -0.008, 1, 16, -4, 0.6),
        26: (5.5, -0.009, 1, 22, -2, 1),
        38: (-1, -0.003, 0.3, 5, 1, 0.4),
        48: (0, 0, 0, -1, 0, 0),
    }
    for frame, (lean, down, knee, head, tilt, breath) in keys.items():
        base_pose(p)
        _breathe(p, breath)
        p.pose("spine", swing=1.0 + 0.5 * breath, tilt=lean)
        p.pose("thigh.L", tilt=-lean * 0.6)
        p.pose("thigh.R", swing=7 * knee, tilt=-lean * 0.6)
        p.pose("shin.R", swing=-14 * knee)
        p.pose("foot.R", swing=7 * knee)
        p.lift("hips", down)
        p.pose("neck", swing=head * 0.3)
        p.pose("head", swing=head, tilt=tilt)
        p.key(frame)


def fidget_b(p: Poser) -> None:
    """Three seconds: raises his right hand towards his face and studies it,
    turning it over; the forearm falls first, then the arm."""
    keys = {
        # frame: (upper arm swing, upper arm in, forearm swing, hand twist, hand swing, head swing, head turn, head tilt)
        0: (0, 0, 6, 0, 0, -1, 0, 0),
        14: (42, 8, 112, 60, -10, 20, -8, 0),
        30: (45, 8, 118, -20, -22, 24, -10, 6),
        46: (44, 8, 115, 40, -12, 22, -8, 3),
        53: (40, 6, 60, 20, -4, 12, -4, 1),
        62: (10, 2, 22, 5, 0, 3, -1, 0),
        72: (0, 0, 6, 0, 0, -1, 0, 0),
    }
    for frame, (arm, inward, forearm, twist, wrist, head, turn, tilt) in keys.items():
        base_pose(p)
        _breathe(p, 0.5)
        p.pose("upper_arm.R", swing=arm, tilt=inward)
        p.pose("forearm.R", swing=forearm)
        p.pose("hand.R", swing=wrist, twist=twist)
        p.pose("neck", swing=head * 0.3)
        p.pose("head", swing=head, twist=turn, tilt=tilt)
        p.key(frame)


def _squat(p: Poser, degrees: float, knee: str = "") -> None:
    """Bends both legs so the feet stay planted: thighs forward, shins back twice
    as far, feet level, and the hips drop by how much the legs fold."""
    for side in (".L", ".R"):
        p.pose("thigh" + side, swing=degrees)
        p.pose("shin" + side, swing=-2 * degrees)
        # A foot's swing turns its toe down; the shin's lean has already
        # turned it down by DEGREES, so it turns back up to stay flat.
        p.pose("foot" + side, swing=-degrees)
    p.lift("hips", -LEG_LENGTH * (1 - math.cos(math.radians(degrees))))


def pickup_low(p: Poser) -> None:
    """Two seconds: stoops from the waist, knees easing, to take something off
    the floor with his right hand (the grab is at frame 22), then straightens
    with it to his waist. A stoop, not a squat: painted over, a deep squat on
    tiptoe read as a jump."""
    keys = {
        # frame: (squat, spine, chest, head, right upper arm, right forearm, right hand, left upper arm)
        0: (0, 1, 0, -1, 0, 6, 0, 0),
        10: (12, 34, 18, 10, 60, 10, 0, 10),
        20: (20, 50, 26, 18, 96, 6, -8, 16),
        26: (20, 50, 26, 18, 96, 10, 18, 16),
        36: (8, 18, 8, 4, 40, 62, 10, 6),
        48: (0, 1, 0, -1, 0, 6, 0, 0),
    }
    for frame, (squat, spine, chest, head, arm, forearm, hand, left) in keys.items():
        base_pose(p)
        _squat(p, squat)
        p.pose("spine", swing=spine)
        p.pose("chest", swing=chest)
        p.pose("neck", swing=head * 0.5)
        p.pose("head", swing=head)
        p.pose("upper_arm.R", swing=arm)
        p.pose("forearm.R", swing=forearm)
        p.pose("hand.R", swing=hand)
        p.pose("upper_arm.L", swing=left, tilt=4)
        p.pose("forearm.L", swing=10 + left * 0.5)
        p.key(frame)


def pickup_high(p: Poser) -> None:
    """Two seconds: reaches up above his head with his right hand, rising onto
    his toes (the grab is at frame 18), and brings it down to his chest."""
    keys = {
        # frame: (right upper arm, right forearm, right hand, head, spine, toes)
        0: (0, 6, 0, -1, 1, 0),
        10: (110, 20, -10, -10, -2, 0.5),
        18: (148, 10, 15, -16, -5, 1),
        24: (146, 14, 25, -14, -4, 1),
        34: (40, 80, 10, -2, 0, 0.2),
        48: (0, 6, 0, -1, 1, 0),
    }
    for frame, (arm, forearm, hand, head, spine, toes) in keys.items():
        base_pose(p)
        p.pose("spine", swing=spine)
        p.pose("chest", swing=spine * 0.5)
        p.pose("head", swing=head)
        p.pose("neck", swing=head * 0.4)
        p.pose("upper_arm.R", swing=arm, tilt=-4)
        p.pose("forearm.R", swing=forearm)
        p.pose("hand.R", swing=hand)
        p.pose("upper_arm.L", swing=4 * toes, tilt=-3 * toes)
        for side in (".L", ".R"):
            p.pose("foot" + side, swing=-14 * toes)
        p.lift("hips", 0.03 * toes)
        p.key(frame)


def use(p: Poser) -> None:
    """A second and a half: reaches forward at chest height and works something
    with his right hand, a push and a turn (contact at frame 16)."""
    keys = {
        # frame: (upper arm, forearm, hand swing, hand twist, spine, head)
        0: (0, 6, 0, 0, 1, -1),
        10: (58, 30, -10, 0, 6, 4),
        16: (64, 20, 10, 0, 8, 5),
        24: (62, 26, -4, 35, 7, 4),
        36: (0, 6, 0, 0, 1, -1),
    }
    for frame, (arm, forearm, hand, twist, spine, head) in keys.items():
        base_pose(p)
        p.pose("spine", swing=spine)
        p.pose("head", swing=head)
        p.pose("upper_arm.R", swing=arm)
        p.pose("forearm.R", swing=forearm)
        p.pose("hand.R", swing=hand, twist=twist)
        p.key(frame)


def give(p: Poser) -> None:
    """A second and a half: holds his right hand out, palm up, offering
    something (the hand-over is at frame 18), then draws it back."""
    keys = {
        # frame: (upper arm, forearm, hand twist, spine, head)
        0: (0, 6, 0, 1, -1),
        12: (46, 40, 40, 4, 2),
        18: (50, 36, 45, 5, 3),
        26: (46, 40, 40, 4, 2),
        36: (0, 6, 0, 1, -1),
    }
    for frame, (arm, forearm, twist, spine, head) in keys.items():
        base_pose(p)
        p.pose("spine", swing=spine)
        p.pose("head", swing=head)
        p.pose("upper_arm.R", swing=arm, tilt=2)
        p.pose("forearm.R", swing=forearm)
        p.pose("hand.R", swing=-6, twist=twist)
        p.key(frame)


def flare(p: Poser) -> None:
    """A second and a half as a memory takes him (played as a flashback opens):
    a sharp breath in, the head lifting, arms tensing out with the fingers
    spread, a held moment, then release."""
    keys = {
        # frame: (chest, spine, head, neck, arms out, forearm, fingers, hips up)
        0: (0, 0, 0, 0, 0, 0, 0, 0.0),
        6: (-8, -5, -14, -6, 12, 25, -20, 0.01),
        14: (-9, -6, -16, -7, 14, 22, -24, 0.012),
        26: (-3, -2, -5, -2, 5, 8, -6, 0.004),
        38: (0, 0, 0, 0, 0, 0, 0, 0.0),
    }
    for frame, (chest, spine, head, neck, out, forearm, fingers, up) in keys.items():
        base_pose(p)
        p.pose("chest", swing=chest)
        p.pose("spine", swing=spine)
        p.pose("head", swing=head)
        p.pose("neck", swing=neck)
        p.pose("upper_arm.L", tilt=out)
        p.pose("upper_arm.R", tilt=-out)
        for side in (".L", ".R"):
            p.pose("forearm" + side, swing=forearm)
            p.pose("hand" + side, swing=fingers)
        p.lift("hips", up)
        p.key(frame)


ANIMATIONS = {
    "walk": (walk, CYCLE, True),
    "idle": (idle, 48, True),
    "look_around": (look_around, 72, False),
    "talk_a": (talk_a, 48, True),
    "talk_b": (talk_b, 48, True),
    "fidget_a": (fidget_a, 48, False),
    "fidget_b": (fidget_b, 72, False),
    "pickup_low": (pickup_low, 48, False),
    "pickup_high": (pickup_high, 48, False),
    "use": (use, 36, False),
    "give": (give, 36, False),
    "flare": (flare, 38, False),
}
# Moments the game reacts to, in 24 fps frames: footsteps on each heel strike,
# the instant a hand closes on something.
EVENTS = {
    "walk": {0: "step", 12: "step"},
    "pickup_low": {22: "grab"},
    "pickup_high": {18: "grab"},
    "use": {16: "use"},
    "give": {18: "give"},
    "flare": {4: "flare"},
}
DIRECTIONS = {"d": 0.0, "r": 90.0, "u": 180.0}


def setup_camera():
    camera_data = bpy.data.cameras.new("SpriteCamera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = ORTHO_SCALE
    camera = bpy.data.objects.new("SpriteCamera", camera_data)
    bpy.context.collection.objects.link(camera)
    center = CAMERA_CENTER_Z
    distance = 10.0
    tilt = math.radians(TILT_DEG)
    camera.location = (0.0, -distance * math.cos(tilt), center + distance * math.sin(tilt))
    camera.rotation_euler = (math.radians(90.0 - TILT_DEG), 0.0, 0.0)
    bpy.context.scene.camera = camera
    return camera


def look_at(obj, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_render() -> None:
    """EEVEE with a black world: two cold rim lights from behind and a faint one
    from above the camera, so the dark body shows its form only at the edges and
    where muscle turns to the light."""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 32
    world = bpy.data.worlds.new("Black")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    scene.world = world
    target = Vector((0.0, 0.0, 1.1))
    for name, location, power, size in (
        ("RimLeft", (-1.7, 1.6, 2.3), 750.0, 1.2),
        ("RimRight", (1.7, 1.6, 2.3), 750.0, 1.2),
        ("Top", (0.0, -1.2, 3.4), 25.0, 2.0),
    ):
        light_data = bpy.data.lights.new(name, "AREA")
        light_data.energy = power
        light_data.size = size
        light_data.color = (0.82, 0.88, 1.0)
        light = bpy.data.objects.new(name, light_data)
        light.location = location
        bpy.context.scene.collection.objects.link(light)
        look_at(light, target)
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = FRAME
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.fps = 24
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"


def pixel(scene, camera, world: Vector) -> list[float]:
    ndc = world_to_camera_view(scene, camera, world)
    return [round(ndc.x * FRAME[0], 2), round((1.0 - ndc.y) * FRAME[1], 2)]


def anchors(scene, camera, rig, eyes) -> dict:
    bones = rig.pose.bones
    world = rig.matrix_world
    head_center = world @ ((bones["head"].head + bones["head"].tail) / 2)
    to_camera = (camera.matrix_world.translation - head_center).normalized()
    eye_points = [eye.matrix_world.translation.copy() for eye in eyes]
    visible = [(point - head_center).normalized().dot(to_camera) > 0.1 for point in eye_points]
    body_back = -(world.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
    chest_mid = world @ ((bones["chest"].head + bones["chest"].tail) / 2)
    return {
        "head": pixel(scene, camera, head_center),
        "eye_l": pixel(scene, camera, eye_points[0]),
        "eye_r": pixel(scene, camera, eye_points[1]),
        "eyes_visible": visible,
        "shoulder_l": pixel(scene, camera, world @ bones["upper_arm.L"].head),
        "shoulder_r": pixel(scene, camera, world @ bones["upper_arm.R"].head),
        "back": pixel(scene, camera, chest_mid + body_back * 0.12 + Vector((0.0, 0.0, 0.08))),
        "hand_l": pixel(scene, camera, world @ bones["hand.L"].tail),
        "hand_r": pixel(scene, camera, world @ bones["hand.R"].tail),
        "feet": pixel(scene, camera, world @ Vector((0.0, 0.0, 0.0))),
    }


def foot_speed_px(scene, camera, rig, fps_frames: int) -> float:
    """Ground speed implied by the walk: how far the planted foot slides back per second, in pixels."""
    bones = rig.pose.bones
    samples = []
    for frame in range(0, 7):
        scene.frame_set(frame)
        samples.append((rig.matrix_world @ bones["foot.R"].head).y)
    metres_per_frame = (samples[-1] - samples[0]) / 6.0
    return abs(metres_per_frame) * 24.0 * CHARACTER_PX / HEIGHT


def sample_times(length: int, loop: bool, fps: float) -> list[float]:
    """When to sample each output frame, in 24 fps frames. A loop of LENGTH frames
    lasts LENGTH/24 s and does not repeat its first pose; a one-shot ends on its last."""
    step = 24.0 / fps
    count = round(length / step) if loop else int(length / step + 1e-6) + 1
    return [index * step for index in range(count)]


def event_frames(anim: str, times: list[float], length: int, loop: bool) -> list[dict]:
    """EVENTS for `anim` moved onto the output frame sampled nearest to each one."""
    events = []
    for time, name in sorted(EVENTS.get(anim, {}).items()):
        index = min(range(len(times)), key=lambda i: abs(times[i] - time))
        if loop and abs(length - time) < abs(times[index] - time):
            index = 0  # nearer to the loop's restart than to any sampled frame
        events.append({"frame": index, "name": name})
    return events


def render(rig, eyes, camera, out: Path, anims: list[str], dirs: list[str], fps: float, preview: bool = False) -> dict:
    scene = bpy.context.scene
    poser = Poser(rig)
    meta = {"frame_size": list(FRAME), "character_px": CHARACTER_PX, "fps": fps, "animations": {}}
    for anim in anims:
        build, length, loop = ANIMATIONS[anim]
        make_action(rig, anim)
        build(poser)
        for direction in dirs:
            rig.rotation_euler = (0.0, 0.0, math.radians(DIRECTIONS[direction]))
            key = f"{anim}_{direction}"
            frames, anchor_list = [], []
            times = sample_times(length, loop, fps)[:1] if preview else sample_times(length, loop, fps)
            for index, time in enumerate(times):
                scene.frame_set(int(time), subframe=time - int(time))
                path = out / key / f"{key}_{index:03d}.png"
                scene.render.filepath = str(path)
                bpy.ops.render.render(write_still=True)
                frames.append(path.name)
                anchor_list.append(anchors(scene, camera, rig, eyes))
            entry = {"fps": fps, "frames": frames, "loop": loop, "anchors": anchor_list, "events": event_frames(anim, times, length, loop)}
            if anim == "walk":
                rig.rotation_euler = (0.0, 0.0, 0.0)
                entry["ground_px_per_second"] = round(foot_speed_px(scene, camera, rig, length), 1)
                rig.rotation_euler = (0.0, 0.0, math.radians(DIRECTIONS[direction]))
            meta["animations"][key] = entry
    rig.rotation_euler = (0.0, 0.0, 0.0)
    (out / "anchors.json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-mesh", default=os.environ.get("HERO_BASE_MESH"),
                        help="Blender Studio's body_male_realistic.blend (or set HERO_BASE_MESH)")
    parser.add_argument("--config", help="JSON with any of the keys in this script's docstring")
    parser.add_argument("--out", required=True)
    parser.add_argument("--anims", default=",".join(ANIMATIONS), help="comma-separated; default all")
    parser.add_argument("--dirs", default="r,u,d")
    parser.add_argument("--fps", type=float, default=12.0)
    parser.add_argument("--blend")
    parser.add_argument("--preview", action="store_true", help="render only each animation's first frame")
    args = parser.parse_args(argv)
    if not args.base_mesh or not Path(args.base_mesh).is_file():
        raise SystemExit("pose_rig: --base-mesh (or HERO_BASE_MESH) must name body_male_realistic.blend")
    configure(json.loads(Path(args.config).read_text()) if args.config else {}, Path(args.base_mesh).resolve())
    clear_scene()
    body, eyes = build_body()
    rig = build_rig()
    bind(body, eyes, rig)
    finish_body(body)
    camera = setup_camera()
    setup_render()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    meta = render(rig, eyes, camera, out, args.anims.split(","), args.dirs.split(","), args.fps, args.preview)
    if args.blend:
        Path(args.blend).parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=args.blend)
    summary = {k: {"frames": len(v["frames"]), **({"ground_px_per_second": v["ground_px_per_second"]} if "ground_px_per_second" in v else {})} for k, v in meta["animations"].items()}
    print("HERO_RENDER", json.dumps(summary))


main()
