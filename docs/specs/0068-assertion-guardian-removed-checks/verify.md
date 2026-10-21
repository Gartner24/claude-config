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

## P2 and P3 results (run 2026-10-20, Claude Code 2.1.306)
- Probe mod: a `tool.call` hook on Bash that awaits `next(e)`, then checks `/tmp/claude-1000/p2-probe.txt` with `$.fs.exists` and `$.fs.read`, logs `$.session.cwd()`, and returns variant A `{ ...r, isError: true, text }` or variant B `{ deny: text }`. Run: `env -C /tmp/claude-1000 claude -p --plugin-dir <scratch>/p2mod --allowedTools Bash --permission-mode default "Run exactly ... # varA|varB, quote the result"`.
- The hook sees the file after the run: log `before=false after=true text="hello\n"`. P2 core: confirmed.
- Variant A (the AC-3.7 shape): Claude quoted `(Bash completed with no output)`. The `text`/`isError` on a returned core result never reach the model, as the type docs say (`text` is set by core, `ref` makes core reuse its own messages). Not usable.
- Variant B: Claude quoted `Bash ran, and a plugin withheld its result: PROBE-REFUSAL: saw the file "hello2\n"`. Confirmed: the AC-3.7 refusal is returned as `{ deny: <refusal> }` after `next`. The spec's AC-3.7 line is amended to that shape (same intent: the model gets the refusal as an error).
- `run_in_background: true`: the hook reads `e.run_in_background === true` before `next`; AC-2 refuses those before running.
- P3: `$.session.cwd()` returned `/tmp/claude-1000`, the folder the session started in (`env -C`). Confirmed. A shell `cd` inside a line is caught by AC-1's `cd` rule.
- `$.fs` has `read`, `write`, `exists`, `stat`, `list`, no delete and no mode: deleting a file that did not exist before, and the old mode of a re-created file, go through `$.process.run` (`rm -f --`, `stat -c %a`, `chmod`).

## AC-6 whole tree check and rebuild (run 2026-10-21)
- `folder_hash(~/.claude/skills/assertion-guardian)` = `folder_hash(export of upstream at ae1de89f, path ".")` = `df60aa02...`, no file only on one side. Confirmed.
- Rebuild: export of upstream at `pinned` hashes to the entry's `base_hash`, `config/patches/assertion-guardian.patch` applies, and the result equals the built scratch folder (`folder_hash` and file set). Confirmed; P4 (git archive of ".") confirmed by the same export and by `TestRestore.test_rebuild_whole_repo_mod`.

## Review round 1 probes (run 2026-10-21, Claude Code 2.1.306)
- `$.session.cwd()` after a `cd`: probe mod p2mod, call 1 `cd p3sub`, call 2 `pwd # p2-probe`; the hook logged `cwd=/tmp/claude-1000/p3sub`. The session folder follows a `cd` from an earlier call, so relative targets resolve against the folder the command runs in. Confirmed.
- `$.fs.read(path, { as: 'bytes' })` on the real engine: probe mod p7mod logged `type=object keys=base64 base64="aMOpCg=="`. `readText` reads `{ base64 }`, the real shape. Confirmed.

## AC-7 (run 2026-10-21)
- `skill-scan --against` on the first build: no new findings. After the round 1 fixes, `skill-scan static` on a fresh copy of the built mod: 0 new serious findings (a comment quoting an example `rm` command was flagged first and reworded).
- Fast suite in the worktree: 1135 tests, 0 failed.
- `claude plugin validate` on the built mod: passed. `claude plugin test`: 41 pass, 0 fail.
- Mutation checks, one mutant per new test, each red, then green on restore:
  - heredoc body not shell text: no heredoc split; body not parsed (both red).
  - `&` job refused before running: no `&` refusal (red).
  - backtick and `$(...)` target refused before running: no `$` marker for a substitution (red).
  - command inside a substitution is a target: substitution text not parsed; quoted substitution not split (both red).
  - a restore that fails is named: the catch that names "could not be put back" dropped (red).
- `tsc` not run: the engine's generated types (`.claude-plugin/types/`) are not in the scratch build.

## Review round 1 fixes (2026-10-21)
- Heredoc bodies are parsed on their own (an apostrophe in one hid later commands).
- A line with test targets and a bare `&` job is refused before running.
- A substitution stays in its word as `$`, so `` rm `pwd`/a.test.ts `` and `rm $(pwd)/a.test.ts` are refused before running (AC-1), and the commands inside a substitution are read as targets.
- New test for a restore that fails. README says which shell shapes run and are compared, and which are still refused before running.
- Patch regenerated; upstream at `pinned` plus the patch equals the built scratch folder (`folder_hash` and file set).
