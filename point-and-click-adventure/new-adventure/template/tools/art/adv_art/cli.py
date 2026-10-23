"""adv-art: image processing for a point-and-click-adventure game (docs/art-pipeline.md §7).

Run from the repository root:  uv run --project tools/art adv-art <command> --help
"""

import argparse
import json
import sys
from pathlib import Path

from . import align, grade, masks, pack, rings, sheet
from .imageio import load, save


def _size(text: str) -> tuple[int, int]:
    w, h = text.lower().split("x")
    return int(w), int(h)


def _rect(text: str) -> tuple[int, int, int, int]:
    x, y, w, h = (int(v) for v in text.split(","))
    return x, y, w, h


def _polygon(text: str) -> list[list[float]]:
    """A JSON list of [x, y] points, inline or from a file."""
    path = Path(text)
    return json.loads(path.read_text() if path.exists() else text)


def _print(data: dict) -> None:
    print(json.dumps(data, indent=2))


def cmd_placeholder_hero(args: argparse.Namespace) -> int:
    from . import placeholder

    _print(placeholder.build(Path(args.out), tuple(args.dirs.split(","))))
    return 0


def cmd_align(args: argparse.Namespace) -> int:
    fixed, moving = load(args.fixed), load(args.moving)
    registration = align.register(fixed, moving)
    report = registration.to_dict()
    report["passes"] = registration.residual_p90_px <= args.max_p90
    if args.out:
        save(args.out, align.warp(moving, registration, (fixed.shape[1], fixed.shape[0])))
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    _print(report)
    return 0 if report["passes"] else 1


def cmd_grade(args: argparse.Namespace) -> int:
    image = load(args.input)
    report: dict = {"saturation_percent_before": round(grade.saturation_percent(image), 2)}
    out = grade.resize(image, _size(args.size)) if args.size else image
    if args.mono:
        out = grade.monochrome(out)
    save(args.out, out)
    if args.walk_polygon:
        h, w = out.shape[:2]
        polygon = _polygon(args.walk_polygon)
        report["walk_area_luminance"] = grade.region_luminance(out, masks.polygon_mask((w, h), polygon))
        # The band where the hero's head and shoulders are seen: from the walk area's top edge up 40% of the frame height.
        top = min(p[1] for p in polygon)
        band = [[0, max(0, top - 0.4 * h)], [w, max(0, top - 0.4 * h)], [w, top], [0, top]]
        report["behind_figure_luminance"] = grade.region_luminance(out, masks.polygon_mask((w, h), band))
    report["out"] = str(args.out)
    _print(report)
    return 0


def cmd_mask(args: argparse.Namespace) -> int:
    save(args.out, masks.polygon_mask(_size(args.size), _polygon(args.polygon), args.feather))
    return 0


def cmd_cut(args: argparse.Namespace) -> int:
    image = load(args.input)
    h, w = image.shape[:2]
    rgba, rect = masks.cut(image, masks.polygon_mask((w, h), _polygon(args.polygon), args.feather))
    save(args.out, rgba)
    _print({"out": str(args.out), "rect": list(rect)})
    return 0


def cmd_ring(args: argparse.Namespace) -> int:
    outer, inner = load(args.outer), load(args.inner)
    rect = _rect(args.rect)
    ring, registration = rings.prepare_ring(outer, inner, rect, args.feather)
    save(args.out, ring)
    if args.preview:
        save(args.preview, rings.blend_preview(outer, ring, rect))
    report = registration.to_dict()
    report["rect_in_outer"] = list(rect)
    _print(report)
    return 0


def cmd_depth(args: argparse.Namespace) -> int:
    from . import depth

    image = load(args.input)
    save(args.out, depth.estimate(image if image.ndim == 2 else image[:, :, :3]))
    _print({"out": str(args.out), "model": depth.MODEL})
    return 0


