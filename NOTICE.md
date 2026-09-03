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
| `sync.sh`, `CLAUDE.md`, `rules/ecc/common/{code-review,testing}.md` additions | Setup and the hand-earned rules |

## Redistributed from elsewhere

| Path | Upstream | Notes |
|---|---|---|
| `agents/` (27 of 29 files) | [affaan-m/ECC](https://github.com/affaan-m/ECC) | Cherry-picked, then frozen. Confirm ECC's license before reusing. |
| `rules/ecc/` (all 43 files) | [affaan-m/ECC](https://github.com/affaan-m/ECC) | Same, plus local additions in `common/code-review.md` and `common/testing.md`. |
| `skills/anti-ai-writing/` | third party, MIT | Recorded in `SKILLS-EVALUATION.md`. |
| `skills/voice-dna/`, `skills/business-analyzer/` | third party | **License not recorded.** Verify before relying on redistribution. |
| `hooks/jjstack-auto-approve-safe.patch` | a local diff against [disciplin-run-org/jjstack](https://github.com/disciplin-run-org/jjstack) | Patch only; jjstack itself is not vendored. |

The frameworks this setup runs on - gstack, jjstack, get-shit-done-cc, the Claude Code
plugins - are **not** vendored here. `SKILLS.md` documents how to install each from source.

The 6-line "Prompt Defense Baseline" block at the top of every file in `agents/` is
upstream ECC boilerplate. Editing one copy does not change the other 28.
