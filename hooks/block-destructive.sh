#!/usr/bin/env bash
# PreToolUse/Bash guard: blocks catastrophic, data-destroying commands.
# Exit 2 = block (reason on stderr is shown to Claude). Exit 0 = allow.
# Runs in ALL permission modes, including auto and bypassPermissions.
# Scans the FULL command string, so chained commands (foo && rm -rf ~) are caught too.
# Tune the PATTERNS list below. To run a command it blocks, type it yourself with `!`.
#
# KNOWN LIMIT, do not mistake this for complete: this is static text matching. It cannot
# see through variable or command indirection (assigning the path, or the command name,
# to a variable first). Closing that would mean evaluating the command, which is worse.
# Treat this as a backstop against typos and careless commands, not against an adversary.
# Everything it CAN catch, it must catch: run `--test` after any edit.

# no `set -e`: check() returns 2 on purpose, which would trip it
set -uo pipefail

# Non-rm destructive patterns (extended regex, matched case-insensitively). Any match blocks.
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
  # deletion that never spells the two-letter command
  'find[[:space:]]+[^|;&]*-delete'
  'find[[:space:]]+[^|;&]*-exec[[:space:]]+rm'
  'git[[:space:]]+clean[[:space:]]+[^|;&]*-[[:alnum:]]*[xdf]'
  'truncate[[:space:]]+[^|;&]*-s[[:space:]]*0([[:space:]]|$)'
  # truncating redirect onto an absolute or home path (/tmp and /dev/null stay allowed)
  '>[[:space:]]*(~|\$HOME|/home/)[^[:space:]|;&]'
)

# Dangerous targets: absolute path, home, parent traversal, whole cwd, bare glob.
# The left boundary now allows a quote, so a quoted home target is caught like a bare one.
RM_TARGETS='(^|[[:space:]]|["'"'"'])(/|~|\$HOME|\.\.|\*|\.([[:space:]]|$)|\./([[:space:]]|$))'

# True when the deletion carries recursive OR force in ANY flag spelling, including flags
# split across separate tokens and uppercase forms. Tokenized on purpose: a regex over a
# single flag token silently misses split flags, which is the hole this replaces.
rm_is_destructive() {
  local cmd="$1" seg tok
  grep -Eqi '(^|[|;&[:space:]])rm([[:space:]]|$)' <<<"$cmd" || return 1
  while read -r seg; do
    [[ -z "$seg" ]] && continue
    for tok in $seg; do
      case "$tok" in
        --recursive|--force) return 0 ;;
        --*) ;;
        -*) [[ "$tok" == *[rRfF]* ]] && return 0 ;;
      esac
    done
  done < <(grep -oEi '(^|[|;&[:space:]])rm[[:space:]]+[^|;&]*' <<<"$cmd")
  return 1
}

check() {
  local cmd="$1" p
  if rm_is_destructive "$cmd" && grep -Eqi "$RM_TARGETS" <<<"$cmd"; then
    echo "recursive/forced deletion against an absolute/home/parent/wildcard target" && return 2
  fi
  for p in "${PATTERNS[@]}"; do
    if grep -Eqi "$p" <<<"$cmd"; then
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
  # regression cases: each of these was ALLOWED before the 2026-09 review
  block 'rm -r -f /home/santiago/x'
  block 'rm -f -r /home/santiago/x'
  block 'rm -RF /'
  block 'rm -Rf /'
  block 'rm -rf "$HOME"'
  block 'rm -rf '"'"'$HOME'"'"''
  block 'find /home/santiago -delete'
  block 'find /home/santiago -exec rm {} ;'
  block 'git clean -xfd'
  block 'truncate -s0 /home/santiago/.claude/settings.json'
  block ': > /home/santiago/.claude/settings.json'
  # must stay allowed: these are ordinary and safe
  allow 'echo hello > /tmp/scratch.txt'
  allow 'git clean -n'
  allow 'truncate -s 10M /tmp/big'
  allow 'find . -name "*.log"'
  allow 'rm -rf ./node_modules'
  allow 'rm file.txt'
  allow 'git status'
  allow 'ls -la /'
  # note: `echo "rm -rf /"` is intentionally over-blocked; guard errs toward blocking
  [[ $fail -eq 0 ]] && echo "all self-checks passed" || exit 1
  exit 0
fi

# Fail CLOSED. A guard that cannot read its input must not wave the command through:
# collapsing "jq failed" into "no command field" is what let everything past when jq
# was missing from PATH. An empty command field is still a legitimate allow.
if ! CMD="$(jq -r '.tool_input.command // empty' 2>/dev/null)"; then
  echo "BLOCKED by block-destructive.sh: cannot parse hook input (jq missing or failed)" >&2
  echo "Install jq, or this guard cannot protect you. Run it yourself with ! if urgent." >&2
  exit 2
fi
[[ -z "$CMD" ]] && exit 0

if reason="$(check "$CMD")"; then
  exit 0
else
  echo "BLOCKED by block-destructive.sh: $reason" >&2
  echo "This command can delete or destroy data. If intentional, run it yourself with the ! prefix." >&2
  exit 2
fi
