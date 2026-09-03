#!/usr/bin/env bash
# Pull the live ~/.claude config into this repo. Run before committing.
# Only copies the hand-maintained parts - frameworks (gstack/jjstack/plugins)
# manage themselves and are documented, not vendored.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
LIVE="$HOME/.claude"

cp "$LIVE/CLAUDE.md"            "$REPO/CLAUDE.md"
# autoMode carries client repo names, env-file names, and internal domains - this repo is public.
jq 'del(.autoMode)' "$LIVE/settings.json" > "$REPO/settings.json"
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
git -C "$LIVE/skills/jjstack" diff -- hooks/auto-approve-safe.sh \
  > "$REPO/hooks/jjstack-auto-approve-safe.patch"

echo "synced. review with: git -C $REPO status"
