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
  # git discarding uncommitted work: reset --hard, checkout of the whole tree
  'git([[:space:]]+-C[[:space:]]+[^[:space:]|;&]+)?[[:space:]]+reset[[:space:]]+([^|;&]*[[:space:]])?--hard'
  'git([[:space:]]+-C[[:space:]]+[^[:space:]|;&]+)?[[:space:]]+checkout[[:space:]]+(--[[:space:]]+)?\.([[:space:]]|$)'
)

# Dangerous targets: absolute path, home, parent traversal, whole cwd, bare glob.
# The left boundary now allows a quote, so a quoted home target is caught like a bare one.
# $PWD only when it is the whole target, like `.`; `$PWD/build` stays allowed.
RM_TARGETS='(^|[[:space:]]|["'"'"'])(/|~|\$HOME|\$\{HOME\}|\.\.|\*|\.([[:space:]]|$)|\./([[:space:]]|$)|(\$PWD|\$\{PWD\})/?(["'"'"'[:space:]]|$))'

# True when the deletion is RECURSIVE, in any flag spelling: -r, -R, inside a combined
# cluster like -rf, split across tokens as -r -f, or --recursive. Tokenized on purpose:
# a regex over a single flag token silently misses split flags.
# Deliberately NOT triggered by -f alone. Force only suppresses the prompt; recursion is
# what turns a deletion catastrophic, and `rm -f ~/.cache/some.lock` is routine cleanup.
rm_is_destructive() {
  local cmd="$1" seg tok
  grep -Eqi '(^|[|;&[:space:]"'"'"'])rm([[:space:]]|$)' <<<"$cmd" || return 1
  while read -r seg; do
    [[ -z "$seg" ]] && continue
    for tok in $seg; do
      case "$tok" in
        --recursive) return 0 ;;
        --*) ;;
        -*) [[ "$tok" == *[rR]* ]] && return 0 ;;
      esac
    done
  done < <(grep -oEi '(^|[|;&[:space:]"'"'"'])rm[[:space:]]+[^|;&]*' <<<"$cmd")
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

# Spec 0016. The patterns above used to block a commit whose MESSAGE named a deletion
# command (2026-10-11), stalling unattended runs. SCANNER returns the command unchanged
# except inside data regions (single quoted strings, double quoted strings with no
# substitution, the `"$(cat <<'EOF' ... EOF )"` commit form, heredoc bodies), where
# whitespace and ; & | < > ( ) become `_`, so quoted prose cannot look like a command.
# It exits nonzero, meaning "check the raw text", when any word could run code (EXEC)
# or when it cannot parse the command. Blanking only turns characters into `_`, so it
# can hide a match but never create one; that is why every doubt goes back to raw.
read -r -d '' SCANNER <<'PY' || true
import os, re, sys

EXEC = {'sh', 'bash', 'zsh', 'dash', 'ksh', 'fish', 'csh', 'tcsh', 'busybox', 'eval',
        'exec', 'source', '.', 'ssh', 'su', 'xargs', 'watch', 'tmux', 'screen', 'script',
        'python', 'python3', 'node', 'perl', 'ruby', 'awk', 'gawk', 'php', 'lua'}
SEP = set(' \t\n\r;&|(){}<>!`')
BLANK = set(';&|<>()')
VAR = re.compile(r'\$[\w{@*#?!-]')
FIRST = re.compile(r'(\$\(|`)[ \t\n]*([^ \t\n;&|(){}<>!`]*)')
CAT = re.compile(r'\$\(cat[ \t]+<<(-?)[ \t]*(?:\'([^\'\n]+)\'|"([^"\n$`\\]+)"|\\([\w.-]+)|([\w.-]+))[ \t]*\n')


class Raw(Exception):
    pass


s = sys.stdin.buffer.read().decode('utf-8', 'surrogateescape')
n = len(s)
out = list(s)
words, firsts = [], []


def blank(a, b):
    for k in range(a, b):
        if out[k].isspace() or out[k] in BLANK:
            out[k] = '_'


def add_first(w):
    # a variable as the command can name any executor: `$($X)`
    firsts.append('sh' if VAR.search(w) else re.sub('[\'"\\\\]', '', w))


