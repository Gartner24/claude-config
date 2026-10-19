#!/usr/bin/env bash
# SessionStart (clear), spec 0057: a rollover used to need /clear AND /resume-from-clear.
# This loads the waiting handover slot into the fresh session so /clear alone resumes it.
# Read only on the slot: /resume-from-clear consumes it, so a second clear never resumes twice.
# Always exits 0; prints nothing unless a live slot (at most 1 day old) is waiting.

if [ "${1:-}" = --test ]; then
  real="$HOME/.claude/skills/jjstack/bin/jjstack-rollover-slot"
  [ -x "$real" ] || { echo "FAIL: $real missing, the fixtures need the real slot script" >&2; exit 1; }
  self="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
  fx="$(mktemp -d)"
  trap 'rm -rf "$fx"' EXIT
  mkdir -p "$fx/.claude/skills/jjstack/bin" "$fx/work"
  cp "$real" "$fx/.claude/skills/jjstack/bin/"
  slot() { env -u TM_WORKER_NAME HOME="$fx" "$@"; }
  hook() { printf '{"cwd":"%s","source":"clear"}' "$fx/work" | env -u WF_RUN HOME="$fx" "$@" bash "$self"; }
  ctx() { python3 -I -c "import json,sys; print(json.load(sys.stdin)['hookSpecificOutput']['additionalContext'])"; }
  bad=0
  ok() { if [ "$1" = 0 ]; then echo "ok: $2"; else echo "FAIL: $2" >&2; bad=1; fi; }

  out="$(hook env -u TM_WORKER_NAME)"
  [ -z "$out" ]; ok $? "no slot prints nothing"

  path="$(printf 'Next: finish AC-3\n**Previous transcript:** /tmp/prev-1234.jsonl\n' | slot "$fx/.claude/skills/jjstack/bin/jjstack-rollover-slot" --cwd "$fx/work" write)"
  out="$(hook env -u TM_WORKER_NAME)"
  printf '%s' "$out" | python3 -I -c "import json,sys; json.load(sys.stdin)"; ok $? "live slot prints valid JSON"
  [ "$(printf '%s' "$out" | python3 -I -c "import json,sys; print(json.load(sys.stdin)['hookSpecificOutput']['hookEventName'])")" = SessionStart ]; ok $? "event name is SessionStart"
  text="$(printf '%s' "$out" | ctx)"
  case "$text" in "Handover waiting: run the /resume-from-clear steps now"*) r=0 ;; *) r=1 ;; esac; ok $r "text opens with the resume line"
  # The transcript path is also inside the slot text, so look only at the header before the data.
  case "${text%%<<<HANDOVER DATA>>>*}" in *"Slot: $path"$'\n'"Previous transcript: /tmp/prev-1234.jsonl"$'\n') r=0 ;; *) r=1 ;; esac; ok $r "header names slot path and transcript"
  printf 'not json' | env -u WF_RUN HOME="$fx" bash "$self" >"$fx/bad.out"; r=$?
  [ "$r" = 0 ] && [ ! -s "$fx/bad.out" ]; ok $? "bad stdin exits 0 and prints nothing"
  case "$text" in *$'<<<HANDOVER DATA>>>\nNext: finish AC-3'*$'<<<END HANDOVER DATA>>>'*) r=0 ;; *) r=1 ;; esac; ok $r "slot text wrapped in data markers"
  [ -f "$path" ]; ok $? "slot not consumed"

  git -C "$fx/work" init -q
  mkdir -p "$fx/work/docs/scope"
  touch "$fx/work/AGENTS.md"
  ws() { printf '{"cwd":"%s","source":"%s"}' "$fx/work" "$1" | (cd "$fx/work" && env -u TM_WORKER_NAME HOME="$fx" bash "$(dirname "$self")/workflow-start.sh"); }
  case "$(ws clear)" in *"run /scope"*) r=1 ;; *) r=0 ;; esac; ok $r "workflow-start skips /scope on clear with a live slot"
  case "$(ws startup)" in *"run /scope"*) r=0 ;; *) r=1 ;; esac; ok $r "workflow-start keeps /scope on startup"

  out="$(hook env WF_RUN=1)"
  [ -z "$out" ]; ok $? "WF_RUN set prints nothing"

  printf 'no transcript here\n' | slot "$fx/.claude/skills/jjstack/bin/jjstack-rollover-slot" --cwd "$fx/work" write >/dev/null
  text="$(hook env -u TM_WORKER_NAME | ctx)"
  case "$text" in *"Previous transcript"*|*jsonl*) r=1 ;; *"$path"*) r=0 ;; *) r=1 ;; esac; ok $r "no transcript line names only the slot"

  python3 -I -c "print('a' * 6999 + 'é' * 2000)" | slot "$fx/.claude/skills/jjstack/bin/jjstack-rollover-slot" --cwd "$fx/work" write >/dev/null
  out="$(hook env -u TM_WORKER_NAME)"
  data="$(printf '%s' "$out" | python3 -I -c "import json,sys; t=json.load(sys.stdin)['hookSpecificOutput']['additionalContext']; print(len(t.split('<<<HANDOVER DATA>>>\n')[1].split('\n<<<END HANDOVER DATA>>>')[0].encode()))")"
  [ "$data" -le 7100 ] && [ "$data" -ge 6990 ]; ok $? "big slot cut to 7000 bytes on a character boundary ($data)"
  case "$(printf '%s' "$out" | ctx)" in *"[cut: "*" bytes shown; Read the slot file"*) r=0 ;; *) r=1 ;; esac; ok $r "big slot says it was cut"
  printf 'small\n' | slot "$fx/.claude/skills/jjstack/bin/jjstack-rollover-slot" --cwd "$fx/work" write >/dev/null
  case "$(hook env -u TM_WORKER_NAME | ctx)" in *"[cut: "*) r=1 ;; *) r=0 ;; esac; ok $r "small slot has no cut note"
  case "$(printf '%s' "$out" | ctx)" in *"$path"*) r=0 ;; *) r=1 ;; esac; ok $r "big slot keeps the slot path"

  touch -d '2 days ago' "$path"
  out="$(hook env -u TM_WORKER_NAME)"
  [ -z "$out" ]; ok $? "slot 2 days old prints nothing"
  case "$(ws clear)" in *"run /scope"*) r=0 ;; *) r=1 ;; esac; ok $r "workflow-start keeps /scope on clear with a stale slot"
  rm -f "$path"

  wpath="$(printf 'worker work\n' | slot env TM_WORKER_NAME=w1 "$fx/.claude/skills/jjstack/bin/jjstack-rollover-slot" --cwd "$fx/work" write)"
  out="$(hook env -u TM_WORKER_NAME)"
  [ -z "$out" ]; ok $? "plain session ignores a worker's slot"
  case "$(hook env TM_WORKER_NAME=w1 | ctx)" in *"$wpath"*"worker work"*) r=0 ;; *) r=1 ;; esac; ok $r "TM_WORKER_NAME finds its own slot"

  rm "$fx/.claude/skills/jjstack/bin/jjstack-rollover-slot"
  out="$(hook env TM_WORKER_NAME=w1)"
  [ -z "$out" ]; ok $? "slot script missing prints nothing"

  [ "$bad" = 0 ] && echo "handover-start: all self-checks passed"
  exit "$bad"
