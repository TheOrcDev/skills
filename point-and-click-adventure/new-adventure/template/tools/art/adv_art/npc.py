"""Prepares an NPC painting for addons/adv_tools/new_npc.gd (the skinned-npc skill).

`art-source/work/characters/<id>/npc.json` names the accepted painting and
gives its bones and feet in the painting's own pixels. `build` trims the
painting to the figure, scales it so the figure is 1.5x its height on screen
(headroom for close-up push-ins), writes it to `content/characters/<id>/`, and
writes `npc_spec.json` with every point moved into the shipped texture's pixels.
"""

import json
from pathlib import Path

import cv2
import numpy as np

from adv_art.imageio import load, save

HEADROOM = 1.5
MARGIN = 8


def build(npc_json: Path, root: Path) -> dict:
    spec = json.loads(npc_json.read_text())
    npc_id = spec["id"]
    image = load(root / spec["painting"])
    if image.ndim != 3 or image.shape[2] != 4:
        raise ValueError(f"{spec['painting']} has no alpha channel")
    ys, xs = np.where(image[:, :, 3] > 8)
    x0, y0 = max(int(xs.min()) - MARGIN, 0), max(int(ys.min()) - MARGIN, 0)
    x1, y1 = min(int(xs.max()) + MARGIN, image.shape[1]), min(int(ys.max()) + MARGIN, image.shape[0])
    figure_height = ys.max() - ys.min()
    factor = min(1.0, spec["height"] * HEADROOM / figure_height)
    crop = image[y0:y1, x0:x1]
    size = (round(crop.shape[1] * factor), round(crop.shape[0] * factor))
    texture = cv2.resize(crop, size, interpolation=cv2.INTER_AREA)
    # The present is monochrome: a painting's stray color (brass,
    # skin) goes grey, unless the spec keeps it (the Dove's trace of blue).
    if not spec.get("keep_color", False):
        grey = cv2.cvtColor(texture[:, :, :3], cv2.COLOR_BGR2GRAY)
        texture = np.dstack([grey, grey, grey, texture[:, :, 3]])
    out_dir = root / "content/characters" / npc_id
    out_dir.mkdir(parents=True, exist_ok=True)
    save(out_dir / f"{npc_id}.png", texture)

    move = lambda point: [round((point[0] - x0) * factor, 1), round((point[1] - y0) * factor, 1)]
    out = {key: value for key, value in spec.items() if key not in ("painting", "bones", "feet", "speech")}
    out["texture"] = f"res://content/characters/{npc_id}/{npc_id}.png"
    out["feet"] = move(spec["feet"])
    out["speech"] = move(spec["speech"])
    out["texture_scale"] = round(spec["height"] / (figure_height * factor), 4)
    out["bones"] = [{**bone, "from": move(bone["from"]), "to": move(bone["to"])} for bone in spec["bones"]]
    contours, _ = cv2.findContours((texture[:, :, 3] > 8).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.approxPolyDP(max(contours, key=cv2.contourArea), 3.0, True).reshape(-1, 2)
    out["outline"] = [[int(x), int(y)] for x, y in hull]
    (npc_json.parent / "npc_spec.json").write_text(json.dumps(out, indent=2) + "\n")
    return {"npc": npc_id, "texture": list(size), "factor": round(factor, 4), "spec": str(npc_json.parent / "npc_spec.json")}
