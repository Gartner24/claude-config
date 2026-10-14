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
# CLAUDE_LIVE_DIR is for the self checks only: they install into a temp live tree.
LIVE="${CLAUDE_LIVE_DIR:-$HOME/.claude}"
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
for f in hooks/block-destructive.sh hooks/review-stack-pre-push hooks/plain-panel.py scripts/chroma-reaper.sh; do
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

# The runner goes on PATH as a copy outside the repo (spec 0020 AC-12). It used to link into
# runner/, and the SessionStart hook naming wf then made every wf run call's guard deny runner/.
# `next` is the same file; called by that name it acts as `wf next`.
echo "runner:"
# Spec 0020 AC-3: under `wf`, install.sh runs into a stage and writes nothing outside $LIVE; wf swaps
# the runner copy, the bin links and the git hooks in itself, with the same code.
if [ -n "${WF_STAGE:-}" ]; then
  note "staged: bin links and git hooks left to wf"
else
BIN="$HOME/.local/bin"
run mkdir -p "$BIN"
# A scratch copy of this script with no runner/ (the spec 0013 self checks) installs the rest.
[ -d "$REPO/runner" ] && python3 -B -c 'import sys; sys.path.insert(0, sys.argv[1] + "/runner"); import finish; finish.install_runner(sys.argv[1], sys.argv[2], sys.argv[3] == "1")' "$REPO" "$HOME" "$DRY"
# Spec 0015 AC-6: /sync runs spec-paths to warn about stale accepted specs.
if [ -e "$BIN/spec-paths" ] && ! [ -L "$BIN/spec-paths" ]; then
  note "SKIP spec-paths (a real file is already at $BIN/spec-paths)"
else
  note "spec-paths -> scripts/spec-paths.py"
  run ln -sfn "$REPO/scripts/spec-paths.py" "$BIN/spec-paths"
fi
# Spec 0023 AC-13: the cheap worker tier.
if [ -e "$BIN/fb-ask" ] && ! [ -L "$BIN/fb-ask" ]; then
  note "SKIP fb-ask (a real file is already at $BIN/fb-ask)"
else
  note "fb-ask -> scripts/fb-ask.py"
  run ln -sfn "$REPO/scripts/fb-ask.py" "$BIN/fb-ask"
fi
fi

