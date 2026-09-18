"""Step 2. Paint the subject out of the background and estimate depth.

usage: inpaint_depth.py <work_dir> [plate]
Reads src.png + mask.png. Pass a hand-made plate (the image with the subject
already painted out) to skip the inpainter and use that instead. Writes bg.png, hole.png, depth-scene.npy, depth-bg.npy
and PNG previews of both depth maps.
"""
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageFilter
from simple_lama_inpainting import SimpleLama
from transformers import pipeline

work = Path(sys.argv[1])
src = Image.open(work / "src.png").convert("RGB")
mask = Image.open(work / "mask.png").convert("L")

# Dilate the hole so the inpainter never sees a subject-coloured fringe.
grow = max(round(src.width * 0.007) * 2 + 1, 5)
hole = mask.point(lambda v: 255 if v > 8 else 0).filter(ImageFilter.MaxFilter(grow))
hole.save(work / "hole.png")
if len(sys.argv) > 2:
    bg = Image.open(sys.argv[2]).convert("RGB").resize(src.size, Image.LANCZOS)
else:
    bg = SimpleLama()(src, hole).crop((0, 0, src.width, src.height))
bg.save(work / "bg.png")

pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
for name, im in (("scene", src), ("bg", bg)):
    d = pipe(im)["predicted_depth"]
    d = d[None, None] if d.ndim == 2 else d[None]
    d = torch.nn.functional.interpolate(d, size=(src.height, src.width), mode="bicubic")
    d = d[0, 0].numpy()
    np.save(work / f"depth-{name}.npy", d)
    n = (d - d.min()) / (d.max() - d.min())
    Image.fromarray((n * 255).astype("uint8")).save(work / f"depth-{name}.png")
print("bg.png and depth maps written")
