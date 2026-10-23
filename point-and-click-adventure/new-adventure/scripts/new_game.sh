#!/usr/bin/env bash
# Creates a new point-and-click-adventure game: copies the template project (template/) and
# the docs skeleton (templates/: AGENTS.md, CLAUDE.md, docs/, plans/), names
# the game, and brings in the sibling skills' files a game owns: the hero's
# pose rig (painted-hero) and the prompt preambles (look-gate). Fetch the
# addons next with fetch_addons.sh.
# Usage: new_game.sh <new dir> "<Game Name>"
set -euo pipefail

SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KIT="$(dirname "$SKILL")"
dest="${1:?usage: new_game.sh <new dir> \"<Game Name>\"}"
name="${2:?usage: new_game.sh <new dir> \"<Game Name>\"}"
slug="$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//; s/-$//')"
today="$(date -u +%Y-%m-%d)"

if [[ -e "$dest" && -n "$(ls -A "$dest" 2>/dev/null)" ]]; then
	echo "$dest exists and is not empty" >&2
	exit 1
fi
mkdir -p "$dest"
dest="$(cd "$dest" && pwd)"

rsync -a --exclude /.godot --exclude /build --exclude node_modules --exclude __pycache__ --exclude .venv \
	--exclude .pytest_cache --exclude /addons/dialogue_manager --exclude /addons/gut "$SKILL/template/" "$dest/"
rsync -a "$SKILL/templates/" "$dest/"

# Files the game owns from the sibling skills, when they are installed.
if [[ -f "$KIT/painted-hero/scripts/pose_rig.py" ]]; then
	mkdir -p "$dest/tools/blender"
	cp "$KIT/painted-hero/scripts/pose_rig.py" "$KIT/painted-hero/scripts/extract_base_mesh.py" "$dest/tools/blender/"
else
	echo "note: painted-hero is not installed beside this skill; copy its scripts/pose_rig.py into tools/blender/ later"
fi
if [[ -d "$KIT/look-gate/templates/preambles" ]]; then
	mkdir -p "$dest/art-source/style/prompts"
	cp "$KIT/look-gate/templates/preambles/"*.txt "$dest/art-source/style/prompts/"
else
	echo "note: look-gate is not installed beside this skill; its preambles go in art-source/style/prompts/"
fi

cd "$dest"
# The template ships its Git LFS rules un-dotted, so this skills repository
# stores its images as plain files; the game stores them in LFS.
mv gitattributes .gitattributes

# The game's name.
sed -i.bak "s/^config\/name=\"Adventure\"/config\/name=\"$name\"/" project.godot
sed -i.bak "s/build\/macos\/Adventure.app/build\/macos\/$name.app/; s/com.example.adventure/com.example.$slug/" export_presets.cfg
sed -i.bak "s/ADVENTURE/$(printf '%s' "$name" | tr '[:lower:]' '[:upper:]')/g; s/Adventure/$name/g" web/shell.html
find AGENTS.md docs plans -type f -name '*.md' -exec sed -i.bak "s/{{GAME_NAME}}/$name/g; s/{{DATE}}/$today/g" {} +
find . -name '*.bak' -delete

echo "created $name in $dest"
echo "next: $SKILL/scripts/fetch_addons.sh \"$dest\", then git init, git lfs install --local, tools/test.sh"
