# 0048. Organize claude-config and ~/.claude, and keep them in sync

**Date**: 2026-10-15
**Status**: In Progress
**Paths:** `README.md`, `AGENTS.md`, `CLAUDE.md`, `LICENSE`, `claude-home/**`, `bin/**`, `config/**`, `scripts/**`, `runner/finish.py`, `runner/run.py`, `runner/e2e/run.py`, `runner/tests/**`
**Amended**: 2026-10-15, after the research review ([docs/research/organize-and-sync-review-2026-10-15.md](../../research/organize-and-sync-review-2026-10-15.md)): edited skills are a pin plus a patch, nothing untraceable or unlicensed enters the public repo, AGENTS.md shrinks under 200 lines.
**Amends**: [0035](../0035-readable-layout/index.md) (AC-3 repo shape: `live/` becomes `claude-home/`, and the top level holds only four files plus folders) and [0003](../0003-scope-contract/index.md) as carried in `rules/scope-contract.md` (the live step shapes: `./install.sh` becomes `bin/install.sh`, and the `cp` shape drops a leading `claude-home/` instead of `live/`).

## What you're agreeing to
- The repo gets a cleaner shape: four files at the top, everything else in folders, and `live/` is renamed `claude-home/` (still a mirror of `~/.claude`).
- One file lists every skill, plugin and framework you downloaded, with where it came from, its license, the exact version, and how to install it again. Skills whose license forbids publishing, and packshot (author unknown), are only named there, never copied into the public repo; packshot, the three design skills with no known source, and your private ones get a private backup copy outside the repo.
- Your edits to a downloaded skill are kept as a small patch on top of the exact upstream version. An update puts your patch on the new version by itself and stops only when your edit and upstream's change collide.
- A new `/claude-config` skill syncs both ways, shows drift, and asks you yes or no per skill before any update. It never changes a working skill on its own. A weekly line at session start reminds you to check for updates.
- Every doc is rewritten for one reader each, regrouped into 5 task guides that each say what kind of guide they are, with a table proving every command, fact and decision from the old docs landed somewhere. AGENTS.md keeps only the rules an AI would not guess, under 200 lines.
- Nothing is deleted and no skill stops working: backups first, one move per step, a check and an undo after each.

## Summary
claude-config has drifted from `~/.claude`: about 180 downloaded skills, 27 commands, 15 hooks and the live settings are not in the repo, and most downloaded skills have no recorded source, so they cannot be updated or restored. This spec renames the install mirror to `claude-home/`, tidies the top level, adds one manifest (a list of where each downloaded thing came from and under which license), keeps your edits to downloaded skills as patches, and adds a `/claude-config` skill that syncs, checks drift and updates each skill after your yes, carrying your patch forward. The docs are rewritten with a mapping table so nothing in them is lost.

## Terms used below
- **Manifest**: `config/manifest.json`, one JSON file listing every downloaded skill, plugin and framework.
- **Pinned version**: the exact upstream commit (or package version) the installed copy came from.
- **Base hash**: a hash of the skill folder exactly as upstream shipped it at the pinned version. If the installed folder hashes differently, you edited it.
- **Patch**: the difference between upstream at the pinned version and your installed copy of an edited skill, stored as `config/patches/<name>.patch` (or `~/.claude/private/patches/<name>.patch` when the skill may not be published).
- **Unpinned**: a skill whose source is known but no upstream commit matches the installed copy, so it is unclear which parts are your edits and which are an older upstream version.
- **Cite only**: a manifest entry with `publish: false`. The repo names its source, license and install command, and never holds its files or a patch of them (a patch, if any, lives only in the private store).
- **Drift**: a skill, rule, hook, command, agent or setting that exists or differs in one place (`claude-home/` or `~/.claude`) but not the other.
- **Three way merge**: `git merge-file` over the base (upstream at the pinned version), yours (the installed copy) and theirs (upstream now), which keeps your edits and takes upstream's, and marks a conflict only where both changed the same lines.

## Requirements

**User stories**:
- As the owner of this setup, I want the repo to name or hold every skill I use, so that a new machine gets the same setup and nothing is lost.
- As the owner, I want updates to carry my edits to a downloaded skill forward and stop only on a real collision, so that updates never undo my edits and cost me no review when nothing collides.
- As the owner of a public repo, I want third party files published only where their license allows it, so that the repo never republishes something I have no right to.
- As a reader (you or an AI), I want a top level and docs I can read in minutes, so that I find any fact without searching.

