#!/usr/bin/env bash
# Installs the pinned Godot addons into a game: Dialogue Manager 4.1.0 and
# GUT 9.7.1, each from its release commit, checked against a hash of its files
# (GitHub's archives themselves are not guaranteed byte-stable). An addon
# already present at the pinned version is left alone.
# Usage: fetch_addons.sh <game dir>
set -euo pipefail

game="$(cd "${1:?usage: fetch_addons.sh <game dir>}" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# name | repository | commit | version | sha256 of the sorted file hashes
ADDONS=(
	"dialogue_manager|nathanhoad/godot_dialogue_manager|a719088aea342572f29b5559fd8726896c9519b2|4.1.0|f6d6286290b6442ea97633b594da1c22e56487c40a51b596abd60c9bb99c88cc"
	"gut|bitwes/Gut|aeb5d4f3f7f0a6c9b5e178876d6c99b791fda605|9.7.1|a66225aa9fccd92f46d00e4fe76c6f840207c0623e9045f60600e330082f3e81"
)

tree_hash() {
	(cd "$1" && find . -type f ! -name '*.uid' ! -name '*.import' | LC_ALL=C sort | xargs shasum -a 256 | shasum -a 256 | cut -d' ' -f1)
}

for entry in "${ADDONS[@]}"; do
	IFS='|' read -r name repo commit version hash <<< "$entry"
	target="$game/addons/$name"
	if grep -q "^version=\"$version\"" "$target/plugin.cfg" 2>/dev/null; then
		echo "$name $version: already installed"
		continue
	fi
	echo "$name $version: downloading $repo@${commit:0:7}"
	curl -fsSL "https://codeload.github.com/$repo/tar.gz/$commit" | tar -xz -C "$work"
	source_dir="$(find "$work" -maxdepth 3 -type d -path "*/addons/$name" | head -1)"
	[[ -n "$source_dir" ]] || { echo "$name: addons/$name not found in the archive" >&2; exit 1; }
	actual="$(tree_hash "$source_dir")"
	if [[ "$actual" != "$hash" ]]; then
		echo "$name: file hash $actual does not match the pinned $hash" >&2
		exit 1
	fi
	mkdir -p "$game/addons"
	rm -rf "$target"
	cp -R "$source_dir" "$target"
	echo "$name $version: installed"
done
