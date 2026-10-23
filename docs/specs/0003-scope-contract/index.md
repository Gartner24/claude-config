# 0003. Scope contract for the runner: header fields, tags and the next box rule

**Date**: 2026-10-11
**Status**: Accepted
**Paths:** `_archive/runner/wf.py`, `claude-home/rules-on-demand/scope-contract.md`, `bin/sync.sh`, `_archive/runner/tests/**`
**Amended by**: [0012](../0012-waiting-boxes-owed-to-you/index.md) - a new box segment ` · waits on you` for a box only you can close, and its rule file line under `## Tags and boxes`.
**Amended by**: [0014](../0014-runner-resilience/index.md) - a waiting box may also carry the ` · later boxes go on` segment (`wf run` and `next` pass over it), and a `/sync` box is the last box of its feature; both rule file lines sit under `## Tags and boxes`.

## Summary

This spec fixes the scope format that `wf` and the skills that write scopes must agree on. A repo scope header gains two lines, `**Source of truth:**` and `**Autopilot:**`, which mean `scope` and `off` when missing, so no existing scope needs editing. A feature is queued for autopilot with a `· auto` tag, skipped boxes get one syntax, and status tags are written in one style. Because `/scope` and `/architect` are vendored, the rules reach them through an always loaded rule file, and `wf` gets one tested header check that warns on a bad value.

## Requirements

**User stories**:
- As you, I want a repo to stay out of unattended runs until I switch it on, so that a client repo never runs before I have looked at it.
- As you, I want `/scope` and `/architect` to write scopes the runner reads correctly, even after a vendor update.

