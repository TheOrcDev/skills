"""Builds a room's shipping art and room spec from one data file.

A room is described by `art-source/work/rooms/<id>/room.json`: its accepted now
and then images, walk area, scale zones, markers, hotspots, occluders and an
effects preset. `build` grades the now image to monochrome at 1920x1080,
aligns the then image to it, estimates depth, cuts the occluders for both
eras, and writes `content/rooms/<id>/art/` plus `room_spec.json` for
`addons/adv_tools/new_room.gd`. Plans 002 and 007 wrote one build.py per room;
Past had 50 rooms, so they are data instead.
"""

import json
from pathlib import Path

from adv_art import align, depth, grade, masks
from adv_art.imageio import load, save

SIZE = (1920, 1080)

# Effects presets: (era, type, name, properties). "{depth}" is the room's depth
# texture, "{light}" and "{aim}" the room's key light. Tuned in Past on a night
# exterior and a candlelit interior.
_NOW_EXTERIOR = [
    ("FogLayer", "FogFar", {"fog_color": [0.85, 0.86, 0.89, 1.0], "density": 0.3, "velocity": [0.005, 0.0], "noise_scale": [1.4, 0.8],
                            "band_top": 0.3, "band_bottom": 0.75, "depth_texture": "{depth}", "near_cutoff": 0.4, "noise_seed": 21}),
    ("FogLayer", "FogLow", {"fog_color": [0.8, 0.82, 0.86, 1.0], "density": 0.24, "velocity": [-0.008, 0.0], "noise_scale": [2.2, 1.1],
                            "band_top": 0.5, "band_bottom": 0.82, "depth_texture": "{depth}", "near_cutoff": 0.55, "noise_seed": 23}),
    ("LightShafts", "Moonlight", {"origin": "{light}", "aim": "{aim}", "spread": 30.0, "beams": 5.0, "intensity": 0.07, "reach": 0.9,
                                  "shaft_color": [0.9, 0.93, 1.0, 1.0], "flicker": 0.3}),
]
_NOW_INTERIOR = [
    ("FogLayer", "FogFar", {"fog_color": [0.85, 0.86, 0.88, 1.0], "density": 0.26, "velocity": [0.006, 0.0], "noise_scale": [1.4, 0.8],
                            "band_top": 0.42, "band_bottom": 0.9, "depth_texture": "{depth}", "near_cutoff": 0.45, "noise_seed": 3}),
    ("LightShafts", "Shafts", {"origin": "{light}", "aim": "{aim}", "spread": 36.0, "beams": 6.0, "intensity": 0.1, "reach": 0.95,
                               "shaft_color": [0.95, 0.96, 1.0, 1.0], "flicker": 0.4}),
    ("DustMotes", "Ash", {"area": [300, 200, 1400, 700], "mote_color": [0.85, 0.85, 0.88, 0.35], "mote_count": 45, "drift": [4, 6], "mote_size": 2.5}),
]
_GROUND_MIST = ("FogLayer", "GroundMist", {"fog_color": [0.86, 0.87, 0.9, 1.0], "density": 0.16, "velocity": [0.01, 0.0], "noise_scale": [2.6, 1.6],
                                           "band_top": 0.84, "band_bottom": 1.02, "band_softness": 0.08, "noise_seed": 27})
_THEN = [
    ("LightShafts", "GoldenShafts", {"origin": "{light}", "aim": "{aim}", "spread": 44.0, "beams": 7.0, "intensity": 0.14, "reach": 1.0,
                                     "shaft_color": [1.0, 0.85, 0.55, 1.0], "flicker": 0.25}),
    ("FogLayer", "WarmHaze", {"fog_color": [1.0, 0.9, 0.75, 1.0], "density": 0.1, "velocity": [0.004, 0.0], "noise_scale": [1.2, 0.7],
                              "band_top": 0.3, "band_bottom": 0.9, "noise_seed": 13}),
    ("DustMotes", "GoldenDust", {"area": [300, 150, 1500, 750], "mote_color": [1.0, 0.86, 0.55, 0.55], "mote_count": 60, "drift": [3, -4], "mote_size": 2.5}),
]
PRESETS = {"exterior": _NOW_EXTERIOR, "interior": _NOW_INTERIOR}


