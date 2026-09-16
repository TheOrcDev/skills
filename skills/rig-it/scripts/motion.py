"""Pure-Python motion primitives shared by every creature family.

Nothing here imports Blender, so gait mechanics can be unit-tested directly.
All positions are expressed as fractions of a subject's calibrated body
height/length; the Blender authoring layer converts them into world units.
"""
from __future__ import annotations

import math


def smooth(a: float, b: float, x: float) -> float:
    """Smoothstep from 0 at a to 1 at b."""
    if b == a:
        return 1.0 if x >= b else 0.0
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def pulse(start: float, peak: float, end: float, x: float) -> float:
    """Rise 0->1 between start..peak, fall 1->0 between peak..end."""
    return smooth(start, peak, x) * (1 - smooth(peak, end, x))


def foot_cycle(phase: float, duty: float, stride: float, clearance: float) -> tuple[float, float, bool]:
    """Return (forward offset, lift, planted) for one leg at normalized phase.

    During stance (phase < duty) the foot moves backward relative to the body
    at constant speed from +stride/2 to -stride/2, which is what makes an
    in-place clip read as planted when the actor travels at the implied speed.
    During swing it returns forward on a cubic Hermite arc whose end slopes
    match the stance velocity, so lift-off and touchdown have no velocity
    discontinuity (no sliding touchdown). Clearance follows a sine-squared arc
    so vertical velocity is also zero at both contacts.
    """
    if not 0 < duty < 1:
        raise ValueError('duty must be in (0, 1)')
    p = phase % 1.0
    if p < duty:
        along = stride * (0.5 - p / duty)
        return along, 0.0, True
    s = (p - duty) / (1 - duty)
    slope = -stride * (1 - duty) / duty  # d(along)/ds at both swing ends
    h00 = 2 * s ** 3 - 3 * s ** 2 + 1
    h10 = s ** 3 - 2 * s ** 2 + s
    h01 = -2 * s ** 3 + 3 * s ** 2
    h11 = s ** 3 - s ** 2
    along = h00 * (-stride / 2) + h10 * slope + h01 * (stride / 2) + h11 * slope
    lift = clearance * math.sin(math.pi * s) ** 2  # zero vertical velocity at lift-off and touchdown
    return along, lift, False


def travel_speed(stride: float, duty: float, cycle_seconds: float) -> float:
    """Implied forward speed (same units as stride, per second)."""
    return stride / (duty * cycle_seconds)


GAIT_PHASES = {
    # diagonal pairs move together
    'trot': {'FL': 0.0, 'RR': 0.0, 'FR': 0.5, 'RL': 0.5},
    # lateral sequence walk: RR, RF, LR, LF
    'walk': {'RR': 0.0, 'FR': 0.25, 'RL': 0.5, 'FL': 0.75},
    # rotary-ish bound used for short scurries: front pair then rear pair
    'bound': {'FL': 0.0, 'FR': 0.1, 'RL': 0.5, 'RR': 0.6},
    # biped: legs alternate
    'biped': {'L': 0.0, 'R': 0.5},
    # insect alternating tripod
    'tripod': {'FL': 0.0, 'MR': 0.0, 'RL': 0.0, 'FR': 0.5, 'ML': 0.5, 'RR': 0.5},
    # spider alternating tetrapod: L1 R2 L3 R4 vs R1 L2 R3 L4
    'tetrapod': {'L1': 0.0, 'R2': 0.0, 'L3': 0.0, 'R4': 0.0,
                 'R1': 0.5, 'L2': 0.5, 'R3': 0.5, 'L4': 0.5},
}


def gait_phases(kind: str) -> dict[str, float]:
    if kind not in GAIT_PHASES:
        raise KeyError(f'Unknown gait {kind}')
    return dict(GAIT_PHASES[kind])


def support_count(kind: str, duty: float, samples: int = 64) -> int:
    """Minimum number of planted legs across the cycle (support sanity)."""
    phases = gait_phases(kind)
    worst = len(phases)
    for i in range(samples):
        t = i / samples
        planted = sum(1 for offset in phases.values() if ((t + offset) % 1.0) < duty)
        worst = min(worst, planted)
    return worst


def body_bounce(phase: float, beats: int, amplitude: float) -> float:
    """Vertical body offset: lowest at each support beat, highest between."""
    return -amplitude * 0.5 * (1 + math.cos(math.tau * phase * beats))


def wing_flap(phase: float, amplitude: float, lag: float = 0.0, power: float = 1.0) -> float:
    """Flap angle at phase (0 = top of upstroke). Positive means downstroke.

    Downstroke is faster than upstroke, so the curve is time-warped: the wing
    reaches the bottom at 0.4 of the cycle and recovers over the remaining 0.6.
    """
    p = (phase - lag) % 1.0
    if p < 0.4:
        s = p / 0.4
        angle = -math.cos(math.pi * s)  # -1 -> 1
    else:
        s = (p - 0.4) / 0.6
        angle = math.cos(math.pi * s)  # 1 -> -1
    return amplitude * angle * power


def lift_from_flap(phase: float, amplitude: float) -> float:
    """Altitude offset that rises during the downstroke and sinks on the upstroke."""
    p = phase % 1.0
    # integrate the flap: body rises while the wings push down (p<0.4)
    if p < 0.4:
        return amplitude * (-0.5 + math.sin(math.pi * p / 0.4 - math.pi / 2) * 0.5 + 1.0) - amplitude * 0.5
    s = (p - 0.4) / 0.6
    return amplitude * 0.5 * math.cos(math.pi * s)


def chain_lag(index: int, count: int, phase: float, amplitude: float, per_link: float = 0.55, fade: float = 1.0) -> float:
    """Follow-through for tails/antennae: later links lag behind the base."""
    return amplitude * (math.sin(phase - index * per_link) - math.sin(-index * per_link)) * fade


def frames_for(seconds: float, fps: int = 30) -> int:
    return int(round(seconds * fps)) + 1
