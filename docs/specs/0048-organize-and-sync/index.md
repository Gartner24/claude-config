# 0048. Organize claude-config and ~/.claude, and keep them in sync

**Date**: 2026-10-15
**Status**: Proposed
**Paths:** `README.md`, `AGENTS.md`, `CLAUDE.md`, `LICENSE`, `live/**`, `claude-home/**`, `bin/**`, `config/**`, `install.sh`, `sync.sh`, `mcp-config.json`, `test-preferences.json`, `NOTICE.md`, `scripts/**`, `runner/finish.py`, `runner/run.py`, `runner/e2e/run.py`, `runner/tests/**`
**Amends**: [0035](../0035-readable-layout/index.md) (AC-3 repo shape: `live/` becomes `claude-home/`, and the top level holds only four files plus folders) and [0003](../0003-scope-contract/index.md) as carried in `rules/scope-contract.md` (the live step shapes: `./install.sh` becomes `bin/install.sh`, and the `cp` shape drops a leading `claude-home/` instead of `live/`).

## What you're agreeing to
- The repo gets a cleaner shape: four files at the top, everything else in folders, and `live/` is renamed `claude-home/` (still a mirror of `~/.claude`).
- One file lists every skill, plugin and framework you downloaded, with where it came from, the exact version, and how to install it again. Skills nobody can trace are copied in and marked "source unknown", so nothing is ever only a name.
- A new `/claude-config` skill syncs both ways, shows drift, and offers upstream updates one change at a time. It never changes a working skill on its own. A weekly line at session start reminds you to check for updates.
- Every doc is rewritten for one reader each, regrouped into 5 task guides, with a table proving every command, fact and decision from the old docs landed somewhere.
- Nothing is deleted and no skill stops working: backups first, one move per step, a check and an undo after each.

## Summary
claude-config has drifted from `~/.claude`: about 180 downloaded skills, 27 commands, 15 hooks and the live settings are not in the repo, and most downloaded skills have no recorded source, so they cannot be updated or restored. This spec renames the install mirror to `claude-home/`, tidies the top level, adds one manifest (a list of where each downloaded thing came from), and adds a `/claude-config` skill that syncs, checks drift and walks you through upstream updates change by change. The docs are rewritten with a mapping table so nothing in them is lost.

## Terms used below
- **Manifest**: `config/manifest.json`, one JSON file listing every downloaded skill, plugin and framework.
- **Pinned version**: the exact upstream commit (or package version) the installed copy came from.
- **Base hash**: a hash of the skill folder exactly as upstream shipped it at the pinned version. If the installed folder hashes differently, you edited it.
- **Detached**: an edited downloaded skill whose copy lives in `claude-home/skills/`; an update never overwrites it, it only offers changes.
- **Drift**: a skill, rule, hook, command, agent or setting that exists or differs in one place (`claude-home/` or `~/.claude`) but not the other.
- **Three way compare**: compare the base (upstream at the pinned version), yours (the installed copy) and theirs (upstream now), so you see only what upstream changed, on top of your edits.

## Requirements

**User stories**:
- As the owner of this setup, I want the repo to name or hold every skill I use, so that a new machine gets the same setup and nothing is lost.
- As the owner, I want to see each upstream change to a downloaded skill and choose it or keep mine, so that updates never undo my edits.
- As a reader (you or an AI), I want a top level and docs I can read in minutes, so that I find any fact without searching.

