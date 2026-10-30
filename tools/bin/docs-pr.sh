#!/usr/bin/env bash
# Spec 0051 AC-11: a session's docs only commits on the default branch reach origin through a small squash merged PR,
# since the ruleset refuses a direct push. Refuses (exit 2, one line) with tracked changes, no commit ahead of
# origin/<default>, or any commit ahead touching a path outside docs/. Prints the PR URL.
# GH names the gh binary; the self checks point it at a fake, never at GitHub.
set -euo pipefail

GH="${GH:-gh}"
# python3, not `realpath`: the Mac before 13 has no realpath command (spec 0082 AC-2)
HERE="$(cd "$(dirname "$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$0")")" && pwd)"
die() { echo "docs-pr: $*" >&2; exit 2; }

slug="${1:-docs}"
[[ "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]] || die "slug must be lower case letters, digits and -"
git rev-parse --show-toplevel >/dev/null 2>&1 || die "not in a git repo"
cd "$(git rev-parse --show-toplevel)"
ref="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)"
default="${ref#origin/}"
[[ "$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)" == "$default" ]] || die "not on $default"
if ! git diff --quiet || ! git diff --cached --quiet; then
  die "the tree has tracked changes"
fi
git fetch --quiet origin
old="$(git rev-parse HEAD)"
range="origin/$default..$old"
[[ -n "$(git rev-list "$range")" ]] || die "no commit ahead of origin/$default"
# -m: a merge commit's own changes count too.
outside="$(git log -m --format= --name-only --no-renames "$range" | grep -v -e '^docs/' -e '^$' | head -n 1 || true)"
[[ -z "$outside" ]] || die "a commit touches $outside, outside docs/"

# Spec 0026 AC-6: both scans on the range before anything leaves. Security review (module shadowing): the checker
# and the runner modules come from this script's repo at its origin default branch, unpacked outside any working
# tree, and run with python -I, so nothing in the tree being landed (an untracked module next to the checker, a
# PYTHONPATH) can stand in for them.
trusted="$(mktemp -d)"
trap 'rm -rf "$trusted"' EXIT
src="$(git -C "$HERE/../.." symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)"
git -C "$HERE/../.." archive "$src" _archive/runner tools/scripts/private-names.py | tar -x -C "$trusted" || die "cannot read the scanners from $src"
python3 -I "$trusted/tools/scripts/private-names.py" check-range "origin/$default" "$old" >&2 || die "private names scan hit"
python3 -I - "$trusted/_archive/runner" "origin/$default" "$old" <<'EOF' || die "attribution scan hit"
import subprocess, sys
sys.path.insert(0, sys.argv[1])
import pr
rng = f"{sys.argv[2]}..{sys.argv[3]}"
log = subprocess.run(["git", "log", "--format=%H%n%B%x00", rng], capture_output=True, text=True, check=True).stdout
diff = subprocess.run(["git", "diff", rng], capture_output=True, text=True, check=True).stdout
msgs = [(f"commit {c.strip()[:12]}", c.strip().split("\n", 1)[1] if "\n" in c.strip() else "")
        for c in log.split("\0") if c.strip()]
hits = pr.attribution_hits(msgs, diff)
if hits:
    print("attribution: " + ", ".join(hits), file=sys.stderr)
    sys.exit(1)
EOF

branch="docs/$(date +%Y%m%d)-$slug"
git switch --quiet -c "$branch"
git push --quiet origin "$old:refs/heads/$branch"
url="$("$GH" pr create --base "$default" --head "$branch" \
  --title "$(git log -1 --format=%s "$old")" --body "$(git log --reverse --format='- %s' "$range")" | tail -n 1)"
"$GH" pr merge "$url" --squash --delete-branch --match-head-commit "$old" >&2
git switch --quiet "$default" 2>/dev/null || true
git branch -D "$branch" >/dev/null 2>&1 || true
git fetch --quiet --prune origin
# The squash commit holds the same changes as the local commits, so the local default branch is resynced, but only
# when the tree is clean and HEAD is still the pushed commit: anything newer or uncommitted is someone's work.
if git diff --quiet && git diff --cached --quiet && [[ "$(git rev-parse HEAD)" == "$old" ]]; then
  git reset --quiet --hard "origin/$default"
fi
echo "$url"
