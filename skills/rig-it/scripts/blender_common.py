"""Blender-side helpers shared by authoring, export and review scripts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

FPS = 30

FBX_EXPORT_SETTINGS = dict(
    global_scale=1.0,
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_UNITS',
    use_space_transform=True,
    bake_space_transform=False,
    axis_forward='-Z',
    axis_up='Y',
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    add_leaf_bones=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    use_armature_deform_only=False,
    bake_anim=True,
    bake_anim_use_all_actions=False,
    bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0,
    path_mode='STRIP',
    embed_textures=False,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=False) + '\n')


def fresh_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load_source(path: Path, use_anim: bool) -> None:
    path = Path(path)
    if path.suffix.lower() == '.fbx':
        fresh_scene()
        bpy.ops.import_scene.fbx(filepath=str(path.resolve()), use_anim=use_anim,
                                 ignore_leaf_bones=False, automatic_bone_orientation=False)
    elif path.suffix.lower() == '.blend':
        bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
    else:
        raise RuntimeError(f'Unsupported source {path}')
    bpy.context.scene.render.fps = FPS


def scene_objects() -> list[bpy.types.Object]:
    return list(bpy.context.scene.objects)


def find_rig() -> bpy.types.Object:
    rigs = [o for o in scene_objects() if o.type == 'ARMATURE']
    if len(rigs) != 1:
        raise RuntimeError(f'Expected one armature, found {[r.name for r in rigs]}')
    return rigs[0]


def deforming_meshes(rig: bpy.types.Object) -> list[bpy.types.Object]:
    result = []
    for obj in scene_objects():
        if obj.type != 'MESH':
            continue
        if any(m.type == 'ARMATURE' and m.object == rig for m in obj.modifiers):
            result.append(obj)
    return result


def rigid_meshes(rig: bpy.types.Object) -> list[bpy.types.Object]:
    deforming = set(deforming_meshes(rig))
    return [o for o in scene_objects() if o.type == 'MESH' and o not in deforming]


def main_mesh(rig: bpy.types.Object) -> bpy.types.Object:
    meshes = deforming_meshes(rig)
    if not meshes:
        raise RuntimeError('No armature-deformed mesh found')
    return max(meshes, key=lambda m: len(m.data.vertices))


def evaluated_world_vertices(obj: bpy.types.Object) -> list[Vector]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    data = evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ v.co for v in data.vertices]
    finally:
        evaluated.to_mesh_clear()


def rest_world_vertices(obj: bpy.types.Object) -> list[Vector]:
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def dominant_group(mesh: bpy.types.Object, vertex) -> str | None:
    best = None
    best_weight = 0.0
    for g in vertex.groups:
        if g.weight > best_weight:
            best_weight = g.weight
            best = mesh.vertex_groups[g.group].name
    return best


def group_vertices(mesh: bpy.types.Object, names: list[str], threshold: float = 0.5) -> list[int]:
    ids = {mesh.vertex_groups[n].index for n in names if mesh.vertex_groups.get(n)}
    return [v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if g.group in ids) > threshold]


def clear_pose(rig: bpy.types.Object) -> None:
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.matrix_basis = Matrix.Identity(4)


def bone_world_head(rig: bpy.types.Object, name: str) -> Vector:
    return rig.matrix_world @ rig.pose.bones[name].head


def bone_world_tail(rig: bpy.types.Object, name: str) -> Vector:
    return rig.matrix_world @ rig.pose.bones[name].tail


def bake_pose_sample(rig: bpy.types.Object) -> dict[str, Matrix]:
    """Return per-bone matrix_basis values that reproduce the evaluated pose."""
    matrices = {b.name: b.matrix.copy() for b in rig.pose.bones}
    local = {}
    for b in rig.pose.bones:
        if b.parent:
            rest_relative = b.parent.bone.matrix_local.inverted() @ b.bone.matrix_local
            local[b.name] = rest_relative.inverted() @ matrices[b.parent.name].inverted() @ matrices[b.name]
        else:
            local[b.name] = b.bone.matrix_local.inverted() @ matrices[b.name]
    return local


def write_action(rig: bpy.types.Object, name: str, samples: list[dict[str, Matrix]]) -> bpy.types.Action:
    scene = bpy.context.scene
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = action
    for frame, pose in enumerate(samples, 1):
        scene.frame_set(frame)
        for bone_name, matrix in pose.items():
            bone = rig.pose.bones[bone_name]
            bone.rotation_mode = 'QUATERNION'
            bone.matrix_basis = matrix
            for prop in ('location', 'rotation_quaternion', 'scale'):
                bone.keyframe_insert(data_path=prop, frame=frame, group=bone_name)
    if action.slots:
        rig.animation_data.action_slot = action.slots[0]
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = 'LINEAR'
    rig.animation_data.action = None
    return action


def bind_action(rig: bpy.types.Object, action: bpy.types.Action) -> None:
    rig.animation_data_create()
    for track in list(rig.animation_data.nla_tracks):
        track.mute = True
    rig.animation_data.action = action
    if action.slots:
        rig.animation_data.action_slot = action.slots[0]


def export_fbx(path: Path, objects: list[bpy.types.Object], **overrides) -> None:
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    settings = dict(FBX_EXPORT_SETTINGS)
    settings.update(overrides)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    result = bpy.ops.export_scene.fbx(filepath=str(Path(path).resolve()), use_selection=True,
                                      object_types={'ARMATURE', 'EMPTY', 'MESH'}, **settings)
    if 'FINISHED' not in result or not Path(path).is_file():
        raise RuntimeError(f'FBX export failed: {result}')


def sole_vertices(mesh: bpy.types.Object, names: list[str], minimum: int = 12, max_z: float | None = None,
                  threshold: float = 0.35) -> list[int]:
    """Vertices forming a foot's contact patch: strongly weighted to the sole bone(s) and, when
    `max_z` is given, lying at or below that world height (the ankle). Falls back to the
    best-weighted few when the strong set is too small."""
    ids = {mesh.vertex_groups[n].index for n in names if mesh.vertex_groups.get(n)}
    scored = []
    for v in mesh.data.vertices:
        if max_z is not None and (mesh.matrix_world @ v.co).z > max_z:
            continue
        weight = sum(g.weight for g in v.groups if g.group in ids)
        if weight > 0:
            scored.append((weight, v.index))
    strong = [i for w, i in scored if w > threshold]
    if len(strong) >= minimum:
        return strong
    scored.sort(reverse=True)
    return [i for _, i in scored[:max(minimum, len(scored) // 4)]]


def skin_rigid_to_bone(obj: bpy.types.Object, rig: bpy.types.Object, bone: str) -> None:
    """Attach a rigid part to one bone through a single full-weight vertex group.

    Bone parenting pivots on the bone tail in Blender and on the bone head in FBX, which
    displaces rigid sockets after a round trip once the bone rotates far. A one-bone skin
    is rigid, pivot-safe and survives FBX/Unity import unchanged.
    """
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = 'OBJECT'
    obj.parent_bone = ''
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    obj.matrix_world = world
    for group in list(obj.vertex_groups):
        obj.vertex_groups.remove(group)
    group = obj.vertex_groups.new(name=bone)
    group.add([v.index for v in obj.data.vertices], 1.0, 'REPLACE')
    for modifier in list(obj.modifiers):
        if modifier.type == 'ARMATURE':
            obj.modifiers.remove(modifier)
    armature = obj.modifiers.new('Armature', 'ARMATURE')
    armature.object = rig


def skin_rigid_to_surface(obj: bpy.types.Object, rig: bpy.types.Object, source: bpy.types.Object) -> dict:
    """Attach a rigid part (crown, egg sacs) to the skinned surface it sits on.

    The part receives the skin weights of the nearest source-mesh surface points, so it
    follows exactly the blend of bones that carries the skull top or abdomen it rests on.
    A pure single-bone attachment would pivot about that bone's root and swing off the
    surface whenever the head or abdomen bends.
    """
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = 'OBJECT'
    obj.parent_bone = ''
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    obj.matrix_world = world
    for group in list(obj.vertex_groups):
        obj.vertex_groups.remove(group)
    for group in source.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    for modifier in list(obj.modifiers):
        obj.modifiers.remove(modifier)
    transfer = obj.modifiers.new('WeightTransfer', 'DATA_TRANSFER')
    transfer.object = source
    transfer.use_vert_data = True
    transfer.data_types_verts = {'VGROUP_WEIGHTS'}
    transfer.vert_mapping = 'POLYINTERP_NEAREST'
    transfer.layers_vgroup_select_src = 'ALL'
    transfer.layers_vgroup_select_dst = 'NAME'
    previous = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    bpy.context.view_layer.objects.active = previous
    armature = obj.modifiers.new('Armature', 'ARMATURE')
    armature.object = rig
    dominant = {}
    for v in obj.data.vertices:
        total = sum(g.weight for g in v.groups)
        if total <= 0:
            raise RuntimeError(f'{obj.name} vertex {v.index} received no surface weight')
        for g in v.groups:
            obj.vertex_groups[g.group].add([v.index], g.weight / total, 'REPLACE')
        name = max(v.groups, key=lambda g: g.weight)
        dominant[obj.vertex_groups[name.group].name] = dominant.get(obj.vertex_groups[name.group].name, 0) + 1
    return dominant