def first_word(k):
    add_first(re.match(r'[ \t\n]*([^ \t\n;&|(){}<>!`]*)', s[k:]).group(1))


def code_firsts(text):
    # an unquoted heredoc body or a substitution runs whatever follows $( or a backtick
    for m in FIRST.finditer(text):
        add_first(m.group(2))


def backtick_end(k):
    while k < n:
        if s[k] == '\\':
            k += 2
        elif s[k] == '`':
            return k
        else:
            k += 1
    raise Raw


def body_end(k, delim, strip):
    # k: start of the first body line. Returns (end of body, index after the delimiter line).
    start = k
    while k <= n:
        e = s.find('\n', k)
        line = s[k:n if e < 0 else e]
        if (line.lstrip('\t') if strip else line) == delim:
            return max(start, k - 1), (n if e < 0 else e + 1)
        if e < 0:
            break
        k = e + 1
    raise Raw


def subst_end(k):
    # k: just after `$(`. Returns the index after the matching `)`.
    depth = 1
    while k < n:
        c = s[k]
        if c == '\\':
            k += 2
        elif c == "'":
            j = s.find("'", k + 1)
            if j < 0:
                raise Raw
            k = j + 1
        elif c == '"':
            k = dq_end(k + 1, False)[0] + 1
        elif c == '`':
            first_word(k + 1)
            k = backtick_end(k + 1) + 1
        elif s.startswith('$(', k):
            first_word(k + 2)
            depth += 1
            k += 2
        elif c == '(':
            depth += 1
            k += 1
        elif c == ')':
            depth -= 1
            k += 1
            if depth == 0:
                return k
        elif s.startswith('<<', k):
            raise Raw
        elif (c == '#' or s.startswith('case', k)) and (k == 0 or s[k - 1] in ' \t\n;&|('):
            # a comment or a case pattern can hold an unmatched paren
            raise Raw
        else:
            k += 1
    raise Raw


def dq_end(k, top):
    # k: just after the opening `"`. Returns (index of the closing `"`, is a data region,
    # the text the word gets, whether that text expands a variable).
    start = k
    m = CAT.match(s, k) if top else None
    if m:
        quoted = m.group(5) is None
        delim = m.group(2) or m.group(3) or m.group(4) or m.group(5)
        try:
            end, after = body_end(m.end(), delim, m.group(1) == '-')
        except Raw:
            end = None
        if end is not None:
            tail = re.match(r'[ \t\n]*\)"', s[after:])
            if tail:
                first_word(k + 2)
                body = s[m.end():end]
                data = quoted or ('$(' not in body and '`' not in body)
                if not data:
                    code_firsts(body)
                # the word is the body: `"$(cat <<'EOF'` + `bash` + ... `)" -c '...'` runs bash
                return after + tail.end() - 1, data, body, not quoted and bool(VAR.search(body))
    data = True
    while k < n:
        c = s[k]
        if c == '\\':
            k += 2
        elif c == '"':
            return k, data, s[start:k], bool(VAR.search(s[start:k]))
        elif c == '`':
            data = False
            first_word(k + 1)
            k = backtick_end(k + 1) + 1
        elif s.startswith('$(', k):
            data = False
            first_word(k + 2)
            k = subst_end(k + 2)
        elif s.startswith('${', k):
            j = s.find('}', k)
            if j < 0 or re.search(r'[\'"`]|\$\(', s[k:j]):
                raise Raw
            k = j + 1
        else:
            k += 1
    raise Raw


