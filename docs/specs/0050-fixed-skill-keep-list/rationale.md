# 0050 rationale

## Context

The research review of spec 0048 (section 5) counted 77 skills still described in every session, above the 30 to 50 tools at which Anthropic says tool choice gets worse. Measured again on 2026-10-15: 83 own skills and commands are not set to `name-only` (209 are), and about 56 plugin skills come from 9 enabled plugins. But the skill list in a real session showed only about 29 own skills with a description: Claude Code drops the least used descriptions when over its budget, and the 29 it kept match the skills used in the last 30 days.

## Options considered

- **Drop the row.** Claude Code already does most of this. Rejected by your answer: you want to decide the list yourself.
- **Shorten the six long descriptions.** Saves about 6,600 characters (about 1,700 tokens) a session, and five of the six would become patches against jjstack. Rejected by your answer: they are important and stay as they are.
- **Turn off unused plugins** (sentry-skills adds 27 skills, 0 uses; it is loaded from `~/.claude/skills/getsentry-skills/.claude-plugin/`, not from `installed_plugins.json`, which is why AC-6 reads both places). Rejected: their skills would stop running by name. Report only.
- **One time edit of the settings files.** Rejected: new skills arrive described, which is how the count reached 83.
- **Keep list plus script** (chosen).

## Rationale

- The script writes only `~/.claude/settings.json` and lets `./sync.sh` copy it, because `sync.sh` already strips private names into a private fragment (spec 0013). Writing the repo copy directly would bypass that; one skill name is already kept out of the repo copy for that reason.
- `off` and `user-invocable-only` values are left alone: they are choices you made on purpose, and the keep list only decides described versus name only.
- Entries for skills not installed are not removed: removing them saves nothing and would lose a setting if the skill comes back.
- Usage counts came from the Skill tool calls and typed commands in every chat log modified in the last 30 days (2,966 files, wf runs included). Built in commands (`loop`, `schedule`, `skill-doctor`) and plugin skills were left out of the list.

## References

None (your setting).
