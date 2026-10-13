# 0013. Work names out of the public repo

**Date**: 2026-10-12
**Status**: Accepted
**Amended**: 2026-10-12, AC-7 copies the checker into the commit hooks instead of linking it

## Summary

This public repo names work orgs, a PR bot, client skills, client sites and private tool paths, on the branch, on main and in old commits. The names move to a few local files under `~/.claude/private/` that are never copied into the repo. A single checker reads the names list and blocks any copy or commit that would bring a name back. Then the whole history is rewritten (every name swapped for a placeholder), and the GitHub repo is deleted and pushed fresh, so old commits stop being reachable.

## What you're agreeing to

- Your private names and the rules that use them live in `~/.claude/private/`. Your `CLAUDE.md` pulls the rules in with one import line, so Claude behaves as today.
- `sync.sh`, and every commit in this repo, refuse to run while a name would land in the repo, or while the names list is missing.
- `install.sh` puts your private deny rules back into `settings.json`, so a reinstall never drops them.
- Every commit gets rewritten. You delete the GitHub repo and push the clean `main` to a new one with the same name. Commit IDs change, and the old ones are gone for good.
- Public readers lose the jjstack install link and the bot reviewed repo details. They see a pointer to a private file instead.
- The commit hooks are copies of the checker, not links to it. A change to the checker reaches your commits only when you rerun `install.sh`.

## Requirements

**User stories**:
- As you, I want no work or client name anywhere in the public repo, its history included, so that nothing private is published.
- As you, I want my setup to behave exactly as today after the move, so that the review rules and deny rules still apply.
- As you, I want sync and commits to stop a name before it lands, so that a leak cannot come back quietly.

