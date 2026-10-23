"""A stand-in hero, drawn in code: a grey mannequin with every animation the
core plays, in the rig's render format (one folder per animation plus
anchors.json), so `pack` and `import_sprites.gd` build it like real frames.

It walks, talks, picks things up and gives, so a new game is playable on its
first day. Replace it with the painted hero (the painted-hero skill) when the
look is set.
"""

import json
import math
from pathlib import Path

import cv2
import numpy as np

from .imageio import save

FRAME = (448, 672)
CHARACTER_PX = 480
FEET = (224.0, 617.0)
# Body proportions in pixels at scale 1, from the feet up.
LEG = 228.0
TORSO = 170.0
NECK = 14.0
HEAD_R = 34.0
UPPER_ARM = 92.0
FOREARM = 90.0
SHOULDER_HALF = 46.0  # front and back views
HIP_HALF = 26.0
LIMB = 26  # line width of arms and legs
BODY = 70  # line width of the torso
SHADE = 34  # the body's grey
RIM = 120  # the rim's grey

WALK_FRAMES = 8
DRAWINGS = 5  # drawings per action, held in turn
WALK_FPS = 8.0
# Ground covered per step at scale 1: the planted foot goes from as far forward
# as the leg swings to as far back, so the feet never slide.
STRIDE_PX = 2 * math.sin(math.radians(26)) * LEG * 0.95
ACTION_FPS = 12.0


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


def _keys(keys: list[tuple[float, dict]], t: float) -> dict:
    """The pose at time `t` (0 to 1) between keyed poses, eased."""
    for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            f = _ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return {k: _lerp(p0.get(k, 0.0), p1.get(k, 0.0), f) for k in set(p0) | set(p1)}
    return dict(keys[-1][1])


def _knee(hip: np.ndarray, foot: np.ndarray, half: float, forward: np.ndarray) -> np.ndarray:
    """Where the knee goes for a leg of two `half`-long bones from `hip` to
    `foot`, bending towards `forward`."""
    span = foot - hip
    d = float(np.linalg.norm(span))
    if d >= 2 * half - 0.01:
        return hip + span / 2
    normal = np.array([-span[1], span[0]]) / d
    if float(np.dot(normal, forward)) < 0:
        normal = -normal
    return hip + span / 2 + normal * math.sqrt(half * half - (d / 2) ** 2)


