"""Turns Sol's painted animation sheets into character frames (the painted-hero skill).

The hero is painted by Sol over pose guides: frames rendered from the pose
rig (tools/blender/pose_rig.py), laid out 4 x 2 on a 1536 x 1024 sheet, each cut to
the sheet's crop of the render frame and scaled into a 384 x 512 cell. Sol
repaints every mannequin as the character in the same pose and place, so a
painted cell maps back into the render frame by the inverse of that layout,
and the render's anchors, events and ground speed still hold.

`art-source/work/characters/<id>/painted.json`:

    {
      "out": "art-source/work/characters/hero/painted",
      "guides": "art-source/work/characters/hero/guides/sheets",
      "frame_size": [448, 672], "character_px": 480,
      "sheets": {
        "walk_r": {"view": "r", "raw": "art-source/raw/IMG-0042/IMG-0042-v3.png",
                   "crop": [34, 125, 380, 520], "thin": 0,
                   "cells": [["walk_r_0", "<renders folder>", "walk_r", 0], ...]},
        ...
      },
      "animations": {
        "walk_r": {"cells": ["walk_r_0", ...], "fps": 8, "from": ["<renders folder>", "walk_r"]},
        "use_r": {"keys": ["idle_r", "use_r_3", "use_r_7"], "from": ["<renders folder>", "use_r"]}
      }
    }

A sheet's cells name the render frames its guide shows, in reading order; its
crop, if not given, is the union of their silhouettes. "thin" erodes the
guide's mannequin by that many pixels and "squeeze" narrows it about the
crop's centre (0.8 is 80% as wide), so Sol paints the hero's slim build and not
the mannequin's muscle. A squeezed sheet stays narrow in the frames: its
anchors and the leg registration are squeezed the same way.

An animation either lists its cells in play order (the walks), or names KEYS:
then each frame of its FROM animation shows the key whose pose is nearest
(head and hands), which keeps the rig's timing and events as limited
animation, a few drawings held in turn. Events, the frame rate, looping and
ground speed come from FROM.

`guides` writes each sheet's guide; `build` cuts each painted sheet that has
a raw:
1. cuts the cell, drops the faint haze below ALPHA_FLOOR and stray marks away
   from the figure;
2. maps it into the render frame and stands it on the guide's feet (soles on
   soles, then sideways within SEARCH pixels), so a planted foot stays put;
3. finds the painted eyes (round bright blobs nearest the rig's eye anchors),
   records them as the eye anchors and paints them out: the game draws eyes
   that blink and flare;
4. writes the frames and an anchors.json in the render folders' format, for
   `adv-art pack --shaded --style painted`.
"""

import json
from pathlib import Path

import cv2
import numpy as np

from adv_art.imageio import load, luminance, save

SHEET = (1536, 1024)
GRID = (4, 2)
CELL = (384, 512)
GUIDE_BACKGROUND = (216, 216, 216)
GUIDE_LIFT, GUIDE_GAIN, GUIDE_CAP = 45.0, 1.5, 165.0
CROP_MARGIN = 24
ALPHA_FLOOR = 16
SEARCH = 48  # pixels the registration may move a cell
FEET_BAND = 60  # rows above the guide's soles compared when registering
FINE = 12  # pixels either side of the feet's centres the registration searches
EYE_SEARCH = 70  # pixels around the rig's head anchor searched for eyes
EYE_MIN_AREA = 6
EYE_MAX_AREA = 900
EYE_LUMA = 205
ERASE_RADIUS = 16
ERASE_LUMA = 70
FILL = (11, 11, 12)  # the body's ink black, BGR
POSE_ANCHORS = ("head", "hand_l", "hand_r")