**Acceptance criteria**:
- **AC-1** (names list): `~/.claude/private/names.txt` holds one name per line, optionally `name==>replacement`. Blank lines and lines starting with `#` are skipped. A line starting with `regex:` or `glob:` is refused (names are literal). Matching is case insensitive, as a substring. The rewrite never reads `names.txt` directly: `filter-expr` (AC-10) turns it into case insensitive expressions, because `git filter-repo` literal lines are case sensitive (P2). When the file is missing, unreadable, or holds no name, every command that reads it (AC-3 to AC-8, AC-10) prints `private names list missing or empty: ~/.claude/private/names.txt` and exits 1. It never treats a missing list as nothing to hide.
- **AC-2** (CLAUDE.md split): every name bearing passage of the live `~/.claude/CLAUDE.md` moves verbatim into `~/.claude/private/work.md`. The bot reviewed orgs, the PR bot, the jjstack source org and any other line naming a listed name all go there. The live `CLAUDE.md` gets one line `@~/.claude/private/work.md` where the first passage stood, plus a short neutral sentence wherever a sentence would otherwise dangle. Probe P1 (verify.md) passes: in a fresh `claude -p` session, the answer to "which orgs are bot reviewed" names the orgs from `work.md`. A P1 failure stops the build before any other file changes.
- **AC-3** (settings strip): `sync.sh` writes the repo `settings.json` with `autoMode` deleted (as today). It also drops every array item that is a string containing a name, and every object key containing a name, at any depth. Parent arrays and objects left empty stay. The dropped entries go to `~/.claude/private/settings.json` (mode 0600) in the same nesting: arrays keep only the dropped items, objects only the dropped keys. `settings.local.json` gets the same strip into `~/.claude/private/settings.local.json`. The fragments are written only after every AC-4 source check passes, and replaced on every passing sync, so they always match the live files. A name left anywhere else in a stripped result (a string value, a hook command) refuses the sync (AC-4).
- **AC-4** (sync refuses before writing): before copying anything, `sync.sh` checks every source it is about to copy: the live `CLAUDE.md`, both stripped settings files, `agents/`, `rules/`, the three single files. On any hit it prints `<live path>:<line>: names.txt line <N>` for each one (never the name itself, so a session cannot copy it onward) and exits 1. The repo working tree is left byte for byte unchanged.
- **AC-5** (sync final check): after copying, `sync.sh` checks every file `git ls-files -co --exclude-standard` lists in the repo. A hit prints `<path>:<line>: names.txt line <N>` and exits 1 (the copy stays, the commit check of AC-8 still blocks it).
- **AC-6** (install restores settings): after `install.sh` writes the live `settings.json`, it merges `~/.claude/private/settings.json` into it when that file exists, and `~/.claude/private/settings.local.json` into the live `settings.local.json` the same way. Each fragment gets the same `/home/santiago` to `$HOME` swap as `settings.json` (`install.sh` lines 70 to 83). Objects merge key by key, arrays append the items not already present, and a fragment scalar replaces the public one. With no fragment it prints `no private settings fragment, private entries not installed` and goes on, so a public reader's install still works. `--dry-run` prints the merge and writes nothing.
- **AC-7** (install, this repo only): when `names.txt` exists, `install.sh` does two things. It appends each line of `~/.claude/private/gitignore` not already present to this repo's `.git/info/exclude`. It also copies `scripts/private-names.py` to `.git/hooks/pre-commit` and `.git/hooks/commit-msg`, mode 0755, never a symlink: a `wf run` call may edit the tracked checker, and a linked hook would run that edit outside the sandbox at your next commit (a real `wf run` stopped `guard_changed` on `.git/hooks/commit-msg` after `/test` edited the checker). Per hook, checked in this order: a symlink resolving to the checker (the old install) is refreshed; any other symlink is left alone. A regular file byte identical to the checker and executable prints `<hook>: up to date`. A regular file whose line 2 equals the checker's line 2 (an older copy, or an identical one missing its execute bit) is refreshed. Missing is copied. Anything else is left alone and install prints `hook exists, not replaced: <hook>`. Refreshed prints `<hook>: refreshed`, copied prints `<hook>: copied`. Every write removes the old path first (`rm -f`, then copy, then `chmod 0755`), so it can never write through a link into the tracked checker. `--dry-run` prints `would: <hook>: copied` or `would: <hook>: refreshed` and writes nothing. Leaving a hook alone is not an error; install goes on and exits 0. With no `names.txt` it skips this step and says so.
- **AC-8** (commit guard): the `pre-commit` hook checks the staged content of each added, copied, modified or renamed file (`git show :<path>`). The `commit-msg` hook checks the message file. Each staged path name is checked too. A hit prints `<path or message>:<line>: names.txt line <N>` and exits 1, so the commit does not happen. A missing names list also blocks (AC-1).
- **AC-9** (tracked files clean): every file `check` reports is fixed, at least `.gitignore`, `CLAUDE.md`, `HOOKS.md`, `README.md`, `SKILLS.md` and `settings.json` (the client site names may show up in more). Wording rule: each name becomes a generic noun ("a work org", "a client site", "a private tool"), and a rule that needs the real value points to the private file: "the bot reviewed orgs listed in your private `work.md`", "jjstack, source in your private `work.md`". `python3 scripts/private-names.py check` over the whole repo exits 0 on the branch and on the merged `main`.
- **AC-10** (history): `python3 scripts/private-names.py filter-expr <out>` writes one `regex:(?i)<escaped name>==><replacement>` line per name (replacement from the `==>` part, else `***REMOVED***`), longest names first, to a scratch path outside any repo. In a fresh clone holding `main`, the runner branch merged in and every other local branch, `git filter-repo --replace-text <out> --replace-message <out> --force` rewrites every ref. After that, `python3 scripts/private-names.py check-history` exits 0. It scans every blob reachable from any ref, binary included (`filter-repo` leaves binary blobs alone, so a binary hit needs a manual fix), every tree path name, every commit and tag message, every author and committer field, and every ref name. A ref name hit gets the branch renamed before the rewrite. You then delete `github.com/Gartner24/claude-config`, create it again (public, same name) and push `main`. A fresh clone of the new remote passes `check-history` with zero hits.
- **AC-11** (same behavior): with `~/.claude/private/` in place, a fresh `install.sh` gives a live `settings.json` and `settings.local.json` equal to today's as a set. `jq -S` of both, `autoMode` deleted from each (sync already drops it and install never restored it, unchanged), arrays sorted, compares equal. P1 shows the private rules load.
- **AC-12** (self check): `python3 scripts/private-names.py --test` exits 0 and asserts AC-1, AC-3, AC-6 and AC-8 on temp files and a temp git repo, using made up names.

## Decision

**Chosen option**: Option 1: private files under `~/.claude/private/`, one names list, one checker that strips known spots and refuses the rest, then a full history rewrite pushed to a recreated repo.

## Feature design

**Private files** (`~/.claude/private/`, never synced, never in any repo):

