# Provenance

Most of this repo is other people's work, redistributed. This file says which is which,
because the LICENSE covers only the parts authored here.

## Authored here (MIT, see LICENSE)

| Path | What |
|---|---|
| `claude-home/skills/review-stack/` | Multi-agent pre-ship and PR review orchestrator |
| `claude-home/agents/regression-hunter.md` | Regression hunting: what worked before a diff and stops after |
| `claude-home/agents/pr-intent-verifier.md` | Does a PR do what it claims, and nothing else |
| `config/routing.md` | Prompt-to-skill routing reference table |
| `scripts/check-routing.py`, `scripts/asciify.py`, `scripts/private-names.py`, `scripts/spec-paths.py`, `scripts/fb-ask.py` | Repo tooling |
| `claude-home/hooks/block-destructive.sh` | Destructive-command guard |
| `claude-home/hooks/handover-start.sh` | Loads a waiting rollover handover after `/clear` (spec 0057) |
| `claude-home/mods/wf-handoff/` | `/handoff` mod: clears so the handover hook loads the handover (spec 0057); hands a chat off on its own at the token line (spec 0063) |
| `claude-home/hooks/plain-panel.py` | Panel check: every question offers "Learn this first", at most 3 real options, no jargon (spec 0028) |
| `_archive/runner/` | `wf`, the workflow runner (spec 0001) |
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
| `claude-home/rules/new-number-replaces-old.md`, `claude-home/skills/lead-finder/`, `claude-home/skills/reaction-tester/` | Ideas borrowed from Harvey, MiroFish and claude-skills-founder, written here from scratch (spec 0056) |
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
| `claude-home/mods/wf-handoff/facts.ts`, the trigger, gate and loop guards in `claude-home/mods/wf-handoff/hooks/register.ts` | [alexknowshtml/claude-auto-handoff](https://github.com/alexknowshtml/claude-auto-handoff) 0.8.6 | MIT. Design reused (spec 0063): token line with unmeasured tool output, tool gate, facts pulled from the transcript (their `extractFacts`), figures marked unverified (their `markUnverifiedFigures`), loop guards, templates. Written fresh here from that design: the upstream source was not fetched into this build, so no upstream file is copied. |
| `claude-home/mods/wf-handoff/pages.ts`, `claude-home/mods/wf-handoff/server.py`, the panel file in `claude-home/mods/wf-handoff/hooks/register.ts`, `claude-home/mods/chip-dash/handoff.ts` | [alexknowshtml/claude-auto-handoff](https://github.com/alexknowshtml/claude-auto-handoff) 0.8.6 | MIT. Design reused (spec 0064): a progress panel per step, a page per handover served on the Tailscale address (their `viewer.ts`, `server.ts`). Written fresh here from that design: GitHub is closed to this build, so no upstream file is copied. |
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

### ccdwyer/assertion-guardian

Patched here: assertion-guardian.
Copyright (c) 2026 Chris Dwyer
SPDX-License-Identifier: MIT

```
MIT License

Copyright (c) 2026 Chris Dwyer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

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
