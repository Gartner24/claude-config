# Verdict on the ./setup Claude Code configuration

I read the files under `./setup` as data. I was not allowed to execute the hooks or the test suite here, so everything about hook behavior below comes from reading the code. I compared it against Anthropic's Claude Code docs and best-practices guidance, and against four popular public setups I know well: everything-claude-code (ECC), obra/superpowers, gstack and get-shit-done (gsd). The setup vendors or borrows from three of those itself. I did not run web searches, so this comparison is from my own knowledge, not fresh research.

## 1. Better work, or ceremony?

**What loads into every session:**
- `claude-home/CLAUDE.md` is 12.9 KB, and the 20 files in `claude-home/rules/` add about 40 KB. That is about 52.7 KB, roughly 13k tokens, before you count the private import `@~/.claude/private/work.md`.
- Descriptions for 31 custom agents and 21 own skills add about 13 KB, roughly 3k tokens.
- About 250 framework skills are set to `name-only` in `settings.json`, which is still about 1.5-2k tokens of names. Seven enabled plugins add their own descriptions.
- Two hooks add text on top of that: `hooks/chain-catch.py --prompt` injects a reminder on every user message (UserPromptSubmit), and `workflow-start.sh` prints at session start.
- The wf-handoff mod then starts `/audit` or `/scope` by itself whenever a chat opens in one of the owner's repos, which loads a whole skill body.

A realistic baseline is 18-25k tokens before the user types anything. On `opus[1m]` the cost is minor. The real cost is attention: Anthropic's guidance is to keep CLAUDE.md short and prune anything Claude would do correctly anyway, because every extra line dilutes the ones that matter.

**Content that earns its place:**
- `rules/lessons.md`: "an absent answer rendered as a definite one" (`total ?? 0`), mutation-checking tests written after the fix, and "a universal claim needs a corpus-wide assertion on the real artifact". These are specific, come from real incidents, and fix things models really get wrong.
- `rules/check-gates.md` gates 1-2 ("a verify step must be able to fail", `can fail: <break>`) are a cheap, well-aimed check against fake verification.
- The "ticket is the spec" block and the two-question review frame (regression, intent) in CLAUDE.md are good.

**Content that is ceremony:**
- Roughly half of CLAUDE.md is routing for a personal process: `/scope`, `/architect`, `/develop`, tiers, briefs, handover indexes. There are paragraphs telling three overlapping review tools apart (`/code-review`, jjstack `/review`, `/review-stack`), including a note that jjstack shadows the built-in `/review`.
- `rules/check-gates.md` gates 3-5 and `rules/skill-map.md` are bookkeeping instructions for the owner's own spec system.
- Every chat in an owned repo starts by running `/scope` whether or not the task needs it. A Stop hook can refuse to end a turn up to 3 times (`chain-catch.py`, `CAP = 3`) because a scope box is "owed".

**Process overhead in the repo itself.** It has 71 specs, 94 closed scope rows in `docs/scope/done.md`, and about 338k words of docs. That is all for a dotfiles repo whose dates span roughly two months. The meta-work has become the product.

**Net:** a small kernel of excellent rules is buried in a personal workflow framework. The kernel helps. The framework mostly helps Claude follow the framework.

## 2. Reliability: do the hooks enforce what the rules claim?

**`hooks/block-destructive.sh` is the best file in the repo.**
- It fails closed when `jq` is missing (lines 580-584).
- It tokenizes split flags like `rm -r -f`.
- It blanks quoted prose so commit messages that mention `rm -rf` no longer trip it, and falls back to the raw text whenever there is doubt.
- It treats `bash -c`, `eval`, `xargs`, `ssh`, `awk` and similar as executors.
- It ships about 100 self-test cases, including regression cases found by earlier reviews.
- Its header honestly says it is "a backstop against typos ... not against an adversary."

