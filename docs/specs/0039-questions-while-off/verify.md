# Verify: questions while wf is off · spec 0039

Run on 2026-10-14 with `python3 -B docs/specs/0039-questions-while-off/probes/drive.py`. It drives the real `wf`
command (`runner/wf.py`) in temp HOME and XDG folders, with the test fake claude, the e2e fake Telegram bot
(`WF_TELEGRAM_API`, 127.0.0.1 only) and a fake `systemctl` on PATH. Bare `wf` prompts get a real terminal (a pty).
Result: 19 of 19 steps pass. Each step was then broken in the code one way and seen to go red (list below).

## Commands
- [x] V1 `wf questions` with no state: prints `no open questions`, exit 0, no state folder made → AC-5
  can fail: the listing creates the state folder (break: `os.makedirs` in `cmd_questions`, V1 red)
- [x] V2 `wf questions` with two open and one answered: open ones only, oldest asked first, numbered options, `(no options, type your answer)`, `spec:`, `issue:`, `PR: #7 <url>`, `asked:`; an escape character is stripped; queue.json bytes unchanged → AC-5, AC-1
  can fail: links missing (break: drop the `spec:` line, V2 red)
- [x] V3 `wf questions` with queue.json `{`: `refused: queue_unreadable: ...`, exit 5 → AC-5
  can fail: exit 0 on an unreadable queue (break: return 0, V3 red)
- [x] V4 bare `wf -y` with an unreadable queue: exactly one `warning: questions not read:` line first, the screen goes on → AC-1
  can fail: the warning stops the screen (break: return 130, V4 red)
- [x] V5 bare `wf -y` with one open question: output starts with the `questions:` section, no `answer` prompt, the answer stays empty → AC-1, AC-2
  can fail: `-y` still asks (break: drop the `if yes` return, V5 red)
- [x] V6 bare `wf` at a terminal: Enter skips the first, `sqlite` typed for the second prints `answered: cd34 SQLite (keyboard)`, queue has `source: keyboard` and `answered` set, the skipped one stays open → AC-2
  can fail: the answer is recorded as a phone answer (break: `source="phone"`, V6 red)
- [x] V7 the queue is answered by the phone while the prompt waits, then `1` typed: `already answered: ab12`, the phone answer kept → AC-2
  can fail: the keyboard overwrites an answered question (break: drop the `answer is None` check, V7 red)
- [x] V8 end of input at the second prompt exits 130 with the first answer kept; SIGINT at a prompt exits 130 → AC-2
  can fail: end of input is not a cancel (break: catch only KeyboardInterrupt, V8 red)
- [x] V9 a real `wf run` (fake claude) asks and the question stays open; bare `wf` answers `2` at the keyboard; the next `wf run later -y` prints `resume: <id>` and resumes the asking session with `The user answered your DECISION NEEDED question: SQLite` → AC-3
  can fail: bare `wf` never shows the questions (break: remove the `questions.screen` call in `finish.cmd_wf`, V9 red); the queue rejects `source: keyboard` (break in `run.queue_problem`, V9 and V10 red)
- [x] V10 `pr.strong` holds for a keyboard answer and not for an uncoded phone answer on ntfy; `run.queue_problem` accepts a keyboard answer → AC-4, AC-3
  can fail: keyboard answers cannot approve a merge (break: drop `keyboard` from `pr.strong`, V10 red)
- [x] V11 `wf telegram fetch` with no telegram.json: exit 0, no output, no log → AC-6
  can fail: a missing config errors (break: drop the existence check, V11 red)
- [x] V12 `wf telegram fetch` three times against the fake bot (one update, none new, one more): silent, exit 0, log holds `u500`, `u501` once each with their texts → AC-6
  can fail: the fetch does not save updates (break: skip `fetch`, V12 red)
- [x] V13 with `telegram.lock` held by another process: the fetch exits 0 at once and saves nothing → AC-6
  can fail: the fetch ignores the run's lock (break: go on after `BlockingIOError`, V13 red)
- [x] V14 telegram.json mode 644: exit 1, one stderr line, no stdout → AC-6
  can fail: a broken config passes silently (break: return 0, V14 red)
- [x] V15 Done when: a run asks over the fake Telegram bot and ends with the question open; a reply `<id> 2` arrives while wf is off; `wf telegram fetch` saves it; the bot then forgets every update (Telegram's 24 hour drop); the next `wf run later -y` resumes the session with `SQLite` → AC-6, Done when
  can fail: the timer's fetch saves nothing (break: skip `fetch`, V15 red)
- [x] V16 `wf telegram timer on` (fake systemctl): writes the service (`Type=oneshot`, `Environment="XDG_STATE_HOME=..."`, `Environment="XDG_CONFIG_HOME=..."`, `ExecStart="<python>" "<wf.py>" telegram fetch`) and the timer (`OnBootSec=1min`, `OnUnitActiveSec=5min`, `WantedBy=timers.target`), calls `daemon-reload` then `enable --now wf-telegram-fetch.timer` → AC-7
  can fail: wrong interval (break: `5h`, V16 red)
- [x] V17 the service's ExecStart run with only the environment the unit sets: fetches a new update into the state folder a run reads → AC-7
  can fail: the unit drops the shell's XDG folders and reads another state folder (break: no Environment lines, V16 and V17 red)
- [x] V18 `wf telegram timer off`: `disable --now` then `daemon-reload`, both unit files removed → AC-7
  can fail: the files stay (break: skip the unlink, V18 red)
- [x] V19 `timer on` under `WF_RUN` exits 5 `refused: unattended`; without telegram.json exits 5 `refused: no_telegram:`; a failing systemctl on `on` and `off` prints `systemctl: boom` and exits 1 → AC-7
  can fail: `on` runs inside an unattended call (break: drop the WF_RUN check, V19 red)

## Not counted
- AC-8 (report, no change): commit 1192f60 does not touch `runner/report.py`; nothing new to drive.
- Your real timer (supporting only): `~/.config/systemd/user/wf-telegram-fetch.service` runs `"/usr/bin/python3" "~/.local/bin/wf" telegram fetch` (home folder shortened here), and `~/.local/state/wf/telegram-updates.jsonl` was rewritten at 23:07:54, 40 seconds before this check. `systemctl --user list-timers` is refused inside the sandbox (no user bus), so the timer's schedule was not read here.

## Acceptance criteria coverage
- AC-1 V2, V4, V5, V6 · AC-2 V5 to V8 · AC-3 V9, V10 · AC-4 V10 · AC-5 V1 to V3 · AC-6 V11 to V15 · AC-7 V16 to V19 · AC-8 no change
