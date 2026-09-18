#!/usr/bin/env bash
# Image in, LivingBackdrop textures out.
#
#   build.sh <image> <out_dir> [work_dir]
#
# Env: MASK_MODEL (rembg model name), PLATE (hand-made background plate, skips
# the inpainter), UPSCALE=auto|1|0, WIDTHS="2560 1440".
# Needs uv, ImageMagick (magick), avifenc, cwebp. Models download on first run
# (~600 MB total) and are cached.
set -euo pipefail

SRC="$1"; OUT="$2"; WORK="${3:-$(mktemp -d)}"
HERE="$(cd "$(dirname "$0")" && pwd)"
WIDTHS="${WIDTHS:-2560 1440}"
mkdir -p "$OUT" "$WORK"

for tool in uv magick avifenc cwebp; do
  command -v "$tool" >/dev/null || { echo "missing: $tool" >&2; exit 1; }
done

magick "$SRC" -auto-orient -strip "$WORK/src.png"
W=$(magick identify -format %w "$WORK/src.png")
H=$(magick identify -format %h "$WORK/src.png")
echo "source ${W}x${H}, aspect $(echo "scale=4; $W/$H" | bc)"

echo "== 1/4 segment"
uv run -q --python 3.12 --with "rembg[cpu]" --with pillow \
  python "$HERE/segment.py" "$WORK" ${MASK_MODEL:-}

echo "== 2/4 inpaint + depth"
uv run -q --python 3.11 --with simple-lama-inpainting --with transformers --with torch --with "numpy<2" \
  python "$HERE/inpaint_depth.py" "$WORK" ${PLATE:-}

UPSCALE="${UPSCALE:-auto}"
if [ "$UPSCALE" = auto ]; then [ "$W" -lt 2400 ] && UPSCALE=1 || UPSCALE=0; fi
if [ "$UPSCALE" = 1 ]; then
  echo "== 3/4 upscale"
  MODEL="${XDG_CACHE_HOME:-$HOME/.cache}/living-backdrop/RealESRGAN_x2plus.pth"
  mkdir -p "$(dirname "$MODEL")"
  [ -f "$MODEL" ] || curl -fL -o "$MODEL" \
    https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth
  uv run -q --python 3.11 --with spandrel --with torch --with "numpy<2" --with pillow \
    python "$HERE/upscale.py" "$WORK" "$MODEL"
else
  echo "== 3/4 upscale skipped"
  cp "$WORK/src.png" "$WORK/scene-full.png"; cp "$WORK/bg.png" "$WORK/bg-full.png"
fi

echo "== 4/4 pack + encode"
uv run -q --python 3.11 --with scipy --with "numpy<2" --with pillow python "$HERE/pack.py" "$WORK"
for w in $WIDTHS; do for n in scene bg; do
  magick "$WORK/$n-full.png" -resize "${w}x>" -strip "$WORK/tmp.png"
  avifenc -q 62 -s 4 -y 420 "$WORK/tmp.png" "$OUT/$n-$w.avif" >/dev/null
done; done
# Lossless: lossy chroma subsampling bleeds the three channels into each other.
cwebp -quiet -lossless -z 9 "$WORK/maps.png" -o "$OUT/maps.webp"
set -- $WIDTHS
magick "$WORK/scene-full.png" -resize "${1}x>" -strip -quality 80 "$OUT/poster.jpg"

# The three things to look at before writing any code.
magick \( "$WORK/src.png" "$WORK/mask.png" +append \) \
       \( "$WORK/bg.png" "$WORK/depth-bg.png" +append \) -append -resize 1800x "$WORK/review.png"

echo; echo "aspect: $(echo "scale=4; $W/$H" | bc)   (pass as the aspect prop)"
ls -l "$OUT" | awk 'NR>1 {printf "  %8.0f KB  %s\n", $5/1024, $NF}'
echo "LOOK AT: $WORK/review.png  (source | mask / inpainted plate | background depth)"
