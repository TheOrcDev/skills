"""Cuts an item sheet into inventory icons.

Each separate object on the sheet's transparent background becomes one icon,
in reading order (rows top to bottom, then left to right): it is trimmed,
padded square and scaled to SIZE. Specks smaller than MIN_AREA are ignored.
"""

from pathlib import Path

import cv2
import numpy as np

from adv_art.imageio import load, save

SIZE = 256
PAD = 0.08
MIN_AREA = 2000


def cut(sheet_path: Path, names: list[str], out_dir: Path, colour: set[str] = frozenset()) -> list[dict]:
    """`colour` names the icons that keep their color; the rest go grey, like the
    present they belong to."""
    sheet = load(sheet_path)
    alpha = (sheet[:, :, 3] > 12).astype(np.uint8)
    # Close small gaps so an object's thin parts (a key's ring and tag) stay one piece.
    joined = cv2.dilate(alpha, np.ones((15, 15), np.uint8))
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(joined)
    boxes = [(stats[i], centroids[i]) for i in range(1, count) if stats[i][cv2.CC_STAT_AREA] >= MIN_AREA]
    if len(boxes) != len(names):
        raise ValueError(f"{sheet_path}: found {len(boxes)} objects, expected {len(names)}")
    row_height = np.median([stat[cv2.CC_STAT_HEIGHT] for stat, _ in boxes])
    boxes.sort(key=lambda box: (round(box[1][1] / row_height), box[1][0]))
    report = []
    for name, (stat, _) in zip(names, boxes):
        x, y, w, h = stat[0], stat[1], stat[2], stat[3]
        crop = sheet[y:y + h, x:x + w].copy()
        side = int(max(w, h) * (1 + 2 * PAD))
        square = np.zeros((side, side, 4), np.uint8)
        square[(side - h) // 2:(side - h) // 2 + h, (side - w) // 2:(side - w) // 2 + w] = crop
        icon = cv2.resize(square, (SIZE, SIZE), interpolation=cv2.INTER_AREA)
        if name not in colour:
            grey = cv2.cvtColor(icon[:, :, :3], cv2.COLOR_BGR2GRAY)
            icon = np.dstack([grey, grey, grey, icon[:, :, 3]])
        path = out_dir / name / "icon.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        save(path, icon)
        report.append({"item": name, "box": [int(x), int(y), int(w), int(h)], "icon": str(path)})
    return report
