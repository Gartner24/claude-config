# 0002. `next <repo>`: start a repo's next scope step in one command

**Date**: 2026-10-11
**Status**: Accepted

## Summary

`next <name>` finds a repo by a path, its folder name or its scope title, reads the first unticked box in its scope, and shows you one line: repo, branch, uncommitted files, feature and the exact command. Press Enter and it opens an interactive Claude session inside that repo, already running the command. With no name it uses the repo you are in, or offers a picker (fzf) of every repo with its next step. `wf next --list` prints that list without launching anything. It removes the `/clear`, the retyping and the wrong folder, which were the main hand steps in the research.

## Requirements

**User stories**:
- As you, from any folder, I want `next dotfiles` to open a session in `~/dotfiles` already running its next step, so that I never type `/clear`, a command, or a `cd`.
- As you, I want to see every repo's next step at once, so that I can pick what is safe to work on.

**Acceptance criteria**:
- **AC-1**: A folder is a candidate when it holds `docs/scope/scope.md`, `docs/scope/index.md`, `.workflow/scope/scope.md` or `.workflow/scope/index.md`. The default roots are `~` (its direct child folders) and `~/projects` (itself and folders up to three levels below). Hidden folders and `node_modules` are skipped. `WF_ROOTS` (a colon separated list of folders) replaces the default roots. Each listed root is scanned the same way as `~/projects`: the root itself and up to three levels below. Candidates are deduplicated by real path (symlinks resolved), so `~/projects`, which is both a child of `~` and a root, appears once. Deeper repos need `WF_ROOTS`.
- **AC-2**: For each candidate that is a main checkout (its `.git` is a folder), its linked worktrees (from `git worktree list --porcelain`) that hold a scope are candidates too, wherever they live. A worktree's label is `worktree <branch>`, or `worktree (detached)` when its record has no `branch` line. A main checkout has no label. A worktree found both by the scan and through git appears once (AC-1 dedupe).
- **AC-3**: The argument is a path when it names an existing folder that holds a scope (`next .`, `next ~/x`). That folder is used directly, even outside the roots. Otherwise it is a name, matched case insensitively against each candidate's folder name and its scope title (the text after `# Scope:` on the first heading). Exact matches win over substring matches. One match is used directly. Several matches open fzf over just those. No match prints `no scope matches '<name>'` and exits 1.
- **AC-4**: `next` with no argument looks at the current folder, then each parent in turn, and uses the first one that is a candidate and not a hub. Finding none, it opens fzf over all candidates. Cancelling fzf, here or in AC-3, exits 0 and launches nothing.
- **AC-5**: Boxes are lines matching `^\s*[-*+]\s+\[([ xX])\]`. A space inside the brackets means open, `x` or `X` means ticked. The next box is the first open box in file order. These are never read: HTML comments (which may span lines), fenced code blocks, and everything from a `## Deferred` heading to the next `##` heading. A box also counts as gone when its feature is done, existing or dropped. Its feature is the nearest `###` heading above it. Any heading of level 1, 2 or 3 starts a new feature context, so a `##` heading clears the previous `###`. A feature is done, existing or dropped when its heading carries that word as a whole tag: case insensitive, either inside parentheses (`(done)`) or as a `·` segment (`· done`, ending at the next `·` or the line end). `(done criteria)` is not a tag. For an `index.md`, its own boxes are ignored. The epic files are its relative `.md` links that resolve inside the scope folder, read once each in first link order. URLs, anchors and links outside the folder are ignored. A linked epic file that is missing adds a warning, and reading goes on.
- **AC-6**: The command is the first backticked span in the box matching `^/[a-z][\w:-]*(\s|$)`. So `/etc/keyd` is not a command and `/develop x` is. A milestone is an open box that has a parent. Parents come from a stack of the boxes read so far: before a box is pushed, every box on the stack with the same or more leading whitespace (tabs and spaces both count) is popped, and the box left on top is its parent. Any heading of level 1, 2 or 3 empties the stack. So sibling milestones at the same indent share one parent, even though the box just above a later sibling is not less indented. An open milestone runs its parent's command and shows its own text as the note. When the chosen box is a parent with open milestones under it, the first open milestone becomes the note. A note containing `after` or `waits on` as a word is marked `waiting:`. A top level box with no command prints `no command in this box, run it yourself` and exits 3 with no session, `-y` or not.
- **AC-7**: A scope with no open box prints `nothing to run in <name>` and exits 0 with no session. This includes a brownfield scope that only has `existing` rows. A hub is a scope with no box lines at all. For a hub it also prints its At a glance rows that are still open: the last table cell, lowercased, whose first word is not done, dropped or existing.
- **AC-8**: Before launching, one line shows:
  - the name and label, and the git branch (`detached <short sha>`, `no commits`, or `no git` when there is no branch to show)
  - the uncommitted change count (lines of `git status --porcelain`, shown as `N changes`, or `-` with no git)
  - the feature (its heading with the number kept and the status and decision tags removed), and the command
  - the note and any warnings, when present
  An empty line (Enter) launches. Any other input, Ctrl C or end of input cancels with exit 130 and launches nothing. `-y` launches with no wait.
