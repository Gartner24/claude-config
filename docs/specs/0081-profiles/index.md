# 0081. Profiles: named switch sets over one shared core

**Date**: 2026-10-27
**Status**: Proposed
**Paths:** `profiles/**`, `tools/bin/install.sh`, `tools/bin/sync.sh`, `tools/bin/claude-config.py`, `claude-home/hooks/profile-lock.py`, `claude-home/settings.json`, `claude-home/skills/claude-config/SKILL.md`, `claude-home/mods/chip-dash/**`, `claude-home/agents/careful-worker.md`, `claude-home/agents/mechanical-worker.md`, `claude-home/skills/instagram-reels-design/**`, `claude-home/skills/lemo-opuscar/**`, `tools/config/manifest.json`, `.github/CODEOWNERS`, `tests/**`
**Amended**: 2026-10-27, PR D (0081d): `creator` built from your partner's setup (D27 to D31)

## What you're agreeing to
- Everything stays one shared core. A profile is a small file in the repo that says which skills fire on their own, which rules load, which hooks run and what its user may edit. Two profiles to start: `engineer` (exactly your setup today) and `creator` (for your partner).
- Install builds `~/.claude` from the core plus the chosen profile, and the repo wins. Before it overwrites anything in `~/.claude`, it lists what would change or be lost, and stops so the change is carried into the repo or you decide.
- `/claude-config profile <name>` switches profiles on one machine (it takes effect in the next chat), and the band shows the active profile.
- In `creator`, Claude can edit only the design and content skills (not `design-gate`) and that person's own custom profiles; a core PR needs your approval on GitHub. Asking a change to a `creator` rule makes a copy, `custom-<name>`, instead.
- `creator` is your partner's setup on your core: your newer skills and guards, his video skills, his model choices, Spanish accents allowed, and `/scope` and `/audit` still running but quiet. His private work (his studio repo, Telegram and boss rules, notes, his two guards) stays on his Mac only. Mac support is a separate row.

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

### PR D (0081d): creator from your partner's setup (amendment, D27 to D31, cross check fixes applied)
Built after PR B merges (it fills the `creator` profile PR B creates). Source material: the partner's zip received 2026-10-27 (not in the repo); every file taken from it passes the private name check before it is staged. AC-3 ("engineer is exactly today") is judged at the end of PR B; PR D changes `engineer` only as AC-22 says, checked by AC-26.
- **AC-16** Before any file from the zip is added, the partner's private names go into the owner's `~/.claude/private/names.txt`, each read from a named place: his first name and Mac user name from the zip's `README.md` title and `claude-home/settings.json` paths; his colleague's name from `README.md` (PRIVATE section); his studio folder name from the zip's top folder; every creator folder name from the studio folder's `reels/creators/` in the zip (all but `_schema`). The build prints the count added, then runs `private-names.py` over every staged file, the spec, its rationale, the brief and the PR's commit messages; the result must be 0 hits. Each hit is read before it blocks (the check matches inside words, so a short name can hit an ordinary word); a hit that is an ordinary word is reported to you, never silenced by editing `names.txt`.
- **AC-17** Profile data model gains `settings` (optional, missing means `{}`): a JSON object whose keys may only be `env`, `model`, `enabledPlugins`, `extraKnownMarketplaces`. The AC-1 validator fails on any other key and names it (so `hooks` and `permissions` never come from a profile). The full build order of `settings.json`, in one place:
  1. the core `claude-home/settings.json`;
  2. `skillOverrides` from the profile's `skills`;
  3. the profile's `settings`: `env`, `enabledPlugins` and `extraKnownMarketplaces` merged key by key, `model` replaced;
  4. hook commands in `hooks_off` removed (empty groups dropped);
  5. live `autoMode` kept, as install does today;
  6. the private fragment, its `/home/santiago` paths rewritten to `$HOME` as today, merged by `private-names.py merge-settings` (objects key by key, lists joined, a scalar replaced), so a private `model` or `env` value wins over the profile's.
  Install records the profile owned keys it wrote (for example `env.PONYTAIL_DEFAULT_MODE`, `model`) in `state/profile.json` as `settings_keys`. AC-5 compares those keys like any repo owned key; a switch to a profile without them removes exactly those keys and keeps every other live key. Tests: a temp profile's `settings` land in the built file; `settings.hooks` fails validation; a private `model` beats the profile `model`; `creator` then `engineer` leaves no `PONYTAIL_DEFAULT_MODE` behind.