class Renders:
    """Render folders (frames + anchors.json), read once each."""

    def __init__(self, root: Path):
        self.root = root
        self._meta: dict[str, dict] = {}

    def meta(self, folder: str) -> dict:
        if folder not in self._meta:
            self._meta[folder] = json.loads((self.root / folder / "anchors.json").read_text())
        return self._meta[folder]

    def anim(self, folder: str, anim: str) -> dict:
        return self.meta(folder)["animations"][anim]

    def frame(self, folder: str, anim: str, index: int) -> np.ndarray:
        return load(self.root / folder / anim / self.anim(folder, anim)["frames"][index])

    def anchors(self, folder: str, anim: str, index: int) -> dict:
        return self.anim(folder, anim)["anchors"][index]


def squeeze_matrix(sheet: dict, crop: list[int]) -> np.ndarray:
    """The frame-space narrowing a sheet asks for, as a 2 x 3 affine."""
    k = float(sheet.get("squeeze", 1.0))
    cx = crop[0] + crop[2] / 2.0
    return np.array([[k, 0.0, cx * (1.0 - k)], [0.0, 1.0, 0.0]], np.float32)


def squeezed(image: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    if matrix[0, 0] == 1.0:
        return image
    return cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0))


def squeeze_anchors(anchors: dict, matrix: np.ndarray) -> dict:
    out = {}
    for name, value in anchors.items():
        # Points only: the eye flags are booleans, which Python counts as ints.
        if isinstance(value, list) and len(value) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value):
            out[name] = [float(matrix[0, 0] * value[0] + matrix[0, 2]), float(value[1])]
        else:
            out[name] = value
    return out


def fit(crop: list[int]) -> tuple[float, float, float]:
    """Scale and padding that fit CROP into a cell, centred."""
    _, _, w, h = crop
    scale = min(CELL[0] / w, CELL[1] / h)
    return scale, (CELL[0] - w * scale) / 2.0, (CELL[1] - h * scale) / 2.0


def cell_to_frame(crop: list[int]) -> np.ndarray:
    """The 2 x 3 affine from cell pixels to render-frame pixels."""
    scale, pad_x, pad_y = fit(crop)
    return np.array([[1 / scale, 0.0, crop[0] - pad_x / scale], [0.0, 1 / scale, crop[1] - pad_y / scale]], np.float32)


def sheet_crop(sheet: dict, renders: Renders, frame_size: tuple[int, int]) -> list[int]:
    if "crop" in sheet:
        return list(sheet["crop"])
    x0, y0, x1, y1 = frame_size[0], frame_size[1], 0, 0
    for _, folder, anim, index in sheet["cells"]:
        ys, xs = np.nonzero(renders.frame(folder, anim, index)[:, :, 3] > 8)
        x0, y0, x1, y1 = min(x0, xs.min()), min(y0, ys.min()), max(x1, xs.max()), max(y1, ys.max())
    x0, y0, x1, y1 = x0 - CROP_MARGIN, y0 - CROP_MARGIN, x1 + CROP_MARGIN, y1 + CROP_MARGIN
    # Widen or heighten to the cell's shape, so the figure fills it.
    w, h = x1 - x0, y1 - y0
    if w * CELL[1] < h * CELL[0]:
        grow = h * CELL[0] / CELL[1] - w
        x0, w = x0 - grow / 2, w + grow
    else:
        grow = w * CELL[1] / CELL[0] - h
        y0, h = y0 - grow, h + grow  # room above: raised hands and hair
    return [int(round(x0)), int(round(y0)), int(round(w)), int(round(h))]


