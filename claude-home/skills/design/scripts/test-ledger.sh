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

# Skill calls are verified against the session transcript, so the suite writes one, shaped
# like Claude Code's own: an assistant record holding a Skill tool_use. Millisecond stamps,
# because init records a float start time and a whole-second stamp can land before it.
PROJ="$HOME/.claude/projects/p"; mkdir -p "$PROJ"
invoke(){  # invoke <session[/subagents/x]> <skill> [args] [iso-timestamp]
  printf '{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"tool_use","name":"Skill","input":{"skill":"%s","args":"%s"}}]}}\n' \
    "${4:-$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)}" "$2" "${3:-}" >> "$PROJ/$1.jsonl"
}
invoke_all(){
  for s in minimalist-ui ui-ux-pro-max frontend-design impeccable assets animate design-gate review-animations cro; do invoke "$1" $s; done
  invoke "$1" impeccable "critique src"; invoke "$1" impeccable "audit src"
}
say(){  # say <session> <text> - a user record, as a person typing it
  printf '{"type":"user","timestamp":"%s","message":{"role":"user","content":"%s"}}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$2" >> "$PROJ/$1.jsonl"
}
critique(){  # critique <target> <total> [mtime offset s] - a report shaped like impeccable's own
  mkdir -p "$1/.impeccable/critique"
  local f="$1/.impeccable/critique/$(date -u +%Y-%m-%dT%H-%M-%S)-${RANDOM}__surface.md"
  printf -- '---\ntotal_score: %s\nmax_score: 40\n---\n# Critique\n' "$2" > "$f"
  [ -n "${3:-}" ] && touch -d "@$(( $(date +%s) + $3 ))" "$f"
}
# review-animations is only required once it is model-invocable; model that state explicitly.
mkdir -p "$HOME/.claude/skills/review-animations"
printf -- '---\nname: review-animations\n---\n' > "$HOME/.claude/skills/review-animations/SKILL.md"

echo "T: no active run -> gate must not interfere"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "gate exits 0 with no pointer" "$?" "0"

echo "T: init"
mkdir -p "$T/src"; echo "body{}" > "$T/src/a.css"
bash $LED init "$T" >/dev/null 2>&1; chk "init exit" "$?" "0"
invoke_all "$CLAUDE_CODE_SESSION_ID"
bash $LED set preview SKIPPED not-client-facing >/dev/null 2>&1
critique "$T" 34; printf '{"assets":[]}' > "$T/.design/assets-manifest.json"
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
for s in detect reference direction tokens assemble assets conversion; do bash $LED set $s RAN "ev-$s" >/dev/null 2>&1; done
bash $LED set motion RAN "skill=animate; register=product-ui; ev-motion" >/dev/null 2>&1
bash $LED set gate RAN ".design/audit-report.md" >/dev/null 2>&1
bash $LED check >/dev/null 2>&1; chk "check still fails - no audit report on disk" "$?" "1"

echo "T: empty report does not satisfy the gate"
: > "$T/.design/audit-report.md"
bash $LED check >/dev/null 2>&1; chk "empty report rejected" "$?" "1"

echo "T: real report passes"
printf '# Audit\nscore: 8/10\nmotion: 0 findings against review-animations standards\nfindings: 0 critical\n' > "$T/.design/audit-report.md"
bash $LED check >/dev/null 2>&1; chk "check passes with a real report" "$?" "0"

echo "T: staleness - editing after the audit re-opens the gate"
sleep 1.1; echo "body{color:red}" > "$T/src/a.css"
bash $LED check >/dev/null 2>&1; chk "edit after audit fails the check" "$?" "1"
printf '{"session_id":"%s"}' "$CLAUDE_CODE_SESSION_ID" | bash $GATE >/dev/null 2>&1; chk "gate blocks on stale audit" "$?" "2"

