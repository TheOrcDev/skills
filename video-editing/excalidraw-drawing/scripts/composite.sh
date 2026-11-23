#!/usr/bin/env bash
# Lay the transparent drawing layer over the untouched footage.
# The footage keeps its frames, color tags and audio (copied); only one high-quality encode.
# Usage: composite.sh VIDEO LAYER.mov START_FRAME OUT.mp4
#   START_FRAME = the first frame rendered into the layer (BOARD_FRAME).
set -euo pipefail
VIDEO=${1:?usage: composite.sh VIDEO LAYER.mov START_FRAME OUT.mp4}
LAYER=${2:?layer}
START=${3:?start frame}
OUT=${4:?output}
FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$VIDEO")

# Restamp both inputs by frame number: concat-style microsecond timestamps can
# otherwise slip the overlay by a frame or two.
ffmpeg -v error -stats -y -i "$VIDEO" -i "$LAYER" -filter_complex \
  "[0:v]settb=1/($FPS),setpts=N[b];[1:v]settb=1/($FPS),setpts=N+$START[o];[b][o]overlay=eof_action=pass:format=yuv420,format=yuv420p[v]" \
  -map "[v]" -map 0:a? -c:v libx264 -preset slow -crf 14 -profile:v high \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a copy -movflags +faststart "$OUT"

# Verify: same frame count, and the pre-board footage is visually identical.
n() { ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$1"; }
echo "frames: source $(n "$VIDEO"), output $(n "$OUT")"
PRE=$(python3 -c "print(max(1, $START - 1) / ($FPS))")
ffmpeg -v info -i "$VIDEO" -i "$OUT" -filter_complex "[0:v]trim=end=$PRE[a];[1:v]trim=end=$PRE[b];[a][b]psnr" -f null - 2>&1 \
  | grep -o "PSNR y:[0-9.]*.*average:[0-9.inf]*" || true
echo "$OUT"
