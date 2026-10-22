# 0073 probes (spec gate: outside tool behavior, run before accept)

## P1 usage endpoint answers (2026-10-22) - PASS
`python3 -B -c "import sys; sys.path.insert(0,'runner'); import usage; ..."` printed `five_hour used 5.0`, `seven_day used 9.0`, with reset times. The runner reader still works with today's login.

## P2 isolated claude -p (2026-10-22) - PASS
In an empty folder holding `pr.txt` (a two line diff with a bug):
`claude -p "<review ask; list your tools>" --model sonnet --tools Read,Grep,Glob --setting-sources user --strict-mcp-config --mcp-config '{"mcpServers":{}}' --settings '{"disableAllHooks":true}' --output-format text`
Answer: `x.py:2` bug with the fix, and `TOOLS: Glob, Grep, Read`. Only the three tools are present.

## P2b hooks really off - owed, first step of Part C
P2 did not observe hooks directly. Before building `review-isolated`, add a temporary user hook that writes a marker file, run the P2 command, and confirm no marker appears. A FAIL goes back to `/architect`.

## P2c read denies, connectors, sandbox - owed, first step of Part C
With the full AC-10 settings JSON and environment: ask the call to Read `~/.claude/.credentials.json`, Grep for `accessToken` under `~`, and Glob `~/.ssh/*`; all three must be refused. Ask it to list its tools: no `mcp__claude_ai_*` tool may appear. The call must start with the sandbox on (`failIfUnavailable: true` makes a missing sandbox a hard error, which is a FAIL to report, not to work around).

## P3 issue edit history (2026-10-22) - PASS
`gh api graphql -f query='{repository(owner:"cli",name:"cli"){issue(number:10000){title updatedAt userContentEdits(first:5){nodes{editedAt diff}} comments(first:2){nodes{createdAt author{login}}}}}}'`
returned 2 edits with `editedAt` and comment `createdAt` times.
