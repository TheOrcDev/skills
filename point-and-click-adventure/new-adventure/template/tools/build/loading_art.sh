#!/usr/bin/env bash
# Makes the browser loading screen's pictures (web/loading/) from a room with
# both eras: its present, the past that blooms back while the game loads, and
# a round crop of the past as the tab's icon. Set --bloom-at in web/shell.html
# to where the bloom should start in the picture.
# Usage: tools/build/loading_art.sh [room_id] [icon crop: WxH+X+Y]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
room="${1:-greybox_chapel}"
crop="${2:-360x360+780+420}"
art="$ROOT/content/rooms/$room/art"
out="$ROOT/web/loading"
mkdir -p "$out"

cwebp -quiet -q 72 -m 6 -metadata none "$art/bg_now.png" -o "$out/now.webp"
cwebp -quiet -q 74 -m 6 -metadata none "$art/bg_then.png" -o "$out/then.webp"
magick "$art/bg_then.png" -crop "$crop" +repage -resize 128x128 \
	\( -size 128x128 xc:none -fill white -draw "circle 64,64 64,1" \) -compose DstIn -composite \
	"$out/icon.png"
ls -l "$out"
