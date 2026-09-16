"""Export a body-only rest-pose rig input (GLB) for provider auto-rigging (Meshy, Mixamo).

Usage (Blender):
  Blender --background --factory-startup --python-exit-code 1 --python rig_input.py -- \
      --contract <rig-contract.json> --input <production fbx|glb> --output <rig-input.glb> [--exclude Part ...]

Rigid parts (weapons, quivers, shields) are excluded so the provider rigs a
clean biped; they are re-attached to hand bones by package_biped.py after
rigging. Excluded parts default to the contract's `rigidParts`. Any existing
armature, modifiers and vertex groups are dropped from the derived scene only;
the production file is untouched. Textures from the contract's
`source.textures` folder (basecolor/albedo/diffuse and normal) become a
preview material; when none are found the GLB is exported untextured and the
receipt says so.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import contract as contract_module  # noqa: E402

BASECOLOR_KEYS = ('basecolor', 'base_color', 'albedo', 'diffuse')
NORMAL_KEYS = ('normal',)


def find_texture(folder: Path | None, keys: tuple[str, ...]) -> Path | None:
    if folder is None or not folder.is_dir():
        return None
    matches = [p for p in sorted(folder.iterdir()) if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.tga')
               and any(key in p.stem.lower().replace('-', '_') for key in keys)]
    return matches[0] if matches else None


def import_model(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == '.fbx':
        bpy.ops.import_scene.fbx(filepath=str(path.resolve()), use_anim=False)
    elif suffix in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    else:
        raise SystemExit(f'Unsupported input {path}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--exclude', action='append', default=None,
                        help='mesh objects to leave out (default: every rigidParts object in the contract)')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if args.output.exists():
        raise SystemExit('Refusing to overwrite a possibly submitted rig input; use a new versioned path')
    row = contract_module.load(args.contract)
    exclude = args.exclude if args.exclude is not None else [p['object'] for p in row.get('rigidParts', [])]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_model(args.input)
    texture_root = Path(row['source']['textures']) if row.get('source', {}).get('textures') else args.input.parent / 'Textures'
    material = bpy.data.materials.new('RigInput_PreviewOnly')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    shader.inputs['Metallic'].default_value = 0
    shader.inputs['Roughness'].default_value = 0.75
    textures = []
    for semantic, keys in (('basecolor', BASECOLOR_KEYS), ('normal', NORMAL_KEYS)):
        found = find_texture(texture_root, keys)
        if found is None:
            continue
        image = bpy.data.images.load(str(found.resolve()))
        image.colorspace_settings.name = 'sRGB' if semantic == 'basecolor' else 'Non-Color'
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = image
        if semantic == 'basecolor':
            links.new(tex.outputs['Color'], shader.inputs['Base Color'])
        else:
            normal = nodes.new('ShaderNodeNormalMap')
            links.new(tex.outputs['Color'], normal.inputs['Color'])
            links.new(normal.outputs['Normal'], shader.inputs['Normal'])
        textures.append({'semantic': semantic, 'path': found.as_posix(),
                         'sha256': hashlib.sha256(found.read_bytes()).hexdigest()})
    for rig in [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']:
        rig.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    kept, removed = [], []
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH' or obj.name in exclude:
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = matrix
        for modifier in list(obj.modifiers):
            obj.modifiers.remove(modifier)
        obj.vertex_groups.clear()
        obj.data.materials.clear()
        obj.data.materials.append(material)
        kept.append((obj.name, len(obj.data.vertices)))
    if not kept:
        raise SystemExit('No body mesh left after exclusions')
    missing = [name for name in exclude if name not in removed]
    if missing:
        raise SystemExit(f'Excluded parts not found in {args.input.name}: {missing}')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(args.output.resolve()), export_format='GLB', export_animations=False)
    receipt = {'contract': row['contractPath'], 'subject': row['subjectId'],
               'input': args.input.as_posix(), 'inputSha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
               'output': args.output.as_posix(), 'outputSha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
               'kept': kept, 'removed': removed, 'textures': textures,
               'textured': bool(textures),
               'textureNote': None if textures else f'No basecolor/normal texture found under {texture_root}; exported untextured',
               'operation': 'Rest body mesh only; armature, weights and rigid parts removed in the derived scene; no vertex edits',
               'materialScope': 'Rig-input preview only; production materials restored after provider rigging', 'acceptance': False}
    args.output.with_suffix('.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'kept': kept, 'removed': removed, 'textured': bool(textures), 'output': args.output.as_posix()}))


if __name__ == '__main__':
    main()
