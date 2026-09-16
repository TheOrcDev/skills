"""Author the complete semantic clip set for one subject on its existing rig.

Usage (Blender 4.5):
  Blender --background --factory-startup --python-exit-code 1 --python author_clips.py -- \
      --contract rig-contract.json --source rigged.fbx|rigged.blend --output <candidate directory>

The contract's family and calibration drive every pose. The script never
overwrites a candidate directory, keeps every original mesh vertex, UV and
texture, transfers stray Root skin weights to the bones that carry the region
so Root stays a stationary navigation root, solves full-chain leg IK with real
sole contact, and bakes evaluated poses to keyframes (no live constraints
survive in the saved candidate). Output: <Folder>_Actions.blend + receipt.json
(forward axis, anchor offset, per-clip contacts, IK residuals, worst
penetration, final-frame diagnostics, nominal locomotion speed).
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
sys.path.insert(0, str(HERE))
import blender_common as bc  # noqa: E402
import calibration as cal  # noqa: E402
import contract as contract_module  # noqa: E402
import motion as mo  # noqa: E402

FPS = 30
UP = Vector((0, 0, 1))


class Creature:
    def __init__(self, calibration: dict, contract: dict):
        self.cal = calibration
        self.contract = contract
        self.rig = bc.find_rig()
        self.mesh = bc.main_mesh(self.rig)
        self.deforming = bc.deforming_meshes(self.rig)
        self.rigid = bc.rigid_meshes(self.rig)
        self.scene = bpy.context.scene
        self.scene.render.fps = FPS
        bones = {b.name for b in self.rig.data.bones}
        errors = cal.validate(calibration, bones)
        if errors:
            raise RuntimeError(f"{contract['subjectId']} calibration errors: {errors}")
        self.rig.animation_data_clear()
        for action in list(bpy.data.actions):
            bpy.data.actions.remove(action)
        bc.clear_pose(self.rig)
        self.rest = bc.rest_world_vertices(self.mesh)
        self.floor = min(v.z for v in self.rest)  # lowest rest vertex: nothing may go below this plane
        self.contact_floor = self.floor             # feet contact plane, refined once soles are known
        head = self.rig.data.bones[self.cal['head']]
        direction = self.rig.matrix_world.to_3x3() @ (head.tail_local - head.head_local)
        self.forward = Vector((0, 1 if direction.y >= 0 else -1, 0))
        self.lateral = Vector((1, 0, 0))
        core = self.core_vertex_ids()
        self.height = max(self.rest[i].z for i in core) - self.floor
        along = [self.rest[i].dot(self.forward) for i in core]
        self.length = max(along) - min(along)
        self.body_rest_z = bc.bone_world_head(self.rig, self.cal['body']).z
        self.ground = self.floor - self.cal.get('anchorOffset', 0.0)
        self.receipt = {
            'subject': self.cal.get('subjectId') or contract['subjectId'], 'family': self.cal['family'], 'mode': self.cal['mode'],
            'forward': list(self.forward), 'bodyHeight': self.height, 'bodyLength': self.length,
            'floor': self.floor, 'groundForDeath': self.ground, 'anchorOffset': self.cal.get('anchorOffset', 0.0),
            'rigidMeshes': [(o.name, o.parent_type, o.parent_bone) for o in self.rigid],
            'clips': {}, 'creditsSpent': 0, 'productionInstalled': False, 'operatorAccepted': False,
        }
        self.transfer_root_weights()
        self.attach_rigid_parts()
        if self.cal.get('addJaw') and not self.cal.get('jaw'):
            self.add_jaw_bone()
        self.setup_legs()
        self.allowed_z = [min(self.contact_floor, v.z) for v in self.rest]
        self.sign_cache = {}

    # ----- geometry / weights -------------------------------------------------
    def core_vertex_ids(self) -> list[int]:
        names = set(self.cal['coreGroups'])
        return [v.index for v in self.mesh.data.vertices if bc.dominant_group(self.mesh, v) in names]

    def attach_rigid_parts(self) -> None:
        attached = []
        for obj in list(self.rigid):
            if obj.parent_type == 'BONE' and obj.parent_bone:
                dominant = bc.skin_rigid_to_surface(obj, self.rig, self.mesh)
                attached.append({'object': obj.name, 'formerParentBone': obj.parent_bone or None, 'surfaceWeights': dominant})
        self.receipt['rigidPartsSkinnedToSurface'] = attached
        self.rigid = bc.rigid_meshes(self.rig)
        self.deforming = bc.deforming_meshes(self.rig)

    def add_jaw_bone(self) -> None:
        """Add a lower-jaw bone under the head and move the lower muzzle's head weight onto it.

        The hinge sits on the head axis at `addJaw['hinge']` of the head length; vertices in the
        front part of the head that lie below the axis by more than `addJaw['depth']` body heights
        move their Head weight to Jaw with a smooth falloff. Topology, UVs and every other weight
        are untouched.
        """
        spec = self.cal['addJaw']
        head_bone = self.rig.data.bones[self.cal['head']]
        head = self.rig.matrix_world @ head_bone.head_local
        tail = self.rig.matrix_world @ head_bone.tail_local
        axis = tail - head
        length = axis.length
        unit = axis / length
        depth = spec.get('depth', 0.03) * self.height
        hinge = spec.get('hinge', 0.45)
        head_group = self.mesh.vertex_groups.get(self.cal['head'])
        if head_group is None:
            raise RuntimeError('head vertex group missing')
        jaw_group = self.mesh.vertex_groups.new(name='Jaw')
        moved = []
        for v in self.mesh.data.vertices:
            weight = next((g.weight for g in v.groups if g.group == head_group.index), 0.0)
            if weight <= 0:
                continue
            p = self.rest[v.index]
            t_along = (p - head).dot(unit) / length
            below = (head + unit * (t_along * length)).z - p.z
            factor = mo.smooth(hinge - 0.08, hinge + 0.08, t_along) * mo.smooth(depth * 0.5, depth * 1.5, below)
            share = weight * factor
            if share > 1e-5:
                head_group.add([v.index], weight - share, 'REPLACE')
                jaw_group.add([v.index], share, 'REPLACE')
                moved.append(v.index)
        if len(moved) < 20:
            raise RuntimeError(f'jaw region too small ({len(moved)} vertices); adjust addJaw calibration')
        rig_from_world = self.rig.matrix_world.inverted()
        hinge_world = head + unit * (hinge * length) - UP * depth
        tip_world = tail - UP * depth * 1.5
        bpy.context.view_layer.objects.active = self.rig
        self.rig.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        jaw = self.rig.data.edit_bones.new('Jaw')
        jaw.head = rig_from_world @ hinge_world
        jaw.tail = rig_from_world @ tip_world
        jaw.parent = self.rig.data.edit_bones[self.cal['head']]
        bpy.ops.object.mode_set(mode='OBJECT')
        self.cal['jaw'] = 'Jaw'
        self.receipt['jawBone'] = {'weightedVertices': len(moved), 'hinge': hinge, 'depthBodyHeights': spec.get('depth', 0.03)}

    def transfer_root_weights(self) -> None:
        """Move every Root skin weight to the bones that actually carry that region.

        Bone-heat weighting gave the navigation root real influence on bellies, feet and
        wing membranes. A vertex that also belongs to other bones gives its Root share to
        them in proportion; a vertex weighted to Root alone goes to the nearest deforming
        bone segment. Root ends up deforming nothing, so it can stay a stationary root.
        """
        moved = {}
        rig_from_world = self.rig.matrix_world.inverted()
        segments = [(b.name, b.head_local.copy(), b.tail_local.copy()) for b in self.rig.data.bones if b.name != self.cal['root']]

        def nearest_bone(point):
            best, best_distance = None, float('inf')
            for name, head, tail in segments:
                axis = tail - head
                length = axis.length_squared
                s = 0.0 if length < 1e-12 else max(0.0, min(1.0, (point - head).dot(axis) / length))
                distance = (head + axis * s - point).length
                if distance < best_distance:
                    best, best_distance = name, distance
            return best

        for mesh in self.deforming:
            root = mesh.vertex_groups.get(self.cal['root'])
            if root is None:
                continue
            destinations = {}
            for v in mesh.data.vertices:
                weight = next((g.weight for g in v.groups if g.group == root.index), 0.0)
                if weight <= 0:
                    continue
                others = [(g.group, g.weight) for g in v.groups if g.group != root.index and g.weight > 0]
                if others:
                    total = sum(w for _, w in others)
                    for group_index, group_weight in others:
                        mesh.vertex_groups[group_index].add([v.index], group_weight + weight * group_weight / total, 'REPLACE')
                        name = mesh.vertex_groups[group_index].name
                        destinations[name] = destinations.get(name, 0) + 1
                else:
                    name = nearest_bone(rig_from_world @ (mesh.matrix_world @ v.co))
                    group = mesh.vertex_groups.get(name) or mesh.vertex_groups.new(name=name)
                    group.add([v.index], weight, 'REPLACE')
                    destinations[name] = destinations.get(name, 0) + 1
                root.remove([v.index])
            moved[mesh.name] = destinations
        self.receipt['rootWeightsMovedTo'] = moved
        self.receipt['rootWeightsMovedToBody'] = {m: sum(d.values()) for m, d in moved.items()}

    # ----- rotation helpers ---------------------------------------------------
    def pose_rotation(self, bone) -> Matrix:
        """Armature-space rotation of a pose bone from the FK rotations set so far (no depsgraph needed)."""
        rest = bone.bone.matrix_local.to_3x3()
        if bone.parent is None:
            return rest @ bone.rotation_quaternion.to_matrix()
        parent_rest = bone.parent.bone.matrix_local.to_3x3()
        return self.pose_rotation(bone.parent) @ (parent_rest.inverted() @ rest) @ bone.rotation_quaternion.to_matrix()

    def rotate(self, name: str, axis: Vector, angle: float) -> None:
        """Rotate a bone about a world axis, honouring the parent chain's current FK rotations."""
        if abs(angle) < 1e-9:
            return
        bone = self.rig.pose.bones[name]
        bone.rotation_mode = 'QUATERNION'
        arm_axis = self.rig.matrix_world.to_3x3().inverted() @ Vector(axis)
        local = self.pose_rotation(bone).inverted() @ arm_axis
        bone.rotation_quaternion = bone.rotation_quaternion @ Quaternion(local.normalized(), angle)

    def translate(self, name: str, delta: Vector) -> None:
        bone = self.rig.pose.bones[name]
        arm_delta = self.rig.matrix_world.to_3x3().inverted() @ Vector(delta)
        bone.location = bone.location + bone.bone.matrix_local.to_3x3().inverted() @ arm_delta

    def sign(self, name: str, axis: Vector, goal: Vector) -> float:
        key = (name, tuple(round(a, 4) for a in axis), tuple(round(g, 4) for g in goal))
        if key in self.sign_cache:
            return self.sign_cache[key]
        bone = self.rig.data.bones[name]
        head = self.rig.matrix_world @ bone.head_local
        tail = self.rig.matrix_world @ bone.tail_local
        vector = tail - head
        rotated = Quaternion(Vector(axis).normalized(), 0.05) @ vector
        delta = rotated - vector
        value = 1.0 if delta.dot(goal) >= 0 else -1.0
        self.sign_cache[key] = value
        return value

    def pitch(self, name: str, angle: float) -> None:
        """Positive angle: the bone tip moves down."""
        self.rotate(name, self.lateral, angle * self.sign(name, self.lateral, -UP))

    def pitch_forward(self, name: str, angle: float) -> None:
        """Positive angle: the bone tip moves toward the creature's forward direction."""
        self.rotate(name, self.lateral, angle * self.sign(name, self.lateral, self.forward))

    def yaw(self, name: str, angle: float) -> None:
        """Positive angle: the bone tip moves toward the creature's left (+X side)."""
        self.rotate(name, UP, angle * self.sign(name, UP, self.lateral))

    def yaw_out(self, name: str, angle: float) -> None:
        """Positive angle: the bone tip moves away from the midline."""
        head = self.rig.matrix_world @ self.rig.data.bones[name].head_local
        tail = self.rig.matrix_world @ self.rig.data.bones[name].tail_local
        side = tail.x if abs(tail.x) > 1e-6 else head.x
        goal = Vector((1 if side >= 0 else -1, 0, 0))
        self.rotate(name, UP, angle * self.sign(name, UP, goal))

    def roll(self, name: str, angle: float) -> None:
        """Rotate about the forward axis (right-hand rule about forward)."""
        self.rotate(name, self.forward, angle)

    def flap(self, name: str, angle: float) -> None:
        """Positive angle: the wing bone tip moves down (downstroke)."""
        self.rotate(name, self.forward, angle * self.sign(name, self.forward, -UP))

    def lift(self, name: str, angle: float) -> None:
        """Positive angle: the bone tip rises, whatever direction the limb points."""
        bone = self.rig.data.bones[name]
        direction = (self.rig.matrix_world.to_3x3() @ (bone.tail_local - bone.head_local))
        direction.z = 0.0
        if direction.length < 1e-6:
            direction = self.lateral.copy()
        axis = direction.normalized().cross(UP)
        self.rotate(name, axis, angle * self.sign(name, axis, UP))

    def splay(self, name: str, angle: float) -> None:
        """Positive angle: the bone tip swings away from the midline about the forward axis."""
        head = self.rig.matrix_world @ self.rig.data.bones[name].head_local
        goal = Vector((1 if head.x >= 0 else -1, 0, 0))
        self.rotate(name, self.forward, angle * self.sign(name, self.forward, goal))

    def sweep_back(self, name: str, angle: float) -> None:
        """Positive angle: the bone tip moves backward (away from forward) about the up axis."""
        self.rotate(name, UP, angle * self.sign(name, UP, -self.forward))

    # ----- legs --------------------------------------------------------------
    def setup_legs(self) -> None:
        self.legs = []
        for spec in self.cal['legs']:
            target = bpy.data.objects.new('IK_' + spec['id'], None)
            self.scene.collection.objects.link(target)
            ankle = self.rig.matrix_world @ self.rig.data.bones[spec['ik']].tail_local
            target.location = ankle
            target.rotation_mode = 'QUATERNION'
            target.rotation_quaternion = (self.rig.matrix_world @ self.rig.data.bones[spec['tip']].matrix_local).to_quaternion()
            ik = self.rig.pose.bones[spec['ik']].constraints.new('IK')
            ik.target = target
            ik.chain_count = spec['ikChain']
            ik.use_stretch = False
            ik.iterations = 500
            if spec['ikChain'] >= 3:
                # Multi-joint chains are redundant for the solver; hinge every joint after the
                # root (twist and yaw locked) so the solution is unique and history-free.
                for name in spec['chain'][1:spec['ikChain']]:
                    joint = self.rig.pose.bones[name]
                    joint.lock_ik_y = True
                    joint.lock_ik_z = True
            orientation = self.rig.pose.bones[spec['tip']].constraints.new('COPY_ROTATION')
            orientation.target = target
            orientation.owner_space = 'WORLD'
            orientation.target_space = 'WORLD'
            ankle_z = ankle.z + self.height * 0.02
            sole = bc.sole_vertices(self.mesh, spec['sole'], max_z=ankle_z, threshold=0.05)
            contact = list(sole)
            hardened = self.harden_sole(spec, sole, ankle_z) if self.cal['mode'] == 'ground' else 0
            if not sole and self.cal['mode'] == 'ground':
                raise RuntimeError(f"{spec['id']} has no sole vertices in {spec['sole']}")
            chain_bones = [self.rig.data.bones[n] for n in spec['chain'][:spec['ikChain']]]
            reach = sum((self.rig.matrix_world.to_3x3() @ (b.tail_local - b.head_local)).length for b in chain_bones)
            hip = self.rig.matrix_world @ chain_bones[0].head_local
            self.legs.append({**spec, 'target': target, 'ikConstraint': ik, 'orientation': orientation,
                              'rest': ankle.copy(), 'soleVertices': sole, 'contactVertices': sorted(set(sole) | set(contact)), 'reach': reach,
                              'hipDrop': hip.z - ankle.z, 'hipOffset': ankle - hip})
        if self.legs and self.cal['mode'] == 'ground':
            # Some sources rest a jaw or belly below their feet; the feet plane is where soles touch.
            self.contact_floor = min(self.rest[i].z for leg in self.legs for i in leg['soleVertices'])
            self.receipt['contactFloor'] = self.contact_floor
        self.receipt['legs'] = [{'id': l['id'], 'soleVertices': len(l['soleVertices']), 'contactVertices': len(l['contactVertices']), 'reach': l['reach'],
                                 'hipDrop': l['hipDrop'], 'restAnkle': list(l['rest'])} for l in self.legs]

    def stride_limit(self, crouch: float) -> float:
        """Longest stride every leg can reach with the body lowered by `crouch` units.

        Reach is measured from the hip with the body crouched; the stride is centred on the
        rest ankle, which may sit ahead of or behind the hip, so the tighter side limits it.
        A margin covers the swing's Hermite overshoot beyond the stance endpoints.
        """
        limit = float('inf')
        for leg in self.legs:
            vertical = max(0.0, leg['hipDrop'] - crouch)
            lateral = abs(leg['hipOffset'].x)
            horizontal_room = leg['reach'] ** 2 - vertical ** 2 - lateral ** 2
            if horizontal_room <= 0:
                raise RuntimeError(f"{leg['id']} cannot reach the ground with crouch {crouch}")
            radius = math.sqrt(horizontal_room)
            offset = abs(leg['hipOffset'].dot(self.forward))
            limit = min(limit, 2 * max(0.0, radius - offset) * 0.85)
        return limit

    def harden_sole(self, spec: dict, sole: list[int], max_z: float) -> int:
        """Give the paw/tarsus underside full weight to its own bone so contacts do not blend with the shin.

        Only vertices already dominated by the sole bone and lying below the ankle are changed;
        topology, UVs and every other vertex keep their original weights."""
        if not self.cal.get('hardenSoles', True):
            return 0
        primary = self.mesh.vertex_groups.get(spec['sole'][0]) or self.mesh.vertex_groups.new(name=spec['sole'][0])
        count = 0
        for index in sole:
            v = self.mesh.data.vertices[index]
            if self.rest[index].z > max_z:
                continue
            # collect group indices first: removing while iterating v.groups leaves stale elements
            others = [g.group for g in v.groups if g.group != primary.index]
            for group_index in others:
                self.mesh.vertex_groups[group_index].remove([index])
            primary.add([index], 1.0, 'REPLACE')
            if any(g.group != primary.index and g.weight > 0 for g in v.groups):
                raise RuntimeError(f'sole vertex {index} kept foreign weights after hardening')
            count += 1
        self.receipt.setdefault('hardenedSoleVertices', {})[spec['id']] = count
        return count

    def set_leg_influence(self, value: float) -> None:
        for leg in self.legs:
            leg['ikConstraint'].influence = value
            leg['orientation'].influence = value

    def reset_legs(self) -> None:
        for leg in self.legs:
            leg['target'].location = leg['rest'].copy()
            leg['lift'] = 0.0
            leg['planted'] = True

    def settle_feet(self, iterations: int = 3) -> None:
        active = [leg for leg in self.legs if leg['ikConstraint'].influence > 0]
        if not active:
            return
        for _ in range(iterations):
            bpy.context.view_layer.update()
            posed = bc.evaluated_world_vertices(self.mesh)
            for leg in active:
                lowest = min(posed[i].z for i in leg['contactVertices'])
                leg['target'].location.z += self.contact_floor + leg['lift'] - lowest
        bpy.context.view_layer.update()

    def lift_clear_of_floor(self, tolerance: float = 0.003) -> None:
        """If any non-foot vertex sinks below the floor (snout, belly, tusks), raise the body and re-plant."""
        contact = set()
        for leg in self.legs:
            contact.update(leg['contactVertices'])
        for _ in range(3):
            bpy.context.view_layer.update()
            posed = bc.evaluated_world_vertices(self.mesh)
            deficit = max(self.allowed_z[i] - p.z for i, p in enumerate(posed) if i not in contact)
            if deficit <= tolerance * self.height:
                return
            self.translate(self.cal['body'], Vector((0, 0, deficit + tolerance * self.height)))
            self.settle_feet(iterations=2)

    def settle_body_above(self, ground: float, iterations: int = 2) -> None:
        """Airborne clips: only push the body up if any vertex would cross the real ground."""
        for _ in range(iterations):
            bpy.context.view_layer.update()
            posed = bc.evaluated_world_vertices(self.mesh)
            deficit = ground - min(v.z for v in posed)
            if deficit <= 0.002 * self.height:
                return
            self.translate(self.cal['body'], Vector((0, 0, deficit + 0.002 * self.height)))
        bpy.context.view_layer.update()

    def settle_body(self, ground: float | None = None, iterations: int = 3, push_up_only: bool = False) -> None:
        """Rest the lowest vertex exactly on `ground` (or only lift it there when push_up_only)."""
        ground = self.floor if ground is None else ground
        for _ in range(iterations):
            bpy.context.view_layer.update()
            posed = bc.evaluated_world_vertices(self.mesh)
            lowest = min(v.z for v in posed)
            correction = ground - lowest
            if abs(correction) < 1e-6 or (push_up_only and correction < 0):
                break
            self.translate(self.cal['body'], Vector((0, 0, correction)))
        bpy.context.view_layer.update()

    # ----- secondary chains --------------------------------------------------
    def tail_wave(self, phase: float, amplitude: float, fade: float = 1.0, pitch_amplitude: float = 0.0) -> None:
        chain = self.cal.get('tail', [])
        for i, bone in enumerate(chain):
            self.yaw(bone, mo.chain_lag(i, len(chain), phase, amplitude, fade=fade))
            if pitch_amplitude:
                self.pitch(bone, mo.chain_lag(i, len(chain), phase * 2, pitch_amplitude, fade=fade))

    def antennae_sway(self, phase: float, amplitude: float) -> None:
        for side, chain in enumerate(self.cal.get('antennae', [])):
            offset = 0.0 if side == 0 else 0.9
            for i, bone in enumerate(chain):
                self.yaw_out(bone, amplitude * 0.5 * math.sin(phase + offset - i * 0.6))
                self.pitch(bone, amplitude * 0.35 * math.sin(phase * 2 + offset - i * 0.6))

    def mandibles(self, angle: float) -> None:
        for bone in self.cal.get('mandibles', []):
            self.yaw_out(bone, angle)

    def fangs(self, angle: float) -> None:
        for bone in self.cal.get('fangs', []):
            self.pitch(bone, angle)

    def jaw_open(self, amount: float) -> None:
        jaw = self.cal.get('jaw')
        if not jaw:
            return
        if isinstance(jaw, dict):
            self.pitch(jaw['lower'], amount)
            self.pitch(jaw['upper'], -amount * 0.4)
        else:
            self.pitch(jaw, amount)

    def head_pitch(self, angle: float) -> None:
        neck = self.cal.get('neck', [])
        share = 1.0 / (len(neck) + 1)
        for bone in neck:
            self.pitch(bone, angle * share)
        self.pitch(self.cal['head'], angle * share)

    def head_yaw(self, angle: float) -> None:
        neck = self.cal.get('neck', [])
        share = 1.0 / (len(neck) + 1)
        for bone in neck:
            self.yaw(bone, angle * share)
        self.yaw(self.cal['head'], angle * share)

    def slump_head_to_ground(self, max_angle: float, ground: float) -> float:
        """Pitch the neck/head down as far as `max_angle` without any head vertex crossing the ground."""
        if max_angle <= 1e-6:
            return 0.0
        names = set(self.cal.get('neck', [])) | {self.cal['head']}
        jaw = self.cal.get('jaw')
        names |= set(jaw.values()) if isinstance(jaw, dict) else ({jaw} if jaw else set())
        if not hasattr(self, '_head_vertex_ids'):
            self._head_vertex_ids = [v.index for v in self.mesh.data.vertices if bc.dominant_group(self.mesh, v) in names]
        ids = self._head_vertex_ids
        margin = ground + 0.01 * self.height

        def lowest_after(angle: float) -> float:
            self.head_pitch(angle)
            bpy.context.view_layer.update()
            posed = bc.evaluated_world_vertices(self.mesh)
            self.head_pitch(-angle)
            return min(posed[i].z for i in ids) if ids else float('inf')

        if lowest_after(max_angle) >= margin:
            self.head_pitch(max_angle)
            return max_angle
        low, high, best = 0.0, max_angle, 0.0
        for _ in range(5):
            mid = (low + high) / 2
            if lowest_after(mid) >= margin:
                best, low = mid, mid
            else:
                high = mid
        self.head_pitch(best)
        return best

    def body_pitch(self, angle: float) -> None:
        """Positive: the head end of the body drops (nose down)."""
        body = self.cal['body']
        self.rotate(body, self.lateral, angle * self.sign(body, self.lateral, self.forward_tip_goal(body, -UP)))

    def forward_tip_goal(self, body: str, goal: Vector) -> Vector:
        # the body bone may point backward (e.g. Spine from hips toward chest);
        # express 'head end goes down' in terms of the bone tip regardless
        head = self.rig.matrix_world @ self.rig.data.bones[body].head_local
        tail = self.rig.matrix_world @ self.rig.data.bones[body].tail_local
        points_forward = (tail - head).dot(self.forward) >= 0
        return goal if points_forward else -goal

    def wings_flap(self, phase: float, amplitude: float, fold: float = 0.0, power: float = 1.0) -> None:
        bias = self.cal['gait'].get('flapBias', 0.0)
        for wing in self.cal.get('wings', []):
            chain = wing['chain']
            lags = (0.0, 0.05, 0.1, 0.15)
            shares = (1.0, 0.35, 0.25, 0.2)
            for bone, lag, share in zip(chain, lags, shares):
                self.flap(bone, mo.wing_flap(phase, amplitude * share, lag=lag, power=power) - bias * share * power)
            if fold:
                for bone, share in zip(chain[1:], (0.4, 0.7, 0.5)):
                    self.sweep_back(bone, fold * share)
            down = mo.smooth(0.0, 0.4, phase % 1.0) * (1 - mo.smooth(0.4, 1.0, phase % 1.0))
            for i, finger in enumerate(wing['fingers']):
                self.flap(finger, mo.wing_flap(phase, amplitude * 0.25, lag=0.2))
                self.yaw_out(finger, 0.08 * down * (1 if i == 0 else -1 if i == len(wing['fingers']) - 1 else 0))

    def wings_fold(self, amount: float) -> None:
        for wing in self.cal.get('wings', []):
            chain = wing['chain']
            self.flap(chain[0], -0.55 * amount)
            self.sweep_back(chain[0], 0.35 * amount)
            for bone, share in zip(chain[1:], (1.0, 1.3, 0.8)):
                self.sweep_back(bone, share * amount)
                self.flap(bone, -0.15 * amount)
            for finger in wing['fingers']:
                self.sweep_back(finger, 0.6 * amount)

    def wings_spread(self, amount: float) -> None:
        """Dead flyer on the ground: wings droop from the shoulder so the tips rest on the ground.

        The droop angle comes from the wing's own geometry (shoulder height above the belly
        over the wing length), so long and short wings both land flat instead of digging in.
        """
        core = self.core_vertex_ids()
        belly = min(self.rest[i].z for i in core)
        for wing in self.cal.get('wings', []):
            chain = wing['chain']
            root = self.rig.matrix_world @ self.rig.data.bones[chain[0]].head_local
            length = 0.0
            for name in chain + wing['fingers'][:1]:
                bone = self.rig.data.bones[name]
                length += (self.rig.matrix_world.to_3x3() @ (bone.tail_local - bone.head_local)).length
            droop = math.asin(max(0.0, min(1.0, (root.z - belly) / max(length, 1e-6))))
            self.flap(chain[0], droop * amount)
            # keep the membrane open: only a whisper of sweep so it does not fold over the body
            self.sweep_back(chain[0], 0.04 * amount)
            for bone, share in zip(chain[1:], (0.05, 0.06, 0.04)):
                self.sweep_back(bone, share * amount)

    def legs_tuck(self, amount: float) -> None:
        for leg in self.legs:
            chain = leg['chain']
            self.pitch_forward(chain[0], -amount)
            self.pitch_forward(chain[1], amount * 1.2)
            if len(chain) > 2:
                self.pitch_forward(chain[2], -amount * 0.4)

    def arms_pose(self, upper: float, forearm: float, spread: float = 0.0) -> None:
        for arm in self.cal.get('arms', []):
            chain = arm['chain']
            self.pitch_forward(chain[1], upper)
            self.pitch_forward(chain[2], forearm)
            if spread:
                self.yaw_out(chain[1], spread)

    # ----- clip drivers ------------------------------------------------------
    def clip_frames(self, seconds: float) -> int:
        return mo.frames_for(seconds, FPS)

    def author_clip(self, name: str, seconds: float, loop: bool, pose_fn, air: bool = False, contact: float | None = None) -> None:
        frames = self.clip_frames(seconds)
        samples = []
        contacts = []
        residuals = []
        final_diagnostic = {}
        worst_penetration = (0.0, 0, '')
        for frame in range(1, frames + 1):
            self.scene.frame_set(frame)
            bc.clear_pose(self.rig)
            self.reset_legs()
            self.set_leg_influence(0.0 if air else 1.0)
            t = (frame - 1) / (frames - 1)
            info = pose_fn(t) or {}
            bpy.context.view_layer.update()
            if info.get('ground') is not None:
                if info.get('feet'):
                    self.settle_feet()
                self.settle_body(info['ground'], push_up_only=info.get('pushUpOnly', False))
            elif not air and not info.get('noSettle'):
                self.settle_feet()
                self.lift_clear_of_floor()
            elif air:
                self.settle_body_above(self.ground)
            bpy.context.view_layer.update()
            for leg in self.legs:
                if not air and leg['ikConstraint'].influence > 0:
                    residual = (bc.bone_world_head(self.rig, leg['tip']) - leg['target'].location).length / self.height
                    residuals.append((residual, frame, leg['id']))
                    contacts.append({'frame': frame, 'leg': leg['id'], 'foot': leg['tip'], 'planted': leg['planted'],
                                     'phase': leg.get('phase', 0.0), 'target': list(leg['target'].location),
                                     'ikResidualBodyHeights': residual})
            samples.append(bc.bake_pose_sample(self.rig))
            posed_now = bc.evaluated_world_vertices(self.mesh)
            deficit, index = max((self.allowed_z[i] - p.z, i) for i, p in enumerate(posed_now))
            if deficit > worst_penetration[0]:
                worst_penetration = (deficit, frame, bc.dominant_group(self.mesh, self.mesh.data.vertices[index]))
            if frame == frames:
                posed = bc.evaluated_world_vertices(self.mesh)
                lowest = min(range(len(posed)), key=lambda i: posed[i].z)
                final_diagnostic = {'lowestVertexGroup': bc.dominant_group(self.mesh, self.mesh.data.vertices[lowest]),
                                    'lowestVertexZ': posed[lowest].z, 'bodyZ': bc.bone_world_head(self.rig, self.cal['body']).z,
                                    'bodyRestZ': self.body_rest_z}
        self.set_leg_influence(0.0)
        bc.write_action(self.rig, name, samples)
        worst = max(residuals) if residuals else (0.0, 0, '')
        entry = {'frames': [1, frames], 'durationSeconds': (frames - 1) / FPS, 'loop': loop,
                 'holdFinalPose': name == 'Death', 'contacts': contacts if name == 'Locomotion' else [],
                 'plantedFrames': sum(1 for c in contacts if c['planted']) if contacts else 0,
                 'maxIkResidualBodyHeights': worst[0], 'maxIkResidualAt': [worst[1], worst[2]],
                 'finalFrame': final_diagnostic,
                 'worstPenetration': {'bodyHeights': worst_penetration[0] / self.height, 'frame': worst_penetration[1], 'group': worst_penetration[2]}}
        if contact is not None:
            entry['visualContactNormalizedTime'] = contact
        self.receipt['clips'][name] = entry

    # ----- ground poses ------------------------------------------------------
    def apply_gait_feet(self, t: float, stride: float, duty: float, clearance: float) -> None:
        for leg in self.legs:
            phase = (t + self.cal['gait']['phases'][leg['id']]) % 1.0
            along, lift, planted = mo.foot_cycle(phase, duty, stride, clearance)
            leg['target'].location = leg['rest'] + self.forward * along
            leg['lift'] = lift
            leg['planted'] = planted
            leg['phase'] = phase

    def pose_idle_ground(self, t: float) -> dict:
        idle = self.cal['idle']
        phase = math.tau * t
        body = self.cal['body']
        self.translate(body, UP * (self.height * idle['breath'] * math.sin(phase)))
        self.body_pitch(0.01 * math.sin(phase))
        self.head_yaw(idle['headTurn'] * math.sin(phase))
        self.head_pitch(idle['headNod'] * math.sin(2 * phase))
        self.tail_wave(phase, idle.get('tailSwing', 0.0))
        self.antennae_sway(phase, idle.get('antennaSway', 0.0))
        twitch = mo.pulse(0.3, 0.36, 0.44, t) + mo.pulse(0.62, 0.68, 0.76, t)
        self.mandibles(idle.get('mandibleTwitch', 0.0) * twitch)
        self.fangs(idle.get('fangTwitch', 0.0) * twitch)
        self.jaw_open(idle.get('jawBreath', 0.0) * 0.5 * (1 - math.cos(phase)))
        for bone in self.cal.get('ears', []):
            self.yaw_out(bone, idle.get('earTwitch', 0.0) * twitch)
        if self.cal.get('arms'):
            self.arms_pose(0.05 + idle.get('armSway', 0.0) * math.sin(phase), 0.15)
        return {}

    def locomotion_stride(self) -> tuple[float, float]:
        gait = self.cal['gait']
        crouch = gait.get('crouch', 0.05) * self.height
        requested = gait['stride'] * self.length
        limit = self.stride_limit(crouch)
        return min(requested, limit), crouch

    def pose_locomotion_ground(self, t: float) -> dict:
        gait = self.cal['gait']
        stride, crouch = self.locomotion_stride()
        clearance = gait['clearance'] * self.height
        phase = math.tau * t
        body = self.cal['body']
        self.translate(body, UP * (mo.body_bounce(t, 2, gait['bounce'] * self.height) - crouch))
        self.body_pitch(gait['pitch'] * math.sin(2 * phase))
        if gait.get('roll'):
            self.roll(body, gait['roll'] * math.sin(phase))
        self.head_pitch(-gait['headBob'] * math.sin(2 * phase))
        self.tail_wave(phase, gait.get('tailSwing', 0.0), pitch_amplitude=gait.get('tailSwing', 0.0) * 0.3)
        self.antennae_sway(phase * 2, self.cal['idle'].get('antennaSway', 0.0) * 0.6)
        self.apply_gait_feet(t, stride, gait['duty'], clearance)
        if self.cal.get('arms') and gait.get('armSwing'):
            # arms counter-swing the legs: the left arm goes forward with the right leg
            for arm in self.cal['arms']:
                sign = 1.0 if arm['side'] == 'L' else -1.0
                self.pitch_forward(arm['chain'][1], gait['armSwing'] * sign * math.sin(phase))
                self.pitch_forward(arm['chain'][2], 0.25 + gait['armSwing'] * 0.3 * max(0.0, sign * math.sin(phase)))
        return {}

    def pose_attack_ground(self, t: float) -> dict:
        attack = self.cal['attack']
        kind = attack['type']
        body = self.cal['body']
        contact = attack['contact']
        anticipate = mo.smooth(0.0, contact * 0.55, t) * (1 - mo.smooth(contact * 0.55, contact, t))
        strike = mo.smooth(contact * 0.6, contact, t) * (1 - mo.smooth(contact + 0.08, 0.9, t))
        gape = mo.smooth(contact * 0.35, contact * 0.75, t) * (1 - mo.smooth(contact * 0.85, contact + 0.05, t))
        if kind in ('bite', 'maw'):
            self.translate(body, self.forward * (self.length * (-0.04 * anticipate + attack['lunge'] * strike)))
            self.translate(body, UP * (self.height * (-0.02 * anticipate - 0.02 * strike)))
            self.body_pitch(-0.05 * anticipate + 0.06 * strike)
            self.head_pitch(-0.18 * anticipate + attack.get('headDip', 0.3) * strike)
            # a bite is a sideways grab: the head yaws and twists as the jaws close
            twist = attack.get('twist', 0.0)
            if twist:
                hold = mo.smooth(contact * 0.7, contact + 0.02, t) * (1 - mo.smooth(contact + 0.12, 0.9, t))
                self.head_yaw(twist * 0.6 * hold)
                self.rotate(self.cal['head'], self.forward, twist * hold)
            if self.cal.get('jaw'):
                self.jaw_open(attack['gape'] * gape)
            for bone in self.cal.get('ridges', []):
                self.pitch(bone, -0.15 * anticipate)
            self.front_step(strike, attack['lunge'] * 0.6)
        elif kind == 'tusk':
            self.translate(body, self.forward * (self.length * (-0.05 * anticipate + attack['lunge'] * strike)))
            self.translate(body, UP * (self.height * (-0.05 * anticipate + 0.03 * strike)))
            self.body_pitch(0.08 * anticipate - 0.1 * strike)
            self.head_pitch(attack.get('dip', 0.3) * anticipate - attack['hook'] * strike)
            self.roll(body, 0.18 * strike)
            self.head_yaw(0.25 * strike)
            self.jaw_open(attack.get('gape', 0.0) * gape)
            self.front_step(strike, attack['lunge'] * 0.5)
        elif kind == 'slam':
            rear = mo.smooth(0.05, contact * 0.55, t) * (1 - mo.smooth(contact * 0.7, contact, t))
            slam = mo.smooth(contact * 0.75, contact, t) * (1 - mo.smooth(contact + 0.1, 0.85, t))
            self.body_pitch(-attack['rear'] * rear + 0.08 * slam)
            self.translate(body, UP * (self.height * (0.12 * rear - 0.05 * slam)))
            self.translate(body, self.forward * (self.length * (-0.04 * rear + 0.06 * slam)))
            self.head_pitch(-0.3 * rear + attack['slam'] * slam)
            self.jaw_open(attack.get('gape', 0.0) * (rear * 0.6 + slam))
            for leg in self.legs:
                if leg['row'] == 'front':
                    leg['target'].location = leg['rest'] + UP * (self.height * 0.32 * rear) - self.forward * (self.length * 0.06 * rear)
                    leg['lift'] = self.height * 0.32 * rear
                    leg['planted'] = rear < 0.05
        elif kind == 'mandible':
            self.translate(body, self.forward * (self.length * (-0.04 * anticipate + attack['lunge'] * strike)))
            self.translate(body, UP * (self.height * (0.03 * anticipate - 0.03 * strike)))
            self.head_pitch(-0.2 * anticipate + 0.28 * strike)
            self.mandibles(attack['gape'] * gape - 0.12 * strike * (1 - gape))
            self.antennae_sway(math.tau * t, self.cal['idle'].get('antennaSway', 0.0))
            self.front_step(strike, attack['lunge'] * 0.6)
        elif kind == 'fang':
            rear = mo.smooth(0.05, contact * 0.6, t) * (1 - mo.smooth(contact * 0.75, contact, t))
            stab = mo.smooth(contact * 0.8, contact, t) * (1 - mo.smooth(contact + 0.1, 0.85, t))
            self.body_pitch(-attack['rear'] * rear + 0.1 * stab)
            self.translate(body, UP * (self.height * (0.1 * rear - 0.06 * stab)))
            self.translate(body, self.forward * (self.length * (attack['lunge'] * stab)))
            self.head_pitch(-0.2 * rear + 0.22 * stab)
            self.fangs(-0.25 * rear + 0.6 * stab)
            for leg in self.legs:
                if leg['row'] in ('Front', 'FrontMiddle'):
                    lift = self.height * (0.3 if leg['row'] == 'Front' else 0.18) * rear
                    leg['target'].location = leg['rest'] + UP * lift - self.lateral * (leg['rest'].x * 0.15 * rear)
                    leg['lift'] = lift
                    leg['planted'] = rear < 0.05
        elif kind == 'swing':
            # one-arm melee swing: wind up behind, strike forward and down, recover
            side = attack.get('arm', 'R')
            swing = attack.get('swing', 1.2)
            self.translate(body, self.forward * (self.length * (-0.03 * anticipate + attack.get('lunge', 0.05) * strike)))
            self.rotate(body, UP, (0.25 * anticipate - 0.3 * strike) * (1.0 if side == 'R' else -1.0))
            self.body_pitch(-0.04 * anticipate + 0.08 * strike)
            self.head_pitch(-0.05 * anticipate + 0.1 * strike)
            for arm in self.cal.get('arms', []):
                chain = arm['chain']
                if arm['side'] == side:
                    self.pitch_forward(chain[1], -swing * 0.75 * anticipate + swing * strike)
                    self.pitch_forward(chain[2], 0.9 * anticipate + 0.2 * strike)
                    self.yaw_out(chain[1], 0.35 * anticipate)
                else:
                    self.pitch_forward(chain[1], 0.3 * anticipate - 0.2 * strike)
                    self.pitch_forward(chain[2], 0.5)
            self.front_step(strike, attack.get('lunge', 0.05) * 0.5)
        else:
            raise RuntimeError(f'Unknown ground attack {kind}')
        self.tail_wave(math.tau * t, self.cal['idle'].get('tailSwing', 0.0) * 0.6)
        return {}

    def front_step(self, strike: float, along: float) -> None:
        for leg in self.legs:
            if leg['row'] == 'front':
                hop = math.sin(math.pi * min(1.0, strike))
                leg['target'].location = leg['rest'] + self.forward * (self.length * along * strike)
                leg['lift'] = self.height * 0.05 * hop
                leg['planted'] = hop < 0.2

    def pose_hit_ground(self, t: float) -> dict:
        hit = self.cal['hit']
        body = self.cal['body']
        recoil = mo.smooth(0.0, 0.2, t) * (1 - mo.smooth(0.25, 1.0, t))
        self.translate(body, -self.forward * (self.length * hit['recoil'] * recoil))
        self.translate(body, UP * (self.height * 0.03 * recoil))
        self.body_pitch(-0.07 * recoil)
        self.roll(body, 0.06 * recoil)
        self.head_pitch(-0.28 * recoil)
        self.head_yaw(0.12 * recoil)
        self.tail_wave(math.tau * t, self.cal['idle'].get('tailSwing', 0.0) * 0.8)
        self.jaw_open(0.15 * recoil)
        self.mandibles(0.15 * recoil)
        return {}

    def pose_death_ground(self, t: float) -> dict:
        death = self.cal['death']
        body = self.cal['body']
        fall = mo.smooth(0.08, 0.7, t)
        settle = mo.smooth(0.7, 1.0, t)
        self.set_leg_influence(0.0)
        kind = death['type']
        if kind == 'sideRoll':
            self.roll(body, -(death['roll'] * fall + 0.08 * settle))
            self.translate(body, UP * (-self.height * 0.34 * fall))
            self.translate(body, self.lateral * (-self.height * 0.12 * fall))
            self.head_pitch(0.1 * fall)
            self.head_yaw(-0.2 * fall)
            self.jaw_open(0.12 * fall)
            for leg in self.legs:
                chain = leg['chain']
                self.pitch_forward(chain[0], 0.25 * fall)
                self.pitch_forward(chain[1], -0.45 * fall)
        elif kind in ('collapse', 'curl'):
            # Legs give way. Collapse: legs splay out sideways (FK) and the body sinks onto its
            # belly. Curl: arthropod legs fold up under the body while it sinks.
            self.set_leg_influence(0.0)
            self.translate(body, UP * (-self.height * (0.75 if kind == 'curl' else 0.62) * fall))
            self.translate(body, self.forward * (self.length * 0.03 * fall))
            self.roll(body, -death['roll'] * (mo.smooth(0.45, 0.9, t) if kind == 'collapse' else fall))
            self.head_pitch(-(0.35 if isinstance(self.cal.get('jaw'), dict) else 0.15) * fall)
            self.head_yaw(-0.15 * settle)
            self.jaw_open(0.15 * fall)
            self.mandibles(0.3 * fall)
            self.fangs(0.25 * fall)
            for chain in self.cal.get('antennae', []):
                for bone in chain:
                    self.pitch(bone, 0.45 * fall)
            for leg in self.legs:
                chain = leg['chain']
                if kind == 'curl':
                    self.lift(chain[0], 0.25 * fall)
                    self.lift(chain[1], 0.75 * fall)
                    self.lift(chain[2], 1.35 * fall)
                    if len(chain) > 3:
                        self.lift(chain[3], 0.6 * fall)
                else:
                    front = leg['row'] in ('front', 'Front')
                    # the legs on the ground side splay flat; the legs that end up on top only
                    # open as far as the roll leaves them lying along the ground
                    rolled_lateral = Quaternion(self.forward, -death['roll']) @ self.lateral
                    down_side = 1.0 if rolled_lateral.z < 0 else -1.0
                    side = 1.0 if leg['rest'].x >= 0 else -1.0
                    # upper legs fold across toward the ground side so they lie beside the lower legs
                    open_angle = 1.15 if side == down_side else -0.45
                    self.splay(chain[0], open_angle * fall)
                    self.pitch_forward(chain[0], (0.35 if front else -0.3) * fall)
                    self.splay(chain[1], (1.0 if side == down_side else -0.2) * fall)
                    self.pitch_forward(chain[1], (-0.3 if front else 0.3) * fall)
            self.tail_wave(math.tau * t * 0.5, self.cal['idle'].get('tailSwing', 0.0), fade=1 - mo.smooth(0.5, 1.0, t))
            return {'ground': self.floor}
        elif kind == 'curl_legacy':
            self.translate(body, UP * (-self.height * 0.6 * fall))
            self.roll(body, -death['roll'] * settle)
            self.head_pitch(0.25 * fall)
            for leg in self.legs:
                chain = leg['chain']
                self.pitch(chain[0], -0.35 * fall)
                self.pitch(chain[1], -0.6 * fall)
                self.pitch(chain[2], 0.9 * fall)
                self.yaw_out(chain[1], -0.25 * fall)
            for bone in self.cal.get('tail', []):
                self.pitch(bone, -0.2 * mo.pulse(0.1, 0.4, 0.8, t) + 0.15 * fall)
            self.mandibles(0.35 * fall)
            self.fangs(0.3 * fall)
            self.antennae_sway(0.0, 0.0)
            for chain in self.cal.get('antennae', []):
                for bone in chain:
                    self.pitch(bone, 0.5 * fall)
        else:
            raise RuntimeError(f'Unknown ground death {kind}')
        self.tail_wave(math.tau * t * 0.5, self.cal['idle'].get('tailSwing', 0.0), fade=1 - mo.smooth(0.5, 1.0, t))
        return {'ground': self.floor}

    def pose_cast_ground(self, t: float) -> dict:
        cast = self.cal['cast']
        body = self.cal['body']
        kind = cast['type']
        if kind == 'spawn':
            build = mo.smooth(0.0, 0.3, t) * (1 - mo.smooth(0.72, 0.95, t))
            release = mo.pulse(0.66, 0.74, 0.9, t)
            pulses = math.sin(math.tau * 3 * t) * build
            self.translate(body, UP * (-self.height * 0.03 * build - self.height * 0.02 * release))
            self.body_pitch(-0.12 * build)
            self.head_pitch(-0.18 * build)
            for bone in self.cal.get('tail', []):
                self.pitch(bone, -0.4 * build - cast['pulse'] * pulses + 0.1 * release)
            self.fangs(0.15 * pulses)
            for leg in self.legs:
                leg['target'].location = leg['rest'].copy()
        elif kind == 'roar':
            build = mo.smooth(0.0, 0.32, t) * (1 - mo.smooth(0.72, 0.9, t))
            hold = mo.smooth(0.3, 0.42, t) * (1 - mo.smooth(0.7, 0.8, t))
            shake = math.sin(math.tau * 6 * t) * hold
            self.translate(body, UP * (self.height * 0.05 * build))
            self.translate(body, -self.forward * (self.length * 0.05 * build))
            self.body_pitch(-0.1 * build)
            self.head_pitch(-0.35 * build + 0.03 * shake)
            self.head_yaw(0.04 * shake)
            self.jaw_open(cast['gape'] * build)
            for i, bone in enumerate(self.cal.get('ridges', [])):
                self.pitch(bone, -(0.25 + 0.08 * i) * build)
        elif kind == 'raise':
            # telegraph: the casting arm (or both) rises, holds with a tremor, releases forward
            build = mo.smooth(0.0, 0.3, t) * (1 - mo.smooth(0.7, 0.95, t))
            hold = mo.smooth(0.28, 0.4, t) * (1 - mo.smooth(0.62, 0.72, t))
            release = mo.pulse(0.62, 0.7, 0.9, t)
            tremor = math.sin(math.tau * 7 * t) * hold
            side = cast.get('arm', 'both')
            amount = cast.get('raise', 1.4)
            self.translate(body, UP * (self.height * 0.02 * build))
            self.body_pitch(-0.06 * build + 0.05 * release)
            self.head_pitch(-0.12 * build + 0.02 * tremor)
            for arm in self.cal.get('arms', []):
                chain = arm['chain']
                if side in ('both', arm['side']):
                    self.pitch_forward(chain[1], amount * build + 0.03 * tremor - 0.3 * release)
                    self.pitch_forward(chain[2], 0.4 * build + 0.2 * release)
                    self.yaw_out(chain[1], 0.25 * build)
                else:
                    self.pitch_forward(chain[1], 0.2 * build)
                    self.pitch_forward(chain[2], 0.45)
        else:
            raise RuntimeError(f'Unknown cast {kind}')
        self.tail_wave(math.tau * t, self.cal['idle'].get('tailSwing', 0.0) * 0.5)
        return {}

    # ----- air poses ---------------------------------------------------------
    def flaps_in(self, seconds: float, cycle: float) -> int:
        return max(1, int(round(seconds / cycle)))

    def pose_idle_air(self, t: float) -> dict:
        idle = self.cal['idle']
        gait = self.cal['gait']
        flaps = self.flaps_in(idle['seconds'], gait['cycleSeconds'] * 1.25)
        phase = t * flaps
        body = self.cal['body']
        self.wings_flap(phase, idle['flapAmplitude'])
        self.translate(body, UP * mo.lift_from_flap(phase, idle['lift'] * self.height))
        self.body_pitch(0.02 * math.sin(math.tau * t))
        self.head_yaw(idle['headTurn'] * math.sin(math.tau * t))
        self.head_pitch(0.03 * math.sin(math.tau * 2 * t))
        self.legs_tuck(idle['legTuck'])
        self.tail_wave(math.tau * t, idle.get('tailSwing', 0.0), pitch_amplitude=idle.get('tailSwing', 0.0) * 0.5)
        twitch = mo.pulse(0.3, 0.36, 0.44, t) + mo.pulse(0.62, 0.68, 0.76, t)
        for bone in self.cal.get('ears', []):
            self.yaw_out(bone, idle.get('earTwitch', 0.0) * twitch)
        self.arms_pose(0.15 + idle.get('armSway', 0.0) * math.sin(math.tau * t), 0.35)
        return {}

    def pose_locomotion_air(self, t: float) -> dict:
        gait = self.cal['gait']
        body = self.cal['body']
        phase = t
        self.wings_flap(phase, gait['flapAmplitude'], fold=gait.get('fold', 0.0))
        self.translate(body, UP * mo.lift_from_flap(phase, gait['lift'] * self.height))
        self.body_pitch(gait['lean'])
        self.head_pitch(-gait['lean'] * 0.7 + gait['headBob'] * math.sin(math.tau * phase))
        self.legs_tuck(gait['legTuck'])
        self.tail_wave(math.tau * t, gait.get('tailSwing', 0.0) * 0.5, pitch_amplitude=gait.get('tailSwing', 0.0))
        self.arms_pose(0.3 + gait.get('armSwing', 0.0) * math.sin(math.tau * t), 0.5)
        return {}

    def pose_attack_air(self, t: float) -> dict:
        attack = self.cal['attack']
        gait = self.cal['gait']
        body = self.cal['body']
        contact = attack['contact']
        flaps = self.flaps_in(attack['seconds'], gait['cycleSeconds'])
        phase = t * flaps
        anticipate = mo.smooth(0.0, contact * 0.55, t) * (1 - mo.smooth(contact * 0.55, contact, t))
        strike = mo.smooth(contact * 0.6, contact, t) * (1 - mo.smooth(contact + 0.08, 0.9, t))
        gape = mo.smooth(contact * 0.35, contact * 0.75, t) * (1 - mo.smooth(contact * 0.85, contact + 0.05, t))
        self.wings_flap(phase, gait['flapAmplitude'] * (1 - 0.4 * strike), fold=0.3 * strike)
        self.translate(body, UP * (mo.lift_from_flap(phase, gait['lift'] * self.height) + self.height * (attack['dive'] * anticipate - attack['dive'] * strike)))
        self.translate(body, self.forward * (self.length * (-0.05 * anticipate + attack['lunge'] * strike)))
        self.body_pitch(-0.1 * anticipate + 0.28 * strike)
        if attack['type'] == 'swoop':
            self.head_pitch(-0.2 * anticipate + 0.35 * strike + attack.get('neckReach', 0.0) * strike)
            twist = attack.get('twist', 0.0)
            if twist:
                hold = mo.smooth(contact * 0.7, contact + 0.02, t) * (1 - mo.smooth(contact + 0.12, 0.9, t))
                self.head_yaw(twist * 0.6 * hold)
                self.rotate(self.cal['head'], self.forward, twist * hold)
            self.jaw_open(attack['gape'] * gape)
            self.legs_tuck(gait['legTuck'] * (1 - 0.4 * strike))
        elif attack['type'] == 'talon':
            self.head_pitch(-0.15 * anticipate + 0.25 * strike)
            self.arms_pose(-0.6 * anticipate + attack['slash'] * strike, 0.3 + 0.4 * strike, spread=0.2 * anticipate)
            for leg in self.legs:
                chain = leg['chain']
                self.pitch_forward(chain[0], -gait['legTuck'] * (1 - strike) + 0.9 * strike)
                self.pitch_forward(chain[1], gait['legTuck'] * 1.2 * (1 - strike) - 0.2 * strike)
                self.pitch_forward(chain[3], 0.4 * strike)
        else:
            raise RuntimeError(f"Unknown air attack {attack['type']}")
        self.tail_wave(math.tau * t, gait.get('tailSwing', 0.0) * 0.6)
        return {}

    def pose_hit_air(self, t: float) -> dict:
        hit = self.cal['hit']
        gait = self.cal['gait']
        body = self.cal['body']
        recoil = mo.smooth(0.0, 0.2, t) * (1 - mo.smooth(0.25, 1.0, t))
        phase = t * self.flaps_in(hit['seconds'], gait['cycleSeconds'])
        self.wings_flap(phase, gait['flapAmplitude'] * 0.8, power=1 - 0.4 * recoil)
        for wing in self.cal['wings']:
            self.flap(wing['chain'][0], -0.4 * recoil)
        self.translate(body, UP * (mo.lift_from_flap(phase, gait['lift'] * self.height) - self.height * hit['dip'] * recoil))
        self.translate(body, -self.forward * (self.length * hit['recoil'] * recoil))
        self.body_pitch(-0.15 * recoil)
        self.roll(body, 0.12 * recoil)
        self.head_pitch(-0.25 * recoil)
        self.legs_tuck(gait['legTuck'] * (1 - 0.3 * recoil))
        self.jaw_open(0.15 * recoil)
        self.arms_pose(0.2 - 0.3 * recoil, 0.4)
        self.tail_wave(math.tau * t, gait.get('tailSwing', 0.0) * 0.5)
        return {}

    def pose_death_air(self, t: float) -> dict:
        death = self.cal['death']
        gait = self.cal['gait']
        body = self.cal['body']
        fall = mo.smooth(0.08, 0.62, t)
        settle = mo.smooth(0.62, 1.0, t)
        flutter = (1 - mo.smooth(0.0, 0.35, t))
        phase = t * 2
        self.wings_flap(phase, gait['flapAmplitude'] * 0.6 * flutter, power=flutter)
        self.wings_spread(fall)
        self.body_pitch(death.get('bodyPitch', 0.08) * fall)
        rolling = mo.smooth(0.4, 0.8, t)
        self.roll(body, -death['roll'] * rolling)
        if death['roll'] > 0.2 and rolling > 0.0 and len(self.cal.get('wings', [])) == 2:
            # keeled over: the wing on the ground side folds up against the body instead of
            # digging into the floor, the upper wing stays spread
            bpy.context.view_layer.update()
            tips = [(rig_tip := (self.rig.matrix_world @ self.rig.pose.bones[w['fingers'][0]].tail).z, w) for w in self.cal['wings']]
            lower = min(tips, key=lambda item: item[0])[1]
            self.flap(lower['chain'][0], -1.3 * rolling)
            self.sweep_back(lower['chain'][0], 0.2 * rolling)
            for bone, share in zip(lower['chain'][1:], (0.4, 0.5, 0.3)):
                self.sweep_back(bone, share * rolling)
        # neck and head slump toward the ground (the tallest part of a long-necked flyer),
        # stopping where the head meets the ground instead of pushing the body up
        self.slump_head_to_ground(death.get('headSlump', 0.3) * fall, self.ground)
        self.legs_tuck(gait['legTuck'] * (1 - fall))
        for leg in self.legs:
            chain = leg['chain']
            # legs fold toward the body whatever way they hang, so nothing props the corpse up
            self.lift(chain[0], death.get('legFold', 0.35) * fall)
            self.lift(chain[1], death.get('legFold', 0.35) * 0.85 * fall)
        core_z = sorted(self.rest[i].z for i in self.core_vertex_ids())
        belly = core_z[int(len(core_z) * 0.08)]  # underside, ignoring stray low verts (claws, membranes)
        drop = (belly - self.ground) + self.height * 0.05
        self.translate(body, UP * (-drop * fall))
        self.tail_wave(math.tau * t, gait.get('tailSwing', 0.0) * 0.4, fade=1 - settle)
        self.arms_pose(0.4 * fall, 0.2)
        # while falling only keep the body above the ground; once down, rest exactly on it
        return {'ground': self.ground, 'pushUpOnly': t < 0.7}

    # ----- orchestration -------------------------------------------------------
    def author_all(self) -> None:
        ground = self.cal['mode'] == 'ground'
        required = self.contract['requiredClips']
        generators = {
            'Idle': (self.cal['idle']['seconds'], True, self.pose_idle_ground if ground else self.pose_idle_air, None),
            'Locomotion': (self.cal['gait']['cycleSeconds'], True, self.pose_locomotion_ground if ground else self.pose_locomotion_air, None),
            'BasicAttack': (self.cal['attack']['seconds'], False, self.pose_attack_ground if ground else self.pose_attack_air, self.cal['attack']['contact']),
            'Hit': (self.cal['hit']['seconds'], False, self.pose_hit_ground if ground else self.pose_hit_air, None),
            'Death': (self.cal['death']['seconds'], False, self.pose_death_ground if ground else self.pose_death_air, None),
        }
        if self.cal.get('cast'):
            generators['Cast'] = (self.cal['cast']['seconds'], False, self.pose_cast_ground, None)
        missing = [clip for clip in required if clip not in generators]
        if missing:
            raise RuntimeError(f'No generator for required clips {missing}')
        for name in required:
            seconds, loop, fn, contact = generators[name]
            self.author_clip(name, seconds, loop, fn, air=not ground, contact=contact)
        gait = self.cal['gait']
        if ground:
            stride, crouch = self.locomotion_stride()
            cycle = self.receipt['clips']['Locomotion']['durationSeconds']
            speed = mo.travel_speed(stride, gait['duty'], cycle)
            self.receipt['clips']['Locomotion'].update({
                'gait': gait['type'], 'strideUnits': stride, 'requestedStrideUnits': gait['stride'] * self.length,
                'strideLimitUnits': self.stride_limit(crouch), 'crouchUnits': crouch, 'stanceFraction': gait['duty'],
                'nominalSpeedUnitsPerSecond': speed, 'nominalSpeedBodyHeightsPerSecond': speed / self.height,
                'minimumSupportLegs': mo.support_count(gait['type'], gait['duty']),
            })
        else:
            self.receipt['clips']['Locomotion'].update({
                'gait': 'flap', 'flapsPerSecond': 1.0 / gait['cycleSeconds'],
                'altitudePolicy': 'body altitude oscillates around the source rest height; runtime anchor offset is not applied in the clip',
            })

    def finalize(self, output: Path) -> None:
        for leg in self.legs:
            for name in (leg['ik'], leg['tip']):
                bone = self.rig.pose.bones[name]
                for constraint in list(bone.constraints):
                    bone.constraints.remove(constraint)
            bpy.data.objects.remove(leg['target'], do_unlink=True)
        for bone in self.rig.pose.bones:
            if bone.constraints:
                raise RuntimeError(f'{bone.name} still has constraints')
        bc.clear_pose(self.rig)
        first = bpy.data.actions[self.contract['requiredClips'][0]]
        bc.bind_action(self.rig, first)
        self.scene.frame_start = 1
        self.scene.frame_end = int(first.frame_range[1])
        self.scene.frame_set(1)
        blend = output / f"{self.contract['folder']}_Actions.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()))
        self.receipt['blend'] = {'path': blend.as_posix(), 'sha256': bc.sha256(blend)}
        bc.write_json(output / 'receipt.json', self.receipt)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if args.output.exists():
        raise RuntimeError(f'Refusing to overwrite candidate directory {args.output}')
    row = contract_module.load(args.contract)
    calibration = row['calibration']
    if calibration['family'] == 'mixamo-biped':
        raise RuntimeError('mixamo-biped clips come from the provider; use package_biped.py instead of authoring')
    args.output.mkdir(parents=True)
    bc.load_source(args.source, use_anim=False)
    creature = Creature(calibration, row)
    creature.receipt['source'] = {'path': Path(args.source).as_posix(), 'sha256': bc.sha256(args.source)}
    creature.receipt['contract'] = {k: v for k, v in row.items() if k != 'calibration'}
    creature.receipt['calibration'] = {k: v for k, v in calibration.items() if k != 'legs'}
    creature.author_all()
    creature.finalize(args.output)
    summary = {name: {k: v for k, v in clip.items() if k != 'contacts'} for name, clip in creature.receipt['clips'].items()}
    print(json.dumps({'subject': row['subjectId'], 'height': creature.height, 'length': creature.length,
                      'rootWeightsMoved': creature.receipt['rootWeightsMovedToBody'], 'clips': summary}))


if __name__ == '__main__':
    main()
