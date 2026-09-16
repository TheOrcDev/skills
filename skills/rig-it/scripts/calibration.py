"""Family calibration templates for rig-it.

A family template names every bone role the tooling needs (root, body, head,
legs with IK chains and sole groups, wings, jaws, tails) and the default gait,
idle, attack, hit and death timings as fractions of body height. A subject's
`rig-contract.json` picks a family and overrides any field under
`calibration`. Nothing here imports Blender, so it is unit-testable.

Families:
  quadruped, hexapod, octopod, winged-bat, winged-biped, maw-quadruped,
  winged-humanoid, humanoid (25-bone scaffold), mixamo-biped (Meshy/Mixamo).
"""
from __future__ import annotations

import copy

from motion import gait_phases

FPS = 30


def quadruped_legs(prefix: str = 'Leg', foot: str = 'Foot') -> list[dict]:
    legs = []
    for row_id, row in (('F', 'Front'), ('R', 'Rear')):
        for side in ('L', 'R'):
            stem = f'{prefix}_{side}_{row}'
            legs.append({
                'id': f'{row_id}{side}', 'side': side, 'row': row.lower(),
                'chain': [f'{stem}_Upper', f'{stem}_Lower', f'{stem}_{foot}'],
                'ik': f'{stem}_Lower', 'ikChain': 2,
                'tip': f'{stem}_{foot}', 'sole': [f'{stem}_{foot}'],
            })
    return legs


def wing(side: str, chain: list[str], fingers: list[str]) -> dict:
    return {'side': side, 'chain': [name.format(s=side) for name in chain],
            'fingers': [name.format(s=side) for name in fingers]}


EMPTY_ROLES = {'wings': [], 'arms': [], 'antennae': [], 'mandibles': [], 'fangs': [], 'ears': [], 'ridges': [],
               'extra': [], 'rigid': []}

QUADRUPED = {
    'family': 'quadruped', 'mode': 'ground',
    'root': 'Root', 'body': 'Spine', 'head': 'Head', 'neck': [], 'chest': None,
    'jaw': None, 'tail': ['Tail_01', 'Tail_02', 'Tail_03'],
    'coreGroups': ['Root', 'Spine', 'Head'],
    'legs': quadruped_legs(),
    **copy.deepcopy(EMPTY_ROLES),
    'anchorOffset': 0.0,
    'gait': {'type': 'trot', 'cycleSeconds': 0.5, 'duty': 0.45, 'stride': 0.42, 'clearance': 0.12,
             'bounce': 0.03, 'pitch': 0.03, 'roll': 0.0, 'headBob': 0.03, 'tailSwing': 0.12},
    'idle': {'seconds': 2.0, 'breath': 0.006, 'headTurn': 0.06, 'headNod': 0.02, 'tailSwing': 0.05},
    'attack': {'type': 'bite', 'seconds': 0.9, 'contact': 0.4, 'lunge': 0.16, 'gape': 0.5},
    'hit': {'seconds': 0.55, 'recoil': 0.07},
    'death': {'type': 'sideRoll', 'seconds': 1.4, 'roll': 1.35},
    'cast': None,
}

