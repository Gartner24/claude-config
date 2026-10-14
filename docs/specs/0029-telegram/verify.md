# Verify: Telegram instead of ntfy · spec 0029

Run 2026-10-14 by `/check verify telegram`, against a local fake Bot API on 127.0.0.1 (`WF_TELEGRAM_API`), temp
`XDG_CONFIG_HOME` and `XDG_STATE_HOME`, so nothing reached a real bot or your config. The scripts are in `probes/`.
Each step names the break that would make it fail (`can fail:`). Three breaks were tried for real in a scratch copy
of `runner/` (`RUNNER=<copy>`), each turned exactly its own step red: the chat filter removed (AC-6), `redact()`
returning the text unchanged (AC-1), an invalid file falling back to ntfy (AC-2).

## Commands
- [x] `python3 -B docs/specs/0029-telegram/probes/drive.py .` -> `25/25 passed`, exit 0. Its steps:
  - [x] load refuses mode 0644, non JSON, bad token, string chat_id; no reason holds the token -> AC-1. can fail: load accepts a group readable file, or a why echoes the token
  - [x] an API error that echoes the URL path shows `/bot<token>/`, also after the 3 ping tries -> AC-1. can fail: redact() not applied (tried: red)
  - [x] `ntfy.write` gives 0600 in a 0700 folder -> AC-1. can fail: write leaves 0644
  - [x] a valid telegram.json picks the telegram module -> AC-2. can fail: channel() prefers ntfy
  - [x] real `wf run` with a 0644 telegram.json: exit 5 `refused: no_telegram: ...` -> AC-2. can fail: falls back to ntfy (tried: red, traceback exit 1)
  - [x] real `wf run` with neither file: exit 5 `refused: no_ntfy: no telegram.json or ntfy.json, run wf telegram init` -> AC-2. can fail: why names only ntfy.json
  - [x] the call sandbox denyRead and Read rules cover `$XDG_CONFIG_HOME/wf/telegram.json` -> AC-3. can fail: `~/.config/wf` dropped from CREDENTIAL_PATHS or expand() misses XDG
  - [x] a 4 option panel is one sendMessage, 4 buttons `abcd 1..4`, ends `tap a button, or reply to this message`, returns the id -> AC-4. can fail: buttons cut to 3, or no id returned
  - [x] a prose question with the styled send refused resends plain, no buttons, ends `reply to this message with your answer` -> AC-4 (as amended by 0038). can fail: no plain retry, or buttons on prose
  - [x] priority 2 sends `disable_notification`, a title is the first line -> AC-5. can fail: acks ring the phone
  - [x] fetch logs your tap, maps a swiped reply to `abcd use the blue one`, skips another chat's message and another sender's tap -> AC-6. can fail: chat filter missing (tried: red)
  - [x] every tap gets answerCallbackQuery, one hint for the stray `hello` only -> AC-6. can fail: hint sent to `abcd 3` too
  - [x] the next fetch asks offset 16, the log is 0600 -> AC-6. can fail: offset restarts, log world readable
  - [x] a held telegram.lock returns at once with no getUpdates -> AC-6. can fail: blocking flock or no lock
  - [x] a 49 hour old line is dropped -> AC-6. can fail: no 48 hour cut
  - [x] poll(`u12`) returns u13 to u16, a bad cursor returns all 7 -> AC-7. can fail: cursor compared as text
  - [x] take: a reply older than the question is ignored; `2`, `1,2`, `GREEN`, free text and prose answer; source `phone` -> AC-8. can fail: asked time not checked
  - [x] report.send: 1223 chars one message, 7223 chars two messages each at most 4096 joined back to the body, 24123 chars one short message plus `wf-report.txt` holding the body -> AC-9. can fail: split mid line or no file
  - [x] real `wf telegram init` with `not-a-token`: exit 2, nothing written -> AC-10. can fail: malformed token accepted
  - [x] real `wf telegram init`: getMe, deleteWebhook, skips a wrong code and a group chat, binds the private `/start <code>` chat, sends `wf connected`, saves 0600, never prints the token -> AC-10. can fail: first /start of any chat binds
  - [x] init again without `--rotate`: exit 2 -> AC-10. can fail: overwrites the file
  - [x] real `wf telegram test`: a tap on button 1 prints `accepted: yes`, exit 0 -> AC-10. can fail: tap never read
  - [x] only stdlib plus local `context`, `ntfy`, `wf` imported; a hung call ends at 10.0 s, token redacted -> AC-11. can fail: no timeout
- [x] `env REPO=. python3 -B docs/specs/0029-telegram/probes/run_over_telegram.py` -> a whole `wf run` (the runner's fake claude) asks over the fake bot, buttons `<id> 1..3`, the tap answers `Postgres (recommended)` source `phone`, the call resumes with it, the ack and the morning report go to Telegram, ntfy gets 0 posts -> AC-2, AC-7, AC-8. can fail: run.py polls ntfy, or take() not passed the message
- [x] `python3 -B docs/specs/0029-telegram/probes/report_uncapped.py .` -> Telegram body 30 built lines, ntfy 12 lines ending `+21 more on the wf screen` -> AC-9. can fail: Telegram keeps the 12 line cap

## Docs
- [x] AGENTS.md has `wf telegram init|test` and the Telegram gotcha; `docs/architecture.md` names both channels, `phone ping`, `wf connected` and the hint in invariant 4 -> AC-12 (read, not counted as a runtime step)

## Live (your box: make the bot with BotFather, then `wf telegram init` and `wf telegram test`)
- [ ] P1 to P5 of the spec against the real Bot API, and `wf telegram test` on your phone -> AC-4, AC-6, AC-9, AC-10

## Acceptance-criteria coverage
- AC-1 met · AC-2 met · AC-3 met · AC-4 met · AC-5 met · AC-6 met · AC-7 met · AC-8 met · AC-9 met · AC-10 met against the fake bot (real bot owed by the live box) · AC-11 met · AC-12 met
