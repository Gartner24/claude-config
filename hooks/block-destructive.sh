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
  # Deletion that never spells the two-letter command. Anchored at a command position
  # (start, or after ; & |) so a commit message or doc that merely MENTIONS these does
  # not trip the guard - that was a real daily-friction false positive.
  '(^|[;&|])[[:space:]]*find[[:space:]]+[^|;&]*-delete'
  '(^|[;&|])[[:space:]]*find[[:space:]]+[^|;&]*-exec[[:space:]]+rm'
  '(^|[;&|])[[:space:]]*truncate[[:space:]]+[^|;&]*-s[[:space:]]*0([[:space:]]|$)'
  # EMPTY redirect onto a home path - `: > file` / `> file` can only truncate.
  # `echo x > ~/out.txt` writes content and is left alone.
  '(^|[;&|])[[:space:]]*(:|true)?[[:space:]]*>[[:space:]]*(~|\$HOME|/home/)[^[:space:]|;&]'
)

# Dangerous targets: absolute path, home, parent traversal, whole cwd, bare glob.
# The left boundary now allows a quote, so a quoted home target is caught like a bare one.
RM_TARGETS='(^|[[:space:]]|["'"'"'])(/|~|\$HOME|\.\.|\*|\.([[:space:]]|$)|\./([[:space:]]|$))'

# True when the deletion is RECURSIVE, in any flag spelling: -r, -R, inside a combined
# cluster like -rf, split across tokens as -r -f, or --recursive. Tokenized on purpose:
# a regex over a single flag token silently misses split flags.
# Deliberately NOT triggered by -f alone. Force only suppresses the prompt; recursion is
# what turns a deletion catastrophic, and `rm -f ~/.cache/some.lock` is routine cleanup.
rm_is_destructive() {
  local cmd="$1" seg tok
  grep -Eqi '(^|[|;&[:space:]])rm([[:space:]]|$)' <<<"$cmd" || return 1
  while read -r seg; do
    [[ -z "$seg" ]] && continue
    for tok in $seg; do
      case "$tok" in
        --recursive) return 0 ;;
        --*) ;;
        -*) [[ "$tok" == *[rR]* ]] && return 0 ;;
      esac
    done
  done < <(grep -oEi '(^|[|;&[:space:]])rm[[:space:]]+[^|;&]*' <<<"$cmd")
  return 1
}

# `git clean` deletes untracked files, but -n/--dry-run only previews them. grep -E is
# POSIX ERE with no negative lookahead, so the exclusion cannot be expressed as one
# pattern - it has to be two tests.
git_clean_is_destructive() {
  local cmd="$1"
  grep -Eqi 'git[[:space:]]+clean[[:space:]]+[^|;&]*-[[:alnum:]]*[xdf]' <<<"$cmd" || return 1
  grep -Eqi 'git[[:space:]]+clean[[:space:]]+[^|;&]*(--dry-run|-[[:alnum:]]*n)' <<<"$cmd" && return 1
  return 0
}

check() {
  local cmd="$1" p
  if git_clean_is_destructive "$cmd"; then
    echo "git clean would delete untracked files (add -n/--dry-run to preview)" && return 2
  fi
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
  allow 'rm -f /home/santiago/.cache/app.lock'
  allow 'rm -f /home/santiago/.npm/_logs/*'
  allow 'git clean --dry-run -xfd'
  allow 'npm config get registry > /home/santiago/reg.txt'
  allow 'git commit -m "docs: explain the -delete flag"'
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