echo "T: gate releases a clean run and clears the pointer"
sleep 1.1; printf '# Audit\nscore: 8/10\nmotion: 0 findings against review-animations standards\n' > "$T/.design/audit-report.md"
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
invoke_all iso-A
CLAUDE_CODE_SESSION_ID=iso-A bash $LED set preview SKIPPED not-client-facing >/dev/null 2>&1
critique "$TA" 34
a=$(cat "$HOME/.claude/.design-active-iso-A" 2>/dev/null)
b=$(cat "$HOME/.claude/.design-active-iso-B" 2>/dev/null)
[ -n "$a" ] && [ -n "$b" ] && [ "$a" != "$b" ] && ok "each session has its own pointer" || no "each session has its own pointer"
for s in detect reference direction tokens source assemble; do CLAUDE_CODE_SESSION_ID=iso-A bash $LED set $s RAN ev >/dev/null 2>&1; done
CLAUDE_CODE_SESSION_ID=iso-A bash $LED set assets SKIPPED no-imagery-needed >/dev/null 2>&1
CLAUDE_CODE_SESSION_ID=iso-A bash $LED set motion SKIPPED no-motion-warranted >/dev/null 2>&1
CLAUDE_CODE_SESSION_ID=iso-A bash $LED set conversion SKIPPED not-marketing-surface >/dev/null 2>&1
mkdir -p "$TA/.design"; printf '# Audit\nscore 9/10\nmotion: none in scope\n' > "$TA/.design/audit-report.md"
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

# ---------------------------------------------------------------------------
# motion. The first real run built a scroll-driven animation while invoking zero motion
# skills, and its gate reported "motion: clean - this round added zero animation" over
# animation that existed. Routing was prose; nothing checked either half.
TM=$(mktemp -d)
echo
echo "T: motion must be built by a skill and audited against review-animations"
export CLAUDE_CODE_SESSION_ID=mot-1
bash $LED init "$TM" >/dev/null 2>&1
invoke_all mot-1
bash $LED set preview SKIPPED not-client-facing >/dev/null 2>&1; critique "$TM" 34
bash $LED set motion RAN "isotipo reveal via animation-timeline" >/dev/null 2>&1; chk "motion RAN without a skill is refused" "$?" "1"
bash $LED set motion RAN "we animate the logo" >/dev/null 2>&1;              chk "a bare 'animate' in prose does not count" "$?" "1"
bash $LED set motion RAN "skill=animate; register=product-ui; isotipo reveal" >/dev/null 2>&1; chk "motion RAN with skill=animate accepted" "$?" "0"
for s in detect reference direction tokens source assemble; do bash $LED set $s RAN ev >/dev/null 2>&1; done
bash $LED set assets SKIPPED no-imagery-needed >/dev/null 2>&1
bash $LED set conversion SKIPPED not-marketing-surface >/dev/null 2>&1
mkdir -p "$TM/.design"
printf '# Audit\nscore 9/10\n' > "$TM/.design/audit-report.md"
bash $LED set gate RAN .design/audit-report.md >/dev/null 2>&1
bash $LED check "$TM" 2>&1 | grep -q "no 'motion:' line" && ok "report without a motion line blocks" || no "report without a motion line blocks"
printf '# Audit\nscore 9/10\nmotion: clean - this round added zero animation\n' > "$TM/.design/audit-report.md"
bash $LED set gate RAN .design/audit-report.md >/dev/null 2>&1
bash $LED check "$TM" >/dev/null 2>&1; chk "motion RAN + 'clean, added zero' blocks" "$?" "1"
printf '# Audit\nscore 9/10\nmotion: 2 findings against review-animations standards (src/styles/motion.css)\n' > "$TM/.design/audit-report.md"
bash $LED set gate RAN .design/audit-report.md >/dev/null 2>&1
bash $LED check "$TM" >/dev/null 2>&1; chk "motion RAN + cited review-animations passes" "$?" "0"
rm -f "$HOME/.claude/.design-active-mot-"* "$HOME/.claude/.design-last-mot-"*

# ---------------------------------------------------------------------------
# invocation. Evidence text is self-report: the first real client run logged "lens=minimalist-ui" and
# shipped motion invoking neither, and the refactor silently dropped impeccable's critique
# and audit. The ledger now reads the session transcript.
TS=$(mktemp -d)
echo
echo "T: a RAN row needs its skills in the transcript, not in the evidence"
export CLAUDE_CODE_SESSION_ID=inv-1
invoke inv-1 cro "" "2020-01-01T00:00:00.000Z"      # from an earlier run - must not count
bash $LED init "$TS" >/dev/null 2>&1
bash $LED set preview SKIPPED not-client-facing >/dev/null 2>&1
bash $LED set assemble RAN "skill=impeccable; skill=frontend-design" 2>&1 | grep -q "never invoked" \
  && ok "naming skills in the evidence is refused" || no "naming skills in the evidence is refused"
invoke inv-1 impeccable
bash $LED set assemble RAN ev 2>&1 | grep -q '`frontend-design`' \
  && ok "half the required skills still refused, naming the missing one" || no "half the required skills still refused, naming the missing one"