def _fill(value, depth_tex: str, light: list, aim: float):
    if value == "{depth}":
        return depth_tex
    if value == "{light}":
        return light
    if value == "{aim}":
        return aim
    return value


def effects(spec: dict, res: str, has_then: bool) -> list[dict]:
    """The room's effects: its preset for now, ground mist unless it opts out,
    the warm set for then, and any extra effects written out in full."""
    fx = spec.get("effects", {})
    preset = fx.get("preset", "exterior")
    light = fx.get("light", [1480, 120])
    aim = float(fx.get("aim", 225.0))
    depth_tex = f"{res}/depth_now.png"
    out = []
    rows = [("now", row) for row in PRESETS.get(preset, [])]
    if fx.get("ground_mist", True) and preset in PRESETS:
        rows.append(("now", _GROUND_MIST))
    if has_then and fx.get("then", True):
        rows += [("then", row) for row in _THEN]
    for era, (kind, name, props) in rows:
        entry = {"type": kind, "name": name, "era": era, "properties": {k: _fill(v, depth_tex, light, aim) for k, v in props.items()}}
        if name == "GroundMist":
            entry["layer"] = "foreground"
        out.append(entry)
    return out + fx.get("extra", [])


def build(room_json: Path, root: Path) -> dict:
    """Writes the room's art and room_spec.json; returns a report."""
    spec = json.loads(room_json.read_text())
    room_id = spec["id"]
    art = root / "content/rooms" / room_id / "art"
    res = f"res://content/rooms/{room_id}/art"
    art.mkdir(parents=True, exist_ok=True)

    now_key = load(root / spec["now"])
    now_colour = grade.resize(now_key, SIZE)
    now = now_colour if spec.get("now_grade") == "keep" else grade.monochrome(now_colour)
    # Props: things that can leave the room, such as a crate the hero
    # takes. The background is the clean plate (the same image without them),
    # and each prop is cut from the full image as its own layer to hide.
    props = []
    if spec.get("plate"):
        plate = grade.monochrome(grade.resize(load(root / spec["plate"]), SIZE))
        for name, polygon in spec.get("props", {}).items():
            rgba, rect = masks.cut(now, masks.polygon_mask(SIZE, polygon, feather_px=2.0))
            save(art / f"prop_{name.lower()}.png", rgba)
            props.append({"name": name, "texture": f"{res}/prop_{name.lower()}.png", "position": [rect[0], rect[1]]})
        now = plate
    save(art / "bg_now.png", now)
    save(art / "depth_now.png", depth.estimate(grade.resize(now_key, (SIZE[0] // 2, SIZE[1] // 2))[:, :, :3]))
    layers = {"now": [{"name": "Background", "texture": f"{res}/bg_now.png"}] + props}
    walk = {"now": spec["walk"]}
    report = {"room": room_id, "walk_area_luminance_now": grade.region_luminance(now, masks.polygon_mask(SIZE, spec["walk"]))}

    then = None
    if spec.get("then"):
        then_key = load(root / spec["then"])
        registration = align.register(now_key, then_key)
        then = grade.resize(align.warp(then_key, registration, (now_key.shape[1], now_key.shape[0])), SIZE)
        save(art / "bg_then.png", then)
        layers["then"] = [{"name": "Background", "texture": f"{res}/bg_then.png"}]
        walk["then"] = spec.get("walk_then", spec["walk"])
        report["then_alignment_p90_px"] = round(registration.residual_p90_px, 2)

    occluders = []
    for name, polygon in spec.get("occluders", {}).items():
        baseline = max(point[1] for point in polygon)
        for era, image in (("now", now), ("then", then)):
            if image is None:
                continue
            rgba, rect = masks.cut(image, masks.polygon_mask(SIZE, polygon, feather_px=1.5))
            file = f"occ_{name}_{era}.png"
            save(art / file, rgba)
            occluders.append({"name": f"{name.title().replace('_', '')}{era.title()}", "era": era if then is not None else "",
                              "texture": f"{res}/{file}", "rect": list(rect), "baseline": baseline})
    if then is None:
        for entry in occluders:
            del entry["era"]

    room_spec = {
        "display_name": spec["display_name"],
        "layers": layers,
        "walk": walk,
        "scale_zones": spec["scale_zones"],
        "markers": spec["markers"],
        "hotspots": spec["hotspots"],
        "occluders": occluders,
        "npcs": spec.get("npcs", []),
        "effects": effects(spec, res, then is not None),
    }
    out = room_json.parent / "room_spec.json"
    out.write_text(json.dumps(room_spec, indent=2) + "\n")
    report["spec"] = str(out)
    return report


def grid(image_path: Path, out: Path, step: int = 100, native: bool = False) -> None:
    """The image at 1920x1080 with a labelled grid, for tracing polygons. With
    `native` it keeps the image's own size (an NPC painting, whose points are
    traced in its own pixels), over grey where it is transparent."""
    import cv2
    import numpy as np

    image = load(image_path) if native else grade.resize(load(image_path), SIZE)
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        alpha = image[:, :, 3:4].astype(np.float32) / 255.0
        image = (image[:, :, :3] * alpha + 110 * (1.0 - alpha)).astype(np.uint8)
    image = image[:, :, :3].copy()
    height, width = image.shape[:2]
    for x in range(0, width, step):
        cv2.line(image, (x, 0), (x, height), (0, 200, 255) if x % 500 else (0, 0, 255), 1)
        cv2.putText(image, str(x), (x + 3, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    for y in range(0, height, step):
        cv2.line(image, (0, y), (width, y), (0, 200, 255) if y % 500 else (0, 0, 255), 1)
        cv2.putText(image, str(y), (3, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    save(out, image)


def overlay(room_json: Path, root: Path, out: Path) -> None:
    """The room's now image with its walk area (green), hotspots (yellow, exits
    red), markers and walk-to points drawn on it, for checking a trace."""
    import cv2
    import numpy as np

    spec = json.loads(room_json.read_text())
    image = grade.resize(load(root / spec["now"]), SIZE)[:, :, :3].copy()
    poly = lambda points: np.array(points, dtype=np.int32).reshape(-1, 1, 2)
    cv2.polylines(image, [poly(spec["walk"])], True, (0, 255, 0), 3)
    for hotspot in spec["hotspots"]:
        colour = (0, 0, 255) if "exit" in hotspot else (0, 255, 255)
        cv2.polylines(image, [poly(hotspot["polygon"])], True, colour, 2)
        x, y = hotspot["walk_to"]
        cv2.circle(image, (int(x), int(y)), 7, colour, -1)
        top = min(hotspot["polygon"], key=lambda p: p[1])
        cv2.putText(image, hotspot["id"], (int(top[0]), int(top[1]) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.8, colour, 2)
    for name, (x, y) in spec["markers"].items():
        cv2.drawMarker(image, (int(x), int(y)), (255, 0, 255), cv2.MARKER_CROSS, 24, 3)
        cv2.putText(image, name, (int(x) + 8, int(y) + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
    for polygon in spec.get("occluders", {}).values():
        cv2.polylines(image, [poly(polygon)], True, (255, 128, 0), 2)
    save(out, image)


def closeup(closeup_json: Path, root: Path) -> dict:
    """Builds a close-up's background and closeup_spec.json from one data file
    (`art-source/work/closeups/<id>/closeup.json`: id, image, hotspots)."""
    spec = json.loads(closeup_json.read_text())
    closeup_id = spec["id"]
    art = root / "content/closeups" / closeup_id / "art"
    art.mkdir(parents=True, exist_ok=True)
    image = grade.resize(load(root / spec["image"]), SIZE)
    save(art / "bg.png", image if spec.get("grade") == "keep" else grade.monochrome(image))
    out = closeup_json.parent / "closeup_spec.json"
    out.write_text(json.dumps({"background": f"res://content/closeups/{closeup_id}/art/bg.png", "hotspots": spec["hotspots"]}, indent=2) + "\n")
    return {"closeup": closeup_id, "spec": str(out)}
