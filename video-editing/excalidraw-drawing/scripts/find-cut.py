#!/usr/bin/env python3
"""Find the frame where the drawing board cuts in (or out).

Samples the mean brightness of a region of every frame and reports the biggest
frame-to-frame jumps. The board is usually a hard cut, so the top jump is it.

Usage: find-cut.py VIDEO [--from S] [--to S] [--crop W:H:X:Y]
  --crop is in source pixels (default: the middle third of the frame).
Prints: frame number (first frame of the new shot), time, brightness before -> after.
"""
import argparse
import json
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--from", dest="start", type=float, default=0.0)
ap.add_argument("--to", dest="end", type=float, default=None)
ap.add_argument("--crop", default=None)
a = ap.parse_args()

probe = json.loads(subprocess.check_output([
    "ffprobe", "-v", "error", "-select_streams", "v:0",
    "-show_entries", "stream=width,height,r_frame_rate:format=duration", "-of", "json", a.video]))
st = probe["streams"][0]
w, h = st["width"], st["height"]
num, den = map(int, st["r_frame_rate"].split("/"))
fps = num / den
end = a.end if a.end is not None else float(probe["format"]["duration"])
crop = a.crop or f"{w // 3}:{h // 3}:{w // 3}:{h // 3}"

cmd = ["ffmpeg", "-v", "error", "-ss", str(a.start), "-t", str(end - a.start), "-i", a.video,
       "-vf", f"crop={crop},scale=8:4,format=gray", "-f", "rawvideo", "-"]
raw = subprocess.run(cmd, capture_output=True, check=True).stdout
lum = [sum(raw[i:i + 32]) / 32 for i in range(0, len(raw) - 31, 32)]
if len(lum) < 2:
    sys.exit("no frames decoded in that range")

first = round(a.start * fps)
jumps = sorted(((abs(lum[i] - lum[i - 1]), i) for i in range(1, len(lum))), reverse=True)[:3]
print(f"{fps:g} fps, {len(lum)} frames scanned, crop {crop}")
for d, i in jumps:
    print(f"frame {first + i:6d}  t={(first + i) / fps:8.3f}s  {lum[i - 1]:6.1f} -> {lum[i]:6.1f}  (jump {d:.1f})")
