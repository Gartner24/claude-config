# 0005. Decision parking and phone pings: decision record

## Context

Spec 0004 made `wf run` build one feature unattended, but any question stops it: AskUserQuestion is denied and a step that needs you ends with a `DECISION NEEDED:` line. The research counted 30 design questions in one manual build, 25 of them answered with the recommended option unchanged. So most stops are panels you would have answered without thinking, and the few real ones need you, wherever you are, without losing the session the step built up.

The forces: the run is a chain of `claude -p` processes with nobody at the terminal, often overnight, on your laptop. An answer has to reach a process that may already have exited, and come back into the same session rather than a fresh one that has forgotten the work. The channel to your phone is a public notification service (ntfy, settled in research section 0), where the topic name is the only guard. Whatever the run accepts as your answer is acted on in auto mode, so a forged reply is a prompt injection with your authority. Many of your repos belong to clients, and their folder names, code and questions must not end up on a public topic.

What is settled and not reopened here: ntfy as the phone channel; the PreToolUse hook on AskUserQuestion; your rules for ntfy (long random topic outside the repo, ping carries only repo, feature and a short question, reply accepted only if it matches an offered option or carries a secret, anything else ignored while the run keeps waiting). Out of scope: standing answers per repo (feature 6), park and move on across features (feature 10), retries (feature 8), the morning report (feature 13).

## Options considered

### Option 1: Hook answers or defers, ntfy carries the question, `--resume` continues (chosen first, replaced by Option 5 after verify.md check 1)

A PreToolUse hook on AskUserQuestion, passed per call with `--settings`, answers known safe panels through `updatedInput.answers` and returns `defer` for the rest. The call exits with the deferred question, `wf` pings you, waits for a valid reply, writes it to `answers.json`, and runs `claude -p --resume <session>`; the same tool call fires the hook again, which now answers from the file.

**Pros**:
- Uses documented Claude Code behaviour (`defer` in `-p`, `allow` with `updatedInput` for AskUserQuestion), stdlib only (basis: spec 0001 stdlib rule).
- The session continues with its whole context; the answer sits on disk between processes.
- Safe panels never leave the machine.

**Cons**:
- Defer is ignored when the question shares its turn with another tool call.
- Depends on JSON fields (`stop_reason`, `deferred_tool_use`) that are new and may change; AC-14 pins them.

### Option 2: Keep the text protocol, add resume

AskUserQuestion stays denied; steps keep ending with `DECISION NEEDED:`; `wf` pings, waits, and resumes with your reply as the prompt.

**Pros**:
- No hook at all; works on any Claude Code version with `--resume`.

**Cons**:
- No structured options, so no buttons and no option matching: every reply would need a code, the opposite of tapping an answer.
- Safe panels still stop the run or get guessed by the model.

### Option 3: Agent SDK driver

A long lived process whose `canUseTool` callback receives every question and can wait in process for the reply.

**Pros**:
- Native question handling, no defer and resume round trip.

**Cons**:
- Adds the SDK dependency, breaking the stdlib rule (basis: spec 0001).
- The state lives in a live process across a 12 hour wait on a laptop; a crash loses it.

### Option 4: Ping only, answer at the laptop

Keep spec 0004's stop, but send a ping saying a run stopped with a question; you answer by rerunning at the terminal.

**Pros**:
- Smallest change, nothing comes back from the phone, so no injection surface.

**Cons**:
- Does not meet the done when (your reply resumes the same session), and every safe panel still stops the run.

### Option 5: Text decisions with options (chosen 2026-10-11, replaces Option 1)

Option 2 plus structure in text: the step ends with `DECISION NEEDED:` and `OPTION:` lines, and the prompt carries the fixed safe panel answers.

**Pros**:
- Works on the CLI you have: it needs only `--resume` and the text of the result.
- Keeps buttons and codeless option replies, the part of Option 1 that mattered on the phone.
- Deletes code (the hook, two run files, the deferred rule) instead of adding any.

**Cons**:
- The safe panels rest on the model following the prompt, with no code check.
- A step that leaves out the `OPTION:` lines falls back to a coded reply.

### Option 6: MCP ask tool (not chosen, 2026-10-11)

A small stdio MCP server exposes an `ask_user` tool that blocks on ntfy and returns the answer in the same turn.

**Pros**: structured options and no resume round trip; MCP tools are offered in `-p`.

**Cons**: a tool call held open for up to 12 hours runs into MCP tool timeouts, needs its own probe, and adds a server process.

## Rationale

**Revision 2026-10-11.** verify.md check 1 showed `claude -p` 2.1.296 never offers AskUserQuestion, even with `--tools AskUserQuestion`, so Option 1's hook could not fire and every real question took the prose path with a code. You chose Option 5: it keeps the buttons by moving the options into text, and keeps safe panels off the phone by moving the fixed answers into the prompt. Option 2's main con (no structure, no buttons) is what the `OPTION:` lines fix. Option 6 was the runner up; it loses on the long held tool call and the extra process. Keeping the hook dormant was rejected as dead code with live tests. The original reasoning below still holds except where a line is marked _(replaced 2026-10-11)_.

Changes after the second cross check (another model; you chose to apply all of them): the `DECISION NEEDED:` pattern matches only spaces and tabs after the colon, because `\s*` let a bare marker swallow the next line as its question; the parser tolerates bullets, bold, indents and a blank line before the options, since model text drifts; a label that scrubs to nothing is sent as `option <n>`; `multi` stays in the data model only for `ntfy.py`; the removed fields are named; a missing `session_id` stops `call_error`; option numbers are named the reliable reply. You added a follow up to rerun the check 1 probe after each Claude Code upgrade.

