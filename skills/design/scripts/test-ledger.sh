#!/usr/bin/env bash
# Self-check for ledger.sh + gate.sh. Fails loudly. No framework.
# Resolve relative to this file, not to one machine's absolute paths.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LED="$HERE/ledger.sh"
GATE="$HERE/gate.sh"

# Run against a FAKE HOME. Both scripts derive their pointer files from $HOME, so this is
# the only way the suite provably cannot touch real state. It previously backed up
# .design-active but not .design-last - which ledger.sh rewrites on every init - and
# clobbered the real one, so `ledger.sh show` with no argument would render a throwaway
# test ledger. gate.sh also resolves LEDGER from $HOME, so the tree is symlinked in.
T=$(mktemp -d); PASS=0; FAIL=0
REAL_HOME="$HOME"
export HOME="$T/home"
mkdir -p "$HOME/.claude/skills/design"
ln -s "$HERE" "$HOME/.claude/skills/design/scripts"
# The pointer is per-session. Pin one so the suite is deterministic and can never
# collide with a real run happening in another session while it executes.
export CLAUDE_CODE_SESSION_ID="test-$$"
POINTER="$HOME/.claude/.design-active-$CLAUDE_CODE_SESSION_ID"

ok(){ PASS=$((PASS+1)); printf "  ok   %s\n" "$1"; }
no(){ FAIL=$((FAIL+1)); printf "  FAIL %s\n" "$1"; }
chk(){ if [ "$2" = "$3" ]; then ok "$1"; else no "$1 (got '$2', want '$3')"; fi; }

echo "T: no active run -> gate must not interfere"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "gate exits 0 with no pointer" "$?" "0"

echo "T: init"
mkdir -p "$T/src"; echo "body{}" > "$T/src/a.css"
bash $LED init "$T" >/dev/null 2>&1; chk "init exit" "$?" "0"
[ -f "$T/.design/run.json" ] && ok "run.json written" || no "run.json written"
[ -f "$POINTER" ] && ok "pointer written" || no "pointer written"

echo "T: incomplete run is caught"
bash $LED check >/dev/null 2>&1; chk "check fails while PENDING" "$?" "1"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "gate BLOCKS while PENDING" "$?" "2"

echo "T: closed skip vocabulary"
# Assert on the MESSAGE, not just the exit code: an empty allowed-set and an
# unrecognised token both exit 1, so exit code alone cannot tell them apart and the
# test would stay green if 'gate' were quietly given a legal skip reason.
bash $LED set gate SKIPPED not-marketing-surface 2>&1 | grep -q "may never be skipped" \
  && ok "gate rejected by the empty allowed-set rule" || no "gate rejected by the empty allowed-set rule"
bash $LED set detect SKIPPED whatever 2>&1 | grep -q "may never be skipped" \
  && ok "detect rejected by the empty allowed-set rule" || no "detect rejected by the empty allowed-set rule"
# Defense in depth: a hand-edited ledger must not get past the check either.
python3 -c "
import json; p='$T/.design/run.json'; d=json.load(open(p))
d['steps']['gate']={'status':'SKIPPED','reason':'not-marketing-surface'}
json.dump(d,open(p,'w'),indent=2)"
bash $LED check 2>&1 | grep -q "did not run" \
  && ok "hand-edited gate skip still blocks" || no "hand-edited gate skip still blocks"
python3 -c "
import json; p='$T/.design/run.json'; d=json.load(open(p))
d['steps']['gate']={'status':'PENDING'}
json.dump(d,open(p,'w'),indent=2)"
bash $LED set source SKIPPED i-felt-like-it >/dev/null 2>&1;      chk "invented reason rejected" "$?" "1"
bash $LED set source SKIPPED not-react >/dev/null 2>&1;           chk "reason not in this step's set rejected" "$?" "1"
bash $LED set source SKIPPED no-component-need >/dev/null 2>&1;   chk "legal skip accepted" "$?" "0"
bash $LED set nonsense RAN x >/dev/null 2>&1;                     chk "unknown step rejected" "$?" "1"