HEXAPOD = {
    'family': 'hexapod', 'mode': 'ground',
    'root': 'Root', 'body': 'Thorax', 'head': 'Head', 'neck': [], 'chest': None,
    'jaw': None, 'tail': ['Abdomen'],
    'coreGroups': ['Root', 'Thorax', 'Abdomen', 'Head'],
    'legs': [
        {'id': 'FL', 'side': 'L', 'row': 'front'}, {'id': 'FR', 'side': 'R', 'row': 'front'},
        {'id': 'ML', 'side': 'L', 'row': 'middle'}, {'id': 'MR', 'side': 'R', 'row': 'middle'},
        {'id': 'RL', 'side': 'L', 'row': 'rear'}, {'id': 'RR', 'side': 'R', 'row': 'rear'},
    ],
    **copy.deepcopy(EMPTY_ROLES),
    'antennae': [['Antenna_L_01', 'Antenna_L_02'], ['Antenna_R_01', 'Antenna_R_02']],
    'mandibles': ['Mandible_L', 'Mandible_R'],
    'anchorOffset': 0.0,
    'gait': {'type': 'tripod', 'cycleSeconds': 0.5, 'duty': 0.55, 'stride': 0.26, 'clearance': 0.14,
             'bounce': 0.012, 'pitch': 0.015, 'roll': 0.0, 'headBob': 0.02, 'tailSwing': 0.05},
    'idle': {'seconds': 2.0, 'breath': 0.005, 'headTurn': 0.05, 'headNod': 0.03, 'tailSwing': 0.04,
             'antennaSway': 0.18, 'mandibleTwitch': 0.08},
    'attack': {'type': 'mandible', 'seconds': 0.8, 'contact': 0.45, 'lunge': 0.14, 'gape': 0.55},
    'hit': {'seconds': 0.5, 'recoil': 0.06},
    'death': {'type': 'curl', 'seconds': 1.3, 'roll': 0.55},
    'cast': None,
}
for leg in HEXAPOD['legs']:
    stem = f"Leg_{leg['side']}_{leg['row'].capitalize()}"
    leg.update({'chain': [f'{stem}_Coxa', f'{stem}_Femur', f'{stem}_Tibia', f'{stem}_Tarsus'],
                'ik': f'{stem}_Tibia', 'ikChain': 3, 'tip': f'{stem}_Tarsus', 'sole': [f'{stem}_Tarsus', f'{stem}_Tibia']})

OCTOPOD = {
    'family': 'octopod', 'mode': 'ground',
    'root': 'Root', 'body': 'Cephalothorax', 'head': 'Head', 'neck': [], 'chest': None,
    'jaw': None, 'tail': ['Abdomen'],
    'coreGroups': ['Root', 'Cephalothorax', 'Abdomen', 'Head'],
    'legs': [],
    **copy.deepcopy(EMPTY_ROLES),
    'fangs': ['Fang_L', 'Fang_R'],
    'anchorOffset': 0.0,
    'gait': {'type': 'tetrapod', 'cycleSeconds': 0.55, 'duty': 0.55, 'stride': 0.24, 'clearance': 0.14,
             'bounce': 0.01, 'pitch': 0.01, 'roll': 0.0, 'headBob': 0.015, 'tailSwing': 0.04},
    'idle': {'seconds': 2.0, 'breath': 0.006, 'headTurn': 0.04, 'headNod': 0.02, 'tailSwing': 0.05,
             'fangTwitch': 0.06},
    'attack': {'type': 'fang', 'seconds': 0.9, 'contact': 0.45, 'lunge': 0.1, 'rear': 0.22},
    'hit': {'seconds': 0.5, 'recoil': 0.06},
    'death': {'type': 'curl', 'seconds': 1.4, 'roll': 0.6},
    'cast': None,
}
for row_id, row in (('1', 'Front'), ('2', 'FrontMiddle'), ('3', 'RearMiddle'), ('4', 'Rear')):
    for side in ('L', 'R'):
        stem = f'Leg_{side}_{row}'
        OCTOPOD['legs'].append({'id': f'{side}{row_id}', 'side': side, 'row': row,
                                'chain': [f'{stem}_Coxa', f'{stem}_Femur', f'{stem}_Tibia', f'{stem}_Tarsus'],
                                'ik': f'{stem}_Tibia', 'ikChain': 3, 'tip': f'{stem}_Tarsus',
                                # bone heat tends to leave outer tarsi unweighted; the tibia tip carries the contact
                                'sole': [f'{stem}_Tarsus', f'{stem}_Tibia']})