def _pose(view: str, p: dict) -> tuple[np.ndarray, dict]:
    """Draws one frame. Angles are degrees from straight down, positive
    forward (towards +x in the side view). `crouch` lowers the hips in pixels,
    `lean` tilts the torso forward, `look` turns the head (-1 to 1)."""
    img = np.zeros((FRAME[1], FRAME[0], 4), np.uint8)
    fx, fy = FEET
    side = view == "r"
    crouch = p.get("crouch", 0.0)
    lean = math.radians(p.get("lean", 0.0))
    bob = p.get("bob", 0.0)
    hip = np.array([fx + p.get("shift", 0.0), fy - LEG - bob + crouch])
    chest = hip + np.array([math.sin(lean) * TORSO if side else 0.0, -math.cos(lean) * TORSO])
    neck = chest + np.array([0.0, -NECK])
    head = neck + np.array([p.get("look", 0.0) * (10.0 if side else 6.0), -HEAD_R])

    def limb(root, a1, a2, l1, l2):
        r1, r2 = math.radians(a1), math.radians(a1 + a2)
        if side:
            mid = root + np.array([math.sin(r1) * l1, math.cos(r1) * l1])
            end = mid + np.array([math.sin(r2) * l2, math.cos(r2) * l2])
        else:
            # Front and back views: forward swing reads as a shortening and a
            # slight spread.
            mid = root + np.array([math.sin(r1) * l1 * 0.25, math.cos(r1) * l1])
            end = mid + np.array([math.sin(r2) * l2 * 0.25, math.cos(r2) * l2])
        return mid, end

    anchors: dict = {}
    layers: list = []  # (depth, draw) so far limbs go behind the body
    for name, sign in (("l", -1.0), ("r", 1.0)):
        if side:
            hip_at = hip.copy()
            shoulder = chest + np.array([0.0, 12.0])
        else:
            mirror = 1.0 if view == "d" else -1.0  # the hero's left is screen right from the front
            hip_at = hip + np.array([-sign * mirror * HIP_HALF, 0.0])
            shoulder = chest + np.array([-sign * mirror * SHOULDER_HALF, 12.0])
        # Legs are two-bone IK: the foot goes where the pose puts it, on or
        # above the ground, and the knee bends forward to reach it.
        angle = math.radians(p.get(f"leg_{name}", 0.0))
        lift = max(0.0, p.get(f"lift_{name}", 0.0))
        reach = math.sin(angle) * LEG * 0.95 if side else 0.0
        foot = np.array([hip_at[0] + reach, min(fy, hip_at[1] + math.cos(angle) * LEG) - lift])
        knee = _knee(hip_at, foot, LEG / 2, forward=np.array([1.0, 0.0]) if side else np.array([-sign * 0.2, -1.0]))
        elbow, hand = limb(shoulder, p.get(f"arm_{name}", 0.0), p.get(f"elbow_{name}", 0.0), UPPER_ARM, FOREARM)
        anchors[f"shoulder_{name}"] = shoulder
        anchors[f"hand_{name}"] = hand
        # In the side view the far limbs (the left ones) are drawn behind.
        depth = -1 if side and name == "l" else 1
        shade = SHADE - 10 if depth < 0 else SHADE
        layers.append((depth, [(hip_at, knee, shade), (knee, foot, shade)], LIMB))
        layers.append((depth, [(shoulder, elbow, shade), (elbow, hand, shade)], LIMB - 4))

    def draw_segments(segments, width, value, alpha=255):
        for a, b, shade in segments:
            cv2.line(img, tuple(int(v) for v in a), tuple(int(v) for v in b), (value or shade,) * 3 + (alpha,), width, cv2.LINE_AA)

    def draw_body(value=None, grow=0):
        for depth, segments, width in layers:
            if depth < 0:
                draw_segments(segments, width + grow, value)
        draw_segments([(hip, chest, SHADE)], BODY + grow, value)
        draw_segments([(chest, neck, SHADE)], 26 + grow, value)
        cv2.circle(img, tuple(int(v) for v in head), int(HEAD_R + grow / 2), (value or SHADE,) * 3 + (255,), -1, cv2.LINE_AA)
        for depth, segments, width in layers:
            if depth > 0:
                draw_segments(segments, width + grow, value)

    # A rim: the body drawn a little larger and lighter, then the body over it.
    draw_body(value=RIM, grow=4)
    draw_body()
    if side:
        eye_l = head + np.array([10.0, -4.0])
        eye_r = head + np.array([20.0, -4.0])
        eyes_visible = [False, True]
    else:
        mirror = 1.0 if view == "d" else -1.0
        eye_l = head + np.array([12.0 * mirror, -4.0])
        eye_r = head + np.array([-12.0 * mirror, -4.0])
        eyes_visible = [view == "d", view == "d"]
    anchors.update({
        "head": head,
        "eye_l": eye_l,
        "eye_r": eye_r,
        "back": chest + np.array([-28.0 if side else 0.0, 20.0]),
        "feet": np.array(FEET),
    })
    out = {k: [round(float(v[0]), 2), round(float(v[1]), 2)] for k, v in anchors.items()}
    out["eyes_visible"] = eyes_visible
    return img, out


def _walk(view: str, i: int) -> dict:
    phase = i / WALK_FRAMES * 2 * math.pi
    swing = math.sin(phase)
    if view == "r":
        return {
            "leg_l": 26 * swing, "leg_r": -26 * swing,
            "lift_l": 34 * max(0.0, math.cos(phase)), "lift_r": 34 * max(0.0, -math.cos(phase)),
            "arm_l": -22 * swing, "arm_r": 22 * swing, "elbow_l": 12, "elbow_r": 12,
            "bob": 6 * abs(math.cos(phase)), "lean": 4,
        }
    return {
        "lift_l": max(0.0, 22 * swing), "lift_r": max(0.0, -22 * swing),
        "arm_l": -14 * swing, "arm_r": 14 * swing, "elbow_l": 6, "elbow_r": 6,
        "bob": 6 * abs(math.cos(phase)), "shift": 4 * swing,
    }


REST = {"arm_l": 4, "arm_r": -4, "elbow_l": 6, "elbow_r": 6}

