# Research G - Skill architecture that does not let steps get skipped

Target: rebuild `/design` (currently `~/claude-config/commands/design.md`, 35 lines,
8-step prose pipeline, symlinked to `~/.claude/commands/design.md`) so every
applicable step actually runs and the model is honest about which did not.

Everything below is labelled VERIFIED (read in official docs or in a working file on
this machine) or UNVERIFIED (secondhand, blog, or inference).

---

## 1. Official guidance

### 1.1 Where a slash command should live now

VERIFIED (code.claude.com/docs/en/skills): skills and slash commands are the same
mechanism in current Claude Code. A directory skill at
`~/.claude/skills/<name>/SKILL.md` is invoked as `/<name>`. The old
`.claude/commands/<file>.md` form is documented as **deprecated**, still working
"alongside skills".

This matters more than it looks. A `commands/*.md` file is a single file. It cannot
bundle reference files, cannot bundle scripts, and - the load-bearing one - **cannot
carry `hooks:` frontmatter**. Every enforcement mechanism ranked #1 below is
unavailable to the current `/design` purely because of its file form.

**Recommendation: `/design` becomes a skill directory.** Delete the
`~/.claude/commands/design.md` symlink when you do, so `/design` resolves to exactly
one thing.

### 1.2 Frontmatter fields - VERIFIED list

From code.claude.com/docs/en/skills. All fields are optional in Claude Code;
`name` defaults to the directory name.

| Field | Type | Notes |
|---|---|---|
| `name` | string | Display name. Defaults to directory name. |
| `description` | string | Drives auto-invocation. Combined with `when_to_use`, truncated at 1,536 chars in listings. |
| `when_to_use` | string | Appended to description, counts toward the same cap. |
| `argument-hint` | string | Autocomplete hint, e.g. `[issue-number]`. |
| `arguments` | string or list | Named positional args for `$name` substitution. |
| `disable-model-invocation` | boolean | `true` = only the user can invoke via `/name`. |
| `user-invocable` | boolean | `false` = hidden from the `/` menu, only Claude invokes. |
| `allowed-tools` | string or list | Tools usable without a permission prompt for the invoking turn only. |
| `disallowed-tools` | string or list | Tools removed from the pool while active. |
| `model` | string | Model override, or `inherit`. |
| `effort` | string | `low` \| `medium` \| `high` \| `xhigh` \| `max`. |
| `context` | string | `fork` = run in an isolated subagent context, no conversation history. |
| `agent` | string | Subagent type when `context: fork`. `Explore`, `Plan`, `general-purpose`, or a custom agent. |
| `background` | boolean | With `context: fork`, `false` waits for the result in the same turn. Requires v2.1.218+. |
| `hooks` | object | Hooks registered on invocation, **persist for the rest of the session**. |
| `paths` | string or list | Globs limiting auto-activation. |
| `shell` | string | `bash` (default) or `powershell` for `` !`cmd` `` blocks. |
| `metadata` | object | Free-form, not acted on. |
| `license` | string | Accepted, not acted on. |
| `compatibility` | string | Accepted, not acted on. Max 500 chars. |

Every field the task brief asked about is real: `name`, `description`,
`allowed-tools`, `model`, `argument-hint`, `disable-model-invocation` all VERIFIED.

**Portability caveat (VERIFIED).** Only `name`, `description`, `license`,
`compatibility`, `metadata`, `allowed-tools` are Agent Skills spec fields usable
outside Claude Code. Everything else - including `hooks`, `context`, `effort` - is a
Claude Code extension. The enforcement design below is deliberately Claude-Code-only.

**Doc conflict, both true.** platform.claude.com says `name` and `description` are
*required*, `name` max 64 chars lowercase/digits/hyphens with no reserved words
("anthropic", "claude"), `description` max 1,024 chars. code.claude.com says all
fields optional and quotes a 1,536-char listing cap. The platform limits are the
API/spec validator; Claude Code is lenient locally. Write to the strict limits.

### 1.3 Size, progressive disclosure, scripts - VERIFIED

From platform.claude.com/.../agent-skills/best-practices:

- Three loading levels: metadata always in context, SKILL.md body on trigger,
  bundled files only when read. Scripts execute without their source entering context.
- **SKILL.md body under 500 lines.** Split past that.
- **Keep references one level deep from SKILL.md.** Nested references
  (SKILL.md -> advanced.md -> details.md) cause partial reads: Claude previews with
  `head -100` instead of reading the file. This is a real failure mode for a router.
- Reference files over 100 lines get a table of contents at the top, so a partial read
  still shows the full scope.