echo "T: close the rest"
for s in detect reference direction tokens assemble assets motion conversion; do bash $LED set $s RAN "ev-$s" >/dev/null 2>&1; done
bash $LED set gate RAN ".design/audit-report.md" >/dev/null 2>&1
bash $LED check >/dev/null 2>&1; chk "check still fails - no audit report on disk" "$?" "1"

echo "T: empty report does not satisfy the gate"
: > "$T/.design/audit-report.md"
bash $LED check >/dev/null 2>&1; chk "empty report rejected" "$?" "1"

echo "T: real report passes"
printf '# Audit\nscore: 8/10\nfindings: 0 critical\n' > "$T/.design/audit-report.md"
bash $LED check >/dev/null 2>&1; chk "check passes with a real report" "$?" "0"

echo "T: staleness - editing after the audit re-opens the gate"
sleep 1.1; echo "body{color:red}" > "$T/src/a.css"
bash $LED check >/dev/null 2>&1; chk "edit after audit fails the check" "$?" "1"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "gate blocks on stale audit" "$?" "2"

echo "T: gate releases a clean run and clears the pointer"
sleep 1.1; printf '# Audit\nscore: 8/10\n' > "$T/.design/audit-report.md"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "gate exits 0 when clean" "$?" "0"
[ -f "$POINTER" ] && no "pointer cleared after pass" || ok "pointer cleared after pass"

echo "T: escape hatch - never trap a session forever"
bash $LED init "$T" >/dev/null 2>&1
rm -f "$T/.design/audit-report.md"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "block 1" "$?" "2"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "block 2" "$?" "2"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "block 3 releases" "$?" "0"
python3 -c "
import json,sys; d=json.load(open('$T/.design/run.json'))
sys.exit(0 if d.get('escaped') is True else 1)" && ok "escaped:true recorded" || no "escaped:true recorded"
bash $LED show "$T" 2>/dev/null | grep -q "NOT fully audited" && ok "show warns about the escape" || no "show warns about the escape"

echo "T: stale ledger (>24h) never holds a session"
bash $LED init "$T" >/dev/null 2>&1
touch -d "2 days ago" "$T/.design/run.json"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "abandoned run released" "$?" "0"


# ---------------------------------------------------------------------------
# brand pipeline
KIT="${BRAND_KIT:-$REAL_HOME/projects/freelance/website-build-templates}"
FIX="$KIT/scripts/fixtures"
export BRAND_VALIDATOR="$KIT/scripts/check-brand-system.py"
if [ ! -d "$FIX" ] || [ ! -f "$BRAND_VALIDATOR" ]; then
  echo "  SKIP brand-validator tests - kit not found at $KIT (set BRAND_KIT)"; SKIP_BRAND=1
fi
T2=$(mktemp -d)
echo
echo "T: brand pipeline - init and step vocabulary"
bash $LED init "$T2" --pipeline brand >/dev/null 2>&1; chk "brand init" "$?" "0"
python3 -c "
import json,sys;d=json.load(open('$T2/.design/run.json'))
sys.exit(0 if d.get('pipeline')=='brand' and 'emit' in d['steps'] and 'detect' not in d['steps'] else 1)" \
  && ok "brand steps loaded, design steps absent" || no "brand steps loaded, design steps absent"
bash $LED set detect RAN x >/dev/null 2>&1;  chk "design step rejected in brand run" "$?" "1"
bash $LED set emit SKIPPED internal-project 2>&1 | grep -q "may never be skipped" \
  && ok "emit rejected by the empty allowed-set rule" || no "emit rejected by the empty allowed-set rule"
bash $LED set logo SKIPPED logo-supplied >/dev/null 2>&1; chk "logo-supplied accepted" "$?" "0"
bash $LED set signoff SKIPPED internal-project >/dev/null 2>&1; chk "internal-project accepted" "$?" "0"

echo "T: brand gate validates CONTENT, not just existence"
for s in brief reference direction type color imagery surfaces audit; do bash $LED set $s RAN "ev" >/dev/null 2>&1; done
bash $LED set emit RAN brand-system.html >/dev/null 2>&1
bash $LED check >/dev/null 2>&1; chk "no board on disk -> blocked" "$?" "1"

