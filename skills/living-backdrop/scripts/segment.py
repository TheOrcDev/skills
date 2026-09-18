"""Step 1. Cut the subject out: writes mask.png (white = subject).

usage: segment.py <work_dir> [model]
Reads <work_dir>/src.png. Default model is birefnet-general-lite; if the mask
is wrong, try isnet-general-use or birefnet-general and LOOK at the result.
"""
import sys
from pathlib import Path

from PIL import Image
from rembg import new_session, remove

work = Path(sys.argv[1])
model = sys.argv[2] if len(sys.argv) > 2 else "birefnet-general-lite"

im = Image.open(work / "src.png").convert("RGB")
mask = remove(im, session=new_session(model), only_mask=True).convert("L")
mask.save(work / "mask.png")

coverage = sum(mask.histogram()[128:]) / (mask.width * mask.height)
print(f"mask.png written with {model}: subject covers {coverage:.0%} of the frame")
if not 0.03 < coverage < 0.75:
    print("WARNING: coverage is outside 3-75%. The mask is probably wrong. Look at it.")