| File | Holds | Written by | Read by |
|---|---|---|---|
| `names.txt` | the names list, optional `==>replacement` per line (AC-1) | you | `private-names.py`, `git filter-repo` |
| `work.md` | the name bearing passages of `CLAUDE.md` (AC-2) | you, once (moved from `CLAUDE.md`) | Claude Code, through the import |
| `settings.json`, `settings.local.json` | the entries stripped from the two settings files (AC-3) | `sync.sh` | `install.sh` (AC-6) |
| `gitignore` | the client skill folder lines that leave `.gitignore` | you, once | `install.sh` (AC-7) |

**Checker** `scripts/private-names.py` (Python 3 stdlib, repo owned, like `check-routing.py`):

| Call | Does | Exit |
|---|---|---|
| `check [paths...]` | scans the paths, or every file `git ls-files -co --exclude-standard` lists; skips a file with a NUL byte in its first 8 KiB (binary) | 0 clean, 1 hit or no list |
| `check-staged` | staged blobs of added, copied, modified, renamed files (AC-8) | same |
| `check-msg <file>` | one message file (AC-8) | same |
| `check-history` | blobs and tree paths from `git rev-list --all --objects` (binary included), messages and author fields from `git log --all`, names from `git for-each-ref` (AC-10) | same |
| `filter-expr <out>` | the case insensitive `filter-repo` expressions file (AC-10) | 0, 1 no list |
| `strip-settings <in> <out> <fragment>` | AC-3, then runs `check` on `<out>` | same |
| `merge-settings <settings> <fragment>` | AC-6 | 0, 1 on bad JSON |
| `--test` | AC-12 | 0 pass |
| invoked as `pre-commit` / `commit-msg` | `check-staged` / `check-msg "$1"`, picked by `argv[0]` basename (as `wf.py` acts as `next`) | same |

Every hit line is `<where>:<line>: names.txt line <N>`, naming the list line that matched, never the name itself. A Claude session reading the output cannot copy a name onward into a commit, memory or doc.

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| any check | the names | `~/.claude/private/names.txt` (AC-1) |
| history rewrite | each replacement | the `==>` part of the names line, else `***REMOVED***`, written into the expressions file by `filter-expr` |
| any hit line | which name matched | its line number in `names.txt` |
| sync strip | what counts as a known spot | array string items and object keys in `settings.json` (AC-3); everything else is refused |
| install merge | the private entries | `~/.claude/private/settings.json`, written by the last sync |
| install exclude | private ignore lines | `~/.claude/private/gitignore` |
| new remote | URL and visibility | the current `origin` (`git@github.com:Gartner24/claude-config.git`), public, as today |
| client site names | the strings | you add them to `names.txt` (build plan step 3) |

**Key invariants**:
- No tracked file, commit message, blob or ref name in this repo, or on its GitHub remote after AC-10, contains a listed name (case insensitive).
- A missing or empty names list never passes a check.
- No `wf run` step writes `.git/hooks` or anything under `~/.claude`.
- Nothing in `.git/hooks` resolves to a tracked file, so no `wf run` edit to a tracked file changes what a hook runs.
- Nothing under `~/.claude/private/` is copied by `sync.sh` or written into any repo. `sync.sh` copies named paths only, and none is `private/`.
- The checker never prints a name, only its `names.txt` line number.
- The 75 local commits on `feat/autonomous-runner` are never pushed to the old remote. The next push of this repo is the rewritten `main` to the recreated one.

**Security model**: the threat is accidental publication by you or a Claude session (a sync, a hand edit, a commit message). Deliberate bypass (`--no-verify`, editing the hook) is out of scope: `check-history` before the push of AC-10 is the backstop, and any later leak is fixed with this same procedure. Names in `~/.claude/private/` are local plain text, as `CLAUDE.md` is today. Rewriting cannot recall copies someone already took. With 0 forks and 0 stars that risk is accepted (rationale).

**Configuration required**: `CLAUDE_LIVE_DIR` (optional, tests only): the live folder `sync.sh`, `install.sh` and the checker use instead of `~/.claude`. The four files above. `git filter-repo` (installed, checked 2026-10-12).