**Acceptance criteria**:
- **AC-1** (repo shape): the repo top holds only `README.md`, `AGENTS.md`, `CLAUDE.md`, `LICENSE`, plus the folders `bin/`, `config/`, `claude-home/`, `runner/`, `scripts/`, `docs/`, `.claude/`, and `.gitignore`. `install.sh` and `sync.sh` live in `bin/`; `mcp-config.json` and `test-preferences.json` in `config/`; `NOTICE.md` in `docs/`. The empty top level `hooks/` is gone. A test lists the top level and fails on any other entry.
- **AC-2** (claude-home): `live/` is renamed `claude-home/` with every file at the same relative path, still mirroring `~/.claude` path for path. Own skills and edited copies of downloaded skills both live in `claude-home/skills/`.
- **AC-3** (every reference follows): open boxes and feature rows in `docs/scope/` that name `./install.sh` or `live/` are rewritten to the new paths. No file outside `docs/specs/`, `docs/reviews/` and `docs/briefs/` (and the temporary `live` link itself, AC-15) names `live/`, `./install.sh`, `./sync.sh`, the old top level `mcp-config.json` or `test-preferences.json` paths. This covers at least `runner/finish.py`, `runner/run.py`, `runner/e2e/run.py`, the runner tests, `scripts/private-names.py`, `scripts/gen-agent-index.py`, `scripts/check-routing.py`, `scripts/asciify.py`, `claude-home/settings.json`, `claude-home/rules/scope-contract.md` and `claude-home/skills/review-stack/SKILL.md`. A test greps the repo for the old paths and fails on any hit outside those three doc folders.
- **AC-4** (live step shape): `rules/scope-contract.md` names `bin/install.sh` as the install shape and says the `cp` shape drops a leading `claude-home/`. The runner accepts exactly those shapes and refuses `./install.sh` and `cp live/...` (no ticked or open box uses them today). Runner tests cover both the accepted and the refused shapes.
- **AC-5** (manifest): `config/manifest.json` holds one entry per downloaded skill, plugin and framework found in `~/.claude` (skills, commands, hooks, agents, plugins). Each entry has `name`, `kind` (`skill`, `command`, `hook`, `agent`, `plugin`, `framework`), `status` (`downloaded`, `edited`, `source-unknown`), `source` (repo or package), `path` inside the source, `pinned` (commit or version), `base_hash`, and `install` (the exact command that reinstalls it). Frameworks (gstack, jjstack, get-shit-done, vendor-jsm-skills) and the skills they install are framework entries plus a `framework` field on each skill they own, not one entry per linked skill. Each `frameworks` entry also has `dir`, its checkout folder; a skill is framework owned when its link (or the real folder) resolves inside a framework's `dir`. ECC commands and get-shit-done hooks map to their framework entry; any other command, hook or agent with no traceable source is copied in as `source-unknown`. Own skills are not in the manifest; anything in `claude-home/skills/` without a manifest entry is yours. It is read and written with the Python standard library only.
- **AC-6** (trace, nothing only listed): every real skill folder in `~/.claude/skills` not owned by a framework and with no source in `~/.agents/.skill-lock.json` is traced on GitHub and skills.sh by its exact `SKILL.md` content (sha256 match against `gh search code` candidates; anything short of an exact match is not found). The trace is one attended build step in a chat session, never a `wf` call, and writes `docs/specs/0048-organize-and-sync/trace-report.md` (each skill, where it searched, the result) so it is never rerun blind. Found: a manifest entry with source and pin. Not found: the folder is copied into `claude-home/skills/` and its manifest entry says `source-unknown`. A check lists every `~/.claude/skills` entry and fails if any is neither in the manifest, nor in `claude-home/skills/`, nor framework owned, nor copied to `~/.claude/private/skills/` (AC-8). Copied skills with no license file are listed in `docs/NOTICE.md` as "license unknown", and the repo `LICENSE` does not claim them. `~/.agents/.skill-lock.json` is read as an input, never duplicated or rewritten.
- **AC-7** (edited detection): an entry whose installed folder hash differs from its `base_hash` is `edited`; its folder is copied into `claude-home/skills/` and the installer never overwrites it. The three local overrides `scripts/skills-audit.sh` guards (industrial-brutalist-ui, minimalist-ui, high-end-visual-design) are `edited` entries. `skills-audit.sh`'s hashing and override guard are folded into `bin/claude-config.py` (one hash routine, one list), and `skills-audit.sh` is removed only after its checks pass inside the new tool.
- **AC-8** (no private leak): every file copied into `claude-home/` by this build passes `scripts/private-names.py`. A skill that fails is not copied into the repo: it is copied to `~/.claude/private/skills/<name>/` (never in any repo), listed in the build report, and stays installed in `~/.claude` untouched. The manifest gets no entry for it (the manifest is public); the drift check reads `~/.claude/private/skills/` as the source for those names. (Your answer 2026-10-15.)
- **AC-9** (`/claude-config` skill): `claude-home/skills/claude-config/SKILL.md` drives `bin/claude-config.py` with four commands: `sync` (live to repo for copied kinds, what `sync.sh` does), `install` (repo to live, what `install.sh` does), `drift` (lists every item in one place and not the other, or different, grouped by kind, and exits 1 when any exist), and `update`. `drift` compares `settings.json` only after the same transform `sync.sh` applies (the `$HOME` swap and the private fragment strip), ignores the keys listed in `config/drift-ignore.json` (keys hooks and the runner write), and reports it under kind `setting`. It never changes a skill in `~/.claude` or `claude-home/` without your yes on that change. The drift check runs only inside this skill, never at session start.
- **AC-10** (upstream update, change by change): `update` fetches each manifest entry's source, and for each entry whose upstream moved past `pinned` shows each changed hunk (a hunk is one block of changed lines) as a three way compare against `base_hash`'s content and your copy. The tool itself never asks: `update --plan <entry>` prints the numbered hunks (with any file mode change) and `update --apply <entry> --take 1,3` applies only those; the `/claude-config` skill asks you take or keep for each hunk, then calls `--apply`. The base content is fetched again by commit (`git fetch --depth 1 <source> <pinned>`); if its hash is not `base_hash`, the entry is reported and nothing changes. Each taken hunk is applied with `git merge-file -p` over base, your copy and upstream with only that hunk. A taken hunk is applied to your copy (edited skills) or the installed copy; a kept hunk is skipped. After an entry is done, `pinned` and `base_hash` move to the new upstream version only if you took every hunk; otherwise `pinned` moves and the entry becomes `edited`. A hunk that does not apply cleanly is shown as a conflict and left as keep. `update` with no network or a source that is gone reports that entry and changes nothing for it.
- **AC-11** (weekly reminder): `update` writes the time of its last completed run to `~/.claude/state/claude-config.json` (`last_upstream_check`). A SessionStart hook in `claude-home/hooks/` prints one line, "claude-config: upstream not checked for N days, run /claude-config update", when 7 or more days passed or the file is missing, and prints nothing otherwise. The hook never fetches and never runs the drift check. Its registration lives in `claude-home/settings.json`, and a test confirms `sync` keeps it.
- **AC-12** (docs rewrite, nothing lost): before any doc is changed, every command, fact and decision in the old `README.md`, `AGENTS.md`, `docs/architecture.md` and the 7 guides is listed, one row each, in `docs/specs/0048-organize-and-sync/docs-map.md` with its old file and line and the new file and heading it lands in. No row may say nowhere; a row that is dropped on purpose says why and is shown to you before the build ends. `README.md` is written for you, `AGENTS.md` for an AI, each opening with who it is for.
- **AC-13** (5 task guides): `docs/guides/` holds exactly `SETUP.md` (install, restore on a new machine, MCP, plugins), `DAILY-USE.md` (the workflow chain and `wf`), `SKILLS.md` (generated from the manifest and `claude-home/skills/`, plus routing), `HOOKS.md` and `DESIGN-PIPELINE.md`. `SKILLS-EVALUATION.md` moves to `docs/research/`. `SKILLS.md` is generated by `bin/claude-config.py docs`, and a test fails when the committed file differs from a fresh run. Every relative markdown link in repo owned markdown resolves, and `scripts/asciify.py --check` passes on every rewritten file.
- **AC-14** (migration safety): the live side of the move follows `docs/specs/0048-organize-and-sync/migrate.md`, numbered steps. Step 0 makes backups: a `tar` of `~/.claude` (mode 0600, outside `~/.claude`), `git bundle create <file> --all` of claude-config. Every later step is one move, then its check (`bin/install.sh --dry-run` exits 0, both settings files parse as JSON, `claude -p` with a one word prompt exits 0, every `~/.claude/skills` link resolves, `wf queue` exits 0) and its exact undo command. Preconditions: no `wf` lock held and no `wf-auto` unit running. The first live step after merge is `bin/install.sh`, so the runner copy is fresh before any other live box runs.
- **AC-15** (no skill breaks): after every step, the set of `~/.claude/skills` names whose `SKILL.md` is readable contains every name it held before step 1 (none missing, compared by name, not only by count). While links still point into `live/`, the repo keeps a `live -> claude-home` symlink; it is removed in its own step only after `bin/install.sh` has relinked every skill and the readable count matched.
- **AC-16** (checks still pass): every command in `AGENTS.md` `## Commands` passes with the new paths, and `python3 -m unittest discover -s runner/tests` passes.

