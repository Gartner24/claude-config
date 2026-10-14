# 0029 rationale

Source: personal scope row 26 ("Telegram instead of ntfy"), docs/briefs/finish-runner-today.md item 18, your message 2026-10-13. Done when (row 26): a run's questions and its end report arrive in Telegram, a button tap or a typed reply answers a question, and ntfy is removed or kept as a fallback (decided here: kept).

## What the code does today
- `runner/ntfy.py` is the only channel: config and validation (`load`, `:51`), scrubbing (`scrub`, `:142`; `scrub_field`, `:166`), repo labels (`:189`), `Topic.publish` with three tries (`:231`), `Topic.ping` with up to 3 buttons (`:249`, `:261`), `poll` by `since` cursor (`:268`), `take` with one time codes for free text (`:273`, `:291`).
- `runner/run.py` loads it at start (`:778`), pings in `ask` (`:1357`), polls in `poll` (`:2243` to `:2300`) with its own cursor and a dedupe on ping, ack and reply ids (`:2273`), re-pings (`:2314`), and waits in `end_wait` (`:2348`).
- `runner/report.py` caps the phone body at 12 lines and 1000 characters (`:13`, `:14`, `:185`) and sends through `ntfy.Topic.publish` (`:213`).
- `wf ntfy init|codes|test` are wired in `runner/wf.py:672` to `:678` and `:705` to `:710`.
- `~/.config/wf/` is not hidden from calls today (`CREDENTIAL_PATHS`, `runner/run.py:60`). That was acceptable for ntfy (the topic is the only secret and codes are stored hashed); a bot token is a real credential, hence AC-3.

## Research (Telegram Bot API, core.telegram.org/bots/api)
- Requests: `https://api.telegram.org/bot<token>/<method>`, JSON or form body, JSON reply `{"ok": ..., "result": ...}`. The token is in the URL path, so any error that echoes the URL leaks it: AC-1 `redact()`.
- `sendMessage` text is 1 to 4096 characters. `reply_markup.inline_keyboard` buttons carry `callback_data` of 1 to 64 bytes. A tap arrives as a `callback_query` update and must be answered with `answerCallbackQuery` or the button keeps spinning.
- `getUpdates` (long polling) and webhooks are exclusive: while a webhook is set, getUpdates fails, hence `deleteWebhook` at init. An update is confirmed by calling getUpdates with an `offset` above its id; unconfirmed updates are kept 24 hours. Two simultaneous getUpdates calls on one bot conflict, which is why one process fetches at a time (AC-6).
- A bot cannot message a user first; the user must open the bot and send `/start`. A `t.me/<bot>?start=<payload>` link sends `/start <payload>`.
- `sendDocument` takes a multipart upload; `urllib` can send a hand built multipart body (P5).

## Decided without asking (2026-10-13)
1. **Keep ntfy or remove it?** Options: remove; keep as the fallback when `telegram.json` is absent. Picked: keep (your message asked for it; it also covers the days before the bot exists).
2. **Invalid `telegram.json`: fall back to ntfy or refuse?** Options: fall back quietly; refuse `no_telegram`. Picked: refuse. A quiet fallback would send questions to a topic you may no longer watch, and you would wake to nothing answered.
3. **Who may answer?** Options: anyone who finds the bot plus one time codes (as ntfy); only your chat id. Picked: only your chat id, checked on both the chat and the sender. Telegram authenticates the sender, so codes add nothing; free text needs no code.
4. **How the chat is found at init.** Options: first `/start` from anyone; `/start <code>` with a code printed at init. Picked: the code. Anyone who guesses the bot name during the 5 minutes could otherwise bind themselves.
5. **How free text finds its question.** Options: any bare text answers the only open question; reply to the question message, or `<id> text`. Picked: reply or id. A bare message is ambiguous when two questions are open and you may just be chatting; you get a one line hint instead.
6. **Several runs side by side share one bot.** Options: each run calls getUpdates (they conflict and confirm each other's updates away); one fetcher under a file lock writing a shared log each run reads. Picked: the shared log (AC-6). The cursor and dedupe in `run.py` keep working on log ids.
7. **Short or long polls in the runner.** Options: long poll (`timeout` 25); `timeout` 0 every 15 s. Picked: `timeout` 0 in `wf run`, so a poll never blocks the run loop and Ctrl C stops within a slice (spec 0005 AC-9); long polling only in `wf telegram init` and `test`, where you wait anyway. Still getUpdates, no webhook and no public server, as asked. Answers arrive within 15 s, same as ntfy.
8. **How many buttons.** Options: 3 (ntfy's limit); every option. Picked: every option, one per row; Telegram has no such limit.
9. **Message length.** Options: keep spec 0005's 140 character question; use the room. Picked: question 1000, label 200, still first line only and scrubbed of paths, code and block listed names: Telegram's servers are a third party just like ntfy.sh.
10. **Long reports.** Options: cut; split; split then a file. Picked: one message to 4096, split up to 3 messages, beyond that a short message plus a `.txt` file of the same scrubbed text. The file is never the local `report.txt` (real names and paths).
11. **Formatting.** Options: MarkdownV2 or HTML; plain text. Picked: plain text. Markdown escaping of feature names and questions is a bug class with no gain.
12. **Acks.** Picked: the `<id> accepted` message stays, sent silently (`disable_notification`). Removing the buttons after an answer is skipped; a late tap is counted `ignored` as today.
13. **Token entry.** Options: argument, environment, prompt. Picked: `getpass` prompt, so it never lands in shell history or a process list.
14. **Module shape.** Options: a channel interface with two classes; a second module with the same names that `run.py` holds as `self.phone`. Picked: the second module, fewest edits in `run.py`.