**Gaps I found by reading it:**
- `cd ~ && rm -rf projects` passes. The target is relative, and `RM_TARGETS` only matches `/`, `~`, `$HOME`, `..`, `*` and `.`.
- `rm -rf ${HOME}` passes. The pattern is the literal `\$HOME`, so the brace form slips through.
- `rm -rf $PWD` passes.
- `git reset --hard` and `git checkout -- .` are not covered at all.

jjstack's `permission-floor.py` may catch some of these, but that file is not in this repo (see below).

**The four security hooks are not in the repo.** `settings.json` wires up `permission-floor.py`, `injection-guard.sh`, `auto-approve-safe.sh` and `error-detector.sh` from `~/.claude/hooks/`. None of them is in `claude-home/hooks/`. `docs/guides/HOOKS.md` says they come from the jjstack installer.
- On a machine without jjstack, the hook command exits 127. Claude Code treats that as a non-blocking error, so the permission floor and the injection scan silently disappear.
- The setup checks its own drift carefully (`claude-config.py drift`), but it never checks whether the hooks `settings.json` points at actually exist.

**`hooks/plain-panel.py` blocks (exit 2) any AskUserQuestion call that:**
- has more than 3 options,
- has no "(Recommended)" first option,
- has a label longer than 5 words or a description outside 6-30 words, or
- contains anything matching `\b[a-z]+(?:_[a-z0-9]+)+\b`.

That last pattern means asking "rename `user_id`?" is rejected as an "internal code", and so is any question where no option should be recommended. That is a misfire built into the design.

**`hooks/chain-catch.py` is careful engineering.**
- Scope text is echoed to the model only after a command allowlist (`SAFE_COMMAND`, `WORKFLOW`), so a malicious scope file cannot inject instructions.
- Errors let the turn end and are logged.
- It is off in headless runs.

But it is 920 lines of Markdown parsing whose job is to stop Claude from ending a turn. Any change in scope-file format becomes a silent no-op or a spurious block.

**The instructions already contradict themselves.**
- CLAUDE.md line 82: "the handoff mod hands a chat off by itself at 250k tokens".
- `settings.json` sets `AUTO_HANDOFF_TOKENS=250000`.
- `hooks/context-monitor.js` lines 11, 62-64 and 130 tell the model the handoff happens "at 200k". It also emits that warning at 250k, after the 200k point it describes.

This is the kind of drift the system was built to prevent, and it is already present in text the model sees.

## 3. Complexity and maintainability

**Moving parts:**
- `bin/` (1.9k lines), `scripts/` (5k lines) and `tests/` (2.8k lines).
- Two TypeScript mods with their own test files (`mods/chip-dash`, `mods/wf-handoff`, about 6k lines in total).
- A workflow engine (`workflows/review-fix/`).
- Copy-versus-symlink install semantics (`README.md` table), private-settings stripping and merge-back, a manifest of downloaded skills with patch files, and a retired runner in `_archive/runner/` that `install.sh` still copies out (per the README table).
- The whole thing sits on top of gstack, jjstack, ECC, seven plugins and three third-party marketplaces.

**Can one person keep this working?** Only the author, and only while they keep spending a large share of their time on it. Each upstream framework update can rename a skill, move a hook, or change the scope-file shape that `chain-catch.py` and `live-tick.py` parse.

**What breaks first:**
- The jjstack-hosted hook paths and `skills/gstack/hosts/claude/hooks/timeline-stop-hook` in `settings.json`. If upstream moves them, the guards vanish without a visible error.
- The `/review` shadowing note in CLAUDE.md.
- The 200k/250k-style text drift between hooks and instructions.

## 4. Security and privacy

