#!/usr/bin/env bash
# Install this config into ~/.claude. The counterpart to tools/bin/sync.sh, which only ever
# ran the other direction (live -> repo), so "restore on a new machine" was a claim
# the repo could not actually deliver.
#
# What this does NOT install: the frameworks (gstack, jjstack)
# and the Claude Code plugins. They manage themselves and are not vendored here -
# docs/guides/SETUP.md documents how to install each. Run this first, then those.
#
#   tools/bin/install.sh                     install the active profile (state/profile.json, else engineer)
#   tools/bin/install.sh --profile <name>    install that profile (spec 0081)
#   tools/bin/install.sh --accept-overwrite  overwrite the live changes the check lists
#   tools/bin/install.sh --dry-run           print what would happen, touch nothing
set -euo pipefail

# Spec 0048 AC-1, 0077 AC-12: this script lives in tools/bin/, the repo is two folders up.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# CLAUDE_LIVE_DIR is for the self checks only: they install into a temp live tree.
LIVE="${CLAUDE_LIVE_DIR:-$HOME/.claude}"
DRY=0
ACCEPT=0
PROFILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --accept-overwrite) ACCEPT=1 ;;
    --profile)
      [ $# -gt 1 ] || { echo "install.sh: --profile needs a name" >&2; exit 2; }
      PROFILE="$2"; shift ;;
    --profile=*) PROFILE="${1#*=}" ;;
    *) echo "install.sh: unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
CONFIG=(python3 "$REPO/tools/bin/claude-config.py")

