# 0081. Profiles: named switch sets over one shared core

**Date**: 2026-10-27
**Status**: Proposed
**Paths:** `profiles/**`, `tools/bin/install.sh`, `tools/bin/sync.sh`, `tools/bin/claude-config.py`, `claude-home/hooks/profile-lock.py`, `claude-home/settings.json`, `claude-home/skills/claude-config/SKILL.md`, `claude-home/mods/chip-dash/**`, `.github/CODEOWNERS`, `tests/**`

## What you're agreeing to
- Everything stays one shared core. A profile is a small file in the repo that says which skills fire on their own, which rules load, which hooks run and what its user may edit. Two profiles to start: `engineer` (exactly your setup today) and `creator` (for your partner).
- Install builds `~/.claude` from the core plus the chosen profile, and the repo wins. Before it overwrites anything in `~/.claude`, it lists what would change or be lost, and stops so the change is carried into the repo or you decide.
- `/claude-config profile <name>` switches profiles on one machine (it takes effect in the next chat), and the band shows the active profile.
- In `creator`, Claude can edit only the design and content skills (not `design-gate`) and that person's own custom profiles; a core PR needs your approval on GitHub. Asking a change to a `creator` rule makes a copy, `custom-<name>`, instead.
- `creator` starts as a copy of your skills and rules with the lock on; it asks the same questions as `engineer` until your partner's own configs arrive. The video part and Mac support are separate rows.

## Summary
claude-config becomes shareable. The core (skills, rules, hooks, design pipeline) stays one copy in the repo; a profile is a named set of switches over it. Install builds `~/.claude` from core plus profile and checks first what it would overwrite. A profile that is not the owner's cannot edit the locked core: a hook stops Claude, and GitHub code owners stop a hand edit from merging.

## Requirements

**User stories**:
- As the owner, I want my setup to work exactly as today under the `engineer` profile, so that sharing costs me nothing.
- As a partner who makes videos, I want to install claude-config with the `creator` profile, so that I get the same workflow and quality bar without being able to break the engineering core.
- As anyone, I want to switch profiles on one machine with one command, so that I can work as `creator` when making videos.

**Acceptance criteria**:

