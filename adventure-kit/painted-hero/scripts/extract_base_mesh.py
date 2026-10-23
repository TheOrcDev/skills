"""Copies the realistic male body and its two eye markers out of Blender
Studio's Human Base Meshes bundle (CC0) into one small .blend for pose_rig.py.

  $BLENDER -b --disable-autoexec -P extract_base_mesh.py -- <bundle folder or .blend> <out.blend>

The bundle is a zip of several .blend files. This script searches every .blend
under the given folder for the objects named GEO-body_male_realistic,
GEO-body_male_realistic.eye.L and GEO-body_male_realistic.eye.R, and saves
them, with their multires sculpt, into OUT. Run Blender with
--disable-autoexec, as the bundle is a downloaded file.
"""

import sys
from pathlib import Path

import bpy

NAMES = ("GEO-body_male_realistic", "GEO-body_male_realistic.eye.L", "GEO-body_male_realistic.eye.R")


def find(source: Path) -> Path:
    files = [source] if source.suffix == ".blend" else sorted(source.rglob("*.blend"))
    for path in files:
        with bpy.data.libraries.load(str(path), link=False) as (src, _):
            if all(name in src.objects for name in NAMES):
                return path
    raise SystemExit(f"extract_base_mesh: no .blend under {source} holds {', '.join(NAMES)}")


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(argv) != 2:
        raise SystemExit("usage: extract_base_mesh.py -- <bundle folder or .blend> <out.blend>")
    source, out = Path(argv[0]).resolve(), Path(argv[1]).resolve()
    path = find(source)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(path), link=False) as (_, target):
        target.objects = list(NAMES)
    for obj in target.objects:
        bpy.context.scene.collection.objects.link(obj)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print("EXTRACTED", path, "->", out)


main()