## Decision
**Chosen option**: Option 2: rename and restructure in place, a manifest plus copies of edited and untraceable skills, and one `/claude-config` tool built on `skills-audit.sh`.

Reorganize the existing repo in one pass of path moves, add `config/manifest.json` and `bin/claude-config.py`, and carry out the live side through a backed up, step by step migration like 0035.

## Rationale
Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (`config/manifest.json`):
```json
{
  "version": 1,
  "frameworks": {
    "jjstack": {"source": "github:<owner>/jjstack", "pinned": "<commit>", "install": "<command>"}
  },
  "entries": {
    "council": {
      "kind": "skill", "status": "downloaded",
      "source": "github:tsenart/council-skill", "path": "skills/council",
      "pinned": "<commit>", "base_hash": "<sha256 of folder>",
      "install": "npx skills add tsenart/council-skill", "framework": null
    }
  }
}
```
Required on every entry: `kind`, `status`, `install`. `source`, `path`, `pinned`, `base_hash` are null only when `status` is `source-unknown`. `framework` names a key in `frameworks` or is null.

**State transitions** (entry `status`): `downloaded -> edited` (hash differs from `base_hash`, or an update kept a hunk); `source-unknown -> downloaded` or `edited` (a later trace finds it); `edited -> downloaded` only when an update leaves your copy equal to upstream. `edited` always means "your copy's hash differs from `base_hash`", so after an update that kept a hunk, `pinned` and `base_hash` describe the new upstream and your copy still differs from it.