**Critical test scenarios**:
- Missing `names.txt`: `check`, `check-staged`, `strip-settings` and `sync.sh` each print the AC-1 line and exit 1. Verifies **AC-1**.
- Settings with a name in a deny path, an allow path and a `skillOverrides` key: the out file has none of them, the fragment has exactly those three, in the same nesting. A name inside a hook command string refuses. Verifies **AC-3**.
- A rule file in a temp live tree containing a name: `sync.sh` against it exits 1, prints `<path>:<line>: <name>`, and `git status --porcelain` of the temp repo is unchanged. Verifies **AC-4**.
- Merge: the public deny list plus a fragment with two private deny paths gives the union. A rerun adds nothing (idempotent). No fragment prints the warning and exits 0. Verifies **AC-6**.
- Install hook copy (AC-7), temp repo through `CLAUDE_LIVE_DIR`: no hook gives two regular 0755 files equal to the checker (`copied`); a rerun prints `up to date`; a symlink to the checker and a file with the checker's line 2 but older content are each replaced by a regular copy (`refreshed`); a hand written hook is untouched (`hook exists, not replaced`); `--dry-run` writes nothing. Verifies **AC-7**.
- Temp git repo with the hooks copied in: staging a file with a name blocks the commit, a message with a name blocks the commit, a clean commit passes, and an upper case variant of a name blocks. Verifies **AC-8**.
- Rewrite in a temp repo with a name in three cases, in a commit message, and inside a longer name: after `filter-expr` plus `filter-repo`, `check-history` exits 0. A planted name in a binary blob, a path name, or a branch name makes it exit 1. Verifies **AC-10**.

## Build plan

Skateboard: each step leaves a working setup; the rewrite is last, after the branch is reviewed.

`wf run` builds the code steps. No `wf` step writes `.git/hooks` or anything under `~/.claude`, and no `wf` step runs `sync.sh` or `install.sh` against the real `~/.claude`. Those steps are yours, on their own scope boxes marked ` · waits on you`.

`sync.sh`, `install.sh` and `private-names.py` read the live folder from `CLAUDE_LIVE_DIR` when it is set, else `~/.claude`. The names list is `$CLAUDE_LIVE_DIR/private/names.txt`. Tests point it at a temp tree, so no test touches the real one.

1. (`wf`) Write `scripts/private-names.py`: `check`, `check-staged`, `check-msg`, `check-history`, `filter-expr`, `strip-settings`, `merge-settings`, the names parser and `--test`, on temp files and made up names. Satisfies **AC-1**, **AC-3**, **AC-6**, **AC-8**, **AC-10**, **AC-12**.
2. (`wf`) `sync.sh`: the source check before copying, `strip-settings` in place of the bare `jq`, the final repo check. `install.sh`: the fragment merge, the exclude lines, the hook copies. Each one is tested only on temp live trees and temp git repos through `CLAUDE_LIVE_DIR`, with the `--dry-run` self checks. Satisfies **AC-3** to **AC-7**.
3. (you) Create `~/.claude/private/`: `names.txt` with the names and shapes from the brief plus the client site names, longest first; `work.md` with the passages moved out of `~/.claude/CLAUDE.md` behind the import line; `gitignore`. Run P1 and stop on a failure. Satisfies **AC-1**, **AC-2**.
4. (`wf`) Reword every file `check` reports, per the AC-9 rule, until `check` exits 0. If the `wf` jail cannot read `names.txt`, `check` exits 1 with the AC-1 line and the call parks. Satisfies **AC-9**.
5. (you) Run `./sync.sh`. It writes the settings fragments under `~/.claude/private/`. It must exit 0, and `check` must still exit 0. Satisfies **AC-3**, **AC-4**, **AC-5**.
6. (you) Run `./install.sh` (fragment merge, exclude lines, hook copies), then the AC-11 compare. Satisfies **AC-6**, **AC-7**, **AC-11**.
7. (`wf`) `/check verify`, then `/test`.
8. (you) Merge `feat/autonomous-runner` into `main` locally, then run migration plan phases 1 and 2. Satisfies **AC-9**, **AC-10**.
9. (you) Migration plan phases 3 to 5: delete and recreate the repo, push `main`, check the new remote. Satisfies **AC-10**.

**AC-7 amendment (2026-10-12), before step 8:**

