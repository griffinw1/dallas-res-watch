#!/usr/bin/env bash
# Check some platforms, render, commit and push results.json + site/.
# Used by the GitHub workflow (resy,sevenrooms) and by the Mac (opentable,tock).
#
#   scripts/publish.sh resy,sevenrooms,phone,walkin,unknown     # cloud
#   scripts/publish.sh opentable,tock                           # Mac
#
# Each side only overwrites rows for the platforms it owns. If the push races the
# other side, it rebases and re-merges the other side's rows from origin, so neither
# side clobbers the other. Set NO_PUSH=1 to only commit locally.
set -euo pipefail
OWN="${1:?usage: publish.sh <comma platforms> [extra check.py args]}"; shift || true
cd "$(dirname "$0")/.."
PY="${PYTHON:-$( [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3 )}"
ALL="resy,sevenrooms,opentable,tock,phone,walkin,unknown"
OTHER=$(echo "$ALL" | tr ',' '\n' | grep -vxF -f <(echo "$OWN" | tr ',' '\n') | paste -sd, -)
HAS_REMOTE=$(git remote | head -1 || true)
BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ -n "$HAS_REMOTE" ] && [ -z "${NO_PUSH:-}" ]; then git pull -q --rebase --autostash || true; fi
[ -f results.json ] && cp results.json .prev.json || echo '{}' > .prev.json

"$PY" check.py --platforms "$OWN" "$@"
"$PY" render.py
"$PY" diff.py .prev.json results.json
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && "$PY" diff.py .prev.json results.json --markdown >> "$GITHUB_STEP_SUMMARY"

git add results.json site/index.html
git commit -qm "availability: $OWN $(date -u +%FT%H:%MZ)" || { echo "nothing changed"; exit 0; }
[ -z "$HAS_REMOTE" ] || [ -n "${NO_PUSH:-}" ] && { echo "committed locally (no push)"; exit 0; }

for i in 1 2 3 4; do
  git push -q origin "$BRANCH" && { echo "pushed"; exit 0; }
  echo "push raced; re-merging (attempt $i)"
  git fetch -q origin
  git rebase -q -X theirs "origin/$BRANCH" || { git rebase --abort; exit 1; }
  # Our rows won the rebase wholesale; put back the other side's fresh rows from origin.
  git show "origin/$BRANCH:results.json" > .theirs.json
  [ -n "$OTHER" ] && "$PY" check.py --platforms "$OTHER" --merge-from .theirs.json
  "$PY" render.py
  git add results.json site/index.html
  git commit -q --amend --no-edit || true
  sleep $((i * 5))
done
echo "push failed after retries"; exit 1
