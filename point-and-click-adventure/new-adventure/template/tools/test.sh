#!/usr/bin/env bash
# Headless import, GUT tests and content lint. Exits non-zero on any failure.
# Logs go to build/test-logs/.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT="$ROOT/tools/godot.sh"
LOGS="$ROOT/build/test-logs"
mkdir -p "$LOGS"
status=0

echo "== import"
"$GODOT" --headless --import > "$LOGS/import.log" 2>&1 || status=1
if grep -E "SCRIPT ERROR|^ERROR" "$LOGS/import.log"; then
	status=1
fi

echo "== tests"
"$GODOT" --headless --script res://addons/gut/gut_cmdln.gd -gdir=res://test -ginclude_subdirs -gpre_run_script=res://test/hooks/pre_run.gd -gexit 2>&1 | tee "$LOGS/gut.log"
[[ ${PIPESTATUS[0]} -eq 0 ]] || status=1

echo "== lint"
"$GODOT" --headless --script res://addons/adv_tools/lint.gd 2>&1 | tee "$LOGS/lint.log"
[[ ${PIPESTATUS[0]} -eq 0 ]] || status=1

if [[ $status -eq 0 ]]; then echo "== ALL PASSED"; else echo "== FAILED (logs in $LOGS)"; fi
exit $status