invoke inv-1 frontend-design:frontend-design
bash $LED set assemble RAN ev >/dev/null 2>&1;   chk "plugin-namespaced invocation counts" "$?" "0"
bash $LED set conversion RAN ev >/dev/null 2>&1; chk "an invocation from before init does not count" "$?" "1"
printf '{"type":"user","timestamp":"%s","message":{"content":"<command-name>/cro</command-name>\\n<command-args></command-args>"}}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" >> "$PROJ/inv-1.jsonl"
bash $LED set conversion RAN ev >/dev/null 2>&1; chk "the user typing the slash command counts" "$?" "0"
invoke inv-1 minimalist-ui
bash $LED set direction RAN ev 2>&1 | grep -q '`design-dna`' \
  && ok "no board: direction also needs design-dna or ui-ux-pro-max" || no "no board: direction also needs design-dna or ui-ux-pro-max"
mkdir -p "$TS/brand"; echo "<html></html>" > "$TS/brand/brand-system.html"
bash $LED set direction RAN ev >/dev/null 2>&1;  chk "a signed board waives the catalogue skill" "$?" "0"

echo "T: the gate needs both impeccable modes, and review-animations when motion shipped"
printf '# Audit\nmotion: 1 findings against review-animations standards (src/a.css)\n' > "$TS/.design/audit-report.md"
invoke inv-1 animate; bash $LED set motion RAN "skill=animate; register=product-ui; x" >/dev/null 2>&1
invoke inv-1 design-gate; invoke inv-1 impeccable "critique src"
bash $LED set gate RAN .design/audit-report.md 2>&1 | grep -q '`impeccable audit`' \
  && ok "critique alone does not satisfy the audit mode" || no "critique alone does not satisfy the audit mode"
invoke inv-1 impeccable "audit src"
bash $LED set gate RAN .design/audit-report.md 2>&1 | grep -q '`review-animations`' \
  && ok "motion RAN: gate refused until review-animations is invoked" || no "motion RAN: gate refused until review-animations is invoked"
mkdir -p "$PROJ/inv-1/subagents"; invoke inv-1/subagents/agent-x review-animations
bash $LED set gate RAN .design/audit-report.md >/dev/null 2>&1; chk "an invocation inside a subagent counts" "$?" "0"

echo "T: a user-only review-animations is not demanded - that would trap every unattended run"
printf -- '---\nname: review-animations\ndisable-model-invocation: true\n---\n' > "$HOME/.claude/skills/review-animations/SKILL.md"
TU=$(mktemp -d); export CLAUDE_CODE_SESSION_ID=inv-u
bash $LED init "$TU" >/dev/null 2>&1
bash $LED set preview SKIPPED not-client-facing >/dev/null 2>&1
for s in animate design-gate; do invoke inv-u $s; done; invoke inv-u impeccable "critique x"; invoke inv-u impeccable "audit x"
bash $LED set motion RAN "skill=animate; register=product-ui; x" >/dev/null 2>&1
bash $LED set gate RAN .design/audit-report.md >/dev/null 2>&1; chk "flag present: gate not blocked on an uncallable skill" "$?" "0"
printf -- '---\nname: review-animations\n---\n' > "$HOME/.claude/skills/review-animations/SKILL.md"
rm -f "$HOME/.claude/.design-active-inv-u"

echo "T: check re-verifies, and adopt keeps the previous owner's calls"
export CLAUDE_CODE_SESSION_ID=inv-1
python3 -c "
import json; p='$TS/.design/run.json'; d=json.load(open(p))
d['steps']['assets']={'status':'RAN','evidence':'hand-edited'}; json.dump(d,open(p,'w'),indent=2)"
bash $LED check "$TS" 2>&1 | grep -q "step 'assets' RAN but" \
  && ok "check catches a hand-closed row with no invocation" || no "check catches a hand-closed row with no invocation"
rm -f "$HOME/.claude/.design-active-inv-1"
CLAUDE_CODE_SESSION_ID=inv-2 bash $LED adopt "$TS" >/dev/null 2>&1
CLAUDE_CODE_SESSION_ID=inv-2 bash $LED set assemble RAN "re-closed after adopt" >/dev/null 2>&1
chk "adopted run still sees the first session's invocations" "$?" "0"
rm -f "$HOME/.claude/.design-active-inv-"* "$HOME/.claude/.design-last-inv-"*