**Acceptance criteria**:
- **AC-1** (repo shape): the repo top holds only `README.md`, `AGENTS.md`, `CLAUDE.md`, `LICENSE`, plus the folders `bin/`, `config/`, `claude-home/`, `runner/`, `scripts/`, `docs/`, `.claude/`, and `.gitignore`. `install.sh` and `sync.sh` live in `bin/`; `mcp-config.json` and `test-preferences.json` in `config/`; `NOTICE.md` in `docs/`. The empty top level `hooks/` is gone. A test lists the top level and fails on any other entry.
- **AC-2** (claude-home): `live/` is renamed `claude-home/` with every file at the same relative path, still mirroring `~/.claude` path for path. `claude-home/skills/` holds your own skills only; edited downloaded skills are patches (AC-7), never full copies.
- **AC-3** (every reference follows): open boxes and feature rows in `docs/scope/` that name `./install.sh` or `live/` are rewritten to the new paths. No file outside `docs/specs/`, `docs/reviews/` and `docs/briefs/` (and the temporary `live` link itself, AC-15) names `live/`, `./install.sh`, `./sync.sh`, the old top level `mcp-config.json` or `test-preferences.json` paths. This covers at least `runner/finish.py`, `runner/run.py`, `runner/e2e/run.py`, the runner tests, `scripts/private-names.py`, `scripts/gen-agent-index.py`, `scripts/check-routing.py`, `scripts/asciify.py`, `claude-home/settings.json`, `claude-home/rules/scope-contract.md` and `claude-home/skills/review-stack/SKILL.md`. A test greps the repo for the old paths and fails on any hit outside those three doc folders.
- **AC-4** (live step shape): `rules/scope-contract.md` names `bin/install.sh` as the install shape and says the `cp` shape drops a leading `claude-home/`. The runner accepts exactly those shapes and refuses `./install.sh` and `cp live/...` (no ticked or open box uses them today). Runner tests cover both the accepted and the refused shapes.
- **AC-5** (manifest): `config/manifest.json` holds one entry per downloaded skill, plugin and framework found in `~/.claude` (skills, commands, hooks, agents, plugins). Each entry has `name`, `kind` (`skill`, `command`, `hook`, `agent`, `plugin`, `framework`), `status` (`downloaded`, `edited`, `unpinned`, `source-unknown`), `source` (repo or package), `path` inside the source, `pinned` (commit or version), `base_hash`, `license` (SPDX id, `custom`, `none` or `unknown`), `publish` (true or false, AC-6), `patch` (path of its patch file, only when `edited`), `description` (the first sentence of the `SKILL.md` front matter `description`, captured at build and on every update), `fetch` (`git` when `source` is a git repo, else `manual`: pip, npm packages and plugins), and `install` (the exact command that reinstalls it). ECC skills are individual entries (ECC has no local checkout to own them). Frameworks (gstack, jjstack, get-shit-done, vendor-jsm-skills) and the skills they install are framework entries plus a `framework` field on each skill they own, not one entry per linked skill. Each `frameworks` entry also has `dir`, its checkout folder; a skill is framework owned when its link (or the real folder) resolves inside a framework's `dir`. ECC commands and get-shit-done hooks map to their framework entry; any other command, hook or agent with no traceable source gets a `source-unknown` entry and goes to the private store like a skill (AC-6). Own skills are not in the manifest; anything in `claude-home/skills/` without a manifest entry is yours. It is read and written with the Python standard library only.
- **AC-6** (sources, pins and publishing): sources come from `~/.agents/.skill-lock.json`, the framework checkouts, and the traced groups in [docs/briefs/untraced-skills.md](../../briefs/untraced-skills.md) (attended research, 2026-10-15); the build does no search of its own. For each traced skill with `fetch: git`, the build clones its source once (`git clone --filter=blob:none`) and walks `git log --follow -- <path>`, newest first, at most 200 commits, for a commit whose folder hash equals the installed folder's hash: a match sets `pinned` and `base_hash` and status `downloaded`; no match sets status `unpinned` with `pinned` and `base_hash` null. A `fetch: manual` entry records its installed version as `pinned` (`pip show`, the package or plugin version file) and its status from that. The folder hash always ignores `.git/`, `__pycache__/`, `node_modules/` and `.plugin-version`. `license` and `publish` come from the brief: `publish: false` for the 14 Figma skills, transitions-dev, transitions-polish and packshot; true for MIT and Apache-2.0 sources, three.js included. Nothing untraceable and nothing with `publish: false` is ever copied into the repo. packshot (no source) gets a `source-unknown` entry with `install` null and a backup copy in `~/.claude/private/skills/packshot/`. `docs/NOTICE.md` has one block per source that has a public patch: its copyright line, SPDX id and full license text (CloudAI-X with the MIT text for the three.js skills; for Apache-2.0 sources, their NOTICE text too). It lists under "not redistributed" every cite only entry and every entry with `license: unknown` or `none`. Each patch of an Apache-2.0 source opens with a header line naming the files it changes. `license` for a source not in the brief is read from its LICENSE file at `pinned` by matching the MIT and Apache-2.0 texts, else `unknown`. The brief's "copy the real files" notes for gstack and iOS skills are superseded by AC-2 and AC-7: only patches enter the repo. A check lists every `~/.claude/skills` entry and fails if any is neither in the manifest, nor in `claude-home/skills/`, nor framework owned, nor copied to `~/.claude/private/skills/` (AC-8). `~/.agents/.skill-lock.json` is read as an input, never duplicated or rewritten.
- **AC-7** (edited is pin plus patch): an entry whose installed folder hash differs from its `base_hash` is `edited`. Its patch is `git diff --no-index --binary` of upstream at `pinned` against the installed folder, run from a temp folder with relative `a/` and `b/` names (exit 1 means the folders differ and is success), written to `config/patches/<name>.patch` when `publish` is true and to `~/.claude/private/patches/<name>.patch` when false; `patch` names that path. The installer never overwrites an installed `edited` or `unpinned` folder. When one is missing (a new machine), it runs `git fetch --depth 1 <source> <pinned>` into a temp repo, copies `path`, applies the patch with `git apply`, and refuses with a message if the patch does not apply; `install` is used only for `downloaded` entries and `fetch: manual` entries. The three local overrides `scripts/skills-audit.sh` guards (industrial-brutalist-ui, minimalist-ui, high-end-visual-design) are not in `~/.agents/.skill-lock.json` or the brief (checked 2026-10-15), so they are `source-unknown` entries with a copy in `~/.claude/private/skills/`, and the guard keeps them as a hash only list until a source is found. `skills-audit.sh`'s hashing and override guard are folded into `bin/claude-config.py` (one hash routine, one list), and `skills-audit.sh` is removed only after its checks pass inside the new tool.
- **AC-8** (no private leak): every file copied into `claude-home/` by this build passes `scripts/private-names.py`. A skill that fails is not copied into the repo: it is copied to `~/.claude/private/skills/<name>/` (never in any repo), listed in the build report, and stays installed in `~/.claude` untouched. Every patch bound for `config/patches/` also passes `scripts/private-names.py`; a patch that fails goes to `~/.claude/private/patches/` and the entry's `patch` points there. The manifest gets no entry for it (the manifest is public); the drift check reads `~/.claude/private/skills/` as the source for those names. (Your answer 2026-10-15.)
- **AC-9** (`/claude-config` skill): `claude-home/skills/claude-config/SKILL.md` drives `bin/claude-config.py` with four commands: `sync` (live to repo for copied kinds, what `sync.sh` does), `install` (repo to live, what `install.sh` does), `drift` (lists every item in one place and not the other, or different, grouped by kind, and exits 1 when any exist), and `update`. `drift` compares `settings.json` only after the same transform `sync.sh` applies (the `$HOME` swap and the private fragment strip), ignores the keys listed in `config/drift-ignore.json` (keys hooks and the runner write), and reports it under kind `setting`. It never changes a skill in `~/.claude` or `claude-home/` without your yes on that skill. The drift check runs only inside this skill, never at session start.
- **AC-10** (upstream update, patch carried forward): the tool itself never asks. `update --plan` fetches each `fetch: git` entry's source and prints every entry whose upstream folder hash differs from `base_hash` (for `unpinned`, from the installed hash), with its changed files and line counts; `fetch: manual` entries are listed as "update by hand, not checked" and `--apply` refuses them. The `/claude-config` skill asks you yes or no per entry, then calls `update --apply <entry>` for each yes. The base is fetched again by commit (`git fetch --depth 1 <source> <pinned>`); if its hash is not `base_hash`, the entry is reported and nothing changes. A `downloaded` entry is replaced with upstream now. An `edited` entry is merged file by file with `git merge-file -p` over base, your installed copy and upstream now (exit 0 clean, above 0 conflict, probe P1); a file only you added is kept, a file only upstream added is taken, a file upstream deleted is deleted when you did not edit it and is a conflict when you did, and a binary file both sides changed is a conflict. When every file merges clean, the result is installed, `pinned` and `base_hash` move to upstream now, and the patch is regenerated against it. When any file conflicts, nothing is installed and nothing in the manifest moves: the merged files with conflict markers go to `~/.claude/state/claude-config-conflicts/<entry>/`, and the skill shows them to you. After you fix them, `update --apply <entry> --resolved` refuses while any `<<<<<<<` marker remains, else installs that folder, moves `pinned` and `base_hash`, regenerates the patch and removes the conflicts folder. An `unpinned` entry shows the whole diff between your installed copy and upstream now; yes replaces it and makes it `downloaded`, no leaves it `unpinned`. `update` with no network or a source that is gone reports that entry and changes nothing for it.
- **AC-11** (weekly reminder): `update --plan` writes the time of its last run that reached every `fetch: git` source to `~/.claude/state/claude-config.json` (`last_upstream_check`). A SessionStart hook in `claude-home/hooks/` prints one line, "claude-config: upstream not checked for N days, run /claude-config update", when 7 or more days passed or the file is missing, and prints nothing otherwise. The hook never fetches and never runs the drift check. Its registration lives in `claude-home/settings.json`, and a test confirms `sync` keeps it.
- **AC-12** (docs rewrite, nothing lost): before any doc is changed, every command, fact and decision in the old `README.md`, `AGENTS.md`, `docs/architecture.md` and the 7 guides is listed, one row each, in `docs/specs/0048-organize-and-sync/docs-map.md` with its old file and line and the new file and heading it lands in. No row may say nowhere; a row that is dropped on purpose says why and is shown to you before the build ends. `README.md` is written for you, `AGENTS.md` for an AI, each opening with who it is for. `AGENTS.md` holds only rules an AI would not guess from the code (no repository overview) and stays under 200 lines; a test counts its lines. Facts cut from it land in `README.md`, a guide or `docs/architecture.md`, as the map says.
- **AC-13** (5 task guides): `docs/guides/` holds exactly `SETUP.md` (install, restore on a new machine, MCP, plugins), `DAILY-USE.md` (the workflow chain and `wf`), `SKILLS.md` (generated from the manifest and `claude-home/skills/`, plus routing), `HOOKS.md` and `DESIGN-PIPELINE.md`. `SKILLS-EVALUATION.md` moves to `docs/research/`. Each guide's second line states its type, one of `Type: tutorial`, `Type: how to`, `Type: reference`, `Type: explanation`, and a guide mixes no two types in one section. `SKILLS.md` is generated by `bin/claude-config.py docs` from the manifest's `description` fields and the front matter of `claude-home/skills/*/SKILL.md` only (no read of `~/.claude`), and a test fails when the committed file differs from a fresh run. Every relative markdown link in repo owned markdown resolves, and `scripts/asciify.py --check` passes on every rewritten file.
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
      "license": "MIT", "publish": true, "patch": null,
      "install": "npx skills add tsenart/council-skill", "framework": null
    },
    "minimalist-ui": {
      "kind": "skill", "status": "edited", "...": "...",
      "patch": "config/patches/minimalist-ui.patch"
    }
  }
}
```
Required on every entry: `kind`, `status`, `license`, `publish`. `install` is null only for `source-unknown`. `source`, `path` are null only when `status` is `source-unknown`; `pinned`, `base_hash` also null when `unpinned`. `patch` is set exactly when `status` is `edited`. `framework` names a key in `frameworks` or is null.

**State transitions** (entry `status`): `downloaded -> edited` (installed hash differs from `base_hash`, found by `drift` or `sync`, which then writes the patch); `unpinned -> downloaded` (you said yes to an update); `source-unknown -> downloaded`, `edited` or `unpinned` (a source is found later and recorded in the brief); `edited -> downloaded` when the installed copy equals upstream after an update (the patch file is removed). A conflicted update changes no status.

**Commands** (`bin/claude-config.py`, called by the `/claude-config` skill):
| Command | Reads | Writes | Exit |
|---|---|---|---|
| `sync` | `~/.claude` copied kinds | `claude-home/` | 0, 1 on a copy error |
| `install` (`--dry-run`) | `claude-home/`, manifest | `~/.claude` links and copies | 0, 1 on a refusal |
| `drift` | both trees, manifest | nothing | 0 none, 1 drift found |
| `update --plan` | manifest, upstream sources | nothing | 0 |
| `update --apply <entry>` | manifest, upstream source, patch | installed copy, patch, manifest, state file, or the conflicts folder | 0 installed, 1 failed, 2 conflict |
| `docs` | manifest, `claude-home/skills/` | `docs/guides/SKILLS.md` | 0 |

`bin/install.sh` and `bin/sync.sh` stay as thin entry points (dotfiles and the runner call them) that run the matching command.

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| manifest build | `source`, `path` | `~/.agents/.skill-lock.json` when listed; a framework's own checkout; else the group's source and path in `docs/briefs/untraced-skills.md` |
| manifest build | `pinned` | a framework: `git -C <dir> rev-parse HEAD`; a lock file entry or a traced skill: the newest commit in the history of `path` whose folder hash equals the installed hash, else null (`unpinned`) |
| manifest build | `license`, `publish` | the group's License and "Publish an edited copy" lines in `docs/briefs/untraced-skills.md`; the lock file entries and frameworks: the source repo's LICENSE file read at `pinned` (`unknown` with `publish: false` when it has none) |
| manifest build | `install` | the lock file's installer (`npx skills add <source>`), the framework's documented installer, the brief's install line (graphify, Chrome DevTools), `claude plugin install <name>` for plugins, else `npx skills add <owner>/<repo>` with the skill's path |
| manifest build, update | `base_hash` | sha256 over the sorted file paths and contents of the upstream folder at `pinned` (same routine as `skills-audit.sh hash_all`, extended to the whole folder) |
| drift, install | `status: edited` | installed folder hash compared to `base_hash` |
| sync, update | patch | `git diff --no-index --binary` of upstream at `pinned` against the installed folder; its location from `publish` |
| update | which entries | `update --plan` lists entries whose upstream moved; your yes or no per entry in the `/claude-config` skill |
| update | merged files | `git merge-file -p` over base, installed copy and upstream now, per file (probe P1) |
| drift | settings ignore list | `config/drift-ignore.json` |
| install | source for a gone upstream | none: an installed copy is left as is, and a missing one is reported (restore it from the step 0 backup or the private store) |
| reminder | days since check | `~/.claude/state/claude-config.json` `last_upstream_check`, written only by a completed `update` |
| reminder | threshold | 7 days (your answer, brief) |
| docs | skill list and routing | manifest plus each `SKILL.md` front matter `description` |

**Key invariants**:
- No command changes a skill without a yes for that change; the reorganization itself only moves files.
- An installed `edited` or `unpinned` skill is never overwritten; a missing `edited` one is rebuilt from upstream at `pinned` plus its patch.
- Nothing under `~/.claude/private/`, nothing that fails `private-names.py`, and no file or patch of a `publish: false` or `source-unknown` entry enters the repo.
- Every `~/.claude/skills` entry is accounted for: framework owned, in the manifest, in `claude-home/skills/`, or in `~/.claude/private/skills/`.

**Security model**: local only. `update` fetches public sources over https with `git`; it never runs code from a fetched source (no install scripts) until you confirm the `install` command for that entry.

**Critical test scenarios**:
- Happy path: a fixture `~/.claude` with one own, one downloaded, one edited, one unpinned, one cite only and one untraceable skill produces the expected manifest, one patch in `config/patches/`, a private copy only for the untraceable one, nothing of the cite only one in the repo, and `drift` exits 0, verifies **AC-5**, **AC-6**, **AC-7**, **AC-9**.
- Restore: removing the edited fixture skill and running `install` rebuilds it from the fixture upstream at `pinned` plus the patch, hash equal to before, verifies **AC-7**.
- Update clean: a fixture upstream that changed lines your patch did not touch installs, moves `pinned` and `base_hash`, and keeps your edit in the regenerated patch, verifies **AC-10**.
- Conflict and no network: an upstream change to the lines you edited exits 2, writes the conflicts folder, and leaves the installed copy and manifest byte for byte unchanged; an unreachable source changes nothing, verifies **AC-10**.
- Publish: a `publish: false` edited fixture writes its patch only under the private patches folder, verifies **AC-6**, **AC-7**.
- Docs: `AGENTS.md` over 200 lines and a guide without a type line both fail their tests, verifies **AC-12**, **AC-13**.
- Reminder: state file 8 days old prints the line, 6 days old prints nothing, missing prints the line, verifies **AC-11**.
- Layout: top level listing and old path grep, verifies **AC-1**, **AC-3**; live step shape accept and refuse, verifies **AC-4**.
- Private: a skill containing a private name is not copied, verifies **AC-8**.

## Probes
Both ran and passed on 2026-10-15 before the amendment was accepted (commands and output in [verify.md](verify.md)). The build runs them again first and stops if either fails:
- **P1** three way merge: `git merge-file -p mine base theirs` exits 0 and keeps both edits when they touch different lines, and exits 1 with conflict markers when they touch the same line.
- **P2** fetch by commit: `git fetch --depth 1 https://github.com/greensock/gsap-skills.git <sha>` into an empty repo succeeds, and `skills/gsap-core/SKILL.md` at that commit has the same sha256 as the installed `~/.claude/skills/gsap-core/SKILL.md`.

