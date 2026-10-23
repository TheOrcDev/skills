#!/usr/bin/env bash
# Exports a build into build/<target>/ and fails if the export logs errors.
# Usage: tools/build/export.sh macos|web [release|debug]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
target="${1:?usage: export.sh macos|web [release|debug]}"
mode="${2:-release}"

# The app is named after the game (application/config/name in project.godot).
name="$(sed -n 's/^config\/name="\(.*\)"$/\1/p' "$ROOT/project.godot")"
case "$target" in
	macos) preset="macOS"; out="$ROOT/build/macos/$name.app" ;;
	web) preset="Web"; out="$ROOT/build/web/index.html" ;;
	*) echo "unknown target: $target" >&2; exit 2 ;;
esac

rm -rf "$(dirname "$out")"
mkdir -p "$(dirname "$out")"
log="$ROOT/build/export-$target.log"

# The browser build carries only the parts marked "web" in content/chapters.json:
# the other parts' rooms, close-ups, characters and dialogue
# are added to the Web preset's exclude filter for this export only.
excluded=()
if [[ "$target" == web ]]; then
	while IFS= read -r path; do excluded+=("$path"); done < <(jq -r '.parts[] | select(.web != true) |
		((.rooms // [])[] | "content/rooms/\(.)"), ((.closeups // [])[] | "content/closeups/\(.)"),
		((.characters // [])[] | "content/characters/\(.)"), ((.dialogue // [])[] | "content/dialogue/\(.)"),
		((.cutscenes // [])[] | "content/cutscenes/\(.)")' "$ROOT/content/chapters.json")
	if [[ ${#excluded[@]} -gt 0 ]]; then
		cp "$ROOT/export_presets.cfg" "$ROOT/build/export_presets.cfg.bak"
		trap 'mv "$ROOT/build/export_presets.cfg.bak" "$ROOT/export_presets.cfg"' EXIT
		patterns="$(printf ', %s/*' "${excluded[@]}")"
		awk -v extra="$patterns" '/^name="Web"/ { web = 1 } web && /^exclude_filter=/ { sub(/"$/, extra "\""); web = 0 } { print }' \
			"$ROOT/build/export_presets.cfg.bak" > "$ROOT/export_presets.cfg"
	fi
fi

"$ROOT/tools/godot.sh" --headless --import > "$log" 2>&1
"$ROOT/tools/godot.sh" --headless "--export-$mode" "$preset" "$out" >> "$log" 2>&1 || {
	cat "$log"
	exit 1
}
if grep -E "SCRIPT ERROR|^ERROR" "$log"; then
	echo "export logged errors; see $log" >&2
	exit 1
fi
# The loading screen's pictures sit beside the custom shell (web/shell.html).
[[ "$target" == web ]] && cp -R "$ROOT/web/loading" "$(dirname "$out")/"
listing="$(python3 "$ROOT/tools/build/pck_list.py" "$(dirname "$out")/index.pck" 2>/dev/null || true)"
for path in ${excluded[@]+"${excluded[@]}"}; do
	if grep -q "^$path/" <<< "$listing"; then
		echo "the web pack still holds $path" >&2
		exit 1
	fi
done
echo "exported $target ($mode): $out${excluded[*]+, without ${#excluded[@]} chapter folders}"
