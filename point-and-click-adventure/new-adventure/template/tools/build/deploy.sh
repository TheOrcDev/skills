#!/usr/bin/env bash
# Deploys build/web (the browser build) to Vercel as a preview, or to
# production with --prod. Export first with tools/build/export.sh web. Set the
# team and project once, in VERCEL_SCOPE and VERCEL_PROJECT (or edit below).
# If the Vercel project is connected to git, a push deploys the repository,
# not the build: redeploy build/web with --prod afterwards, or disconnect git.
# Usage: tools/build/deploy.sh [--prod]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
web="$ROOT/build/web"
vercel=(bunx vercel@63.1.2)
scope="${VERCEL_SCOPE:?set VERCEL_SCOPE to the Vercel team slug}"
project="${VERCEL_PROJECT:?set VERCEL_PROJECT to the Vercel project name}"

[[ -f "$web/index.pck" ]] || { echo "no web build; run tools/build/export.sh web" >&2; exit 1; }

# The export wipes build/web, and with it the project link. Linking writes a
# .env.local with an OIDC token, which must never be uploaded.
printf '.env*\n.gitignore\n.vercel\n' > "$web/.vercelignore"
[[ -f "$web/.vercel/project.json" ]] || "${vercel[@]}" link --cwd "$web" --scope "$scope" --project "$project" --yes
"${vercel[@]}" deploy --cwd "$web" --yes "$@"