WINGED_BAT = {
    'family': 'winged-bat', 'mode': 'air',
    'root': 'Root', 'body': 'Spine', 'head': 'Head', 'neck': [], 'chest': 'Chest',
    'jaw': 'Jaw', 'tail': [],
    'coreGroups': ['Root', 'Spine', 'Chest', 'Head'],
    'legs': [
        {'id': 'L', 'side': 'L', 'row': 'rear', 'chain': ['Leg_L_Upper', 'Leg_L_Lower', 'Leg_L_Foot'],
         'ik': 'Leg_L_Lower', 'ikChain': 2, 'tip': 'Leg_L_Foot', 'sole': ['Leg_L_Foot', 'Leg_L_Lower']},
        {'id': 'R', 'side': 'R', 'row': 'rear', 'chain': ['Leg_R_Upper', 'Leg_R_Lower', 'Leg_R_Foot'],
         'ik': 'Leg_R_Lower', 'ikChain': 2, 'tip': 'Leg_R_Foot', 'sole': ['Leg_R_Foot', 'Leg_R_Lower']},
    ],
    **copy.deepcopy(EMPTY_ROLES),
    'ears': ['Ear_L', 'Ear_R'],
    'wings': [wing('L', ['Wing_{s}_Shoulder', 'Wing_{s}_UpperArm', 'Wing_{s}_Forearm', 'Wing_{s}_Wrist'],
                   ['Wing_{s}_Finger_01', 'Wing_{s}_Finger_02', 'Wing_{s}_Finger_03']),
              wing('R', ['Wing_{s}_Shoulder', 'Wing_{s}_UpperArm', 'Wing_{s}_Forearm', 'Wing_{s}_Wrist'],
                   ['Wing_{s}_Finger_01', 'Wing_{s}_Finger_02', 'Wing_{s}_Finger_03'])],
    'anchorOffset': 0.0,
    'gait': {'type': 'flap', 'cycleSeconds': 0.4, 'flapAmplitude': 0.5, 'flapBias': 0.45, 'lift': 0.05, 'lean': 0.22,
             'legTuck': 0.5, 'headBob': 0.03, 'fold': 0.12},
    'idle': {'seconds': 1.6, 'flapAmplitude': 0.42, 'lift': 0.035, 'headTurn': 0.08, 'earTwitch': 0.12,
             'legTuck': 0.35},
    'attack': {'type': 'swoop', 'seconds': 0.9, 'contact': 0.45, 'lunge': 0.22, 'dive': 0.12, 'gape': 0.5, 'twist': 0.35},
    'hit': {'seconds': 0.55, 'recoil': 0.08, 'dip': 0.06},
    'death': {'type': 'fold', 'seconds': 1.4, 'roll': 0.0, 'headSlump': 0.0, 'legFold': 1.1},
    'cast': None,
}

