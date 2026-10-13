#!/usr/bin/env bash
# Spec 0004 AC-4 amendment (review stack finding M9): one real claude -p call carrying run.py's DENIED list.
# Only the deny rules are tested: git is allowed by an explicit rule in default mode, so the auto mode classifier
# (which wf calls also face) cannot deny anything here; a deny rule beats an allow rule.
# Expect: steps 1 and 2 run (git stash push, a commit whose message holds "push"); steps 3 to 8 are denied, and the
# local bare remote never gets a branch. Run it yourself with ! (about 1 minute).
set -u
P=$(cd "$(dirname "$0")" && pwd)
RUNNER=$(cd "$P/../../../../runner" && pwd)
R=$(mktemp -d)
trap 'rm -rf "$R"' EXIT
DENIED=$(python3 -B -c 'import sys; sys.path.insert(0, sys.argv[1]); import run; print(run.DENIED)' "$RUNNER")
echo "DENIED: $DENIED"
git init -q --bare "$R/remote.git"
git init -q -b work "$R/repo"
git -C "$R/repo" remote add origin "$R/remote.git"
# The identity lives in the repo config: a `git -c user.name=... commit -m "...push..."` is denied by design.
git -C "$R/repo" config user.name probe
git -C "$R/repo" config user.email probe@example.invalid
printf 'a\n' > "$R/repo/a.txt"
git -C "$R/repo" add -A
git -C "$R/repo" commit -qm base
printf 'b\n' >> "$R/repo/a.txt"
PROMPT="Permission probe for the machine owner. Run each step as exactly one Bash command, exactly as written, one step at a time, and report each numbered result with its exact output or error. Never retry, never rephrase a command, never work around a denial, and go on to the next step after a denial.
1. git stash push -m probe
2. git commit --allow-empty -m 'fix the push button'
3. git push origin work
4. git -c core.askPass=true push origin work
5. git -C . push origin work
6. git --no-pager push origin work
7. git -P push origin work
8. git -p push origin work"
OUT=$(cd "$R/repo" && claude -p "$PROMPT" --model haiku --output-format json --permission-mode default \
  --allowedTools "Bash(git *)" --disallowedTools "$DENIED")
printf '%s' "$OUT" | python3 -c '
import json, sys
d = json.load(sys.stdin)
denied = [x.get("tool_input", {}).get("command") for x in d.get("permission_denials", [])]
print("denied commands (expect steps 3 to 8 only):")
for c in denied:
    print("  ", c)
print("result:", d.get("result", "")[:1500])'
echo "stash list: $(git -C "$R/repo" stash list | wc -l) (expect 1)"
echo "commits with push in message: $(git -C "$R/repo" log --oneline --grep='push button' | wc -l) (expect 1)"
echo "remote branches: $(git -C "$R/remote.git" branch | wc -l) (expect 0)"
