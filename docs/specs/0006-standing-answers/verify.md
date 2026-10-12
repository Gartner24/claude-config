# Verify: Standing answers · spec 0006 · updated 2026-10-12
_Steps derived from spec 0006 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [x] Scratch repo per AC-9 (Autopilot allowed, work branch, spec with ACs, `test-preferences.json` naming an installed `tool`, uncommitted source). Beta feature, only `Test it` open, `AGENTS.md` has `- run suite: yes` and `- done: yes`. `wf run <repo>` -> confirm line shows `answers: run suite yes, done yes`; run ends `feature_done`; `run.json` `decisions` is `[]`; heading reads `· done` -> AC-9 check 1, AC-5, AC-7
  - Run 2026-10-12, claude 2.1.296, from a Claude Code session: `wf run -y --budget 5 --call-timeout 20 --max-calls 4 --max-wait 0.25 <scratch>/ac9-1` (Python `calc.py` uncommitted, `unittest` in `test-preferences.json`, spec 0001 with 2 ACs). Confirm line `answers: run suite yes, done yes | guard: 9 hosts, 61 files`; `[1/4] /test calc -> success, 0.69 USD`, `[2/4] /sync -> success, 0.47 USD`, `done: 1. Calc`, exit 0. `run.json`: `stop_reason` `feature_done`, `decisions` `[]`, `/test calc` `last_box` true, `/sync` `last_box` false. Heading `### 1. Calc · done`, all boxes ticked. PASS
- [x] Same setup, open boxes `Verify it` then `Test it`, `- done: yes`. After the `Verify it` call: its record has `last_box` false and the feature is still `in-progress`; a done offer there arrives as a ping -> AC-9 check 2, AC-6
  - Run 2026-10-12, same session and claude: `wf run -y --budget 5 --call-timeout 20 --max-calls 1 --max-wait 0.25 <scratch>/ac9-2` (`AGENTS.md` has only `- done: yes`). Confirm line `answers: done yes`; `[1/1] /check verify calc -> success, 0.45 USD, next: /test calc`, then `stopped: max_calls` (exit 6, the cap set to stop after this call). `run.json`: the call's `last_box` false, `decisions` `[]`. Heading still `### 1. Calc · in-progress`, `Verify it` ticked, `Test it` open. PASS; the verify call made no done offer, so the ping branch was not exercised (unit covered by `test_last_box`)
- [x] Same repo but `.workflow/scope` instead of `docs/scope`, section only in root `AGENTS.md` -> confirm line shows `answers: none` (the root file is ignored) -> AC-1
  - Run 2026-10-12 by `/check verify`, stdin not a tty so the confirm cancels before any call: `wf run <scratch>/wf-repo` printed `... | /test calc | caps: ... | answers: none | guard: 9 hosts, 61 files`, exit 130. Control: the same section copied into `.workflow/AGENTS.md` printed `answers: run suite yes, done yes`. PASS
- [x] Put `- cross check: yes` in the section -> `refused: bad_answers: AGENTS.md:<line>: unknown key cross check (expected: ...)`, exit 5, no run folder -> AC-3
  - Run 2026-10-12 by `/check verify`: `wf run <scratch>/docs-repo` printed `refused: bad_answers: AGENTS.md:6: unknown key cross check (expected: - run suite: yes|ask, - done: yes|ask)`, exit 5, `$XDG_STATE_HOME/wf/runs` empty. PASS

## Commands
- [x] `python3 -B -m unittest discover -s runner/tests -k TestStandingAnswers` -> 9 tests OK -> AC-1 to AC-8
- [x] `python3 -B -m unittest discover -s runner/tests` -> all OK, `test_argv` still compares against `UNATTENDED_PROMPT` with no section -> AC-5 (153 tests OK, 2026-10-12)

## Value sourcing
- [x] Which `AGENTS.md`: `test_base` (docs/scope reads root, .workflow/scope reads `.workflow/AGENTS.md`, never the other) -> AC-1
- [x] Last box flag: `test_last_box` (Verify false while Test open, Test true, resume keeps true after the asking call added a box, /sync false) -> AC-6
- [x] Each answer: `test_parse` (case, spaces, prose, a bullet outside the section ignored, table order) -> AC-2
- [x] Prompt labels: `Run tests?` / `Yes, run and fix to green` still match `skills/test/SKILL.md` step 7.5, and the done offers in `skills/test/SKILL.md` and `skills/check/modes/verify.md` still read as the `DONE_YES` sentence describes -> AC-5 (grep 2026-10-12: SKILL.md lines 164, 165, 187; verify.md line 142)
- [x] Base text: `test_argv` pins `UNATTENDED_PROMPT` unchanged -> AC-5
- [x] Confirm line and `run.json`: `test_prompt_and_record`, `TestConfirmLine` -> AC-7

## Acceptance-criteria coverage
- AC-1 `test_parse`, `test_base`, `test_refusals` (extra heading text) · AC-2 `test_parse`, `test_refusals` · AC-3 `test_refusals` · AC-4 `test_defaults`, `test_freeze` · AC-5 `test_prompt_and_record`, `test_no_sentences` · AC-6 `test_last_box` · AC-7 `test_prompt_and_record`, `TestConfirmLine`, `TestHappyPath` · AC-8 `test_architect_still_refused` · AC-9 manual steps 1 and 2 (passed 2026-10-12, real claude 2.1.296)
- Mutation checks run 2026-10-12: every box treated as last box (3 tests red), resumes recomputing the flag (`test_last_box` red), answers reread per call (`test_freeze` red); restored, 152 tests green.