def guide(sheet: dict, renders: Renders, frame_size: tuple[int, int]) -> np.ndarray:
    """The pose guide Sol paints over: the mannequins on light grey, 4 x 2."""
    crop = sheet_crop(sheet, renders, frame_size)
    scale, pad_x, pad_y = fit(crop)
    matrix = np.array([[scale, 0.0, pad_x - crop[0] * scale], [0.0, scale, pad_y - crop[1] * scale]], np.float32)
    out = np.zeros((SHEET[1], SHEET[0], 3), np.uint8)
    out[:] = GUIDE_BACKGROUND
    thin = int(sheet.get("thin", 0))
    narrow = squeeze_matrix(sheet, crop)
    for index, (_, folder, anim, frame) in enumerate(sheet["cells"]):
        image = squeezed(renders.frame(folder, anim, frame), narrow).astype(np.float32)
        if thin:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * thin + 1, 2 * thin + 1))
            image[:, :, 3] = cv2.erode(image[:, :, 3], kernel)
        # Lift the dark front views and cap the speculars, so overlapping limbs
        # read and no highlight is mistaken for a painted detail.
        grey = np.clip(GUIDE_LIFT + GUIDE_GAIN * luminance(image.astype(np.uint8)), 0, GUIDE_CAP)
        image[:, :, 0] = image[:, :, 1] = image[:, :, 2] = grey
        cell = cv2.warpAffine(image, matrix, CELL, flags=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
        alpha = np.clip(cell[:, :, 3:4] / 255.0, 0.0, 1.0)
        col, row = index % GRID[0], index // GRID[0]
        target = out[row * CELL[1] : (row + 1) * CELL[1], col * CELL[0] : (col + 1) * CELL[0]]
        target[:] = np.clip(cell[:, :, :3] * alpha + target * (1.0 - alpha), 0, 255).astype(np.uint8)
    return out


def cut_cell(sheet: np.ndarray, index: int) -> np.ndarray:
    if (sheet.shape[1], sheet.shape[0]) != SHEET:
        sheet = cv2.resize(sheet, SHEET, interpolation=cv2.INTER_AREA)
    col, row = index % GRID[0], index // GRID[0]
    cell = sheet[row * CELL[1] : (row + 1) * CELL[1], col * CELL[0] : (col + 1) * CELL[0]].copy()
    return clean(cell)


def clean(cell: np.ndarray) -> np.ndarray:
    """Clears the faint haze and keeps the figure: the biggest blob and any
    sizeable blob close to it (a fraying coat tail, a curl of hair)."""
    alpha = cell[:, :, 3]
    alpha[alpha < ALPHA_FLOOR] = 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 0).astype(np.uint8), 8)
    if count <= 1:
        return cell
    main = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    mx, my, mw, mh = stats[main, :4]
    keep = np.zeros(count, bool)
    for label in range(1, count):
        x, y, w, h, area = stats[label]
        near = x < mx + mw + 12 and x + w > mx - 12 and y < my + mh + 12 and y + h > my - 12
        keep[label] = label == main or (near and area >= 12)
    cell[:, :, 3] = np.where(keep[labels], alpha, 0)
    return cell