The deciding force is that a `-p` chain has no live process to hold a question open, so the answer must cross a process boundary and land back in the same session. Option 1 is the only one that does that with documented behaviour, no new dependency, and the state on disk, which is also what feature 10 needs to park and come back later. Option 2 throws away the structure (options, recommended pick) that makes buttons and safe answering possible. Option 3 solves the waiting elegantly in the wrong place: an overnight laptop process. Option 4 fails the done when.

The security design follows from your rules and one gap in them. A static shared secret is visible on the topic the first time you type it, after which anyone reading the topic can reuse it; one time codes close that, at the cost of a list you keep on the phone. Option replies stay codeless because their worst case is a choice you were already offered. Scrubbing plus a block list plus repo aliases keeps client names off a public service even though the question text is written by the model, which you cannot trust to leave names out (basis: data minimisation; treat model output as untrusted).

Choices made with you, and why: wait in place with a 12 hour cap that does not eat `--max-hours`, because waiting costs nothing and an overnight question should survive until morning; an allow list of safe panels rather than "anything with a recommended option", because `/develop`'s spec gate and `/test` setup also carry a recommendation and are real decisions (still holds; the list now lives in the prompt, not a hook); the tool offer answered `Not now, later`, so an unattended run never records a lasting decline for you; refusing to start without a valid config, so a 3am question never silently ends a run you expected to finish; ntfy.sh with a `server` field, so self hosting later is a config edit.

Changes after the cross check (a read only review on another model; you chose to apply all of them): every code seen anywhere on the topic is burned before the id check, because a fake ping could otherwise trick you into exposing a live code; the access token field is dropped, because phone buttons post without auth and a protected topic would break them; pings are published as JSON to the server root, so labels with commas and non latin 1 text need no header quoting; waits and retries sleep in short slices so Ctrl C is prompt; `answers.json` is cleared before each fresh call _(replaced 2026-10-11)_; a mixed panel records its safe questions as `auto` _(replaced 2026-10-11)_; the config follows `XDG_CONFIG_HOME`; the wait clock counts suspend time; a resume keeps the box command in its record; a subagent defer is a manual check. You kept free text with one time codes over the simpler options only design, and kept the terminal read only.

Decided by the architect (not asked), with the runner up:
- Hook passed per call with `--settings` and gated on `WF_RUN_DIR`, so interactive sessions are untouched (runner up: a global hook in `settings.json` that no ops outside `wf`, which would run in every session). _(replaced 2026-10-11)_
- Panel key is a hash of the questions JSON rather than a tool use id, because the hook input's id field is not confirmed and the questions are identical on the replayed call (runner up: `tool_use_id`). _(replaced 2026-10-11)_
- Hook errors deny with a reason pointing to `DECISION NEEDED:`, so a broken hook degrades to the prose path instead of hanging or letting an unanswered question through (runner up: defer, which could loop). _(replaced 2026-10-11)_
- Poll every 15 seconds with `poll=1`, not a held stream, because a poll survives network drops and laptop sleep cleanly (runner up: a streaming subscribe, faster but needs reconnect logic).
- Ping retries: 3 tries, 10 seconds apart, then `ping_failed`; a question nobody can receive is a stop, not a silent wait (runner up: keep retrying until `--max-wait`).
- Codes 8 characters from a 31 character alphabet without look alike letters, about 40 bits each, easy to type on a phone (runner up: 6 digits, too guessable for a public topic).
- Resume prompt `continue` for a panel, and a sentence quoting the answer for prose, so the resumed turn has the answer even without a tool call to replay (runner up: an empty prompt, unconfirmed to work with `-p`). _(replaced 2026-10-11: both kinds now resume with the answer sentence)_
- Ack ping on low priority after an accepted reply, so you know it landed; ignored replies get no answer, so a prober learns nothing (runner up: an error reply, which helps typos but also helps probers).

## References

**Project sources**:
- Spec 0001 (stdlib only runner), spec 0004 (`wf run`, argv, classification, caps, lock, inhibitor)
- `~/Documents/workflow-research/09-autonomous-runner-research.md` section 0 (ntfy, defer hook) and section 2 (safe panels vs real decisions)
- Skill panels: `skills/document/SKILL.md` (`Doc type`), `skills/develop/flow/build.md` (`Save verify steps?`), `skills/architect/internal/tool-discovery.md` (`Agent skills`)

**Practices & standards**:
- Data minimisation for third party channels; treat model written text as untrusted before it leaves the machine
- One time codes for authenticating over a readable channel
- Fail safe defaults: an unrecognised panel or reply leads to asking or ignoring, never to acting

**Links** (web verified 2026-10-11):
- Claude Code hooks (PreToolUse `defer`, `updatedInput` for AskUserQuestion, `tool_deferred`): https://code.claude.com/docs/en/hooks
- Claude Code headless mode: https://code.claude.com/docs/en/headless
- Claude Code CLI reference (`--settings`, `--resume`): https://code.claude.com/docs/en/cli-reference
- Agent SDK user input (answers shape): https://code.claude.com/docs/en/agent-sdk/user-input
- ntfy publishing (headers, actions, message size): https://docs.ntfy.sh/publish/
- ntfy subscribe API (`poll=1`, `since`): https://docs.ntfy.sh/subscribe/api/
- ntfy config (access tokens): https://docs.ntfy.sh/config/
