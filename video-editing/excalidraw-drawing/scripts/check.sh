#!/usr/bin/env bash
# Render the Guide composition at one frame and lay it over the real video frame,
# so layout is judged against the footage (board edges, webcam, toolbar), not a flat fill.
# Run from the drawing project. Usage: check.sh VIDEO FRAME [SCALE] [OUT.png]
set -euo pipefail
VIDEO=${1:?usage: check.sh VIDEO FRAME [SCALE] [OUT.png]}
FRAME=${2:?frame number}
SCALE=${3:-2}
OUT=${4:-out/check-$FRAME.png}
mkdir -p "$(dirname "$OUT")"
FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$VIDEO")
TMP=$(mktemp -d)
npx remotion still src/index.ts Guide "$TMP/layer.png" --frame="$FRAME" --scale="$SCALE" --log=error
ffmpeg -v error -y -ss "$(python3 -c "print($FRAME/($FPS))")" -i "$VIDEO" -i "$TMP/layer.png" \
  -filter_complex "[0:v][1:v]overlay,scale=1920:-1" -frames:v 1 "$OUT"
rm -rf "$TMP"
echo "$OUT"
