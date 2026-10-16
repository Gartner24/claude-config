#!/bin/bash
# Self-check for spawn-review: a ref target makes an excluded worktree, --list shows it,
# --cleanup removes it, a bad ref is refused. PATH holds only basic tools, so no tmux or
# claude is launched.
set -u
S="$(cd "$(dirname "$0")" && pwd)/spawn-review"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
bin=$T/bin; mkdir -p "$bin"
for c in bash env git sed tr grep mkdir basename cat; do ln -s "$(command -v $c)" "$bin/$c"; done
git init -q "$T/repo"; git -C "$T/repo" -c user.name=t -c user.email=t@t commit -q --allow-empty -m init
cd "$T/repo"
fail=0
out=$(PATH=$bin bash "$S" HEAD 2>&1) || { echo "FAIL spawn: $out"; fail=1; }
[ -d .spawn-review-worktrees/HEAD ] || { echo "FAIL no worktree dir"; fail=1; }
echo "$out" | grep -q "run these two yourself" || { echo "FAIL no fallback commands"; fail=1; }
echo "$out" | grep -q "claude --setting-sources user --strict-mcp-config" || { echo "FAIL ref launch keeps project settings"; fail=1; }
grep -qxF ".spawn-review-worktrees/" .git/info/exclude || { echo "FAIL not excluded"; fail=1; }
[ -z "$(git status --porcelain)" ] || { echo "FAIL git status dirty"; fail=1; }
PATH=$bin bash "$S" --list | grep -q spawn-review-worktrees/HEAD || { echo "FAIL list"; fail=1; }
PATH=$bin bash "$S" --cleanup >/dev/null
[ -d .spawn-review-worktrees/HEAD ] && { echo "FAIL cleanup"; fail=1; }
PATH=$bin bash "$S" nosuchref >/dev/null 2>&1 && { echo "FAIL bad ref accepted"; fail=1; }
# A PR target: a fake gh whose title carries an escape, and an origin that serves pull/7/head.
git init -q --bare "$T/origin.git"
git push -q "$T/origin.git" HEAD:refs/pull/7/head
git remote add origin "$T/origin.git"
printf '#!/bin/bash\ncase "$1 $2" in "repo view") echo o/r ;; "pr view") printf "Ti\\033[31mt\\302\\233le" ;; esac\n' > "$bin/gh"
chmod +x "$bin/gh"
out=$(PATH=$bin bash "$S" 7 2>&1) || { echo "FAIL pr spawn: $out"; fail=1; }
[ -d .spawn-review-worktrees/7 ] || { echo "FAIL no pr worktree"; fail=1; }
echo "$out" | grep -q "claude --setting-sources user --strict-mcp-config" || { echo "FAIL pr launch keeps project settings"; fail=1; }
echo "$out" | grep -q "Ti.31mtle" || { echo "FAIL pr title missing"; fail=1; }
# The script's own colours use ESC too, so only the title's bytes are checked.
LC_ALL=C grep -qe "Ti"$'\033' -e $'t\302\233le' <<<"$out" && { echo "FAIL escape reached the screen"; fail=1; }
out=$(PATH=$bin bash "$S" --cleanup) && echo "$out" | grep -q "cleaned 1" || { echo "FAIL pr cleanup"; fail=1; }
[ $fail = 0 ] && echo PASS
exit $fail