def scan():
    if '\\\n' in s:
        # bash joins lines before it reads `$\<newline>(` or `$\<newline>X`, the scanner
        # does not; quoted text with a line continuation is rare enough to scan raw
        raise Raw
    word, var, pending, i = '', False, [], 0

    def end_word():
        # a word that expands a variable can hold an executor or run quoted text:
        # `X='mkfs.ext4 /dev/sdb1'; $X`, `m$X`
        nonlocal word, var
        if word:
            words.append('sh' if var else word)
        word, var = '', False

    while i < n:
        c = s[i]
        if c == '\\':
            word += s[i + 1:i + 2]
            i += 2
        elif c == "'":
            j = s.find("'", i + 1)
            if j < 0:
                raise Raw
            word += s[i + 1:j]
            blank(i + 1, j)
            i = j + 1
        elif c == '$' and s[i + 1:i + 2] == "'":
            j = i + 2
            while j < n and s[j] != "'":
                j += 2 if s[j] == '\\' else 1
            if j >= n:
                raise Raw
            word += s[i + 2:j]
            i = j + 1
        elif c == '$' and s[i + 1:i + 2] == '"':
            j, _, text, v = dq_end(i + 2, False)
            word += text
            var |= v
            i = j + 1
        elif c == '"':
            j, data, text, v = dq_end(i + 1, True)
            if data:
                blank(i + 1, j)
            word += text
            var |= v
            i = j + 1
        elif c == '`' or s.startswith('$(', i):
            # unquoted, its output is split into words and can run as a command:
            # `$(printf 'mkfs.ext4 /dev/sdb1')` would pass with its quotes blanked
            raise Raw
        elif c == '{' and s[i + 1:i + 2] not in ('', '}') and not s[i + 1].isspace():
            # brace expansion builds words: `{sh,-c,'mkfs.ext4 /dev/sdb1'}`
            raise Raw
        elif c == '#' and not word and (i == 0 or s[i - 1] in ' \t\n;&|()<>'):
            j = s.find('\n', i)
            i = n if j < 0 else j
        elif s.startswith('<<<', i):
            end_word()
            i += 3
        elif s.startswith('<<', i):
            end_word()
            k = i + 2
            strip = s[k:k + 1] == '-'
            k += strip
            while k < n and s[k] in ' \t':
                k += 1
            quoted = True
            if s[k:k + 1] in ('"', "'"):
                j = s.find(s[k], k + 1)
                if j < 0:
                    raise Raw
                delim, k = s[k + 1:j], j + 1
            else:
                if s[k:k + 1] == '\\':
                    k += 1
                else:
                    quoted = False
                j = k
                while j < n and not s[j].isspace() and s[j] not in ';&|()<>':
                    j += 1
                delim, k = s[k:j], j
            if not delim or re.search(r'[\'"\\$`]', delim) or (k < n and s[k] in '\'"\\$`'):
                raise Raw
            pending.append((delim, strip, quoted))
            i = k
        elif c == '\n':
            end_word()
            i += 1
            for delim, strip, quoted in pending:
                end, after = body_end(i, delim, strip)
                body = s[i:end]
                if quoted or ('$(' not in body and '`' not in body):
                    blank(i, end)
                else:
                    code_firsts(body)
                i = after
            pending = []
        elif c in SEP:
            end_word()
            i += 1
        else:
            var |= bool(VAR.match(s, i))
            word += c
            i += 1
    end_word()
    if pending:
        raise Raw


try:
    scan()
except (Raw, IndexError, RecursionError):
    sys.exit(3)
force = sys.argv[1:] == ['force']  # --test only: skip the executor check
if not force and any(os.path.basename(w) in EXEC for w in words + firsts):
    sys.exit(4)
sys.stdout.buffer.write(''.join(out).encode('utf-8', 'surrogateescape'))
PY

