# 0028 · Understand everything: plain words, and learn any idea first

**Date**: 2026-10-13
**Status**: Accepted (built 8b7fd19)
**Paths:** `claude-home/rules/plain-questions.md`, `claude-home/hooks/plain-panel.py`, `claude-home/settings.json`, `tools/bin/install.sh`, `tools/bin/sync.sh`, `_archive/runner/plain.py`, `_archive/runner/run.py`, `_archive/runner/ntfy.py`, `_archive/runner/report.py`, `_archive/runner/tests/test_plain.py`
**Amends**: [0005](../../../_archive/runner/docs/specs/0005-decision-parking-phone-pings/index.md) (the ping body gains a `learn:` line, the prompt a `LEARN:` line), [0011](../0011-build-decision-queue/index.md) (a Decision gains `learn` and `jargon`), [0018](../0018-morning-report/index.md) AC-2 and AC-4 (item words and reasons in plain words), [0021](../../../_archive/runner/docs/specs/0021-never-stop/index.md) AC-2 (case questions in plain words with a learn line).

## What you're agreeing to
- Everything Claude tells you, in chat, in question panels, in phone questions and in the morning report, uses words you can follow, and explains any new idea in a few words where it first comes up.
- Every question panel has a last choice, "Learn this first": pick it and Claude explains the idea from zero with an everyday example, then asks the same question again.
- Phone questions carry a short explanation under the question, and one choice to get a longer one before you answer.
- A small checker refuses a panel with no "Learn this first" choice, and a test fails if a runner report or phone question uses a word on the jargon list.
- Panels keep at most 3 real choices, so about 1 in 8 of today's panels (the 4 choice ones) gets split in two.

## Acceptance criteria

