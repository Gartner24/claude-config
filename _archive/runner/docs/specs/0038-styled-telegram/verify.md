# Verify: styled Telegram messages · spec 0038

Run on 2026-10-14 against the code at 6a24b49 (feature commit 047fb02). The driver sends real questions through
`telegram.Topic.ping` and `telegram.send_report` to a local fake Bot API (`WF_TELEGRAM_API`, the path e2e checks
use), then reads what Telegram would receive. The HTML is parsed with Python's `html.parser`, so "visible text"
means the text Telegram shows after it reads the tags.

The inputs carry injected markup: `<a href="https://evil.example">` in the question, an option and the step's own
words; `<b>`, `<i>`, `<script>` and `&` in the question, learn line, feature and options. Earlier specs' scrub
(0029, 0033) already drops path like tokens from scrubbed fields, so the checks look at what is left of each value.

## Commands
- [x] `python3 docs/specs/0038-styled-telegram/probes/verify-styled.py` -> 6 PASS lines, exit 0
- [x] `python3 docs/specs/0038-styled-telegram/probes/mutants.py` -> 8 RED lines, exit 0 (each break of a copy of
  `runner/telegram.py` turns its step red; the repo's runner is never touched)

## Steps
- [x] V1 question sent with `parse_mode: HTML`; the only tags are `b`, `i`, `a href`, `blockquote expandable`; the only
  anchors are the spec, issue and PR links; every injected `<a ...>`, `<b>`, `<i>`, `<script>`, `&` shows as text
  -> AC-1. can fail: the question or a from: line goes in unescaped (mutants 1 and 2 red)
- [x] V2 first line `<b>Question ab12 (its name, so your reply finds it):</b>`, the question in `<b>`, learn in `<i>`,
  `<b>from:</b>`; every anchor's text equals its href; `<b>what the step said, unverified:</b>` then
  `<blockquote expandable>` holding the escaped words; options, hint and title as plain lines -> AC-2.
  can fail: a link shows other text than it opens, or the quote is not collapsible (mutants 3 and 4 red)
- [x] V3 a question of 1000 visible characters of `& < > "` plus 100 issue links: the visible text stays at most 4096
  while the escaped text is over 1500 characters longer -> AC-3. can fail: the from: room ignores the limit
  (mutant 5 red, visible text over 4096)
- [x] V4 `d["sent"]` holds the raw plain text (no `&amp;`, no tags added); a reply whose `reply_to_message.text` is the
  styled message's visible text is read as `ab12 2` by `telegram.entry` -> AC-4. can fail: sent holds the escaped
  text (mutant 6 red)
- [x] V5 the fake bot refuses the HTML once with `Bad Request: can't parse entities`; the second send has no
  `parse_mode` and its text is `d["sent"]` plus the title; the ping returns a message id -> AC-5. can fail: the
  refusal is raised instead of resent plain (mutant 7 red)
- [x] V6 an ack (`publish`) and a report (`send_report`) with `<b>` and `&` go with no `parse_mode`, text unchanged;
  `runner/ntfy.py` is not in the feature commit -> AC-6. can fail: acks and reports go as HTML too (mutant 8 red)

## Acceptance-criteria coverage
- AC-1 V1 · AC-2 V2 · AC-3 V3 · AC-4 V4 · AC-5 V5 · AC-6 V6

## Not exercised here
- The scope row's "a real question arrives styled, its links open" on your phone: this session cannot read
  `~/.config/wf` and must not reach the real bot. `wf telegram test` (spec 0029) sends one question through the same
  `Topic.ping`; run it in your own terminal and look for a bold first line, tappable links and a collapsed quote.
  Telegram drawing `<blockquote expandable>` is unconfirmed until then; if it refuses the tag, V5's plain resend
  still delivers the question.

## Notes for review
- `Topic.publish` resends plain on any `ApiError` from the HTML send, not only `can't parse entities`. A network
  error therefore costs one extra plain try inside each of the three retries. Wider than AC-5 says, harmless.