# ---------------------------------------------------------------------------
# quality. Every check above can pass on a bad page, and one did: a client redesign closed
# every row with a 25/40 critique, the owner's scroll reference rebuilt too faint to notice,
# a paid hero video unused, and nobody shown the first section before 34 commits landed.
TQ=$(mktemp -d); export CLAUDE_CODE_SESSION_ID=q-1
echo
echo "T: the owner sees the first section before the rest is built"
say q-1 "0 Work the redesign"                                   # a loop prompt, seen before the pause
bash $LED init "$TQ" >/dev/null 2>&1; invoke_all q-1
mkdir -p "$TQ/src"; echo "body{}" > "$TQ/src/a.css"
bash $LED set assemble RAN ev 2>&1 | grep -q "owner has seen" \
  && ok "assemble cannot close before the preview" || no "assemble cannot close before the preview"
bash $LED set preview RAN "looks fine" 2>&1 | grep -q "ledger.sh await" \
  && ok "preview RAN refused without await" || no "preview RAN refused without await"
bash $LED await "hero at 1440 and 390" >/dev/null 2>&1;              chk "await accepted" "$?" "0"
bash $LED check "$TQ" >/dev/null 2>&1;                                chk "check reports the pause (exit 3)" "$?" "3"
printf '{"session_id":"q-1"}' | bash $GATE >/dev/null 2>&1;           chk "Stop hook lets the turn end while paused" "$?" "0"
[ -f "$HOME/.claude/.design-active-q-1" ] && ok "and keeps the pointer" || no "and keeps the pointer"
say q-1 "0 Work the redesign"                                   # the loop wakes again
say q-1 "Stop hook feedback: design gate blocked"
mkdir -p "$PROJ/q-1/subagents"; say q-1/subagents/agent-z "Looks great, build the rest"
bash $LED set preview RAN "approved" >/dev/null 2>&1
chk "a repeated loop prompt, hook text or subagent is not the owner" "$?" "1"
say q-1 "[Image #3]"
bash $LED set preview RAN "approved" >/dev/null 2>&1
chk "a screenshot with no words is not a reply" "$?" "1"
say q-1 "[Image #4] me gusta, sigue con el resto"                # a real reply that opens with a screenshot
bash $LED check "$TQ" >/dev/null 2>&1;                                chk "once the owner replied the gate re-engages" "$?" "1"
bash $LED set preview RAN "owner approved the hero" >/dev/null 2>&1;  chk "preview closes after a real reply" "$?" "0"
python3 -c "
import json,sys; d=json.load(open('$TQ/.design/run.json'))
sys.exit(0 if 'me gusta' in d['steps']['preview']['evidence'] and 'awaiting' not in d else 1)" \
  && ok "their words are recorded and the pause cleared" || no "their words are recorded and the pause cleared"

echo "T: motion is built at the strength of its register"
bash $LED set motion RAN "skill=animate; hero parallax" 2>&1 | grep -q "needs its register" \
  && ok "motion RAN needs a register" || no "motion RAN needs a register"
bash $LED set motion RAN "skill=animate; register=marketing; parallax" 2>&1 | grep -q "motion-reference.md first" \
  && ok "marketing motion needs the reference measured first" || no "marketing motion needs the reference measured first"
printf '| effect | reference | ours |\n| parallax | 50%% | 45%% |\n' > "$TQ/.design/motion-reference.md"
bash $LED set motion RAN "skill=animate; register=marketing; parallax" >/dev/null 2>&1
chk "marketing motion with a measured reference accepted" "$?" "0"

echo "T: an asset that was made has to ship"
bash $LED set assets RAN "skill=assets" >/dev/null 2>&1
M="$TQ/.design/assets-manifest.json"
printf '{"assets":[{"id":"hero-loop","model":"veo","status":"approved-draft"},{"id":"ref","model":"x","status":"approved-as-reference"}]}' > "$M"
out=$(bash $LED check "$TQ" 2>&1)
printf '%s' "$out" | grep -q "'hero-loop' was generated or fetched but records no shipped files" \
  && ok "a generated asset with no shipped files blocks" || no "a generated asset with no shipped files blocks"
printf '%s' "$out" | grep -q "'ref'" && no "a reference-only asset is exempt" || ok "a reference-only asset is exempt"
printf '{"assets":[{"id":"hero-loop","model":"veo","status":"approved","files":["public/video/hero-loop.mp4"]},{"id":"old","source":"x","unused":"superseded"}]}' > "$M"
out=$(bash $LED check "$TQ" 2>&1)
printf '%s' "$out" | grep -q "hero-loop.mp4 is not referenced" \
  && ok "a paid asset nothing uses blocks the gate" || no "a paid asset nothing uses blocks the gate"