## Build plan
Skateboard: each slice is usable alone, the next grows the same tool.
1. Repo shape on the feature branch: `git mv live claude-home`, scripts to `bin/`, configs to `config/`, `NOTICE.md` to `docs/`, remove top `hooks/`, add the `live -> claude-home` link, update every path reference, runner live step shapes and `rules/scope-contract.md`; layout and old path tests. Satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**, **AC-16**.
2. `bin/claude-config.py` with `sync`, `install`, `drift`, folding in `skills-audit.sh` hashing and the override guard; `bin/install.sh` and `bin/sync.sh` call it; the skill file. Satisfies **AC-7** (guard), **AC-9**.
3. Manifest: build it from the lock file, framework checkouts and the traced brief; pin by history walk, license and publish from the brief, patches for edited skills, packshot and private names to the private store, `docs/NOTICE.md`, the accounting check. Satisfies **AC-5**, **AC-6**, **AC-7**, **AC-8**.
4. `update --plan` and `--apply` with the patch carried forward and the conflicts folder, the state file and the SessionStart reminder hook. Satisfies **AC-10**, **AC-11**.
5. Docs: `docs-map.md` first, then the README, a short `AGENTS.md`, `docs/architecture.md` and the 5 typed guides, `docs` command for `SKILLS.md`, link, ASCII, line count and type line checks. Satisfies **AC-12**, **AC-13**.
6. `migrate.md` and the live steps, each its own box, waiting on you (they write `~/.claude`). Satisfies **AC-14**, **AC-15**.