WINGED_BIPED = {
    'family': 'winged-biped', 'mode': 'air',
    'root': 'Root', 'body': 'Pelvis', 'head': 'Head', 'neck': ['Neck_01', 'Neck_02'], 'chest': 'Chest',
    'spine': 'Spine',
    'jaw': 'Jaw', 'tail': ['Tail_01', 'Tail_02', 'Tail_03', 'Tail_04'],
    'coreGroups': ['Root', 'Pelvis', 'Spine', 'Chest', 'Neck_01', 'Neck_02', 'Head', 'Tail_01'],
    'legs': [
        {'id': 'L', 'side': 'L', 'row': 'rear', 'chain': ['Leg_L_Thigh', 'Leg_L_Shin', 'Leg_L_Foot', 'Leg_L_Toe'],
         'ik': 'Leg_L_Shin', 'ikChain': 2, 'tip': 'Leg_L_Foot', 'sole': ['Leg_L_Foot', 'Leg_L_Toe', 'Leg_L_Shin']},
        {'id': 'R', 'side': 'R', 'row': 'rear', 'chain': ['Leg_R_Thigh', 'Leg_R_Shin', 'Leg_R_Foot', 'Leg_R_Toe'],
         'ik': 'Leg_R_Shin', 'ikChain': 2, 'tip': 'Leg_R_Foot', 'sole': ['Leg_R_Foot', 'Leg_R_Toe', 'Leg_R_Shin']},
    ],
    **copy.deepcopy(EMPTY_ROLES),
    'wings': [wing('L', ['Wing_{s}_Shoulder', 'Wing_{s}_UpperArm', 'Wing_{s}_Forearm', 'Wing_{s}_Wrist'],
                   ['Wing_{s}_Finger_01', 'Wing_{s}_Finger_02', 'Wing_{s}_Finger_03']),
              wing('R', ['Wing_{s}_Shoulder', 'Wing_{s}_UpperArm', 'Wing_{s}_Forearm', 'Wing_{s}_Wrist'],
                   ['Wing_{s}_Finger_01', 'Wing_{s}_Finger_02', 'Wing_{s}_Finger_03'])],
    'anchorOffset': 0.0,
    'gait': {'type': 'flap', 'cycleSeconds': 0.6, 'flapAmplitude': 0.45, 'flapBias': 0.62, 'lift': 0.05, 'lean': 0.16,
             'legTuck': 0.45, 'headBob': 0.02, 'fold': 0.1, 'tailSwing': 0.1},
    'idle': {'seconds': 1.8, 'flapAmplitude': 0.4, 'lift': 0.035, 'headTurn': 0.06, 'legTuck': 0.3,
             'tailSwing': 0.08},
    'attack': {'type': 'swoop', 'seconds': 1.0, 'contact': 0.45, 'lunge': 0.18, 'dive': 0.08, 'gape': 0.55,
               'neckReach': 0.35, 'twist': 0.3},
    'hit': {'seconds': 0.6, 'recoil': 0.07, 'dip': 0.06},
    'death': {'type': 'fold', 'seconds': 1.6, 'roll': 0.6, 'headSlump': 1.6, 'bodyPitch': 0.0},
    'cast': None,
}

MAW_QUADRUPED = {
    'family': 'maw-quadruped', 'mode': 'ground',
    'root': 'Root', 'body': 'Spine', 'head': 'Head', 'neck': ['Neck'], 'chest': 'Chest',
    'jaw': {'lower': 'Jaw_Lower', 'upper': 'Jaw_Upper'}, 'tail': [],
    'coreGroups': ['Root', 'Spine', 'Chest', 'Neck', 'Head'],
    'legs': quadruped_legs(),
    **copy.deepcopy(EMPTY_ROLES),
    'ridges': ['Back_Ridge_01', 'Back_Ridge_02', 'Back_Ridge_03'],
    'anchorOffset': 0.0,
    'gait': {'type': 'walk', 'cycleSeconds': 0.9, 'duty': 0.75, 'stride': 0.14, 'clearance': 0.05, 'crouch': 0.012,
             'bounce': 0.006, 'pitch': 0.005, 'roll': 0.012, 'headBob': 0.0, 'tailSwing': 0.0},
    'idle': {'seconds': 2.2, 'breath': 0.008, 'headTurn': 0.05, 'headNod': 0.025, 'tailSwing': 0.0,
             'jawBreath': 0.06},
    'attack': {'type': 'maw', 'seconds': 1.0, 'contact': 0.45, 'lunge': 0.18, 'gape': 0.6, 'twist': 0.25, 'headDip': 0.2},
    'hit': {'seconds': 0.6, 'recoil': 0.05},
    'death': {'type': 'collapse', 'seconds': 1.7, 'roll': 0.5},
    'cast': {'type': 'roar', 'seconds': 1.4, 'gape': 0.75},
}

