"""Export an action package: one FBX per required clip plus one multi-take production FBX, with a hashed manifest.

Usage (Blender):
  Blender --background --factory-startup --python-exit-code 1 --python export_fbx.py -- \
      --contract <rig-contract.json> --input <Actions.blend | multi-take.fbx> --output <exports dir> [--receipt receipt.json]

The input may be an authored/packaged Actions .blend or an FBX that already carries
the clips as takes (an engine-installed production FBX). FBX takes import as
"<Armature>|<Take>"; the take part is matched against the contract's required clips.
The manifest records nominal speeds from the receipt when one exists; without a receipt
(reviewing a foreign asset) the manifest says `receipt: null` and the review cannot
measure planted-sole drift.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import blender_common as bc  # noqa: E402
import contract as contract_module  # noqa: E402

FPS = 30


def normalize_weights(meshes) -> float:
    worst = 0.0
    for mesh in meshes:
        for v in mesh.data.vertices:
            total = sum(g.weight for g in v.groups)
            if total <= 0:
                raise RuntimeError(f'{mesh.name} vertex {v.index} has no skin weight')
            worst = max(worst, abs(total - 1))
            if abs(total - 1) > 1e-5:
                for g in v.groups:
                    mesh.vertex_groups[g.group].add([v.index], g.weight / total, 'REPLACE')
    return worst


def match_actions(required: list[str]) -> dict[str, bpy.types.Action]:
    """Map each required clip to an action by exact name or by the take part of "<Rig>|<Take>"."""
    by_name = {a.name: a for a in bpy.data.actions}
    matched = {}
    for clip in required:
        candidates = [a for name, a in by_name.items() if name == clip or name.split('|')[-1] == clip]
        if len(candidates) != 1:
            raise RuntimeError(f'{clip}: expected one matching action, found {[a.name for a in candidates]} '
                               f'among {sorted(by_name)}')
        matched[clip] = candidates[0]
    extra = sorted(set(by_name) - {a.name for a in matched.values()})
    if extra:
        print(json.dumps({'warning': 'actions not in contract are ignored', 'actions': extra}))
    return matched


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if args.output.exists():
        raise RuntimeError(f'Refusing to overwrite exports {args.output}')
    row = contract_module.load(args.contract)
    required = list(row['requiredClips'])
    args.output.mkdir(parents=True)
    bc.load_source(args.input, use_anim=True)
    rig = bc.find_rig()
    meshes = bc.deforming_meshes(rig)
    rigid = bc.rigid_meshes(rig)
    objects = [rig, *meshes, *rigid]
    if any(b.constraints for b in rig.pose.bones):
        raise RuntimeError('Unbaked constraints in candidate')
    worst = normalize_weights(meshes)
    actions = match_actions(required)
    for clip, action in actions.items():
        if action.name != clip:
            action.name = clip
        action.use_fake_user = True
    receipt = json.loads(args.receipt.read_text()) if args.receipt and args.receipt.exists() else None
    scene = bpy.context.scene
    scene.render.fps = FPS
    manifest = {'schemaVersion': 1, 'subject': row['subjectId'], 'folder': row['folder'],
                'source': args.input.as_posix(), 'sourceSha256': bc.sha256(args.input), 'fps': FPS,
                'rootBone': row['calibration']['root'],
                'receipt': args.receipt.as_posix() if receipt is not None else None,
                'weightNormalizationCorrection': worst, 'objects': [o.name for o in objects],
                'productionInstalled': False, 'operatorAccepted': False, 'clips': []}
    # Independent single-action exports for reimport review.
    for name in required:
        action = actions[name]
        bc.clear_pose(rig)
        bc.bind_action(rig, action)
        first, last = map(int, action.frame_range)
        scene.frame_start, scene.frame_end = first, last
        scene.frame_set(first)
        target = args.output / f"{row['folder']}_{name}.fbx"
        bc.export_fbx(target, objects, bake_anim_use_nla_strips=False, path_mode='ABSOLUTE')
        clip = (receipt or {}).get('clips', {}).get(name, {})
        manifest['clips'].append({
            'name': name, 'contractSemantic': name, 'file': target.name, 'sha256': bc.sha256(target),
            'frameRange': [first, last], 'durationSeconds': (last - first) / FPS,
            'loop': name in contract_module.LOOPING_SEMANTICS, 'holdFinalPose': name == 'Death',
            'visualContactNormalizedTime': clip.get('visualContactNormalizedTime'),
            'nominalSpeedUnitsPerSecond': clip.get('nominalSpeedUnitsPerSecond'),
            'nominalSpeedBodyHeightsPerSecond': clip.get('nominalSpeedBodyHeightsPerSecond'),
            'gait': clip.get('gait'),
        })
    # Production multi-take export: exactly the contract clips as NLA strips.
    rig.animation_data.action = None
    for track in list(rig.animation_data.nla_tracks):
        rig.animation_data.nla_tracks.remove(track)
    for name in required:
        action = actions[name]
        track = rig.animation_data.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, int(action.frame_range[0]), action)
        strip.name = name
        strip.extrapolation = 'NOTHING'
        strip.blend_type = 'REPLACE'
    scene.frame_start = 1
    scene.frame_end = max(int(actions[n].frame_range[1]) for n in required)
    scene.frame_set(1)
    bc.clear_pose(rig)
    production = args.output / f"{row['subjectId']}.fbx"
    bc.export_fbx(production, objects, bake_anim_use_nla_strips=True)
    manifest['production'] = {'file': production.name, 'sha256': bc.sha256(production),
                              'takes': required, 'engineClipNames': required}
    bc.write_json(args.output / 'animation-manifest.json', manifest)
    print(json.dumps({'subject': row['subjectId'], 'production': manifest['production'],
                      'clips': [(c['name'], c['frameRange']) for c in manifest['clips']]}))


if __name__ == '__main__':
    main()