**Commands** (`bin/claude-config.py`, called by the `/claude-config` skill):
| Command | Reads | Writes | Exit |
|---|---|---|---|
| `sync` | `~/.claude` copied kinds | `claude-home/` | 0, 1 on a copy error |
| `install` (`--dry-run`) | `claude-home/`, manifest | `~/.claude` links and copies | 0, 1 on a refusal |
| `drift` | both trees, manifest | nothing | 0 none, 1 drift found |
| `update` | manifest, upstream sources | your copies after each yes, manifest, state file | 0, 1 when any entry failed |
| `docs` | manifest, `claude-home/skills/` | `docs/guides/SKILLS.md` | 0 |

`bin/install.sh` and `bin/sync.sh` stay as thin entry points (dotfiles and the runner call them) that run the matching command.

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| trace | `source`, `path`, `pinned` | `~/.agents/.skill-lock.json` when listed; a framework's own checkout (`git -C <dir> rev-parse HEAD`); else the GitHub or skills.sh match on exact `SKILL.md` content |
| trace | `install` | the lock file's installer (`npx skills add <source>`), the framework's documented installer, or `claude plugin install <name>` for plugins |
| trace, update | `base_hash` | sha256 over the sorted file paths and contents of the upstream folder at `pinned` (same routine as `skills-audit.sh hash_all`, extended to the whole folder) |
| drift, install | `status: edited` | installed folder hash compared to `base_hash` |
| update | hunks | `difflib` over upstream at `pinned` (fetched again by commit) vs upstream now; each taken hunk applied with `git merge-file -p` over base, your copy, and upstream with only that hunk |
| update | take or keep | your answer per hunk in the `/claude-config` skill, passed as `--take` |
| drift | settings ignore list | `config/drift-ignore.json` |
| install | source for a gone upstream | the `claude-home/skills/` copy only |
| reminder | days since check | `~/.claude/state/claude-config.json` `last_upstream_check`, written only by a completed `update` |
| reminder | threshold | 7 days (your answer, brief) |
| docs | skill list and routing | manifest plus each `SKILL.md` front matter `description` |

**Key invariants**:
- No command changes a skill without a yes for that change; the reorganization itself only moves files.
- An `edited` or `source-unknown` skill is installed from `claude-home/skills/`, never from upstream.
- Nothing under `~/.claude/private/` or that fails `private-names.py` enters the repo.
- Every `~/.claude/skills` entry is accounted for: framework owned, in the manifest, in `claude-home/skills/`, or in `~/.claude/private/skills/`.

**Security model**: local only. `update` fetches public sources over https with `git`; it never runs code from a fetched source (no install scripts) until you confirm the `install` command for that entry.

