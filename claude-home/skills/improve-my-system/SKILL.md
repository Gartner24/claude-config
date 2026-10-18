---
name: improve-my-system
description: Weekly review of your own session history. Finds repeated corrections, context you keep explaining, skills you should have, jobs to automate and stale rules, each backed by 3 or more sessions and a quote, and applies nothing without your yes (spec 0061).
disable-model-invocation: true
---
You run this by hand, about once a week. It reads only the projects listed in `~/.claude/private/history-allow.txt`,
through a script that removes keys, emails and private names before you read a word. It changes no file until the
user names the items to apply. Never copy the report or the extract into a repo.

## 1. Extract

Run `python3 ~/.claude/skills/improve-my-system/extract.py`. If it exits 1, print its message and stop: a missing
allow list, a missing `names.txt`, or `~/claude-improve` inside a git repo are for the user to fix. Read nothing
from `~/.claude/projects/` yourself; the files in `~/claude-improve/extract/` are your only source for sessions.

## 2. Read, project by project

For each `~/claude-improve/extract/project-NN.jsonl`, start one subagent (model sonnet, Read only) that reads that
one file and returns, for each pattern below, the sessions (id and date) it appears in and one short quote of the
user's own words:

- a correction the user typed more than once (the same "no, do X", "I told you", "stop doing Y");
- context the user keeps explaining again (the same facts about a repo, a tool, a preference);
- a job done by hand the same way each time (a skill candidate: count the sessions and the rough minutes each);
- a step that could run on its own (an automation: a hook, a `wf` box, a schedule);
- a rule or skill the sessions show is out of date or ignored.

Then read `~/.claude/CLAUDE.md`, `~/.claude/rules/*.md` and the skill list, so each finding names the rule or file it
belongs in, and `~/claude-improve/report.md` from last time if it exists.

## 3. Write `~/claude-improve/report.md`

- The numbers: projects, sessions, dates covered, messages read.
- Top recurring corrections: each with the exact rule text to add and the file it goes in.
- Context to write once: the fact and where it goes (`AGENTS.md`, a rule, a memory).
- Skills you should have: up to 7, ranked by occurrences times minutes.
- Automations.
- Cleanup: stale rules and unused skills.
- Fixed since last report: last report's findings that no longer appear.
- Too early to tell: anything seen in fewer than 3 sessions.

Every finding outside "too early to tell" needs 3 or more sessions, their dates, and one short quote. No quote or
fewer than 3 sessions: it goes under "too early to tell".

## 4. Inbox

Pick up to 3 top findings and add each as one plain line:
`python3 ~/.claude/skills/improve-my-system/extract.py --propose "<finding 1>" "<finding 2>" "<finding 3>"`.
It writes the runner's inbox with the same never twice rule, and your session start then shows `wf proposals: N new`.

## 5. Ask

Print a summary of at most 15 lines: the numbers, then the findings numbered. Ask which numbers to apply. Change no
file until the user names them; then apply only those, one at a time, and never guards, deny lists, settings or the
plan without that item named.
