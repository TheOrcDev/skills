"""Load and validate a subject's rig-contract.json (pure Python, no Blender).

The contract is the only authority for what a subject must have: family, engine
rig type, required clips, rigid parts and their sockets, gameplay move speed,
budgets. Tooling reads it; tooling never redefines it.
"""
from __future__ import annotations

import json
from pathlib import Path

import calibration as cal

SEMANTIC_CLIPS = ('Idle', 'Locomotion', 'BasicAttack', 'Cast', 'Hit', 'Death')
LOOPING_SEMANTICS = ('Idle', 'Locomotion')
ENGINE_RIGS = ('Generic', 'Humanoid')
SCHEMA_VERSION = 1


def folder_name(display_name: str) -> str:
    return ''.join(display_name.split(' '))


def load(path: Path) -> dict:
    path = Path(path)
    row = json.loads(path.read_text())
    errors = validate(row)
    if errors:
        raise ValueError(f'{path}: ' + '; '.join(errors))
    row = dict(row)
    row['contractPath'] = path.resolve().as_posix()
    row['folder'] = row.get('folder') or folder_name(row['displayName'])
    base = path.resolve().parent
    source = dict(row.get('source', {}))
    if source.get('model'):
        source['model'] = (base / source['model']).resolve().as_posix() if not Path(source['model']).is_absolute() else source['model']
    if source.get('textures'):
        source['textures'] = (base / source['textures']).resolve().as_posix() if not Path(source['textures']).is_absolute() else source['textures']
    row['source'] = source
    row['calibration'] = cal.resolve(row['family'], row.get('calibration'), row['subjectId'])
    rigid = [part['object'] for part in row.get('rigidParts', [])]
    row['calibration']['rigid'] = rigid
    return row


def validate(row: dict) -> list[str]:
    errors = []
    for key in ('subjectId', 'displayName', 'family', 'engineRig', 'requiredClips'):
        if key not in row:
            errors.append(f'missing {key}')
    if errors:
        return errors
    if row.get('schemaVersion', SCHEMA_VERSION) != SCHEMA_VERSION:
        errors.append(f"schemaVersion {row.get('schemaVersion')} is not {SCHEMA_VERSION}")
    if row['family'] not in cal.FAMILIES:
        errors.append(f"unknown family {row['family']!r} (choose from {sorted(cal.FAMILIES)})")
    if row['engineRig'] not in ENGINE_RIGS:
        errors.append(f"engineRig must be one of {ENGINE_RIGS}")
    clips = row['requiredClips']
    unknown = [c for c in clips if c not in SEMANTIC_CLIPS]
    if unknown:
        errors.append(f'unknown clips {unknown}; semantic clips are {SEMANTIC_CLIPS}')
    if len(set(clips)) != len(clips):
        errors.append('duplicate clips')
    for part in row.get('rigidParts', []):
        if 'object' not in part or 'bone' not in part:
            errors.append(f'rigid part needs object and bone: {part}')
        grip = part.get('grip')
        if grip is not None:
            if not (0.0 <= float(grip.get('fraction', -1)) <= 1.0):
                errors.append(f"grip fraction for {part.get('object')} must be within 0..1")
            if grip.get('direction') not in ('up', 'down'):
                errors.append(f"grip direction for {part.get('object')} must be up or down")
    speed = row.get('moveSpeedUnitsPerSecond')
    if speed is not None and not (isinstance(speed, (int, float)) and speed >= 0):
        errors.append('moveSpeedUnitsPerSecond must be a non-negative number')
    return errors


def describe(row: dict) -> dict:
    calibration = row['calibration']
    return {
        'subjectId': row['subjectId'], 'family': row['family'], 'engineRig': row['engineRig'],
        'requiredClips': row['requiredClips'], 'mode': calibration['mode'],
        'requiredBones': cal.referenced_bones(calibration),
        'rigidParts': row.get('rigidParts', []),
        'moveSpeedUnitsPerSecond': row.get('moveSpeedUnitsPerSecond'),
    }


if __name__ == '__main__':
    import sys
    print(json.dumps(describe(load(Path(sys.argv[1]))), indent=2))
