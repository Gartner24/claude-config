# 0039 · Questions while wf is off

**Date**: 2026-10-14
**Status**: Accepted
**Paths:** `runner/questions.py`, `runner/finish.py`, `runner/telegram.py`, `runner/run.py`, `runner/pr.py`, `runner/wf.py`, `runner/tests/test_questions.py`
**Amends**: [0020](../0020-one-command-wf/index.md) AC-2 (a questions section on the `wf` screen), [0029](../0029-telegram/index.md) AC-6 (a fetch outside a run), [0031](../0031-adopt-open-prs/index.md) security review (a keyboard answer counts as yours)

## What you're agreeing to
- When you type `wf`, every question still waiting is shown first, with its choices and the recommended one, and you can answer each one right there; Enter leaves it open. With `-y` they are only listed.
- `wf questions` lists the waiting questions with their links, and changes nothing.
- `wf telegram timer on` starts a small timer that saves your Telegram answers every 5 minutes, so an answer you tap while wf is off is still there when wf next runs. `wf telegram timer off` removes it.
- An answer typed at your keyboard is used exactly like one from your phone, and can approve a merge or a post, because the keyboard is you.

## Acceptance criteria
Today: the `wf` screen has no questions section (`runner/finish.py:1005-1027`); Telegram answers are read only by a running wf (`runner/telegram.py:203` `fetch`, called from `Topic.poll`), and Telegram drops a bot's unread updates after about 24 hours; a decision's `source` may only be `None` or `phone` (`runner/run.py:454`); the strong answer check knows only Telegram and ntfy codes (`runner/pr.py:672`); the morning report already lists each repo's open questions with the recommended answer (`runner/report.py:52`, spec 0021 AC-6).

- **AC-1** (screen): bare `wf`, after an interrupted swap is finished and before the plan, prints a `questions:` section when queue.json holds an open question (answer `None`), oldest asked first. Each question: `<id> <repo folder name>: <feature>: <question>`, then its options numbered from 1 with ` (recommended)` on the first, or `(no options, type your answer)`. Every field goes through `wf.clean` (a terminal, so real names stay, control characters go). Questions of every level are listed (a running run reads a keyboard answer to its own keep going question too, `run.py` `limit_check`). An unreadable queue prints one `warning:` line and the screen goes on (the retakes step refuses it as before).
- **AC-2** (answer): at a terminal without `-y`, after the section, one prompt per question: `answer <id> (number, text, Enter skips): `. Enter skips it. Anything else is parsed exactly as a Telegram reply (`telegram.answer_text`, shared with `Topic.take`: a number or comma list of numbers picks labels, a label matches ignoring case, else the text itself) and written under queue.lock only while the answer is still `None`, with `source: keyboard` and `answered` now. It prints `answered: <id> <answer> (keyboard)`, or `already answered: <id>` when the phone or a run got there first. Ctrl C or end of input cancels `wf` with exit 130; answers already written stay. With `-y` the section is printed and nothing is asked.
- **AC-3** (resume): a keyboard answer is the same record change a phone answer makes (`run.py` `poll`), so the next run resumes the call with it (`pick`), or a running run picks it up at its next pick. `queue_problem` accepts `source: keyboard`.
- **AC-4** (strong): `pr.strong` also holds when `source` is `keyboard`. There was no keyboard answer before; `wf` already takes your Enter at the keyboard as your go for setup swaps and builds, so a keyboard answer counts as yours, like a Telegram answer from your own chat.
- **AC-5** (`wf questions`): read only, never creates the state folder. The same lines as AC-1, plus under each question the links its `context` holds (spec 0033): `spec:`, `issue:` per issue, `PR: #<n> <url>`, and `asked: <time>`. `no open questions` when there are none. An unreadable queue: `refused: queue_unreadable: <why>`, exit 5.
- **AC-6** (`wf telegram fetch`): one `telegram.fetch` and exit 0, printing nothing. No telegram.json: exit 0 at once. An invalid telegram.json or a failed getUpdates: one line on stderr, exit 1. It takes the same `telegram.lock` with the same non blocking flock as a running wf's fetch, so the two never read or write the update log at once; when wf holds it, the fetch returns and wf's own fetch saves the update. Offsets come from the log, so nothing is fetched twice.
- **AC-7** (`wf telegram timer on|off`): `on` refuses under `WF_RUN` (exit 5) and without telegram.json (exit 5); else writes `$XDG_CONFIG_HOME/systemd/user/wf-telegram-fetch.service` (oneshot, `ExecStart=` this Python and the `wf` on PATH, else this wf.py, `telegram fetch`, with the `XDG_STATE_HOME` and `XDG_CONFIG_HOME` of the shell that ran `on` when set, so the timer reads the same state folder) and `wf-telegram-fetch.timer` (`OnBootSec=1min`, `OnUnitActiveSec=5min`, `WantedBy=timers.target`), then `systemctl --user daemon-reload` and `systemctl --user enable --now wf-telegram-fetch.timer`. `off` runs `systemctl --user disable --now wf-telegram-fetch.timer`, removes both files, then `daemon-reload`. A failed systemctl prints its error and exits 1.
- **AC-8** (report): no change. The report already lists open questions with the recommended answer, and its `next: wf` line now leads to the questions section.

Known limit: an answer the timer saved but no run has read yet still shows as open on the `wf` screen; press Enter and the run takes the phone answer.

## Build plan
1. `runner/questions.py`: `open_list`, `lines`, `answer`, `screen(yes)` for `finish.cmd_wf`, `cmd_questions`.
2. `telegram.py`: `answer_text` out of `Topic.take`; `cmd_fetch`, `cmd_timer`.
3. `run.py` `queue_problem` and `pr.strong`: `keyboard`. `wf.py`: `questions`, `telegram fetch|timer`.
4. Tests in `runner/tests/test_questions.py`, systemctl mocked, temp HOME and XDG folders.
