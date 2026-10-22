#!/usr/bin/env bash
# SessionStart (startup|clear): inject the workflow's first step for this repo,
# plus a once-a-week reminder to review the hub scopes.
# --test runs the self checks.

# Spec 0070 F1: the wf-handoff mod starts /audit or /scope by itself at chat open, so this line
# would only repeat it. This hook runs before the mod (probe F1), so it cannot wait for a mark the
# mod writes: it applies the mod's start rule itself (startSkills in mods/wf-handoff/hooks/register.ts)
# and stays quiet where the mod starts a skill. Both copies are driven by one case list,
# mods/wf-handoff/tests/start-cases.ts.
mod_starts() { # $1 repo top, $2 1 when a handover slot is live
  [ -e "$HOME/.claude/skills/wf-handoff/hooks/register.ts" ] || return 1
  case "${CLAUDE_CODE_ENTRYPOINT:-}" in sdk*) return 1 ;; esac
  [ -z "${WF_RUN:-}" ] && [ -z "${TM_WORKER_NAME:-}" ] && [ "${AUTO_HANDOFF_DISABLE:-}" != 1 ] || return 1
  [ "$2" = 0 ] || return 1
  local url kind
  url=$(git -C "$1" remote get-url origin 2>/dev/null)
  kind=$(origin_kind "$url" "$HOME/.claude/private/work.md")
  case "$kind" in
    own) return 0 ;;
    bot) [ -d "$1/docs/scope" ] || [ -d "$1/.workflow/scope" ] ;;
    *) return 1 ;;
  esac
}

# own | bot | bad, the same parse as originKind in register.ts: scp, ssh:// and https:// forms,
# host github.com and an org listed in work.md, ignoring case. A substring match used to take an
# org ending in a listed name as bot reviewed. No origin is own; one that does not parse is bad.
origin_kind() {
  python3 -I -c '
import re, sys
url = sys.argv[1].strip()
try:
    work = open(sys.argv[2], encoding="utf-8", errors="replace").read()
except OSError:
    work = ""
if not url:
    print("own"); sys.exit()
m = re.match(r"^(?:ssh|https?|git)://(?:[^@/]+@)?([^/:]+)(?::\d+)?/([^/]+)/.+$", url, re.I) \
    or re.match(r"^(?:[^@/]+@)?([^/:]+):(?!//)([^/]+)/.+$", url)
orgs = {o.lower() for o in re.findall(r"github\.com[:/]([\w.-]+)/", work)}
print("bad" if not m else "bot" if m.group(1).lower() == "github.com" and m.group(2).lower() in orgs else "own")
' "$1" "$2" 2>/dev/null || echo bad
}

if [ "${1:-}" = --test ]; then
  self="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
  cases="$(dirname "$self")/../mods/wf-handoff/tests/start-cases.ts"
  [ -e "$cases" ] || cases="$HOME/.claude/skills/wf-handoff/tests/start-cases.ts"
  exec python3 -I - "$self" "$cases" <<'PY'
import json, os, re, subprocess, sys, tempfile
hook, cases_file = sys.argv[1], sys.argv[2]
text = open(cases_file).read()
fixture = json.loads(re.search(r"/\* json:start \*/(.*)/\* json:end \*/", text, re.S).group(1))
failures = []
LINE = "Workflow:"


