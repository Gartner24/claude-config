# 0013 rationale

## Context

The repo is public (`github.com/Gartner24/claude-config`, 0 forks, 0 stars, checked 2026-10-12). It mirrors `~/.claude` through `sync.sh`, and the mirrored text names things that belong to your work and clients. The names sit in several places:

- the bot reviewed org rule in `CLAUDE.md`: two work orgs and the team PR bot
- the jjstack source org in `README.md` and `SKILLS.md`, and the client tool names in `HOOKS.md` and `SKILLS.md`
- the client skill folders in `.gitignore`
- a client skill in `settings.json` `skillOverrides`
- three private tool paths in the `settings.json` deny rules

`origin/main` also names the orgs in `NOTICE.md`. Old commits carry names in 32 commits' contents and 11 commit messages. A filter-branch rewrite on 2026-10-12 cleaned only unpushed docs commits, and its `refs/original` backup still holds the old ones.

Two forces pull against each other. The live setup needs these names to work: the review rule must know which orgs are bot reviewed, and the deny rules must guard the private tool files. Meanwhile `install.sh` overwrites the live `settings.json` from the repo copy. So a public file with the entries simply removed would, on the next install, quietly drop the deny rules that protect secrets.

Removing names from current files does not unpublish them. Any commit already pushed stays readable by its ID, even after a force push, until GitHub collects it. The merge of the runner branch to `main` waits on this, because that merge plus a push would publish 75 more commits.

The probe of 2026-10-12 (verify.md P0) showed that `claude -p` skips an `@import` from a project `CLAUDE.md` to a file outside the project, while an import inside the project loads. So the private text has to be imported from your user level `~/.claude/CLAUDE.md`, never from a repo's `CLAUDE.md`.

## Options considered

### Option 1: private files plus an import, strip known spots and refuse the rest, full rewrite

Name bearing text moves to `~/.claude/private/work.md`, which the live `CLAUDE.md` imports. The private settings entries are stripped by `sync.sh` into a fragment that `install.sh` merges back. One names list drives a checker used by `sync.sh`, two git hooks and the history scan. History is rewritten with `git filter-repo` and pushed to a recreated repo.

**Pros**:
- Nothing private ever enters the repo tree, so there is nothing to undo on the way back.
- One list, one checker, four callers.
- Deleting the repo is the only way old commit IDs stop resolving, and with 0 forks it costs nothing.

**Cons**:
- One import line becomes load bearing. If it breaks, the private rules stop loading quietly (P1 guards the setup, not every future upgrade).
- Commit IDs quoted in docs stop resolving.
- A fresh machine needs the private folder before sync or commits work.

### Option 2: placeholder swap in sync and install

Names stay in the live files. `sync.sh` swaps each name for a placeholder through a mapping file, and `install.sh` swaps them back.

**Pros**:
- The live setup does not change at all.

**Cons**:
- Two transforms must stay exact inverses. A placeholder that also appears in normal text gets "restored" into a name.
- The public docs read as placeholder soup.

### Option 3: strip and keep going, no refusal

`sync.sh` replaces every name anywhere and never blocks.

**Pros**:
- Sync never stops.

**Cons**:
- A name inside a sentence becomes a silent nonsense edit. No signal ever reaches you that a new file started carrying names.

### Option 4: clean current files only, keep history

The same file changes, without the rewrite.

**Pros**:
- Nothing destructive. Commit IDs stay.

**Cons**:
- Every name stays one click away in the history, which is the exposure this feature exists to end.

## Rationale

You picked each part on 2026-10-12: the imported private file, strip the known spots and refuse the rest, rewrite and recreate, merge a private fragment, a commit hook too, refuse when the list is missing, and replacements from the list. Option 1 is the only combination where the repo never holds a name, even for a moment. The import is a documented Claude Code feature and P1 checks it on your real setup before anything else changes.

Stripping only `settings.json` entries works because they are list items and keys: dropping one never breaks a sentence, and the fragment lets `install.sh` put back exactly what was dropped. Anywhere else a name sits inside prose, and the right fix there is a human rewording, so the checker refuses rather than guesses.

A force push leaves old commits reachable by ID. Deleting and recreating the repo is the complete fix, and with no forks, stars or watchers nothing is lost but the repo settings. Rewriting in a fresh clone keeps the original as the rollback until the new remote checks clean.

Settled by me while writing (RECOMMEND items):
- **Checker in Python, not jq plus grep.** A nested settings walk, a fragment in the same shape, and staged blob reads are clumsy in shell; the repo already runs stdlib Python scripts. The runner up is a jq walk in `sync.sh` plus a shell hook: fewer files, but two languages for one rule.
- **The hooks are links to the checker, dispatched by name.** This mirrors `wf.py` acting as `next`. The runner up, two small shell wrappers, means two more files.
- **Substring, case insensitive matching.** The names are distinctive, and a case variant is the likeliest miss. The runner up is word boundary matching, which would miss `<name>-website` style folders.
- **Push only `main` to the new remote.** The runner branch is merged. The other local branches are rewritten too (so the working clone is clean) but stay local. The runner up is pushing every branch, which would publish stale work.
- **Install without the private folder warns, it does not refuse.** `install.sh` also serves public readers, who have no private folder. Only the leak paths (sync, commit) fail closed.