WINGED_HUMANOID = {
    'family': 'winged-humanoid', 'mode': 'air',
    'root': 'Root', 'body': 'Pelvis', 'head': 'Head', 'neck': ['Neck'], 'chest': 'Chest', 'spine': 'Spine',
    'jaw': None, 'tail': ['Tail_Feathers_01', 'Tail_Feathers_02'],
    'coreGroups': ['Root', 'Pelvis', 'Spine', 'Chest', 'Neck', 'Head'],
    'legs': [
        {'id': 'L', 'side': 'L', 'row': 'rear', 'chain': ['Leg_L_Thigh', 'Leg_L_Shin', 'Leg_L_Ankle', 'Leg_L_Talon'],
         'ik': 'Leg_L_Shin', 'ikChain': 2, 'tip': 'Leg_L_Ankle', 'sole': ['Leg_L_Ankle', 'Leg_L_Talon', 'Leg_L_Shin']},
        {'id': 'R', 'side': 'R', 'row': 'rear', 'chain': ['Leg_R_Thigh', 'Leg_R_Shin', 'Leg_R_Ankle', 'Leg_R_Talon'],
         'ik': 'Leg_R_Shin', 'ikChain': 2, 'tip': 'Leg_R_Ankle', 'sole': ['Leg_R_Ankle', 'Leg_R_Talon', 'Leg_R_Shin']},
    ],
    **copy.deepcopy(EMPTY_ROLES),
    'wings': [wing('L', ['Wing_{s}_Shoulder', 'Wing_{s}_Upper', 'Wing_{s}_Forearm', 'Wing_{s}_Wrist'],
                   ['Wing_{s}_Primary_01', 'Wing_{s}_Primary_02']),
              wing('R', ['Wing_{s}_Shoulder', 'Wing_{s}_Upper', 'Wing_{s}_Forearm', 'Wing_{s}_Wrist'],
                   ['Wing_{s}_Primary_01', 'Wing_{s}_Primary_02'])],
    'arms': [{'side': 'L', 'chain': ['Arm_L_Clavicle', 'Arm_L_Upper', 'Arm_L_Forearm', 'Arm_L_Hand']},
             {'side': 'R', 'chain': ['Arm_R_Clavicle', 'Arm_R_Upper', 'Arm_R_Forearm', 'Arm_R_Hand']}],
    'anchorOffset': 0.95,
    'gait': {'type': 'flap', 'cycleSeconds': 0.5, 'flapAmplitude': 0.45, 'flapBias': 0.4, 'lift': 0.04, 'lean': 0.2,
             'legTuck': 0.35, 'headBob': 0.02, 'fold': 0.08, 'tailSwing': 0.08, 'armSwing': 0.12},
    'idle': {'seconds': 2.0, 'flapAmplitude': 0.38, 'lift': 0.03, 'headTurn': 0.08, 'legTuck': 0.25,
             'tailSwing': 0.06, 'armSway': 0.08},
    'attack': {'type': 'talon', 'seconds': 1.0, 'contact': 0.45, 'lunge': 0.2, 'dive': 0.1, 'slash': 0.9},
    'hit': {'seconds': 0.6, 'recoil': 0.07, 'dip': 0.06},
    'death': {'type': 'fold', 'seconds': 1.6, 'roll': 0.0},
    'cast': None,
}

