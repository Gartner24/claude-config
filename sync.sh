#!/usr/bin/env bash
# Pull the live ~/.claude config into this repo. Run before committing.
# Only copies the hand-maintained parts - frameworks (gstack/jjstack/plugins)
# manage themselves and are documented, not vendored.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
LIVE="$HOME/.claude"

cp "$LIVE/CLAUDE.md"            "$REPO/CLAUDE.md"
# autoMode carries client repo names, env-file names, and internal domains - this repo is public.
# Temp file first: `jq ... > dest` truncates dest BEFORE jq runs, so a malformed
# settings.json or a missing jq left a committable 0-byte file in a public repo.
jq 'del(.autoMode)' "$LIVE/settings.json" > "$REPO/settings.json.tmp"
mv "$REPO/settings.json.tmp" "$REPO/settings.json"
cp "$LIVE/settings.local.json"  "$REPO/settings.local.json"

# ponytail: copy-over, no delete - stale files show up in git status, delete by hand
mkdir -p "$REPO/agents" "$REPO/rules"
cp -a "$LIVE/agents/." "$REPO/agents/"
cp -a "$LIVE/rules/."  "$REPO/rules/"

# Hooks + scripts that are real files here (the rest are framework symlinks).
mkdir -p "$REPO/hooks" "$REPO/scripts"
cp "$LIVE/hooks/block-destructive.sh" "$REPO/hooks/"
cp "$LIVE/scripts/chroma-reaper.sh"   "$REPO/scripts/"

# Local tweak to jjstack's hook, kept as a patch so it survives a jjstack upgrade.
# Only overwrite when there is actually a diff: redirecting straight into the file
# truncated it to 0 bytes whenever jjstack was absent or had been reset to stock,
# silently deleting the tracked tweak this line exists to preserve.
if _patch=$(git -C "$LIVE/skills/jjstack" diff -- hooks/auto-approve-safe.sh 2>/dev/null) \
   && [ -n "$_patch" ]; then
  printf '%s\n' "$_patch" > "$REPO/hooks/jjstack-auto-approve-safe.patch"
else
  echo "  note: no jjstack hook diff (absent or reset to stock) - kept the tracked patch"
fi

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

echo "synced. review with: git -C $REPO status"