- Directory convention: `SKILL.md`, `references/`, `scripts/`, `assets/`
  (VERIFIED in skill-creator's own "Anatomy of a Skill" block).
- "Make execution intent clear": `Run scripts/x.py` (execute) vs
  `See scripts/x.py for the algorithm` (read).
- Description quality drives invocation: it is how Claude picks among 100+ skills.
  Third person, always. Include *what it does* AND *when to use it*.
  skill-creator adds a blunt note: "currently Claude has a tendency to **undertrigger**
  skills... make the skill descriptions a little bit **pushy**."

### 1.4 Anthropic's own words on skipped steps - VERIFIED, and directly on point

Two passages from the official best-practices page are exactly the user's problem:

> For particularly complex workflows, provide a checklist that Claude can copy into
> its response and check off as it progresses.

> Clear steps prevent Claude from skipping critical validation. The checklist helps
> both Claude and you track progress through multistep workflows.

And the validator loop:

> **Common pattern:** Run validator -> fix errors -> repeat. This pattern greatly
> improves output quality.
> ... 4. **Only proceed when validation passes**

And "create verifiable intermediate outputs" (plan-validate-execute): have the model
emit a structured plan file, validate that file with a script, then execute. Listed
use cases: batch operations, destructive changes, high-stakes operations. A design
pipeline with a mandatory audit is exactly this shape.

### 1.5 anthropics/skills - structural patterns worth copying

Repo layout VERIFIED: `skills/` (19 skills), `spec/`, `template/`, `.claude-plugin/`.

**`frontend-design`** (read in full). Structure:
- Frontmatter is 2 fields plus `license`. No enforcement machinery at all - it is a
  *taste* skill, not a *process* skill, and it knows the difference.
- Its distinguishing move is a **calibration list of AI-design tells**, named with
  actual hex values: warm cream `#F4F1EA` + high-contrast serif + terracotta
  `#D97757`; near-black + acid green; broadsheet hairline rules; the SaaS-card kit;
  "template chrome" (tracked-out ALL-CAPS eyebrows, middle-dot meta strings,
  `#0B0B0B` standing in for black, `->` appended to buttons). Then: "All traits are
  legitimate for some briefs, but they are defaults rather than choices."
- **A mandatory two-pass process with a self-review gate between them**: brainstorm a
  compact token plan (4-6 named hex, typefaces + roles, ASCII wireframes, principles),
  then *review the plan against the brief before building* - "work through a similar
  prompt to see if you arrive somewhere similar" - "revise that part, **say what you
  changed and why**." Only then write code.
- Closes with restraint: "Spend your boldness in one place." "Remove one accessory."

**`webapp-testing`**. Structure worth stealing:
- A **decision tree in a code fence at the very top**, before any prose.
- Bundled scripts explicitly framed as black boxes: "**Always run scripts with
  `--help` first**. DO NOT read the source until you try running the script first...
  These scripts can be very large and thus pollute your context window."
- One "Common Pitfall" block with a single wrong/right pair.

**`skill-creator`**. Confirms the anatomy (`scripts/` `references/` `assets/`), the
three-level disclosure model, the 500-line rule, ToC for >300-line refs, and the
"push the description" note above. Its writing-style advice cuts against heavy-handed
enforcement: "Try to explain to the model why things are important in lieu of
heavy-handed musty MUSTs." Weigh that against superpowers' opposite finding in 2.3.

---

## 2. Why models skip steps, and what actually fixes it

### 2.1 The mechanism

UNVERIFIED but consistently reported: long tasks inflate the context window, early
instructions drift toward the edges, attention dilutes, and a step named in turn 1 is
gone by turn 40. Claude Code skips steps **silently** - no error, no notice. The
conditional steps go first because "skip this if not React" gives the model an
explicit, pre-authorized exit, and the terminal steps go next because by then the
model has produced something presentable and the gradient points at presenting it.

VERIFIED corroboration from Anthropic itself: the best-practices page's advice to
iterate on skills is built around exactly this observation - "I noticed Claude B forgot
to filter test accounts when I asked for a regional report. The Skill mentions
filtering, but maybe it's not prominent enough?" The suggested fixes escalate from
reorganizing for prominence, to "using stronger language such as 'MUST filter'", to
restructuring the workflow section. Prose prominence is the whole ladder there. It is
not enough on its own, which is why the ranking below puts a mechanical backstop first.

### 2.2 The candidates, ranked

Ranked by whether the mechanism can fail *silently*. A mechanism the model can no-op
without anyone noticing is worth less than one that produces an artifact or an error.

**#1 - (f) Hooks, specifically a `Stop` hook registered from the skill's own
frontmatter.** The only candidate that is not a request.

VERIFIED, official, and quotable
(claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more):

> When there's something that absolutely must not happen, an instruction is the wrong
> tool... A real guardrail needs to be deterministic, and the enforcement methods are
> hooks and permissions.

> The model choosing to run a formatter is different from the formatter running
> automatically.

Two hard constraints found while verifying, both of which change the design:
- **`PostToolUse` cannot block.** VERIFIED from the hooks reference event table. It
  can only inject `additionalContext`. Any plan that says "PostToolUse blocks until the
  audit passes" is wrong. The blockable events are `PreToolUse`, `UserPromptSubmit`,
  `UserPromptExpansion`, `Stop`, `SubagentStop`, `TeammateIdle`, `TaskCreated`,
  `TaskCompleted`, `ConfigChange`, `WorktreeCreate`, `PreModelSwitch`.
- **A hook can only check machine-readable state.** It cannot read the model's
  intent. So #1 is worthless without #2. They are one design, not two.

Cost: one shell script. Risk: skill hooks persist for the whole session (see 3.4).

**#2 - (b) A written artifact per step.** The thing that makes #1 possible, and
independently the highest-value soft mechanism because it converts "did you do it"
from a self-report into a `test -s`.

VERIFIED official backing: the plan-validate-execute / "create verifiable intermediate
outputs" pattern, and the whole feedback-loop section, are official best practice.
UNVERIFIED but convergent: the agent-framework literature's append-only ledger pattern
("each event is added to an append-only log... an agent's state is never volatile"),
and checkpoint-after-a-unit-of-work-succeeds.

This subsumes candidate **(d) state/checkpoint file** entirely. Do not build both. One
run ledger is simultaneously the per-step artifact, the state file, the compaction
survivor, and the hook's input.

**#3 - (a) Forced TodoWrite, one todo per step, as an explicit step 0.**

Strongest *field* evidence of any candidate, though it is n=1 and self-reported
(UNVERIFIED, mariogiancini.com): an 18-step `/daily-brief` command was silently
dropping trend-intelligence and network-health steps mid-run. Adding a Step 0 that
initializes a TodoWrite checklist of all steps *before any work begins* took skipped
steps to zero, reproducibly, in both Claude Code and Cursor. The framing is Gawande's
Checklist Manifesto: complex procedures fail without explicit tracking regardless of
expertise.

Endorsed independently by obra/superpowers (VERIFIED, read locally): "follow the skill
exactly. **If it has a checklist, create a todo per item.**" And by Anthropic's
best-practices checklist pattern (VERIFIED, quoted in 1.4).

Why it is #3 and not #1: a todo can be marked `completed` without the work happening.
It is a commitment device and a visibility device, not a gate. It makes skipping
*conspicuous*, which is most of the value, but it does not make it *impossible*.

**#4 - (g) Final self-audit table, each step RAN or SKIPPED-because-X.**

This is the half of the brief about honesty rather than execution, and it is cheap.
VERIFIED support from superpowers' `verification-before-completion`, whose "Common
Failures" table has the exact row: claim "Requirements met" requires "Line-by-line
checklist", *not sufficient*: "Tests passing".

Its power is that it converts silence into a claim. A skipped step currently costs the
model nothing because nobody notices; a table with a row per step forces it to either
write `RAN` (checkable) or write `SKIPPED: <reason>` (arguable). Both are better than
absence.

Upgrade that costs nothing: **make the skip reasons a closed vocabulary**, not prose.
`SKIPPED:not-react`, `SKIPPED:no-imagery`, `SKIPPED:internal-tool`. A closed set is
greppable by the hook in #1, and it blocks the "skipped because it seemed unnecessary"
escape hatch that free prose grants.

**#5 - (c) Gates that require quoting specific output before proceeding.**

Real, and it is the commitment principle in action, but it is a weaker version of #2:
the evidence lands in context instead of on disk, and context gets compacted. Use it
where a file would be silly (naming the register lens chosen, quoting the four hex
values from the locked palette) and use #2 where the evidence is substantial.

**#6 - (e) Subagent per step.** Genuinely double-edged, and the honest answer is
"for some steps, not as the architecture".

For: fresh context per step, cannot be summarized away, preserves the orchestrator's
context. superpowers' `subagent-driven-development` is built entirely on this -
"They should never inherit your session's context or history - you construct exactly
what they need." Claude Code supports it natively in skill frontmatter via
`context: fork` + `agent` + `background: false`.

Against (UNVERIFIED, from an agent-reliability survey): each handoff forces the
receiver to reconstruct context from a compressed summary rather than the full
reasoning trace, and reconstruction loss compounds; a cited Google Research figure of
39-70% degradation on sequential tasks. The explicit conclusion: "When tasks have
dependencies or shared context, a single-threaded linear agent often produces better
results."

A design pipeline is about as sequential and shared-context as work gets - the palette
locked in step 1 must survive to step 6. So:
- **Do not fork the assembly legs** (direction, source, assemble, motion). They need
  each other's state.
- **Do fork the audit leg.** Blindness is a feature there: an auditor with no memory of
  the reasoning that produced the page cannot rubber-stamp its own work. This is the
  same insight behind the user's own `/review-stack` blind lane.

**#7 - (h) Shorten the skill, push detail into reference files.**

Necessary hygiene, but be honest about the diagnosis: **the current `/design` is 35
lines.** Length is not why it skips steps. Ranking this as a fix for the stated problem
would be cargo cult.

Its real contribution here is indirect and worth having anyway: if step 3's detail
lives in `references/source.md` and the skill says "read it before sourcing", then
*reading the file is a tool call*, and a tool call is a trace. Progressive disclosure
becomes a cheap form of #2. Plus the router stays scannable as the pipeline grows.

### 2.3 One more mechanism the brief did not list: persuasion framing

VERIFIED (read locally at
`.../superpowers/6.3.0/skills/writing-skills/persuasion-principles.md`). Cites Meincke
et al. 2025, N=28,000 LLM conversations: persuasion techniques moved compliance
33% -> 72% (p < .001). The recommended combination for a discipline-enforcing skill is
**Authority + Commitment + Social Proof**, and explicitly *not* Liking or Reciprocity.

Concretely, and directly applicable to the audit step:
- Authority: bright-line, no-exception phrasing. Absolute language removes the
  "is this an exception?" question rather than answering it.
- Commitment: require an announcement. "When you find a skill, you MUST announce
  'I'm using [Skill Name]'." Public statement, then action.
- Social proof: the file's own example is uncannily on-topic -
  "Checklists without todo tracking = steps get skipped. **Every time.**"

Note the tension with Anthropic's skill-creator, which says "explain to the model why
things are important in lieu of heavy-handed musty MUSTs." Both are right for
different skill types: guidance skills should explain, discipline skills should be
absolute. `/design` is a hybrid - the taste steps are guidance, the gate is discipline.
Write them in different registers.

Also from superpowers, and cheap to copy: the **rationalization table**. A two-column
`Thought | Reality` or `Excuse | Reality` table that names the specific escape hatches
in advance. `using-superpowers` has twelve rows; `verification-before-completion` has
eight. For `/design` the rows write themselves: "The design already looks good" ->
"Looking good is not an audit result." "I'll note the a11y issues instead of running
the audit" -> "A note is not a report."

---

## 3. Hooks as hard enforcement

### 3.1 Event list - VERIFIED, and larger than the brief assumed

The brief's candidate list was PreToolUse, PostToolUse, Stop, SubagentStop,
SessionStart, UserPromptSubmit, PreCompact, Notification. All eight are real. The
actual documented set is much larger and includes `SessionEnd`, `PostCompact`,
`SubagentStart`, `PostToolUseFailure`, `PostToolBatch`, `PermissionRequest`,
`PermissionDenied`, `StopFailure`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`,
`UserPromptExpansion`, `PreModelSwitch`, `PostModelSwitch`, `ConfigChange`,
`CwdChanged`, `DirectoryAdded`, `FileChanged`, `InstructionsLoaded`, `MessageDisplay`,
`WorktreeCreate`, `WorktreeRemove`, `Elicitation`, `ElicitationResult`, `Setup`.

Only the blockable ones matter here (listed in 2.2). For this job: **`Stop`**.

### 3.2 Input / output contract - VERIFIED

Common input on stdin (command hooks) or POST body (http hooks):
`session_id`, `prompt_id`, `transcript_path`, `cwd`, `scratchpad_dir`,
`permission_mode`, `effort.level`, `hook_event_name`, plus `agent_id` / `agent_type`
inside a subagent.

`Stop` adds: `stop_reason`, `stop_hook_active`, `last_assistant_message`,
`num_tool_uses`, `tool_use_ids`.

Output: JSON on stdout. The modern envelope is
`hookSpecificOutput: { hookEventName, permissionDecision, permissionDecisionReason,
additionalContext, updatedInput, stopReason, continue, systemMessage, retry }`.
The simpler legacy form `{"decision":"block","reason":"..."}` with exit 0 is also
reported working for Stop (UNVERIFIED against the current reference, seen in a blog
implementation). **Exit code 2 is the documented simple path and the one to use**:

> To block the stop, exit 2. To let Claude stop normally, exit 0 or any other code
> besides 2. For events using the standard decision model, you can also return JSON,
> but for `Stop`, exit code 2 is the simplest way.

Exit codes: 0 = success (JSON honored if present); 1 or any non-zero except 2 =
non-blocking error, first stderr line surfaces in the transcript, action proceeds;
2 = blocking error on blockable events, and **exit 2 cannot be overridden by a JSON
`permissionDecision: "allow"`**. Blocking reason comes from the JSON `reason` if
present, otherwise from stderr.

Five handler types VERIFIED: `command`, `http`, `mcp_tool`, `prompt` (single-turn LLM
evaluation, default timeout 30s, `model` field, `$ARGUMENTS` = the hook input JSON),
`agent` (spawns a subagent with Read/Grep/Glob, marked **experimental**, default
timeout 60s). Common fields: `type`, `if` (permission-rule filter, **only evaluated on
tool events** - a hook with `if` set never runs on `Stop`), `timeout`,
`statusMessage`, `once`.

### 3.3 Can a Stop hook genuinely force the agent to keep working - VERIFIED yes, with
a specific and important escape valve

> To prevent infinite loops, Claude Code tracks whether a `Stop` hook is actively
> blocking. If a hook blocks and Claude responds again, and the hook blocks again
> **without the response changing in any way that might make the hook pass**, Claude
> Code stops the hook from running on the next `Stop` and stops the session instead.
> A response "changes" if its `text` field differs. **Claude Code compares only the
> text**, so a response with different tool calls but identical text counts as
> unchanged.

> The `stop_hook_active` field ... `true` means a prior `Stop` hook blocked, Claude
> responded again, and now this hook is running on the second `Stop`. Use it to avoid
> your own infinite loops, such as by exiting 0 instead of blocking again if
> `stop_hook_active` is already `true`.

Two design consequences, both non-obvious:

1. **The block reason must provoke different response text.** If it says "run the
   audit" twice and the model replies "Running the audit." twice, the harness disables
   the hook and stops. Make the reason name the *specific missing rows* so the reply
   necessarily differs: "gate=MISSING, conversion=MISSING". Naming state, not
   restating a rule.
2. `stop_hook_active` is *not* "always true" (one secondhand source claims that; it
   contradicts the doc, so treat that source as wrong). It signals a second consecutive
   Stop after a block. Blindly exiting 0 on it, as the common blog snippet does, hands
   the model a one-response bypass. Better: keep blocking but count blocks in the
   ledger and release after N, so the release is auditable rather than automatic.

### 3.4 Skill-scoped hooks - the finding that makes this buildable

VERIFIED in docs:

> Hooks can be defined directly in **skills** and **subagents** using frontmatter, in
> the same configuration format as settings-based hooks.
> - **Subagent hooks**: run only while that subagent is running, removed when it
>   finishes. Claude Code **converts a `Stop` hook here to `SubagentStop`**.
> - **Skill hooks**: registered when you or Claude invoke the skill and **kept running
>   for the rest of the session**, on turns after the skill's own turn as well. Set
>   `once: true` to remove after the first successful run.

`once` is **only honored in skill frontmatter** - ignored in settings files and in
agent frontmatter. VERIFIED.

VERIFIED by working example on this machine, which is better than the doc: three
installed skills already ship frontmatter hooks - `~/.claude/skills/careful/SKILL.md`,
`guard/SKILL.md`, `freeze/SKILL.md`. The exact working shape:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "bash $HOME/.claude/skills/gstack/careful/bin/check-careful.sh"
          statusMessage: "Checking for destructive commands..."
```

Note they use `$HOME/...` absolute paths, not `${CLAUDE_SKILL_DIR}`.
**UNVERIFIED: whether `${CLAUDE_SKILL_DIR}` expands inside a frontmatter hook
`command`.** It is documented as a substitution in skill *content*. Use the `$HOME`
form that is demonstrably working here. This is exactly the class of hallucinated
detail that breaks a skill silently.

Also note: `matcher` belongs to tool events. **Omit `matcher` for a `Stop` hook.**

Reported open issues (UNVERIFIED severity, titles only):
anthropics/claude-code#17688 skill frontmatter hooks not triggered inside plugins;
#39468 skill and agent frontmatter hooks silently not firing on Windows CLI;
#30874 skill-scoped PreToolUse hooks persist after the skill completes (which is the
documented behavior, but people trip on it). Mitigation for the last one is built into
the design below: the gate script exits 0 in under a millisecond when no design run is
in flight, so persistence costs nothing.

