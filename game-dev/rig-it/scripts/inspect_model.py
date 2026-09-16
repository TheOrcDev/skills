"""Inspect a model file before rigging or reviewing: hierarchy, bounds, weights, parts, actions.

Usage (Blender):
  Blender --background --factory-startup --python-exit-code 1 --python inspect_model.py -- \
      --input <fbx|glb|blend> --output <report.json> [--contract <rig-contract.json>]

With a contract it also validates the calibration against the rig (missing bones), checks
that every rigid part object exists, and reports which required clips are present.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import calibration as cal  # noqa: E402
import contract as contract_module  # noqa: E402


def load(path: Path) -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    suffix = path.suffix.lower()
    if suffix == '.fbx':
        bpy.ops.import_scene.fbx(filepath=str(path.resolve()), use_anim=True)
    elif suffix in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    elif suffix == '.blend':
        bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
    else:
        raise RuntimeError(f'Unsupported input {path}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--contract', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    load(args.input)
    scene = bpy.context.scene
    rigs = [o for o in scene.objects if o.type == 'ARMATURE']
    meshes = [o for o in scene.objects if o.type == 'MESH']
    info = {'file': args.input.as_posix(), 'sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
            'fps': scene.render.fps,
            'objects': [{'name': o.name, 'type': o.type, 'parent': o.parent.name if o.parent else None,
                         'scale': list(o.scale), 'location': list(o.location)} for o in scene.objects],
            'rigs': [], 'meshes': []}
    for rig in rigs:
        bones = [{'name': b.name, 'parent': b.parent.name if b.parent else None,
                  'head': list(rig.matrix_world @ b.head_local), 'tail': list(rig.matrix_world @ b.tail_local),
                  'deform': b.use_deform} for b in rig.data.bones]
        info['rigs'].append({'name': rig.name, 'scale': list(rig.scale), 'rotation': list(rig.rotation_euler),
                             'boneCount': len(bones), 'bones': bones,
                             'action': rig.animation_data.action.name if rig.animation_data and rig.animation_data.action else None,
                             'nla': [(t.name, [(s.name, s.action.name if s.action else None, s.frame_start, s.frame_end) for s in t.strips])
                                     for t in rig.animation_data.nla_tracks] if rig.animation_data else []})
    everything = []
    for m in meshes:
        world = [m.matrix_world @ v.co for v in m.data.vertices]
        groups = {g.index: g.name for g in m.vertex_groups}
        counts = {}
        unweighted = 0
        for v in m.data.vertices:
            if sum(g.weight for g in v.groups) < 1e-4:
                unweighted += 1
            for g in v.groups:
                if g.weight > 0.01:
                    counts[groups[g.group]] = counts.get(groups[g.group], 0) + 1
        modifiers = [(md.type, getattr(md, 'object', None).name if getattr(md, 'object', None) else None) for md in m.modifiers]
        skinned = any(t == 'ARMATURE' for t, _ in modifiers)
        info['meshes'].append({'name': m.name, 'vertices': len(m.data.vertices), 'faces': len(m.data.polygons),
                               'min': [min(v[i] for v in world) for i in range(3)] if world else None,
                               'max': [max(v[i] for v in world) for i in range(3)] if world else None,
                               'materials': [s.material.name if s.material else None for s in m.material_slots],
                               'modifiers': modifiers, 'skinned': skinned, 'unweighted': unweighted,
                               'groupVertexCounts': counts, 'uvLayers': [u.name for u in m.data.uv_layers],
                               'parent': m.parent.name if m.parent else None})
        everything += world
    if everything:
        info['bounds'] = {'min': [min(v[i] for v in everything) for i in range(3)],
                          'max': [max(v[i] for v in everything) for i in range(3)]}
        extent = [info['bounds']['max'][i] - info['bounds']['min'][i] for i in range(3)]
        info['extent'] = extent
        info['groundedAtZero'] = abs(info['bounds']['min'][2]) < 0.01
    info['actions'] = [{'name': a.name, 'take': a.name.split('|')[-1], 'range': list(a.frame_range), 'fcurves': len(a.fcurves)}
                       for a in bpy.data.actions]
    info['images'] = [(i.name, i.filepath, i.size[0], i.size[1]) for i in bpy.data.images]
    summary = {'file': args.input.name, 'rigs': [(r['name'], r['boneCount']) for r in info['rigs']],
               'meshes': [(m['name'], m['vertices'], 'skinned' if m['skinned'] else 'rigid', f"unweighted={m['unweighted']}") for m in info['meshes']],
               'actions': [a['take'] for a in info['actions']], 'bounds': info.get('bounds')}
    if args.contract:
        row = contract_module.load(args.contract)
        calibration = row['calibration']
        check = {'subject': row['subjectId'], 'family': row['family']}
        if len(rigs) == 1:
            names = {b.name for b in rigs[0].data.bones}
            check['calibrationErrors'] = cal.validate(calibration, names)
            body = rigs[0].data.bones.get(calibration['body'])
            head = rigs[0].data.bones.get(calibration['head'])
            if body and head:
                forward = (rigs[0].matrix_world @ head.head_local) - (rigs[0].matrix_world @ body.head_local)
                forward.z = 0
                check['forwardGuess'] = list(forward.normalized()) if forward.length > 1e-6 else None
        else:
            check['calibrationErrors'] = [f'expected one armature, found {len(rigs)}']
        mesh_names = {m.name for m in meshes}
        parts = [p['object'] for p in row.get('rigidParts', [])]
        check['rigidPartsFound'] = [p for p in parts if p in mesh_names]
        check['rigidPartsMissing'] = [p for p in parts if p not in mesh_names]
        takes = {a['take'] for a in info['actions']}
        check['clipsPresent'] = [c for c in row['requiredClips'] if c in takes]
        check['clipsMissing'] = [c for c in row['requiredClips'] if c not in takes]
        check['skinnedMeshes'] = [m['name'] for m in info['meshes'] if m['skinned']]
        check['unweightedVertices'] = sum(m['unweighted'] for m in info['meshes'] if m['skinned'])
        info['contractCheck'] = check
        summary['contractCheck'] = check
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(info, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