cp $FIX/fixture-inter.html "$T2/brand-system.html"
bash $LED check 2>&1 | grep -q "does not conform" \
  && ok "non-conforming board blocked by the validator" || no "non-conforming board blocked by the validator"

cp $FIX/fixture-broken.html "$T2/brand-system.html"
bash $LED check >/dev/null 2>&1; chk "broken clamp board blocked" "$?" "1"

cp $FIX/fixture-conforming.html "$T2/brand-system.html"
bash $LED check >/dev/null 2>&1; chk "conforming board passes the gate" "$?" "0"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "Stop hook releases a conforming brand run" "$?" "0"


# ---------------------------------------------------------------------------
# session isolation. Two /design runs at once used to fight over one global
# pointer: the last init won and the other session's Stop hook gated on a ledger
# from a repo it was not in. Observed live with two real runs 77 seconds apart.
TA=$(mktemp -d); TB=$(mktemp -d)
echo
echo "T: two sessions do not share a pointer"
CLAUDE_CODE_SESSION_ID=iso-A bash $LED init "$TA" >/dev/null 2>&1
CLAUDE_CODE_SESSION_ID=iso-B bash $LED init "$TB" >/dev/null 2>&1
a=$(cat "$HOME/.claude/.design-active-iso-A" 2>/dev/null)
b=$(cat "$HOME/.claude/.design-active-iso-B" 2>/dev/null)
[ -n "$a" ] && [ -n "$b" ] && [ "$a" != "$b" ] && ok "each session has its own pointer" || no "each session has its own pointer"
for s in detect reference direction tokens source assemble; do CLAUDE_CODE_SESSION_ID=iso-A bash $LED set $s RAN ev >/dev/null 2>&1; done
CLAUDE_CODE_SESSION_ID=iso-A bash $LED set assets SKIPPED no-imagery-needed >/dev/null 2>&1
CLAUDE_CODE_SESSION_ID=iso-A bash $LED set motion SKIPPED no-motion-warranted >/dev/null 2>&1
CLAUDE_CODE_SESSION_ID=iso-A bash $LED set conversion SKIPPED not-marketing-surface >/dev/null 2>&1
mkdir -p "$TA/.design"; printf '# Audit\nscore 9/10\n' > "$TA/.design/audit-report.md"
CLAUDE_CODE_SESSION_ID=iso-A bash $LED set gate RAN .design/audit-report.md >/dev/null 2>&1
printf '{"session_id":"iso-A"}' | bash $GATE >/dev/null 2>&1; chk "session A releases when A is done" "$?" "0"
printf '{"session_id":"iso-B"}' | bash $GATE >/dev/null 2>&1; chk "session B still blocks - unaffected by A" "$?" "2"
rm -f "$HOME/.claude/.design-active-iso-"* "$HOME/.claude/.design-last-iso-"*

# ---------------------------------------------------------------------------
# ledger ownership. Per-session pointers stopped two sessions in DIFFERENT repos
# colliding; they did not stop two sessions in the SAME repo. The second init
# archived the first's rows and the first then wrote into the second's ledger,
# both believing it was theirs, neither told.
TO=$(mktemp -d); mkdir -p "$TO/sub"
echo
echo "T: a repo's ledger is owned by one session"
CLAUDE_CODE_SESSION_ID=own-1 bash $LED init "$TO" >/dev/null 2>&1
CLAUDE_CODE_SESSION_ID=own-1 bash $LED set detect RAN "own-1 work" >/dev/null 2>&1
CLAUDE_CODE_SESSION_ID=own-2 bash $LED init "$TO" >/dev/null 2>&1; chk "second session cannot init the same repo" "$?" "1"
CLAUDE_CODE_SESSION_ID=own-2 bash $LED init "$TO" 2>&1 | grep -q "already has a design run open" \
  && ok "and it says which session owns it" || no "and it says which session owns it"
( cd "$TO/sub" && CLAUDE_CODE_SESSION_ID=own-2 bash $LED set direction RAN "intrusion" >/dev/null 2>&1 )
chk "second session cannot write the owner's ledger" "$?" "1"
python3 -c "
import json,sys
d=json.load(open('$TO/.design/run.json'))
sys.exit(0 if d.get('session')=='own-1' and d['steps']['direction']['status']=='PENDING'
         and d['steps']['detect'].get('evidence')=='own-1 work' else 1)" \
  && ok "owner's rows survive the attempt" || no "owner's rows survive the attempt"
