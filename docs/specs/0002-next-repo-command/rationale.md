# 0002. `next <repo>`: rationale

Build spec: [index.md](index.md).

## Context

Every workflow step today ends with you typing `/clear`, then retyping the next command with its arguments. You also have to start the session in the right folder. The research counted 33 human touches to start one build, and its friction all had one cause. Sessions started in `~/.claude` while the work lived in `~/dotfiles`. Skills resolve `docs/scope`, `docs/specs` and `AGENTS.md` from the folder they start in, and nothing said which folder that was (section 1 of `~/Documents/workflow-research/09-autonomous-runner-research.md`).

The next step is already written down: each scope's first unticked box is a command (`/architect x`, `/develop x`, `/check verify x`). Reading it is mechanical, but the real scopes have rough edges:
- Status tags are written two ways (`· done` in claude-config, `(existing)` in dotfiles).
- Milestones sit under an unticked `Build it` box, and some carry wait notes ("after its branch is merged").
- Team repos keep the scope in `.workflow/scope/` instead of `docs/scope/`.
- Hub scopes (`~/projects`, `~/projects/freelance`, `~/projects/work`) have rows but no command boxes.

A scan found 25 scopes on disk, the deepest at ~/projects/freelance/<client>/<site> (three levels below ~/projects), under `~`, `~/projects/personal`, `~/projects/freelance` and `~/projects/work`.

The runner stack is decided in [spec 0001](../0001-runner-stack-and-layout.md): `runner/wf.py`, stdlib Python, `next` as a shortcut for `wf next`. Feature 2 (the scope contract) will later add `Repo`, `Source of truth` and `Autopilot` header fields. This spec does not need them; it reads the scopes as they are written today.

## Options considered

### Option 1: Discover scopes by scanning, fzf for choices (chosen)
Scan fixed roots for scope folders, match by folder name or title, read the box with a lenient parser, confirm on one line.

**Pros**:
- Nothing to maintain; a new repo shows up on its own.
- Works with scopes as written today, both tag styles and both bases.

**Cons**:
- A repo outside the roots is invisible until `WF_ROOTS` is set.
- The lenient parser can misread a scope written in an unusual style.

### Option 2: A registry file of name to path
`~/.config/wf/repos` maps each name to a folder.

**Pros**:
- Exact and fast; no scan or guessing.

**Cons**:
- Every new repo needs a hand edit, and a forgotten one fails silently as "no match".

### Option 3: Paths in the hub scopes
Add a path column to the hub tables and read repos from there.

**Pros**:
- One place lists all work, which the later queue features want.

**Cons**:
- Depends on the scope contract (feature 2), which is not designed yet, and hubs today list repos by name only.

## Rationale

The research's main friction was the wrong folder, and every fix that needs you to keep a list is the same failure in a new place. Scanning removes the list (basis: research section 1, the wrong folder friction). It is cheap at this size: about 25 scopes, three levels deep, read in milliseconds. Reading the first unticked box in file order is exactly the documented rule ("Next step = the first unticked box", `scope-template.md`), so `next` agrees with what `/scope` and `/develop` already say. The confirm line (basis: confirm before an action that starts paid work) costs one key press and catches the two expensive mistakes: a wrong match, and a dirty tree or wrong branch before a session starts work. Hubs are included because you asked for it. Their rows are shown rather than run, since hub rows are not commands.

### Amendment 2026-10-11: worktree discovery without git (feature 17)

After `c26dc8a` the list and picker stopped running git in scanned repos, but discovery still ran `git worktree list --porcelain` in every main checkout, and again for every candidate whose `.git` is a file (`runner/wf.py` `discover()` and `worktree_label()`). That command runs no filter drivers, and `GIT_SAFE` already turns off fsmonitor and hooks, so the `git status` danger did not strictly apply. The costs were that the rule had an exception, one subprocess per repo, and no worktrees at all when git is not installed.

Options you weighed:
- **Read the files (chosen).** `<main>/.git/worktrees/<id>/gitdir` names each worktree's `.git`. No git in a scanned repo, the rule has no exception, and worktrees are found without a git binary. It depends on git's on disk layout.
- **Keep `git worktree list`, record why it is allowed.** No code change, but the exception and the missing git case stay.

Smaller calls, each your pick: a linked worktree is told apart from a submodule by the `commondir` file (git writes it only for linked worktrees; matching a `worktrees/` path part would misfire on a folder that happens to have that name). A prunable entry is skipped silently, as it already was (its folder holds no scope). Reftable's `.invalid` placeholder labels as `worktree (branch unknown)`, so the label never claims detached when that is not known.

A cross check (another model) then found seven gaps, all closed with its recommended fix on your pick: skip unreadable or empty entries and a missing `.git/worktrees`; require the worktree's `.git` to point back to its `<id>` (a reused folder would otherwise get a wrong label); `detached` only for a commit hash, `branch unknown` for an unreadable, empty or other `HEAD`; strip whitespace, drop `gitdir:` only from a `.git` file, `clean()` the branch; name both join bases; read `<id>` sorted; record the `--separate-git-dir` miss.

Checked against git 2.56.0 in a temp repo: an absolute `gitdir` (default), a relative one (`worktree.useRelativePaths=true`, relative to the `<id>` folder, and the worktree's own `.git` file relative to the worktree), a detached `HEAD` holding a bare sha, and a submodule whose `gitdir:` folder has no `commondir`.

## References

**Project sources**:
- [Spec 0001](../0001-runner-stack-and-layout.md) (stack, layout, `next` shortcut)
- `~/Documents/workflow-research/09-autonomous-runner-research.md` sections 0, 1, 2 (stage 1, the wrong folder friction, next step = first unticked box)
- `~/.claude/skills/scope/scope-template.md` (next step rule, heading tags)
- `~/dotfiles/docs/scope/scope.md` (the `(existing)` tag style and milestone wait note)
- `docs/scope/scope.md` row 3

**Practices & standards**:
- Confirm before an action that starts paid work
- Pass external commands as argument lists, never through a shell

**Links**:
- Claude Code CLI reference (`claude "query"` starts an interactive session with an initial prompt): https://code.claude.com/docs/en/cli-reference
- git worktree (`list --porcelain` record format, the `.git` pointer in a linked worktree, the `$GIT_DIR/worktrees/<id>` files): https://git-scm.com/docs/git-worktree
- fzf man page (reads stdin, prints the pick; exit 130 on Ctrl C or Esc, 1 on no match): https://raw.githubusercontent.com/junegunn/fzf/master/man/man1/fzf.1
- `/proc/<pid>/cwd` (the proc_pid_cwd(5) man page): found by search but not fetched, so cited by name only