- **AC-9**: Unless AC-16 applies, launching changes into the candidate folder and replaces the `next` process with `claude <command>` (`os.execvp`). The command is passed as one argument, with no shell. Ctrl C and the exit code are then claude's own.
- **AC-10**: The launch line warns `N session(s) already open here` when running processes match. A match has `comm` equal to `claude`, a command line without `--chrome-native-host`, and a working folder equal to the candidate or inside it. It still launches on Enter.
- **AC-11**: When both `docs/scope/` and `.workflow/scope/` exist, `docs/scope/` is used, with a warning that names both.
- **AC-12**: `wf next --list` prints one line per candidate, sorted by name, in tab separated columns: name, label, feature, command (or `nothing to run`), branch, changes. It takes no argument and no `-y` (either is a usage error, exit 2). It launches nothing and exits 0. The fzf picker shows the same columns.
- **AC-13**: Calling the program as `next` behaves exactly as `wf next` with the same arguments.
- **AC-14**: A missing `claude` is checked before the confirm line is shown, and a missing `fzf` when a picker is needed. Either prints which one is missing and exits 1. `--list` and a single match never need fzf. A missing `git` is not an error: branch shows `no git` and changes show `-`.
- **AC-15**: A manual check against the real `claude` binary confirms that `claude "/develop x"` opens an interactive session with that slash command running. It is recorded in the verify step, since every automated test uses a fake `claude`.
- **AC-16**: Launch mode. When `$TMUX` is set, `next` does not exec. It runs `tmux new-window -c <candidate path> -n <name> claude <command>` as an argument list (tmux runs a multi argument command directly, with no shell), prints `opened tmux window <name>`, and exits 0, so the calling shell or Claude session stays where it is. When `$TMUX` is unset and stdin is a terminal, it execs as in AC-9. When `$TMUX` is unset and stdin is not a terminal, it launches nothing, prints `cd <candidate path> && claude <command>` with the command shell quoted, and exits 4. In every mode, when stdin is not a terminal the confirm line (AC-8) is printed and `-y` is required to launch; without `-y` it exits 130.

## Decision

**Chosen option**: Option 1: Discover scopes by scanning, fzf for choices

`wf next` scans the roots, matches a name to a scope, finds the first unticked box, shows one confirm line, and runs `claude <command>` inside the repo.

## Feature design

**Data model sketch** (in memory only, nothing stored):
- `Candidate`: `path` (real path, required, unique), `scope_dir` (`docs/scope` or `.workflow/scope`, required), `name` (folder basename, required), `title` (from `# Scope:`, nullable), `label` (empty, `worktree <branch>` or `worktree (detached)`), `is_hub` (true when its scope files have no box line), `warnings` (list).
- `NextBox`: `feature` (display heading, nullable for a box outside any feature), `box_text` (required), `command` (nullable), `note` (milestone text, nullable), `waiting` (bool), `file` and `line` (required).
- A candidate has zero or one `NextBox`.

**API surface** (command line):
| Command | Key inputs | Key outputs | Exit codes |
|---|---|---|---|
| `wf next [path or name] [-y]` | path or name (opt), `-y` (opt) | launch line, then `exec claude` | before exec: 0 nothing to run or picker cancelled; 1 no match or a missing claude or fzf; 2 usage error; 3 box without a command; 4 no terminal and no tmux, command printed instead; 130 cancelled at the confirm. After exec the exit code is claude's own. |
| `wf next --list` | none | tab separated line per candidate | 0; 2 with any argument or `-y` |
| `next ...` | same as `wf next` | same | same |

