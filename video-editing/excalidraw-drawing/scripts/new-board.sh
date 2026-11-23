#!/usr/bin/env bash
# Scaffold a drawing-layer project from the template, fetch the Excalidraw fonts, install.
# Usage: new-board.sh <project-dir>
set -euo pipefail
DEST=${1:?usage: new-board.sh <project-dir>}
SKILL_DIR=$(cd "$(dirname "$0")/.." && pwd)

[ -e "$DEST" ] && { echo "refusing: $DEST already exists" >&2; exit 1; }
mkdir -p "$DEST"
cp -R "$SKILL_DIR/template/." "$DEST/"
mkdir -p "$DEST/public/fonts" "$DEST/out"

# Virgil (hand) and Cascadia (code) are Excalidraw's classic fonts, both SIL OFL.
TMP=$(mktemp -d)
( cd "$TMP" && npm pack --silent @excalidraw/excalidraw@0.17.6 >/dev/null && tar xzf excalidraw-excalidraw-0.17.6.tgz )
cp "$TMP/package/dist/excalidraw-assets/Virgil.woff2" "$TMP/package/dist/excalidraw-assets/Cascadia.woff2" "$DEST/public/fonts/"
rm -rf "$TMP"

( cd "$DEST" && npm install --silent )
echo "ready: $DEST  (edit src/config.ts, then src/scene.ts)"