# 25-bone Unity-Humanoid-compatible scaffold with hand sockets (scaffold_rig.py builds it).
# Bone names are Unity's own Humanoid names so the Avatar maps with no rename table.
HUMANOID = {
    'family': 'humanoid', 'mode': 'ground',
    'root': 'Root', 'body': 'Hips', 'head': 'Head', 'neck': ['Neck'], 'chest': 'Chest', 'spine': 'Spine',
    'jaw': None, 'tail': [],
    'coreGroups': ['Root', 'Hips', 'Spine', 'Chest', 'UpperChest', 'Neck', 'Head'],
    'legs': [
        {'id': 'L', 'side': 'L', 'row': 'rear', 'chain': ['LeftUpperLeg', 'LeftLowerLeg', 'LeftFoot', 'LeftToes'],
         'ik': 'LeftLowerLeg', 'ikChain': 2, 'tip': 'LeftFoot', 'sole': ['LeftFoot', 'LeftToes']},
        {'id': 'R', 'side': 'R', 'row': 'rear', 'chain': ['RightUpperLeg', 'RightLowerLeg', 'RightFoot', 'RightToes'],
         'ik': 'RightLowerLeg', 'ikChain': 2, 'tip': 'RightFoot', 'sole': ['RightFoot', 'RightToes']},
    ],
    **copy.deepcopy(EMPTY_ROLES),
    'extra': ['UpperChest'],
    'arms': [{'side': 'L', 'chain': ['LeftShoulder', 'LeftUpperArm', 'LeftLowerArm', 'LeftHand']},
             {'side': 'R', 'chain': ['RightShoulder', 'RightUpperArm', 'RightLowerArm', 'RightHand']}],
    'sockets': {'Socket_Hand_L': 'LeftHand', 'Socket_Hand_R': 'RightHand'},
    'anchorOffset': 0.0,
    'gait': {'type': 'biped', 'cycleSeconds': 1.0, 'duty': 0.6, 'stride': 0.3, 'clearance': 0.05,
             'bounce': 0.02, 'pitch': 0.0, 'roll': 0.0, 'headBob': 0.0, 'tailSwing': 0.0, 'armSwing': 0.35},
    'idle': {'seconds': 2.0, 'breath': 0.006, 'headTurn': 0.04, 'headNod': 0.01, 'tailSwing': 0.0, 'armSway': 0.03},
    'attack': {'type': 'swing', 'seconds': 0.9, 'contact': 0.45, 'lunge': 0.06, 'arm': 'R', 'swing': 1.2},
    'hit': {'seconds': 0.55, 'recoil': 0.06},
    'death': {'type': 'collapse', 'seconds': 1.6, 'roll': 0.0},
    'cast': {'type': 'raise', 'seconds': 1.2, 'arm': 'R', 'raise': 1.4},
}

# Meshy / Mixamo skeleton (any Mixamo-template FBX). Reviewed and packaged, not authored, by this tooling.
MIXAMO_BIPED = {
    'family': 'mixamo-biped', 'mode': 'ground',
    'root': 'Root', 'body': 'mixamorig:Hips', 'head': 'mixamorig:Head', 'neck': ['mixamorig:Neck'],
    'chest': 'mixamorig:Spine2', 'spine': 'mixamorig:Spine', 'jaw': None, 'tail': [],
    **copy.deepcopy(EMPTY_ROLES),
    'extra': ['mixamorig:Spine1', 'mixamorig:HeadTop_End', 'mixamorig:HeadTop_End_end',
              'mixamorig:LeftHandMiddle4', 'mixamorig:LeftHandMiddle4_end', 'mixamorig:RightHandMiddle4', 'mixamorig:RightHandMiddle4_end',
              'mixamorig:LeftToe_End', 'mixamorig:LeftToe_End_end', 'mixamorig:RightToe_End', 'mixamorig:RightToe_End_end'],
    'coreGroups': ['Root', 'mixamorig:Hips', 'mixamorig:Spine', 'mixamorig:Spine1', 'mixamorig:Spine2', 'mixamorig:Neck', 'mixamorig:Head'],
    'legs': [
        {'id': 'L', 'side': 'L', 'row': 'rear', 'chain': ['mixamorig:LeftUpLeg', 'mixamorig:LeftLeg', 'mixamorig:LeftFoot', 'mixamorig:LeftToeBase'],
         'ik': 'mixamorig:LeftLeg', 'ikChain': 2, 'tip': 'mixamorig:LeftFoot', 'sole': ['mixamorig:LeftFoot', 'mixamorig:LeftToeBase']},
        {'id': 'R', 'side': 'R', 'row': 'rear', 'chain': ['mixamorig:RightUpLeg', 'mixamorig:RightLeg', 'mixamorig:RightFoot', 'mixamorig:RightToeBase'],
         'ik': 'mixamorig:RightLeg', 'ikChain': 2, 'tip': 'mixamorig:RightFoot', 'sole': ['mixamorig:RightFoot', 'mixamorig:RightToeBase']},
    ],
    'arms': [{'side': 'L', 'chain': ['mixamorig:LeftShoulder', 'mixamorig:LeftArm', 'mixamorig:LeftForeArm', 'mixamorig:LeftHand']},
             {'side': 'R', 'chain': ['mixamorig:RightShoulder', 'mixamorig:RightArm', 'mixamorig:RightForeArm', 'mixamorig:RightHand']}],
    'anchorOffset': 0.0,
    'gait': {'type': 'biped', 'cycleSeconds': 1.0, 'duty': 0.6, 'stride': 0.3, 'clearance': 0.05,
             'bounce': 0.02, 'pitch': 0.0, 'roll': 0.0, 'headBob': 0.0, 'tailSwing': 0.0},
    'idle': {'seconds': 2.0, 'breath': 0.005, 'headTurn': 0.0, 'headNod': 0.0, 'tailSwing': 0.0},
    'attack': {'type': 'preset', 'seconds': 1.0, 'contact': 0.5},
    'hit': {'seconds': 0.6, 'recoil': 0.05},
    'death': {'type': 'collapse', 'seconds': 2.0, 'roll': 0.0},
    'cast': {'type': 'preset', 'seconds': 2.0},
}

