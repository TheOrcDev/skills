"""Pure-Python checks for rig-it (no Blender): contract, calibration, motion, gates.

Run: python3 -m unittest discover -s game-dev/rig-it/tests
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import calibration as cal  # noqa: E402
import contract  # noqa: E402
import gates  # noqa: E402
import motion  # noqa: E402


class FamilyTests(unittest.TestCase):
    def test_every_family_is_self_consistent(self):
        for family in cal.FAMILIES:
            with self.subTest(family=family):
                resolved = cal.resolve(family)
                bones = set(cal.referenced_bones(resolved))
                self.assertEqual(cal.validate(resolved, bones), [])
                self.assertEqual(resolved['root'], 'Root')

    def test_humanoid_uses_unity_names_and_sockets(self):
        bones = cal.referenced_bones(cal.resolve('humanoid'))
        for name in ('Hips', 'LeftUpperLeg', 'RightLowerArm', 'UpperChest', 'Socket_Hand_L', 'Socket_Hand_R'):
            self.assertIn(name, bones)
        self.assertEqual(len(bones), 25)

    def test_ground_gait_phases_cover_legs(self):
        for family in ('quadruped', 'hexapod', 'octopod', 'humanoid', 'mixamo-biped', 'maw-quadruped'):
            resolved = cal.resolve(family)
            self.assertEqual(set(resolved['gait']['phases']), {leg['id'] for leg in resolved['legs']}, family)

    def test_override_merges_deeply(self):
        resolved = cal.resolve('quadruped', {'gait': {'stride': 0.5}, 'addJaw': {'hinge': 0.4}})
        self.assertEqual(resolved['gait']['stride'], 0.5)
        self.assertEqual(resolved['gait']['type'], 'trot')
        self.assertEqual(resolved['addJaw']['hinge'], 0.4)

    def test_missing_bone_is_reported(self):
        resolved = cal.resolve('quadruped')
        errors = cal.validate(resolved, set(cal.referenced_bones(resolved)) - {'Tail_02'})
        self.assertEqual(errors, ['missing bone Tail_02'])


class ContractTests(unittest.TestCase):
    def test_templates_load(self):
        for name in ('rig-contract.json', 'rig-contract.biped.json'):
            row = contract.load(HERE.parent / 'templates' / name)
            self.assertIn('calibration', row)
            self.assertTrue(row['source']['model'].endswith('.fbx'))

    def test_rigid_parts_feed_calibration(self):
        row = contract.load(HERE.parent / 'templates' / 'rig-contract.biped.json')
        self.assertEqual(row['calibration']['rigid'], ['Malachar_Staff'])
        self.assertEqual(row['calibration']['soleWeightThreshold'], 0.85)

    def test_validation_rejects_bad_rows(self):
        base = {'subjectId': 'x', 'displayName': 'X', 'family': 'quadruped', 'engineRig': 'Generic',
                'requiredClips': ['Idle']}
        self.assertEqual(contract.validate(base), [])
        self.assertTrue(contract.validate({**base, 'family': 'dragon'}))
        self.assertTrue(contract.validate({**base, 'engineRig': 'Human'}))
        self.assertTrue(contract.validate({**base, 'requiredClips': ['Idle', 'Idle']}))
        self.assertTrue(contract.validate({**base, 'requiredClips': ['Walk']}))
        self.assertTrue(contract.validate({**base, 'rigidParts': [{'object': 'Sword'}]}))
        self.assertTrue(contract.validate({**base, 'rigidParts': [{'object': 'Sword', 'bone': 'RightHand',
                                                                    'grip': {'fraction': 2, 'direction': 'up'}}]}))

    def test_relative_source_resolves_against_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'rig-contract.json'
            path.write_text(json.dumps({'subjectId': 'x', 'displayName': 'X Y', 'family': 'quadruped',
                                        'engineRig': 'Generic', 'requiredClips': ['Idle'],
                                        'source': {'model': 'm/x.fbx'}}))
            row = contract.load(path)
            self.assertEqual(row['folder'], 'XY')
            self.assertEqual(row['source']['model'], (Path(tmp) / 'm/x.fbx').resolve().as_posix())


class MotionTests(unittest.TestCase):
    def test_foot_cycle_is_continuous_at_contacts(self):
        duty, stride, clearance = 0.6, 0.4, 0.1
        along_a, lift_a, planted_a = motion.foot_cycle(duty - 1e-6, duty, stride, clearance)
        along_b, lift_b, planted_b = motion.foot_cycle(duty + 1e-6, duty, stride, clearance)
        self.assertTrue(planted_a and not planted_b)
        self.assertAlmostEqual(along_a, along_b, places=4)
        self.assertAlmostEqual(lift_a, lift_b, places=4)
        along_end, lift_end, _ = motion.foot_cycle(1 - 1e-6, duty, stride, clearance)
        along_start, lift_start, _ = motion.foot_cycle(0.0, duty, stride, clearance)
        self.assertAlmostEqual(along_end, along_start, places=4)
        self.assertAlmostEqual(lift_end, lift_start, places=4)

    def test_travel_speed(self):
        self.assertAlmostEqual(motion.travel_speed(0.4, 0.5, 0.5), 1.6)

    def test_support_counts(self):
        self.assertEqual(motion.support_count('tripod', 0.55), 3)
        self.assertEqual(motion.support_count('tetrapod', 0.55), 4)
        self.assertEqual(motion.support_count('walk', 0.75), 3)

    def test_flap_is_periodic(self):
        self.assertAlmostEqual(motion.wing_flap(0.0, 1.0), motion.wing_flap(1.0, 1.0), places=6)


def clip(**overrides):
    base = {'maxFloorPenetration': 0.0, 'maxVertexMotion': 0.05, 'rootStationary': True, 'bodyScaleUnit': True,
            'maxDrop': {'front': 0.01, 'mid': 0.01, 'rear': 0.01}, 'loopSeam': 0.001, 'seamAccelerationRatio': 1.0,
            'finalCoreDrop': 0.0, 'finalBodyRotationAngle': 0.0, 'settleMotion': 0.0,
            'meanDisplacement': [0.0, 0.01, 0.02, 0.03], 'maxWeaponAngle': {}, 'finalWeaponAngle': {}}
    base.update(overrides)
    return base


class GateTests(unittest.TestCase):
    def test_clean_review_passes(self):
        review = {'clips': {
            'Idle': clip(meanDisplacement=[0, 0.01, 0.02, 0.03]),
            'Locomotion': clip(stanceDriftBodyHeights=0.01, swingSoleClearance=0.05, meanDisplacement=[0, 0.02, 0.04, 0.06]),
            'BasicAttack': clip(loopSeam=0.3, meanDisplacement=[0, 0.03, 0.05, 0.02]),
            'Hit': clip(loopSeam=0.3, meanDisplacement=[0, 0.05, 0.02, 0.01]),
            'Death': clip(finalCoreDrop=0.4, loopSeam=0.5, meanDisplacement=[0, 0.1, 0.3, 0.5]),
        }}
        self.assertEqual(gates.evaluate(review, 'ground', ['Idle', 'Locomotion', 'BasicAttack', 'Hit', 'Death']), [])

    def test_failures_are_named(self):
        review = {'clips': {
            'Idle': clip(maxFloorPenetration=0.05, loopSeam=0.02),
            'Locomotion': clip(meanDisplacement=[0, 0.02, 0.04, 0.06]),
            'Death': clip(finalCoreDrop=0.02, loopSeam=0.05, meanDisplacement=[0, 0.1, 0.3, 0.5]),
        }}
        failures = gates.evaluate(review, 'ground', ['Idle', 'Locomotion', 'Death', 'Hit'])
        text = '\n'.join(failures)
        self.assertIn('Idle: floor penetration', text)
        self.assertIn('Idle: loop seam', text)
        self.assertIn('no traveling contact evidence', text)
        self.assertIn('Death: core only dropped', text)
        self.assertIn('Death: ends near its starting pose', text)
        self.assertIn('Hit: missing from review', text)

    def test_duplicate_clips_are_caught(self):
        same = [0, 0.01, 0.02, 0.03]
        review = {'clips': {'BasicAttack': clip(loopSeam=0.3, meanDisplacement=same),
                            'Hit': clip(loopSeam=0.3, meanDisplacement=same)}}
        self.assertTrue(any('duplicates' in f for f in gates.evaluate(review, 'ground')))


if __name__ == '__main__':
    unittest.main()
