#!/usr/bin/env bash
# SessionStart (startup|clear): inject the workflow's first step for this repo,
# plus a once-a-week reminder to review the hub scopes.

input=$(cat)
root=$(git rev-parse --show-toplevel 2>/dev/null)
# Spec 0057 AC-3: after a /clear with a handover waiting, handover-start.sh says resume it;
# "run /scope first" here used to compete with it. Same status call and flags as that hook.
src=$(printf '%s' "$input" | python3 -I -c "import json,sys; d=json.load(sys.stdin); print(d.get('source',''), d.get('cwd',''), sep='\n')" 2>/dev/null)
if [ "${src%%$'\n'*}" = clear ] && timeout 2 "$HOME/.claude/skills/jjstack/bin/jjstack-rollover-slot" --cwd "${src#*$'\n'}" status --max-age-days 1 >/dev/null 2>&1; then
  root=
fi
if [ -n "$root" ]; then
  if [ ! -f "$root/AGENTS.md" ]; then
    echo "Workflow: this repo has no AGENTS.md. Run /audit before any feature work, then /scope."
  elif [ -d "$root/docs/scope" ] || [ -d "$root/.workflow/scope" ]; then
    echo "Workflow: run /scope (no argument) first and state where things stand, including any Assumed specs."
  else
    echo "Workflow: this repo has no scope yet. Run /scope before feature work."
  fi
fi

stamp="$HOME/.claude/.hub-review-stamp"
if [ -z "$(find "$stamp" -mtime -7 2>/dev/null)" ]; then
  touch "$stamp"
  echo "Weekly reminder: review the hub scopes (/scope in ~/projects/freelance and ~/projects/work, and ~/projects for personal). Mention this to the user once."
fi
exit 0