FAMILIES: dict[str, dict] = {
    'quadruped': QUADRUPED,
    'hexapod': HEXAPOD,
    'octopod': OCTOPOD,
    'winged-bat': WINGED_BAT,
    'winged-biped': WINGED_BIPED,
    'maw-quadruped': MAW_QUADRUPED,
    'winged-humanoid': WINGED_HUMANOID,
    'humanoid': HUMANOID,
    'mixamo-biped': MIXAMO_BIPED,
}


def merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def resolve(family: str, overrides: dict | None = None, subject_id: str | None = None) -> dict:
    if family not in FAMILIES:
        raise KeyError(f'Unknown family {family!r}; choose one of {sorted(FAMILIES)}')
    calibration = merge(FAMILIES[family], overrides or {})
    calibration['subjectId'] = subject_id
    if calibration['mode'] == 'ground' and calibration['gait'].get('type') in ('trot', 'walk', 'bound', 'biped', 'tripod', 'tetrapod'):
        calibration['gait']['phases'] = calibration['gait'].get('phases') or gait_phases(calibration['gait']['type'])
    return calibration


def referenced_bones(calibration: dict) -> list[str]:
    names = [calibration['root'], calibration['body'], calibration['head']]
    names += calibration.get('neck', [])
    if calibration.get('chest'):
        names.append(calibration['chest'])
    if calibration.get('spine'):
        names.append(calibration['spine'])
    jaw = calibration.get('jaw')
    if isinstance(jaw, dict):
        names += [jaw['lower'], jaw['upper']]
    elif jaw:
        names.append(jaw)
    for key in ('tail', 'ears', 'ridges', 'mandibles', 'fangs', 'extra'):
        names += calibration.get(key, [])
    for chain in calibration.get('antennae', []):
        names += chain
    for leg in calibration['legs']:
        names += leg['chain']
        names += [leg['ik'], leg['tip']] + leg['sole']
    for wing_ in calibration.get('wings', []):
        names += wing_['chain'] + wing_['fingers']
    for arm in calibration.get('arms', []):
        names += arm['chain']
    names += list(calibration.get('sockets', {}).keys())
    seen = []
    for name in names:
        if name not in seen:
            seen.append(name)
    return seen


def validate(calibration: dict, bone_names: set[str]) -> list[str]:
    errors = []
    for name in referenced_bones(calibration):
        if name not in bone_names:
            errors.append(f'missing bone {name}')
    if calibration['mode'] == 'ground':
        gait = calibration['gait']
        phases = gait.get('phases') or gait_phases(gait['type'])
        ids = {leg['id'] for leg in calibration['legs']}
        if set(phases) != ids:
            errors.append(f'gait phases {sorted(phases)} do not cover legs {sorted(ids)}')
        if not 0 < gait['duty'] < 1:
            errors.append('duty out of range')
    else:
        if not calibration.get('wings'):
            errors.append('air mode requires wings')
    return errors