# settings.json hardcodes absolute paths to hook scripts. Substituting $HOME is
# what makes this repo installable by anyone, not just its author.
echo "settings.json:"
# Spec 0019 AC-9: sync.sh strips autoMode from the repo copy, so every install used to
# drop yours. Read it before the file is replaced, write it back after the private merge.
keep_auto=""
if [ -e "$LIVE/settings.json" ]; then
  if ! keep_auto=$(python3 -c '
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except (OSError, ValueError) as e:
    print(e)
    sys.exit(1)
if isinstance(d, dict) and "autoMode" in d:
    print(json.dumps(d["autoMode"]))
' "$LIVE/settings.json"); then
    note "autoMode not kept: $keep_auto"
    keep_auto=""
  fi
fi
[ -n "$keep_auto" ] && [ "$DRY" = 1 ] && note "would keep autoMode"
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

# Spec 0013: sync.sh strips name bearing entries out of both settings files into
# ~/.claude/private/. Merging them back is what keeps a reinstall from silently dropping
# the private deny rules. A public reader has no fragment and gets the public settings.
echo "private settings:"
for f in settings.json settings.local.json; do
  frag="$LIVE/private/$f"
  if [ ! -e "$frag" ]; then
    note "$f: no private settings fragment, private entries not installed"
  elif [ "$DRY" = 1 ]; then
    note "would: python3 scripts/private-names.py merge-settings $LIVE/$f $frag (paths swapped to \$HOME)"
  else
    note "$f: merging $frag"
    sed "s|/home/santiago|$HOME|g" "$frag" | python3 "$REPO/scripts/private-names.py" merge-settings "$LIVE/$f" -
  fi
done
if [ -n "$keep_auto" ] && [ "$DRY" = 0 ]; then
  python3 -c '
import json, os, sys
p = sys.argv[1]
d = json.load(open(p))
d["autoMode"] = json.loads(sys.argv[2])
with open(p + ".tmp", "w") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
os.replace(p + ".tmp", p)
' "$LIVE/settings.json" "$keep_auto"
  note "kept your autoMode"
fi

# The names list exists only on the author's machine, so this part is this repo only:
# private ignore lines go to .git/info/exclude (never the public .gitignore) and the
# commit hooks refuse any commit that would bring a name back.
echo "private names:"
if [ -e "$LIVE/private/names.txt" ]; then
  excl="$(git -C "$REPO" rev-parse --git-path info/exclude)"
  hooks="$(git -C "$REPO" rev-parse --git-path hooks)"
  case "$excl" in /*) ;; *) excl="$REPO/$excl"; hooks="$REPO/$hooks" ;; esac
  add=()
  if [ -e "$LIVE/private/gitignore" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      [ -n "$line" ] || continue
      [ -e "$excl" ] && grep -qxF -- "$line" "$excl" && continue
      add+=("$line")
    done < "$LIVE/private/gitignore"
  fi
  # the lines themselves hold names, so only their count is printed
  note "exclude: ${#add[@]} private ignore line(s) to add"
  if [ "${#add[@]}" -gt 0 ] && [ "$DRY" = 0 ]; then
    mkdir -p "$(dirname "$excl")"
    printf '%s\n' "${add[@]}" >> "$excl"
  fi
  # Copies, never links: a wf run call may edit the tracked checker, and a linked hook
  # used to run that edit outside the sandbox at the next commit (spec 0013 AC-7).
  checker="$REPO/scripts/private-names.py"
  [ -n "${WF_STAGE:-}" ] || run mkdir -p "$hooks"
  for h in pre-commit commit-msg; do
    [ -n "${WF_STAGE:-}" ] && break
    dst="$hooks/$h"
    act=""
    if [ -L "$dst" ]; then
      [ "$(readlink -f "$dst")" = "$(readlink -f "$checker")" ] && act=refreshed
    elif [ -f "$dst" ] && [ -x "$dst" ] && cmp -s "$dst" "$checker"; then
      note "$h: up to date"
      continue
    elif [ -f "$dst" ] && [ "$(sed -n 2p "$dst")" = "$(sed -n 2p "$checker")" ]; then
      act=refreshed
    elif [ ! -e "$dst" ]; then
      act=copied
    fi
    if [ -z "$act" ]; then
      note "hook exists, not replaced: $h"
    elif [ "$DRY" = 1 ]; then
      note "would: $h: $act"
    else
      # rm first so the copy can never write through a link into the tracked checker
      rm -f "$dst"
      cp "$checker" "$dst"
      chmod 0755 "$dst"
      note "$h: $act"
    fi
  done
else
  note "no private names list, exclude lines and commit hooks skipped"
fi

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
  bash "$REPO/skills/design/scripts/test-ledger.sh" >/dev/null 2>&1 \
    && note "design ledger + Stop hook: 37 assertions pass" \
    || { echo "  DESIGN LEDGER SELF-CHECK FAILED - the Stop hook may block or leak" >&2; exit 1; }
  node "$REPO/skills/design/scripts/build-ramp.mjs" --check >/dev/null 2>&1 \
    && note "colour ramp: solver targets and emitted pairs meet AA" \
    || { echo "  RAMP SELF-CHECK FAILED - generated palettes may ship below AA" >&2; exit 1; }
  # The suite builds its own temp homes; the stage or live dir this install writes must not leak into it.
  env -u WF_STAGE -u CLAUDE_LIVE_DIR python3 -m unittest discover -s "$REPO/runner/tests" </dev/null >/dev/null 2>&1 \
    && note "runner: unittest suite passes" \
    || { echo "  RUNNER SELF-CHECK FAILED - run: python3 -m unittest discover -s runner/tests" >&2; exit 1; }
  python3 "$REPO/scripts/spec-paths.py" --test >/dev/null 2>&1 \
    && note "spec-paths: all self-checks passed" \
    || { echo "  SPEC-PATHS SELF-CHECK FAILED - run: python3 scripts/spec-paths.py --test" >&2; exit 1; }
  python3 "$REPO/scripts/fb-ask.py" --test </dev/null >/dev/null 2>&1 \
    && note "fb-ask: all self-checks passed" \
    || { echo "  FB-ASK SELF-CHECK FAILED - run: python3 scripts/fb-ask.py --test" >&2; exit 1; }
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