### PR A (0081a): profiles and install
- **AC-1** `profiles/<name>/profile.json` holds the fields of the data model below; `profiles/<name>/rules/*.md` holds rules only that profile loads. `profiles/engineer/` and `profiles/creator/` exist. A test validates every profile file: required fields present, `name` equals the folder name, every `rules` entry exists in `claude-home/rules/`, every `skills` value is `on` or `name-only`, `base` names an existing profile or is empty, every `hooks_off` entry is the file name of a script in `claude-home/hooks/` and is never `profile-lock.py`.
- **AC-2** `tools/bin/install.sh --profile <name>` first builds the whole result in a temporary staging folder, then copies it into `~/.claude` only after the AC-5 check, so a failed build never leaves half a profile live. The build: `rules/` gets the core files the profile lists plus `profiles/<name>/rules/*.md` (core rules it does not list are not installed); `rules/ecc/` and `rules-on-demand/` always install whole; `CLAUDE.md` is the core file for every profile and is now always installed (it was copied only when missing); `settings.json` is the core file with `skillOverrides` set from the profile's `skills`, then every hook command whose script file name is in `hooks_off` removed from every event (groups left empty dropped), then the private fragment merged as today (so a private entry may override a profile entry). `settings.local.json` is untouched. Everything else is installed as today. It writes `~/.claude/state/profile.json` atomically (write a temp file, then rename): the active profile file plus a `repo` field, the repo's absolute path. Paths use `$CLAUDE_LIVE_DIR` when set (the self checks). An unknown profile name exits 2 naming the known ones, before anything is written.
- **AC-3** `skillOverrides` moves out of `claude-home/settings.json` into `profiles/engineer/profile.json` `skills`, unchanged. After `install.sh --profile engineer` on today's machine, `claude-config.py drift` prints `drift: none`, live `settings.json` parses to the same JSON as before (compared parsed, not as text), and `CLAUDE.md` and `rules/` are byte for byte what they were before (test on a temp live tree built from today's files; verify step on the real machine). The 20,000 character check of always loaded text runs on the built profile.
- **AC-4** `install.sh` with no `--profile` uses the name in `~/.claude/state/profile.json`, else `engineer`, and says which it used.
- **AC-5** Overwrite check: install compares the staging folder with `~/.claude` over the files it writes (`CLAUDE.md`, `agents/`, `rules/`, `rules-on-demand/`, the copied hooks, `MAP.md`, `settings.json`). `settings.json` is compared only on the keys the repo owns (everything except the keys on `claude-config.py`'s drift ignore list, which Claude Code changes itself: permissions, model, plugins, theme and the like), after the same `$HOME` and private fragment steps install applies, so an install right after an install lists nothing (test: install twice, the second prints no item and exits 0). A live file the build would not write (today moved silently to `backups/rules/<date>/`) is listed as `lost`. Output, one line per item: `overwrite: changed <path> +<added>/-<removed>` or `overwrite: lost <path>`. When any is listed and neither `--accept-overwrite` nor `--dry-run` is given, install writes nothing and exits 3. `/claude-config` reads those lines and, per item, offers to carry it into the repo (owner profile: sync it) or overwrite it, one question per item; run without a person (no question tool), it prints the lines and stops.
- **AC-6** `sync.sh` with an `owner: true` profile: live `skillOverrides` go into the active profile's `skills` (not into `claude-home/settings.json`); a live rule the profile lists from core goes back to `claude-home/rules/`, a rule from the profile's own folder goes back to `profiles/<active>/rules/`. With `owner: false` sync copies nothing at all and prints `sync: <profile> is not an owner profile; changes reach the repo through a PR`, exit 0.
- **AC-7** `claude-config.py profile <name>` (and `/claude-config profile <name>` in the skill) runs the install for that profile, through the AC-5 check, then prints `profile <name> active: open a new chat`. `claude-config.py profile` with no name lists every profile with its description and marks the active one.
- **AC-8** `claude-config.py profile update` stops with exit 1 when the repo has uncommitted changes (naming them), else runs `git pull --ff-only` in the repo, then installs the active profile through the AC-5 check. It never installs another profile. The `/claude-config` skill's `update` action runs it after the downloaded skills step.
- **AC-9** The chip-dash band shows the active profile name read from `state/profile.json` under `$CLAUDE_LIVE_DIR`, else `~/.claude`, and nothing when the file is missing; a mod test covers both.
- **AC-9b** New and changed shell code in this spec uses no GNU only construct (`find -printf`, `readlink -f`, `sed -i` without a suffix, `${x^^}`, `declare -A`, `timeout`); a test greps the files this spec adds or changes and prints each hit (row 119 fixes the existing ones).

### PR B (0081b): the lock and custom profiles
- **AC-10** `claude-home/hooks/profile-lock.py`, PreToolUse on `Edit`, `Write`, `MultiEdit`, `NotebookEdit`, copied, synced and wired in settings like the other core hooks: resolves the target path through links. A target outside the repo and outside `~/.claude` is allowed (the person's own projects). Under `~/.claude`, Claude's own working folders are allowed (`projects/`, which holds memory, plus `plans/` and `todos/`); live copies of core files, `state/` and `private/` are denied; a path that resolves into the repo is judged as a repo path; a path that resolves into a framework folder outside the repo (jjstack, gstack) is denied. Inside the repo: allowed when it matches a pattern in the active profile's `editable` (repo relative, `fnmatch`); otherwise denied with `locked core (profile <name>): ask the owner to change <repo relative path>`. With `owner: true` and `editable: ["**"]` every repo path is allowed.
- **AC-11** With an active profile that has `owner: false`, a write under `profiles/<active>/` is denied with: `<active> is shared. Make the person's own copy now: propose a short name, let them change it, then run claude-config.py profile custom <name> and apply the change there.` Claude does that itself (D14, automatic); the person only confirms or types the name.
- **AC-12** `claude-config.py profile custom <name>` copies the active profile folder to `profiles/custom-<name>/` with `name` set, `base` set to the active profile, `owner: true`, and `editable` = the base's `editable` plus `profiles/custom-<name>/rules/**`, then switches to it (AC-7). A custom profile's `profile.json` changes only through `claude-config.py` commands (the hook denies a direct write to it), so a custom profile cannot widen its own `editable` or change `owner`. `<name>` must match `[a-z0-9-]{1,30}`; an existing `custom-<name>` exits 2 and asks for another name. Made while a custom profile is active, it copies that custom profile and records it as `base`.
- **AC-13** `profiles/creator/profile.json`: `owner: false`; `skills` and `rules` a copy of `engineer`'s; `hooks_off` empty; `editable`: `claude-home/skills/{design,assets,brand-system,nano-banana,video-to-website,voice-dna,content-ops,anti-ai-writing,watch-reels}/**`, `tools/config/patches/{high-end-visual-design,minimalist-ui,industrial-brutalist-ui}.patch`, `profiles/custom-*/**`. `engineer`: `owner: true`, `editable: ["**"]`.
- **AC-14** The hook fails open on bad hook input (invariant 5). A missing or unreadable `state/profile.json` while the hook is wired is the one exception: writes inside the repo and `~/.claude` are denied with `profile state missing: run install`, since the hook only runs when install wired it, and allowing would unlock the core. Its `--test` self check runs in install verify and covers: allowed outside, allowed editable, denied core, denied own shared profile, allowed with owner, link into the repo resolved.

### PR C (0081c): the GitHub lock
- **AC-15** `.github/CODEOWNERS` names the owner for every path outside the `creator` editable list; a test derives the expected owned paths from `profiles/creator/profile.json` and fails when the two disagree. The branch ruleset on `main` blocks direct pushes and requires a code owner review, with the repository admin role as a bypass actor so your own PRs still merge under the self merge checklist (`gh pr merge --admin`). A probe PR by a non-admin account touching `tools/` is blocked; one touching only `claude-home/skills/design/` is not. The ruleset change runs only on your yes. · waits on you

## Decision

**Chosen option**: Option 1: Repo built profiles with an overwrite check (see rationale.md).

Install composes `~/.claude` from the shared core and one profile file; the repo is the source for every profile built file, a pre-install check protects live edits, a PreToolUse hook and GitHub code owners enforce each profile's edit list.

## Feature design

**Data model** (approved by you 2026-10-27):

| Field | Type | Required | Meaning |
|---|---|---|---|
| `name` | text, unique, equals folder name | yes | used in `/claude-config profile <name>` |
| `description` | text | yes | one line in the profile list |
| `owner` | boolean | yes | true: edits change this profile directly; false: a rule edit needs a custom copy (D14) |
| `base` | profile name or empty | yes | the profile a custom profile was copied from |
| `skills` | map skill name to `on` or `name-only` | yes | becomes `skillOverrides` (D1) |
| `rules` | list of core `rules/*.md` file names | yes | always loaded core rules; the profile's own `rules/` folder loads too |
| `hooks_off` | list of hook script names | yes, may be empty | core hooks left out of settings |
| `editable` | list of repo relative patterns | yes | where Claude may write in the repo and `~/.claude` (D13) |

Relationships: a custom profile has exactly one `base` (base 1 to N custom). A machine has exactly one active profile, recorded in `~/.claude/state/profile.json` (the profile file plus `repo`).

**Interface surface**:

| Command | Inputs | Output | Errors |
|---|---|---|---|
| `install.sh [--profile <name>] [--accept-overwrite] [--dry-run]` | profile name | builds `~/.claude`, writes state | exit 2 unknown profile; exit 3 overwrite list |
| `claude-config.py profile` | none | profile list, active marked | none |
| `claude-config.py profile <name>` | profile name | install, then "open a new chat" | as install |
| `claude-config.py profile custom <name>` | short name | new `profiles/custom-<name>/`, switched | exit 2 bad or taken name |
| `claude-config.py profile update` | none | pull, reinstall active | git pull failure exits 1, nothing installed |
| `profile-lock.py` (hook) | tool input path | allow, or deny with the AC-10/AC-11 text | fails open |

**Value sourcing**:

| Action | Value | Source |
|---|---|---|
| install | which profile | `--profile`, else `state/profile.json` `name`, else `engineer` (AC-4) |
| install | `skillOverrides` | the profile's `skills` |
| install | which core rules load | the profile's `rules` |
| lock hook | active profile, `editable`, `owner` | `~/.claude/state/profile.json` |
| lock hook | repo root for patterns | `state/profile.json` `repo`, written by install |
| custom | new profile name | the person, asked by `/claude-config` |
| band | profile name | `state/profile.json` `name` |
| CODEOWNERS | owner account | the repo owner, `Gartner24` |

**Key invariants**:
- `engineer` reproduces today's live setup exactly (AC-3).
- A base profile with `owner: false` never changes through Claude; its user's rule changes live in `custom-*` profiles.
- Install never overwrites a live change silently (AC-5).
- Profiles never hold private names or keys; `~/.claude/private/` stays per person.

**Security model**: the hook stops Claude in a non owner profile from writing locked paths; it covers file tools, not shell writes, so GitHub code owners are the real lock against hand or shell edits reaching `main`. Your admin bypass keeps your own merges working.

**Critical test scenarios**:
- Happy path: install `engineer` on a copy of today's live tree; no file differs, verifies **AC-3**.
- Switch: `profile creator` then `profile engineer` on a temp tree returns to the first build exactly, verifies **AC-7**.
- Overwrite: a live rule edited after install; the next install lists it as `changed`, writes nothing, exits 3; two installs in a row with no edit list nothing, verifies **AC-5**.
- Lock: as `creator`, a Write to `tools/bin/install.sh` is denied, a Write to `claude-home/skills/design/SKILL.md` is allowed, verifies **AC-10**.
- Custom: as `creator`, a Write to `profiles/creator/rules/x.md` is denied with the custom hint; `profile custom ana` then allows writes to `profiles/custom-ana/`, verifies **AC-11**, **AC-12**.

## Build plan
Skateboard: each PR is usable alone. One branch per PR, `feat/0081a-profiles`, then 0081b, then 0081c (each under about 400 lines).

1. PR A: profile files, validator test, `engineer` from today's `skillOverrides` and rules, satisfies **AC-1**, **AC-3**.
2. PR A: `install.sh --profile`, settings and rules composition, state file, default profile, satisfies **AC-2**, **AC-4**.
3. PR A: the overwrite check and the `/claude-config` panel for it, satisfies **AC-5**.
4. PR A: sync routing, `profile`, `profile update`, band name, satisfies **AC-6** to **AC-9b**.
5. PR B: `profile-lock.py` with its self check and settings entry; `creator` profile; `profile custom`, satisfies **AC-10** to **AC-14**.
6. PR C: CODEOWNERS and the ruleset, after your yes, with the probe PRs, satisfies **AC-15**.

## Consequences
**Positive**: two people share one repo without overwriting each other; a new person picks a profile instead of copying your setup.

**Negative / tradeoffs**:
- Editing `~/.claude` directly no longer sticks on its own: install stops on it (AC-5), and you carry it into the repo with sync.
- The lock hook covers file tools only; shell writes in a non owner profile are caught at the PR, not before.
- A missing state file locks the core (AC-14), an exception to invariant 5 (hooks fail open); `docs/architecture.md` says so.
- Linked skills edit the repo directly, so the overwrite check cannot see them; "repo wins" there is as today.
- Your core PRs need the admin bypass to merge once code owner review is required.

**Neutral**: invariant 1 in `docs/architecture.md` gains "profile built files: repo wins"; `skillOverrides` moves into the profile file.

## Follow-up
- [ ] When your partner's configs arrive (D5, D6): adapt them into `creator` (fewer questions, the video skills) as an amendment.
- [ ] Row 119 (Mac support) covers the new scripts too; keep them Python stdlib and POSIX shell.

## Rationale
Options, context and reasoning: [rationale.md](rationale.md). Your answers: [brief](../../briefs/profiles.md).
