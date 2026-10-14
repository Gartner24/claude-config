# 0038 · Styled Telegram messages

**Status**: Accepted
**Date**: 2026-10-14
**Paths:** `runner/telegram.py`, `runner/tests/test_telegram.py`
**Amends**: [0029](../0029-telegram/index.md) AC-4 (the question message), [0033](../0033-context-in-messages/index.md) AC-4 (the from: block)

## What you're agreeing to
- Telegram questions get real formatting: the question's name and the question in bold, the learn line in italics, links you can tap, and the step's own unverified words in a quote you can expand.
- Every piece of text that goes in is escaped first, so text from a step, a repo or GitHub can never add its own formatting or a link that hides where it goes.
- ntfy, the reports and your typed or swiped replies work exactly as before.

## Acceptance criteria
Today: `telegram.Topic.ping` sends plain text with no `parse_mode` (`runner/telegram.py:257-281`); the from: block is plain `key: value` lines (`runner/context.py` `telegram_block`).

- **AC-1** (HTML mode): question messages are sent with `parse_mode: HTML`. Every inserted value (question, learn, every from: line, option labels, the reply hint, the title) is escaped with `html.escape(..., quote=True)` before any tag is added. The only tags are the runner's own: `<b>`, `<i>`, `<a href>`, `<blockquote expandable>`.
- **AC-2** (layout): first line `<b>Question <id> (its name, so your reply finds it):</b>`; the question in `<b>`; the learn line in `<i>`; `from:` in `<b>`; a from: line whose value is a runner built `https://` link (spec, issue, PR) becomes `<key>: <a href="<escaped url>"><escaped url></a>`, so the link shown is the link opened; the `what the step said, unverified:` part goes in `<blockquote expandable>`; the options and reply hint stay plain lines.
- **AC-3** (length): the 4096 limit applies to the visible text, as before; the room for the from: block is computed on the unescaped text, as today.
- **AC-4** (replies unchanged): `d["sent"]` stays the plain text, so swiped replies (`telegram.ASKED`), the queue and the report read the same text as before.
- **AC-5** (fallback): when Telegram refuses the HTML (`can't parse entities`), the same message goes once more as plain text.
- **AC-6** (scope): reports, acks and ntfy are unchanged.

## Build plan
1. `telegram.py`: an `html_body(lines)` builder over the plain lines `ping` already makes; `publish` takes `parse_mode` and retries plain on a parse error.
2. Tests: an injected `<a href=...>`, `<b>` and `&` in the question, a from: line and an option reach Telegram escaped; a runner link is a real anchor whose text equals its href; `d["sent"]` stays plain; the plain retry.