rm -f "$HOME/.claude/.design-active-own-1"
CLAUDE_CODE_SESSION_ID=own-2 bash $LED init "$TO" >/dev/null 2>&1; chk "a dead owner releases the repo" "$?" "0"
rm -f "$HOME/.claude/.design-active-own-"* "$HOME/.claude/.design-last-own-"*

# adopt: a run started before per-session pointers existed has no owner and no
# pointer, so its gate sits inert. Adopting must fix that in place, without
# re-initialising - a live session cannot afford to lose its ledger or its context.
TAD=$(mktemp -d)
echo
echo "T: adopt takes over an ownerless run in place"
CLAUDE_CODE_SESSION_ID=ad-1 bash $LED init "$TAD" >/dev/null 2>&1
CLAUDE_CODE_SESSION_ID=ad-1 bash $LED set detect RAN "work worth keeping" >/dev/null 2>&1
python3 -c "
import json,pathlib
p=pathlib.Path('$TAD/.design/run.json'); d=json.loads(p.read_text()); d.pop('session',None)
p.write_text(json.dumps(d,indent=2))"                      # simulate a pre-upgrade ledger
rm -f "$HOME/.claude/.design-active-ad-1"
printf '{"session_id":"ad-2"}' | bash $GATE >/dev/null 2>&1; chk "ownerless run: gate is inert" "$?" "0"
CLAUDE_CODE_SESSION_ID=ad-2 bash $LED adopt "$TAD" >/dev/null 2>&1; chk "adopt succeeds" "$?" "0"
printf '{"session_id":"ad-2"}' | bash $GATE >/dev/null 2>&1; chk "adopted run: gate active again" "$?" "2"
python3 -c "
import json,sys
d=json.load(open('$TAD/.design/run.json'))
sys.exit(0 if d['steps']['detect'].get('evidence')=='work worth keeping' else 1)" \
  && ok "adopt preserved the existing rows" || no "adopt preserved the existing rows"
CLAUDE_CODE_SESSION_ID=ad-3 bash $LED adopt "$TAD" >/dev/null 2>&1; chk "cannot adopt a live owner's ledger" "$?" "1"
rm -f "$HOME/.claude/.design-active-ad-"* "$HOME/.claude/.design-last-ad-"*

# ---------------------------------------------------------------------------
# token-leak applicability. The check proves a CSS custom-property token layer is
# not bypassed. On a stack whose tokens live in a JS object it printed a count
# anyway - "319 lines across 387 files" on a styled-components repo - which is
# neither a finding nor a pass. A gate that answers a question it cannot evaluate
# is worse than one that declines to.
TL=/home/santiago/.claude/skills/design-gate/scripts/token-leak.sh
TT=$(mktemp -d)
echo
echo "T: token-leak knows when it does not apply"
mkdir -p "$TT/js"; printf 'export const t={c:"#ff0000",d:"200ms"}\n' > "$TT/js/theme.js"
bash $TL "$TT/js" >/dev/null 2>&1; chk "no tokens.css -> NOT APPLICABLE" "$?" "2"
bash $TL "$TT/js" 2>&1 | grep -q "NOT APPLICABLE" && ok "and says so plainly" || no "and says so plainly"
mkdir -p "$TT/css"; printf ':root{--brand:oklch(62%% .19 27)}\n' > "$TT/css/tokens.css"
printf '.a{color:var(--brand)}\n' > "$TT/css/ok.css"
bash $TL "$TT/css" >/dev/null 2>&1; chk "tokens.css present, clean -> pass" "$?" "0"
printf '.b{color:#ff0000}\n' > "$TT/css/bad.css"
bash $TL "$TT/css" >/dev/null 2>&1; chk "tokens.css present, leaky -> fail" "$?" "1"
echo; echo "TOTAL pass=$PASS fail=$FAIL"; [ $FAIL -eq 0 ] || exit 1
