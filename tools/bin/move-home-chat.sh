#!/usr/bin/env bash
# Spec 0067: move the ~/.claude home chat (chats, memory, runner rules, approvals) into claude-config's
# live chat folder, after a full backup, and link the two old folder names to it.
# Run it yourself, once, in a plain terminal with every Claude chat and wf closed:
#   bash ~/claude-config/tools/bin/move-home-chat.sh
# Every path is built from $HOME, so the tests run it against a fake home.
set -euo pipefail
shopt -s dotglob nullglob

P="$HOME/.claude/projects"
LIVE="$P/-home-santiago-dotfiles-claude-config"
OLD="$P/-home-santiago--claude"
COPY="$P/-home-santiago-claude-config"
REPO="$HOME/claude-config"
RSRC="$HOME/.claude/.claude/CLAUDE.md"
RTGT="$REPO/CLAUDE.local.md"
ASRC="$HOME/.claude/.claude/settings.local.json"
ATGT="$REPO/.claude/settings.local.json"
HEADER="# Runner rules for the home chat (private, not committed; spec 0067)"
DATE="$(date +%F)"
BACKUP="$HOME/Documents/claude-chats-backup-$DATE.tar.gz"

moved=0 skipped=0 notes=0 appended=0 added=0

die() { echo "move-home-chat: $*" >&2; exit 1; }
tmp=""
trap 'rm -f "$tmp"' EXIT
# A source folder is merged only while it is a real folder; once it is a link it is done.
is_src() { [[ -d "$1" && ! -L "$1" ]]; }
is_link() { [[ -L "$1" && "$(readlink "$1")" == "$LIVE" ]]; }
rules_text() { printf '%s\n' "$HEADER"; tail -n +2 "$RSRC"; }

# ---- checks (AC-1): nothing is written before all of them pass, except the lock file
missing=()
for t in pgrep flock jq tar cmp; do
  command -v "$t" >/dev/null 2>&1 || missing+=("$t")