7a. (you) Swap today's two hook links for plain copies by hand, so a `wf` edit to the checker no longer changes a guarded hook file: `cp --remove-destination scripts/private-names.py .git/hooks/pre-commit`, the same for `commit-msg`. Without this the 7b build stops `guard_changed` again, since spec 0007 hashes `.git/hooks` through the link.
7b. (`wf`) `install.sh`: the copy and refresh rules of AC-7 in place of the `ln -s`. `private-names.py`: the `--test` hook fixtures copy the script instead of linking it, the install assertions cover the AC-7 scenario above in temp repos only (never the real `.git/hooks`), and docstring line 19 says copied. Line 2 stays as it is, since it is how install recognizes an older copy. Tested only through `CLAUDE_LIVE_DIR` temp trees. Satisfies **AC-7**.
7c. (you) Rerun `./install.sh`. Both hooks print `refreshed` (or `up to date`), and `test -L .git/hooks/commit-msg` fails for both. Satisfies **AC-7**.

## Migration plan

**Strategy**: big bang rewrite in a copy. The original clone stays untouched until the new remote checks clean.
**Phases**:
1. Commit everything first (this spec included); `git status` in the original must be clean, since uncommitted work does not reach a clone. Then `git clone --no-local ~/claude-config <scratch>/claude-config-clean` and create a local branch there for every `origin/*` branch (all local branches of the original). Stashes, reflogs and `refs/original` stay behind in the original on purpose.
2. In the copy: `python3 scripts/private-names.py filter-expr <scratch>/expr.txt`, then `git filter-repo --replace-text <scratch>/expr.txt --replace-message <scratch>/expr.txt --force`. Then `python3 scripts/private-names.py check-history`, which must exit 0. A hit in a binary blob, a path or a ref name is fixed by hand in the original (commit, or rename the branch) and the procedure reruns from phase 1.
3. Before deleting, note any GitHub state the delete loses: description, topics, and any secrets, webhooks, branch rules or collaborators. Then you (outward and destructive, never run by a session): `gh repo delete Gartner24/claude-config`, `gh repo create Gartner24/claude-config --public`, then in the copy `git remote add origin git@github.com:Gartner24/claude-config.git` and `git push -u origin main`.
4. `git clone` the new remote to a scratch folder and run `check-history` there. It must exit 0.
5. Swap folders: move the original clone aside, put the clean copy at `~/claude-config`, rerun `install.sh` (the hook links and the exclude lines live in `.git`). Once phase 4 passes, delete the moved original yourself. It still holds the old commits and the `refs/original` backup.
**Rollback**: before phase 3, delete the copy, and nothing changed. After phase 3, the original clone still holds the full history and can be pushed back.
**Risks**: a spelling that is not a case variant (a space for a hyphen, a domain form) missing from `names.txt` (caught by `check-history` only if listed; the brief lists the shapes to cover). Unpushed branches in the original that were not copied (phase 1 copies every branch). GitHub repo settings (description, topics) are not carried over; you set them again on create.

## Consequences

**Positive**:
- No published file or commit names a work org, client, PR bot or private tool.
- One list drives sync, commits and the rewrite, so a new name is one line.
- A reinstall keeps the private deny rules, which today it already would not once they leave the public file.

**Negative / tradeoffs**:
- Public readers lose the jjstack install URL and the bot reviewed repo rule details.
- Every commit ID changes. Commit IDs quoted in specs and briefs (for example "built in b8402dc") stop resolving. Their text stays, but `git show` of the old ID fails.
- A new machine needs `~/.claude/private/` before `sync.sh` or a commit in this repo works.
- The rewrite is irreversible on GitHub once the old repo is deleted.
- A checker fix waits for your next `install.sh` before it guards commits. Changing line 2 of the checker makes install treat the old hooks as hand written; delete them and rerun. Between 7a and 7c your commits run the checker as it was at 7a, before the 7b edit.

**Neutral**:
- Spec 0007's guard hashes git hook files during a `wf run` call. Copying the hooks happens in `install.sh`, outside any call; a copy, unlike a link, does not change when a call edits the checker. Under `wf run` the commit hook needs `~/.claude/private/names.txt` readable; when the sandbox hides it, the commit is blocked and the call parks (fail closed). `/check verify` records which happens; a read only bind, if needed, is a later spec 0007 amendment.
- The repo root `CLAUDE.md` copy carries the import line too. In this repo it loads as project instructions, where an outside import is skipped (P0), so it adds nothing; the user level copy does the loading.
- No git hook exists in this repo today; the commit format check is a Claude Code hook, so the hook links do not collide with it (checked 2026-10-12).
- `AGENTS.md` gains a gotcha and a command line (owned by `/sync`).

## Follow-up

- [x] `/sync`: add `python3 scripts/private-names.py --test` to the `AGENTS.md` commands and a gotcha about `~/.claude/private/`.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
