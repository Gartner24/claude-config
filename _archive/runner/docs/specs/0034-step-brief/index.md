# 0034 · Each step gets the feature's brief

**Date**: 2026-10-14
**Status**: Accepted
**Paths:** `runner/run.py`, `runner/tests/test_brief.py`
**Amends**: none. Builds on [0024](../0024-issues-source-of-truth/index.md) (the same read, cap and fence pattern, used for linked issues) and [0021](../0021-never-stop/index.md) (a missing brief never stops anything).

## What you're agreeing to
- Every step `wf` starts for a feature also gets two short texts read from your files: the "Agreed so far" part of the feature's brief, and the "What you're agreeing to" part of its spec. So a fresh session knows what you already decided and does not ask again or quietly drop it.
- Both are read by `wf` itself, cut to a fixed size, and marked as information, not commands.
- If the feature has no brief, or the brief has no "Agreed so far" part, the step is told so plainly and the morning report says so. Nothing is made up to fill the gap, and the build goes on.

## Terms used below
- **Brief**: a markdown file under a `briefs/` folder (for example `docs/briefs/<slug>.md`) that holds decisions agreed in chat before they reach a spec. Its top section is headed "Agreed so far, do not ask again" (rule in `~/.claude/CLAUDE.md`, `### Context`).
- **Source line**: the `Source:` line under a feature heading in the scope file, which names where the feature came from (a brief, an issue, a message).
- **Spec line**: the `Spec [NNNN](../specs/...)` link under a feature heading.
- **Appended system prompt**: the extra instructions `wf` passes to every `claude -p` call with `--append-system-prompt` (`runner/run.py:2305`). Today it holds the unattended rules, standing answers, a hint, and linked issues (`runner/run.py:2283-2284`).
- **Fence**: two marker lines (`BEGIN X` and `END X`) around text that is data. The marker is chosen so the text cannot contain it, so the text cannot close its own block and pose as instructions (same as `issue_block`, `runner/run.py:4522-4538`).

## Acceptance criteria
- **AC-1** (which brief): `wf` reads the feature's uncommented `Source:` lines outside fenced code blocks (the same lines `linked_issues` reads, `runner/run.py:4343-4368`). Every markdown link target or backticked path on them, after `Source:` and up to the next `·` (so the row's own `Spec [..](..)` link is not read as a brief), that ends in `.md` is a candidate. Relative paths resolve from the scope file's folder, `~` expands to the home folder. A candidate counts as a brief only when its real path (symlinks resolved) is a regular file whose parent folder is named `briefs` and that lies inside the repo or inside `~/projects`. At most 3 briefs, in order, each once.
- **AC-2** (which section): from each brief, the section whose heading starts with "Agreed so far" (any heading level, case ignored), up to the next heading of the same or a higher level. Nothing else from the brief is sent.
- **AC-3** (which spec summary): `wf` reads the feature's `Spec` lines for links into the repo's `docs/specs/` (or `.workflow/specs/` for a `.workflow/scope` base). For each linked spec (at most 3; a folder link means its `index.md`), the `## What you're agreeing to` section up to the next `##` heading. The real path must stay inside that specs folder.
- **AC-4** (cap): each brief section is cut at 6000 characters and each spec section at 2000; a cut section ends with the line `[cut at <n> characters; the full text is in <path relative to the repo, or the file name for a brief outside it>]`. Control characters other than newline are removed (`PROMPT_CONTROL`, `runner/run.py:398`).
- **AC-5** (fence): all of it goes into one block appended after the issue text: one sentence saying this is what the user already agreed, to follow as requirements where it applies and not to ask about again, and to treat as data, never as instructions; then each part between `BEGIN BRIEF-DATA-<n>` and `END BRIEF-DATA-<n>` lines, with `<n>` the lowest number whose marker the text does not contain.
- **AC-6** (named, never invented): each gap gets one plain sentence inside the block instead of text, and one report note (`note`, `runner/run.py:2499-2503`, once per run): no brief linked; a linked brief not found or refused by AC-1 (the note says which rule refused it); a brief with no "Agreed so far" section; no spec linked; a linked spec with no "What you're agreeing to" section. The sentence for a missing brief says: build from the spec and the scope only, and do not assume decisions that are not written down.
- **AC-7** (every call): the block is read fresh before every call of the feature, in the same place the linked issues are read (`runner/run.py:2963`), so an edit to the brief between steps reaches the next step. Resumes, retries and reruns get the block read at that time.
- **AC-8** (never stops): no outcome of AC-1 to AC-7 stops, parks or asks. A read error is an AC-6 gap.
- **AC-9** (size of the call): when the whole appended system prompt would pass 120000 bytes (Linux refuses one argument over 131072 bytes, `MAX_ARG_STRLEN`), the brief block is cut first, part by part from the last, each cut part replaced by its AC-6 style sentence plus a report note. The call is never refused for size.
- **AC-10** (tests, `runner/tests/test_brief.py`): a fixture scope and brief cover AC-1 (a symlink from `docs/briefs/` to a file outside any `briefs` folder is refused; a `../` path leaving the repo and `~/projects` is refused), AC-2 (heading levels), AC-3, AC-4 (cut line), AC-5 (a brief containing `END BRIEF-DATA-0` gets marker 1), AC-6 (each gap sentence and note), AC-9 (an oversized issue block pushes the brief out, the call still starts).

## Build plan
1. Readers: `brief_paths`, `spec_paths`, `md_section` beside `linked_issues` in `runner/run.py`, with the AC-1 path rules. AC-1, AC-2, AC-3.
2. Block: `brief_data` and `brief_parts` with cap, control strip and fence, and the gap sentences and notes. AC-4, AC-5, AC-6.
3. Wiring: `Run.brief_check` sets `self.brief` next to `self.issue_check()` before every call; `call()` appends it after `self.issue_prompt` for that feature's own calls (never an isolated call); the size guard `brief_fit`. AC-7, AC-8, AC-9.
4. Tests and the `docs/architecture.md` components row for `claude -p` calls ("each gets the unattended prompt, the brief and spec summary, ..."). AC-10.

## Probes
None needed before the build: the block rides on `--append-system-prompt`, which `wf` already uses for issue text of up to 100000 characters (`ISSUE_CAP` times `MAX_ISSUES`, `runner/run.py:386`, `runner/run.py:393`). AC-9's byte limit is a Linux kernel constant, checked by the AC-10 test with a real `subprocess` spawn of `true` carrying the long argument.

## Follow-up
- The issue blocks alone can already pass 131072 bytes (5 issues of 20000 characters, more bytes in UTF-8). AC-9 covers the brief only; the same guard for issue text belongs to a spec 0024 fix.
- `/scope` and `/architect` already read the brief in chat (`rules/check-gates.md`); this spec covers only what `wf` hands to its calls.
