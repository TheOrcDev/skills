"""Package provider (Meshy, mixamo.com) Mixamo-skeleton clip exports onto the production body.

Usage (Blender):
  Blender --background --factory-startup --python-exit-code 1 --python package_biped.py -- \
      --contract <rig-contract.json> --raw <dir of per-clip FBX/GLB exports> --production <fbx|glb> \
      --output <candidate dir> --map Idle_02=Idle --map Walking=Locomotion ... \
      [--part Object=bone] [--grip Object=bone,fraction,up|down] [polish flags]

Keeps the provider skeleton (`mixamorig:*` names) and adds a stationary `Root`
above the hips; transfers the provider skin weights onto the exact production
body with both meshes in rest pose; re-attaches rigid parts as one-bone skins
(optionally seated across the fist with `--grip`); resamples the source clips
(24 fps Meshy, 30 fps Mixamo, or `--source-fps`) to 30 fps by evaluating real
poses; strips horizontal root travel so every clip is in place; extracts foot
contacts from Locomotion so the review can measure planted-sole drift; then
runs the polish passes in this order, each recording its numbers in the
receipt:

  --leg-splay, --posture-relax, --ground-clamp (hands excluded when guarding),
  --hand-guard (+ full clamp), --plant-feet, --loop-blend, --death-hold,
  --lock-feet (+ clamp, second lock when the clamp lifted), then the opt-in
  --post-lock-loop-blend / --post-lock-cycle-correction.

`--map rawSuffix=Semantic` names which raw file is which semantic: a raw file
matches a suffix when its stem, with any trailing `_withSkin` removed, equals
the suffix or ends with `_<suffix>`. A `presets` table in the contract is only a
record of what was chosen on the provider; the map still drives the packager.
Rigid parts and grips default to the contract's `rigidParts`; `--part` and
`--grip` override or add.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import blender_common as bc  # noqa: E402
import contract as contract_module  # noqa: E402

FPS = 30
DEFAULT_SOURCE_FPS = 24
UP = Vector((0, 0, 1))
ROUTE = 'Provider Mixamo-template skeleton export, packaged onto the production body'


# ---------------------------------------------------------------- treadmill helpers

def loop_frame_index(index, frame_count):
    """Index unique loop frames; the last stored frame duplicates the first."""
    if frame_count < 2:
        raise ValueError('a loop needs a unique frame and its duplicate endpoint')
    return index % (frame_count - 1)


def fill_unsupported_steps(steps, backward):
    """Fill None pairs with median supported backward travel, never zero speed."""
    if len(backward) != 3 or not all(math.isfinite(v) for v in backward):
        raise ValueError('finite backward direction required')
    length = math.sqrt(sum(v * v for v in backward))
    if not math.isfinite(length) or length <= 0:
        raise ValueError('nonzero backward direction required')
    axis = tuple(v / length for v in backward)
    observed = [step for step in steps if step is not None]
    if not observed or any(len(step) != 3 or not all(math.isfinite(v) for v in step) for step in observed):
        raise ValueError('finite supported displacements required')
    travel = median(sum(a * b for a, b in zip(step, axis)) for step in observed)
    if not math.isfinite(travel) or travel <= 0:
        raise ValueError('supported feet must show backward treadmill travel')
    continuation = tuple(v * travel for v in axis)
    return [continuation if step is None else tuple(step) for step in steps]


# ---------------------------------------------------------------- import helpers

def long_action(rig):
    actions = [a for a in bpy.data.actions if a.users and a.frame_range[1] - a.frame_range[0] > 3]
    return max(actions, key=lambda a: a.frame_range[1] - a.frame_range[0])


def import_any(path: Path, use_anim: bool):
    before = set(bpy.data.objects)
    before_actions = set(bpy.data.actions)
    suffix = path.suffix.lower()
    if suffix == '.fbx':
        bpy.ops.import_scene.fbx(filepath=str(path.resolve()), use_anim=use_anim)
    elif suffix in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    else:
        raise SystemExit(f'Unsupported file {path}')
    objects = [o for o in bpy.data.objects if o not in before]
    actions = [a for a in bpy.data.actions if a not in before_actions]
    return objects, actions


def match_raw(files: list[Path], suffix: str) -> Path | None:
    hits = []
    for path in files:
        stem = path.stem
        if stem.lower().endswith('_withskin'):
            stem = stem[:-len('_withSkin')]
        if stem == suffix or stem.endswith(f'_{suffix}'):
            hits.append(path)
    if len(hits) > 1:
        raise SystemExit(f'Raw suffix {suffix!r} matches several files: {[h.name for h in hits]}')
    return hits[0] if hits else None


def parse_grips(specs: list[str]) -> dict:
    grips = {}
    for spec in specs:
        name, rest_spec = spec.split('=', 1)
        bone, fraction, direction = rest_spec.rsplit(',', 2)
        if direction not in ('up', 'down'):
            raise SystemExit(f'grip direction for {name} must be up or down')
        grips[name] = (bone, float(fraction), direction)
    return grips


# ---------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--raw', required=True, type=Path, help='directory of per-clip provider exports (FBX or GLB, skinned)')
    parser.add_argument('--production', required=True, type=Path, help='production model (FBX or GLB) whose body receives the weights')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--map', action='append', default=[], help='rawSuffix=Semantic')
    parser.add_argument('--part', action='append', default=[], help='PartObject=bone (overrides the contract rigidParts)')
    parser.add_argument('--grip', action='append', default=[],
                        help='Part=bone,fraction,down|up: seat a rigid part across the fist: its long axis crosses the palm, '
                             'the point at `fraction` from the handle end sits at the fist centre, the far end points down or up in rest')
    parser.add_argument('--source-fps', dest='source_fps', type=float, default=0.0,
                        help='frame rate of the raw clips; 0 reads it from the file (Meshy exports 24, Mixamo 30)')
    parser.add_argument('--ground-clamp', dest='ground_clamp', action='store_true', help='lift hips per frame so the body never sinks below the floor')
    parser.add_argument('--posture-relax', dest='posture_relax', action='append', default=[],
                        help='Semantic=fraction: blend spine/neck/head rotations toward rest by this fraction (limits provider hunch)')
    parser.add_argument('--leg-splay', dest='leg_splay', type=float, default=0.0,
                        help='radians to swing each upper leg outward about the forward axis in every clip (soles kept flat)')
    parser.add_argument('--loop-blend', dest='loop_blend', type=int, default=0,
                        help='frames: ease the tail of each looping clip into its first pose so the seam is continuous')
    parser.add_argument('--death-hold', dest='death_hold', type=float, default=0.0,
                        help='seconds of held final pose appended to Death (provider falls often end on impact)')
    parser.add_argument('--post-lock-loop-blend', type=int, default=0,
                        help='opt-in tail blend after foot IK/clamp; recheck contact and floor gates afterwards')
    parser.add_argument('--post-lock-cycle-correction', action='store_true',
                        help='distribute endpoint pose mismatch across loops after IK; preserves cyclic variation')
    parser.add_argument('--hand-guard', dest='hand_guard', action='store_true',
                        help='arm IK keeps every hand above the floor (elbows bend instead of the body lifting)')
    parser.add_argument('--lock-feet', dest='lock_feet', action='store_true',
                        help='IK-pin each planted ankle to a uniformly moving treadmill target (removes per-foot retarget slide)')
    parser.add_argument('--plant-feet', dest='plant_feet', action='store_true',
                        help='shift hips horizontally so the planted foot travels backward at one uniform speed (treadmill fix)')
    parser.add_argument('--preserve-flight-speed', action='store_true',
                        help='opt-in: continue supported treadmill velocity through airborne frame pairs; requires --plant-feet')
    parser.add_argument('--periodic-foot-lock', action='store_true',
                        help='opt-in: use unique loop period and duplicate the solved endpoint; requires --lock-feet')
    parser.add_argument('--forward-knee-hinges', action='store_true',
                        help='opt-in Mixamo knee hinge limits during foot IK to avoid backward-knee Humanoid ambiguity; requires --lock-feet')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if args.preserve_flight_speed and not args.plant_feet:
        raise SystemExit('--preserve-flight-speed requires --plant-feet')
    if args.periodic_foot_lock and not args.lock_feet:
        raise SystemExit('--periodic-foot-lock requires --lock-feet')
    if args.forward_knee_hinges and not args.lock_feet:
        raise SystemExit('--forward-knee-hinges requires --lock-feet')
    if args.output.exists():
        raise SystemExit(f'Refusing to overwrite {args.output}')
    row = contract_module.load(args.contract)
    calibration = row['calibration']
    if calibration['family'] != 'mixamo-biped':
        raise SystemExit(f"package_biped.py expects family mixamo-biped, contract says {calibration['family']!r}")
    required = list(row['requiredClips'])
    mapping = dict(m.split('=', 1) for m in args.map)
    unknown = [s for s in mapping.values() if s not in contract_module.SEMANTIC_CLIPS]
    if unknown:
        raise SystemExit(f'--map targets unknown semantics {unknown}')
    parts = {p['object']: p['bone'] for p in row.get('rigidParts', [])}
    parts.update(dict(p.split('=', 1) for p in args.part))
    grips = {p['object']: (p['bone'], float(p['grip']['fraction']), p['grip']['direction'])
             for p in row.get('rigidParts', []) if p.get('grip')}
    grips.update(parse_grips(args.grip))
    raw_files = sorted([*args.raw.glob('*.fbx'), *args.raw.glob('*.FBX'), *args.raw.glob('*.glb'), *args.raw.glob('*.gltf')])
    files = {}
    for suffix, semantic in mapping.items():
        path = match_raw(raw_files, suffix)
        if path is None:
            raise SystemExit(f'No raw export matches suffix {suffix!r} in {args.raw}; have {[p.name for p in raw_files]}')
        files[semantic] = (path, suffix)
    missing = [s for s in required if s not in files]
    if missing:
        raise SystemExit(f'No raw export mapped for {missing}; mapped {sorted(files)}')
    args.output.mkdir(parents=True)
    bc.fresh_scene()
    scene = bpy.context.scene
    receipt = {'subject': row['subjectId'], 'family': calibration['family'], 'mode': 'ground', 'route': ROUTE,
               'raw': {}, 'clips': {}, 'creditsSpent': 0, 'productionInstalled': False, 'operatorAccepted': False}
    # ---- base rig from the first clip
    first_semantic = required[0]
    objects, actions = import_any(files[first_semantic][0], use_anim=True)
    detected_fps = scene.render.fps / (scene.render.fps_base or 1.0)
    source_fps = args.source_fps or (detected_fps if 1 < detected_fps < 240 else DEFAULT_SOURCE_FPS)
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    rigs = [o for o in objects if o.type == 'ARMATURE']
    if len(rigs) != 1:
        raise SystemExit(f'{files[first_semantic][0].name}: expected one armature, found {len(rigs)}')
    rig = rigs[0]
    skinned = [o for o in objects if o.type == 'MESH' and o.vertex_groups]
    if not skinned:
        raise SystemExit(f'{files[first_semantic][0].name}: no skinned mesh; export the provider clips with skin')
    provider_body = max(skinned, key=lambda o: len(o.data.vertices))
    for o in objects:
        if o.type == 'MESH' and o is not provider_body:
            bpy.data.objects.remove(o, do_unlink=True)  # provider preview spheres etc.
    raw_actions = {first_semantic: long_action(rig)}
    receipt['raw'][first_semantic] = {'path': files[first_semantic][0].as_posix(), 'sha256': bc.sha256(files[first_semantic][0]),
                                      'suffix': files[first_semantic][1]}
    for semantic in required[1:]:
        others, new_actions = import_any(files[semantic][0], use_anim=True)
        candidates = [a for a in new_actions if a.frame_range[1] - a.frame_range[0] > 3]
        if not candidates:
            raise SystemExit(f'{files[semantic][0].name}: no animation longer than 3 frames')
        raw_actions[semantic] = max(candidates, key=lambda a: a.frame_range[1] - a.frame_range[0])
        raw_actions[semantic].use_fake_user = True
        other_rig = next((o for o in others if o.type == 'ARMATURE'), None)
        if other_rig is not None and {b.name for b in other_rig.data.bones} != {b.name for b in rig.data.bones}:
            raise SystemExit(f'{files[semantic][0].name}: skeleton differs from {files[first_semantic][0].name}')
        for o in others:
            bpy.data.objects.remove(o, do_unlink=True)
        receipt['raw'][semantic] = {'path': files[semantic][0].as_posix(), 'sha256': bc.sha256(files[semantic][0]),
                                    'suffix': files[semantic][1]}
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    for a in list(bpy.data.actions):
        if a not in raw_actions.values():
            bpy.data.actions.remove(a)
    for name in (calibration['body'], calibration['head'], *[leg['tip'] for leg in calibration['legs']]):
        if name not in rig.data.bones:
            raise SystemExit(f'Provider skeleton lacks {name}; this packager expects the Mixamo template')
    # ---- stationary Root above the provider hips
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    if calibration['root'] in rig.data.edit_bones:
        raise SystemExit(f"Provider skeleton already has a {calibration['root']} bone")
    root = rig.data.edit_bones.new(calibration['root'])
    root.head = (0, 0, 0)
    root.tail = (0, 0, 0.1)
    hips = rig.data.edit_bones[calibration['body']]
    hips.parent = root
    bpy.ops.object.mode_set(mode='OBJECT')
    rest_world = bc.rest_world_vertices(provider_body)
    floor = min(v.z for v in rest_world)
    height = max(v.z for v in rest_world) - floor
    body_bone = rig.pose.bones[calibration['body']]
    head_bone = rig.data.bones[calibration['head']]
    left_leg = next(leg for leg in calibration['legs'] if leg['side'] == 'L')
    toe_name = next((b for b in ('mixamorig:LeftToe_End', *reversed(left_leg['chain'])) if b in rig.data.bones and b != left_leg['tip']), None)
    toe = rig.data.bones[toe_name] if toe_name else head_bone
    foot = rig.data.bones[left_leg['tip']]
    forward_dir = rig.matrix_world.to_3x3() @ (toe.head_local - foot.head_local)
    forward = Vector((0, 1 if forward_dir.y >= 0 else -1, 0))
    receipt.update({'forward': list(forward), 'bodyHeight': height, 'floor': floor, 'groundForDeath': floor, 'anchorOffset': 0.0,
                    'sourceFps': source_fps, 'sourceFpsDetected': detected_fps})
    # ---- resample each clip to 30 fps, strip horizontal travel, bake
    tips = [leg['tip'] for leg in calibration['legs']]
    for semantic, action in raw_actions.items():
        bc.clear_pose(rig)
        bc.bind_action(rig, action)
        first, last = action.frame_range
        duration = (last - first) / source_fps
        frames = int(round(duration * FPS)) + 1
        hips_world = []
        for f in range(frames):
            src = first + (last - first) * (f / (frames - 1))
            scene.frame_set(int(math.floor(src)), subframe=src - math.floor(src))
            bpy.context.view_layer.update()
            hips_world.append((rig.matrix_world @ body_bone.head).copy())
        travel = hips_world[-1] - hips_world[0]
        travel.z = 0.0
        strip = travel.length > 0.02 * height
        samples = []
        feet = []
        for f in range(frames):
            src = first + (last - first) * (f / (frames - 1))
            scene.frame_set(int(math.floor(src)), subframe=src - math.floor(src))
            bpy.context.view_layer.update()
            if strip:
                drift = travel * (f / (frames - 1))
                local = body_bone.bone.matrix_local.to_3x3().inverted() @ (rig.matrix_world.to_3x3().inverted() @ drift)
                body_bone.location = body_bone.location - local
                bpy.context.view_layer.update()
            samples.append(bc.bake_pose_sample(rig))
            feet.append({n: (rig.matrix_world @ rig.pose.bones[n].head).copy() for n in tips})
            if strip:
                body_bone.location = body_bone.location + local
        rig.animation_data.action = None
        bc.write_action(rig, semantic, samples)
        entry = {'frames': [1, frames], 'durationSeconds': (frames - 1) / FPS, 'loop': semantic in contract_module.LOOPING_SEMANTICS,
                 'holdFinalPose': semantic == 'Death', 'sourceFps': source_fps, 'sourceFrames': [first, last],
                 'rootTravelStrippedUnits': travel.length if strip else 0.0, 'contacts': [],
                 'sourcePreset': files[semantic][1]}
        if semantic == 'Locomotion':
            contacts, speed = extract_contacts(feet, calibration, forward, height, frames)
            entry.update({'contacts': contacts, 'gait': f"provider preset {entry['sourcePreset']}", 'nominalSpeedUnitsPerSecond': speed,
                          'nominalSpeedBodyHeightsPerSecond': speed / height})
        if semantic == 'BasicAttack':
            entry['visualContactNormalizedTime'] = 0.5
        receipt['clips'][semantic] = entry
    for action in list(raw_actions.values()):
        bpy.data.actions.remove(action)
    # ---- production body + rigid parts
    prod, _ = import_any(args.production, use_anim=False)
    prod_meshes = [o for o in prod if o.type == 'MESH']
    part_objects = [o for o in prod_meshes if o.name in parts]
    missing_parts = sorted(set(parts) - {o.name for o in part_objects})
    if missing_parts:
        raise SystemExit(f'Rigid parts not found in {args.production.name}: {missing_parts}; meshes are {[o.name for o in prod_meshes]}')
    bodies = [o for o in prod_meshes if o.name not in parts]
    if not bodies:
        raise SystemExit('Production model has no body mesh besides the rigid parts')
    prod_body = max(bodies, key=lambda o: len(o.data.vertices))
    for o in (prod_body, *part_objects):
        matrix = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = matrix
        for mod in list(o.modifiers):
            o.modifiers.remove(mod)
        o.vertex_groups.clear()
    for o in prod:
        if o.type != 'MESH' or (o is not prod_body and o not in part_objects):
            bpy.data.objects.remove(o, do_unlink=True)
    # transfer weights between the two REST bodies: unbind clips and force the rest pose
    rig.animation_data.action = None
    bc.clear_pose(rig)
    rig.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    rest_world = bc.evaluated_world_vertices(provider_body)
    prod_rest = bc.rest_world_vertices(prod_body)
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromPolygons([tuple(v) for v in rest_world], [tuple(p.vertices) for p in provider_body.data.polygons])
    worst = max(tree.find_nearest(v)[3] for v in prod_rest)
    for group in provider_body.vertex_groups:
        prod_body.vertex_groups.new(name=group.name)
    transfer = prod_body.modifiers.new('WeightTransfer', 'DATA_TRANSFER')
    transfer.object = provider_body
    transfer.use_vert_data = True
    transfer.data_types_verts = {'VGROUP_WEIGHTS'}
    transfer.vert_mapping = 'POLYINTERP_NEAREST'
    transfer.layers_vgroup_select_src = 'ALL'
    transfer.layers_vgroup_select_dst = 'NAME'
    bpy.context.view_layer.objects.active = prod_body
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    unweighted = sum(1 for v in prod_body.data.vertices if sum(g.weight for g in v.groups) < 1e-4)
    if unweighted:
        raise SystemExit(f'{unweighted} production vertices received no weight')
    armature = prod_body.modifiers.new('Armature', 'ARMATURE')
    armature.object = rig
    matrix = prod_body.matrix_world.copy()
    prod_body.parent = rig
    prod_body.matrix_world = matrix
    receipt['gripAdjust'] = {}
    for part in part_objects:
        if part.name in grips:
            receipt['gripAdjust'][part.name] = fit_grip(part, rig, prod_body, *grips[part.name])
        bc.skin_rigid_to_bone(part, rig, parts[part.name])
    original_name = prod_body.name.split('.')[0]
    bpy.data.objects.remove(provider_body, do_unlink=True)
    rig.data.pose_position = 'POSE'
    prod_body.name = original_name
    prod_body.data.name = original_name
    rig.name = f"{row['folder']}_Rig"
    rig.data.name = rig.name
    receipt['weightTransfer'] = {'method': 'DATA_TRANSFER POLYINTERP_NEAREST from provider skin to production body, both in rest pose',
                                 'productionVertices': len(prod_body.data.vertices), 'providerVertices': len(rest_world),
                                 'maxSurfaceDistance': worst, 'maxSurfaceDistanceBodyHeights': worst / height}
    receipt['rigidParts'] = [{'object': p.name, 'bone': parts[p.name]} for p in part_objects]
    receipt['skeleton'] = [b.name for b in rig.data.bones]
    # ---- polish passes, in order
    if args.leg_splay:
        receipt['legSplay'] = leg_splay(rig, calibration, forward, args.leg_splay, receipt['clips'])
    relax = {k: float(v) for k, v in (m.split('=', 1) for m in args.posture_relax)}
    if relax:
        receipt['postureRelax'] = posture_relax(rig, calibration, relax, receipt['clips'])
    hand_prefixes = tuple(arm['chain'][-1] for arm in calibration.get('arms', [])) if args.hand_guard else ()
    if args.ground_clamp:
        # first clamp ignores the hands: their penetration is the hand guard's job (elbows/shoulders), not a body lift
        receipt['groundClamp'] = ground_clamp(rig, body_bone, prod_body, floor, receipt['clips'], exclude_prefixes=hand_prefixes, periodic_loops=args.periodic_foot_lock)
    if args.hand_guard:
        receipt['handGuard'] = hand_guard(rig, calibration, prod_body, floor, height, receipt['clips'])
        if args.ground_clamp:
            receipt['groundClampAfterHands'] = ground_clamp(rig, body_bone, prod_body, floor, receipt['clips'], periodic_loops=args.periodic_foot_lock)
    if args.plant_feet and 'Locomotion' in receipt['clips']:
        receipt['plantFeet'] = plant_feet(rig, body_bone, calibration, forward, height, receipt['clips']['Locomotion'], args.preserve_flight_speed)
    if args.loop_blend:
        receipt['loopBlend'] = loop_blend(rig, args.loop_blend, receipt['clips'])
    if args.death_hold and 'Death' in receipt['clips']:
        receipt['deathHold'] = death_hold(rig, args.death_hold, receipt['clips']['Death'])
    if args.lock_feet and 'Locomotion' in receipt['clips']:
        receipt['lockFeet'] = lock_feet(rig, calibration, forward, height, receipt['clips']['Locomotion'], body=prod_body, floor=floor, periodic_loops=args.periodic_foot_lock, forward_knees=args.forward_knee_hinges)
        if args.ground_clamp:
            receipt['groundClampAfterLock'] = ground_clamp(rig, body_bone, prod_body, floor, {'Locomotion': receipt['clips']['Locomotion']}, periodic_loops=args.periodic_foot_lock)
            if receipt['groundClampAfterLock']['Locomotion']['maxLiftUnits'] > 0.005:
                # the clamp lifted some planted frames (a lowered hip pushed something under the floor);
                # re-lock with each stance held at its lifted height so the contact stays stationary
                receipt['lockFeetSecondPass'] = lock_feet(rig, calibration, forward, height, receipt['clips']['Locomotion'], z_mode='max', periodic_loops=args.periodic_foot_lock, forward_knees=args.forward_knee_hinges)
                receipt['groundClampAfterSecondLock'] = ground_clamp(rig, body_bone, prod_body, floor, {'Locomotion': receipt['clips']['Locomotion']}, periodic_loops=args.periodic_foot_lock)
    bc.clear_pose(rig)
    if args.post_lock_loop_blend:
        receipt['postLockLoopBlend'] = loop_blend(rig, args.post_lock_loop_blend, receipt['clips'])
    if args.post_lock_cycle_correction:
        receipt['postLockCycleCorrection'] = cycle_correction(rig, receipt['clips'])
    first_action = bpy.data.actions[required[0]]
    bc.bind_action(rig, first_action)
    scene.frame_start, scene.frame_end = 1, int(first_action.frame_range[1])
    scene.frame_set(1)
    blend = args.output / f"{row['folder']}_Actions.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()))
    receipt['blend'] = {'path': blend.as_posix(), 'sha256': bc.sha256(blend)}
    receipt['source'] = {'path': args.production.as_posix(), 'sha256': bc.sha256(args.production)}
    receipt['contract'] = {**contract_module.describe(row), 'path': row['contractPath'], 'presets': row.get('presets')}
    receipt['passes'] = [key for key in ('legSplay', 'postureRelax', 'groundClamp', 'handGuard', 'groundClampAfterHands', 'plantFeet',
                                         'loopBlend', 'deathHold', 'lockFeet', 'groundClampAfterLock', 'lockFeetSecondPass',
                                         'groundClampAfterSecondLock', 'postLockLoopBlend', 'postLockCycleCorrection') if key in receipt]
    bc.write_json(args.output / 'receipt.json', receipt)
    print(json.dumps({'subject': row['subjectId'], 'height': height, 'sourceFps': source_fps,
                      'clips': {k: {a: b for a, b in v.items() if a != 'contacts'} for k, v in receipt['clips'].items()},
                      'weightTransfer': receipt['weightTransfer'], 'passes': receipt['passes']}))


# ---------------------------------------------------------------- passes

def fit_grip(part, rig, body, bone, fraction, direction):
    """Seat a rigid part in a fist. Rest-pose geometry only: the fist is the body's vertices weighted to
    `bone`; its principal axes give the finger direction (longest), the palm normal (shortest) and the
    knuckle line across the palm (middle), which is where a held shaft runs. The part's long axis is
    aligned to that line, its point at `fraction` from the handle end is moved to the fist centre, and
    the far end points `down` or `up` in the rest pose. Returns the applied transform for the receipt."""
    import numpy as np
    if bone not in body.vertex_groups:
        raise SystemExit(f'grip bone {bone} has no vertex group on the production body')
    gid = body.vertex_groups[bone].index
    fist = np.array([[*(body.matrix_world @ v.co)] for v in body.data.vertices
                     if any(g.group == gid and g.weight > 0.5 for g in v.groups)])
    if len(fist) < 4:
        raise SystemExit(f'grip bone {bone} carries too few vertices ({len(fist)}) to find a fist')
    centre = fist.mean(axis=0)
    with np.errstate(all='ignore'):  # Accelerate-backed numpy warns spuriously on small matmuls; results are checked below
        _, _, vt = np.linalg.svd(fist - centre, full_matrices=False)
        finger_dir, knuckle_dir = vt[0], vt[1]
        pts = np.array([[*(part.matrix_world @ v.co)] for v in part.data.vertices])
        pc = pts.mean(axis=0)
        _, _, pvt = np.linalg.svd(pts - pc, full_matrices=False)
        axis = pvt[0]
        proj = (pts - pc) @ axis
    if not (np.isfinite(proj).all() and np.isfinite(vt).all()):
        raise SystemExit(f'grip seating for {part.name} produced non-finite geometry')
    lo, hi = proj.min(), proj.max()
    # the handle end is the end the modeler left nearer the fist (a sword's guard is thicker than its
    # tip and a club's head is thicker than its handle, so thickness alone cannot tell them apart)
    end_lo, end_hi = pc + axis * lo, pc + axis * hi
    handle_end, head_end = (end_lo, end_hi) if np.linalg.norm(end_lo - centre) <= np.linalg.norm(end_hi - centre) else (end_hi, end_lo)
    shaft = head_end - handle_end
    length = float(np.linalg.norm(shaft))
    shaft /= length
    target_dir = knuckle_dir if (knuckle_dir[2] < 0) == (direction == 'down') else -knuckle_dir
    grip_point = handle_end + shaft * (length * fraction)
    rot = Vector(shaft).rotation_difference(Vector(target_dir)).to_matrix().to_4x4()
    move = Matrix.Translation(Vector(centre) - rot @ Vector(grip_point))
    transform = move @ rot
    part.matrix_world = transform @ part.matrix_world
    return {'bone': bone, 'fraction': fraction, 'direction': direction, 'partLengthUnits': length,
            'gripPointBefore': [float(x) for x in grip_point], 'fistCentre': [float(x) for x in centre],
            'rotationDegrees': math.degrees(Vector(shaft).angle(Vector(target_dir))),
            'translationUnits': float((Vector(centre) - Vector(grip_point)).length)}


def leg_splay(rig, calibration, forward, angle, clips):
    """Swing each upper leg outward about the forward axis in every clip, keeping the sole orientation.

    Human presets hold the thighs parallel under the hips; on a wide-stanced brute that reads as legs
    glued together. The rotation is applied in world space per frame (the knee follows); the foot is
    counter-rotated back to its provider orientation so the sole stays flat for the clamp and lock."""
    scene = bpy.context.scene
    arm_axis = (rig.matrix_world.to_3x3().inverted() @ forward).normalized()
    # the outward direction is decided once per leg from the rest pose (a forward-flexed thigh
    # makes a per-frame test flip sides between frames)
    signs = {}
    for leg in calibration['legs']:
        bone = rig.data.bones[leg['chain'][0]]
        head, tail = bone.head_local, bone.tail_local
        side = 1.0 if (rig.matrix_world @ head).x >= 0 else -1.0
        vector = tail - head
        moved = Matrix.Rotation(0.05, 3, arm_axis) @ vector - vector
        signs[leg['id']] = 1.0 if (rig.matrix_world.to_3x3() @ moved).x * side > 0 else -1.0
    report = {'signs': signs}
    for semantic, entry in clips.items():
        action = bpy.data.actions[semantic]
        bc.clear_pose(rig)
        bc.bind_action(rig, action)
        first, last = entry['frames']
        for f in range(first, last + 1):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            for leg in calibration['legs']:
                upper = rig.pose.bones[leg['chain'][0]]
                foot = rig.pose.bones[leg['tip']]
                head = upper.matrix.translation.copy()
                foot_rot_before = foot.matrix.to_3x3().copy()
                spin = Matrix.Translation(head) @ Matrix.Rotation(signs[leg['id']] * angle, 4, arm_axis) @ Matrix.Translation(-head)
                upper.matrix = spin @ upper.matrix
                upper.keyframe_insert('rotation_quaternion', frame=f)
                bpy.context.view_layer.update()
                foot_pos = foot.matrix.translation.copy()
                foot.matrix = Matrix.Translation(foot_pos) @ foot_rot_before.to_4x4()
                foot.keyframe_insert('rotation_quaternion', frame=f)
                bpy.context.view_layer.update()
        rig.animation_data.action = None
        report[semantic] = {'radians': angle}
    bc.clear_pose(rig)
    return report


def posture_relax(rig, calibration, fractions, clips):
    """Blend the spine, neck and head pose rotations toward rest by a fraction per clip.

    Provider presets carry human torso leans; on a long-spined brute the same angles hide the head
    behind the shoulders and trip the posture gate. Descendants (arms, hands) follow the relaxed spine."""
    scene = bpy.context.scene
    middle = [name for name in calibration.get('extra', []) if 'Spine' in name]
    chain = [calibration.get('spine'), *middle, calibration.get('chest'), *calibration.get('neck', []), calibration['head']]
    chain = [b for b in chain if b and b in rig.pose.bones]
    identity = Quaternion((1.0, 0.0, 0.0, 0.0))
    report = {}
    for semantic, fraction in fractions.items():
        if semantic not in clips:
            raise SystemExit(f'--posture-relax names {semantic}, which is not a packaged clip')
        entry = clips[semantic]
        action = bpy.data.actions[semantic]
        bc.clear_pose(rig)
        bc.bind_action(rig, action)
        first, last = entry['frames']
        worst = 0.0
        for f in range(first, last + 1):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            for name in chain:
                bone = rig.pose.bones[name]
                q = bone.rotation_quaternion.copy()
                worst = max(worst, q.angle if q.angle <= math.pi else 2 * math.pi - q.angle)
                bone.rotation_quaternion = q.slerp(identity, fraction)
                bone.keyframe_insert('rotation_quaternion', frame=f)
        rig.animation_data.action = None
        report[semantic] = {'fraction': fraction, 'bones': chain, 'maxSourceAngleRadians': worst}
    bc.clear_pose(rig)
    return report


def plant_feet(rig, body_bone, calibration, forward, height, entry, preserve_flight_speed=False):
    """Make the treadmill uniform: shift the hips horizontally per frame so the planted foot slides backward
    at one constant speed (the loop-average), then record that speed as the clip's nominal travel rate."""
    scene = bpy.context.scene
    action = bpy.data.actions['Locomotion']
    bc.clear_pose(rig)
    bc.bind_action(rig, action)
    first, last = entry['frames']
    n = last - first + 1
    legs = [leg['id'] for leg in calibration['legs']]
    tips = {leg['id']: leg['tip'] for leg in calibration['legs']}
    planted = {leg: [False] * n for leg in legs}
    for c in entry['contacts']:
        planted[c['leg']][c['frame'] - 1] = c['planted']
    pos = {leg: [] for leg in legs}
    for f in range(first, last + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        for leg in legs:
            p = bc.bone_world_head(rig, tips[leg])
            pos[leg].append(Vector((p.x, p.y, 0.0)))
    # cumulative treadmill displacement: the mean motion of every foot planted across the frame pair,
    # so double support splits any inter-foot mismatch instead of loading it onto one foot
    steps = []
    for i in range(1, n):
        moving = [pos[leg][i] - pos[leg][i - 1] for leg in legs if planted[leg][i] and planted[leg][i - 1]]
        steps.append(sum(moving, Vector((0.0, 0.0, 0.0))) / len(moving) if moving else None)
    unsupported = sum(step is None for step in steps)
    backward = -forward
    if preserve_flight_speed:
        steps = [Vector(step) for step in fill_unsupported_steps(steps, backward)]
    else:
        steps = [step if step is not None else Vector((0.0, 0.0, 0.0)) for step in steps]
    D = [Vector((0.0, 0.0, 0.0))]
    for step in steps:
        D.append(D[-1] + step)
    along = D[-1].dot(backward)
    duration = (n - 1) / FPS
    speed = along / duration
    if speed <= 0.0:
        rig.animation_data.action = None
        return {'applied': False, 'reason': 'no backward treadmill travel'}
    lateral = D[-1] - backward * along
    to_local = body_bone.bone.matrix_local.to_3x3().inverted() @ rig.matrix_world.to_3x3().inverted()
    worst = 0.0
    for i, f in enumerate(range(first, last + 1)):
        t = i / FPS
        offset = -D[i] + backward * (speed * t) + lateral * (i / (n - 1))
        worst = max(worst, offset.length)
        scene.frame_set(f)
        bpy.context.view_layer.update()
        body_bone.location = body_bone.location + (to_local @ offset)
        body_bone.keyframe_insert('location', frame=f)
    rig.animation_data.action = None
    bc.clear_pose(rig)
    report = {'applied': True, 'speedBeforeUnitsPerSecond': entry['nominalSpeedUnitsPerSecond'], 'speedAfterUnitsPerSecond': speed,
              'preserveFlightSpeed': preserve_flight_speed, 'unsupportedFramePairs': unsupported,
              'maxHipOffsetUnits': worst, 'maxHipOffsetBodyHeights': worst / height, 'loopLateralResidualUnits': lateral.length}
    entry['nominalSpeedUnitsPerSecond'] = speed
    entry['nominalSpeedBodyHeightsPerSecond'] = speed / height
    entry['gait'] = f"provider preset {entry.get('sourcePreset', 'unspecified')}, planted-foot speed equalised"
    return report


def lock_feet(rig, calibration, forward, height, entry, blend_frames=4, z_mode='min', body=None, floor=0.0, periodic_loops=False, forward_knees=False):
    """Pin planted ankles with leg IK so every contact slides backward at exactly the clip's treadmill speed.

    Rotation-only retargets onto legs with other proportions make each foot follow its own path, so the
    hips alone cannot keep both planted feet consistent. Per stance the ankle is held on a line moving at
    the nominal speed through the stance's least-squares anchor; the correction fades over `blend_frames`
    of swing on either side. Vertical and foot orientation stay as the provider posed them."""
    scene = bpy.context.scene
    action = bpy.data.actions['Locomotion']
    bc.clear_pose(rig)
    bc.bind_action(rig, action)
    first, last = entry['frames']
    n = last - first + 1
    loop = entry['loop']
    speed = entry['nominalSpeedUnitsPerSecond']
    backward = -forward
    legs = calibration['legs']
    if forward_knees and any(leg['ikChain'] != 2 or leg['ik'] not in
                            ('mixamorig:LeftLeg', 'mixamorig:RightLeg') for leg in legs):
        raise ValueError('Forward knee hinges require the two-bone Mixamo leg calibration')
    planted = {leg['id']: [False] * n for leg in legs}
    for c in entry['contacts']:
        planted[c['leg']][c['frame'] - 1] = c['planted']
    if periodic_loops and loop and any(flags[0] != flags[-1] for flags in planted.values()):
        raise ValueError('Periodic foot lock requires matching duplicate-endpoint contact flags')
    ankle = {leg['id']: [] for leg in legs}
    foot_rot = {leg['id']: [] for leg in legs}
    toes = {leg['id']: next((b for b in leg['chain'] if b.endswith('ToeBase')), None) for leg in legs}
    toe_rot = {leg['id']: [] for leg in legs}
    sole_ids = {}
    if body is not None and z_mode == 'min':
        for leg in legs:
            sole_ids[leg['id']] = bc.sole_vertices(body, leg['sole'], threshold=calibration.get('soleWeightThreshold', 0.05))
    sole_low = {leg['id']: [] for leg in legs}
    for f in range(first, last + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        world = bc.evaluated_world_vertices(body) if sole_ids else None
        for leg in legs:
            if sole_ids.get(leg['id']):
                sole_low[leg['id']].append(min(world[i].z for i in sole_ids[leg['id']]))
            ankle[leg['id']].append((rig.matrix_world @ rig.pose.bones[leg['ik']].tail).copy())
            foot_rot[leg['id']].append((rig.matrix_world @ rig.pose.bones[leg['tip']].matrix).to_quaternion())
            toe_rot[leg['id']].append(rig.pose.bones[toes[leg['id']]].rotation_quaternion.copy() if toes[leg['id']] else None)

    # stance segments (circular for loops): lists of frame indices
    def segments(flags):
        segs, cur = [], []
        for i, on in enumerate(flags):
            if on:
                cur.append(i)
            elif cur:
                segs.append(cur); cur = []
        if cur:
            segs.append(cur)
        if loop and len(segs) > 1 and flags[0] and flags[-1]:
            segs[0] = segs[-1] + segs[0]
            segs.pop()
        return segs
    delta = {leg['id']: [Vector((0.0, 0.0, 0.0)) for _ in range(n)] for leg in legs}
    rot_target = {leg['id']: list(foot_rot[leg['id']]) for leg in legs}
    toe_target = {leg['id']: list(toe_rot[leg['id']]) for leg in legs}
    worst = 0.0
    for leg in legs:
        lid = leg['id']
        for seg in segments(planted[lid]):
            # flat foot through the stance: hold the ankle at the stance's lowest height with the sole
            # orientation of that frame (no heel roll), so the contact really is stationary
            lowest = (min if z_mode == 'min' else max)(seg, key=lambda i: ankle[lid][i].z)
            z_lock = ankle[lid][lowest].z
            if sole_low.get(lid):
                # seat the sole itself on the floor: the ankle height alone can leave a splayed foot hovering
                z_lock -= sole_low[lid][lowest] - floor
            rot_lock = foot_rot[lid][lowest]
            toe_lock = toe_rot[lid][lowest]
            # unwrap times so a wrapped segment is monotonic
            times = []
            t_prev = None
            for k, i in enumerate(seg):
                t = i / FPS
                if t_prev is not None and t < t_prev:
                    t += (n - 1) / FPS
                times.append(t); t_prev = t
            t0 = times[0]
            anchor = sum((ankle[lid][i] - backward * (speed * (t - t0)) for i, t in zip(seg, times)), Vector((0.0, 0.0, 0.0))) / len(seg)
            for i, t in zip(seg, times):
                target = anchor + backward * (speed * (t - t0))
                d = target - ankle[lid][i]
                d.z = z_lock - ankle[lid][i].z
                delta[lid][i] = d
                rot_target[lid][i] = rot_lock
                toe_target[lid][i] = toe_lock
                worst = max(worst, d.length)
            # fade the correction into the neighbouring swing frames
            for edge, direction, d_edge in ((seg[0], -1, delta[lid][seg[0]]), (seg[-1], 1, delta[lid][seg[-1]])):
                for k in range(1, blend_frames + 1):
                    j = edge + direction * k
                    if loop:
                        j = loop_frame_index(j, n) if periodic_loops else j % n
                    elif not 0 <= j < n:
                        break
                    if planted[lid][j]:
                        break
                    w = 1 - k / (blend_frames + 1)
                    delta[lid][j] = d_edge * w
                    rot_target[lid][j] = foot_rot[lid][j].slerp(rot_lock, w)
                    if toe_lock is not None:
                        toe_target[lid][j] = toe_rot[lid][j].slerp(toe_lock, w)
    # IK rigs
    targets = []
    knee_settings = []
    for leg in legs:
        if forward_knees:
            knee = rig.pose.bones[leg['ik']]
            values = {'lock_ik_y': True, 'lock_ik_z': True, 'use_ik_limit_x': True,
                      'ik_min_x': .02, 'ik_max_x': 2.8}
            knee_settings.append((knee, {key: getattr(knee, key) for key in values}))
            for key, value in values.items():
                setattr(knee, key, value)
        target = bpy.data.objects.new('IKLock_' + leg['id'], None)
        scene.collection.objects.link(target)
        target.rotation_mode = 'QUATERNION'
        ik = rig.pose.bones[leg['ik']].constraints.new('IK')
        ik.target = target
        ik.chain_count = leg['ikChain']
        ik.use_stretch = False
        ik.iterations = 500
        orientation = rig.pose.bones[leg['tip']].constraints.new('COPY_ROTATION')
        orientation.target = target
        orientation.owner_space = 'WORLD'
        orientation.target_space = 'WORLD'
        targets.append((leg, target, ik, orientation))
    samples = []
    worst_residual = 0.0
    worst_lowering = 0.0
    body_bone = rig.pose.bones[calibration['body']]
    to_local = body_bone.bone.matrix_local.to_3x3().inverted() @ rig.matrix_world.to_3x3().inverted()

    def pose_frame(k, f):
        scene.frame_set(f)
        for leg, target, _, _ in targets:
            target.location = ankle[leg['id']][k] + delta[leg['id']][k]
            target.rotation_quaternion = rot_target[leg['id']][k]
            if toes[leg['id']] and toe_target[leg['id']][k] is not None:
                rig.pose.bones[toes[leg['id']]].rotation_quaternion = toe_target[leg['id']][k]
        bpy.context.view_layer.update()

    def reach_gap(k):
        gaps = [((rig.matrix_world @ rig.pose.bones[leg['ik']].tail) - target.location).length
                for leg, target, _, _ in targets if planted[leg['id']][k] or delta[leg['id']][k].length > 0.0]
        return max(gaps) if gaps else 0.0

    # probe: how far the hips must drop per frame so every planted target is reachable
    # (splayed or short legs); then smooth that curve with an element-wise max so the
    # drop never falls short of a frame's need but no longer switches on within one frame
    needed = []
    for k, f in enumerate(range(first, last + 1)):
        pose_frame(k, f)
        lowered = 0.0
        for _ in range(4):
            gap = reach_gap(k)
            if gap <= 0.005:
                break
            body_bone.location = body_bone.location + (to_local @ Vector((0.0, 0.0, -gap)))
            lowered += gap
            bpy.context.view_layer.update()
        needed.append(lowered)
    # a wide stance needs a lower pelvis for the whole clip: apply the largest per-frame need everywhere
    # (a per-frame drop dives and leaps at every stance change)
    lowering = [max(needed)] * n
    for k, f in enumerate(range(first, last + 1)):
        pose_frame(k, f)
        if lowering[k] > 0.0:
            body_bone.location = body_bone.location + (to_local @ Vector((0.0, 0.0, -lowering[k])))
            body_bone.keyframe_insert('location', frame=f)
            bpy.context.view_layer.update()
            worst_lowering = max(worst_lowering, lowering[k])
        for leg, target, _, _ in targets:
            residual = ((rig.matrix_world @ rig.pose.bones[leg['ik']].tail) - target.location).length
            worst_residual = max(worst_residual, residual)
        samples.append(bc.bake_pose_sample(rig))
    if periodic_loops and loop:
        # IK can solve the same endpoint slightly differently after traversing
        # the cycle. Its duplicate is not a new stance sample: reuse frame zero
        # without distributing a correction through already-planted frames.
        samples[-1] = {name: matrix.copy() for name, matrix in samples[0].items()}
    for leg, target, ik, orientation in targets:
        rig.pose.bones[leg['ik']].constraints.remove(ik)
        rig.pose.bones[leg['tip']].constraints.remove(orientation)
        bpy.data.objects.remove(target, do_unlink=True)
    for knee, values in knee_settings:
        for key, value in values.items():
            setattr(knee, key, value)
    rig.animation_data.action = None
    bpy.data.actions.remove(action)
    bc.write_action(rig, 'Locomotion', samples)
    bc.clear_pose(rig)
    entry['gait'] = f"provider preset {entry.get('sourcePreset', 'unspecified')}, planted feet IK-locked to a uniform treadmill"
    return {'applied': True, 'periodicLoops': periodic_loops, 'forwardKneeHinges': forward_knees, 'maxAnkleCorrectionUnits': worst, 'maxAnkleCorrectionBodyHeights': worst / height, 'blendFrames': blend_frames,
            'maxIkResidualUnits': worst_residual, 'maxHipLoweringUnits': worst_lowering, 'toesLocked': [t for t in toes.values() if t],
            'stanceHeight': z_mode}


def hand_guard(rig, calibration, body, floor, height, clips, window=2):
    """Keep every hand above the floor with two-bone arm IK. Long arms on a brute reach under the floor
    in slams and falls; lifting the body for them (ground clamp) makes it hop, so instead the wrist is
    raised just enough for the hand's lowest vertex to rest on the floor, the elbow bends, and the hand
    keeps its provider orientation. Runs before the ground clamp; the raise curve is smoothed with an
    element-wise max so it never falls short of a frame's need."""
    scene = bpy.context.scene
    arms = calibration.get('arms', [])
    if not arms:
        return {}
    ids = {}
    for arm in arms:
        prefix = arm['chain'][-1]  # mixamorig:LeftHand
        groups = {g.index for g in body.vertex_groups if g.name.startswith(prefix)}
        ids[arm['side']] = [v.index for v in body.data.vertices if any(g.group in groups and g.weight > 0.5 for g in v.groups)]
    report = {}
    for semantic, entry in clips.items():
        action = bpy.data.actions[semantic]
        bc.clear_pose(rig)
        bc.bind_action(rig, action)
        first, last = entry['frames']
        n = last - first + 1
        wrist = {a['side']: [] for a in arms}
        shoulder = {a['side']: [] for a in arms}
        hand_rot = {a['side']: [] for a in arms}
        need = {a['side']: [] for a in arms}
        hips_pos = []
        for f in range(first, last + 1):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            world = bc.evaluated_world_vertices(body)
            hips_pos.append((rig.matrix_world @ rig.pose.bones[calibration['body']].head).copy())
            for arm in arms:
                side = arm['side']
                wrist[side].append((rig.matrix_world @ rig.pose.bones[arm['chain'][2]].tail).copy())
                shoulder[side].append((rig.matrix_world @ rig.pose.bones[arm['chain'][1]].head).copy())
                hand_rot[side].append((rig.matrix_world @ rig.pose.bones[arm['chain'][3]].matrix).to_quaternion())
                low = min(world[i].z for i in ids[side]) if ids[side] else floor
                need[side].append(max(0.0, floor - low))
        if all(max(need[a['side']]) <= 0.0 for a in arms):
            rig.animation_data.action = None
            continue
        raise_by = {}
        for arm in arms:
            side = arm['side']
            sm = []
            for i in range(n):
                idx = [((i + j) % n if entry['loop'] else min(n - 1, max(0, i + j))) for j in range(-window, window + 1)]
                sm.append(max(need[side][i], sum(need[side][j] for j in idx) / len(idx)))
            raise_by[side] = sm
        targets = []
        for arm in arms:
            target = bpy.data.objects.new('IKHand_' + arm['side'], None)
            scene.collection.objects.link(target)
            target.rotation_mode = 'QUATERNION'
            ik = rig.pose.bones[arm['chain'][2]].constraints.new('IK')
            ik.target = target
            # a small raise bends the elbow; a large one (an arm lying through the floor) turns the
            # whole arm at the shoulder so it can lie flat instead of pointing up
            ik.chain_count = 3 if max(raise_by[arm['side']]) > 0.25 * height else 2
            ik.use_stretch = False
            ik.iterations = 500
            orientation = rig.pose.bones[arm['chain'][3]].constraints.new('COPY_ROTATION')
            orientation.target = target
            orientation.owner_space = 'WORLD'
            orientation.target_space = 'WORLD'
            targets.append((arm, target, ik, orientation))
        samples = []
        worst_residual = 0.0
        for k, f in enumerate(range(first, last + 1)):
            scene.frame_set(f)
            for arm, target, ik, _ in targets:
                side = arm['side']
                if ik.chain_count == 3 and raise_by[side][k] > 0.0:
                    # swing the whole arm about the shoulder in its own vertical plane, keeping its
                    # extension, until the hand rests on the floor (an arm lying on the ground)
                    v = wrist[side][k] - shoulder[side][k]
                    reach = v.length
                    z = max(-reach, min(reach, v.z + raise_by[side][k]))
                    # an arm hanging straight down has no horizontal direction of its own: bias it
                    # outward, away from the hips, so it lies out to the side instead of folding up
                    outward = shoulder[side][k] - hips_pos[k]
                    outward = Vector((outward.x, outward.y, 0.0))
                    flat = Vector((v.x, v.y, 0.0)) + (outward.normalized() * 0.25 * reach if outward.length > 1e-6 else Vector((0.0, 0.0, 0.0)))
                    horizontal = flat.normalized() * math.sqrt(max(0.0, reach * reach - z * z)) if flat.length > 1e-6 else Vector((0.0, 0.0, 0.0))
                    target.location = shoulder[side][k] + horizontal + Vector((0.0, 0.0, z))
                else:
                    target.location = wrist[side][k] + Vector((0.0, 0.0, raise_by[side][k]))
                target.rotation_quaternion = hand_rot[side][k]
            bpy.context.view_layer.update()
            for arm, target, _, _ in targets:
                if raise_by[arm['side']][k] > 0.0:
                    worst_residual = max(worst_residual, ((rig.matrix_world @ rig.pose.bones[arm['chain'][2]].tail) - target.location).length)
            samples.append(bc.bake_pose_sample(rig))
        for arm, target, ik, orientation in targets:
            rig.pose.bones[arm['chain'][2]].constraints.remove(ik)
            rig.pose.bones[arm['chain'][3]].constraints.remove(orientation)
            bpy.data.objects.remove(target, do_unlink=True)
        rig.animation_data.action = None
        bpy.data.actions.remove(action)
        bc.write_action(rig, semantic, samples)
        report[semantic] = {side: {'maxRaiseUnits': max(raise_by[side]), 'framesRaised': sum(1 for v in raise_by[side] if v > 0),
                                   'chain': 3 if max(raise_by[side]) > 0.25 * height else 2} for side in raise_by}
        report[semantic]['maxIkResidualUnits'] = worst_residual
    bc.clear_pose(rig)
    return report


def cycle_correction(rig, clips):
    """Remove only endpoint drift, not the intervening cyclic performance.

    Sample the complete original cycle before writing keys so interpolation of
    edited keys cannot feed back into later frames. Always recheck contact gates.
    """
    scene = bpy.context.scene
    report = {}
    for semantic, entry in clips.items():
        if not entry['loop']:
            continue
        bc.clear_pose(rig)
        bc.bind_action(rig, bpy.data.actions[semantic])
        first, last = entry['frames']
        samples = []
        for frame in range(first, last + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            samples.append({b.name: (b.location.copy(), b.rotation_quaternion.copy())
                            for b in rig.pose.bones})
        for index, pose in enumerate(samples):
            phase = index / (last - first)
            scene.frame_set(first + index)
            for bone in rig.pose.bones:
                start_loc, start_rot = samples[0][bone.name]
                end_loc, end_rot = samples[-1][bone.name]
                loc, rot = pose[bone.name]
                correction = end_rot.inverted() @ start_rot
                bone.location = loc + (start_loc - end_loc) * phase
                bone.rotation_quaternion = rot @ Quaternion().slerp(correction, phase)
                bone.keyframe_insert('location', frame=first + index)
                bone.keyframe_insert('rotation_quaternion', frame=first + index)
        rig.animation_data.action = None
        report[semantic] = {'frames': len(samples), 'method': 'linear endpoint residual, sampled before mutation'}
    bc.clear_pose(rig)
    return report


def loop_blend(rig, frames, clips):
    """Ease the last `frames` of each looping clip toward its first pose (rotation slerp, location lerp) so
    the loop seam is continuous. Provider walks and idles rarely return exactly to their first frame."""
    scene = bpy.context.scene
    report = {}
    for semantic, entry in clips.items():
        if not entry['loop']:
            continue
        action = bpy.data.actions[semantic]
        bc.clear_pose(rig)
        bc.bind_action(rig, action)
        first, last = entry['frames']
        scene.frame_set(first)
        bpy.context.view_layer.update()
        target = {b.name: (b.location.copy(), b.rotation_quaternion.copy()) for b in rig.pose.bones}
        n = min(frames, last - first)
        for k in range(1, n + 1):
            f = last - n + k
            w = k / n  # 0 -> 1 across the tail, reaching the first pose exactly at `last`
            scene.frame_set(f)
            bpy.context.view_layer.update()
            for b in rig.pose.bones:
                loc, rot = target[b.name]
                b.location = b.location.lerp(loc, w)
                b.rotation_quaternion = b.rotation_quaternion.slerp(rot, w)
                b.keyframe_insert('location', frame=f)
                b.keyframe_insert('rotation_quaternion', frame=f)
        rig.animation_data.action = None
        report[semantic] = {'frames': n}
    bc.clear_pose(rig)
    return report


def death_hold(rig, seconds, entry):
    """Append `seconds` of the final pose to Death so the body holds still on the ground."""
    scene = bpy.context.scene
    action = bpy.data.actions['Death']
    bc.clear_pose(rig)
    bc.bind_action(rig, action)
    first, last = entry['frames']
    extra = int(round(seconds * FPS))
    scene.frame_set(last)
    bpy.context.view_layer.update()
    pose = {b.name: (b.location.copy(), b.rotation_quaternion.copy(), b.scale.copy()) for b in rig.pose.bones}
    for f in range(last + 1, last + extra + 1):
        scene.frame_set(f)
        for b in rig.pose.bones:
            loc, rot, scl = pose[b.name]
            b.location, b.rotation_quaternion, b.scale = loc, rot, scl
            for prop in ('location', 'rotation_quaternion', 'scale'):
                b.keyframe_insert(prop, frame=f)
    rig.animation_data.action = None
    bc.clear_pose(rig)
    entry['frames'] = [first, last + extra]
    entry['durationSeconds'] = (last + extra - first) / FPS
    return {'heldFrames': extra}


def ground_clamp(rig, body_bone, body, floor, clips, exclude_prefixes=(), periodic_loops=False):
    """Per-frame hip lift so the lowest deforming vertex of `body` never goes below `floor`.

    Raw offsets are smoothed with a short window and merged back with an element-wise
    maximum, so the lift never dips under what a frame needs (no residual penetration)."""
    scene = bpy.context.scene
    report = {}
    to_local = body_bone.bone.matrix_local.to_3x3().inverted() @ rig.matrix_world.to_3x3().inverted()
    excluded = set()
    if exclude_prefixes:
        groups = {g.index for g in body.vertex_groups if g.name.startswith(tuple(exclude_prefixes))}
        excluded = {v.index for v in body.data.vertices if any(g.group in groups and g.weight > 0.5 for g in v.groups)}
    keep = [i for i in range(len(body.data.vertices)) if i not in excluded]
    for semantic, entry in clips.items():
        action = bpy.data.actions[semantic]
        bc.clear_pose(rig)
        bc.bind_action(rig, action)
        first, last = entry['frames']
        raw = []
        for f in range(first, last + 1):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            world = bc.evaluated_world_vertices(body)
            low = min(world[i].z for i in keep)
            raw.append(max(0.0, floor - low))
        n = len(raw)
        window = 2
        smooth = []
        for i in range(n):
            if entry['loop']:
                idx = [(loop_frame_index(i + k, n) if periodic_loops else (i + k) % n) for k in range(-window, window + 1)]
            else:
                idx = [min(n - 1, max(0, i + k)) for k in range(-window, window + 1)]
            smooth.append(max(raw[i], sum(raw[j] for j in idx) / len(idx)))
        for i, f in enumerate(range(first, last + 1)):
            if smooth[i] <= 0.0:
                continue
            scene.frame_set(f)
            bpy.context.view_layer.update()
            body_bone.location = body_bone.location + (to_local @ Vector((0.0, 0.0, smooth[i])))
            body_bone.keyframe_insert('location', frame=f)
        report[semantic] = {'maxLiftUnits': max(smooth), 'meanLiftUnits': sum(smooth) / n, 'framesLifted': sum(1 for v in smooth if v > 0)}
        rig.animation_data.action = None
    bc.clear_pose(rig)
    return report


def extract_contacts(feet, calibration, forward, height, frames):
    contacts = []
    speeds = []
    for leg in calibration['legs']:
        tip = leg['tip']
        zs = [feet[f][tip].z for f in range(frames)]
        low = min(zs)
        planted = [z <= low + 0.03 * height for z in zs]
        # a foot is planted while it is low AND rides the treadmill: frames where it still slides in
        # (heel strike) or peels off (toe-off) move at a different rate and are not contacts
        along = [0.0] + [-(feet[f][tip] - feet[f - 1][tip]).dot(forward) * FPS for f in range(1, frames)]
        stance = sorted(along[f] for f in range(1, frames) if planted[f] and planted[f - 1])
        if stance:
            med = stance[len(stance) // 2]
            band = max(0.35 * abs(med), 0.02 * height)
            refined = [planted[f] and (f == 0 or abs(along[f] - med) <= band) and (f == frames - 1 or abs(along[f + 1] - med) <= band)
                       for f in range(frames)]
            if sum(refined) >= 0.5 * sum(planted):
                planted = refined
        start = next((f for f in range(frames) if planted[f] and (f == 0 or not planted[f - 1])), 0)
        for f in range(frames):
            phase = ((f - start) % (frames - 1)) / (frames - 1)
            contacts.append({'frame': f + 1, 'leg': leg['id'], 'foot': tip, 'planted': planted[f], 'phase': phase,
                             'target': list(feet[f][tip])})
            if f > 0 and planted[f] and planted[f - 1]:
                along_step = (feet[f][tip] - feet[f - 1][tip]).dot(forward)
                speeds.append(-along_step * FPS)
    speeds.sort()
    speed = speeds[len(speeds) // 2] if speeds else 0.0
    return contacts, max(speed, 0.0)


if __name__ == '__main__':
    main()