### 3.5 Concretely: could a Stop hook enforce "the design audit ran before you
presented"?

Yes, with one condition: **the audit must leave a file.** The hook cannot see that the
model thought about accessibility. It can see that
`.design/audit-report.md` exists, is non-empty, and is newer than the last file the
pipeline wrote.

What it checks, in order, all cheap:

1. `.design/run.json` missing -> exit 0. No design run in flight. This is the common
   case and it keeps the persistent hook free.
2. `stop_hook_active` is true and `blocks` in the ledger is >= 2 -> exit 0, but write
   an `ESCAPED` marker into the ledger so the release shows up in the final table.
   Never wedge a session.
3. Every step in the ledger has a status. Any step still `PENDING` -> block, naming
   those steps.
4. Any `SKIPPED` whose reason token is not in that step's allowed set -> block, naming
   the step and listing the legal tokens.
5. `gate` is the one step with an empty allowed-skip set. `gate.status != RAN` ->
   block.
6. `gate.evidence` file must exist, be non-empty, and have an mtime >= the newest
   mtime under the target directory. This is the anti-rubber-stamp check: it catches
   "ran the audit, then kept editing", which is the realistic failure once the model
   learns the hook exists.

Realistic example (`scripts/gate.sh`, the whole thing):

```bash
#!/usr/bin/env bash
# Stop hook for /design. Exit 2 blocks the stop.
set -u
IN=$(cat)
CWD=$(printf '%s' "$IN" | jq -r '.cwd // "."')
LEDGER="$CWD/.design/run.json"
[ -f "$LEDGER" ] || exit 0

ACTIVE=$(printf '%s' "$IN" | jq -r '.stop_hook_active // false')
BLOCKS=$(jq -r '.blocks // 0' "$LEDGER")

if [ "$ACTIVE" = "true" ] && [ "$BLOCKS" -ge 2 ]; then
  jq '.escaped = true' "$LEDGER" > "$LEDGER.tmp" && mv "$LEDGER.tmp" "$LEDGER"
  echo "design gate released after 2 blocks; ledger marked escaped" >&2
  exit 0
fi

MISSING=$(jq -r '
  [ .steps | to_entries[]
    | select(.value.status == "PENDING"
          or (.value.status == "SKIPPED" and ((.value.reason // "") | length) == 0))
    | .key ] | join(", ")' "$LEDGER")

GATE=$(jq -r '.steps.gate.status // "PENDING"' "$LEDGER")
REPORT=$(jq -r '.steps.gate.evidence // ""' "$LEDGER")
TARGET=$(jq -r '.target // "."' "$LEDGER")

FAIL=""
[ -n "$MISSING" ] && FAIL="steps with no terminal status: $MISSING. "
[ "$GATE" != "RAN" ] && FAIL="${FAIL}gate=$GATE and gate may never be SKIPPED. "
if [ "$GATE" = "RAN" ]; then
  [ -s "$CWD/$REPORT" ] || FAIL="${FAIL}gate evidence '$REPORT' missing or empty. "
  NEWEST=$(find "$CWD/$TARGET" -type f -newer "$CWD/$REPORT" 2>/dev/null | head -1)
  [ -n "$NEWEST" ] && FAIL="${FAIL}files changed after the audit ran (e.g. $NEWEST); re-run it. "
fi

[ -z "$FAIL" ] && exit 0

jq '.blocks = ((.blocks // 0) + 1)' "$LEDGER" > "$LEDGER.tmp" && mv "$LEDGER.tmp" "$LEDGER"
echo "DESIGN GATE: $FAIL Fix the named items, update .design/run.json, then finish." >&2
exit 2
```

