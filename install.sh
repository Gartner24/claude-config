#!/usr/bin/env bash
# Install this config into ~/.claude. The counterpart to sync.sh, which only ever
# ran the other direction (live -> repo), so "restore on a new machine" was a claim
# the repo could not actually deliver.
#
# What this does NOT install: the frameworks (gstack, jjstack, get-shit-done-cc)
# and the Claude Code plugins. They manage themselves and are not vendored here -
# SKILLS.md documents how to install each. Run this first, then those.
#
#   ./install.sh            install
#   ./install.sh --dry-run  print what would happen, touch nothing
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIVE="$HOME/.claude"
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

run() { if [ "$DRY" = 1 ]; then echo "  would: $*"; else "$@"; fi; }
note() { echo "  $*"; }

echo "installing $REPO -> $LIVE"
[ "$DRY" = 1 ] && echo "(dry run)"

for d in agents rules hooks scripts commands skills; do
  run mkdir -p "$LIVE/$d"
done

# Copied: these are files the harness reads directly.
echo "copy:"
for d in agents rules; do
  note "$d/ ($(find "$REPO/$d" -type f | wc -l) files)"
  run cp -a "$REPO/$d/." "$LIVE/$d/"
done
for f in hooks/block-destructive.sh scripts/chroma-reaper.sh; do
  note "$f"
  run cp -a "$REPO/$f" "$LIVE/$f"
  run chmod +x "$LIVE/$f"
done

# Symlinked: editing the live file edits the repo, so there is one copy of the
# truth. This is how the existing install is already wired.
echo "symlink:"
for d in commands skills; do
  for src in "$REPO/$d"/*; do
    [ -e "$src" ] || continue
    name="$(basename "$src")"
    dst="$LIVE/$d/$name"
    [ -L "$dst" ] && [ "$(readlink -f "$dst")" = "$(readlink -f "$src")" ] && continue
    [ -e "$dst" ] && ! [ -L "$dst" ] && { note "SKIP $d/$name (a real file is already there)"; continue; }
    note "$d/$name"
    run ln -sfn "$src" "$dst"
  done
done

# settings.json hardcodes absolute paths to hook scripts. Substituting $HOME is
# what makes this repo installable by anyone, not just its author.
echo "settings.json:"
if [ -e "$LIVE/settings.json" ] && [ "$DRY" = 0 ]; then
  bak="$LIVE/settings.json.bak.$(date +%Y%m%d-%H%M%S)"
  cp "$LIVE/settings.json" "$bak"
  note "backed up existing -> $(basename "$bak")"
fi
n=$(grep -c '/home/santiago' "$REPO/settings.json" || true)
note "rewriting $n hardcoded path(s) to \$HOME"
if [ "$DRY" = 0 ]; then
  sed "s|/home/santiago|$HOME|g" "$REPO/settings.json" > "$LIVE/settings.json.tmp"
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$LIVE/settings.json.tmp"
  mv "$LIVE/settings.json.tmp" "$LIVE/settings.json"
fi
[ -e "$LIVE/CLAUDE.md" ] || run cp "$REPO/CLAUDE.md" "$LIVE/CLAUDE.md"

# Prove it took, rather than reporting success on faith.
echo "verify:"
if [ "$DRY" = 1 ]; then
  note "skipped (dry run)"
else
  bash "$LIVE/hooks/block-destructive.sh" --test >/dev/null \
    && note "guard hook: all self-checks passed" \
    || { echo "  guard hook SELF-CHECK FAILED - do not rely on it" >&2; exit 1; }
  python3 "$REPO/scripts/gen-agent-index.py" --check >/dev/null \
    && note "agent index: matches agents/" || note "agent index: DRIFTED (regenerate)"
  missing=0
  while read -r imp; do
    real="${imp/#@\~/$HOME}"
    [ -f "$real" ] || missing=$((missing + 1))
  done < <(grep -hoE '^@~/[^ ]+' "$REPO"/rules/ecc/*/index.md)
  [ "$missing" -eq 0 ] && note "rule imports: all resolve" || note "rule imports: $missing dangling"
fi

cat <<EOF

done. Still to install, none of it vendored here (see SKILLS.md):
  gstack / jjstack / get-shit-done-cc, and the Claude Code plugins.

Activate the rules per project by adding one line to that project's CLAUDE.md:
  @~/.claude/rules/ecc/<language>/index.md
EOF