**Critical test scenarios**:
- Happy path: a fixture `~/.claude` with one own, one downloaded, one edited, one untraceable skill produces the expected manifest and copies, and `drift` exits 0, verifies **AC-5**, **AC-6**, **AC-7**, **AC-9**.
- Update: a fixture upstream with two hunks, take one and keep one, leaves the entry `edited` with `pinned` moved and only the taken hunk applied, verifies **AC-10**.
- Conflict and no network: a hunk overlapping your edit is shown as a conflict and kept; an unreachable source changes nothing, verifies **AC-10**.
- Reminder: state file 8 days old prints the line, 6 days old prints nothing, missing prints the line, verifies **AC-11**.
- Layout: top level listing and old path grep, verifies **AC-1**, **AC-3**; live step shape accept and refuse, verifies **AC-4**.
- Private: a skill containing a private name is not copied, verifies **AC-8**.

## Probes
The build runs these first and stops if either fails (results in `verify.md`):
- **P1** trace search: `gh search code --filename SKILL.md "<a unique line from council/SKILL.md>"` returns `tsenart/council-skill` (a skill whose source the lock file already names).
- **P2** fetch by commit: `git fetch --depth 1 https://github.com/tsenart/council-skill.git <pinned sha>` into an empty repo succeeds, and the folder hash at that commit matches.

## Build plan
Skateboard: each slice is usable alone, the next grows the same tool.
1. Repo shape on the feature branch: `git mv live claude-home`, scripts to `bin/`, configs to `config/`, `NOTICE.md` to `docs/`, remove top `hooks/`, add the `live -> claude-home` link, update every path reference, runner live step shapes and `rules/scope-contract.md`; layout and old path tests. Satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**, **AC-16**.
2. `bin/claude-config.py` with `sync`, `install`, `drift`, folding in `skills-audit.sh` hashing and the override guard; `bin/install.sh` and `bin/sync.sh` call it; the skill file. Satisfies **AC-7** (guard), **AC-9**.
3. Manifest: build it from the lock file and framework checkouts, copy in edited skills through the private names check. Satisfies **AC-5**, **AC-7**, **AC-8**.
3b. Trace (attended, in a chat session, never `wf`): trace the rest, write `trace-report.md`, copy in what is not found, private ones to `~/.claude/private/skills/`, NOTICE entries, accounting check. Satisfies **AC-6**, **AC-8**.
4. `update` with per hunk take or keep, the state file and the SessionStart reminder hook. Satisfies **AC-10**, **AC-11**.
5. Docs: `docs-map.md` first, then the README, `AGENTS.md`, `docs/architecture.md` and the 5 guides, `docs` command for `SKILLS.md`, link and ASCII checks. Satisfies **AC-12**, **AC-13**.
6. `migrate.md` and the live steps, each its own box, waiting on you (they write `~/.claude`). Satisfies **AC-14**, **AC-15**.

## Migration plan
**Strategy**: in place rename with a temporary compatibility link, then a step by step live cut over.
**Phases**:
1. Repo changes land on the feature branch (worktree), so links in `~/.claude` keep pointing at the main checkout's `live/` until merge.
2. After merge, the `live -> claude-home` link keeps every skill link working.
3. Live steps from `migrate.md`: backups, `bin/install.sh` (relinks into `claude-home/`, installs the hook), readable count check, remove the compatibility link, `drift` exits 0.
**Rollback**: each step's undo command; full rollback is `git revert` of the merge plus restoring the `tar` and the bundle from step 0.
**Risks**: a skill link left pointing at `live/` after the link is removed (caught by the readable count check before removal); a traced source that is wrong (caught on the first `update`, which shows the whole upstream diff against `base_hash`).

## Consequences
**Positive**:
- A new machine is restored from the repo plus the manifest's install commands, with nothing missing.
- Your edits to downloaded skills survive every update.
- The drift and update questions finally have one command each.

**Negative / tradeoffs**:
- Copying untraceable third party skills into a public repo carries their license question; each copied skill keeps its own license file if it has one, and `docs/NOTICE.md` lists them.
- Tracing about 160 skills by content is slow and some will be wrong or missing; `source-unknown` copies grow the repo.
- The rename touches the runner's live step parser, so a stale runner copy refuses new boxes until `bin/install.sh` refreshes it.

**Neutral**:
- `scripts/skills-audit.sh` and `~/.claude/.skills-manifest.json` are retired after their checks move into the new tool.

## Follow-up
- [ ] Missed skill report on 2026-10-18 (plan row 46), then delete `~/claude-migration-20261015/` and `~/claude-config-old` once that report is in and nothing broke (carried from the brief).
- [ ] dotfiles specs that mention `install.sh` and `sync.sh` at the old path are updated by dotfiles' own `/sync`; dotfiles code does not call them.
