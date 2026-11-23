#!/usr/bin/env bash
# Local evidence for an agent worktree. Datasets and artifacts are never in Git.
#
#   seed            clone the owner's artifacts/ and data/ into this worktree (APFS clones,
#                   no extra disk space), then add agent evidence from $ROOT/evidence/ that
#                   the owner does not have yet. Read only for the owner's checkout.
#   save <dir>      copy the new directory artifacts/<dir> of this worktree to the evidence
#                   store $ROOT/evidence/<dir>. Refuses if it exists there or in the owner's
#                   checkout: frozen evidence is never overwritten.
#   promote <dir>   release-merger only, after the PR that cites <dir> is merged: clone
#                   $ROOT/evidence/<dir> into the owner's artifacts/<dir>. Skips if present.
#   list            evidence store directories, newest first.
#   clean           remove artifacts/ and data/ from this worktree.
#
# Run from the root of an agent worktree.
set -euo pipefail

ROOT="${HELIO24_AGENTS_ROOT:-/Users/esma/Projects/helio24_orchestra_work}"
OWNER="${HELIO24_OWNER_CHECKOUT:-/Users/esma/Developer/Helio24-restored}"
STORE="$ROOT/evidence"
cmd="${1:?usage: evidence.sh seed|save <dir>|promote <dir>|list|clean}"

case "$PWD" in
  "$ROOT"/work/*) ;;
  *) echo "run from an agent worktree under $ROOT/work" >&2; exit 2 ;;
esac

valid() { [[ "$1" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "bad directory name: $1" >&2; exit 2; }; }

case "$cmd" in
  seed)
    mkdir -p artifacts data
    for d in artifacts data; do
      if [ -d "$OWNER/$d" ]; then
        for src in "$OWNER/$d"/* "$OWNER/$d"/.[!.]*; do
          [ -e "$src" ] || continue
          name="$(basename "$src")"
          [ "$name" = .DS_Store ] && continue
          [ -e "$d/$name" ] || cp -Rc "$src" "$d/$name"
        done
      fi
    done
    for src in "$STORE"/*; do
      [ -d "$src" ] || continue
      name="$(basename "$src")"
      [ -e "artifacts/$name" ] || cp -Rc "$src" "artifacts/$name"
    done
    echo "seeded: $(ls artifacts | wc -l | tr -d ' ') artifact entries, $(ls data | wc -l | tr -d ' ') data entries"
    ;;
  save)
    d="${2:?save needs a directory name under artifacts/}"; valid "$d"
    [ -d "artifacts/$d" ] || { echo "artifacts/$d does not exist" >&2; exit 1; }
    if [ -e "$STORE/$d" ] || [ -e "$OWNER/artifacts/$d" ]; then
      echo "refused: $d already exists as frozen evidence; use a new revision name (_r2, _r3)" >&2; exit 1
    fi
    cp -Rc "artifacts/$d" "$STORE/$d"
    find "$STORE/$d" -type f -exec chmod a-w {} +
    echo "saved $STORE/$d"
    ;;
  promote)
    d="${2:?promote needs a directory name}"; valid "$d"
    [ -d "$STORE/$d" ] || { echo "not in the evidence store: $d" >&2; exit 1; }
    if [ -e "$OWNER/artifacts/$d" ]; then echo "skipped: $d already in the owner's artifacts"; exit 0; fi
    cp -Rc "$STORE/$d" "$OWNER/artifacts/$d"
    chmod -R u+w "$OWNER/artifacts/$d"
    echo "promoted $d"
    ;;
  list)
    ls -1t "$STORE" 2>/dev/null || true
    ;;
  clean)
    rm -rf artifacts data
    echo "cleaned"
    ;;
  *)
    echo "unknown command: $cmd" >&2; exit 2 ;;
esac
