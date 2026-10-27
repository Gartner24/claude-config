# Creator setup
Type: how to

How a creator installs claude-config with the `creator` profile, and what stays in their own private layer. Spec
[0081](../specs/0081-profiles/index.md).

## Install

```bash
git clone https://github.com/Gartner24/claude-config ~/claude-config
~/claude-config/tools/bin/install.sh --profile creator --dry-run   # see what it would change
~/claude-config/tools/bin/install.sh --profile creator
```

Install builds `~/.claude` from the shared core plus `profiles/creator/`. When it would overwrite or drop a file you
changed in `~/.claude`, it lists it (`overwrite: changed <path>` or `overwrite: lost <path>`) and writes nothing. Carry
the change into your private layer or a PR, or run again with `--accept-overwrite`. Open a new chat after an install.

What `creator` sets:
- Model `opus[1m]` for the main chat, Sonnet for helpers (`CLAUDE_CODE_SUBAGENT_MODEL`), ponytail at level lite.
- Two rules only this profile loads: `creator-overlay.md` (accents outside the repo, a quiet `/scope` and `/audit`, free
  tools only) and `model-routing.md` (which helper runs what).
- Claude may edit the design and content skills; the rest of the core is locked. Asking for a change to a creator rule
  makes your own copy, `profiles/custom-<name>/`, and switches to it.

Switch any time: `python3 ~/claude-config/tools/bin/claude-config.py profile <name>`. Update: `/claude-config update`.

## Your private layer

Everything below lives in `~/.claude/private/` on your machine. Install reads it; sync never copies it into the repo.

| Put it in | What | Example |
|---|---|---|
| `private/settings.json` | settings only you need, merged last, so they win | the Telegram plugin, your own hooks, a SessionStart check, `statusLine`, your `permissions.allow` lines |
| `private/rules/` | rules only you load; subfolders are kept (`private/rules/work/x.md` installs as `rules/work/x.md`) | chat safety, people and privacy rules |
| `private/hooks/` | the scripts your private hooks run, referenced from `private/settings.json` by path | a guard for your own folders |
| `~/.claude/skills/<name>` | a link to a skill kept in your own private repo | your studio's reel skills |

A private rule must not have the name of a core or profile rule: install refuses it and names it. A hook in
`private/settings.json` whose file is missing is named at install (`private hook missing: <path>`).

## Rules the profile keeps, and where each lives

| Rule | Where it lives |
|---|---|
| Confirm before push, send, new channels; nothing deleted without a list and undo | core (`CLAUDE.md`, `block-destructive.sh`) |
| Telegram only to your own chat; people rules; a mail send asks first | your private layer (`private/rules/`, a guard in `private/hooks/`) |
| Free tools only | creator overlay |
| Model routing | creator rule `model-routing.md` |
| A test imports the real module, mutation check | core (`rules/lessons.md`) |
| Your project's own quality gate must pass | that project's `CLAUDE.md` (private) |
| No auto `/scope` and `/audit` chains; Spanish accents | changed: the chains still start but stay quiet; accents are allowed outside the repo |

## Rules in subfolders load (AC-25 probe)

A rule in a subfolder of `~/.claude/rules/` loads in a new chat, so private subfolders are kept as they are. Probe run
2026-10-27: a rule at `~/.claude/rules/zz-probe-0081/x.md` holding a probe word, then
`claude -p "What is the probe word? ..."` answered the word. The probe file was removed afterwards.
