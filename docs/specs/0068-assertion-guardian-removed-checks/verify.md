# 0068 verify notes

## P1 installed copy equals upstream (done 2026-10-20)
- `git hash-object ~/.claude/skills/assertion-guardian/hooks/analyze.ts` = `ca09408a...`, `hooks/register.tsx` = `92276329...`; both equal the blob shas the GitHub contents API gives for github.com/ccdwyer/assertion-guardian at head `ae1de89f090f04e6353b03346541c8a9f3e696db`.
- Result: confirmed. The patch is made against that commit.

## P2 a tool.call handler sees the Bash result after the command ran (build runs it first, stops on failure)
- Evidence so far: `~/.claude/skills/loop-guard/hooks/register.ts` line 17 awaits `next(e)` and reads `r.isError` and `r.text` of the finished call. Unconfirmed for this use until run.
- Probe: a scratch mod loaded with `claude --plugin-dir <scratch>` whose `tool.call` handler, for a Bash call, awaits `next(e)`, then checks that a file the command wrote exists, and returns `{ ...r, isError: true, text: "probe: saw the file" }`. Run `echo x > /tmp/p2-probe.txt` through it. Pass: Claude receives the text "probe: saw the file" as an error result and the file exists. A fail stops the build and goes back to `/architect`.
## P3 the mod can read the session's working folder (build runs it first)
- Probe: in the same scratch mod, log which field of the `tool.call` event or `$` gives the folder a Bash call runs in (check the type file first). Pass: a field exists and matches `pwd` after a `cd`-free call. Fail: AC-1 refuses every relative target before running (no stop).

## P4 git archive of path "." exports the whole repo
- Covered by the AC-6 rebuild test.

## P2 notes
- Also record: what Claude sees for a `run_in_background: true` call (expected: `next` returns before the command ends, which is why AC-2 refuses those before running).
