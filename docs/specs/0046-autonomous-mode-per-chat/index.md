# 0046 · Autonomous mode per chat

**Date**: 2026-10-15
**Status**: Accepted
**Paths:** `runner/auto.py`, `runner/wf.py`, `runner/finish.py`, `runner/run.py`, `skills/auto/SKILL.md`, `settings.json`, `runner/tests/test_auto.py`, `runner/tests/test_auto_chats.py`
**Amends**: [0030](../0030-autonomous-mode/index.md) (one driving folder becomes one per chat)

## What you're agreeing to
- Several Claude chats can each run autonomous mode for their own repos at once: this chat for claude-config, a chat in a work repo for that repo and its related repos. Each chat starts, watches and relays only its own repos' runner, questions and report.
- `/auto on` takes the chat's own repo plus any you name; the chat then suggests related repos and you pick them in a multiple choice panel.
- A repo belongs to one chat at a time. A chat that is still open keeps its repos until it hands them over, writing what was agreed in chat into the feature's brief first, so the new chat starts with that context.
- Questions still go to your one Telegram chat, each naming its repo. Keeping groups apart on the phone comes later.

## Summary

Today one folder drives the runner for every allowed repo, and only that chat can start it or see its questions. Your messages of 2026-10-14 and 2026-10-15 asked for one autonomous chat per group of repos, built tonight. Source: [brief](../../briefs/autonomous-per-chat.md).

## Requirements