- **AC-18** `profiles/creator/profile.json` gets `settings`: `model` `opus[1m]`; `env` `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`, `PONYTAIL_DEFAULT_MODE=lite`; `enabledPlugins` `ponytail@ponytail: true`; `extraKnownMarketplaces` `ponytail` from GitHub `DietrichGebert/ponytail` pinned to one commit (`ref`), read at build time and written in the PR text. The Telegram plugin and his `statusLine` are not in it (one person's chat and Mac paths; they go in that person's private fragment).
- **AC-19** `profiles/creator/rules/creator-overlay.md` (loads only in `creator`; says it beats `CLAUDE.md` and skill text on these points, nothing else):
  - ASCII: accented letters and Spanish punctuation (vowels with an acute accent, n with a tilde, u with a diaeresis, the inverted question and exclamation marks) are allowed in text written for people outside the claude-config repo; `/polish` keeps them there. Code, commands, and every file inside the claude-config repo stay ASCII (the repo rule holds for everyone, and the overlay file itself is ASCII).
  - `/scope` and `/audit` still start by themselves when a chat opens in a repo, but stay quiet: one plain line on where things stand plus the next step, no long readout, a question only for a real decision (D28). This is best effort: the vendored skills keep their own text, and the `chain-catch.py` Stop hook still owes planned steps as for everyone.
  - Free tools only: no paid service or API is added without the person's yes.
  - Test: after `install.sh --profile creator` on a temp live tree the file is in `rules/` and `skill-rules.py` lists it for `/scope`; after `--profile engineer` it is not there. "Quiet" itself has no automated test.
