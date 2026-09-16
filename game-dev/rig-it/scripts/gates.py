"""Technical gates evaluated on review evidence (no Blender needed).

Thresholds come from shipped creature and biped review. They are
screening gates: passing them is necessary, never sufficient, for acceptance.
Any change to a threshold must be reviewed with the operator and recorded here.
"""
from __future__ import annotations

POSTURE_CLIPS = ('Idle', 'Locomotion')
THRESHOLDS = {
    'floorPenetration': 0.01,          # ≤1% body height below the floor (rat guard)
    'postureDrop': 0.10,               # ≤10% collapse of any core region relative to the body bone (Idle/Locomotion)
    'actionDrop': 0.30,                # actions intentionally move head/neck regions; still catch detachment
    'loopSeam': 0.005,                 # ≤0.5% body height pose difference across the loop
    'seamAcceleration': 1.6,           # seam acceleration ≤1.6× the worst interior acceleration (no hitch)
    'stanceDrift': 0.02,               # ≤2% body height planted sole drift while traveling
    'minSwingClearance': 0.03,         # swing feet clear the floor by ≥3% body height
    'frozen': 0.001,                   # every clip must move the mesh
    'deathCoreDrop': 0.15,             # death lowers the core by ≥15% body height ...
    'deathCoreDropMinimum': -0.10,     # ... or, for bodies whose belly already rests on the floor, a keel-over: the core may
    'deathBodyRotation': 0.5,          # rise up to 10% while the body rotates ≥0.5 rad (OPEN DECISION recorded on the board)
    'deathSettle': 0.05,               # last 20% of death moves the core by ≤5% body height
    'deathSeam': 0.2,                  # death must not loop back to its start
    'weaponAngle': 0.35,               # jaw/mandible/fang opens ≥0.35 rad in an attack when such a bone exists
    'weaponClosed': 0.05,              # and returns closed at the end
    'flapRange': 0.25,                 # flight clips move wing tips ≥25% body height
    'deadWingHeight': 0.2,             # a dead flyer's wing tips rest within 20% body height of the ground ...
    'deadWingMotion': 0.03,            # ... and stop moving (≤3% body height over the last fifth of the clip)
}


def evaluate(review: dict, mode: str = 'ground', required: list[str] | None = None) -> list[str]:
    """Return a list of failures (empty means every technical gate passed)."""
    failures = []
    clips = review['clips']
    for name in (required or list(clips)):
        if name not in clips:
            failures.append(f'{name}: missing from review')
            continue
        clip = clips[name]
        if clip['maxFloorPenetration'] > THRESHOLDS['floorPenetration']:
            failures.append(f"{name}: floor penetration {clip['maxFloorPenetration']:.4f}")
        if clip['maxVertexMotion'] < THRESHOLDS['frozen']:
            failures.append(f'{name}: frozen mesh')
        if not clip['rootStationary']:
            failures.append(f'{name}: navigation root moved')
        if not clip['bodyScaleUnit']:
            failures.append(f'{name}: body bone scale is not 1')
        limit = THRESHOLDS['postureDrop'] if name in POSTURE_CLIPS else THRESHOLDS['actionDrop']
        # Death is judged by its own core-drop, rotation and settle rules below: a body lying flat drops
        # every region relative to the hips by design, so the detachment check does not apply to it.
        for region, value in ({} if name == 'Death' else clip['maxDrop']).items():
            if value > limit:
                failures.append(f'{name}: {region} region drop {value:.3f} > {limit}')
        if name in POSTURE_CLIPS:
            if clip['loopSeam'] > THRESHOLDS['loopSeam']:
                failures.append(f"{name}: loop seam {clip['loopSeam']:.4f}")
            ratio = clip.get('seamAccelerationRatio')
            if ratio is not None and ratio > THRESHOLDS['seamAcceleration']:
                failures.append(f'{name}: loop hitch, seam acceleration ratio {ratio:.2f}')
        if name == 'Locomotion' and mode == 'ground':
            drift = clip.get('stanceDriftBodyHeights')
            if drift is None:
                failures.append('Locomotion: no traveling contact evidence')
            elif drift > THRESHOLDS['stanceDrift']:
                failures.append(f'Locomotion: planted sole drift {drift:.4f}')
            clearance = clip.get('swingSoleClearance')
            if clearance is not None and clearance < THRESHOLDS['minSwingClearance']:
                failures.append(f'Locomotion: swing clearance {clearance:.4f}')
        if name in ('Idle', 'Locomotion') and mode == 'air':
            if not clip.get('wingTipRange') or min(clip['wingTipRange'].values()) < THRESHOLDS['flapRange']:
                failures.append(f"{name}: wing tips barely move {clip.get('wingTipRange')}")
        if name == 'Death':
            rotation = clip.get('finalBodyRotationAngle', 0.0)
            dropped_enough = clip['finalCoreDrop'] >= THRESHOLDS['deathCoreDrop'] or (
                clip['finalCoreDrop'] >= THRESHOLDS['deathCoreDropMinimum'] and rotation >= THRESHOLDS['deathBodyRotation'])
            if mode == 'air' and not dropped_enough and clip.get('finalWingTipHeight'):
                # a flyer that already skims the ground dies by losing flight: wings down on the ground, no flapping
                wings_down = max(clip['finalWingTipHeight'].values()) <= THRESHOLDS['deadWingHeight']
                wings_still = max(clip['finalWingMotion'].values()) <= THRESHOLDS['deadWingMotion']
                dropped_enough = wings_down and wings_still and clip['finalCoreDrop'] >= -0.03
            if not dropped_enough:
                failures.append(f"Death: core only dropped {clip['finalCoreDrop']:.3f} with body rotation {rotation:.2f} rad"
                                + (f", wings {clip.get('finalWingTipHeight')} / motion {clip.get('finalWingMotion')}" if mode == 'air' else ''))
            if clip['settleMotion'] > THRESHOLDS['deathSettle']:
                failures.append(f"Death: still moving at the end {clip['settleMotion']:.3f}")
            if clip['loopSeam'] < THRESHOLDS['deathSeam']:
                failures.append('Death: ends near its starting pose')
        if name == 'BasicAttack' and clip.get('maxWeaponAngle'):
            if max(clip['maxWeaponAngle'].values()) < THRESHOLDS['weaponAngle']:
                failures.append(f"BasicAttack: weapon bones open only {clip['maxWeaponAngle']}")
            if max(clip['finalWeaponAngle'].values()) > THRESHOLDS['weaponClosed']:
                failures.append(f"BasicAttack: weapon bones not closed at the end {clip['finalWeaponAngle']}")
    # distinctness: no two clips may share the same motion signature
    signatures = {n: tuple(c['meanDisplacement'][:8]) for n, c in clips.items() if c.get('meanDisplacement')}
    seen = {}
    for name, signature in signatures.items():
        if signature in seen and len(signature) > 2:
            failures.append(f'{name} duplicates {seen[signature]}')
        seen.setdefault(signature, name)
    return failures