**Acceptance criteria**:
- **AC-1** (state): `auto.json` holds `{"version": 2, "chats": {<folder realpath>: {"repos": [<repo keys>], "since", "seen", "started", "relayed", "suggested"}}}`, repo keys as `wf.key_of` gives them (a worktree counts as its main checkout). A chat exists only while it is on: off deletes its entry. Turning on sets `seen` to `since`. A version 1 file with `on` true is read as one chat for its folder whose repos are every repo on the wf allow list; with `on` false it is read as no chats; either is written back as version 2 on the next change. Unreadable stays off (spec 0030). **Chat key**: the nearest folder at or above the current folder that is a chat key; the hook (`cwd`), the bar (`workspace.current_dir`), `take`, `release`, `wait`, `status` and `start` (`os.getcwd()`) all resolve it this one way.
- **AC-2** (on): `/auto on [names]`, typed by you in an interactive session (spec 0030's `interactive()` check, unchanged), turns on the chat of the session's folder. Its repos: the git repo holding the folder, when it is on the wf allow list; plus each name after `on`. A name matches an allow list entry by a case insensitive exact match on its folder name or its realpath, never a substring. The hook accepts the prompt `/auto on` alone or followed by names split on spaces, each `[A-Za-z0-9._-]+`; anything else refuses. In a folder that is in no allowed repo and with no names, the chat turns on with no repos and prints the allowed names to pick from. A name that matches no allowed repo, or more than one, refuses the whole command with the allowed names listed. A repo another live chat holds is left out and named (AC-4). A repo held by a chat that is not live may be taken here, because you typed it: the line says `taken from the chat in <folder>, idle since <time>; its briefs: <brief paths of that repo's open features, or none>`. It prints `autonomous: on in <folder>: <repo names>`. Turning a chat on stays yours only: the deny rules of spec 0030 are unchanged.
- **AC-3** (suggest and take): once per chat, at the first SessionStart or prompt hook after it turns on, the hook output adds one line `suggested repos: <names>` and sets `suggested` so it never repeats: allowed repos held by no chat that share the parent folder of one of the chat's repos, or its GitHub owner (`run.github_origin`; a repo with no GitHub origin matches on parent folder only), at most 6; a chat with no repos gets every allowed repo held by no chat, at most 6. The DRIVE text tells the session to ask you with a multiple choice panel which to add, and to run `wf auto take <names>` with your picks. `wf auto take <names>` adds allowed repos to the current chat, matching names as AC-2 does, at most 6 per call, and prints one line per added repo. It refuses when that chat is off, any argument starting with `-`, a name not on the allow list, a repo any other chat holds (live or not: only you take from another chat, with `/auto on <name>`), and a repo whose runner lock (spec 0004) another unit holds. It is allowed for Claude through the single allow rule `Bash(wf auto take *)`, since it never turns a chat on and only reaches repos you already allowed with `wf allow`.
- **AC-4** (one owner): a chat is live while its status bar ran within the last 10 minutes: `wf auto bar` writes the chat's `seen` time, at most once a minute. A repo held by a live chat cannot be taken or turned on elsewhere; the refusal says `held by the chat in <folder>: release it there first`. `wf auto release <names>` (allowed for Claude) drops repos from the current folder's chat. The DRIVE text tells a session to write the chat's agreed decisions about a repo into that feature's brief under "Agreed so far" (the brief before handoff rule) before it releases the repo. A repo of a chat that is not live moves only when you type `/auto on <name>` (AC-2). A running unit keeps its repo list until its next start: `take` and `release` on a chat whose unit runs print `applies at the next wf auto start`.
- **AC-5** (runner per chat): `wf auto start` in a chat starts the user unit `wf-auto-<first 8 hex of sha1(folder)>` with `WF_AUTO_FOLDER=<folder>`, running `wf -y --repos <path> [--repos <path> ...]`. The new hidden, repeatable `--repos` option limits bare `wf` to those repos in every place it reads the whole queue: discovery, the plan, `questions.screen`, retakes, `recover`, `end_wait`, watched PRs, and `auto.fingerprint`, `counts` and `active`. `run.auto_off` ends a run when its `WF_AUTO_FOLDER` chat entry is gone. Two units that meet the setup swap lock: the second waits for it. A chat with no repos refuses `refused: no repos`. Two chats never hold one repo, and spec 0004's repo lock stays the guard if they ever did.
- **AC-6** (wait per chat): `wf auto wait` in a chat returns `question <id>` only for decisions of its repos, `run ended` for its own unit, and `work` from a fingerprint over its own repos.
- **AC-7** (status): in a chat that is on, the bar shows `AUTO running <n> feature(s) in <m> repo(s), <q> question(s)`, counted from `active.json` entries of its repos (no runner lock count), or `AUTO idle, <q> question(s)`, questions counting only its repos (the count shows while idle too, which the 2026-10-15 P3 check could not see); `wf auto status` the same in words with its repo names. A folder whose chat is off shows `auto: <n> chat(s) on` when any chat is on, else nothing.
- **AC-8** (off): `/auto off` deletes only this chat's entry, so its unit ends at its next pick (AC-5); `/auto off now` also stops only its unit. Other chats go on.
- **AC-9** (phone): unchanged: one Telegram chat; every question already names its repo. Keeping groups apart on the phone is deferred (below).
- **AC-10** (tests): every AC above, including version 1 migration, a refusal for a live holder, a take from an idle holder, suggestion cap and filters, `--repos` limiting the plan, wait and bar counting only the chat's repos, off for one chat (chat A off ends unit A, unit B goes on), a version 1 file with `on` false, a refused name starting with `-` or with shell characters, and that the deny rule wins for `wf auto take x && wf auto on`. The allow rules never cover `wf auto on`. Each mutation checked.
- **AC-11** (real check, waits on you): two real sessions in two folders each turn on their own chat and their bars show only their own repos; a take of a repo the other live chat holds is refused.

Deferred: separate Telegram groups per chat (for example one Telegram forum topic per chat); your words: "we should come up with a solution because we are gonna combine a lot of things in a single chat".

## Cross check

Another model read this spec on 2026-10-15. Each gap took its recommended fix (your standing answer for tonight):
- A chat in a folder outside any repo would have grabbed every repo, so a work chat opened later was refused its own repo: it now takes none and lists the names (AC-2).
- `/auto off` could not end a running unit, which only knew the old single switch: units carry their chat folder and end when its entry is gone (AC-1, AC-5, AC-8).
- A closed chat's unit keeps building: `take` refuses a repo whose runner lock is held, and a running unit keeps its list until the next start (AC-3, AC-4).
- `take` could widen a chat by loose name matching or extra flags: exact names only, no `-` arguments, at most 6, each added repo printed (AC-2, AC-3).
- Taking from an idle chat would lose unwritten context, against your "refuse until the context can pass": only you can do it, by typing `/auto on <name>`, and the line names that repo's briefs (AC-2, AC-4).
- Where `--repos` must filter, the swap lock, the once only suggestion, the bar's count and one way to find the chat folder were unstated (AC-1, AC-3, AC-5, AC-7).

## Decision

Chats are keyed by folder in the existing `auto.json`, each with its repo list and its own unit; liveness comes from the status bar the chat already runs every few seconds, so no new process is needed. A repo moves only through an explicit release, or when you type `/auto on <name>` after its chat has been gone for 10 minutes, with the brief rule carrying the context.

## Feature design

**Value sourcing**:
| Value | Source |
|---|---|
| chat key | the session folder's realpath (hook `cwd`, bar `workspace.current_dir`) |
| a chat's repos | `/auto on` names and the folder's repo, matched against `read_allowed()` |
| suggested repos | allow list, shared parent folder or `origin` owner, at most 6, not held live |
| live | `seen` within 10 minutes, written by `wf auto bar` at most once a minute, `since` at turn on |
| unit name | `wf-auto-` + first 8 hex of sha1(folder realpath) |
| question scope | `queue.json` decisions whose `repo` is one of the chat's repos |

**Security model**: turning a chat on stays user only (deny rules plus the interactive check). `take` and `release` are open to Claude but only move repos already on your `wf allow` list, never turn anything on, and never take a repo a live chat holds. Repo names and suggestions reach the session as quoted data.

## Build plan

1. State v2 with migration, `on` with names, `take`, `release`, liveness from the bar. AC-1 to AC-4.
2. `--repos` for bare wf; per chat unit in `start` and `off now`. AC-5, AC-8.
3. Wait, status and bar per chat; DRIVE text for suggest, take and release. AC-3, AC-6, AC-7.
4. Settings allow rules for take and release; tests and mutation checks. AC-10.
5. Real check, two sessions. AC-11.

## Consequences

**Positive**: work and personal autonomous chats side by side, each with its own context, and a repo can move between them without losing what was agreed.
**Negative**: a closed chat holds its repos until you take them; a session can widen its own chat to more allowed repos after your panel answer, though never beyond your allow list.

## Rationale

Your three answers of 2026-10-15 (this repo plus named with a suggested set picked in a panel; refuse until the context can pass; the same Telegram chat for now) decide the shape; the rest are recommended defaults taken tonight under your standing answer, listed in the cross check note below.