**Acceptance criteria**:
- **AC-1**: A repo scope's header is read from its top file only (`scope.md`, or `index.md` for an epic split; epic files are never read for it), after HTML comments and fenced blocks are removed (as `parse_text` already does). The header ends at the first heading of level 2 or 3, or the first box line, whichever comes first. A header line matches `^\*\*(Source of truth|Autopilot):\*\*\s*(.*)$`, case insensitive, anchored at column 0; `**Autopilot**:` (colon outside the bold) does not match. The value: split the rest of the line on whitespace, take the first token, strip the characters `.,;:!?()[]*_"'` from both ends, lowercase it, and compare exactly. So `Allowed (client signed off)` reads `allowed`, `**allowed**` reads `allowed`, and `allowed-ish` is unknown. An empty value is unknown with value `''`. Valid values: Source of truth `scope`, `issues`, `mixed`; Autopilot `allowed`, `off`.
- **AC-2**: A missing field means Source of truth `scope` and Autopilot `off`. The first matching line for a field always wins, even when its value is unknown. One warning per problem, with these exact strings:
  - `unknown Source of truth value '<value>', using scope`
  - `unknown Autopilot value '<value>', using off`
  - `Source of truth set twice, using the first`
  - `Autopilot set twice, using the first`
- **AC-3**: `wf` checks the header of every candidate that is not a hub; hubs are skipped. Header warnings join the candidate's warnings. They appear on the confirm line (spec 0002 AC-8), and also, as `warning: <text>` lines, on the `nothing to run` and `no command in this box` paths, which today return before any warning is printed (`runner/wf.py:321-329`). The `--list` columns do not change (spec 0002 AC-12). Checking the header never changes which box is next.
- **AC-4**: Convention only, checked by reading the rule file (no reader, no test in this feature): repo scopes carry no `**Repo:**` line. A hub row points to its repos through the `Repos` column of its At a glance table: comma separated entries, each a folder name or a `~` path (a path for an ambiguous name or a repo outside the roots). The queue in Release 3 reads it.
- **AC-5**: A feature is queued for autopilot by an `auto` tag on its heading (`### 4. Headless step loop · in-progress · auto`). It counts only as a whole `·` segment, case insensitive, ending at the next `·` or the line end, the same shape as the done/existing/dropped tag test: `·\s*auto\s*(?=·|$)`. So `· auto-merge` is not the tag. `auto` does nothing unless the feature is open (not done, existing or dropped, not in `## Deferred`) and its repo's Autopilot is `allowed`. `next` ignores it, and the feature display strips it like any other `·` segment.
- **AC-6**: Skills write status tags only as `·` segments (`· done`, `· existing`, `· dropped`). The runner keeps reading both styles, unchanged from spec 0002 AC-5. Rule text only, no new check.
- **AC-7**: A skipped box is ticked with a `· skipped` segment at the end: `- [x] Test it: /test runner · skipped`. Skipping a parent box ticks every box under it with `· skipped` too, since an open milestone under a ticked parent still runs the parent's command (spec 0002 AC-6). A whole feature is never skipped; it is marked `· dropped`. An unticked box carrying `· skipped` is a mistake and stays open; the runner does not warn. No parser change.
- **AC-8**: The next box rule is spec 0002 AC-5, AC-6 and AC-11, unchanged. For skills, that means: one command, in the first backticked span of the box; milestones indented under their parent box; nothing runnable inside `## Deferred`, comments or fenced blocks; `docs/` wins over `.workflow/` when both exist. Rule text only, no new check.
- **AC-9**: A rule file `~/.claude/rules/scope-contract.md` (always loaded, synced into this repo's `rules/`), at most 25 lines, states AC-1 to AC-8 for skills, and tells:
  - `/scope`: on a new plan, write `**Source of truth:** scope` and `**Autopilot:** off` on their own lines right after the `**Workflow:**` line; with no Workflow line, right after the last bold `**Key:**` header line; never below the first `##` heading. On a replan, add either line when missing and never change an existing value. Never write them in a hub; never write `**Repo:**`; write status tags and skipped boxes per AC-6 and AC-7.
  - `/architect`: add `· auto` to a feature heading at spec capture only when you ask to queue that feature; never on its own; write status tags per AC-6.
- **AC-10**: A manual check, recorded in the verify step: `/scope` with no argument on this repo adds the two header lines to `docs/scope/scope.md` with the defaults; the same `/scope` run through `claude -p` in a scratch repo (as the unattended runner will call it) writes them too, proving the rule file loads headless; and `/architect` asked to queue a feature writes `· auto` on that heading.

## Decision

**Chosen option**: Option 1: Always loaded rule file plus a header check in `wf`

The contract lives in this spec, reaches `/scope` and `/architect` through `~/.claude/rules/scope-contract.md`, and `wf` checks the two header fields and warns on a bad value.

## Standard definition

**Canonical pattern** (repo scope top file):
```markdown
# Scope: claude-config

Your Claude Code setup, published.

**Build approach:** Skateboard (each stage is usable on its own).
**Workflow:** Beta (after `/develop`: `/check verify`, then `/test`).
**Source of truth:** scope
**Autopilot:** off

### 4. Headless step loop · in-progress · auto
- [x] Design it (spec): `/architect headless step loop`
- [ ] Build it: `/develop headless step loop`
   - [x] Lock per repo (AC-3)
   - [ ] Budget caps (AC-4)
- [ ] Verify it: `/check verify headless step loop`
- [x] Test it: `/test headless step loop` · skipped
```

Hub At a glance:
```markdown
| # | Work | Repos | Status |
|---|------|-------|--------|
| 3 | SEO data connectors | claude-config, ~/projects/example/site-templates | planned |
```

**Replaces**:
- `**Repo:** <path>` in a repo scope (from research section 0).
- `(done)`, `(existing)`, `(dropped)` as newly written status tags.
- Skipped boxes left unticked or with no marker.

**Enforcement**:
- `wf` warns on unknown or repeated header values (AC-2).
- The always loaded rule file instructs the skills (AC-9).
- Fixture tests in `runner/tests/` pin the header check.

**Rollout**: new writes immediately. Existing scopes need no migration; `/scope` adds the header lines on each repo's next replan.

**Exceptions**: hubs carry no `**Source of truth:**` or `**Autopilot:**` lines. Parenthesized status tags in old scopes stay valid.

## Feature design

**Data model sketch** (in memory only):
- No stored fields in this feature. One header check function returns warnings only, appended to the existing `Candidate.warnings` for non hub candidates. Release 2 adds `source_of_truth` and `autopilot` attributes when something reads them.

**Value sourcing**:
| Action | Value produced / displayed | Source |
|---|---|---|
| check header | header lines | top file text with comments and fences removed, up to the first level 2 or 3 heading or box line (AC-1) |
| check header | field value | first whitespace token after the anchored pattern, ends stripped of `.,;:!?()[]*_"'`, lowercased, compared exactly (AC-1) |
| check header | header warnings | the four literal strings of AC-2 |
| confirm line, `nothing to run`, `no command` | warnings shown | `Candidate.warnings` (spec 0002 AC-8, plus the two early paths, AC-3) |
| feature display | heading without `· auto` | existing `DISPLAY_TAG` stripping of `·` segments |
| `/scope` write | header line values | the defaults `scope`, `off` (AC-9) |
| `/architect` write | `· auto` | your explicit request to queue the feature (AC-9) |

**Key invariants**:
- A missing, empty or malformed value never resolves to `allowed`.
- Checking the header never changes the next box.
- No skill overwrites an existing header value.

**Security model**:
- Autopilot is opt in per repo. "Only you set `allowed`" holds only for repos you wrote: a cloned third party scope can write `allowed` itself, and nothing stops that until the Release 2 run guard exists (feature 8).

**Critical test scenarios** (fixtures in `runner/tests/fixtures/`; tests call the header check in `wf.py`, never a copy of it):
- Valid values, including `Allowed (client signed off)`, `**allowed**` and `ISSUES.`, give no warning, verifies **AC-1**.
- `allowed-ish`, an empty value, and `**Autopilot**: allowed` (colon outside the bold, so no match) never read as `allowed`, verifies **AC-1**.
- A header line inside an HTML comment or a fenced block is ignored, verifies **AC-1**.
- A scope with `###` features and no `##`: an `**Autopilot:**` line in a feature body is ignored; so is one after the first `##`, verifies **AC-1**.
- An `index.md` epic split is checked from `index.md`; an Autopilot line in an epic file is ignored, verifies **AC-1**.
- No header lines gives no warning, verifies **AC-2**.
- `**Autopilot:** on` warns `unknown Autopilot value 'on', using off`; an unknown first line followed by a valid second line warns both the unknown value and `Autopilot set twice, using the first`; same pair for Source of truth, verifies **AC-2**.
- A hub with a bad Autopilot line gives no warning, verifies **AC-3**.
- A bad value shows `warning:` on the confirm line, on the `nothing to run` path and on the `no command` path; `--list` output is unchanged, verifies **AC-3**.
- A heading `· in-progress · auto` displays without `· auto` and gives the same next box as without it; `· auto` matches the AC-5 pattern and `· auto-merge` does not, verifies **AC-5**.
- `- [x] ... · skipped` is not the next box; a ticked `· skipped` parent with all children ticked `· skipped` yields the next feature's box, verifies **AC-7**.
- Manual: `/scope` replan on this repo, `/scope` through `claude -p` in a scratch repo, and an `/architect` queue request, verifies **AC-10**.

## Build plan

Skateboard: the rule file alone already makes the skills write the contract; the header check then catches what they get wrong.

1. Write `~/.claude/rules/scope-contract.md` (at most 25 lines: AC-1 to AC-8 for skills, plus the `/scope` and `/architect` instructions), run `./sync.sh`, add it to `NOTICE.md` as authored. AC-4, AC-6 and AC-8 are rule text only, checked by reading the file. Satisfies **AC-4**, **AC-5**, **AC-6**, **AC-7**, **AC-8**, **AC-9**
2. Header check in `runner/wf.py` (warnings only, non hub candidates), warnings printed on the confirm line and the two early return paths, with fixtures and tests, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-5**, **AC-7**
3. Manual check: `/scope` replan on this repo, `/scope` through `claude -p` in a scratch repo, and an `/architect` queue request, recorded in the verify step, satisfies **AC-10**

## Consequences

**Positive**:
- Every existing scope is already valid; autopilot is off until you switch a repo on.
- The vendored skills can update freely without losing the contract.

**Negative / tradeoffs**:
- The rule file costs context in every session, even in repos with no scope.
- A skill can still ignore the rule file; only the warning and the manual check catch it, not a hard gate.
- The hub `Repos` column has no reader until Release 3, so a malformed entry goes unnoticed until then.
- The parser keeps two status tag styles indefinitely.
- A replan that regenerates the header can drop the two lines; Autopilot then falls back to `off` with no signal. Safe in direction, but a value you set is lost silently. Accepted.

**Neutral**:
- `**Source of truth:**` values `issues` and `mixed` are only validated; they have no behavior until feature 16.
- Discovery stays a scan (spec 0002); the dropped `**Repo:**` field means it is not replaced.

## Follow-up

- [ ] Research doc section 0 still says each repo scope carries `**Repo:** <path>`; note there that spec 0003 replaced it with the hub `Repos` column.
- [x] Spec 0002 Follow-up item (hubs, tag style, skipped marker) is answered by this spec; tick it there.
- [x] Feature 8: guard against a third party scope that writes `**Autopilot:** allowed` itself (feature 4 shipped without it). (closed by spec 0008 AC-9, the trust list)

Decision record (context, options, rationale): [rationale.md](rationale.md). Verify steps: [verify.md](verify.md).