**Value sourcing**:
| Action | Value produced / displayed | Source |
|---|---|---|
| discover | candidate folders | scan of `WF_ROOTS`, else the default roots (AC-1), plus `git worktree list --porcelain` per main checkout (AC-2), deduplicated by `os.path.realpath` |
| discover | `scope_dir` | whichever of `docs/scope`, `.workflow/scope` holds `scope.md` or `index.md`, with `docs/` winning (AC-11) |
| discover | main checkout | `<path>/.git` is a folder |
| match | path argument | the argument names an existing folder holding a scope (AC-3) |
| match | name, title | folder basename; the first `# Scope:` heading of `scope.md` or `index.md` |
| match | current candidate | cwd, then each parent in turn; the first that is a candidate and not a hub (AC-4) |
| next box | open or ticked | `^\s*[-*+]\s+\[([ xX])\]` (AC-5) |
| next box | feature, done/existing/dropped | nearest `###` above, reset by any heading of level 1 to 3; tag test, case insensitive: `\(\s*(done\|existing\|dropped)\s*\)` or `·\s*(done\|existing\|dropped)\s*(?=·\|$)` |
| next box | feature display | heading text without `#`, with tag groups (`· ...`, `(...)` status or `needs a decision`) removed, number kept |
| next box | command | first backticked span matching `^/[a-z][\w:-]*(\s\|$)` (AC-6) |
| next box | parent, note, waiting | leading whitespace comparison (AC-6); `waiting` when the note matches `\b(after\|waits on)\b`, case insensitive |
| launch line | branch | `git -C <path> rev-parse --abbrev-ref HEAD`; `HEAD` means detached, shown as `detached` plus `git rev-parse --short HEAD`; failure inside a repo with no commits shows `no commits`; no repo or no git binary shows `no git` |
| launch line | changes | line count of `git -C <path> status --porcelain`; `-` with no repo or no git binary |
| launch line | open sessions | for each `/proc/<pid>`: `comm` equal to `claude`, `cmdline` without `--chrome-native-host`, `cwd` real path equal to or under the candidate path; unreadable entries skipped |
| launch line | worktree label | the `branch refs/heads/<x>` line of that worktree's porcelain record, else `(detached)` |
| launch | launch mode | `$TMUX` set, then `os.isatty(0)` (AC-16) |
| hub rows | open rows | At a glance table rows whose last cell, lowercased, does not start with done, dropped or existing |

**Key invariants**:
- `next` never launches without either an empty line at the confirm prompt or `-y`.
- A candidate appears once, by real path.
- The command reaches `claude` as one argument in an argument list; no shell ever parses scope text.
- A box is read, never written. `next` changes no file in any repo.

**Security model**:
- Local, single user. Scope files come from repos under your roots. A cloned third party repo could put a crafted command in its scope, which is why the confirm line shows the exact command before launch. `-y` skips that look, so use it only on your own repos.
- No credentials, no network.

