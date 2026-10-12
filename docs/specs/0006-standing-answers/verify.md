# Verify: Standing answers · spec 0006 · updated 2026-10-12
_Steps derived from spec 0006 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [ ] Scratch repo per AC-9 (Autopilot allowed, work branch, spec with ACs, `test-preferences.json` naming an installed `tool`, uncommitted source). Beta feature, only `Test it` open, `AGENTS.md` has `- run suite: yes` and `- done: yes`. `wf run <repo>` -> confirm line shows `answers: run suite yes, done yes`; run ends `feature_done`; `run.json` `decisions` is `[]`; heading reads `· done` -> AC-9 check 1, AC-5, AC-7
- [ ] Same setup, open boxes `Verify it` then `Test it`, `- done: yes`. After the `Verify it` call: its record has `last_box` false and the feature is still `in-progress`; a done offer there arrives as a ping -> AC-9 check 2, AC-6
- [ ] Same repo but `.workflow/scope` instead of `docs/scope`, section only in root `AGENTS.md` -> confirm line shows `answers: none` (the root file is ignored) -> AC-1
- [ ] Put `- cross check: yes` in the section -> `refused: bad_answers: AGENTS.md:<line>: unknown key cross check (expected: ...)`, exit 5, no run folder -> AC-3

## Commands
- [ ] `python3 -B -m unittest discover -s runner/tests -k TestStandingAnswers` -> 9 tests OK -> AC-1 to AC-8
- [ ] `python3 -B -m unittest discover -s runner/tests` -> all OK, `test_argv` still compares against `UNATTENDED_PROMPT` with no section -> AC-5

## Value sourcing
- [ ] Which `AGENTS.md`: `test_base` (docs/scope reads root, .workflow/scope reads `.workflow/AGENTS.md`, never the other) -> AC-1
- [ ] Last box flag: `test_last_box` (Verify false while Test open, Test true, resume keeps true after the asking call added a box, /sync false) -> AC-6
- [ ] Each answer: `test_parse` (case, spaces, prose, a bullet outside the section ignored, table order) -> AC-2
- [ ] Prompt labels: `Run tests?` / `Yes, run and fix to green` still match `skills/test/SKILL.md` step 7.5, and the done offers in `skills/test/SKILL.md` and `skills/check/modes/verify.md` still read as the `DONE_YES` sentence describes -> AC-5
- [ ] Base text: `test_argv` pins `UNATTENDED_PROMPT` unchanged -> AC-5
- [ ] Confirm line and `run.json`: `test_prompt_and_record`, `TestConfirmLine` -> AC-7

## Acceptance-criteria coverage
- AC-1 `test_parse`, `test_base`, `test_refusals` (extra heading text) · AC-2 `test_parse`, `test_refusals` · AC-3 `test_refusals` · AC-4 `test_defaults`, `test_freeze` · AC-5 `test_prompt_and_record`, `test_no_sentences` · AC-6 `test_last_box` · AC-7 `test_prompt_and_record`, `TestConfirmLine`, `TestHappyPath` · AC-8 `test_architect_still_refused` · AC-9 manual steps 1 and 2 (not run yet)
- Mutation checks run 2026-10-12: every box treated as last box (3 tests red), resumes recomputing the flag (`test_last_box` red), answers reread per call (`test_freeze` red); restored, 152 tests green.
