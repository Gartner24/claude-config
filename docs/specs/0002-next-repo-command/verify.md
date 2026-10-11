# Verify: `next <repo>` · spec 0002 · updated 2026-10-11
_Steps derived from spec 0002 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## UI / manual
- [x] In a plain terminal (no tmux), from `~/.claude`: `next dotfiles`, press Enter -> a Claude session opens in `~/dotfiles` with `/develop repo layout and linking method` already running -> AC-15, AC-9
  (2026-10-11: run against a scratch repo whose box is `/help`, so no real build started; claude opened in that folder with `/help` showing, process `claude /help` replaced `next`)
- [x] Same, but type `n` at the prompt -> nothing launches, `echo $?` prints 130 -> AC-8
- [x] Inside tmux: `next dotfiles` then Enter -> a new tmux window named `dotfiles` runs the session, the calling pane stays put -> AC-16
- [x] From inside a running Claude session (no tmux): `next dotfiles -y` -> prints the `cd ... && claude '...'` line and exits 4, nothing launches -> AC-16
- [x] `cd ~/dotfiles/home && next` -> uses dotfiles (parent walk) -> AC-4
- [x] `cd ~/projects/personal && next` (a folder below the hub with no scope) -> fzf opens over every repo; Esc exits 0 -> AC-4
- [x] A name matching several repos (e.g. `next <org>`) -> fzf over just those; pick one -> its confirm line -> AC-3
- [x] With a Claude session already open in the repo -> confirm line shows `warning: 1 session(s) already open here`; the chrome native host process is not counted -> AC-10

## Commands
- [x] `next --list` -> one tab separated line per repo under `~` and `~/projects`, sorted by name, 6 columns; `~/projects` (the hub) appears once and says `nothing to run` -> AC-1, AC-12
- [x] `next --list x` and `next --list -y` -> usage error, exit 2 -> AC-12
- [x] `next zzz` -> `no scope matches 'zzz'`, exit 1 -> AC-3
- [x] `next work` -> picks `~/projects/work` (exact), not `workflow-automation` -> AC-3
- [x] `next personal` -> matches the hub by its title, prints its open At a glance rows, exit 0 -> AC-3, AC-7
- [x] `next ~/dotfiles` and `next .` from inside a repo -> path argument used directly -> AC-3
- [x] `WF_ROOTS=/some/dir next --list` -> only repos under that root, up to three levels down -> AC-1
- [x] A repo with an open linked worktree -> `next --list` shows it with `worktree <branch>`; a detached one shows `worktree (detached)` -> AC-2
- [x] A team repo with `.workflow/scope/` -> found and read; a repo with both bases warns and uses `docs/scope` -> AC-11
- [x] `PATH=/nonexistent /usr/bin/python3 ~/.local/bin/next dotfiles` -> `claude not found on PATH`, exit 1, no confirm line -> AC-14
- [x] `ls -l ~/.local/bin/next` -> symlink to `runner/wf.py`; `next --list` equals `wf next --list` -> AC-13
- [x] `python3 -m unittest discover -s runner/tests` -> 28 tests pass -> all automated ACs

## Value sourcing
- [x] Branch states: a repo on a branch shows its name; a detached HEAD shows `detached <sha>`; `git init` with no commits shows `no commits`; a folder outside git shows `no git` and `-`
- [x] Changes: edit a file in a repo, its confirm line count goes up by one
- [x] Feature display: claude-config shows `3. ...` style with the number kept and `· in-progress` / `(needs a decision)` removed
- [x] Command: a box mentioning `/etc/keyd` before its command still yields the slash command
- [x] Waiting note: dotfiles shows `waiting:` because its open milestone says "after its branch is merged"
- [x] Hub rows: only rows whose status is not done, dropped or existing are printed

## Acceptance-criteria coverage
- AC-1 list + WF_ROOTS steps; test_discovery_depth_and_symlink_dedupe
- AC-2 worktree step; test_worktrees_listed_with_labels
- AC-3 name and path steps; test_exact_name_beats_substring_and_no_match, test_path_argument_outside_roots, test_several_matches_go_to_fzf_and_cancel_exits_0
- AC-4 parent walk and hub picker steps; test_no_argument_uses_cwd_repo, test_no_argument_below_hub_opens_picker_over_all
- AC-5 status tag and command steps; TestParser
- AC-6 command and waiting steps; TestParser, test_no_command_box_exits_3_even_with_y
- AC-7 hub step; test_hub_and_brownfield_have_nothing_to_run
- AC-8 `n` at prompt step; test_confirm_line_inputs
- AC-9 real launch step; test_happy_path_execs_claude_in_repo
- AC-10 session warning step; TestSessions
- AC-11 both bases step; test_both_bases_docs_wins, test_workflow_base_alone
- AC-12 list steps; test_list_sorted_and_usage_errors
- AC-13 symlink step; test_next_shortcut_equals_wf_next
- AC-14 missing claude step; test_missing_claude_fzf_and_git
- AC-15 manual real claude step only (no automated test by design)
- AC-16 tmux and non terminal steps; test_launch_modes