def cmd_sheet(args: argparse.Namespace) -> int:
    images, labels = [], []
    for item in args.images:
        path, _, label = item.partition(":")
        images.append(load(path))
        labels.append(label or Path(path).stem)
    save(args.out, sheet.contact_sheet(images, labels, args.columns, _size(args.tile)))
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    renders = [Path(folder) for folder in args.renders]
    manifest = pack.pack(renders, Path(args.out_dir), Path(args.manifest), args.res_prefix, args.name, args.shaded, args.style)
    _print({key: {"fps": value["fps"], "frames": len(value["frames"])} for key, value in manifest["animations"].items()})
    return 0


def cmd_room(args: argparse.Namespace) -> int:
    from . import room

    root = Path(__file__).resolve().parents[3]
    for room_json in args.rooms:
        _print(room.build(Path(room_json).resolve(), root))
    return 0


def cmd_npc(args: argparse.Namespace) -> int:
    from . import npc

    root = Path(__file__).resolve().parents[3]
    for npc_json in args.npcs:
        _print(npc.build(Path(npc_json).resolve(), root))
    return 0


def cmd_painted(args: argparse.Namespace) -> int:
    from . import painted

    root = Path(__file__).resolve().parents[3]
    for spec in args.specs:
        _print(painted.write_guides(Path(spec).resolve(), root) if args.guides else painted.build(Path(spec).resolve(), root))
    return 0


def cmd_icons(args: argparse.Namespace) -> int:
    from . import icons

    root = Path(__file__).resolve().parents[3]
    _print({"icons": icons.cut(Path(args.sheet), args.names, root / "content/items", set(args.colour))})
    return 0


def cmd_closeup(args: argparse.Namespace) -> int:
    from . import room

    root = Path(__file__).resolve().parents[3]
    for closeup_json in args.closeups:
        _print(room.closeup(Path(closeup_json).resolve(), root))
    return 0


def cmd_reveal(args: argparse.Namespace) -> int:
    from . import reveal

    root = Path(__file__).resolve().parents[3]
    for reveal_json in args.reveals:
        path = Path(reveal_json).resolve()
        _print(reveal.sources(path, root) if args.sources else reveal.build(path, root))
    return 0


def cmd_grid(args: argparse.Namespace) -> int:
    from . import room

    room.grid(Path(args.input), Path(args.out), args.step, args.native)
    return 0


