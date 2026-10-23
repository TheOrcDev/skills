#!/usr/bin/env bash
# Builds the hero's sprite set (the painted-hero skill):
#   1. the pose rig's renders, when missing (tools/blender/pose_rig.py, with
#      the base mesh at HERO_BASE_MESH): every animation at 12 fps into
#      $W/rig and the walk at 8 fps into $W/rig-walk8;
#   2. the painted frames from the accepted Sol sheets in $W/painted.json
#      (tools/adv-art painted), with the report in $W/painted-report.json;
#   3. the sprite sheets and manifest (tools/adv-art pack --style painted);
#   4. Godot's import, lossless, and the CharacterSprites resource.
# Animations not painted yet fall back to the stand-in's, if it was drawn.
#
# Usage: tools/build/build_hero.sh               # the painted set
#        tools/build/build_hero.sh --guides      # renders + pose-guide sheets only
#        tools/build/build_hero.sh --placeholder # the stand-in drawn in code, no Blender
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
W=art-source/work/characters/hero
SPRITES=content/characters/hero/sprites
mode="${1:-}"

render() {  # render <out> <fps> [anims]
	local out=$1 fps=$2 anims=${3:-}
	[[ -f "$out/anchors.json" ]] && return
	[[ -n "${HERO_BASE_MESH:-}" ]] || { echo "set HERO_BASE_MESH to the base mesh .blend (painted-hero WORKFLOW §0)" >&2; exit 1; }
	"$BLENDER" -b --disable-autoexec -P tools/blender/pose_rig.py -- --out "$out" --fps "$fps" \
		--base-mesh "$HERO_BASE_MESH" ${anims:+--anims "$anims"} \
		${HERO_RIG_CONFIG:+--config "$HERO_RIG_CONFIG"} | grep HERO_RENDER || true
}

renders=()
style=()
if [[ "$mode" == --placeholder ]]; then
	tools/adv-art placeholder-hero --out "$W" > /dev/null
	renders=(--renders "$W/renders" --renders "$W/renders-walk")
else
	[[ -f "$W/painted.json" ]] || { echo "no $W/painted.json (copy it from the painted-hero skill's templates)" >&2; exit 1; }
	render "$W/rig" 12
	render "$W/rig-walk8" 8 walk
	if [[ "$mode" == --guides ]]; then
		tools/adv-art painted --guides "$W/painted.json"
		exit 0
	fi
	tools/adv-art painted "$W/painted.json" > "$W/painted-report.json"
	# The stand-in first, so a painted animation replaces it and an unpainted one keeps it.
	if [[ -f "$W/renders/anchors.json" ]]; then
		renders+=(--renders "$W/renders" --renders "$W/renders-walk")
	fi
	renders+=(--renders "$W/painted")
	style=(--style painted)
fi

rm -f "$SPRITES"/*.png "$SPRITES"/*.png.import
tools/adv-art pack "${renders[@]}" --out-dir "$SPRITES" --manifest "$W/hero_sprites.json" \
	--res-prefix "res://$SPRITES" --name hero --shaded ${style[@]+"${style[@]}"} > /dev/null

# Painted ink blocks up under VRAM compression: the sheets import lossless.
tools/godot.sh --headless --import > /dev/null 2>&1 || true
for file in "$SPRITES"/*.png.import; do
	sed -i.bak 's/^compress\/mode=.*/compress\/mode=0/' "$file" && rm -f "$file.bak"
done
tools/godot.sh --headless --import > /dev/null 2>&1 || true
tools/godot.sh --headless --script res://addons/adv_tools/import_sprites.gd -- \
	--manifest="$W/hero_sprites.json" --out=res://content/characters/hero/hero_sprites.tres
