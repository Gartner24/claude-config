# Provenance

Most of this repo is other people's work, redistributed. This file says which is which,
because the LICENSE covers only the parts authored here.

## Authored here (MIT, see LICENSE)

| Path | What |
|---|---|
| `claude-home/skills/review-stack/` | Multi-agent pre-ship and PR review orchestrator |
| `claude-home/agents/regression-hunter.md` | Regression hunting: what worked before a diff and stops after |
| `claude-home/agents/pr-intent-verifier.md` | Does a PR do what it claims, and nothing else |
| `claude-home/skills/intent-router/`, `config/routing.md` | Prompt-to-skill routing table and its scorer |
| `scripts/check-routing.py`, `scripts/asciify.py`, `scripts/private-names.py`, `scripts/spec-paths.py`, `scripts/fb-ask.py` | Repo tooling |
| `claude-home/hooks/block-destructive.sh` | Destructive-command guard |
| `claude-home/hooks/plain-panel.py` | Panel check: every question offers "Learn this first", at most 3 real options, no jargon (spec 0028) |
| `runner/` | `wf`, the workflow runner (spec 0001) |
| `claude-home/skills/auto/` | `/auto on`, `/auto off`: autonomous mode, the session drives `wf` (spec 0030) |
| `claude-home/skills/improve-my-system/` | Weekly review of your own session history, redacted before any model reads it (spec 0061) |
| `claude-home/rules/scope-contract.md` | The scope format the runner reads and the skills write (spec 0003) |
| `claude-home/rules/spec-gate.md` | Spec gate: the agreeing section, probe before accept, small change fast path, `docs/architecture.md` |
| `claude-home/rules/handoff.md` | Handoff override: replaces the skills' bare "/clear" line with `/rollover` or `/save-and-clear` |
| `claude-home/rules/standing-answers.md` | Standing answers: skill questions answered the same way every time in interactive sessions |
| `claude-home/rules/plain-questions.md` | Plain words: everything said to you in plain words, a "Learn this first" option on every panel, and an explanation from zero on request (spec 0028) |
| `claude-home/rules/skill-map.md` | Skill map: which skill fits each situation, its rough cost, and who starts it |
| `claude-home/rules/check-gates.md` | Check gates: verify steps and tests that can fail, `**Paths:**` on every spec with `/sync` stale warnings, cross checks against the brief (spec 0015) |
| `claude-home/rules/review-fix.md` | After a review: which findings are fixed without asking, which are asked, and the two round stopping point |
| `claude-home/rules/cheap-worker.md` | Cheap worker tier: which text jobs go to `fb-ask`, the never list, and what exit 3 or 4 means (spec 0023) |
| `claude-home/rules/ecc/*/index.md` (7 files) | Per-language rule indexes - authored here, not upstream. They only `@import` the files below. |
| `bin/sync.sh`, `claude-home/CLAUDE.md`, `claude-home/rules/ecc/common/{code-review,testing}.md` additions | Setup and the hand-earned rules |

## Redistributed from elsewhere

| Path | Upstream | Notes |
|---|---|---|
| `claude-home/agents/` (27 of 31 files) | [affaan-m/ECC](https://github.com/affaan-m/ECC) | Cherry-picked, then frozen. Confirm ECC's license before reusing. |
| `claude-home/rules/ecc/` (43 of 50 files) | [affaan-m/ECC](https://github.com/affaan-m/ECC) | Same, plus local additions in `common/code-review.md` and `common/testing.md`. The other 7 are the `index.md` files listed above. |
| `claude-home/agents/scout.md`, `claude-home/agents/researcher.md` | [JavaScript-Mastery-Pro/skills](https://github.com/JavaScript-Mastery-Pro/skills) | MIT; copied unchanged as the helper agents its workflow skills call. |
| `claude-home/skills/deep-research/` | [affaan-m/ECC](https://github.com/affaan-m/ECC) | Forked 2026-10-11 so an ECC reinstall cannot overwrite it; local additions: academic tools, web, code and forum search tools, fallback rule. |
| `claude-home/hooks/context-monitor.js` | [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) (`get-shit-done-cc` on npm) | MIT. Derived from its `gsd-context-monitor.js`: reads the transcript instead of the status line bridge file, token thresholds from `~/.claude/CLAUDE.md` (spec 0037). |
| `claude-home/skills/anti-ai-writing/` | third party, MIT | Recorded in `docs/research/SKILLS-EVALUATION.md`. |
| `claude-home/skills/voice-dna/`, `claude-home/skills/business-analyzer/` | third party | **License not recorded.** Verify before relying on redistribution. |

The frameworks this setup runs on - gstack, jjstack, get-shit-done-cc, the Claude Code
plugins - are **not** vendored here. `docs/guides/SKILLS.md` documents how to install each from source.

The 6-line "Prompt Defense Baseline" block after the frontmatter of 29 files in `claude-home/agents/`
(the 27 ECC agents plus `regression-hunter.md` and `pr-intent-verifier.md`) is upstream
ECC boilerplate. Editing one copy does not change the other 28. `scout.md` and
`researcher.md` do not carry it.

<!-- manifest:start -->

## Downloaded skills with a public patch

Written by `bin/claude-config.py build` from `config/manifest.json`; edit the manifest, not this part.

## Not redistributed

Named in the manifest only; no file or patch of these is in this repo.

- astro: astrolicious/agent-skills (unknown)
- figma-code-connect: figma/mcp-server-guide (none)
- figma-create-new-file: figma/mcp-server-guide (none)
- figma-design-to-code: figma/mcp-server-guide (none)
- figma-generate-design: figma/mcp-server-guide (none)
- figma-generate-diagram: figma/mcp-server-guide (none)
- figma-generate-library: figma/mcp-server-guide (none)
- figma-generative-plugins: figma/mcp-server-guide (none)
- figma-implement-motion: figma/mcp-server-guide (none)
- figma-shaders: figma/mcp-server-guide (none)
- figma-swiftui: figma/mcp-server-guide (none)
- figma-use: figma/mcp-server-guide (none)
- figma-use-figjam: figma/mcp-server-guide (none)
- figma-use-motion: figma/mcp-server-guide (none)
- figma-use-slides: figma/mcp-server-guide (none)
- high-end-visual-design: Leonxlnx/taste-skill (unknown)
- industrial-brutalist-ui: Leonxlnx/taste-skill (unknown)
- minimalist-ui: Leonxlnx/taste-skill (unknown)
- packshot: source unknown (unknown)
- project-finder: source unknown (unknown)
- tailwind-4-docs: lombiq/tailwind-agent-skills (unknown)
- transitions-dev: Jakubantalik/transitions.dev (custom)
- transitions-polish: Jakubantalik/transitions.dev (custom)

<!-- manifest:end -->