### The rule (sessions)
- **AC-1** (rule text): `rules/plain-questions.md` is replaced by the text in [The rule](#the-rule) below, word for word. Its title says it beats skill text and the output lines of `~/.claude/CLAUDE.md` for anything addressed to you. It covers chat replies, question panels, and prose files written for you (scope rows, briefs, "What you're agreeing to"), never code, commit messages or text another tool parses.
- **AC-2** (reaches every session): the rule reaches `~/.claude/rules/plain-questions.md` by the live step `./install.sh` (spec 0019 install shape), so it loads in every session, headless included, and survives a pull of the vendored skills. The repo file is the source; `sync.sh` already copies `rules/` back.

### Panels
- **AC-3** (the hook): `hooks/plain-panel.py`, a PreToolUse hook on `AskUserQuestion`, reads the hook JSON on stdin and checks `tool_input.questions[]`. A question passes when its last option's `label`, case folded and stripped, starts with `learn this first`, and it has at most 4 options in all (3 real ones plus that one). Any failing question denies the call (exit 2) with one stderr line per failing question: `panel: question <n>: <what is missing>; add a last option "Learn this first" (explain the ideas here from zero with an example, then ask again), split a question with more than 3 real options`. A passing panel exits 0 with no output. Input that is not that shape (no `questions` list, unparsed input) exits 0: the hook never blocks a panel it cannot read.
- **AC-4** (jargon in panels): when the runner copy's `plain.py` can be imported (the folder of `os.path.realpath(~/.local/bin/wf)`), the hook also runs `plain.jargon()` over each question's `question`, option `label` and `description` text, and a hit denies the call with `panel: question <n>: plain words: <hits>`. When it cannot be imported, this check is skipped and only AC-3 applies.
- **AC-5** (wiring): `settings.json` gains a PreToolUse entry, matcher `AskUserQuestion`, command `python3 /home/santiago/.claude/hooks/plain-panel.py`, timeout 5. `install.sh` copies `hooks/plain-panel.py` with the other copied hooks (`install.sh:36`), `sync.sh` copies it back (`sync.sh:24`, `sync.sh:43`), `NOTICE.md` lists it as authored.
- **AC-6** (self checks): `python3 hooks/plain-panel.py --test` asserts: a 2 option panel without the learn option is denied; the same panel with it passes; 4 real options plus the learn option is denied; two questions where only the second fails names question 2; unparsed input passes; a question holding `verify_failed` is denied only when `plain.py` imports.

### Runner (phone questions and reports)
- **AC-7** (`runner/plain.py`): holds `PLAIN`, a map from every reason in `run.CASES` plus `queue_done`, `decision_open` and `feature_done` to `(words, learn)`: `words` a plain phrase under 60 characters ("the checks found a bug it could not fix"), `learn` one or two plain sentences under 300 characters saying what happened and what each answer does, with an everyday example where one fits. It holds `jargon(text)`, returning the sorted distinct hits of: every `snake_case` token (`\b[a-z]+_[a-z0-9_]+\b`), `AC-\d+`, `spec \d{4}`, and each word or phrase of `WORDS` matched on word boundaries, case folded. Any whitespace separated token holding a `/` (a path or URL) is left out before matching. `WORDS` starts as: `park`, `parked`, `traceback`, `stderr`, `stdout`, `sigint`, `sigterm`, `flock`, `session id`, `exit code`, `repo stop`, `run stop`, `guard`, `cap`, `budget`, `fingerprint`, `sandbox`, `deny list`, `allow list`, `scrub`, `ntfy`. A word may be added, never removed without a spec.
- **AC-8** (the prompt): `UNATTENDED_PROMPT` (`runner/run.py:139`) gains: after the OPTION lines, one line starting `LEARN:` that explains the idea the question rests on from zero, with one everyday example, in plain words, at most 300 characters, no paths or code; and: write the question and labels in plain words, explaining any technical term in a few words.
- **AC-9** (reading it): `read_decision` (`runner/run.py:3576`) returns `(question, options, learn)`: `learn` joins the text of every `LEARN:` line after the DECISION NEEDED line (same prefix rules as `OPTION`, `runner/run.py:285`), flattened, else `None`. The Decision record and its run.json entry gain `learn` (`DECISION_FIELDS`, `ENTRY_FIELDS`, `runner/run.py:267` and `:278`); a record without it still loads.
- **AC-10** (learn this first on the phone): `ask()` (`runner/run.py:1327`) appends the option `learn this first` as the last option of every panel Decision a call asked (not of case questions, AC-12), keeping at most `MAX_OPTIONS` in all by cutting real options from the end. When that option is the answer, the resume prompt is `LEARN_PROMPT` in place of `ANSWERED + answer` (`runner/run.py:2535`): "The user asked to learn this first. Explain the idea behind your question from zero, with one everyday example, in at most 600 characters on LEARN: lines, then end with the same DECISION NEEDED and OPTION lines." The new Decision it ends with pings as usual. The resume counts as a call (spec 0005 AC-10); a resume that ends without a decision follows its spec 0021 case like any call.
- **AC-11** (ping body): `Topic.ping` (`runner/ntfy.py:249`) adds, right after the question line, `learn: <text>` when the Decision has `learn`: the text flattened to one line and passed through `scrub_field(cfg, text, 300, "")` (spec 0018 AC-4), the line left out when the result is empty. Buttons stay the first 3 options (`runner/ntfy.py:261`).
- **AC-12** (case questions): `ask_case` (`runner/run.py:1381`) builds the question as `<PLAIN words> in <feature>.` plus the detail in plain form (the F1 path keeps its `allow <path> for <repo>?` sentence) and passes `learn=PLAIN[reason][1]`, in place of `f"{reason}: {flat(detail)}"` (`runner/run.py:1387`). Case options keep their labels (`CASES`, `runner/run.py:212`).
- **AC-13** (report words): in the report, both renderings (`report.item_line`, `runner/report.py:134`, and `head`, `:103`), each reason prints as its `PLAIN` words, never as the code; item prefixes become `built:`, `stuck:` (was `parked:`), `stopped:`, `question <id>:`, `setup steps:` (was `live:`), `for you:` (was `yours:`), `no record:` stays, `did not finish:` (was `no end:`), `not started:` stays; the U10 pointer reads `(error details: <path>)`. The head counts read `<b> built, <p> stuck, <o> questions`. The codes stay in run.json and log.txt.
- **AC-14** (model text check, never blocking): `ask()` runs `plain.jargon()` over the question, options and learn text of a Decision a call asked, records the hits as `jargon` (a list, `[]` when clean) on the Decision and its run.json entry, and writes `jargon <id>: <hits>` to log.txt when any. Nothing else changes: the question is still asked.

### The corpus tests
- **AC-15** (runner corpus, `runner/tests/test_plain.py`): through the real code, never a copy of it: for every reason in `run.CASES`, the question and learn text `ask_case` builds, and the ping body `Topic.ping` builds for it (publish mocked); `report.render` over a run record holding one feature entry per reason in `run.PARKS | run.REPO_STOPS | run.RUN_STOPS`, a built feature, an open question, a live box and a waiting box, in one repo and in two, full and phone renderings. Each text goes through `plain.jargon()`; the test asserts the total hit count is 0 and on failure prints the count and every `<source>: <hits>` line. It also asserts `PLAIN` has an entry for every reason in `run.CASES`, each under its length limits.
- **AC-16** (panel corpus, live): `docs/specs/0028-understand-everything/probes/panels.py` walks every `AskUserQuestion` call in `~/.claude/projects/*/*.jsonl` whose transcript line time is after the modification time of `~/.claude/hooks/plain-panel.py`, runs the AC-3 check (imported from the repo's `hooks/plain-panel.py`) on each, prints `panels: <n>, failing: <k>` and one `<file>:<line>: question <q>` per failure (never panel text), and exits 0 only when `n > 0` and `k == 0`. With `n == 0` it prints `no panels since the hook was installed, ask one first` and exits 1.

### Never stop
- **AC-17**: nothing in this spec adds a stop. A jargon hit is recorded (AC-14), a missing `LEARN:` line pings without the line, a `learn this first` resume follows spec 0021 like any call, and a hook that crashes exits 0 (it wraps its body and lets the panel through).

## The rule

The text of `rules/plain-questions.md` (AC-1):

```
# Plain words, and learn any idea first (beats skill text)

Spec 0028 in ~/claude-config. Applies to everything you say to the user: chat replies,
question panels, and prose files written for them (scope rows, briefs, "What you're
agreeing to"). Not code, commit messages, or text another tool parses. It wins over a
skill's output style block and over the terse output lines of ~/.claude/CLAUDE.md for
anything addressed to the user.

## Plain words
- Open with one plain sentence: what happened, or what is being decided and why it matters.
- Explain a technical term in a few words where it first appears ("bwrap, a jail that
  limits what a program can touch"). No unexplained acronyms, AC numbers, spec numbers,
  reason codes or internal names.
- Short sentences, everyday words, active voice. Write for a smart person outside the field.
- Keep it short. A few words of explanation, never a lecture: the user may already know.

## Learn any idea first
- When the user says "learn X", "explain X", "what is X", or picks "Learn this first":
  stop, then explain from zero in this order: what it is in one sentence, one everyday
  example, why it matters here. Then go back to exactly where you were, and ask the same
  question again if there was one.
- Never ask "do you understand?" or quiz the user. If an answer or a follow up shows a
  mix up, explain it again a different way, with a different example.

## Question panels
- Each question opens with one plain sentence on what is decided and why it matters, then
  one short sentence for each idea the options rest on.
- At most 3 real options. Each says what the user gains and what they risk. Mark the
  recommended one and say why in one line. More than 3: split the question.
- The last option is always "Learn this first", described as "Explain the ideas here from
  zero with an example, then ask again". A hook refuses a panel without it.

## Under wf run (no panels)
- After the OPTION lines, add one LEARN: line: the idea behind the question, from zero,
  with one everyday example, at most 300 characters, no paths or code.
```

## Build plan
1. `runner/plain.py` (`PLAIN`, `WORDS`, `jargon`) and `runner/tests/test_plain.py`, red first: satisfies **AC-7**, **AC-15**.
2. Runner wiring: prompt line, `read_decision` learn, `ask()` learn option, `LEARN_PROMPT` resume, jargon record, `ask_case` plain question, ping `learn:` line, report words. Update the existing tests that assert the old report words and case question text (`test_report.py`, `test_never_stop.py`): satisfies **AC-8** to **AC-14**, **AC-17**, and **AC-15** goes green.
3. `hooks/plain-panel.py` with `--test`, the settings entry, `install.sh`, `sync.sh`, `NOTICE.md`, the AGENTS.md command line for the self check: satisfies **AC-3** to **AC-6**.
4. `rules/plain-questions.md` repo copy (a copy file: never run `./sync.sh` before the live step, or it overwrites it): satisfies **AC-1**.
5. `docs/specs/0028-understand-everything/probes/panels.py` and `probes/learn-line.py` (P2): satisfies **AC-16**.
6. Live steps, one per box, each ` · waits on you · live`: `./install.sh`, `python3 docs/specs/0028-understand-everything/probes/learn-line.py`, then later `python3 docs/specs/0028-understand-everything/probes/panels.py` (it needs at least one panel asked after the install). One human box without ` · live`: in a fresh session, ask for a two option panel and see it refused, then shown with "Learn this first"; pick it and see the explanation and the same question again (P3). Satisfies **AC-2**, **AC-16**.

## Probes
- **P1** (ran 2026-10-13, read only, no claude call): `python3 -I docs/specs/0028-understand-everything/probes/panel-shape.py`. Result in [verify.md](verify.md): panels are `{"questions": [{"question", "header", "multiSelect", "options": [{"label", "description", "preview"?}]}]}`; 953 questions, 2 to 4 options each, 126 with 4; 1 option starting "learn" or "explain". AC-3 reads that shape.
- **P2** (before step 2 lands, calls the real claude, run by `wf` as a live step, never by an unattended call): `python3 docs/specs/0028-understand-everything/probes/learn-line.py` runs `claude -p` in a temp folder with `run.unattended_prompt` and a task that must end in a decision ("ask which of two database engines to use"), then passes when `read_decision` returns options and a `learn` of at most 300 characters with no `plain.jargon` hits. It sends no ping.
- **P3** (manual, interactive, ` · waits on you`): a PreToolUse exit 2 on `AskUserQuestion` reaches the model in an interactive session and it asks again with the fix (spec 0005 dropped its hook on this tool before it was ever seen firing, its rationale "Revision 2026-10-11"). If it does not, AC-3 falls back to the rule alone and the hook is removed; say so in verify.md.

## Follow-up
- [ ] The `wf` screen and `wf queue` lines (`runner/wf.py`) through the same word list; out of scope here, the request named reports and phone questions.
- [ ] If P3 shows the hook cannot deny `AskUserQuestion`, reopen AC-3 with `/architect understand everything`.