**Critical test scenarios**:
Fixtures are trimmed copies of real scopes pinned in `runner/tests/fixtures/` (dotfiles, claude-config, the personal hub, a `.workflow/` team scope), never read live. A fake `claude` script on PATH records its cwd and argv.
- Happy path, real shape: dotfiles fixture (open `Build it` parent, milestones ticked except one "after its branch is merged"), `next dotfiles -y` execs the fake with cwd the fixture and argv `/develop repo layout and linking method`, note marked `waiting:`, verifies **AC-3**, **AC-5**, **AC-6**, **AC-9**.
- Milestone under a ticked parent launches the parent command with the milestone note, verifies **AC-6**.
- Status tags: `· done`, `(existing)`, `(DROPPED)` features are skipped, `(done criteria)` is not, a `## Deferred` box and a box in a fenced block or a multi line comment are ignored, a `##` heading after a done `###` resets it, verifies **AC-5**.
- Command extraction: a box whose first backticks hold `/etc/keyd` and later `/develop x` yields `/develop x`; a box with no command exits 3 even with `-y`, verifies **AC-6**.
- Epics: `index.md` linking two epic files plus a URL and a missing file reads both epics in order and warns once, verifies **AC-5**.
- Hub and brownfield: the personal hub prints its open rows; a scope with only `existing` rows prints `nothing to run`; both exit 0 with no exec, verifies **AC-7**.
- Discovery: `WF_ROOTS` with a root holding a repo two levels down finds one three levels down and not one four levels down; a symlinked duplicate appears once, verifies **AC-1**.
- Path and names: `next <fixture path>` works outside the roots; `next work` picks the exact folder over `workflow-automation`; `next personal` matches the hub title; `next zzz` exits 1, verifies **AC-3**.
- No argument: inside a repo uses it; inside a folder below a hub with no scope of its own does not pick the hub (fzf is stubbed and receives all candidates), verifies **AC-4**.
- Confirm: input `n` and end of input both exit 130 with no exec; an empty line execs, verifies **AC-8**.
- Sessions: a stubbed `/proc` listing with one claude in the repo, one in a subfolder and one `--chrome-native-host` warns `2 session(s)`, verifies **AC-10**.
- Both bases present: `docs/scope` wins with a warning, verifies **AC-11**.
- Worktree: a temp repo with a linked worktree on a branch and one detached lists three candidates with the right labels, verifies **AC-2**.
- List: `wf next --list` prints sorted tab separated lines; `wf next --list x` exits 2, verifies **AC-12**.
- Shortcut: invoking through a `next` symlink equals `wf next`, verifies **AC-13**.
- Missing tools: no `claude` on PATH exits 1 before the prompt; no `fzf` with several matches exits 1; no `git` shows `no git` and `-`, verifies **AC-14**.
- Launch mode: with `$TMUX` set and a fake `tmux` on PATH, `next dotfiles -y` calls `tmux new-window -c <fixture> -n dotfiles claude '/develop repo layout and linking method'` and exits 0 with no exec; with `$TMUX` unset and stdin not a terminal it prints the cd line and exits 4; with stdin not a terminal and no `-y` it exits 130, verifies **AC-16**.
- Manual: from a real repo, `next <repo>` opens a real session running the command, recorded in the verify step, verifies **AC-15**.

## Build plan

Skateboard: the first milestone is already usable on its own (`next <exact name> -y` works), then each milestone widens what `next` handles.

1. Skeleton `runner/wf.py` with the `wf next` subcommand and the `next` shortcut, plus the `install.sh` symlinks and test hook, satisfies **AC-13**, **AC-14**
2. Discovery with realpath dedupe, path argument, exact or substring matching over the default roots and `WF_ROOTS`, both scope bases, satisfies **AC-1**, **AC-3**, **AC-11**
3. Box parser: box syntax, comments and fences, Deferred, heading resets and tags, command pattern, milestones and waiting notes, hubs and brownfield, `index.md` epics, satisfies **AC-5**, **AC-6**, **AC-7**
4. Confirm line and exec: branch states, change count, open session warning, empty line or `-y`, satisfies **AC-8**, **AC-9**, **AC-10**, **AC-14**, **AC-16**
5. No argument and several matches via fzf, linked worktrees, `--list`, then the manual real claude check, satisfies **AC-2**, **AC-4**, **AC-12**, **AC-15**

## Consequences

**Positive**:
- One command from any folder replaces `/clear`, `cd` and retyping.
- `--list` answers "what is safe to pick up" across all repos at once.

**Negative / tradeoffs**:
- The parser encodes today's two scope styles. A third style (or a skill changing the template) can make `next` misread a box until the parser learns it; the fixtures are the early warning.
- A repo outside the roots is invisible without `WF_ROOTS`.
- The open session check reads `/proc`, so it is Linux only (the runner's only target).
- Including worktrees can show stale copies of a scope; the label is the only guard.

**Neutral**:
- Feature 2 (scope contract) may replace the scan with `**Repo:**` fields later; this design keeps discovery in one function so that swap stays local.

## Follow-up

- [ ] Feature 2 (scope contract): decide whether hubs get paths, whether `/scope` should write status tags in one style so the parser can drop the second regex branch, and the syntax for a skipped box (the template mentions "skipped" boxes but defines no marker, so `next` treats them as open today).

Decision record (context, options, rationale, references): [rationale.md](rationale.md). Verify steps: [verify.md](verify.md).
