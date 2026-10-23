"""Builds a discovery reveal's zoom stack from one data file.

`art-source/work/reveal/<id>/reveal.json` names ring 0 (the widest painting),
where the hero's feet are in it, and, once they exist, rings 1 and 2. Each inner
ring is a 2x detail repaint of a 1536x536 crop of the ring outside it, centred
on the hero as far as the edges allow (art-pipeline.md §5B).

- `sources` writes ring1_source.png (from ring 0) and, when ring 1 is given,
  ring2_source.png: the crops scaled to 3072x1072, references for the repaint
  requests.
- `build` registers and level-matches the rings, grades them monochrome and
  writes content/cutscenes/<id>/art/ring*.png and reveal_spec.json for
  addons/adv_tools/new_reveal.gd.
"""

import json
from pathlib import Path

from adv_art import grade, rings
from adv_art.imageio import load, save

CROP = (1536, 536)
FEATHER = 0.08
# The zoom point sits this far above the feet, at ring 0's scale.
ZOOM_ABOVE_FEET = 82


def _crop(point: list[float], size: tuple[int, int]) -> list[int]:
    w, h = size
    x = min(max(round(point[0] - CROP[0] / 2), 0), w - CROP[0])
    y = min(max(round(point[1] - CROP[1] / 2), 0), h - CROP[1])
    return [x, y, CROP[0], CROP[1]]


def _geometry(spec: dict, ring0) -> dict:
    h, w = ring0.shape[:2]
    feet = spec["feet"]
    zoom = [feet[0], feet[1] - ZOOM_ABOVE_FEET]
    crop1 = _crop(zoom, (w, h))
    zoom1 = [(zoom[0] - crop1[0]) * 2, (zoom[1] - crop1[1]) * 2]
    crop2 = _crop(zoom1, (w, h))
    return {"zoom": zoom, "crops": [crop1, crop2], "size": (w, h)}


def sources(reveal_json: Path, root: Path) -> dict:
    spec = json.loads(reveal_json.read_text())
    ring0 = load(root / spec["ring0"])
    geometry = _geometry(spec, ring0)
    out = {}
    for index, (outer_key, crop) in enumerate(zip(["ring0", "ring1"], geometry["crops"]), start=1):
        if not spec.get(outer_key):
            break
        outer = load(root / spec[outer_key])
        x, y, w, h = crop
        path = reveal_json.parent / f"ring{index}_source.png"
        save(path, grade.resize(outer[y : y + h, x : x + w], geometry["size"]))
        out[f"ring{index}_source"] = str(path)
    return {**out, "crops": geometry["crops"], "zoom_point": geometry["zoom"]}


def build(reveal_json: Path, root: Path) -> dict:
    spec = json.loads(reveal_json.read_text())
    reveal_id = spec["id"]
    art = root / "content/cutscenes" / reveal_id / "art"
    res = f"res://content/cutscenes/{reveal_id}/art"
    ring0 = load(root / spec["ring0"])
    geometry = _geometry(spec, ring0)
    images, report = [ring0], []
    for index, crop in enumerate(geometry["crops"], start=1):
        inner = spec.get(f"ring{index}")
        if not inner:
            break
        prepared, registration = rings.prepare_ring(images[-1], load(root / inner), tuple(crop), FEATHER)
        images.append(prepared[:, :, :3])
        report.append({"ring": index, "residual_p90_px": round(registration.residual_p90_px, 2), "scale": round(registration.scale, 4)})
    placements, position, scale = [], [0.0, 0.0], 1.0
    for index, image in enumerate(images):
        if index > 0:
            x, y, _, _ = geometry["crops"][index - 1]
            position = [position[0] + x * scale, position[1] + y * scale]
            scale *= 0.5
        save(art / f"ring{index}.png", grade.monochrome(image))
        placements.append({"texture": f"{res}/ring{index}.png", "position": position, "scale": scale})
    h, w = ring0.shape[:2]
    feet = spec["feet"]
    reveal = {
        "rings": placements,
        "world_size": [w, h],
        "feather": FEATHER,
        "zoom_point": geometry["zoom"],
        "hero": {"feet": feet, "height": spec.get("hero_height", 260), "facing": spec.get("facing", "idle_r")},
        "start": {"zoom": 2.4, "center": [feet[0], feet[1] - 130]},
        "end": {"zoom": round(803 / h, 4), "center": [w / 2, h / 2]},
        "alignment": report,
    }
    (reveal_json.parent / "reveal_spec.json").write_text(json.dumps(reveal, indent=2) + "\n")
    return {"reveal": reveal_id, "rings": len(images), "alignment": report}
