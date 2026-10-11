# Provenance

Most of this repo is other people's work, redistributed. This file says which is which,
because the LICENSE covers only the parts authored here.

## Authored here (MIT, see LICENSE)

| Path | What |
|---|---|
| `skills/review-stack/` | Multi-agent pre-ship and PR review orchestrator |
| `agents/regression-hunter.md` | Regression hunting: what worked before a diff and stops after |
| `agents/pr-intent-verifier.md` | Does a PR do what it claims, and nothing else |
| `skills/intent-router/`, `USAGE.md` | Prompt-to-skill routing table and its scorer |
| `scripts/check-routing.py`, `scripts/asciify.py` | Repo tooling |
| `hooks/block-destructive.sh` | Destructive-command guard |
| `runner/` | `wf`, the workflow runner (spec 0001) |
| `rules/ecc/*/index.md` (7 files) | Per-language rule indexes - authored here, not upstream. They only `@import` the files below. |
| `sync.sh`, `CLAUDE.md`, `rules/ecc/common/{code-review,testing}.md` additions | Setup and the hand-earned rules |

## Redistributed from elsewhere

| Path | Upstream | Notes |
|---|---|---|
| `agents/` (27 of 31 files) | [affaan-m/ECC](https://github.com/affaan-m/ECC) | Cherry-picked, then frozen. Confirm ECC's license before reusing. |
| `rules/ecc/` (43 of 50 files) | [affaan-m/ECC](https://github.com/affaan-m/ECC) | Same, plus local additions in `common/code-review.md` and `common/testing.md`. The other 7 are the `index.md` files listed above. |
| `agents/scout.md`, `agents/researcher.md` | [JavaScript-Mastery-Pro/skills](https://github.com/JavaScript-Mastery-Pro/skills) | MIT; copied unchanged as the helper agents its workflow skills call. |
| `skills/deep-research/` | [affaan-m/ECC](https://github.com/affaan-m/ECC) | Forked 2026-10-11 so an ECC reinstall cannot overwrite it; local additions: academic tools, web, code and forum search tools, fallback rule. |
| `skills/anti-ai-writing/` | third party, MIT | Recorded in `SKILLS-EVALUATION.md`. |
| `skills/voice-dna/`, `skills/business-analyzer/` | third party | **License not recorded.** Verify before relying on redistribution. |

The frameworks this setup runs on - gstack, jjstack, get-shit-done-cc, the Claude Code
plugins - are **not** vendored here. `SKILLS.md` documents how to install each from source.

The 6-line "Prompt Defense Baseline" block after the frontmatter of 29 files in `agents/`
(the 27 ECC agents plus `regression-hunter.md` and `pr-intent-verifier.md`) is upstream
ECC boilerplate. Editing one copy does not change the other 28. `scout.md` and
`researcher.md` do not carry it.
