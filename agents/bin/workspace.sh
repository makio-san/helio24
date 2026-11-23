#!/usr/bin/env bash
# Give an agent a clean worktree of origin/main, outside the owner's own checkout.
#
# Usage: bash agents/bin/workspace.sh <name>
# Prints the worktree path: $HELIO24_AGENTS_ROOT/work/<name>
# (HELIO24_AGENTS_ROOT defaults to /Users/esma/Projects/helio24_orchestra_work)
#
# Every run starts from the newest origin/<ref> with no local changes and no ignored
# files: artifacts/ and data/ are empty until `bash agents/bin/evidence.sh seed` clones them.
set -euo pipefail

NAME="${1:?usage: workspace.sh <name>}"
ROOT="${HELIO24_AGENTS_ROOT:-/Users/esma/Projects/helio24_orchestra_work}"
BASE="$ROOT/base"
WORK="$ROOT/work/$NAME"
REF="origin/${HELIO24_REF:-main}"  # another branch only when testing agents before a merge

mkdir -p "$ROOT/work" "$ROOT/logs" "$ROOT/evidence" "$ROOT/tmp"
if [ ! -d "$BASE/.git" ]; then
  git clone -q https://github.com/makio-san/helio24.git "$BASE"
fi
git -C "$BASE" fetch -q --prune origin
git -C "$BASE" worktree prune

if [ ! -e "$WORK/.git" ]; then
  git -C "$BASE" worktree add -q --detach "$WORK" "$REF"
fi

cd "$WORK"
git checkout -q -f --detach "$REF"
git reset -q --hard "$REF"
git clean -fdxq
echo "$WORK"
