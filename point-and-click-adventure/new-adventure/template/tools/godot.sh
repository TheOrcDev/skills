#!/usr/bin/env bash
# Runs the pinned Godot (4.7.2) on this project with any extra arguments.
# Usage: tools/godot.sh --headless --import
set -euo pipefail

GODOT_BIN="${GODOT_BIN:-$HOME/Applications/Godot-4.7.2.app/Contents/MacOS/Godot}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -x "$GODOT_BIN" ]]; then
	echo "Godot not found at $GODOT_BIN (set GODOT_BIN)" >&2
	exit 1
fi

# build/ holds exports, screenshots and logs; Godot must never import it.
mkdir -p "$ROOT/build" && touch "$ROOT/build/.gdignore"

exec "$GODOT_BIN" --path "$ROOT" "$@"