def to_frame(cell: np.ndarray, crop: list[int], frame_size: tuple[int, int], shift: tuple[int, int] = (0, 0)) -> np.ndarray:
    matrix = cell_to_frame(crop)
    matrix[:, 2] += shift
    return cv2.warpAffine(cell, matrix, frame_size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def register(painted: np.ndarray, guide_alpha: np.ndarray, feet_y: float) -> tuple[int, int]:
    """The shift, in whole pixels, that stands the painted figure on the guide's
    feet: its soles on the guide's soles, then sideways until its feet lie on
    the guide's. Only the feet are compared: the coat hides the legs from the
    front and back, and the hair and coat outgrow the mannequin."""
    mask = painted[:, :, 3] > 127
    target = guide_alpha > 127
    rows = np.nonzero(mask.any(axis=1))[0]
    guide_rows = np.nonzero(target.any(axis=1))[0]
    if len(rows) == 0 or len(guide_rows) == 0:
        return (0, 0)
    dy = int(guide_rows.max() - rows.max())
    bottom = int(guide_rows.max()) + 1
    top = max(0, bottom - FEET_BAND)
    band_target = target[top:bottom]
    h, w = mask.shape
    # Start from the feet's centres (both feet together), then fine-tune within
    # FINE pixels, so the search can't lock one foot onto the other.
    painted_band = mask[top - dy : bottom - dy] if top - dy >= 0 else mask[max(0, top - dy) : max(0, bottom - dy)]
    guide_xs = np.nonzero(band_target)[1]
    painted_xs = np.nonzero(painted_band)[1]
    centre = int(round(guide_xs.mean() - painted_xs.mean())) if len(guide_xs) and len(painted_xs) else 0
    centre = int(np.clip(centre, -SEARCH, SEARCH))
    best, best_score = (centre, dy), -1.0
    for dx in range(centre - FINE, centre + FINE + 1):
        moved = np.zeros_like(mask)
        ys, ye = max(0, dy), min(h, h + dy)
        xs, xe = max(0, dx), min(w, w + dx)
        moved[ys:ye, xs:xe] = mask[ys - dy : ye - dy, xs - dx : xe - dx]
        band = moved[top:bottom]
        union = np.count_nonzero(band | band_target)
        score = np.count_nonzero(band & band_target) / union if union else 0.0
        if score > best_score:
            best, best_score = (dx, dy), score
    return best


def find_eyes(frame: np.ndarray, head: tuple[float, float], expected: list[tuple[float, float]]) -> list[tuple[float, float, float]]:
    """The painted eyes, (x, y, radius) each: of the round, bright blobs near the
    head, the one nearest each EXPECTED eye position (the rig's anchors), so a
    bright collar edge or rim line is never taken for an eye."""
    hx, hy = int(head[0]), int(head[1])
    x0, y0 = max(0, hx - EYE_SEARCH), max(0, hy - EYE_SEARCH)
    x1, y1 = min(frame.shape[1], hx + EYE_SEARCH), min(frame.shape[0], hy + EYE_SEARCH)
    region = frame[y0:y1, x0:x1]
    bright = ((luminance(region) >= EYE_LUMA) & (region[:, :, 3] > 160)).astype(np.uint8)
    count, _, stats, centroids = cv2.connectedComponentsWithStats(bright, 8)
    blobs = []
    for label in range(1, count):
        _, _, w, h, area = stats[label]
        radius = max(w, h) / 2.0
        # Eyes are round dots; rim lines are long and thin.
        if EYE_MIN_AREA <= area <= EYE_MAX_AREA and area >= 0.4 * np.pi * radius * radius:
            cx, cy = centroids[label]
            blobs.append((x0 + float(cx), y0 + float(cy), float(radius)))
    eyes = []
    for ex, ey in expected:
        free = [blob for blob in blobs if blob not in eyes]
        if not free:
            break
        nearest = min(free, key=lambda blob: (blob[0] - ex) ** 2 + (blob[1] - ey) ** 2)
        if (nearest[0] - ex) ** 2 + (nearest[1] - ey) ** 2 <= EYE_SEARCH**2:
            eyes.append(nearest)
    return eyes


def erase_eyes(frame: np.ndarray, eyes: list[tuple[float, float, float]]) -> None:
    """Paints the eyes and their glow out with the body's black."""
    if not eyes:
        return
    luma = luminance(frame)
    yy, xx = np.mgrid[0 : frame.shape[0], 0 : frame.shape[1]]
    for x, y, r in eyes:
        reach = max(ERASE_RADIUS, r * 2.6)
        near = (xx - x) ** 2 + (yy - y) ** 2 <= reach**2
        glow = near & (luma >= ERASE_LUMA) & (frame[:, :, 3] > 0)
        frame[glow, 0], frame[glow, 1], frame[glow, 2] = FILL


def place_eyes(anchors: dict, eyes: list[tuple[float, float, float]], view: str) -> dict:
    """Eye anchors from the painted eyes: in profile the one eye is the right
    eye; from the front the eye on the viewer's left is his right. Where Sol
    painted none (his head turned away or bowed), the game draws none."""
    anchors = dict(anchors)
    if view == "u" or not eyes:
        anchors["eyes_visible"] = [False, False]
        return anchors
    if view == "d" and len(eyes) == 2:
        right, left = sorted(eyes, key=lambda eye: eye[0])
        anchors["eye_r"], anchors["eye_l"] = [right[0], right[1]], [left[0], left[1]]
        anchors["eyes_visible"] = [True, True]
    else:
        x, y, _ = eyes[0]
        anchors["eye_r"] = anchors["eye_l"] = [x, y]
        anchors["eyes_visible"] = [False, True]
    return anchors


def write_guides(spec_path: Path, root: Path) -> list[str]:
    spec = json.loads(spec_path.read_text())
    renders = Renders(root)
    frame_size = tuple(spec["frame_size"])
    written = []
    for name, sheet in spec["sheets"].items():
        path = root / spec["guides"] / f"{name}.png"
        save(path, guide(sheet, renders, frame_size))
        written.append(str(path.relative_to(root)))
    return written


def nearest_key(target: dict, keys: list[tuple[str, dict]]) -> str:
    def distance(anchors: dict) -> float:
        return sum(float(np.hypot(anchors[a][0] - target[a][0], anchors[a][1] - target[a][1])) for a in POSE_ANCHORS)

    return min(keys, key=lambda key: distance(key[1]))[0]


def build(spec_path: Path, root: Path) -> dict:
    spec = json.loads(spec_path.read_text())
    out = root / spec["out"]
    frame_size = tuple(spec["frame_size"])
    renders = Renders(root)
    cells: dict[str, dict] = {}  # name -> anchors of the painted drawing
    poses: dict[str, dict] = {}  # name -> the rig's own anchors for it, to match poses on
    report: dict = {}
    for sheet_name, sheet in spec["sheets"].items():
        if not sheet.get("raw"):
            continue
        crop = sheet_crop(sheet, renders, frame_size)
        narrow = squeeze_matrix(sheet, crop)
        painting = load(root / sheet["raw"])
        view = sheet["view"]
        for index, (name, folder, anim, frame_index) in enumerate(sheet["cells"]):
            anchors = squeeze_anchors(renders.anchors(folder, anim, frame_index), narrow)
            guide_alpha = squeezed(renders.frame(folder, anim, frame_index), narrow)[:, :, 3]
            cell = cut_cell(painting, index)
            shift = register(to_frame(cell, crop, frame_size), guide_alpha, anchors["feet"][1])
            frame = to_frame(cell, crop, frame_size, shift)
            expected = {"r": [anchors["eye_r"]], "d": [anchors["eye_r"], anchors["eye_l"]]}.get(view, [])
            eyes = find_eyes(frame, anchors["head"], expected)
            erase_eyes(frame, eyes)
            save(out / "cells" / f"{name}.png", frame)
            cells[name] = place_eyes(anchors, eyes, view)
            poses[name] = renders.anchors(folder, anim, frame_index)
            report[name] = {"sheet": sheet_name, "shift": list(shift), "eyes": len(eyes)}
    animations = {}
    for anim, entry in spec["animations"].items():
        folder, source = entry["from"]
        origin = renders.anim(folder, source)
        if "cells" in entry:
            names = list(entry["cells"])
        else:
            keys = [(key, poses[key]) for key in entry["keys"] if key in cells]
            if len(keys) != len(entry["keys"]):
                continue  # a sheet it needs is not painted yet
            names = [nearest_key(frame_anchors, keys) for frame_anchors in origin["anchors"]]
        if any(name not in cells for name in names):
            continue
        (out / anim).mkdir(parents=True, exist_ok=True)
        for name in set(names):
            (out / anim / f"{name}.png").write_bytes((out / "cells" / f"{name}.png").read_bytes())
        record = {
            "fps": entry.get("fps", origin.get("fps", spec_fps(renders, folder))),
            "frames": [f"{name}.png" for name in names],
            "loop": entry.get("loop", origin["loop"]),
            "anchors": [cells[name] for name in names],
        }
        if origin.get("events"):
            record["events"] = origin["events"]
        if "ground_px_per_second" in origin:
            record["ground_px_per_second"] = origin["ground_px_per_second"]
        animations[anim] = record
        report[anim] = " ".join(name.rsplit("_", 1)[-1] if name.startswith(source) else name for name in names)
    (out / "anchors.json").write_text(json.dumps({"frame_size": list(frame_size), "character_px": spec["character_px"], "fps": 12.0, "animations": animations}, indent=1) + "\n")
    return report


def spec_fps(renders: Renders, folder: str) -> float:
    return float(renders.meta(folder)["fps"])
