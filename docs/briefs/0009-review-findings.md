# Brief: spec 0009 security review findings (2026-10-12)

## Agreed so far, do not ask again

- Steps 1 to 6 of spec 0009 are built (`c4eec49`, step 5 commit after it). Code matches AC-1 to AC-10 as written.
- Spec 0009 Threat model: a door found after acceptance goes to a new `/architect` run, not into the build. So the three findings below were not patched in the build.
- Settled by `/architect` 2026-10-12, now in spec 0009 (amendment "review findings 1 to 7"): fix 1, 2, 3, 5, 7; 4 accepted with the AC-8 prompt reworded; 6 accepted (P11: no download saved); app network stays open. No further hardening rounds. Build fixes, rerun P2 to P11, then P8 and P9.
- Open build work: P8 and P9 through `wf run` (step 7). Hold them until `/architect` settles the findings, since a jail or MCP change reruns P2 to P9 anyway.

## Findings (background security review of `c4eec49`)

1. High, sandbox escape. `jail_argv()` (`runner/run.py`) re-binds read only only `<repo>/.claude` and the common dir's `config` and `hooks`, as AC-3 lists. The calls' deny set (`deny_paths()`) is wider: a linked worktree's `.git` pointer, its real path, `commondir`, `gitdir`, `config.worktree`, git include targets, hook token scripts, writable `PATH` dirs. `app start` runs repo code a call can edit (`package.json` scripts), so a prompt injected call can reach those paths through the app. The next unsandboxed git (wf's own `snapshot()`, `test_base()`, or yours) then runs it. The review's fix: build the jail's read only list from the frozen `deny_paths`, and run `files_changed()` right after `stop_app()`.
2. Medium, sandbox escape. The jail has no network limit (accepted in the spec as "no credentials"), but `call_env()` keeps `CLAUDE_CODE_OAUTH_TOKEN`, the jail can read `~/.config/wf` (ntfy topic and one time codes) and the wf state dir, and it can reach the forge hosts calls are denied. The review's fix: `--unshare-net` with a localhost bridge, or the same proxy and deny list; strip the token from the app env; hide `~/.config/wf` and the state dir in `JAIL_HIDDEN`.
3. Medium, untrusted code run. `npx -y chrome-devtools-mcp@1.10.1` prefers a matching package in the current project (npm docs, not probed). The AC-2 `--version` check runs in wf's cwd, and the MCP itself is started by claude in the repo. A call planted `node_modules/chrome-devtools-mcp` would run outside every sandbox. The review's fix: a wf owned cwd (or `--prefix`) for every npx run. The MCP's cwd is set by Claude Code, so this needs a probe of what the MCP config can control.

## Findings (background security review of the step 5 commit)

4. Medium, loopback reach. Chromium sends localhost, 127.0.0.1 and [::1] direct and skips the proxy, so the browser (outside every sandbox) reaches any loopback port, through app JS, `evaluate_script`, a clicked link, or a redirect. The spec already accepts "the browser can reach other services on your loopback" as residual. But the AC-8 prompt sentence ("the browser can reach only that address") states more than is enforced. The reviewers' fix: `--chromeArg=--proxy-bypass-list=<-loopback>` plus a direct path for the app origin only (host resolver rules, PAC, or a forwarding proxy). Needs a probe.
5. Medium, parser differential in `BROWSER_GUARD`. `http://localhost:22\@localhost:3000/`: Python `urlsplit` reads host `localhost:3000` (allowed), but Chrome treats `\` as `/` and goes to `localhost:22`. Impact is the same loopback reach as 4. The reviewer's fix: reject URLs containing `\`, `@`, whitespace or control characters before parsing. A local fix, but it changes AC-7.
6. Medium, unguarded file write. A click on a download link (or a Content-Disposition response) saves to Brave's default download folder (`~/Downloads`), outside the shots dir. No download policy is set in `MCP_BROWSER`. The reviewer's fix: point the download folder at the shots dir, or deny downloads (CDP `Browser.setDownloadBehavior`). Needs a probe of what chrome-devtools-mcp 1.10.1 and Brave honor.

7. High, symlink swap after the check. `BROWSER_GUARD` checks `os.path.realpath(v)`, but the MCP (outside every sandbox) opens the original string later. A path through a repo symlink that points into shots passes the check. A sandboxed call or the jailed app can then swap the link to `.git/hooks` or a dotfile folder before the MCP writes. `take_snapshot` and `get_network_request` write content the app controls, so this is an unsandboxed arbitrary file write. The reviewer's fix: require each path to be absolute, already normalized (`os.path.normpath(v) == v`), lexically under shots, and equal to its own realpath (no symlink anywhere in it), since nothing but the MCP can write shots. Local to AC-7, testable without a probe.

## For /architect

Decide per finding: fix in spec 0009 (amend AC-2 to AC-4, AC-7, AC-8) or accept as residual. Findings 3, 4 and 6 need a probe before accept (`rules/spec-gate.md`). The spec's Threat model guards accidental or prompt injected leaks, not a model working to escape; findings 1, 3, 5 and 6 are reachable by a prompt injected call, so they sit inside it.
