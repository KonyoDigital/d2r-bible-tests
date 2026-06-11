#!/bin/bash
# autosnap.sh — bible.html lost-update safeguard (CC 2026-06-11).
#
# Fired by launchd (com.konyo.d2r-bible-autosnap) whenever bible.html changes
# on disk, NO MATTER WHO wrote it (Claude Desktop, Claude Code, Konyo, anyone).
# Commits the new content to the LOCAL-ONLY ref refs/snapshots/bible using git
# plumbing — it never touches main, the index, or the working tree, and plain
# `git push` never publishes it (the repo is PUBLIC; snapshots must stay local).
#
# Why: the 2026-06-11 incident — Desktop edits the live file without committing,
# CC commits to git; two read-modify-write lineages silently lost-updated each
# other. With every on-disk save captured here, divergence is always a visible,
# mergeable history instead of vanished work.
#
# Inspect:  git log refs/snapshots/bible --oneline
# Recover:  git show refs/snapshots/bible:bible.html > recovered.html
# Diff:     git diff refs/snapshots/bible main -- bible.html

set -u
REPO="/Users/konyo/d2r_bible_tests"
FILE="bible.html"
REF="refs/snapshots/bible"
LOG="$REPO/.autosnap.log"

cd "$REPO" || exit 1
[ -f "$FILE" ] || { echo "$(date '+%F %T') SKIP: $FILE missing" >> "$LOG"; exit 0; }

# settle: editors often write in bursts (write-rename, multi-save)
sleep 2

blob=$(git hash-object -w "$FILE") || exit 1
prev_blob=$(git rev-parse -q --verify "$REF:$FILE" 2>/dev/null || echo "")

if [ "$blob" = "$prev_blob" ]; then
  echo "$(date '+%F %T') NOOP: content unchanged ($blob)" >> "$LOG"
  exit 0
fi

parent=$(git rev-parse -q --verify "$REF" 2>/dev/null || echo "")
tree=$(printf '100644 blob %s\t%s\n' "$blob" "$FILE" | git mktree) || exit 1

# annotate who likely wrote it: EDIT_LOCK owner if claimed, else "unclaimed"
owner="unclaimed"
[ -f "$FILE.EDIT_LOCK" ] && owner=$(head -1 "$FILE.EDIT_LOCK" | tr -d '\n' | cut -c1-80)

msg="autosnap $(date '+%F %T') md5=$(md5 -q "$FILE") lock=[$owner]"
if [ -n "$parent" ]; then
  commit=$(git commit-tree "$tree" -p "$parent" -m "$msg")
else
  commit=$(git commit-tree "$tree" -m "$msg")
fi
git update-ref "$REF" "$commit"
echo "$(date '+%F %T') SNAP: $commit $msg" >> "$LOG"