run() { if [ "$DRY" = 1 ]; then echo "  would: $*"; else "$@"; fi; }
note() { echo "  $*"; }
# Spec 0082 AC-2: GNU readlink's resolve flag is missing on older Macs; python3 is there (install needs it anyway).
realp() { python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"; }

# Spec 0081 AC-2, AC-4: an unknown profile exits 2 before anything is written.
read -r PROFILE from < <("${CONFIG[@]}" profile-resolve ${PROFILE:+"$PROFILE"}) || exit 2
[ -n "$PROFILE" ] || exit 2

echo "installing $REPO -> $LIVE"
echo "profile: $PROFILE (from $from)"
[ "$DRY" = 1 ] && echo "(dry run)"

# Spec 0036 AC-4: a dry run used to pass a settings file that does not parse; only the real
# install caught it, after the copies. Refuse first, in both modes, naming the file.
for f in settings.json settings.local.json; do
  [ -e "$REPO/claude-home/$f" ] || continue
  if ! err=$(python3 -c 'import json, sys; json.load(open(sys.argv[1]))' "$REPO/claude-home/$f" 2>&1); then
    echo "refused: $REPO/claude-home/$f does not parse: ${err##*$'\n'}" >&2
    exit 1
  fi
done

# Spec 0081 AC-2: the profile is built whole in a staging folder first, so a failed build never leaves half a profile
# live. It holds every file install copies: CLAUDE.md, agents/, rules/, rules-on-demand/, the copied hooks, MAP.md
# and settings.json.
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
"${CONFIG[@]}" stage "$PROFILE" "$STAGE" || { echo "refused: profile $PROFILE did not build (above)" >&2; exit 2; }

# settings.json hardcodes absolute paths to hook scripts. Substituting $HOME is
# what makes this repo installable by anyone, not just its author (the stage step does it).
echo "settings.json:"
n=$(grep -c '/home/santiago' "$REPO/claude-home/settings.json" || true)
note "rewriting $n hardcoded path(s) to \$HOME"
# Spec 0019 AC-9: sync.sh strips autoMode from the repo copy, so every install used to
# drop yours. It is read from the live file and written into the built one, before the private merge (AC-17).
if [ -e "$LIVE/settings.json" ]; then
  if ! msg=$(python3 -c '
import json, os, sys
try:
    d = json.load(open(sys.argv[1]))
except (OSError, ValueError) as e:
    print(e)
    sys.exit(1)
if isinstance(d, dict) and "autoMode" in d:
    p = sys.argv[2]
    s = json.load(open(p))
    s["autoMode"] = d["autoMode"]
    with open(p + ".tmp", "w") as f:
        json.dump(s, f, indent=2)
        f.write("\n")
    os.replace(p + ".tmp", p)
    print("kept your autoMode")
' "$LIVE/settings.json" "$STAGE/settings.json"); then
    note "autoMode not kept: $msg"
  elif [ -n "$msg" ] && [ "$DRY" = 1 ]; then
    note "would keep autoMode"
  elif [ -n "$msg" ]; then
    note "$msg"
  fi
fi

# Spec 0013: sync.sh strips name bearing entries out of both settings files into
# ~/.claude/private/. Merging them back is what keeps a reinstall from silently dropping
# the private deny rules. A public reader has no fragment and gets the public settings.
frag="$LIVE/private/settings.json"
if [ -e "$frag" ]; then
  note "merging $frag into the built file (private-names.py merge-settings, paths swapped to \$HOME)"
  sed "s|/home/santiago|$HOME|g" "$frag" | python3 "$REPO/tools/scripts/private-names.py" merge-settings "$STAGE/settings.json" -
else
  note "no private settings fragment, private entries not installed"
fi
# Spec 0081 AC-23: hook scripts in private/hooks/ are never copied; a private hook whose file is missing is named.
if [ -e "$frag" ]; then
  python3 - "$frag" "$HOME" <<'PY' || true
import json, os, shlex, sys
home = sys.argv[2]
try:
    d = json.loads(open(sys.argv[1]).read().replace("/home/santiago", home))
except (OSError, ValueError):
    sys.exit(0)
for groups in (d.get("hooks") or {}).values():
    for g in groups if isinstance(groups, list) else []:
        for c in (g.get("hooks") or []) if isinstance(g, dict) else []:
            try:
                words = shlex.split(c.get("command", "")) if isinstance(c, dict) else []
            except ValueError:
                continue
            if len(words) > 1 and os.path.basename(words[0]) in ("bash", "sh", "zsh", "python", "python3", "node"):
                words = words[1:]
            path = os.path.expanduser(words[0].replace("$HOME", home)) if words else ""
            if path.startswith("/") and not os.path.exists(path):
                print(f"  private hook missing: {path}")
PY
fi

# Spec 0081 AC-5: never overwrite a live change silently. Every live file the build would change, and every live rule
# it would not write, is listed; with any, nothing is written unless --accept-overwrite (a dry run only lists them).
echo "overwrite check:"
rc=0
"${CONFIG[@]}" overwrite "$STAGE" || rc=$?
if [ "$rc" = 3 ] && [ "$DRY" = 0 ] && [ "$ACCEPT" = 0 ]; then
  echo "refused: live changes above would be overwritten; carry them into the repo (sync) or rerun with --accept-overwrite" >&2
  exit 3
fi
[ "$rc" = 0 ] || [ "$rc" = 3 ] || { echo "refused: the overwrite check failed (above)" >&2; exit 1; }

for d in agents rules rules-on-demand hooks scripts commands skills workflows; do
  run mkdir -p "$LIVE/$d"
done

# Copied: these are files the harness reads directly. Spec 0081 AC-2: CLAUDE.md is always installed now.
echo "copy:"
note "CLAUDE.md"
run cp "$STAGE/CLAUDE.md" "$LIVE/CLAUDE.md"
for d in agents rules rules-on-demand; do
  [ -d "$STAGE/$d" ] || continue
  note "$d/ ($(find "$STAGE/$d" -type f | wc -l | tr -d ' ') files)"
  run cp -a "$STAGE/$d/." "$LIVE/$d/"
done
# Spec 0077 AC-7: cp -a never deletes, so a rule moved out of rules/ kept auto loading live. A live file in either
# folder the build did not write is moved to a dated backup folder, and named here.
stamp="$(date +%Y-%m-%d)"
for d in rules rules-on-demand; do
  [ -d "$LIVE/$d" ] || continue
  while IFS= read -r rel; do
    [ -e "$STAGE/$d/$rel" ] && continue
    note "live only: $d/$rel -> backups/rules/$stamp/$d/$rel"
    dest="$LIVE/backups/rules/$stamp/$d/$rel"
    # an earlier same-day backup of this path is kept: the next one gets a numbered suffix
    n=0
    while [ -e "$dest" ]; do n=$((n + 1)); dest="$LIVE/backups/rules/$stamp/$d/$rel.$n"; done
    run mkdir -p "$(dirname "$dest")"
    run mv "$LIVE/$d/$rel" "$dest"
  done < <(cd "$LIVE/$d" && find . -type f | sed 's|^\./||')
done
# Spec 0077 AC-6: MAP.md, the pointer back to this repo, never auto loaded. Spec 0048 AC-11 and AC-5: the reminder
# and your own hooks, which a scratch copy of this script (the self checks) may lack.
for f in MAP.md hooks/block-destructive.sh hooks/review-stack-pre-push hooks/plain-panel.py hooks/context-monitor.js \
         hooks/handover-start.sh hooks/no-jjstack-bar.py hooks/skill-rules.py hooks/chain-catch.py hooks/live-tick.py \
         hooks/claude-config-reminder.py hooks/workflow-start.sh scripts/claude-ram-watch.sh hooks/profile-lock.py; do
  # the stage step refused a missing required one; the others may be absent from a scratch copy
  [ -e "$STAGE/$f" ] || continue
  note "$f"
  run cp -a "$STAGE/$f" "$LIVE/$f"
  [ "$f" = MAP.md ] || run chmod +x "$LIVE/$f"
done
if [ -e "$LIVE/settings.json" ] && [ "$DRY" = 0 ]; then
  # Spec 0035 AC-7: backups used to pile up as settings.json.bak.* at the top of the live dir.
  mkdir -p "$LIVE/backups/settings"
  bak="$LIVE/backups/settings/settings.json.bak.$(date +%Y%m%d-%H%M%S)"
  cp "$LIVE/settings.json" "$bak"
  note "settings.json: backed up existing -> backups/settings/$(basename "$bak")"
fi
note "settings.json"
if [ "$DRY" = 0 ]; then
  cp "$STAGE/settings.json" "$LIVE/settings.json.tmp"
  mv "$LIVE/settings.json.tmp" "$LIVE/settings.json"
fi
frag="$LIVE/private/settings.local.json"
if [ ! -e "$frag" ]; then
  note "settings.local.json: no private settings fragment, private entries not installed"
elif [ "$DRY" = 1 ]; then
  note "would: python3 tools/scripts/private-names.py merge-settings $LIVE/settings.local.json $frag (paths swapped to \$HOME)"
else
  note "settings.local.json: merging $frag"
  sed "s|/home/santiago|$HOME|g" "$frag" | python3 "$REPO/tools/scripts/private-names.py" merge-settings "$LIVE/settings.local.json" -
fi
# Spec 0081 AC-2: the active profile, read by the band, sync and the lock hook.
note "state/profile.json: $PROFILE"
run "${CONFIG[@]}" write-state "$PROFILE" "$STAGE"

# Symlinked: editing the live file edits the repo, so there is one copy of the
# truth. This is how the existing install is already wired. Spec 0076 AC-6: workflows/<name> the same way.
echo "symlink:"
for d in commands skills workflows; do
  for src in "$REPO/claude-home/$d"/*; do
    [ -e "$src" ] || continue
    name="$(basename "$src")"
    dst="$LIVE/$d/$name"
    # Spec 0048 AC-15: a link through the old "live" folder resolves to the same file while the
    # compatibility link exists, but breaks once it is removed, so it is relinked too.
    [ -L "$dst" ] && [ "$(realp "$dst")" = "$(realp "$src")" ] \
      && [[ "$(readlink "$dst")" != */live/* ]] && continue
    [ -e "$dst" ] && ! [ -L "$dst" ] && { note "SKIP $d/$name (a real file is already there)"; continue; }
    note "$d/$name"
    run ln -sfn "$src" "$dst"
  done
done

# Spec 0048 AC-7: an edited downloaded skill that is missing (a new machine) is rebuilt from upstream at
# its pinned commit plus its patch; an installed one is rebuilt only when it equals upstream or upstream plus
# the previous patch (old copy moved to backups/skills), and refused when it has edits of its own (row 110).
if [ -f "$REPO/tools/config/manifest.json" ]; then
  echo "downloaded skills:"
  if [ "$DRY" = 1 ]; then
    note "would: python3 tools/bin/claude-config.py restore"
  else
    python3 "$REPO/tools/bin/claude-config.py" restore || { echo "  a missing edited skill was not rebuilt (above)" >&2; exit 1; }
  fi
fi

# The wf runner is retired live (2026-10-21): _archive/runner/ stays in the repo but is no longer copied
# to ~/.local/share/wf, linked as wf/next, or tested here.
echo "bin links:"
# Spec 0020 AC-3: under `wf`, install.sh runs into a stage and writes nothing outside $LIVE; wf swaps
# the bin links and the git hooks in itself, with the same code.
if [ -n "${WF_STAGE:-}" ]; then
  note "staged: bin links and git hooks left to wf"
  note "staged: skill trigger index not rebuilt; run ~/.claude/skills/jjstack/bin/jjstack-extract-triggers"
else
BIN="$HOME/.local/bin"
run mkdir -p "$BIN"
# Spec 0015 AC-6: /sync runs spec-paths to warn about stale accepted specs.
if [ -e "$BIN/spec-paths" ] && ! [ -L "$BIN/spec-paths" ]; then
  note "SKIP spec-paths (a real file is already at $BIN/spec-paths)"
else
  note "spec-paths -> tools/scripts/spec-paths.py"
  run ln -sfn "$REPO/tools/scripts/spec-paths.py" "$BIN/spec-paths"
fi
# Spec 0023 AC-13: the cheap worker tier.
if [ -e "$BIN/fb-ask" ] && ! [ -L "$BIN/fb-ask" ]; then
  note "SKIP fb-ask (a real file is already at $BIN/fb-ask)"
else
  note "fb-ask -> tools/scripts/fb-ask.py"
  run ln -sfn "$REPO/tools/scripts/fb-ask.py" "$BIN/fb-ask"
fi
# Spec 0054 AC-10: skillspector over every skill and plugin, only new serious findings.
if [ -e "$BIN/skill-scan" ] && ! [ -L "$BIN/skill-scan" ]; then
  note "SKIP skill-scan (a real file is already at $BIN/skill-scan)"
else
  note "skill-scan -> tools/scripts/skill-scan.py"
  run ln -sfn "$REPO/tools/scripts/skill-scan.py" "$BIN/skill-scan"
fi
# Spec 0073 AC-14: the helpers the switch-on rules call.
for name in start-gates design-check issue-reread review-isolated; do
  if [ -e "$BIN/$name" ] && ! [ -L "$BIN/$name" ]; then
    note "SKIP $name (a real file is already at $BIN/$name)"
  else
    note "$name -> tools/scripts/$name.py"
    run ln -sfn "$REPO/tools/scripts/$name.py" "$BIN/$name"
  fi
done
# claude-fb: fb-ask's repo allowlist and key pointer stay in the private folder agents cannot write;
# the repo copies only seed a new machine and never overwrite yours.
for f in fb-ask.conf fb-ok.txt; do
  [ -e "$REPO/tools/claude-fb/$f" ] || continue  # a scratch copy of this repo (the self checks) may lack it
  if [ -e "$LIVE/private/$f" ]; then
    note "claude-fb $f: kept (private copy exists)"
  else
    note "claude-fb $f -> private/$f (seeded from tools/claude-fb)"
    run mkdir -p "$LIVE/private"
    run cp "$REPO/tools/claude-fb/$f" "$LIVE/private/$f"
  fi
done
# claude-fb: the proxy start script and its model list; keys.env stays out of every repo.
for pair in "start-proxy.sh:$HOME/.local/share/claude-fb" "litellm.yaml:$HOME/.config/claude-fb"; do
  f="${pair%%:*}" dir="${pair#*:}"
  if [ -e "$dir/$f" ] && ! [ -L "$dir/$f" ]; then
    note "SKIP claude-fb $f (a real file is already at $dir/$f)"
  else
    note "claude-fb $f -> tools/claude-fb/$f"
    run mkdir -p "$dir"
    run ln -sfn "$REPO/tools/claude-fb/$f" "$dir/$f"
  fi
done
# Spec 0036 AC-6: the missed skill hook matches messages against this index, which jjstack setup
# builds once; without a rebuild it misses every skill added since.
triggers="$LIVE/skills/jjstack/bin/jjstack-extract-triggers"
if [ -x "$triggers" ]; then
  note "skill trigger index -> ~/.jjstack/skill-triggers.json"
  if [ "$DRY" = 1 ]; then
    note "would: $triggers"
  elif ! "$triggers" >/dev/null; then
    note "skill trigger index NOT rebuilt: run $triggers"
  fi
fi
fi

# The names list exists only on the author's machine, so this part is this repo only:
# private ignore lines go to .git/info/exclude (never the public .gitignore) and the
# commit hooks refuse any commit that would bring a name back.
echo "private names:"
if [ -e "$LIVE/private/names.txt" ]; then
  excl="$(git -C "$REPO" rev-parse --git-path info/exclude)"
  # --git-common-dir/hooks, where the global dispatcher looks; --git-path hooks follows core.hooksPath
  hooks="$(git -C "$REPO" rev-parse --git-common-dir)/hooks"
  case "$excl" in /*) ;; *) excl="$REPO/$excl" ;; esac
  case "$hooks" in /*) ;; *) hooks="$REPO/$hooks" ;; esac
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
  checker="$REPO/tools/scripts/private-names.py"
  [ -n "${WF_STAGE:-}" ] || run mkdir -p "$hooks"
  for h in pre-commit commit-msg; do
    [ -n "${WF_STAGE:-}" ] && break
    dst="$hooks/$h"
    act=""
    if [ -L "$dst" ]; then
      [ "$(realp "$dst")" = "$(realp "$checker")" ] && act=refreshed
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
  # Spec 0082 AC-12: its fixtures need jjstack's slot script, which a new machine (or CI) gets only after this
  # install; the hook itself does nothing without it.
  if [ ! -x "$HOME/.claude/skills/jjstack/bin/jjstack-rollover-slot" ]; then
    note "handover hook: self-checks skipped (jjstack not installed yet)"
  else
    bash "$LIVE/hooks/handover-start.sh" --test >/dev/null 2>&1 \
      && note "handover hook: all self-checks passed" \
      || { echo "  HANDOVER HOOK SELF-CHECK FAILED - run: bash ~/.claude/hooks/handover-start.sh --test" >&2; exit 1; }
  fi
  python3 "$LIVE/hooks/skill-rules.py" --test >/dev/null 2>&1 \
    && note "skill rules hook: all self-checks passed" \
    || { echo "  SKILL RULES HOOK SELF-CHECK FAILED - run: python3 ~/.claude/hooks/skill-rules.py --test" >&2; exit 1; }
  # Spec 0081 AC-14: the profile lock; a scratch copy of this repo (the self checks) may lack it.
  if [ -e "$LIVE/hooks/profile-lock.py" ]; then
    python3 "$LIVE/hooks/profile-lock.py" --test >/dev/null 2>&1 \
      && note "profile lock hook: all self-checks passed" \
      || { echo "  PROFILE LOCK HOOK SELF-CHECK FAILED - run: python3 ~/.claude/hooks/profile-lock.py --test" >&2; exit 1; }
  fi
  # Spec 0077 AC-1: the always loaded text of the live folder, CLAUDE.md plus the rules. Spec 0081 AC-23, AC-25: a rule in a
  # subfolder loads too (private ones included); settings.json claudeMdExcludes (rules/ecc/) is left out.
  if ! total=$(python3 -c '
import fnmatch, glob, json, os, sys
live = sys.argv[1]
try:
    skip = json.load(open(live + "/settings.json")).get("claudeMdExcludes") or []
except (OSError, ValueError):
    skip = []
files = [live + "/CLAUDE.md"] + sorted(glob.glob(live + "/rules/**/*.md", recursive=True))
files = [f for f in files if os.path.isfile(f) and not any(fnmatch.fnmatch(f, p) for p in skip)]
print(sum(len(open(f, encoding="utf-8").read()) for f in files))
' "$LIVE"); then
    echo "  LIVE SIZE CHECK FAILED - could not measure $LIVE" >&2; exit 1
  fi
  [ "$total" -le 20000 ] \
    && note "live always loaded text: $total characters (limit 20000)" \
    || { echo "  LIVE ALWAYS LOADED TEXT IS $total CHARACTERS, over the 20000 limit" >&2; exit 1; }
  python3 "$REPO/tools/scripts/gen-agent-index.py" --check >/dev/null \
    && note "agent index: matches claude-home/agents/" || note "agent index: DRIFTED (regenerate)"
  bash "$REPO/claude-home/skills/design/scripts/test-ledger.sh" >/dev/null 2>&1 \
    && note "design ledger + Stop hook: 37 assertions pass" \
    || { echo "  DESIGN LEDGER SELF-CHECK FAILED - the Stop hook may block or leak" >&2; exit 1; }
  node "$REPO/claude-home/skills/design/scripts/build-ramp.mjs" --check >/dev/null 2>&1 \
    && note "colour ramp: solver targets and emitted pairs meet AA" \
    || { echo "  RAMP SELF-CHECK FAILED - generated palettes may ship below AA" >&2; exit 1; }
  python3 "$REPO/tools/scripts/spec-paths.py" --test >/dev/null 2>&1 \
    && note "spec-paths: all self-checks passed" \
    || { echo "  SPEC-PATHS SELF-CHECK FAILED - run: python3 tools/scripts/spec-paths.py --test" >&2; exit 1; }
  python3 "$REPO/tools/scripts/fb-ask.py" --test </dev/null >/dev/null 2>&1 \
    && note "fb-ask: all self-checks passed" \
    || { echo "  FB-ASK SELF-CHECK FAILED - run: python3 tools/scripts/fb-ask.py --test" >&2; exit 1; }
  for name in start-gates design-check issue-reread review-isolated; do
    python3 "$REPO/tools/scripts/$name.py" --test </dev/null >/dev/null 2>&1 \
      && note "$name: all self-checks passed" \
      || { echo "  SELF-CHECK FAILED: $name - run: python3 tools/scripts/$name.py --test" >&2; exit 1; }
  done
  missing=0
  while read -r imp; do
    real="${imp/#@\~/$HOME}"
    [ -f "$real" ] || missing=$((missing + 1))
  done < <(grep -hoE '^@~/[^ ]+' "$REPO"/claude-home/rules/ecc/*/index.md)
  [ "$missing" -eq 0 ] && note "rule imports: all resolve" || note "rule imports: $missing dangling"
  # Last, so every check above still runs. A hook command naming a missing file fails on every event it is
  # wired to. Hooks under the live skills folder belong to jjstack/gstack, installed by their own tools.
  rc=0
  python3 "$REPO/tools/bin/claude-config.py" hook-files >&2 || rc=$?
  case "$rc" in
    0) note "hook files: every settings.json hook command names a file that exists" ;;
    1) echo "  HOOK FILES MISSING (above) - those hooks fail on every call" >&2; exit 1 ;;
    *) echo "  HOOK FILES CHECK FAILED (above) - settings.json was not checked" >&2; exit 1 ;;
  esac
fi

cat <<EOF

done. Still to install, none of it vendored here (see docs/guides/SETUP.md):
  gstack / jjstack, and the Claude Code plugins.

Activate the rules per project by adding one line to that project's CLAUDE.md:
  @~/.claude/rules/ecc/<language>/index.md
EOF