fi

[ -n "${WF_RUN:-}" ] && exit 0
cwd="$(python3 -I -c "import json,sys; print(json.load(sys.stdin).get('cwd') or '')" 2>/dev/null)"
[ -n "$cwd" ] || exit 0
rslot="$HOME/.claude/skills/jjstack/bin/jjstack-rollover-slot"
[ -x "$rslot" ] || exit 0
path="$(timeout 2 "$rslot" --cwd "$cwd" status --max-age-days 1 2>/dev/null)"
[ -n "$path" ] || exit 0
LC_ALL=C.UTF-8 python3 -I - "$path" <<'PY' 2>/dev/null
import json, sys
path = sys.argv[1]
raw = open(path, "rb").read()
# Research 60: additionalContext is capped near 10,000 characters; the slot path stays so the rest is readable.
body = raw[:7000].decode("utf-8", "ignore")
if len(raw) > 7000:
    # A silent cut lost the Re-arm section of a 7.8k handover; say so, so the successor reads the file.
    body += "\n[cut: %d of %d bytes shown; Read the slot file for the rest before anything else]" % (len(body.encode()), len(raw))
prev = next((l.split("**Previous transcript:**", 1)[1].strip()
             for l in raw.decode("utf-8", "replace").splitlines() if "**Previous transcript:**" in l), "")
head = ("Handover waiting: run the /resume-from-clear steps now (this replaces typing it; "
        "the skill still consumes the slot).\nSlot: " + path)
if prev:
    head += "\nPrevious transcript: " + prev
text = head + "\n<<<HANDOVER DATA>>>\n" + body + "\n<<<END HANDOVER DATA>>>"
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
PY
exit 0