# Prints the text check() should scan: the blanked command, or the raw command on any doubt.
blank_data() {
  local cmd="$1" out
  if [[ "$cmd" != *[\'\"]* && "$cmd" != *'<<'* ]]; then
    printf '%s' "$cmd"
  elif out="$(printf '%s' "$cmd" | timeout 2 python3 -I -c "$SCANNER" 2>/dev/null)" && [[ -n "$out" ]]; then
    printf '%s' "$out"
  else
    printf '%s' "$cmd"
  fi
}

guard() { check "$(blank_data "$1")"; }

# --test: self-check, no stdin needed
if [[ "${1:-}" == "--test" ]]; then
  fail=0
  block() { check "$1" >/dev/null 2>&1 && echo "FAIL (allowed): $1" && fail=1 || true; }
  allow() { check "$1" >/dev/null 2>&1 && echo "FAIL (blocked): $1" && fail=1 || true; }
  # `check` returns 2 (block) or 0 (allow). Invert logic:
  block() { local r; guard "$1" >/dev/null 2>&1; r=$?; [[ $r -ne 2 ]] && { echo "FAIL should-block: $1"; fail=1; }; }
  allow() { local r; guard "$1" >/dev/null 2>&1; r=$?; [[ $r -eq 2 ]] && { echo "FAIL should-allow: $1"; fail=1; }; }
  # Spec 0016 allow case: blocked on the raw text, so it passes only through the blanking.
  # This is the mutation check kept in the suite: without blank_data it goes red.
  allow_data() {
    check "$1" >/dev/null 2>&1 && { echo "FAIL not blocked raw, proves nothing: $1"; fail=1; }
    allow "$1"
  }
  # Still blocked even with the executor check skipped, so a hole in the blanking shows
  # even where the raw fallback would hide it. The scanner must parse it, or the case
  # would only be testing the fallback.
  force_block() {
    local out
    block "$1"
    if ! out="$(printf '%s' "$1" | python3 -I -c "$SCANNER" force)"; then
      echo "FAIL forced scan did not parse: $1"; fail=1; return
    fi
    check "$out" >/dev/null 2>&1 && { echo "FAIL forced blanking let through: $1"; fail=1; }
    return 0
  }
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
  # 2026-10-22 blind review: brace and cwd spellings, and git discarding work
  block 'rm -rf ${HOME}'
  block 'rm -rf "${HOME}"'
  block 'rm -rf $PWD'
  block 'rm -rf ${PWD}'
  block 'rm -rf "$PWD/"'
  block 'git reset --hard'
  block 'git reset --hard origin/main'
  block 'git -C /tmp/repo reset --hard'
  block 'git checkout -- .'
  block 'git checkout .'
  allow 'rm -rf $PWD/build'
  allow 'git reset --soft HEAD~1'
  allow 'git checkout -- src/file.txt'
  allow 'git checkout main'
  allow_data 'git commit -m "docs: never git reset --hard"'
  # follow-up of spec 0016: a destructive rm inside a quoted shell string
  block 'bash -c "rm -rf ~"'
  block "sh -c 'rm -rf /'"
  block 'eval "rm -rf ~"'
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
  # spec 0016: quoted prose is data now (this one was over blocked on purpose before)
  allow 'echo "rm -rf /"'
  allow_data 'git commit -m "docs: rm -rf / was the bug"'
  allow_data "git commit -m \"\$(cat <<'EOF'
fix the guard
rm -rf ~
EOF
)\""
  allow_data 'cat <<EOF > notes.md
wipe it with mkfs.ext4 /dev/sda
EOF'
  allow_data "sed -i 's/a/mkfs.ext4 x/' f"
  allow_data 'echo "wipe it with mkfs.ext4 /dev/sdb1"'
  allow_data "printf '%s\n' 'dd if=/dev/zero of=/dev/sda'"
  # spec 0016: blocked today, must stay blocked
  force_block 'cat x >/dev/sda'
  force_block ': > /home/santiago/f'
  force_block 'echo hi
find / -delete'
  block 'rm -rf \
/'
  block 'rm -rf $(echo /)'
  block 'rm -rf `echo ~`'
  force_block "rm -rf \$'/'"
  force_block 'rm -rf "$HOME"'
  force_block 'rm -rf "/home/x y"'
  block "bash -c ':(){ :|:& };:'"
  block "nohup sh -c 'mkfs.ext4 /dev/sdb1'"
  block "timeout 5 bash -c 'dd if=/dev/zero of=/dev/sda'"
  block 'cat <<EOF | sh
mkfs.ext4 /dev/sdb1
EOF'
  block "python3 -c \"import os; os.system('mkfs.ext4 /dev/sdb1')\""
  block 'echo "a; mkfs.ext4 /dev/sdb1" | sh'
  block 'git commit -m "x; mkfs.ext4 /dev/sdb1'
  # holes the cross check did not list: a quote inside a comment pairing with a later
  # one, an unquoted heredoc body that runs $(...), and a quoted executor name
  force_block "echo hi # don't
mkfs.ext4 /dev/sdb1 # won't"
  force_block 'cat <<EOF
$(mkfs.ext4 /dev/sdb1)
EOF'
  force_block "git commit -m \"\$(cat <<EOF
\$(mkfs.ext4 /dev/sdb1)
EOF
)\""
  block "'bash' -c 'mkfs.ext4 /dev/sdb1'"
  # found by the security review of the first build: text that becomes a command
  block "\$(printf 'mkfs.ext4 /dev/sdb1')"
  block "\`echo 'mkfs.ext4 /dev/sdb1'\`"
  block "X='mkfs.ext4 /dev/sdb1'; \$X"
  block "X='mkfs.ext4 /dev/sdb1'; \"\$X\""
  block "{sh,-c,'mkfs.ext4 /dev/sdb1'}"
  block "X='kfs.ext4 /dev/sdb1'; m\$X; Y='mkfs.ext4 /dev/sdb1'"
  block "\"\$(cat <<'EOF'
bash
EOF
)\" -c 'mkfs.ext4 /dev/sdb1'"
  block "X='mkfs.ext4 /dev/sdb1'; \$\\
