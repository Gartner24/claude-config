#!/usr/bin/env bash
# Provenance and drift audit for ~/.claude/skills.
#
#   skills-audit.sh snapshot   record the current state as the baseline
#   skills-audit.sh check      report git updates, drift, and clobbered local overrides
#
# WHY THIS EXISTS: of ~225 installed skills, only four trees are version-controlled
# (jjstack, gstack, anthropic-security-review, getsentry-skills). The rest were copied in
# with no remote, no version field and no lock file, so "has this been updated upstream?"
# is unanswerable for them. This makes it answerable in the only way left: hash them, and
# tell you when one changes under you.
#
# It also guards LOCAL OVERRIDES. Where a defect was patched into a skill we do not own,
# re-copying that skill silently reverts the fix. Overrides are listed below and checked
# by content, not by date.
set -uo pipefail
SKILLS="$HOME/.claude/skills"
MANIFEST="$HOME/.claude/.skills-manifest.json"

# skill -> a string that MUST still be present. Add a row when you patch a skill you do
# not own. If the string vanishes, the skill was re-installed over your fix.
declare -A OVERRIDES=(
  ["industrial-brutalist-ui"]="LOCAL OVERRIDE"
  ["minimalist-ui"]="LOCAL OVERRIDE"
  ["high-end-visual-design"]="LOCAL OVERRIDE"
)

REPOS=(
  "$HOME/.claude/skills/jjstack"
  "$HOME/.claude/skills/gstack"
  "$HOME/.claude/skills/anthropic-security-review"
  "$HOME/.claude/skills/getsentry-skills"
  "$HOME/claude-config"
)

hash_all() {
  python3 - "$SKILLS" <<'PY'
import hashlib, json, os, sys
root = sys.argv[1]
out = {}
for name in sorted(os.listdir(root)):
    p = os.path.join(root, name, "SKILL.md")
    if not os.path.isfile(p):
        continue
    with open(p, "rb") as f:
        out[name] = {
            "sha": hashlib.sha256(f.read()).hexdigest()[:16],
            "link": os.path.islink(os.path.join(root, name)),
        }
print(json.dumps(out, indent=1, sort_keys=True))
PY
}

case "${1:-check}" in
  snapshot)
    hash_all > "$MANIFEST"
    echo "baseline recorded: $MANIFEST ($(python3 -c "
import json;print(len(json.load(open('$MANIFEST'))))") skills)"
    ;;

  check)
    TMPNOW=$(mktemp); trap "rm -f \"$TMPNOW\"" EXIT
    echo "== version-controlled trees =="
    for r in "${REPOS[@]}"; do
      [ -d "$r/.git" ] || { printf "  %-28s (not a repo)\n" "$(basename "$r")"; continue; }
      git -C "$r" fetch --quiet 2>/dev/null
      behind=$(git -C "$r" rev-list --count HEAD..@{u} 2>/dev/null || echo "?")
      dirty=$(git -C "$r" status --porcelain 2>/dev/null | wc -l)
      flag=""; [ "$behind" != "0" ] && [ "$behind" != "?" ] && flag="  <-- UPDATE AVAILABLE"
      printf "  %-28s behind=%-4s dirty=%-3s%s\n" "$(basename "$r")" "$behind" "$dirty" "$flag"
    done

    echo
    echo "== local overrides on skills we do not own =="
    for s in "${!OVERRIDES[@]}"; do
      f="$SKILLS/$s/SKILL.md"
      if [ ! -f "$f" ]; then
        printf "  %-28s SKILL GONE\n" "$s"
      elif grep -qF "${OVERRIDES[$s]}" "$f"; then
        printf "  %-28s intact\n" "$s"
      else
        printf "  %-28s *** OVERRIDE LOST - skill was replaced, re-apply the patch ***\n" "$s"
      fi
    done

    echo
    echo "== drift since the last snapshot =="
    if [ ! -f "$MANIFEST" ]; then
      echo "  no baseline yet - run: skills-audit.sh snapshot"
      exit 0
    fi
    hash_all > "$TMPNOW"
    python3 - "$MANIFEST" "$TMPNOW" <<'PY'
import json, sys
old = json.load(open(sys.argv[1])); new = json.load(open(sys.argv[2]))
added   = sorted(set(new) - set(old))
removed = sorted(set(old) - set(new))
changed = sorted(k for k in set(old) & set(new) if old[k]["sha"] != new[k]["sha"])
for label, items in (("added", added), ("removed", removed), ("changed", changed)):
    if items:
        print(f"  {label}: {len(items)}")
        for i in items:
            print(f"    {i}")
if not (added or removed or changed):
    print("  none - every SKILL.md matches the baseline")
PY
    ;;

  *) sed -n '2,12p' "$0"; exit 2 ;;
esac