def world(tmp, case):
    home = os.path.join(tmp, "home")
    os.makedirs(os.path.join(home, ".claude/skills/wf-handoff/hooks"))
    open(os.path.join(home, ".claude/skills/wf-handoff/hooks/register.ts"), "w").close()
    os.makedirs(os.path.join(home, ".claude/private"))
    open(os.path.join(home, ".claude/private/work.md"), "w").write(fixture["work"])
    slot = os.path.join(home, ".claude/skills/jjstack/bin/jjstack-rollover-slot")
    os.makedirs(os.path.dirname(slot))
    open(slot, "w").write("#!/bin/sh\nexit %d\n" % (0 if case.get("slot") else 1))
    os.chmod(slot, 0o755)
    # the weekly hub reminder stamp, so its line does not depend on the week
    open(os.path.join(home, ".claude/.hub-review-stamp"), "w").close()
    repo = os.path.join(tmp, "w")
    os.makedirs(repo)
    if case.get("repo", True):
        subprocess.run(["git", "init", "-q", repo], check=True)
        if case.get("origin"):
            subprocess.run(["git", "-C", repo, "remote", "add", "origin", case["origin"]], check=True)
    if case.get("agents"):
        open(os.path.join(repo, "AGENTS.md"), "w").write("# w\n")
    if case.get("scope"):
        d = os.path.join(repo, "docs/scope" if case.get("agents") else ".workflow/scope")
        os.makedirs(d)
        open(os.path.join(d, "scope.md"), "w").write("# s\n")
    return home, repo


def printed(case, env=None, source="startup", nomod=False):
    with tempfile.TemporaryDirectory() as tmp:
        home, repo = world(tmp, case)
        if nomod:
            os.remove(os.path.join(home, ".claude/skills/wf-handoff/hooks/register.ts"))
        e = {k: v for k, v in os.environ.items() if k not in ("WF_RUN", "TM_WORKER_NAME", "AUTO_HANDOFF_DISABLE", "GIT_DIR")}
        e.update({"HOME": home, "CLAUDE_CODE_ENTRYPOINT": "cli", "GIT_CEILING_DIRECTORIES": tmp, **(env or {})})
        p = subprocess.run(["bash", hook], input=json.dumps({"source": source, "cwd": repo}), cwd=repo,
                           capture_output=True, text=True, env=e)
        return LINE in p.stdout


def check(name, got, want):
    if got != want:
        failures.append(f"{name}: got {got!r}, want {want!r}")


# The mod's own cases: quiet exactly where the mod starts a skill, the line only in a repo.
for c in fixture["cases"]:
    check(f"shared case: {c['name']}", printed(c), c["repo"] and c["start"] is None)
# AC-13: where the mod does not run, the line is printed as before
own = {"origin": "git@github.com:me/own.git", "agents": True}
check("skip: the mod starts /scope, the line is not printed", printed(own), False)
check("no skip without the mod linked", printed(own, nomod=True), True)
check("no skip in a claude -p run", printed(own, {"CLAUDE_CODE_ENTRYPOINT": "sdk-cli"}), True)
for var in ("WF_RUN", "TM_WORKER_NAME"):
    check(f"no skip with {var}", printed(own, {var: "1"}), True)
check("no skip with AUTO_HANDOFF_DISABLE=1", printed(own, {"AUTO_HANDOFF_DISABLE": "1"}), True)
check("a clear with a live slot: quiet, the handover wins", printed({**own, "slot": True}, source="clear"), False)
check("a clear with no slot: quiet, the mod starts /scope", printed(own, source="clear"), False)
for f in failures:
    print(f"FAIL {f}")
print(f"workflow-start self checks: {'all passed' if not failures else f'{len(failures)} failed'}")
sys.exit(1 if failures else 0)
PY
fi

input=$(cat)
root=$(git rev-parse --show-toplevel 2>/dev/null)
# Spec 0057 AC-3: after a /clear with a handover waiting, handover-start.sh says resume it;
# "run /scope first" here used to compete with it. Same status call and flags as that hook.
src=$(printf '%s' "$input" | python3 -I -c "import json,sys; d=json.load(sys.stdin); print(d.get('source',''), d.get('cwd',''), sep='\n')" 2>/dev/null)
slot=0
timeout 2 "$HOME/.claude/skills/jjstack/bin/jjstack-rollover-slot" --cwd "${src#*$'\n'}" status --max-age-days 1 >/dev/null 2>&1 && slot=1
if [ "${src%%$'\n'*}" = clear ] && [ "$slot" = 1 ]; then
  root=
fi
if [ -n "$root" ] && mod_starts "$root" "$slot"; then
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