# Every action: frame count, loop, events (frame -> name) and keyed poses.
ACTIONS: dict[str, dict] = {
    "idle": {"frames": 24, "loop": True, "keys": [(0.0, REST), (0.5, {**REST, "bob": 3}), (1.0, REST)]},
    "talk_a": {"frames": 16, "loop": True, "keys": [(0.0, REST), (0.4, {**REST, "arm_r": 70, "elbow_r": 50}), (0.7, {**REST, "arm_r": 55, "elbow_r": 70}), (1.0, REST)]},
    "talk_b": {"frames": 16, "loop": True, "keys": [(0.0, REST), (0.5, {"arm_l": 60, "arm_r": 60, "elbow_l": 50, "elbow_r": 50}), (1.0, REST)]},
    "look_around": {"frames": 36, "loop": False, "keys": [(0.0, REST), (0.3, {**REST, "look": -1}), (0.7, {**REST, "look": 1}), (1.0, REST)]},
    "fidget_a": {"frames": 24, "loop": False, "keys": [(0.0, REST), (0.5, {**REST, "shift": 8, "look": -0.6, "lean": 6}), (1.0, REST)]},
    "fidget_b": {"frames": 30, "loop": False, "keys": [(0.0, REST), (0.4, {**REST, "arm_r": 80, "elbow_r": 70, "look": 0.4}), (0.8, {**REST, "arm_r": 80, "elbow_r": 70, "look": 0.4}), (1.0, REST)]},
    "pickup_low": {"frames": 24, "loop": False, "events": {11: "grab"}, "keys": [(0.0, REST), (0.45, {"crouch": 80, "lean": 40, "arm_r": 35, "arm_l": 15, "leg_l": 8, "leg_r": 8}), (1.0, REST)]},
    "pickup_high": {"frames": 24, "loop": False, "events": {9: "grab"}, "keys": [(0.0, REST), (0.4, {**REST, "arm_r": 160, "elbow_r": 10}), (1.0, REST)]},
    "use": {"frames": 18, "loop": False, "events": {8: "use"}, "keys": [(0.0, REST), (0.45, {**REST, "arm_r": 85, "elbow_r": 5, "lean": 8}), (1.0, REST)]},
    "give": {"frames": 18, "loop": False, "events": {9: "give"}, "keys": [(0.0, REST), (0.5, {**REST, "arm_r": 75, "elbow_r": 15}), (1.0, REST)]},
    "flare": {"frames": 20, "loop": False, "events": {2: "flare"}, "keys": [(0.0, REST), (0.2, {"arm_l": 30, "arm_r": 30, "elbow_l": 20, "elbow_r": 20, "lean": -8}), (1.0, REST)]},
}


def _write(folder: Path, fps: float, animations: dict) -> None:
    meta = {"frame_size": list(FRAME), "character_px": CHARACTER_PX, "fps": fps, "animations": animations}
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "anchors.json").write_text(json.dumps(meta, indent=1) + "\n")


def build(out: Path, dirs: tuple[str, ...] = ("r", "u", "d")) -> dict:
    """Writes OUT/renders (actions at 12 fps) and OUT/renders-walk (the walk
    at 8 fps) and returns a summary."""
    actions: dict = {}
    walks: dict = {}
    for view in dirs:
        key = f"walk_{view}"
        frames, anchors = [], []
        for i in range(WALK_FRAMES):
            img, a = _pose(view, _walk(view, i))
            name = f"{key}_{i:03d}.png"
            save(out / "renders-walk" / key / name, img)
            frames.append(name)
            anchors.append(a)
        walks[key] = {
            "frames": frames, "loop": True, "anchors": anchors,
            "events": [{"frame": 0, "name": "step"}, {"frame": WALK_FRAMES // 2, "name": "step"}],
            "ground_px_per_second": round(2 * STRIDE_PX * WALK_FPS / WALK_FRAMES, 1),
        }
        for base, spec in ACTIONS.items():
            key = f"{base}_{view}"
            # Limited animation, as the painted hero has: a few drawings held
            # in turn on the frame rate, so the sheets stay small (a frame
            # named twice is packed once).
            frames, anchors = [], []
            count, drawings = spec["frames"], DRAWINGS
            drawn: dict[int, dict] = {}
            for i in range(count):
                index = i * drawings // count if spec["loop"] else round(i / max(1, count - 1) * (drawings - 1))
                name = f"{key}_{index:03d}.png"
                if index not in drawn:
                    t = index / drawings if spec["loop"] else index / (drawings - 1)
                    img, drawn[index] = _pose(view, _keys(spec["keys"], t))
                    save(out / "renders" / key / name, img)
                frames.append(name)
                anchors.append(drawn[index])
            actions[key] = {
                "frames": frames, "loop": spec["loop"], "anchors": anchors,
                "events": [{"frame": f, "name": n} for f, n in spec.get("events", {}).items()],
            }
    _write(out / "renders", ACTION_FPS, actions)
    _write(out / "renders-walk", WALK_FPS, walks)
    return {"renders": str(out / "renders"), "renders_walk": str(out / "renders-walk"), "animations": len(actions) + len(walks)}
