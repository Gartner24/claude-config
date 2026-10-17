#!/usr/bin/env bash
# Scratch verify for bin/docs-pr.sh (AC-11) and bin/repo-settings.sh --check (AC-10), fake gh, real git.
set -u
W="$(cd "$(dirname "$0")/../../../.." && pwd)"
S=$(mktemp -d)
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid
cat > "$S/gh" <<EOF
#!/usr/bin/env bash
echo "\$*" >> "$S/gh.log"
case "\$1 \$2" in
  "pr create") echo "https://github.com/o/r/pull/9" ;;
  "pr merge") git --git-dir "$S/origin.git" update-ref refs/heads/main "\$(git --git-dir "$S/origin.git" commit-tree "\$(git --git-dir "$S/origin.git" rev-parse "\${@: -1}^{tree}")" -p refs/heads/main -m squash)" ;;
  "api repos/o/r") case "\$4" in .allow_merge_commit) echo true ;; .allow_squash_merge|.delete_branch_on_merge) echo true ;; .allow_rebase_merge) echo false ;; .squash_merge_commit_title) echo PR_TITLE ;; *) echo PR_BODY ;; esac ;;
  "api repos/o/r/rulesets") echo 5 ;;
  "api repos/o/r/rulesets/5") echo "active branch ~DEFAULT_BRANCH deletion,non_fast_forward,pull_request 0 0" ;;
esac
EOF
chmod +x "$S/gh"
git init -q --bare "$S/origin.git"
git init -q -b main "$S/repo"
cd "$S/repo"
mkdir docs && echo a > docs/a.md && git add -A && git commit -qm base
git remote add origin "$S/origin.git" && git push -q origin main && git remote set-head origin main
echo "--- AC-11 outside docs/"
echo x > code.py && git add -A && git commit -qm "feat: code"
GH="$S/gh" "$W/bin/docs-pr.sh" note; echo "exit $?"
git reset -q --hard origin/main
echo "--- AC-11 nothing ahead"
GH="$S/gh" "$W/bin/docs-pr.sh" note; echo "exit $?"
echo "--- AC-11 tracked changes"
echo b >> docs/a.md
GH="$S/gh" "$W/bin/docs-pr.sh" note; echo "exit $?"
git checkout -q docs/a.md
echo "--- AC-11 docs only"
echo b >> docs/a.md && git commit -qam "docs: a note"
GH="$S/gh" "$W/bin/docs-pr.sh" note; echo "exit $?"
echo "gh calls:"; cat "$S/gh.log"
echo "branch now: $(git symbolic-ref --short HEAD); local==origin: $([[ $(git rev-parse HEAD) == $(git rev-parse origin/main) ]] && echo yes || echo no)"
echo "origin main subject: $(git --git-dir "$S/origin.git" log -1 --format=%s main)"
echo "local branches: $(git branch --format='%(refname:short)' | tr '\n' ' ')"
echo "--- AC-10 --check with merge commits allowed"
GH="$S/gh" "$W/bin/repo-settings.sh" --check o/r; echo "exit $?"
echo "--- AC-10 --check with every setting right"
sed -i 's/.allow_merge_commit) echo true/.allow_merge_commit) echo false/' "$S/gh"
GH="$S/gh" "$W/bin/repo-settings.sh" --check o/r; echo "exit $?"
