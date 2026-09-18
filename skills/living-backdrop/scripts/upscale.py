"""Step 3 (optional). Real-ESRGAN 2x for sources too small for a full-bleed hero.

usage: upscale.py <work_dir> <model.pth>
Reads src.png + bg.png, writes scene-full.png + bg-full.png. Tiled, runs on
MPS or CPU. Skip this step when the source is already >= 2560px wide.
"""
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from spandrel import ModelLoader

work = Path(sys.argv[1])
dev = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
model = ModelLoader().load_from_file(sys.argv[2]).to(dev).eval()
scale = model.scale


def upscale(src, out, tile=512, pad=16):
    im = np.asarray(Image.open(src).convert("RGB")).astype("float32") / 255
    h, w, _ = im.shape
    res = np.zeros((h * scale, w * scale, 3), "float32")
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            y0, x0 = max(y - pad, 0), max(x - pad, 0)
            y1, x1 = min(y + tile + pad, h), min(x + tile + pad, w)
            t = torch.from_numpy(im[y0:y1, x0:x1]).permute(2, 0, 1)[None].to(dev)
            with torch.no_grad():
                o = model(t)[0].permute(1, 2, 0).clamp(0, 1).cpu().numpy()
            oy, ox = (y - y0) * scale, (x - x0) * scale
            th, tw = (min(y + tile, h) - y) * scale, (min(x + tile, w) - x) * scale
            res[y * scale:y * scale + th, x * scale:x * scale + tw] = o[oy:oy + th, ox:ox + tw]
    Image.fromarray((res * 255).round().astype("uint8")).save(out)


upscale(work / "src.png", work / "scene-full.png")
upscale(work / "bg.png", work / "bg-full.png")
print(f"upscaled {scale}x on {dev}")
