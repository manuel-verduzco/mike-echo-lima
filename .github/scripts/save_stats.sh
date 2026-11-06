#!/usr/bin/env bash
# Saves a fresh stats.json onto the "stats-data" branch (creating the branch the first time).
#
# Why a separate branch: a commit on main makes GitHub rebuild the website, and Pages only allows
# about 10 rebuilds an hour. Snapshots every 5 minutes would hit that, and they would bury your real
# changes in "Update stats" commits. On its own branch they cost nothing and the history of the
# numbers stays tidy. The stats page reads the file straight from that branch.
#
# Run from the root of the repository (the update-stats workflow does this).
set -euo pipefail

BRANCH="stats-data"
DATA_DIR="${DATA_DIR:-../stats-data-worktree}"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

rm -rf "$DATA_DIR"
git worktree prune
git fetch --quiet origin "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH" 2>/dev/null || true

if git rev-parse --verify --quiet "refs/remotes/origin/$BRANCH" >/dev/null; then
  git worktree add --quiet --detach "$DATA_DIR" "origin/$BRANCH"
  git -C "$DATA_DIR" checkout --quiet -B "$BRANCH" "origin/$BRANCH"
else
  echo "First run: creating the $BRANCH branch."
  git worktree add --quiet --detach "$DATA_DIR"
  git -C "$DATA_DIR" checkout --quiet --orphan "$BRANCH"
  git -C "$DATA_DIR" rm -rfq .
  cat > "$DATA_DIR/README.md" <<'TXT'
# stats-data

This branch only holds `stats.json`, a snapshot of how many times each sentence has landed.
It is rewritten automatically by the "Update stats" workflow on the main branch (about every
5 minutes, and only when something changed). The stats page reads the file from here.
Please do not edit it by hand.
TXT
fi

python3 update_stats.py --out "$DATA_DIR/stats.json"

cd "$DATA_DIR"
git add -A
if git diff --cached --quiet; then
  echo "Nothing new to save."
else
  git commit --quiet -m "Update stats"
  git push --quiet origin "$BRANCH"
  echo "Saved a new snapshot."
fi