## Migration plan
**Strategy**: in place rename with a temporary compatibility link, then a step by step live cut over.
**Phases**:
1. Repo changes land on the feature branch (worktree), so links in `~/.claude` keep pointing at the main checkout's `live/` until merge.
2. After merge, the `live -> claude-home` link keeps every skill link working.
3. Live steps from `migrate.md`: backups, `bin/install.sh` (relinks into `claude-home/`, installs the hook), readable count check, remove the compatibility link, `drift` exits 0.
**Rollback**: each step's undo command; full rollback is `git revert` of the merge plus restoring the `tar` and the bundle from step 0.
**Risks**: a skill link left pointing at `live/` after the link is removed (caught by the readable count check before removal); a traced source that is wrong (no commit matches, so the entry is `unpinned` and its first update shows the whole diff before anything changes).

## Consequences
**Positive**:
- A new machine is restored from the repo plus the manifest's install commands, with nothing missing.
- Your edits to downloaded skills survive every update.
- The drift and update questions finally have one command each.

**Negative / tradeoffs**:
- Restoring a new machine needs the network: downloaded and edited skills come from upstream (plus the patch), and cite only skills are only named. If an upstream disappears, the only copies left are the installed one, the step 0 backup and, for packshot and private names, the private store.
- An `unpinned` skill cannot be updated without seeing its whole diff, and saying yes replaces any edit hidden in it.
- Walking upstream history to find each pin costs one fetch per source repo at build time (about 15 repos).
- The rename touches the runner's live step parser, so a stale runner copy refuses new boxes until `bin/install.sh` refreshes it.

**Neutral**:
- `scripts/skills-audit.sh` and `~/.claude/.skills-manifest.json` are retired after their checks move into the new tool.

## Follow-up
- [ ] Missed skill report on 2026-10-18 (plan row 46), then delete `~/claude-migration-20261015/` and `~/claude-config-old` once that report is in and nothing broke (carried from the brief).
- Fewer skills described in every session is its own feature (plan row 55, spec 0050), not part of this build.
- [ ] dotfiles specs that mention `install.sh` and `sync.sh` at the old path are updated by dotfiles' own `/sync`; dotfiles code does not call them.
