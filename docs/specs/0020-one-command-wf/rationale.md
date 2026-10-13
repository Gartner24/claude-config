# 0020. One command: wf (rationale)

## Context

On 2026-10-13 one morning showed the problem. `wf finish` held every repo's lock for 30 minutes while its install self checks hung, so `wf unpark` in another repo was refused. `wf finish` also refused because a run in another repo was going, and you had to start a wait loop by hand. The refusal named an old run's pid, because only `wf run` writes the holder line and a later taker leaves the old one in the file (`runner/run.py` `lock_file`).

Underneath, there are five commands (`wf run`, `wf finish`, `wf unpark`, `wf report`, `wf queue`) for one morning routine, and each one guards itself with locks that are broader than the work they protect. The only real conflict between `wf finish` and a run is the shared live setup in `~/.claude`. A run's guard hashes `settings*.json`, the plugin `hooks.json` and the hook scripts those settings name, and stops `guard_changed` on any change. Rules and agents are not hashed, so in practice only the install step stops runs.

Brief: [docs/briefs/never-wait-on-each-other.md](../../briefs/never-wait-on-each-other.md). Its "Agreed so far" items are taken as given: one command `wf`, the five steps in order behind one confirm, a run never stopped by `wf`, an atomic swap, no long locks, and refusals that name the real holder.

## Options considered

### Option 1: bare `wf` orchestrates the existing internals (chosen)
Bare `wf` plans from every part (report, live boxes, parks, the queue), shows one screen, then calls the same code the subcommands use. The setup is staged and swapped, runs trust a ledger, and parks retake by reason.
**Pros**: reuses spec 0017's parent, spec 0019's shapes and steps, and spec 0018's report. Small, testable slices. **Cons**: the internals stay as code paths to keep consistent.

### Option 2: a long lived `wf` daemon
A background service owns the queue, swaps and runs, and `wf` only talks to it.
**Pros**: one owner of all state, no locks between processes. **Cons**: a new process to supervise, restart and secure. That is far more than the problem needs, and it breaks the "each run is its own process" model specs 0004 to 0017 rest on.

### Option 3: keep the subcommands and remove only the refusals
`wf finish` stops refusing, and the docs list the order.
**Pros**: least code. **Cons**: you still type four commands in the right order. That is the rule you set.

## Rationale

Option 1 meets the one command rule without a new moving part. The design choices inside it, each answered by you on 2026-10-13:

- **Per file swap in a tight loop**, not a whole set behind directory links. Linux renames one path atomically. A whole set swap would turn `rules/`, `agents/`, `hooks/` into links, which reworks `sync.sh`, `install.sh` and the guard's path lists. The cost is a window of a few milliseconds where a starting Claude could see a mix of new and old files. Every file it reads is whole.
- **Running calls see the new files.** Probe P1 (verify.md) showed that a running `claude -p` 2.1.296 rereads `settings.json` mid call and runs hook scripts fresh for each tool use. Making every call run wholly under one setup would mean waiting for calls to end, which is the waiting this feature removes. The new files are whole and approved by you on the screen. So `settings.json` is renamed last: a hook it names is in place before it is read.
- **Stage, then swap** instead of a swap aware `install.sh`. `install.sh` already supports `CLAUDE_LIVE_DIR` for its own tests. Staging runs its self checks before anything goes live, so the 30 minute self check hang can no longer hold any lock or leave a half installed setup.
- **Ctrl C held and a crash finished forward.** Every new file is written aside before the first rename, so finishing the journal yields exactly what you approved. Rolling back would mean a second `wf` just to get the approved files back.
- **A fingerprint ledger** tells a swap made by `wf` from any other change. "Ignore changes while a `wf` is going" would accept anything in that window. The ledger accepts only byte exact content `wf` wrote, after the run's last baseline. A call cannot write `~/.claude`, and with the added Edit deny it cannot write the state folder either, so it cannot forge an accepted change. After accepting, the run rebuilds its guard, because new settings can name new hook scripts and change the deny lists.
- **Tick and commit anyway in a repo a run holds.** The overlap is a one line scope edit (reread right before, spec 0019 AC-6) and a commit of only `wf`'s own files. Git's index lock keeps the history whole; three retries absorb a call's commit happening at the same moment.
- **A second `wf` skips only the swap** (your answer, chosen over refusing or waiting). The swap lock covers only the stage, install and renames, and the second `wf` still shows the report, retakes and starts builds.
- **Retake by reason.** Each class of park depends on a different fix: code and check failures on a new commit, denials and timeouts on the setup or the Claude Code version, caps on a higher cap. Retaking on any change would rerun code failures after every setup swap; retaking always would spend budget blindly. An old record without `head` uses HEAD's committer time against `parked_at`.
- **Checks beside builds**, so nothing waits on the long end to end run. **A failed setup step still lets builds start** on the old setup, so one bad step never costs the night.
- `next`, `wf allow` and `wf ntfy` stay as you type them: they are one time setup or another job (opening an interactive session), not the daily flow.

Cross check (another model, 2026-10-13) found 15 issues; you chose to apply every recommended fix. The main changes: `install.sh` skips its writes outside the live dir under `WF_STAGE=1` and `wf` does them in the swap, with the git hooks copies in the ledger (otherwise staging was not isolated and a run in this repo stopped); the ledger has no time test (a run starting mid swap stopped); the journal is written before the asides and the ledger (a crash left orphans with nothing to finish); a code park is retaken only by a commit outside the scope and `verify.md` files (every `wf` tick and `/sync` moved HEAD); cap parks stay with `applies()`; unknown values never retake; the holder line is written then truncated; the stage is 0700 and cleaned; one `live_dir()` helper; the guard rebuild keeps each repo's own baseline; checks never write the live dir. The simpler option it offered (in place install plus expected hashes) was kept out, since staging is what runs the self checks before anything goes live.

Recommended without a question (small calls with full context): holder line contents `<pid> <time> <what>`; the swap lock name and scope; the ledger as an append only JSON lines file; the live dir from `CLAUDE_CONFIG_DIR` so that the swap, the guard and claude itself agree (runner up: keep `CLAUDE_LIVE_DIR`, rejected because the e2e check needs the run's guard to watch the same temp folder); 3 commit retries at 2 s (runner up: none, rejected because a call's commit at the same moment is common); the corpus test for AC-10 (a universal "no text tells you to type" claim needs a whole corpus assertion, `rules/lessons.md`).

## Amendment 2026-10-13: runner copy (AC-12)

A `wf run` call in this repo was denied every Edit of `runner/` (verify.md P2): the SessionStart hook names `~/.local/bin/wf`, `hook_tokens` follows it to `runner/wf.py`, and `deny_paths` denies that folder. Options: drop the token folder deny for the runner (weakens spec 0007), point the hook at a path outside the link (the token still resolves into the repo), or install a copy of the runner outside the repo. The copy keeps every guard as it is. One folder per content fingerprint was chosen over one flat folder (your answer): a running `wf` keeps reading its own folder, so an install or swap mid run never mixes old and new modules, and identical installs reuse the folder. Kept: the 5 newest plus any linked folder.