printf '%s' "$out" | grep -q "'old'" && no "an asset with a stated unused reason is exempt" || ok "an asset with a stated unused reason is exempt"
echo '<video src="/video/hero-loop.mp4"></video>' > "$TQ/src/index.html"
bash $LED check "$TQ" 2>&1 | grep -q "hero-loop" && no "a used asset passes" || ok "a used asset passes"

echo "T: the gate grades the result, not only that the audits ran"
for s in detect reference direction tokens source assemble conversion; do bash $LED set $s RAN ev >/dev/null 2>&1; done
RPT="$TQ/.design/audit-report.md"
report(){ printf '# Audit\nmotion: 0 findings against review-animations standards\n%b\n' "$1" > "$RPT"; }
report "motion-reference: 0 effects below reference"
bash $LED set gate RAN .design/audit-report.md >/dev/null 2>&1
bash $LED check "$TQ" 2>&1 | grep -q "no impeccable critique report" && ok "no saved critique blocks" || no "no saved critique blocks"
critique "$TQ" 25
bash $LED check "$TQ" 2>&1 | grep -q "scored 25/40" && ok "a 25/40 critique blocks" || no "a 25/40 critique blocks"
critique "$TQ" 34 5
bash $LED check "$TQ" 2>&1 | grep -q "scored" && no "a newer critique over the bar supersedes it" || ok "a newer critique over the bar supersedes it"
report "motion-reference: 3 effects below reference (parallax, curtain, line reveal)"
bash $LED check "$TQ" 2>&1 | grep -q "3 effect(s) built below" && ok "effects below the reference block" || no "effects below the reference block"
report ""
bash $LED check "$TQ" 2>&1 | grep -q "no 'motion-reference:" && ok "marketing run without the motion-reference line blocks" || no "marketing run without the motion-reference line blocks"
printf 'primary: example.com\n' > "$TQ/.design/reference-lock.md"
report "motion-reference: 0 effects below reference"
bash $LED check "$TQ" 2>&1 | grep -q "never put beside" && ok "a reference lock demands the side-by-side" || no "a reference lock demands the side-by-side"
report "motion-reference: 0 effects below reference\nreference: 4 sections compared against example.com, 2 worse"
bash $LED check "$TQ" 2>&1 | grep -q "2 section(s) judged worse" && ok "a section worse than the reference blocks" || no "a section worse than the reference blocks"
report "motion-reference: 0 effects below reference\nreference: 4 sections compared against example.com, 0 worse"
bash $LED check "$TQ" >/dev/null 2>&1; chk "a run that clears every bar passes" "$?" "0"

echo "T: any owner question pauses the run, and a released run can be re-armed"
bash $LED await "pick a pattern: A, B or C" >/dev/null 2>&1;        chk "await works after the preview is closed" "$?" "0"
bash $LED check "$TQ" >/dev/null 2>&1;                               chk "a second owner question pauses the gate (exit 3)" "$?" "3"
say q-1 "A"
bash $LED check "$TQ" >/dev/null 2>&1;                               chk "the owner's answer resumes grading" "$?" "0"
python3 -c "
import json; p='$TQ/.design/run.json'; d=json.load(open(p)); d['blocks']=3; d['escaped']=True
json.dump(d,open(p,'w'),indent=2)"
rm -f "$HOME/.claude/.design-active-q-1"
bash $LED adopt "$TQ" >/dev/null 2>&1
[ -f "$HOME/.claude/.design-active-q-1" ] && ok "re-arming restores the pointer" || no "re-arming restores the pointer"
python3 -c "import json,sys; sys.exit(0 if json.load(open('$TQ/.design/run.json'))['blocks']==0 else 1)" \
  && ok "re-arming resets the block count" || no "re-arming resets the block count"
bash $LED check "$TQ" >/dev/null 2>&1;                               chk "the re-armed run passes the full gate" "$?" "0"
python3 -c "import json,sys; d=json.load(open('$TQ/.design/run.json')); sys.exit(0 if d.get('escaped') is False and d.get('escape_cleared') else 1)" \
  && ok "a full pass clears the unaudited mark" || no "a full pass clears the unaudited mark"
bash $LED show "$TQ" 2>/dev/null | grep -q "then passed the full gate" \
  && ok "show says it was released once, then passed" || no "show says it was released once, then passed"
rm -f "$HOME/.claude/.design-active-q-"* "$HOME/.claude/.design-last-q-"*
echo; echo "TOTAL pass=$PASS fail=$FAIL"; [ $FAIL -eq 0 ] || exit 1
