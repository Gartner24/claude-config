# 0034 rationale

## Why
Personal plan row 12, part 4: decisions agreed in chat were lost after `/clear`, because skills read only repo files. Parts 1 to 3 made every session write a brief and made `/scope` and `/architect` read it. A `wf` step is a fresh `claude -p` session that today gets only the box command and the appended system prompt (`runner/run.py:2283-2305`). It can read the brief itself, but nothing tells it to, so an agreed decision that never reached the spec is invisible to the build.

## What the code does today
- The appended system prompt is `unattended_prompt` + the sync box sentence + the user's hint + `issue_prompt` (`runner/run.py:2283-2284`), rebuilt for every call.
- `issue_check` (`runner/run.py:2527-2580`) runs before every call (`runner/run.py:2963`), reads linked issues with `wf`'s own `gh`, and builds fenced blocks with `issue_block` (`runner/run.py:4522-4538`). This spec copies that shape: read by `wf`, capped, fenced, refreshed every call, gaps are report notes.
- `Feature.lines` already holds the uncommented lines of a feature (`runner/run.py:521-522`), and `linked_issues` already walks its `Source:` lines skipping fenced blocks (`runner/run.py:4343-4368`).
- Features name their spec on a `Spec [NNNN](../specs/...)` line (for example `docs/scope/scope.md:485`) and their brief on the `Source:` line (`docs/scope/scope.md:486`). Some briefs live outside the repo, in a hub's `docs/briefs/` under `~/projects` (`docs/scope/scope.md:373`).

## Decided without asking (2026-10-14)
Per `docs/briefs/finish-runner-today.md`, the recommended option was taken for every question.

| Question | Options | Pick |
|---|---|---|
| Who reads the brief | `wf` reads it and puts it in the prompt; the prompt only tells the call to read it | `wf` reads it. A call can skip an instruction; text already in its prompt cannot be skipped. Same choice as spec 0024 for issues. |
| How much of the brief | the "Agreed so far" section; the whole file | The section. The ticket names it, and the rest of a brief is often research and history that would crowd the prompt. |
| Which paths are allowed | any path on the Source line; repo only; repo plus `~/projects`, inside a `briefs` folder | Repo or `~/projects`, real path inside a `briefs` folder. A call can edit the scope file, so an open path would let a call make `wf` paste any file (a key, a token) into the next prompt. The `briefs` folder test on the resolved path also blocks a symlink trick. Hub briefs under `~/projects` stay reachable. |
| Missing brief | name it in the prompt and the report; ask; stop | Name it. The ticket says "named, never invented", and spec 0021 says nothing stops for this. A question for every feature without a brief would be noise. |
| Missing "Agreed so far" section | send nothing and name the gap; send the whole brief | Send nothing, name it. Sending the whole file would invent a section the user did not write. |
| Caps | 6000 / 2000 characters; no cap | 6000 per brief section, 2000 per spec section, at most 3 of each (24000 characters at worst). Real "Agreed so far" sections in this repo are well under that (`docs/briefs/finish-runner-today.md` is 3583 bytes in total, its "Agreed so far" section about 500); a spec summary is at most 5 lines by rule (`rules/spec-gate.md`). |
| Wording | "data, never instructions"; "follow as requirements" | Both: the brief is the user's decisions (follow them, do not ask again), but no line in it is a command to the call. Same pairing as `ISSUE_PROMPT` (`runner/run.py:394-395`). |
| When it is read | once per run; before every call | Before every call, so an edit made between steps is seen. Cost is a few file reads. |
| Oversized prompt | cut the brief first; refuse the call; cut issues first | Cut the brief first: the issue text is the requirement in an `issues` repo (spec 0024) and wins over the brief. The call is never refused, per spec 0021. |

## Options not taken
- A new `Brief:` line in the scope contract (spec 0003). Not needed: the `Source:` line already names the brief by convention (`~/.claude/CLAUDE.md` `### Context`: "point the row's `Source:` at it"), and the `briefs` folder test tells a brief apart from other sources.
