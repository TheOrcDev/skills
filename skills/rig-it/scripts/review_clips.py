"""Evaluate and render an action package from freshly imported exports, then run the gates.

Usage (Blender):
  Blender --background --factory-startup --python-exit-code 1 --python review_clips.py -- \
      --contract <rig-contract.json> --exports <exports dir> --output <evidence dir> \
      [--receipt receipt.json] [--render all|keys|none] [--view three-quarter|front|side] [--render-clip Idle ...]

Every clip is imported from its own exported FBX into an empty scene, every
frame is evaluated on real vertices and bones, and renders use that reimported
data (never an unsaved working pose). Locomotion is measured while the actor
travels at its nominal speed over a visible floor. The final JSON line carries
the gate `failures` list; an empty list is a technical pass, not art acceptance.
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
import contract as contract_module  # noqa: E402
import gates  # noqa: E402
from render_previews import configure_scene, aim_camera  # noqa: E402

FPS = 30
UP = Vector((0, 0, 1))


def region_ids(rest: list[Vector], core: list[int], forward: Vector, height: float, floor: float) -> dict[str, list[int]]:
    along = {i: rest[i].dot(forward) for i in core}
    lo, hi = min(along.values()), max(along.values())
    span = max(hi - lo, 1e-6)
    upper = [i for i in core if (rest[i].z - floor) / height > 0.55]
    regions = {'front': [], 'mid': [], 'rear': []}
    for i in upper:
        f = (along[i] - lo) / span
        regions['front' if f > 0.66 else 'rear' if f < 0.33 else 'mid'].append(i)
    return {k: v for k, v in regions.items() if len(v) >= 8}


def add_floor(ground: float, size: float, cell: float) -> None:
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, ground))
    plane = bpy.context.active_object
    plane.name = 'ReviewFloor'
    material = bpy.data.materials.new('ReviewFloor')
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes['Principled BSDF']
    checker = nodes.new('ShaderNodeTexChecker')
    checker.inputs['Scale'].default_value = 1.0 / cell
    checker.inputs['Color1'].default_value = (0.32, 0.33, 0.35, 1)
    checker.inputs['Color2'].default_value = (0.2, 0.21, 0.23, 1)
    coords = nodes.new('ShaderNodeTexCoord')
    links.new(coords.outputs['Object'], checker.inputs['Vector'])
    links.new(checker.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.9
    plane.data.materials.append(material)


def relink_textures(folder: Path | None) -> None:
    available = {p.name.lower(): p for p in folder.glob('*') if p.is_file()} if folder and folder.is_dir() else {}
    for image in bpy.data.images:
        candidate = available.get(Path(image.filepath).name.lower()) or available.get(image.name.lower())
        if candidate is None:
            for path in available.values():
                if path.stem.lower() == Path(image.name).stem.lower():
                    candidate = path
                    break
        if candidate is not None:
            image.filepath = str(candidate.resolve())
            image.reload()
    # Images with no file on disk would render magenta; disconnect their nodes so the
    # remaining textures show the real surface.
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        for node in list(material.node_tree.nodes):
            if node.type == 'TEX_IMAGE' and (node.image is None or node.image.size[0] == 0):
                for output in node.outputs:
                    for link in list(output.links):
                        socket = link.to_socket
                        material.node_tree.links.remove(link)
                        if 'Emission' in socket.name and hasattr(socket, 'default_value'):
                            try:
                                socket.default_value = (0.0, 0.0, 0.0, 1.0) if len(socket.default_value) == 4 else 0.0
                            except (TypeError, AttributeError):
                                pass


def guess_forward(rig: bpy.types.Object, calibration: dict) -> Vector:
    """Without a receipt, forward runs from the body bone toward the head bone, flattened to the floor."""
    body = rig.matrix_world @ rig.data.bones[calibration['body']].head_local
    head = rig.matrix_world @ rig.data.bones[calibration['head']].head_local
    forward = head - body
    forward.z = 0.0
    if forward.length < 1e-6:
        forward = Vector((0, 1, 0))
    return forward.normalized()


def weapon_bones(rig: bpy.types.Object, calibration: dict) -> list[str]:
    weapon = []
    jaw = calibration.get('jaw')
    if not jaw and 'Jaw' in rig.pose.bones:
        jaw = 'Jaw'  # authored at runtime for rigs that had no jaw
    if isinstance(jaw, dict):
        weapon += [jaw['lower'], jaw['upper']]
    elif jaw:
        weapon.append(jaw)
    weapon += calibration.get('mandibles', []) + calibration.get('fangs', [])
    return [n for n in weapon if n in rig.pose.bones]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--exports', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--render', default='all', choices=['all', 'keys', 'none'])
    parser.add_argument('--resolution', type=int, default=640)
    parser.add_argument('--view', choices=['three-quarter', 'front', 'side'], default='three-quarter')
    parser.add_argument('--render-clip', action='append', choices=contract_module.SEMANTIC_CLIPS,
                        help='Render only selected clips; still evaluate every manifest clip.')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    row = contract_module.load(args.contract)
    calibration = row['calibration']
    receipt = json.loads(args.receipt.read_text()) if args.receipt and args.receipt.exists() else {}
    manifest = json.loads((args.exports / 'animation-manifest.json').read_text())
    if args.render_clip and not set(args.render_clip).issubset({entry['name'] for entry in manifest['clips']}):
        raise RuntimeError('Requested render clip is absent from manifest')
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'schemaVersion': 1, 'subject': row['subjectId'], 'exports': args.exports.as_posix(),
              'receipt': args.receipt.as_posix() if receipt else None,
              'renderedClipSelection': args.render_clip, 'renderMode': args.render, 'view': args.view,
              'manifestProductionSha256': manifest['production']['sha256'], 'clips': {}}
    anchor = receipt.get('anchorOffset', calibration.get('anchorOffset', 0.0))
    texture_folder = Path(row['source']['textures']) if row['source'].get('textures') else None
    for entry in manifest['clips']:
        name = entry['name']
        path = args.exports / entry['file']
        if bc.sha256(path) != entry['sha256']:
            raise RuntimeError(f'{path} hash does not match manifest')
        bc.load_source(path, use_anim=True)
        relink_textures(texture_folder)
        rig = bc.find_rig()
        mesh = bc.main_mesh(rig)
        actions = list(bpy.data.actions)
        if len(actions) != 1:
            raise RuntimeError(f'{name}: expected one imported action, found {[a.name for a in actions]}')
        action = actions[0]
        bc.clear_pose(rig)
        forward = Vector(receipt['forward']) if receipt.get('forward') else guess_forward(rig, calibration)
        report.setdefault('forward', list(forward))
        rest = bc.rest_world_vertices(mesh)
        floor = min(v.z for v in rest)
        # Airborne subjects hover above the real ground by the runtime anchor offset; their
        # penetration reference is that ground, not the model's local floor.
        ground = floor - anchor if calibration['mode'] == 'air' else floor
        core_names = set(calibration['coreGroups']) | {calibration['body']}
        core = [v.index for v in mesh.data.vertices if bc.dominant_group(mesh, v) in core_names]
        if not core:
            raise RuntimeError(f'{name}: no vertices are dominated by the core groups {sorted(core_names)}')
        height = max(rest[i].z for i in core) - floor
        regions = region_ids(rest, core, forward, height, floor)
        body = rig.pose.bones[calibration['body']]
        body_rest = rig.matrix_world @ body.bone.matrix_local
        bc.bind_action(rig, action)
        first, last = map(int, action.frame_range)
        expected = entry['frameRange']
        offset = first - expected[0]
        if (last - first) != (expected[1] - expected[0]):
            raise RuntimeError(f'{name}: imported duration {last - first} != exported {expected[1] - expected[0]}')
        scene = bpy.context.scene
        scene.render.fps = FPS
        speed = entry.get('nominalSpeedUnitsPerSecond') or 0.0
        rows = []
        history = []
        first_world = None
        previous = None
        max_motion = 0.0
        wing_tips = [w['fingers'][0] for w in calibration.get('wings', []) if w['fingers'][0] in rig.pose.bones]
        weapon = weapon_bones(rig, calibration)
        tips = [leg['tip'] for leg in calibration['legs']]
        soles = {}
        for leg in calibration['legs']:
            ankle_z = (rig.matrix_world @ rig.data.bones[leg['ik']].tail_local).z + height * 0.02
            # a robed body weights its hem to the foot bones too; subjects can raise the weight a sole vertex needs
            sole_threshold = calibration.get('soleWeightThreshold', 0.05)
            ids = bc.sole_vertices(mesh, leg['sole'], max_z=ankle_z, threshold=sole_threshold) or bc.sole_vertices(mesh, leg['sole'], threshold=sole_threshold)
            if ids:
                soles[leg['tip']] = ids
        feet_plane = min((rest[i].z for ids in soles.values() for i in ids), default=floor) if calibration['mode'] == 'ground' else floor
        # a vertex may sink to the feet plane, or to its own rest depth if the source already hangs lower
        allowed = [min(feet_plane, v.z) if calibration['mode'] == 'ground' else ground for v in rest]
        root_bone = rig.pose.bones[calibration['root']]
        for frame in range(first, last + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            world = bc.evaluated_world_vertices(mesh)
            if first_world is None:
                first_world = [v.copy() for v in world]
            history.append(world)
            max_motion = max(max_motion, max((a - b).length / height for a, b in zip(world, first_world)))
            aligned_matrix = body_rest @ (rig.matrix_world @ body.matrix).inverted()
            aligned = [aligned_matrix @ v for v in world]
            travel = forward * (speed * (frame - first) / FPS)
            row_ = {
                'frame': frame - offset,
                'floorPenetration': max(0.0, max(allowed[i] - v.z for i, v in enumerate(world)) / height),
                'lowestVertexZ': min(v.z for v in world),
                'drop': {n: max((rest[i].z - aligned[i].z) / height for i in ids) for n, ids in regions.items()},
                'coreCenterZ': sum(world[i].z for i in core) / len(core),
                'feet': {n: list(bc.bone_world_head(rig, n) + travel) for n in tips},
                'soles': {n: list(sum((world[i] for i in ids), Vector()) / len(ids) + travel) for n, ids in soles.items()},
                'soleLowest': {n: min(world[i].z for i in ids) for n, ids in soles.items()},
                'rootLocation': list(root_bone.location),
                'rootRotation': list(root_bone.rotation_quaternion),
                'bodyScale': list(body.scale),
                'bodyZ': (rig.matrix_world @ body.head).z,
                'bodyRotationAngle': (body_rest.to_3x3().inverted() @ (rig.matrix_world @ body.matrix).to_3x3()).to_quaternion().angle,
                'weaponAngles': {n: rig.pose.bones[n].rotation_quaternion.angle for n in weapon},
                'wingTipZ': {n: (rig.matrix_world @ rig.pose.bones[n].tail).z for n in wing_tips},
                'meanDisplacement': sum((a - b).length for a, b in zip(world, first_world)) / len(world) / height,
            }
            rows.append(row_)
            previous = world
        loop_seam = max((a - b).length / height for a, b in zip(previous, first_world))
        velocity_seam = None
        seam_ratio = None
        if len(history) >= 4:
            velocities = [[(b - a) for a, b in zip(history[k], history[k + 1])] for k in range(len(history) - 1)]
            interior = 0.0
            for k in range(1, len(velocities)):
                interior = max(interior, max((a - b).length for a, b in zip(velocities[k], velocities[k - 1])))
            seam = max((a - b).length for a, b in zip(velocities[0], velocities[-1]))
            velocity_seam = seam / height
            seam_ratio = seam / interior if interior > 1e-9 else 0.0
        tail_frames = max(2, int(len(rows) * 0.2))
        clip_report = {
            'range': [first, last], 'importedFrameOffset': offset, 'frames': len(rows),
            'maxFloorPenetration': max(r['floorPenetration'] for r in rows),
            'maxVertexMotion': max_motion, 'loopSeam': loop_seam, 'velocitySeam': velocity_seam,
            'seamAccelerationRatio': seam_ratio,
            'maxDrop': {n: max(r['drop'][n] for r in rows) for n in regions},
            'rootStationary': all(max(abs(x) for x in r['rootLocation']) < 1e-6 and abs(r['rootRotation'][0] - 1) < 1e-6 for r in rows),
            'bodyScaleUnit': all(max(abs(x - 1) for x in r['bodyScale']) < 1e-5 for r in rows),
            'finalCoreDrop': (rows[0]['coreCenterZ'] - rows[-1]['coreCenterZ']) / height,
            'finalBodyRotationAngle': rows[-1]['bodyRotationAngle'],
            'restCoreHeight': (rows[0]['coreCenterZ'] - floor) / height,
            'settleMotion': max(abs(rows[-1]['coreCenterZ'] - r['coreCenterZ']) / height for r in rows[-tail_frames:]),
            'maxWeaponAngle': {n: max(r['weaponAngles'][n] for r in rows) for n in weapon},
            'finalWeaponAngle': {n: rows[-1]['weaponAngles'][n] for n in weapon},
            'wingTipRange': {n: (max(r['wingTipZ'][n] for r in rows) - min(r['wingTipZ'][n] for r in rows)) / height for n in wing_tips},
            'finalWingTipHeight': {n: (rows[-1]['wingTipZ'][n] - ground) / height for n in wing_tips},
            'finalWingMotion': {n: (max(r['wingTipZ'][n] for r in rows[-tail_frames:]) - min(r['wingTipZ'][n] for r in rows[-tail_frames:])) / height for n in wing_tips},
            'bodyAltitude': {'min': min(r['bodyZ'] for r in rows), 'max': max(r['bodyZ'] for r in rows),
                             'rest': body_rest.translation.z},
            'meanDisplacement': [round(r['meanDisplacement'], 5) for r in rows],
            'samples': rows,
        }
        contacts = receipt.get('clips', {}).get(name, {}).get('contacts', [])
        if name == 'Locomotion' and contacts:
            by_frame = {r['frame']: r for r in rows}
            drift = {}
            for key in ('soles', 'feet'):
                state = {}
                worst = 0.0
                for contact in contacts:
                    foot = contact['foot']
                    position = Vector(by_frame[contact['frame']][key][foot])
                    if not contact['planted']:
                        state.pop(foot, None)
                        continue
                    prior = state.get(foot)
                    if prior is None or contact['phase'] < prior[0]:
                        state[foot] = (contact['phase'], position)
                    else:
                        worst = max(worst, (position - prior[1]).length / height)
                drift[key] = worst
            clip_report['stanceDriftBodyHeights'] = drift['soles']
            clip_report['ankleDriftBodyHeights'] = drift['feet']
            clip_report['plantedSoleClearance'] = max(
                (by_frame[c['frame']]['soleLowest'][c['foot']] - floor) / height for c in contacts if c['planted'])
            clip_report['swingSoleClearance'] = max(
                (by_frame[c['frame']]['soleLowest'][c['foot']] - floor) / height for c in contacts if not c['planted'])
            clip_report['travelSpeedUnitsPerSecond'] = speed
        elif name == 'Locomotion':
            clip_report['contactEvidence'] = 'none: no receipt contacts, planted-sole drift cannot be measured'
        report['clips'][name] = clip_report
        report['height'] = height
        report['floor'] = floor
        report['ground'] = ground
        if args.render == 'none' or (args.render_clip and name not in args.render_clip):
            continue
        # ----- render from the reimported data -----
        minimum = Vector(tuple(min(v[a] for v in rest) for a in range(3)))
        maximum = Vector(tuple(max(v[a] for v in rest) for a in range(3)))
        span = max(maximum - minimum)
        add_floor(floor - anchor, span * 40, height * 0.25)
        camera = configure_scene(args.resolution, 'source', minimum, maximum, 0.15, 0.03)
        direction = (Vector((1, 0, 0)) * 0.85 + forward * 0.5 + UP * 0.38).normalized()
        if args.view == 'front':
            direction = (forward + UP * 0.15).normalized()
        elif args.view == 'side':
            side = forward.cross(UP)
            direction = (side + UP * 0.15).normalized()
        center = (minimum + maximum) * 0.5
        center.z = (floor - anchor + maximum.z) * 0.5
        aim_camera(camera, center, minimum, maximum, direction)
        camera.data.ortho_scale = max(span, height * 2.2, maximum.z - (floor - anchor) + height * 0.6) * 1.12
        travel_parent = bpy.data.objects.new('TravelCamera', None)
        scene.collection.objects.link(travel_parent)
        camera.parent = travel_parent
        rig_parent = bpy.data.objects.new('TravelRig', None)
        scene.collection.objects.link(rig_parent)
        for obj in (rig, *bc.deforming_meshes(rig), *bc.rigid_meshes(rig)):
            if obj.parent is None:
                obj.parent = rig_parent
        directory = args.output / 'frames' / name
        directory.mkdir(parents=True, exist_ok=True)
        frames = range(first, last + 1) if args.render == 'all' else sorted({first, round(first + (last - first) * 0.3), round(first + (last - first) * 0.6), last})
        for frame in frames:
            scene.frame_set(frame)
            travel = forward * (speed * (frame - first) / FPS)
            rig_parent.location = travel
            travel_parent.location = travel
            scene.render.filepath = str((directory / f'frame-{frame - offset:03}.png').resolve())
            bpy.ops.render.render(write_still=True)
    failures = gates.evaluate(report, mode=calibration['mode'], required=row['requiredClips'])
    report['gateFailures'] = failures
    report['technicalPass'] = not failures
    bc.write_json(args.output / 'review.json', report)
    summary = {n: {k: v for k, v in r.items() if k not in ('samples', 'meanDisplacement')} for n, r in report['clips'].items()}
    # one line so pipeline.py can pick it up as the script's result
    print(json.dumps({'subject': row['subjectId'], 'clips': summary, 'failures': failures,
                      'technicalPass': not failures, 'review': (args.output / 'review.json').as_posix()}))


if __name__ == '__main__':
    main()