Registered from the skill's own frontmatter (no `matcher` on `Stop`):

```yaml
hooks:
  Stop:
    - hooks:
        - type: command
          command: "bash $HOME/.claude/skills/design/scripts/gate.sh"
          statusMessage: "Checking the design gate..."
```

The stderr text is the blocking reason (VERIFIED: "Blocking reason comes from the JSON
blocking decision's reason field if present, otherwise stderr text"), and because it
names the specific missing rows it differs between blocks, which keeps the harness's
text-comparison loop-breaker from firing prematurely.

**Optional second layer**, worth knowing but not worth building first: a `type: prompt`
Stop hook, evaluated by a fast model, asking "does the final message claim design work
is complete without citing an audit report path?" That catches semantic dodges the
file check misses. It is a second LLM in the loop, so it can be wrong; the file check
cannot. Ship the file check, add the prompt hook only if the model starts gaming it.

---

## 4. Skill composition

### 4.1 How skills reference each other - VERIFIED behavior, UNVERIFIED internals

Skills do not call each other. The `Skill` tool is invoked by the model, its response
injects the target skill's base path and SKILL.md body into context, and the model
continues. UNVERIFIED (mikhail.io, reverse-engineered): the tool takes a single
`command` string, the skill name **with no arguments**, and the description embeds an
`<available_skills>` list built from every skill's frontmatter with a `user`/`project`
location tag. Treat "no arguments" as likely-true but unconfirmed - `argument-hint` and
`$ARGUMENTS` exist precisely for user-typed `/name args`, and a model-invoked call may
not carry them. **Design the leaf skills so they read their input from the ledger file
rather than from arguments.** That sidesteps the question entirely and is more robust.

A skill invoking a slash command is the same thing: `/name` and the skill named `name`
resolve to one entry.

### 4.2 Router plus leaves, and how to keep the router short

The composition pattern is well attested:

- **obra/superpowers** (VERIFIED, read locally). `using-superpowers` is a pure router:
  no procedure at all, just the rule ("Invoke relevant skills BEFORE any response or
  action"), a priority ordering (process skills before implementation skills), a
  twelve-row rationalization table, and platform reference files. Leaves reference each
  other by name with explicit escalation language: `executing-plans` says
  "**REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch", and
  `writing-skills` says "**REQUIRED BACKGROUND:** You MUST understand
  superpowers:test-driven-development before using this skill."
- **plugin87/ux-ui-agent-skills** (UNVERIFIED, fetched summary). A two-tier model that
  maps almost exactly onto what `/design` needs: **user-invoked orchestrators**
  (`/brandkit`, `/redesign`, `/prototype`, `/governance`) and **model-invoked
  disciplines** (`/design-tokens`, `/design-component`, `/design-review`, `/a11y-audit`,
  `/apply-aesthetic`, `/ux-writing`, `/performance`, `/design-qa`), plus a separate
  `/gate` command that "runs the full accuracy gate, report real N/N".

The mechanics that keep a router short:

1. Each step in the router is 3-5 lines maximum: what it produces, which skill does it,
   what artifact it must leave, which reference file has the detail.
2. Detail lives in `references/<step>.md`, **one level deep only** (see 1.3 - deeper
   nesting causes partial reads).
3. Long conditional trees become a decision tree in a fence at the top, the
   `webapp-testing` move, not prose scattered through the steps.
4. Anything deterministic becomes a script called by name, never inlined.

Tradeoff, honestly: one big skill keeps shared state trivially available and costs one
file; a router plus leaves keeps each piece independently invocable and testable but
pays a Skill-tool round trip per leaf and risks the leaf losing the router's context.
**Split only where the leaf is independently useful.** For `/design` that is exactly two
places: assets, and the gate.

### 4.3 Forked leaves

`context: fork` + `agent: <type>` + `background: false` (VERIFIED frontmatter fields,
`background` requires v2.1.218+) makes a leaf skill run in an isolated subagent with no
conversation history and return its result in the same turn. That is the right shape for
the audit and the wrong shape for everything upstream of it (see 2.2 #6).

---

## 5. The two-command split: `/design` and `/assets`

### 5.1 The seam test

Make it a separate skill when **all** of these hold. Otherwise it is a reference file.

1. **Independently invocable.** Would you ever want it without the parent? Assets: yes,
   constantly - "regenerate the hero image", "make me a mascot". This alone is close to
   decisive.
2. **Distinct trigger vocabulary.** Would its `description` fire on phrasings that
   should not pull in the whole parent? "generate a hero image", "vectorize this logo",
   "I need product shots" should not drag in palette selection and a conversion audit.
3. **Its own dependency and tool surface.** Assets carries nano-banana/Gemini, vtracer,
   and the stock-photo fallback policy. None of that should be resident context during
   a pure CSS refactor.
4. **Its own artifact type.** Assets produces image files plus a manifest; the design
   pipeline produces code plus an audit report. Different outputs, different verification.

All four hold. **Split it.** By the same test, the register lens (step 2) fails #1 and
#2 and stays a reference file, and the motion picker (step 6) fails #1 and stays a
reference file with a decision tree.

By the same test the **gate** passes #1 (you want to audit a page you did not just
build), #2 ("audit this UI", "check a11y"), and #4 (it produces the audit report). It
should also be a leaf skill - and it gains the blind-fork property from 2.2 #6, which
is the strongest single answer to "the audit gets rubber-stamped".

### 5.2 Which side invokes which

**`/design` invokes `/assets`. The user does not have to.** Reasons:

- The user's stated failure mode is steps being skipped. Handing step 5 to the user
  guarantees it is skipped whenever they do not think of it.
- The ledger needs a row for assets either way. If the user invokes it out of band, the
  row says PENDING and the Stop hook blocks on a step the model cannot resolve. Bad.
- Model invocation requires only that `/assets` leaves `disable-model-invocation`
  unset (default false) and `user-invocable` unset (default true). Both modes work.

The handoff is through the ledger, not through arguments - which also dodges the
"can the Skill tool pass arguments" uncertainty in 4.1:

- `/design` writes the locked direction to `.design/direction.json` and sets
  `steps.assets.status = "PENDING"`.
- `/assets`, on invocation, reads `.design/direction.json` if it exists (palette,
  typefaces, register, subject matter) and otherwise asks or infers - it must work
  standalone.
- `/assets` writes `.design/assets-manifest.json` (one entry per generated file: path,
  prompt, source, post-processing) and sets `steps.assets` to `RAN` with that manifest
  as evidence, or `SKIPPED` with a token from its allowed set.
- `/assets` never calls back into `/design`. One-directional. A leaf that calls its
  router is how you get loops.

Standalone `/assets` runs write no ledger at all, so the Stop hook stays inert.

---

## 6. Existing design skills worth stealing from

**1. `anthropics/skills` -> `frontend-design`** (VERIFIED, read in full).
Steal: the **named calibration list of AI-design tells** with actual hex values, and
the framing "these are defaults rather than choices, and they appear regardless of
subject". Steal the **mandatory plan-then-review-the-plan-before-building pass**,
including "work through a similar prompt to see if you arrive somewhere similar" and
"say what you changed and why" - that is a self-audit gate placed *before* the build
rather than after it, which is a step the current `/design` does not have at all.
Steal the restraint close ("spend your boldness in one place", "remove one accessory").
Current `/design` has zero anti-default calibration and no plan-review pass.

**2. `plugin87/ux-ui-agent-skills`** (UNVERIFIED, summarized).
Steal: the **two-tier user-invoked / model-invoked split**; the separate **`/gate`
command that reports "real N/N"** rather than a prose verdict; **executable
validators** (`validate_contrast.py` for WCAG 2.2 AA in light and dark,
`axe_audit.mjs`, `verify_states.mjs`, `verify_focustrap.mjs`) so the a11y half of the
audit is a script exit code and not a judgement; the weighted six-dimension score
(hierarchy 20 / usability 20 / consistency 20 / responsive 10 / a11y 20 / perf 10);
and the honesty line worth copying verbatim in spirit - **"a passing gate is never
evidence of taste"**, with adversarial critique done from rendered screenshots rather
than source. Current `/design` has one prose sentence ("Run BOTH impeccable passes")
with no score, no N/N, and no script.

**3. `obra/superpowers` -> `verification-before-completion` + `using-superpowers`**
(VERIFIED, read locally).
Steal: the **Iron Law** block ("NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION
EVIDENCE... If you haven't run the verification command in this message, you cannot
claim it passes"); the numbered **Gate Function** (identify the command -> run it ->
read full output -> verify -> only then claim, with "skip any step = lying, not
verifying"); the **`Claim | Requires | Not Sufficient`** table; the
**rationalization table**; the **announce-the-skill commitment device**. Note also its
sharpest row for this use case: "Agent completed" requires "VCS diff shows changes",
not "Agent reports success" - which is the argument for the mtime check in 3.5.

**4. `anthropics/skills` -> `webapp-testing`** (VERIFIED, read in full).
Steal: the **decision tree in a fence at the top of the file**, before prose; and
**scripts as black boxes** - "Always run scripts with `--help` first. DO NOT read the
source until you try running the script first... They exist to be called directly as
black-box scripts rather than ingested into your context window." Exactly how the
design gate's validators should be treated.

**5. `anthropics/skills` -> `skill-creator`** (VERIFIED, read in full).
Steal: the **"push the description"** rule for undertriggering, and the explicit
anatomy (`scripts/` executable, `references/` loaded as needed, `assets/` used in
output). Useful as the checklist while writing the rebuild.

**What the current `/design` structurally lacks, consolidated:**
no checklist bootstrap; no artifact or trace per step; conditionals phrased as
pre-authorized exits with no forced declaration of the branch taken; a bare
"Never skip this step" with no commitment device and no mechanical backstop; no final
RAN/SKIPPED table; no reference files; no scripts; no hooks; and a file form
(`commands/*.md`) that structurally forbids the last three.

---

## The enforcement design

Five mechanisms, layered so each one catches what the one above it misses. The first
three are the ones that matter; four and five are cheap additions.

**Layer 0 - the ledger is the spine.** First action of `/design`, before any
conversation about style: run `scripts/ledger.sh init "<target dir>"`, which writes
`.design/run.json` with one row per pipeline step, every row `PENDING`, plus
`blocks: 0`. Nothing else in the design works without this file, and its existence is
what arms the hook.

```json
{
  "target": "src/app/pricing",
  "steps": {
    "direction":  {"status": "PENDING"},
    "register":   {"status": "PENDING"},
    "source":     {"status": "PENDING"},
    "assemble":   {"status": "PENDING"},
    "assets":     {"status": "PENDING"},
    "motion":     {"status": "PENDING"},
    "gate":       {"status": "PENDING"},
    "conversion": {"status": "PENDING"}
  },
  "blocks": 0
}
```

Each row closes as `{"status":"RAN","evidence":"<path or quoted token>"}` or
`{"status":"SKIPPED","reason":"<token>"}` via `scripts/ledger.sh set <step> ...`.

**Layer 1 - closed skip vocabulary.** Free-prose reasons are how a skip becomes
unfalsifiable. Each step gets a fixed allowed set, listed in the router and enforced by
the script:

| step | may be skipped when |
|---|---|
| `direction` | never |
| `register` | never |
| `source` | `not-react`, `no-component-need`, `magic-mcp-unavailable` |
| `assemble` | never |
| `assets` | `no-imagery-needed`, `assets-supplied` |
| `motion` | `no-motion-warranted`, `reduced-motion-only` |
| `gate` | **never** |
| `conversion` | `not-marketing-surface` |

`magic-mcp-unavailable` earns its place: the magic MCP failed to authenticate in this
very session, and without a token for it the model would have had to invent a prose
excuse or lie.

**Layer 2 - the Stop hook.** `scripts/gate.sh` from 3.5, registered in the skill's own
frontmatter, blocking on exit 2. It is the only part of this that is not a request. It
checks: every row terminal, every skip token legal, `gate` is `RAN`, the audit report
exists and is non-empty, and no file under `target` is newer than the report. It
releases after two blocks with `escaped: true` written into the ledger so a release is
never silent. It exits 0 instantly when `.design/run.json` does not exist, which is
every other session.

**Layer 3 - TodoWrite mirroring the ledger.** Step 0 also creates one todo per ledger
row, worded identically. This is the visibility layer: it puts the whole pipeline in the
terminal UI from the first turn, which is what took the 18-step command from silent
skips to zero. It is soft on its own - hence layers 1 and 2 - but it is free and it makes
divergence conspicuous mid-run rather than at the end.

**Layer 4 - the closing table, generated not written.** The last thing `/design` prints
is `scripts/ledger.sh show`, rendering the ledger as a table. Generated from the file,
so it cannot disagree with the file, which removes the "write RAN in the summary while
the row says PENDING" failure entirely:

```
step         status   evidence / reason
direction    RAN      .design/direction.json
register     RAN      high-end-visual-design
source       SKIPPED  not-react
assemble     RAN      12 files changed
assets       RAN      .design/assets-manifest.json (4 files)
motion       SKIPPED  no-motion-warranted
gate         RAN      .design/audit-report.md (a11y 0 crit, perf LCP 1.9s)
conversion   SKIPPED  not-marketing-surface
```

**Layer 5 - the blind audit.** `design-gate` is a leaf skill with
`context: fork`, `agent: general-purpose`, `background: false`. It runs with no
conversation history, reads the built files and screenshots rather than the reasoning
that produced them, runs the a11y and perf validators as scripts, and writes
`.design/audit-report.md`. Blindness is the point: an auditor that remembers arguing
for the choices cannot honestly grade them. Same insight as the `/review-stack` blind
lane already in use here.

**Tone, per 2.3.** The taste steps (direction, register, assemble, motion) are written
as guidance with reasons - skill-creator's register. The gate is written as discipline:
an Iron Law block, a closed skip set of zero, and a rationalization table with the four
rows that matter ("it already looks good" -> "looking good is not an audit result";
"I'll note the issues instead" -> "a note is not a report"; "the user is waiting" ->
"the audit is faster than a rebuild"; "I'll audit after presenting" -> "presenting is
the claim; the claim needs evidence first").

**What this does not fix, stated plainly.** The hook proves the audit *ran* and that
nothing changed after it. It cannot prove the audit was *good*. Layer 5 is the mitigation
and it is a mitigation, not a proof. If the model learns to write a thin
`audit-report.md` to satisfy the file check, the next lever is a minimum-content check in
`gate.sh` (report must contain a score line and a findings count) or a `type: prompt`
Stop hook grading the report. Do not build either until the thin report actually appears.

---

## File layout

Three skill directories, following the existing convention on this machine: real files
in `~/claude-config/`, symlinked into `~/.claude/skills/`.

```
~/claude-config/skills/
  design/
    SKILL.md                      # router. target <150 lines, hard cap 500.
    references/
      direction.md                # brand-system.html > design-dna > ui-ux-pro-max
                                  #   catalog; the register-lens table; the
                                  #   plan-then-review-the-plan pass; the
                                  #   AI-design-tells calibration list
      motion.md                   # decision tree in a fence: transitions-dev /
                                  #   gsap-scrolltrigger / gsap-timeline / gsap-react /
                                  #   apple-design / threejs-* / animation-vocabulary
      gate.md                     # what the audit runs, pass criteria, report format,
                                  #   the Iron Law block, the rationalization table
      conversion.md               # cro / pricing / signup / paywalls / popups /
                                  #   marketing-psychology. marketing surfaces only.
    scripts/
      ledger.sh                   # init | set | show  -> .design/run.json
      gate.sh                     # the Stop hook. exit 2 blocks.

  design-gate/
    SKILL.md                      # context: fork, agent: general-purpose,
                                  #   background: false. writes .design/audit-report.md
    scripts/
      a11y.mjs                    # axe-core over the rendered page
      contrast.py                 # WCAG 2.2 AA pairs, light and dark
      perf.mjs                    # lighthouse or equivalent, CWV thresholds

  assets/
    SKILL.md                      # standalone-capable. reads .design/direction.json
                                  #   when present. writes .design/assets-manifest.json
    references/
      nano-banana.md              # prompt patterns, mascot, product shots,
                                  #   vtracer logo vectorization
      stock-fallback.md           # when generated imagery is wrong for the surface;
                                  #   Unsplash / Pexels / Pixabay. fallback, not default
```

Symlinks:

```
~/.claude/skills/design      -> ~/claude-config/skills/design
~/.claude/skills/design-gate -> ~/claude-config/skills/design-gate
~/.claude/skills/assets      -> ~/claude-config/skills/assets
```

Remove `~/.claude/commands/design.md` (currently a symlink to
`~/claude-config/commands/design.md`) so `/design` resolves to the skill only.

Per-run state, written into the project being designed, not into the skill:

```
<project>/.design/
  run.json                        # the ledger. created by ledger.sh init.
  direction.json                  # locked palette, typefaces, register, subject
  assets-manifest.json            # written by /assets
  audit-report.md                 # written by /design-gate. the gate's evidence.
```

Add `.design/` to the project `.gitignore`, or keep it if a design audit trail per run
is wanted - it is small and it is the receipt.

`design/SKILL.md` frontmatter:

```yaml
---
name: design
description: Runs the design pipeline end to end - lock direction (brand-system, else
  design-dna from a reference, else ui-ux-pro-max plus a register lens), source real
  components, assemble, generate assets, add motion, then audit before presenting. Use
  whenever the user asks to design, redesign, restyle, build a page or a UI surface, or
  polish an interface, even if they do not say "design".
argument-hint: "[what to design] [where]"
hooks:
  Stop:
    - hooks:
        - type: command
          command: "bash $HOME/.claude/skills/design/scripts/gate.sh"
          statusMessage: "Checking the design gate..."
---
```

Notes on that block: no `matcher` on `Stop` (matchers are tool-event only, VERIFIED);
no `once` (the gate must keep running until it passes); `$HOME/...` rather than
`${CLAUDE_SKILL_DIR}` because the `$HOME` form is demonstrably working in the three
installed hook-bearing skills on this machine and the latter is UNVERIFIED inside a
frontmatter hook command; description written third-person and deliberately pushy per
skill-creator's undertriggering note.

`design-gate/SKILL.md` frontmatter:

```yaml
---
name: design-gate
description: Audits a built UI surface blind - accessibility, performance, responsive
  behavior, motion discipline, and heuristic UX - and writes .design/audit-report.md.
  Use before presenting any design work, and whenever asked to audit, review, or check
  an interface.
context: fork
agent: general-purpose
background: false
---
```

`assets/SKILL.md` frontmatter:

```yaml
---
name: assets
description: Generates brand imagery, hero frames, product shots, mascots, and logo
  vectors with nano-banana (Gemini), with stock as a fallback rather than a default.
  Writes .design/assets-manifest.json. Use when asked for images, illustrations, a
  mascot, a hero visual, product shots, or a logo, standalone or as part of a design run.
argument-hint: "[what imagery] [for which surface]"
---
```

Both leaves leave `disable-model-invocation` and `user-invocable` at their defaults, so
`/design` can invoke them and the user can invoke them directly.

Build order, if it is being done incrementally: ledger.sh and Layer 0/1/3/4 first (they
are the whole honesty half and need no hook), then gate.sh, then split out `/assets`,
then `design-gate` as a fork. Layers 0 through 4 are useful without layer 5; layer 2 is
useless without layer 0.