**Risky:**
- **`settings.local.json`: `"enableAllProjectMcpServers": true`.** Any repo you clone that contains a `.mcp.json` gets its MCP servers started without a prompt. Combined with `"defaultMode": "auto"` and `"skipAutoPermissionPrompt": true`, this is the most serious item here.
- **`"Edit(~/.claude/CLAUDE.md)"` and `"Edit(~/.claude/rules/**)"` are pre-allowed.** Claude can rewrite its own global instructions without asking. A prompt injection that lands there persists into every future session.
- **`gh pr merge * -R Gartner24/*` is pre-allowed.** Claude can merge PRs in all of the owner's repos without a prompt.
- **The Read deny rules for `.ssh`, `.pem`, `.env.production` and similar do not stop `cat` through Bash.** That is a known Claude Code limitation. Coverage depends on the missing jjstack `permission-floor.py`.

**Privacy:**
- The private-name machinery is good. `scripts/private-names.py` checks every source before copying, `sync.sh` refuses atomically, and it reports orphaned files that were deleted live but are still published.
- It still let through the owner's personal email and git identities in `docs/research/tool-review-2026-10/57-jjstack-own-parts.md`, line 4.
- `/home/santiago/` paths throughout `settings.json` disclose the username and break portability.

**Hook hygiene is good.** Scripts use `python3 -I`, call external commands with argument lists, and use timeouts.

## 5. What is genuinely better than common practice

- **`block-destructive.sh` with its self-test** is more rigorous than the destructive-command hooks in ECC or typical dotfiles. Those usually match a few regexes and fail open.
- **The "checks that cannot lie" ideas** (`can fail:` notes, mutation checks, corpus-wide assertions in `lessons.md`) go beyond what superpowers' TDD skill asks for, and they target the real failure: false "done".
- **Excluding most of ECC (`claudeMdExcludes`) and setting 250 skills to `name-only`** shows real awareness of context cost. Most public setups load everything.
- **Treating scope and repo text as untrusted data inside Stop hooks** (`chain-catch.py` lines 52-61) shows prompt-injection awareness I rarely see in personal configs.
- **The sync pipeline's public/private split** is thoughtful.

## 6. The five changes that would help most

1. **Cut the always-loaded text to under 3k tokens.**
   - Keep the code rules, "ticket is the spec", the review frame, and `lessons.md`.
   - Move workflow routing, reviewer selection, `check-gates.md` gates 3-5, `skill-map.md`, the handoff rules and the design pipeline into the skills that use them, loaded on demand.
   - Drop the UserPromptSubmit reminder and the automatic `/scope` at chat open.
2. **Fix the dangerous permission defaults.**
   - Set `enableAllProjectMcpServers` to false.
   - Remove the `Edit(~/.claude/CLAUDE.md|rules/**)` allows.
   - Make `gh pr merge` ask.
   - Rethink `skipAutoPermissionPrompt` with `auto` mode.
3. **Vendor or pin the security hooks, and fail loudly when one is missing.**
   - Copy `permission-floor.py` and `injection-guard.sh` into `claude-home/hooks/`, or have `install.sh` and `drift` exit non-zero when a path named in `settings.json` does not exist.
   - A guard that can silently disappear is not a guard.
4. **Close the cheap guard gaps.**
   - In `block-destructive.sh`: `${HOME}`, `$PWD`, `git reset --hard` and `git checkout -- .`.
   - Relax `plain-panel.py`: warn instead of blocking, and drop the snake_case "internal code" rule and the mandatory "(Recommended)".
   - Fix the 200k/250k contradiction, and generate the number from one source.
5. **Shrink the stack.**
   - Pick one of gstack, jjstack or the built-in reviewers instead of three overlapping review paths.
   - Archive the spec and brief machinery for the config repo itself. 71 specs for dotfiles is a sign the process has replaced the goal.
   - Replace absolute `/home/santiago` paths with `~` or `$HOME`.

## Verdict

**average, 5/10.** The hook engineering (`block-destructive.sh`, `chain-catch.py`'s injection handling) and the lessons and gates are well above common practice, and a few of those rules would really improve Claude's output. But they sit inside an overbuilt personal process framework: about 20k tokens of standing context, guards that can silently vanish, contradictions already in what the model reads, and permission settings (`enableAllProjectMcpServers`, self-editable rules) that undercut the safety work.
