#!/usr/bin/env bash
# Stop hook for the design and brand pipelines. Exit 2 blocks the stop and hands
# stderr back to the model. Exits 0 instantly when no run is active, which is every
# other session - this must never interfere with unrelated work.
#
# Registered from design/SKILL.md and brand-system/SKILL.md frontmatter:
#   hooks: { Stop: [ { hooks: [ { type: command, command: "bash $HOME/.claude/skills/design/scripts/gate.sh" } ] } ] }
set -uo pipefail
LEDGER="$HOME/.claude/skills/design/scripts/ledger.sh"
POINTER="$HOME/.claude/.design-active"

cat >/dev/null 2>&1   # drain the hook's JSON stdin; we key off the pointer file

[ -f "$POINTER" ] || exit 0
RUN="$(head -n1 "$POINTER" 2>/dev/null || true)"
[ -n "$RUN" ] && [ -f "$RUN" ] || { rm -f "$POINTER"; exit 0; }

# A ledger older than 24h is abandoned, not active. Never hold a session hostage to it.
if [ -n "$(find "$RUN" -mmin +1440 2>/dev/null)" ]; then rm -f "$POINTER"; exit 0; fi

# Paths go to python as ARGV, never interpolated into a source literal. A directory
# named "Bob's site" used to raise SyntaxError here, which left BLOCKS empty, which made
# the escape-hatch comparison error out, which meant the counter never advanced and the
# hook blocked every stop until the 24h bail. It was also an injection vector.
PIPE="$(python3 -c 'import json,sys
print(json.load(open(sys.argv[1])).get("pipeline","design"))' "$RUN" 2>/dev/null || echo design)"

FAILURES="$(bash "$LEDGER" check 2>&1)"; STATUS=$?
if [ $STATUS -eq 0 ]; then rm -f "$POINTER"; exit 0; fi

BLOCKS="$(python3 -c 'import json,sys
p=sys.argv[1]; d=json.load(open(p)); d["blocks"]=d.get("blocks",0)+1
json.dump(d,open(p,"w"),indent=2); print(d["blocks"])' "$RUN" 2>/dev/null || true)"

# An unreadable or truncated ledger must RELEASE, not trap. Failing closed here means a
# corrupt state file costs the user every stop for 24h, and the corrupt case is reachable:
# this script's own json.dump truncates before writing, so an interrupted hook leaves an
# empty file behind.
case "$BLOCKS" in ''|*[!0-9]*) BLOCKS=3 ;; esac

if [ "$BLOCKS" -ge 3 ]; then
  python3 -c 'import json,sys
p=sys.argv[1]
try:
    d=json.load(open(p))
except Exception:
    d={}
d["escaped"]=True
json.dump(d,open(p,"w"),indent=2)' "$RUN" 2>/dev/null || true
  rm -f "$POINTER"
  echo "$PIPE gate: released after $BLOCKS block(s) without passing. Marked escaped:true in the ledger - tell the user this run was NOT fully audited and say which steps are open." >&2
  exit 0
fi

cat >&2 <<EOF
$PIPE gate: this $PIPE run is not finished. Do not present it yet.

$FAILURES

Close the open rows with: bash $LEDGER set <step> RAN <evidence>
A step may only be SKIPPED with a reason from its allowed set; the script rejects
anything else. The gate step has an empty allowed set - it must actually run.
Then print the closing table with: bash $LEDGER show
(block $BLOCKS of 3; after the third this releases and marks the run unaudited)
EOF
exit 2