done
((${#missing[@]} == 0)) || die "missing tools: ${missing[*]}"

exec 9>"$HOME/.claude/move-home-chat.lock"
flock -n 9 || die "another copy holds $HOME/.claude/move-home-chat.lock"

busy=()
for pid in $(pgrep -x claude || true); do
  [[ "$pid" == "$$" || "$pid" == "$PPID" ]] || busy+=("$pid (claude: $(ps -o args= -p "$pid" || true))")
done
# wf runs as ~/.local/bin/wf or as an installed or repo wf.py
for pid in $(pgrep -f 'python[0-9.]* .*(/\.local/bin/wf|/wf\.py)( |$)' || true); do
  [[ "$pid" == "$$" || "$pid" == "$PPID" ]] || busy+=("$pid (wf)")
done
if ((${#busy[@]})); then
  printf 'busy: pid %s\n' "${busy[@]}" >&2
  die "close every Claude chat and wf first"
fi

if is_link "$OLD" && is_link "$COPY" && [[ ! -e "$RSRC" && ! -e "$ASRC" ]]; then
  echo "already moved"
  exit 0
fi

for f in .claude/settings.local.json CLAUDE.local.md; do
  git -C "$REPO" check-ignore -q "$f" || die "$REPO/$f is not ignored by git there; refusing"
done

for s in "$OLD" "$COPY"; do
  [[ ! -e "$s" && ! -L "$s" ]] || is_src "$s" || is_link "$s" \
    || die "$s is neither a folder nor a link to $LIVE; fix it by hand"
done

for j in "$ASRC" "$ATGT"; do
  [[ ! -f "$j" ]] || jq empty "$j" 2>/dev/null || die "$j does not parse; nothing changed"
done
# only permissions.allow is carried; refuse rather than drop deny or ask rules
[[ ! -f "$ASRC" ]] || jq -e '(.permissions // {}) | keys - ["allow"] == []' "$ASRC" >/dev/null \
  || die "$ASRC has permission rules other than allow; move them by hand first"

srcs=()
is_src "$OLD" && srcs+=("$OLD")
is_src "$COPY" && srcs+=("$COPY")

sizes=()
for d in "$OLD" "$LIVE" "$COPY"; do [[ -e "$d" ]] && sizes+=("$d"); done
need=0
for d in "${sizes[@]}"; do need=$((need + $(du -sk "$d" | cut -f1))); done
docs="$HOME/Documents"
[[ -d "$docs" ]] || docs="$HOME"
free="$(df -Pk "$docs" | awk 'NR==2 {print $4}')"
((free >= need)) || die "only ${free}K free in $docs, the backup needs ${need}K"

scan=("${srcs[@]}")
[[ -d "$LIVE" ]] && scan+=("$LIVE")
if ((${#scan[@]})); then
  odd="$(find "${scan[@]}" -mindepth 1 ! -type f ! -type d -print)"
  [[ -z "$odd" ]] || die "not a regular file or folder: $odd"
fi

# Clash pass (AC-3, AC-4, AC-6): find every clash before anything moves.
clashes=()
for s in "${srcs[@]}"; do
  while IFS= read -r -d '' p; do
    r="${p#"$s"/}"
    [[ "$r" == memory/MEMORY.md ]] && continue
    t="$LIVE/$r"
    if [[ "$s" == "$COPY" && ! -e "$t" ]] && is_src "$OLD" && [[ -e "$OLD/$r" ]]; then
      t="$OLD/$r"
    fi
    [[ -e "$t" ]] || continue
    if [[ -d "$p" ]]; then
      [[ -d "$t" ]] || clashes+=("$p vs $t")
    elif [[ ! -f "$t" ]] || ! cmp -s "$p" "$t"; then
      clashes+=("$p vs $t")
    fi
  done < <(find "$s" -mindepth 1 -print0)
done
if [[ -f "$RSRC" && -e "$RTGT" ]] && ! cmp -s <(rules_text) "$RTGT"; then
  clashes+=("$RSRC vs $RTGT")
fi
if ((${#clashes[@]})); then
  printf 'clash: %s\n' "${clashes[@]}" >&2
  die "${#clashes[@]} clash(es), nothing changed"
fi

# ---- backup (AC-2); one already written today is kept, it holds the state before the first run
paths=()
for f in "$OLD" "$LIVE" "$COPY" "$HOME/.claude/.claude/" "$ATGT" "$RTGT"; do
  [[ -e "$f" || -L "$f" ]] && paths+=("${f#/}")
done
if [[ -f "$BACKUP" ]]; then
  tar tzf "$BACKUP" >/dev/null || die "$BACKUP does not read back; move it away and run again"
  echo "backup exists, kept: $BACKUP"
else
  mkdir -p "$HOME/Documents"
  part="$BACKUP.part"
  if ! (umask 077 && tar -czf "$part" -C / "${paths[@]}"); then
    rm -f "$part"
    die "backup failed, nothing moved"
  fi
  chmod 600 "$part"
  if ! n="$(tar tzf "$part" | wc -l)"; then
    rm -f "$part"
    die "backup does not read back, nothing moved"
  fi
  mv "$part" "$BACKUP"
  echo "backup: $BACKUP ($n entries)"
fi

# Merge folder $1 into $2 file by file. $3 is chats or memory, $4 the depth.
merge() {
  local s="$1" d="$2" kind="$3" lvl="$4" e n
  for e in "$s"/*; do
    n="${e##*/}"
    if ((lvl == 0)); then
      [[ "$kind" == chats && "$n" == memory ]] && continue
      [[ "$kind" == memory && "$n" == MEMORY.md ]] && continue
    fi
    if [[ ! -e "$d/$n" ]]; then
      mv "$e" "$d/$n"
      if [[ "$kind" == memory ]]; then notes=$((notes + 1)); elif ((lvl == 0)); then moved=$((moved + 1)); fi
    elif [[ -d "$e" && -d "$d/$n" ]]; then
      merge "$e" "$d/$n" "$kind" $((lvl + 1))
      rmdir "$e"
    elif [[ -f "$e" && -f "$d/$n" ]] && cmp -s "$e" "$d/$n"; then
      rm "$e"
      skipped=$((skipped + 1))
    else
      die "clash: $e vs $d/$n"
    fi
  done
}

# Append the lines of index $1 that LIVE's index lacks (trailing spaces trimmed), under one heading.
append_index() {
  local idx="$LIVE/memory/MEMORY.md" have="$LIVE/memory/MEMORY.md" lines
  [[ -f "$idx" ]] || have=/dev/null
  lines="$(awk -v first="$have" '
    { sub(/[ \t]+$/, "") }
    FILENAME == first { seen[$0] = 1; next }
    $0 ~ /^[ \t]*$/ || ($0 in seen) { next }
    { seen[$0] = 1; print }' "$have" "$1")"
  [[ -n "$lines" ]] || return 0
  [[ -s "$idx" && -n "$(tail -c 1 "$idx")" ]] && echo >>"$idx"
  printf '\n## From ~/.claude (moved %s)\n\n%s\n' "$DATE" "$lines" >>"$idx"
  appended=$((appended + $(printf '%s\n' "$lines" | wc -l)))
}

# ---- chats (AC-3)
mkdir -p "$LIVE"
for s in "${srcs[@]}"; do merge "$s" "$LIVE" chats 0; done

# ---- memory (AC-4)
for s in "${srcs[@]}"; do
  is_src "$s/memory" || continue
  mkdir -p "$LIVE/memory"
  merge "$s/memory" "$LIVE/memory" memory 0
  idx="$s/memory/MEMORY.md"
  if [[ -f "$idx" ]]; then
    if [[ "$s" == "$COPY" && -f "$LIVE/memory/MEMORY.md" ]] && cmp -s "$idx" "$LIVE/memory/MEMORY.md"; then
      :
    else
      append_index "$idx"
    fi
    rm "$idx"
  fi
  rmdir "$s/memory"
done

mds=("$LIVE/memory"/*.md)
if ((${#mds[@]})); then
  awk '
    FNR == 1 { inb = ($0 == "---"); next }
    inb && $0 == "---" { inb = 0; next }
    inb && /^description:/ {
      n = FILENAME; sub(/.*\//, "", n)
      if ($0 in list) list[$0] = list[$0] "\t" n; else list[$0] = n
      inb = 0
    }
    END {
      for (k in list) {
        c = split(list[k], f, "\t")
        for (i = 1; i < c; i++) for (j = i + 1; j <= c; j++) print "possible duplicate: " f[i] " and " f[j]
      }
    }' "${mds[@]}"
fi

# ---- rules (AC-6)
if [[ -f "$RSRC" ]]; then
  if [[ ! -e "$RTGT" ]]; then
    tmp="$(mktemp "$REPO/.CLAUDE.local.md.XXXXXX")"
    rules_text >"$tmp"
    chmod 600 "$tmp"
    mv "$tmp" "$RTGT"
  fi
  cmp -s <(rules_text) "$RTGT" || die "$RTGT differs from the rules it should hold; $RSRC kept"
  rm "$RSRC"
fi

# ---- approvals (AC-7)
if [[ -f "$ASRC" ]]; then
  mkdir -p "$REPO/.claude"
  before=0
  [[ -f "$ATGT" ]] && before="$(jq '.permissions.allow // [] | length' "$ATGT")" || true
  tmp="$(mktemp "$REPO/.claude/.settings.local.json.XXXXXX")"
  prog='.permissions = (.permissions // {})
    | .permissions.allow = (reduce ((.permissions.allow // []) + ($s[0].permissions.allow // []))[] as $x
        ([]; if any(.[]; . == $x) then . else . + [$x] end))'
  if [[ -f "$ATGT" ]]; then
    ok=1; jq --slurpfile s "$ASRC" "$prog" "$ATGT" >"$tmp" || ok=0
  else
    ok=1; echo '{}' | jq --slurpfile s "$ASRC" "$prog" >"$tmp" || ok=0
  fi
  if ((ok == 0)) || ! jq empty "$tmp"; then
    rm -f "$tmp"
    die "approvals did not parse; $ASRC and $ATGT left as they were"
  fi
  mv "$tmp" "$ATGT"
  rm "$ASRC"
  added=$(($(jq '.permissions.allow | length' "$ATGT") - before))
fi

# ---- links (AC-5)
for s in "$OLD" "$COPY"; do
  is_link "$s" && continue
  if [[ -e "$s" || -L "$s" ]]; then
    rmdir "$s" || die "$s is not empty, left as it is"
  fi
  ln -s "$LIVE" "$s"
done

# ---- report (AC-9)
echo "top level entries moved: $moved"
echo "files skipped as identical: $skipped"
echo "notes moved: $notes"
echo "index lines appended: $appended"
echo "approvals added: $added"
echo "backup: $BACKUP"
