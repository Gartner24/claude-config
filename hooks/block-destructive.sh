#!/usr/bin/env bash
# PreToolUse/Bash guard: blocks catastrophic, data-destroying commands.
# Exit 2 = block (reason on stderr is shown to Claude). Exit 0 = allow.
# Runs in ALL permission modes, including auto and bypassPermissions.
# Scans the FULL command string, so chained commands (foo && rm -rf ~) are caught too.
# Tune the PATTERNS list below. To run a command it blocks, type it yourself with `!`.

# no `set -e`: check() returns 2 on purpose, which would trip it
set -uo pipefail

# Non-rm destructive patterns (extended regex). Any match blocks.
PATTERNS=(
  # whole-disk / filesystem destroyers
  'mkfs(\.[[:alnum:]]+)?[[:space:]]'
  'dd[[:space:]]+([^|;&]*[[:space:]])?of=/dev/'
  '>[[:space:]]*/dev/(sd|nvme|hd|vd|mmcblk|disk)'
  '(wipefs|shred)[[:space:]]+([^|;&]*[[:space:]])?/dev/'
  # recursive chmod/chown on filesystem root
  '(chmod|chown)[[:space:]]+([^|;&]*[[:space:]])?-[[:alnum:]]*R[[:alnum:]]*[[:space:]]+([^|;&]*[[:space:]])?/([[:space:]]|$)'
  # fork bomb
  ':\(\)[[:space:]]*\{[[:space:]]*:[[:space:]]*\|[[:space:]]*:'
)

# rm is blocked only when recursive+force AND the target is dangerous.
RM_RECURSIVE_FORCE='rm[[:space:]]+([^|;&]*[[:space:]])?(-([[:alnum:]]*r[[:alnum:]]*f|[[:alnum:]]*f[[:alnum:]]*r)|--recursive|--force)'
# Dangerous targets: absolute path (/...), home (~ / $HOME), parent traversal (.. / ../),
# whole cwd (. or ./), or a bare glob (*). Plain relative dirs (node_modules, ./build) are allowed.
RM_TARGETS='(^|[[:space:]])(/|~|\$HOME|\.\.|\*|\.([[:space:]]|$)|\./([[:space:]]|$))'

check() {
  local cmd="$1" p
  if grep -Eq "$RM_RECURSIVE_FORCE" <<<"$cmd" && grep -Eq "$RM_TARGETS" <<<"$cmd"; then
    echo "rm -rf against an absolute/home/parent/wildcard target" && return 2
  fi
  for p in "${PATTERNS[@]}"; do
    if grep -Eq "$p" <<<"$cmd"; then
      echo "matched destructive pattern: $p" && return 2
    fi
  done
  return 0
}

# --test: self-check, no stdin needed
if [[ "${1:-}" == "--test" ]]; then
  fail=0
  block() { check "$1" >/dev/null 2>&1 && echo "FAIL (allowed): $1" && fail=1 || true; }
  allow() { check "$1" >/dev/null 2>&1 && echo "FAIL (blocked): $1" && fail=1 || true; }
  # `check` returns 2 (block) or 0 (allow). Invert logic:
  block() { local r; check "$1" >/dev/null 2>&1; r=$?; [[ $r -ne 2 ]] && { echo "FAIL should-block: $1"; fail=1; }; }
  allow() { local r; check "$1" >/dev/null 2>&1; r=$?; [[ $r -eq 2 ]] && { echo "FAIL should-allow: $1"; fail=1; }; }
  block 'rm -rf /'
  block 'rm -rf ~'
  block 'rm -rf $HOME'
  block 'rm -fr /*'
  block 'rm -rf .'
  block 'rm -rf ./'
  block 'rm -rf ~/projects'
  block 'rm -rf /home/santiago/.claude'
  block 'rm -rf ../sibling'
  block 'cd /tmp && rm -rf *'
  block 'rm --recursive --force ~/'
  block 'dd if=/dev/zero of=/dev/sda'
  block 'mkfs.ext4 /dev/sdb1'
  block ':(){ :|:& };:'
  block 'chmod -R 777 /'
  allow 'rm -rf node_modules'
  allow 'rm -rf ./build/cache'
  allow 'rm file.txt'
  allow 'git status'
  allow 'ls -la /'
  # note: `echo "rm -rf /"` is intentionally over-blocked; guard errs toward blocking
  [[ $fail -eq 0 ]] && echo "all self-checks passed" || exit 1
  exit 0
fi

CMD="$(jq -r '.tool_input.command // empty' 2>/dev/null || true)"
[[ -z "$CMD" ]] && exit 0

if reason="$(check "$CMD")"; then
  exit 0
else
  echo "BLOCKED by block-destructive.sh: $reason" >&2
  echo "This command can delete or destroy data. If intentional, run it yourself with the ! prefix." >&2
  exit 2
fi