- **AC-20** `profiles/creator/rules/model-routing.md` is a rewrite, not a copy (his `rules/work/` is private by his README). It keeps only the generic lines: Opus main session for creative and taste work; `careful-worker` (Sonnet) for routine code, tests and docs; `mechanical-worker` (Haiku) for batch checks, counting and file moves; `researcher` for web legs; the main session rechecks every helper result against the gates; a cheap result that fails is redone on Opus and noted. Dropped: his paths, his quality lock and sandbox lines, his dated decisions. In `rules` of `creator` only.
- **AC-21** `claude-home/agents/careful-worker.md` and `claude-home/agents/mechanical-worker.md` are added to the core agents from the zip, unchanged apart from removing any private name or path; `web-researcher` is not added (`researcher` covers it). Every profile gets them, since `agents/` installs whole.
- **AC-22** Skills, 15 in all:
  - 13 official Remotion skills (`remotion-best-practices` and the 12 `remotion-*` it routes to, names as in the zip) as `downloaded` manifest entries, `source` `github:remotion-dev/skills`, `pinned` to the commit fetched at build time, `path` per skill from that repo.
  - `lemo-opuscar` as a manifest entry for its own repo with source, license and `pinned` commit; its `setup.sh` clones the library at that pinned commit, not the moving head.
  - `instagram-reels-design` copied under `claude-home/skills/` (repo owned, after AC-16), with a manifest row naming its MIT starter kit file as the license of its `scripts/`.
  - License rule: only MIT and Apache-2.0 pass (the set `claude-config.py` knows). Any other license, or none found, stops the build for that skill and asks you; the others go on.
  - In `creator` these 15 are `on`; in `engineer` they are `name-only`. `creator`'s `editable` (AC-13) gains `claude-home/skills/{instagram-reels-design,lemo-opuscar}/**`.
  - `watch-reels`, `anti-ai-writing`, `deep-research` and `block-destructive.sh` keep the repo version (newer than the zip copies; his Mac patch is row 119's job).
- **AC-23** Private layer, read by install from `~/.claude/private/` on the person's machine (D29). The staged `rules/` is built in this order: core rules the profile lists, the profile's own `rules/`, then `private/rules/**/*.md` with subfolders kept (or flattened, AC-25). A private file whose staged path equals a core or profile rule is refused: install names it and exits 2, nothing is written. Install records every private origin path in `state/profile.json` as `private_rules`; AC-5 never lists them as `lost`; AC-6 sync skips them, so a private rule never reaches the repo. The 20,000 character check counts every rule file that loads (subfolders included when AC-25 shows they load). The rules step drops `find -printf` for a portable listing (AC-9b). Hook scripts in `private/hooks/` are never copied; install warns `private hook missing: <path>` for each hook command in the private fragment whose file does not exist. Tests on a temp tree: a private rule lands and a second install lists nothing; sync with an owner profile does not copy it; a name clash exits 2; a missing private hook prints the warning.
- **AC-24** `docs/guides/creator-setup.md` (ASCII, public, no private names): how a creator installs (`install.sh --profile creator`) and what goes in the person's own private layer: the settings fragment (Telegram plugin, their own hooks, a SessionStart check, statusLine, their `permissions.allow` lines), `private/rules/`, `private/hooks/`, and links in `~/.claude/skills/` to skills kept in their own private repo (for the partner: perfume-reel, perfume-learn, perfume-sync). It carries the table below and the AC-25 probe result.
- **AC-25** Probe before build (spec gate): on a real Claude Code, a rule in `~/.claude/rules/work/x.md` (a subfolder) is loaded in a new chat. The command and result go in `verify.md`. Loaded: subfolders kept. Not loaded: the named fallback applies with no further question, `private/rules/a/b.md` installs as `rules/private-a-b.md`.
- **AC-26** After PR D, `install.sh --profile engineer` on a temp tree built from today's files differs from the PR B result only by: the 15 `name-only` entries in `skillOverrides`, the two new agents, and the new skill folders. A test asserts that exact list.

His README's "Rules the profile must keep", mapped (goes into the AC-24 guide):

| His rule | Where it lives |
|---|---|
| Confirm before push, send, new channels; nothing deleted without a list and undo | core (`CLAUDE.md`, `block-destructive.sh`) |
| Telegram only to his chat; boss rules; Gmail send asks first | his private layer (`private/rules/`, `work-guard` in `private/hooks/`) |
| Free tools only, no Gemini | creator overlay (AC-19) |
| Model routing | creator rule (AC-20) |
| Test imports the real module, mutation check | core (`rules/lessons.md`) |
| Perfume gate must pass | his studio repo's own `CLAUDE.md` (private) |
| No auto /scope and /audit chains; Spanish accents | changed by you: chains stay but quiet; accents outside the repo (AC-19) |

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
| `settings` | object, keys only `env`, `model`, `enabledPlugins`, `extraKnownMarketplaces` | no, missing means `{}` | merged into `settings.json` before the private fragment (D30, approved 2026-10-27, AC-17) |

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
| install | profile `settings` values for `creator` | the partner's zip `claude-home/settings.json` (`model`, `env`, ponytail plugin and marketplace); the ponytail commit read at build time (AC-18) |
| install | a person's own rules and hooks | `~/.claude/private/rules/**`, `~/.claude/private/hooks/` plus their private settings fragment (AC-23) |
| overlay rule | what creator changes | the partner README "Not wanted here" list, D27, D28 (AC-19) |
| routing rule | which helper runs what | a rewrite keeping only the generic lines of the partner's routing rule, D31 (AC-20) |
| manifest | Remotion and lemo-opuscar pins and licenses | their source repos, commit and license read at build time; only MIT and Apache-2.0 pass (AC-22) |
| state | `settings_keys`, `private_rules` | written by install (AC-17, AC-23) |
| names.txt | partner's private names | the named places in AC-16 |

**Key invariants**:
- `engineer` reproduces today's live setup exactly (AC-3) up to PR B; after PR D it differs only as AC-26 lists.
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
7. PR D (`feat/0081d-profiles`, after PR B merges): the rules subfolder probe first (**AC-25**); partner names into `names.txt` (**AC-16**); `settings` field, validator and merge (**AC-17**, **AC-23**); creator settings, overlay and routing rules (**AC-18** to **AC-20**); core agents and skills, Remotion manifest entries (**AC-21**, **AC-22**); the creator setup guide (**AC-24**); the engineer check (**AC-26**). If it grows past about 400 lines, the skills and agents part (AC-21, AC-22) splits into its own PR.

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
- [x] When your partner's configs arrive (D5, D6): adapt them into `creator` (fewer questions, the video skills) as an amendment. Done 2026-10-27 as PR D (AC-16 to AC-25).
- [ ] The partner's `engineering.md` is not taken: core `rules/lessons.md` already holds its test and review rules.
- [ ] His two guards (`work-guard`, `install-guard`) stay in his private layer (D29). If you want the Gmail send prompt yourself later, that is a new row for a generic core hook.
- [ ] Row 119 (Mac support) covers the new scripts too; keep them Python stdlib and POSIX shell.

## Rationale
Options, context and reasoning: [rationale.md](rationale.md). Your answers: [brief](../../briefs/profiles.md).
