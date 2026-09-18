"""Step 4. Pack the data map: R subject depth, G background depth, B subject mask.

usage: pack.py <work_dir>
Reads depth-scene.npy, depth-bg.npy, mask.png. Writes maps.png (1024px wide).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

work = Path(sys.argv[1])
ds, db = np.load(work / "depth-scene.npy"), np.load(work / "depth-bg.npy")
mask = np.asarray(Image.open(work / "mask.png").convert("L")).astype("float32") / 255

# One scale for both layers, or they slide at unrelated rates.
lo, hi = min(ds.min(), db.min()), max(ds.max(), db.max())
ds, db = (ds - lo) / (hi - lo), (db - lo) / (hi - lo)

# Depth estimators blur across the silhouette, so edge pixels of the subject
# read as half-background and shear under parallax. Trust only the eroded
# interior and extend it outward.
px = max(round(mask.shape[1] * 0.006), 3)
core = ndi.binary_erosion(mask > 0.5, iterations=px)
if not core.any():
    sys.exit("mask is empty after erosion: fix the mask first")
idx = ndi.distance_transform_edt(~core, return_distances=False, return_indices=True)
subject = ndi.gaussian_filter(ds[tuple(idx)], px / 2)
# Blur the background depth too, or fine texture (grass, leaves) swims.
db = ndi.gaussian_filter(db, px * 0.6)

maps = np.stack([subject, db, mask], -1).clip(0, 1)
im = Image.fromarray((maps * 255).round().astype("uint8"))
im.resize((1024, round(1024 * im.height / im.width)), Image.LANCZOS).save(work / "maps.png")

print(f"subject depth {subject[core].min():.2f}-{subject[core].max():.2f}, "
      f"background depth {db.min():.2f}-{db.max():.2f}")
print(f"suggested focus (midway between the layers): "
      f"{(float(np.median(subject[core])) + float(np.median(db))) / 2:.2f}")
