#!/usr/bin/env bash
# Pull the live ~/.claude config into this repo. Run before committing.
# Only copies the hand-maintained parts - frameworks (gstack/jjstack/plugins)
# manage themselves and are documented, not vendored.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
# CLAUDE_LIVE_DIR is for the self checks only: they sync a temp live tree, never ~/.claude.
LIVE="${CLAUDE_LIVE_DIR:-$HOME/.claude}"
NAMES=(python3 "$REPO/scripts/private-names.py")

# Spec 0013: private names (~/.claude/private/names.txt) never reach this public repo.
# Every source is checked BEFORE anything is copied, so a refused sync leaves the repo
# byte for byte unchanged. The settings files are stripped into a temp dir first (autoMode
# and every name bearing array string or object key out); the stripped entries become the
# private fragments install.sh merges back. Temp files also mean a malformed settings.json
# can never leave a committable 0-byte file here, as `jq ... > dest` once did.
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
fail=0
"${NAMES[@]}" strip-settings "$LIVE/settings.json" "$tmp/settings.json" "$tmp/private-settings.json" || fail=1
"${NAMES[@]}" strip-settings "$LIVE/settings.local.json" "$tmp/settings.local.json" "$tmp/private-settings.local.json" || fail=1
"${NAMES[@]}" check "$LIVE/CLAUDE.md" "$LIVE/agents" "$LIVE/rules" \
  "$LIVE/hooks/block-destructive.sh" "$LIVE/hooks/review-stack-pre-push" "$LIVE/hooks/plain-panel.py" \
  "$LIVE/scripts/chroma-reaper.sh" || fail=1
if [ "$fail" = 1 ]; then
  echo "sync refused: a private name (or no names list) in the sources above; nothing was copied" >&2
  exit 1
fi
mv "$tmp/private-settings.json" "$LIVE/private/settings.json"
mv "$tmp/private-settings.local.json" "$LIVE/private/settings.local.json"

cp "$LIVE/CLAUDE.md"            "$REPO/CLAUDE.md"
mv "$tmp/settings.json"         "$REPO/settings.json"
mv "$tmp/settings.local.json"   "$REPO/settings.local.json"

# ponytail: copy-over, no delete - stale files show up in git status, delete by hand
mkdir -p "$REPO/agents" "$REPO/rules"
cp -a "$LIVE/agents/." "$REPO/agents/"
cp -a "$LIVE/rules/."  "$REPO/rules/"

# Hooks + scripts that are real files here (the rest are framework symlinks).
mkdir -p "$REPO/hooks" "$REPO/scripts"
cp "$LIVE/hooks/block-destructive.sh"     "$REPO/hooks/"
cp "$LIVE/hooks/review-stack-pre-push" "$REPO/hooks/"
cp "$LIVE/hooks/plain-panel.py"        "$REPO/hooks/"
cp "$LIVE/hooks/context-monitor.js"    "$REPO/hooks/"
cp "$LIVE/scripts/chroma-reaper.sh"   "$REPO/scripts/"


# cp -a never deletes, and the header's claim that stale files show up in `git status`
# is only true for MODIFIED files. A file deleted from ~/.claude stays committed here
# with no signal at all - which for a public repo means a file removed because it became
# sensitive would remain published. Name the orphans instead of trusting git status.
orphans=0
for d in agents rules; do
  while IFS= read -r rel; do
    [ -e "$LIVE/$d/$rel" ] && continue
    orphans=$((orphans + 1))
    [ "$orphans" -le 10 ] && \
      echo "  ORPHAN: $d/$rel is tracked here but gone from $LIVE/$d - delete it by hand"
  done < <(cd "$REPO/$d" && find . -type f -printf '%P\n')
done
[ "$orphans" -gt 10 ] && echo "  ... and $((orphans - 10)) more"
[ "$orphans" -gt 0 ] && echo "  $orphans orphan(s); nothing was auto-deleted. A full list means $LIVE is incomplete, not that this repo is stale."

# Last line of defence: a name already in a repo-only file (README, a doc) is caught here.
# The copy stays; the pre-commit hook still blocks the commit.
if ! (cd "$REPO" && "${NAMES[@]}" check); then
  echo "sync done, but the repo holds a private name (above); reword it before committing" >&2
  exit 1
fi

echo "synced. review with: git -C $REPO status"