X"
  block "X='mkfs.ext4 /dev/sdb1'; \"\$\\
X\""
  block "\$\\
(printf 'mkfs.ext4 /dev/sdb1')"
  block "X='mkfs.ext4 /dev/sdb1'; cat <<EOF
\$(\$X)
EOF"
  # a variable in a quoted heredoc commit body is literal text, not an expansion
  allow_data "git commit -m \"\$(cat <<'EOF'
rm -rf \"\$HOME\" was never blocked when quoted
EOF
)\""
  # AC-3 forms the cases above do not reach: <<- with tab stripped delimiter, two heredocs
  # on one line (bodies in operator order), the \EOF and "EOF" commit delimiters
  allow_data "$(printf 'cat <<-EOF > notes.md\n\tmkfs.ext4 /dev/sda\n\tEOF')"
  allow_data 'cat <<A - <<B > notes.md
mkfs.ext4 /dev/sda
A
dd if=/dev/zero of=/dev/sda
B'
  allow_data "git commit -m \"\$(cat <<\\EOF
rm -rf ~
EOF
)\""
  allow_data "git commit -m \"\$(cat <<\"EOF\"
rm -rf ~
EOF
)\""
  # never data: $"..." strings, the rest of the heredoc operator's own line
  force_block "printf \$\"mkfs.ext4 /dev/sdb1\""
  force_block 'cat <<EOF > notes.md; mkfs.ext4 /dev/sdb1
text
EOF'
  # AC-4: a heredoc with no end line or an unclosed quote means the raw scan. An unmatched
  # $( is not its own case: its outer quote is always unclosed too, so it fails the same way
  raw_block() {
    block "$1"
    printf '%s' "$1" | python3 -I -c "$SCANNER" force >/dev/null 2>&1 \
      && { echo "FAIL scanner parsed, should fall back to raw: $1"; fail=1; }
    return 0
  }
  raw_block 'cat <<EOF
mkfs.ext4 /dev/sdb1'
  raw_block 'git commit -m "x; mkfs.ext4 /dev/sdb1'
  # AC-2: more executors, by basename too
  block "eval 'mkfs.ext4 /dev/sdb1'"
  block "echo 'mkfs.ext4 /dev/sdb1' | /bin/sh"
  block "ssh host 'mkfs.ext4 /dev/sdb1'"
  block "awk 'BEGIN { system(\"mkfs.ext4 /dev/sdb1\") }'"
  block "echo 'mkfs.ext4 /dev/sdb1' | xargs -0 env"
  # no python3 means the raw scan, as before (AC-4)
  [[ "$(PATH=/nonexistent blank_data 'echo "rm -rf /"' 2>/dev/null)" == 'echo "rm -rf /"' ]] \
    || { echo "FAIL missing python3 did not fall back to raw"; fail=1; }
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

if reason="$(guard "$CMD")"; then
  exit 0
else
  echo "BLOCKED by block-destructive.sh: $reason" >&2
  echo "This command can delete or destroy data. If intentional, run it yourself with the ! prefix." >&2
  exit 2
fi
