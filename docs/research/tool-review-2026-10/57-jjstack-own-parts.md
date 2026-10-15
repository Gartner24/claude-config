# Row 57: jjstack - which parts are the user's, what is used, what a move needs

## 1. Authorship (git -C ~/.claude/skills/jjstack shortlog -sne --all)
- 256 Jesper Jurcenoks; 54 github-actions[bot]; user identities: "gartner24 <santiagovalencialeon@gmail.com>" 6, "Santiago Valencia <102266047+Gartner24@users.noreply.github.com>" 2, "Gartner24 <santiagovalencialeon@gmail.com>" 1 (9 commits, about 3% of history). Global git email = santiagovalencialeon@gmail.com.
- Upstream: `origin git@github.com:JesperJurcenoks/jjstack.git`. Local main tracks origin/main (`## main...origin/main`); HEAD = 0b659d3, same as the pin in ~/claude-config/config/manifest.json.
- The user's work is small edits plus one new skill, and none of it is a whole skill in use:
  - NEW, never merged: `bin/jjstack-spawn-review`, `skills/spawn-review/SKILL.md` (a782140, 2026-09-03). Only on `remotes/origin/feat/spawn-review`; `skills/` on main has no spawn-review.
  - Edits to upstream files, merged upstream via PRs: `bin/statusline.sh` + `test/smoke.sh` + CHANGELOG (show provider off Anthropic, real effort; 8fb9e48, PR #66); `skills/consensus/SKILL.md` (#32); `hooks/auto-approve-safe.sh` (9fc4e31); `skills/review/SKILL.md` + `bin/jjstack-verify-skills` + README (builtin-name collisions, bd922cc).
- Local-only: nothing committed. One uncommitted edit: `jjstack.config.yaml` output.location repo -> home (git diff). A config choice, not authorship.
- Conclusion: jjstack is Jesper's. The user owns no skill that the setup uses. Reimplementing "their parts" means nothing; the real question is who owns the other ~99%.

## 2. What the setup uses
- 54 jjstack skills are symlinks in ~/.claude/skills/ (not copies); `diff -rq` against jjstack/skills/ is identical for all 54 (own script, same=54 diff=0). Corrects the setup summary, which said "plain folders".
- settings.json hooks (grep): UserPromptSubmit `jjstack/hooks/skill-miss-detect.sh` (l.410), PreToolUse `skill-fired-clear.sh` (l.520), PostToolUseFailure `mcp-reconnect.sh` (l.542). Symlinks in ~/.claude/hooks/ to jjstack: `auto-approve-safe.sh`, `error-detector.sh`, `injection-guard.sh`, `permission-floor.py`.
- statusLine: ~/claude-config/runner/auto.py l.641 runs `bash ~/.claude/skills/jjstack/bin/statusline.sh` (237 lines).
- Named in rules: /review, /jj-security-review (CLAUDE.md), /rollover, /resume-from-clear, /save-and-clear (handoff.md), jjstack-rollover-slot, jjstack-skill-miss-report (spec 0036). install.sh l.120 calls `jjstack-extract-triggers`.
- Not jjstack, already own: review-stack, regression-hunter, pr-intent-verifier, intent-router (docs/NOTICE.md "Authored here"); context-monitor.js derived from gsd.
- Refs in claude-config: runner/auto.py, runner/tests/test_auto.py, test_skill_miss_hooks.py, bin/install.sh, claude-home/settings.json, rules/skill-map.md, manifest.json, many specs (0022, 0030, 0036, 0037, 0050).

## 3. Licence and provenance
- LICENSE: MIT, "Copyright (c) 2026 Jesper Jurcenoks". Redistribution allowed if the notice is kept.
- docs/NOTICE.md says the repo lists third-party code with upstream + licence; frameworks "are not vendored here". Vendoring needs a NOTICE row per file group (upstream, MIT, modified or not) plus the LICENSE text.
- manifest.json l.2881-2888: jjstack `fetch: manual`, source "private: ~/.claude/private/work.md", licence MIT. Remote is a github.com URL; the "private" label is a choice, not a licence limit (public repo status unverified: I did not fetch it).
- Dependencies: rollover, resume-from-clear, save-and-clear, review SKILL.md mention internal-relay / Quartermaster / gstack (grep). skill-miss-detect.sh only filters internal-relay/Quartermaster prompts (l.43-58), not required. /review wraps gstack /review and `bin/jjstack-review-*` helpers; rollover needs `bin/jjstack-rollover-slot` (290 lines). Whether the plain-session path of rollover works without internal-relay/QM is unverified; the setup summary says it does.

## 4. What moving into claude-home would need
- Per piece: copy file(s), add NOTICE row + keep MIT header, add manifest/skills-audit entry, change settings.json hook paths (3 hooks + statusline in auto.py + 4 symlinks), and own all future upstream merges by hand (no more `git pull`).
- Minimal set for the used behavior: statusline.sh, skill-miss-detect.sh, skill-fired-clear.sh, mcp-reconnect.sh, jjstack-skill-miss-report, jjstack-extract-triggers, plus 4 guard hooks, plus 3 handoff skills + jjstack-rollover-slot, plus review + its 5 jjstack-review-* helpers. About 15-20 files, and /review still needs gstack. Not a clean cut.
- Hidden coupling: ~/.jjstack/skill-triggers.json index, jjstack config yaml, jjstack-skills-pin, setup symlink creation. `./setup` also wires gstack.

## Recommendation: reject moving; keep pinned external (adopt as is)
- The user authored nothing in use, so there is no "own parts" migration. Everything used is Jesper's MIT code.
- Vendoring buys little (nothing breaks today; pin 0b659d3 already fixes the version) and costs a fork: merge conflicts on every jjstack update, NOTICE upkeep, gstack tie.
- Cheap hardening instead (about 1 hour): keep pin; copy only the single file the runner depends on (statusline.sh, 237 lines, MIT, plus the user's own provider/effort fix already merged upstream) if the status line must survive a jjstack outage; add a NOTICE row for it.
- Either push or drop `feat/spawn-review` (local knowledge only; unmerged upstream). If the user wants it, it is the only truly "own" artifact: 1 skill + 1 script, copyable into claude-home/skills with the user's authorship, effort about 30 min plus skill scan.
- Unverified: whether jjstack on GitHub is public; plain-session rollover without internal-relay; spawn-review quality.