def cmd_overlay(args: argparse.Namespace) -> int:
    from . import room

    room.overlay(Path(args.room).resolve(), Path(__file__).resolve().parents[3], Path(args.out))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="adv-art", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("align", help="register MOVING onto FIXED and report the residual")
    p.add_argument("--fixed", required=True)
    p.add_argument("--moving", required=True)
    p.add_argument("--out", help="write MOVING warped into FIXED's frame")
    p.add_argument("--report", help="write the report as JSON")
    p.add_argument("--max-p90", type=float, default=3.0, help="fail above this p90 residual (px)")
    p.set_defaults(func=cmd_align)

    p = sub.add_parser("grade", help="resize, optionally make monochrome, and measure the walk area")
    p.add_argument("--in", dest="input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--size", help="WIDTHxHEIGHT")
    p.add_argument("--mono", action="store_true")
    p.add_argument("--walk-polygon", help="JSON points (in output pixels) of the walk area, inline or a file")
    p.set_defaults(func=cmd_grade)

    p = sub.add_parser("mask", help="write a polygon mask")
    p.add_argument("--size", required=True)
    p.add_argument("--polygon", required=True)
    p.add_argument("--feather", type=float, default=0.0)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_mask)

    p = sub.add_parser("cut", help="cut a polygon out of an image as RGBA (for occluders)")
    p.add_argument("--in", dest="input", required=True)
    p.add_argument("--polygon", required=True)
    p.add_argument("--feather", type=float, default=1.5)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_cut)

    p = sub.add_parser("ring", help="prepare an inner reveal ring for RECT of OUTER")
    p.add_argument("--outer", required=True)
    p.add_argument("--inner", required=True)
    p.add_argument("--rect", required=True, help="x,y,width,height in OUTER pixels")
    p.add_argument("--feather", type=float, default=0.08)
    p.add_argument("--out", required=True)
    p.add_argument("--preview")
    p.set_defaults(func=cmd_ring)

    p = sub.add_parser("depth", help="depth map (needs `uv sync --extra depth`)")
    p.add_argument("--in", dest="input", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_depth)

    p = sub.add_parser("sheet", help="contact sheet; images as PATH[:LABEL]")
    p.add_argument("--out", required=True)
    p.add_argument("--columns", type=int, default=2)
    p.add_argument("--tile", default="960x540")
    p.add_argument("images", nargs="+")
    p.set_defaults(func=cmd_sheet)

    p = sub.add_parser("pack", help="pack rendered character frames into alpha-mask sprite sheets")
    p.add_argument("--renders", required=True, action="append",
                   help="folder with anchors.json and one subfolder per animation; repeat to replace animations")
    p.add_argument("--out-dir", required=True, help="where the sheets go")
    p.add_argument("--manifest", required=True, help="where the JSON manifest goes")
    p.add_argument("--res-prefix", required=True, help="res:// folder the sheets are loaded from")
    p.add_argument("--name", required=True)
    p.add_argument("--shaded", action="store_true", help="keep the renders' shading: grey + alpha sheets")
    p.add_argument("--style", default="", help='"painted" for Sol\'s painted frames')
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("room", help="build rooms' art and room_spec.json from art-source/work/rooms/<id>/room.json")
    p.add_argument("rooms", nargs="+", help="room.json files")
    p.set_defaults(func=cmd_room)

    p = sub.add_parser("npc", help="prepare NPC paintings and npc_spec.json from art-source/work/characters/<id>/npc.json")
    p.add_argument("npcs", nargs="+", help="npc.json files")
    p.set_defaults(func=cmd_npc)

    p = sub.add_parser("painted", help="cut Sol's painted animation sheets into character frames, from art-source/work/characters/<id>/painted.json")
    p.add_argument("specs", nargs="+", help="painted.json files")
    p.add_argument("--guides", action="store_true", help="write each sheet's pose guide instead")
    p.set_defaults(func=cmd_painted)

    p = sub.add_parser("icons", help="cut an item sheet into content/items/<name>/icon.png, in reading order")
    p.add_argument("--sheet", required=True)
    p.add_argument("--colour", nargs="*", default=[], help="icons that keep their color; the rest go grey")
    p.add_argument("names", nargs="+")
    p.set_defaults(func=cmd_icons)

    p = sub.add_parser("closeup", help="build close-ups' art and closeup_spec.json from art-source/work/closeups/<id>/closeup.json")
    p.add_argument("closeups", nargs="+", help="closeup.json files")
    p.set_defaults(func=cmd_closeup)

    p = sub.add_parser("reveal", help="a reveal's ring sources (--sources) or its rings and reveal_spec.json, from art-source/work/reveal/<id>/reveal.json")
    p.add_argument("--sources", action="store_true")
    p.add_argument("reveals", nargs="+")
    p.set_defaults(func=cmd_reveal)

    p = sub.add_parser("placeholder-hero", help="draw a stand-in hero's frames in the render format, for pack")
    p.add_argument("--out", required=True, help="writes OUT/renders and OUT/renders-walk")
    p.add_argument("--dirs", default="r,u,d")
    p.set_defaults(func=cmd_placeholder_hero)

    p = sub.add_parser("grid", help="an image at 1920x1080 with a labelled grid, for tracing")
    p.add_argument("--in", dest="input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--step", type=int, default=100)
    p.add_argument("--native", action="store_true", help="keep the image's own size (NPC paintings)")
    p.set_defaults(func=cmd_grid)

    p = sub.add_parser("overlay", help="a room.json's walk area, hotspots and markers drawn on its now image")
    p.add_argument("--room", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_overlay)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
