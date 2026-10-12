# Brief: spec 0009 security review findings (2026-10-12)

## Agreed so far, do not ask again

- Steps 1 to 6 of spec 0009 are built (`c4eec49`, step 5 commit after it). Code matches AC-1 to AC-10 as written.
- Spec 0009 Threat model: a door found after acceptance goes to a new `/architect` run, not into the build. So the three findings below were not patched in the build.
- Open build work: P8 and P9 through `wf run` (step 7). Hold them until `/architect` settles the findings, since a jail or MCP change reruns P2 to P9 anyway.

## Findings (background security review of `c4eec49`)

1. High, sandbox escape. `jail_argv()` (`runner/run.py`) re-binds read only only `<repo>/.claude` and the common dir's `config` and `hooks`, as AC-3 lists. The calls' deny set (`deny_paths()`) is wider: a linked worktree's `.git` pointer, its real path, `commondir`, `gitdir`, `config.worktree`, git include targets, hook token scripts, writable `PATH` dirs. `app start` runs repo code a call can edit (`package.json` scripts), so a prompt injected call can reach those paths through the app. The next unsandboxed git (wf's own `snapshot()`, `test_base()`, or yours) then runs it. The review's fix: build the jail's read only list from the frozen `deny_paths`, and run `files_changed()` right after `stop_app()`.
2. Medium, sandbox escape. The jail has no network limit (accepted in the spec as "no credentials"), but `call_env()` keeps `CLAUDE_CODE_OAUTH_TOKEN`, the jail can read `~/.config/wf` (ntfy topic and one time codes) and the wf state dir, and it can reach the forge hosts calls are denied. The review's fix: `--unshare-net` with a localhost bridge, or the same proxy and deny list; strip the token from the app env; hide `~/.config/wf` and the state dir in `JAIL_HIDDEN`.
3. Medium, untrusted code run. `npx -y chrome-devtools-mcp@1.10.1` prefers a matching package in the current project (npm docs, not probed). The AC-2 `--version` check runs in wf's cwd, and the MCP itself is started by claude in the repo. A call planted `node_modules/chrome-devtools-mcp` would run outside every sandbox. The review's fix: a wf owned cwd (or `--prefix`) for every npx run. The MCP's cwd is set by Claude Code, so this needs a probe of what the MCP config can control.

## For /architect

Decide per finding: fix in spec 0009 (amend AC-3, AC-2, AC-4) or accept as residual. Finding 3 needs a probe before accept (`rules/spec-gate.md`).
