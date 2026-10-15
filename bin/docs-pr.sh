#!/usr/bin/env bash
# Spec 0051 AC-11: a session's docs only commits on the default branch reach origin through a small squash merged PR,
# since the ruleset refuses a direct push. Refuses (exit 2, one line) with tracked changes, no commit ahead of
# origin/<default>, or any commit ahead touching a path outside docs/. Prints the PR URL.
# GH names the gh binary; the self checks point it at a fake, never at GitHub.
set -euo pipefail

GH="${GH:-gh}"
HERE="$(cd "$(dirname "$(realpath "$0")")" && pwd)"
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

# Spec 0026 AC-6: both scans on the range before anything leaves.
python3 "$HERE/../scripts/private-names.py" check-range "origin/$default" "$old" >&2 || die "private names scan hit"
python3 - "$HERE/../runner" "origin/$default" "$old" <<'EOF' || die "attribution scan hit"
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
url="$("$GH" pr create --base "$default" --head "$branch" --fill | tail -n 1)"
"$GH" pr merge "$url" --squash --delete-branch --match-head-commit "$old" >&2
git switch --quiet "$default" 2>/dev/null || true
git branch -D "$branch" >/dev/null 2>&1 || true
git fetch --quiet --prune origin
if git diff --quiet "$old" "origin/$default" -- docs; then
  git reset --quiet --keep "origin/$default"
else
  echo "docs-pr: origin/$default differs in docs/ from your commits; they stay local" >&2
  echo "$url"
  exit 1
fi
echo "$url"
