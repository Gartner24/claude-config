# 0009. Headless verify and test for `wf run`

**Date**: 2026-10-12
**Status**: In Progress

## Summary

In a `wf run`, `/check verify` today has no browser and no app it can reach, so it reports BLOCKED. `/test` only looks at uncommitted files, so it misses work that was already committed. With this spec, `wf` starts your app itself, in its own jail (a `bwrap` sandbox that hides your keys and agent sockets but shares localhost). Verify and debug calls then get a throwaway headless Brave through the chrome-devtools MCP, and that browser can only reach your app. `/test` is told the feature's changes are everything on the branch since it left `main`.

## What you're agreeing to

- You add `app start` and `app url` to a repo's `## Standing answers` once. Without them, verify works as it does today.
- `wf` runs your app jailed during each verify and debug call: it cannot read your keys or reach your ssh or gpg agent, and can only write inside the repo (minus its settings and git hooks) and the caches.
- The browser is a fresh headless Brave with no cookies, it can only reach your app's local address, and it can only write files into the run folder. Fonts or scripts from the web do not load during verify.
- `/test` covers every file changed on the branch since your local `main` (or `master`), so a branch holding several features tests them all.
- Build step 1 runs probes P2 to P7 before any other code; if any fails, the build stops and the spec goes back to /architect.

## Threat model

Guarded: an accidental or prompt injected leak or push from the app or the browser that a run starts, whatever tool or spelling it reaches for first. Not guarded: a model actively working to escape (a `bwrap` or Chrome bug, a door not named here). The residual risks are listed once under Security model and accepted. There are no further hardening rounds on this feature; a new door found later goes to a new `/architect` run, not into the build.

## Requirements

**User stories**:
- As you, I want an overnight `/check verify` to really drive my app in a browser, so that a Beta feature can pass verify without me, and only a login, captcha, 2FA or hardware stops it.
- As you, I want `/test` to see the whole feature even after checkpoint commits, so that it never asks "No changes" in the middle of the night.
- As you, I want the browser and the app a run starts to reach nothing of mine (keys, agent sockets, logged in sessions, other sites, my dotfiles), so that the push guard of spec 0007 still holds.

**Acceptance criteria**:
- **AC-1** (standing answer keys): spec 0006 AC-2 gains two keys. `app start`: the command that starts your app, any text (spaces allowed), kept exactly as written, never case folded. `app url`: `http://` or `https://`, host `localhost`, `127.0.0.1` or `[::1]`, an explicit port from 1 to 65535, an optional path, no whitespace, kept as written. The entry pattern becomes `^\s*[-*]\s+([^:]+?)\s*:\s*(\S.*?)\s*$`; `run suite` and `done` keep exactly their spec 0006 values and folding. A repeated app key refuses like any repeated key (spec 0006 AC-3). `wf run` refuses `bad_answers` (spec 0006 AC-3 path and detail form) when only one of the two keys is present (`app start and app url go together`) or when `app url` breaks the form above (`app url must be http(s)://localhost|127.0.0.1|[::1]:<port 1-65535>`). The `expected:` hint in the detail lists the two new keys. No app keys means no app and no browser for any call.
- **AC-2** (start checks): when the app keys are present, `start_checks()`, right after the standing answers check, resolves `npx` and `brave` with `shutil.which` then `os.path.realpath` (spec 0007 AC-6 style), then runs `<npx> -y <MCP_PACKAGE> --version` with `call_env()` and a 120 s timeout. A missing binary, a non zero exit or a timeout refuses `no_browser` (exit 5, the `refuse()` path, no lock, no call), detail `npx`, `brave` or `mcp: <first stderr line>`. `bwrap` is already required by spec 0007 AC-8.
- **AC-3** (app jail): a browser call is a call of kind `debug`, or a box call whose command starts with `/check verify`, in a repo with the app keys. Before its first attempt, and again before each resume, `wf`:
  1. takes the spec 0008 AC-3 debug guard snapshot first, for a debug call (the app starts after it).
  2. requests `app url`. Any HTTP answer stops the run `app_port_busy`, detail `something already answers at <app url>` (a stop in spec 0008 AC-1, since every later feature would hit it too).
  3. starts `<bwrap> --die-with-parent --unshare-pid --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --tmpfs /run`. Then `--bind <p> <p>` for each existing path in: the repo, `~/.npm`, `~/.cache`, `~/.local/share/pnpm`. Then `--ro-bind <p> <p>` for each existing path in the repo's write deny set: `<repo>/.claude`, the git common dir's `config` and `hooks`. Then `--tmpfs <d>` for each existing directory and `--ro-bind /dev/null <f>` for each existing file in `JAIL_HIDDEN`: `~/.ssh`, `~/.config/gh`, `~/.git-credentials`, `~/.netrc`, `~/.aws`, `~/.config/gcloud`, `~/.azure`, `~/.gnupg`, `~/.claude/.credentials.json`, `~/.config/BraveSoftware`. Then `--chdir <repo> /bin/sh -c <app start>`. It runs with `call_env()` (specs 0007, 0008, plus `WF_RUN`, AC-3 step 6), `start_new_session=True`, stdin `/dev/null`, stdout and stderr to `<run folder>/app-NN.log` (`NN` is the call's `seq`; a resume's restart appends `-rK`, K counting from 1). The network is shared, so the app is on your real localhost.
  4. polls `app url` (a GET, 2 s timeout) every 0.5 s. The first answer with a status below 500 means ready; a 5xx is polled again. If the process exits first, park `app_failed`, detail `app exited <code>: <tail>`. With no ready answer after `APP_READY` (120 s), park `app_failed`, detail `not ready at <app url> after 120 s (last status <n or none>): <tail>`. `<tail>` is the last 20 lines of the log through `clean()`, first 1000 characters. A park stops the app first. The readiness time counts toward the run's wall clock (`--max-hours`) but not toward the call's timeout (that clock starts after ready) or `--max-calls`.
  5. keeps the app through the call's retry (spec 0008 AC-6, same app, same log) and a usage limit wait. It stops the app when a decision wait starts (spec 0005), and restarts it through steps 2 to 4 before the resume. The app is stopped when the call is finished, after a park, and in `cleanup()` on every exit path. A debug call's after snapshot (spec 0008 AC-3) is taken only after the app has stopped.
  6. Stopping: `call_env()` carries `WF_RUN=<run id>` for every call and the app. On a stop, `wf` sends SIGTERM to the claude call's process group (when one is running) and the app's process group together, waits one shared `GRACE`, then sends SIGKILL to both. After every browser call and in `cleanup()`, it scans `/proc/*/environ` for processes of its own user carrying `WF_RUN=<run id>` (leftover Brave, the MCP's node process) and sends SIGKILL to each. `app_failed` is a park and `app_port_busy` a stop in spec 0008 AC-1.
- **AC-4** (browser MCP): a browser call and its retry and resumes get `--strict-mcp-config --mcp-config <MCP_BROWSER>` instead of spec 0007's empty `MCP_ALLOW`, and `--allowedTools` listing `mcp__chrome-devtools__<tool>` for every tool in `BROWSER_TOOLS` (the 1.10.1 tool list recorded in `verify.md` by P3, minus the AC-6 six). `MCP_BROWSER` is built at start: `{"mcpServers": {"chrome-devtools": {"type": "stdio", "command": <npx path>, "args": ["-y", "chrome-devtools-mcp@1.10.1", "--isolated", "--headless", "--executablePath", <brave path>, "--proxyServer", "127.0.0.1:9", "--chromeArg=--force-webrtc-ip-handling-policy=disable_non_proxied_udp", "--chromeArg=--disable-quic", "--no-usage-statistics", "--no-performance-crux"]}}}`. Every other call keeps `MCP_ALLOW`. The version is pinned; raising it reruns P2 to P7 and changes this AC.
- **AC-5** (no attaching): the argv test reads the `MCP_BROWSER` args and fails unless they contain `--isolated`, `--headless`, `--proxyServer` and exactly one `chrome-devtools-mcp@<digits>.<digits>.<digits>` package, every `--chromeArg` is one of the two in AC-4, and none of `--browserUrl`, `--browser-url`, `-u`, `--wsEndpoint`, `--ws-endpoint`, `-w`, `--autoConnect`, `--auto-connect`, `--userDataDir`, `--user-data-dir`, `--channel`, or any `@latest` appears.
- **AC-6** (tool denies): a browser call's `--disallowedTools` adds `mcp__chrome-devtools__upload_file`, `mcp__chrome-devtools__take_heapsnapshot`, `mcp__chrome-devtools__performance_start_trace`, `mcp__chrome-devtools__performance_stop_trace`, `mcp__chrome-devtools__performance_analyze_insight`, `mcp__chrome-devtools__lighthouse_audit`.
- **AC-7** (browser hook): a browser call's inline `--settings` (spec 0007 AC-2) adds a second `PreToolUse` entry: matcher `mcp__chrome-devtools__.*`, `"type": "command"`, `"timeout": 10`, `"command": "<python3> -c '<BROWSER_GUARD>' <quoted app url> <quoted shots dir> || exit 2"`, where the shots dir is `<run folder>/shots/` (created by `wf` at start). `BROWSER_GUARD` is a constant in `runner/run.py` and fails closed. It exits 0 only when stdin parses as JSON, `tool_name` starts with `mcp__chrome-devtools__`, `tool_input` is an object, and all of these hold:
  - for `navigate_page` and `new_page`: either the tool is `navigate_page`, `url` is absent and `type` is `reload`, or `url` is a string whose origin equals the `app url` origin. An origin is the lower cased scheme, the lower cased host, and the port (the scheme's default when none is given), from `urllib.parse.urlsplit`. `http://localhost:3000.evil.example`, `file://` and `chrome://` do not match.
  - for any tool: every `tool_input` value whose key ends in `path` or `Path` (case kept, for example `filePath`, `requestFilePath`, `responseFilePath`) is a string whose `os.path.realpath` lies under the shots dir's real path.
  In every other case, any exception included, it prints `wf run: browser tool call refused` and the reason to stderr and exits 2.
- **AC-8** (prompt): a browser call's `--append-system-prompt` adds, after the spec 0006 text: ` wf started the app at <app url> and stops it after this step; do not start, stop or restart it. Drive it with the chrome-devtools tools; the browser can reach only that address. Save any file a browser tool writes under <shots dir>, or leave its path out. Anything you start from Bash runs in a separate sandbox the browser cannot reach. If no chrome-devtools tool is available, end with BLOCKED: browser tools unavailable. Otherwise end with BLOCKED only for a login, captcha, 2FA or hardware.` Calls without an app get no new text.
- **AC-9** (/test base): right before each box call whose command's first word is `/test` (its retry and resumes reuse the value), `wf` finds the base: the first of `main`, `master` for which `<git> rev-parse --verify --quiet refs/heads/<b>` succeeds, then `<git> merge-base HEAD <b>`, both with the absolute `git` from spec 0007 AC-6. If either step fails, there is no base. With a base, the prompt adds: ` For /test, the feature's changes are the files in git diff --name-only --diff-filter=ACMR <sha> plus the untracked files from git ls-files --others --exclude-standard; use that list as the changed files instead of uncommitted files only.` With no base, nothing is added (today's behaviour). Accepted limit: the base is the local branch, so a stale local `main`, or a branch cut from another feature branch, widens the list; more than 15 files then brings `/test`'s scope question as a ping.
- **AC-10** (record): each call record gets `app` and `test_base`. `app` is null on a call that is not a browser call, else `{"url", "logs", "ready_s", "exit"}`: `logs` the log file names in start order, `ready_s` the first start's readiness time in seconds rounded to 0.1, `exit` the last app process's exit code once stopped (null while it runs). A retry and its resumes carry the same object. `test_base` is the sha or null. The confirm line and `run.json` `answers` show the two keys through spec 0006 AC-7, for example `answers: run suite yes, app start npm run dev, app url http://localhost:3000`.
- **AC-11** (probes): `verify.md` records P1 (run 2026-10-12: sandboxed Bash and the host do not share localhost) and P2 to P9 with command and result. With a hand built argv and env:
  - P2: a jailed app answers at `app url` from the host. Inside the jail, `cat ~/.ssh/<any file>` fails, `touch ~/probe-wf` fails, `touch <repo>/probe` succeeds, writing `<repo>/.git/hooks/probe` and `<repo>/.claude/settings.json` fails, and connecting to `$XDG_RUNTIME_DIR/gnupg` or any ssh agent socket path from your session fails.
  - P3: a browser call lists the `mcp__chrome-devtools__` tools (the list saved as `BROWSER_TOOLS`), makes one real `new_page` to `app url` and one `take_snapshot` with no prompt or denial, no Brave window appears, and the profile has none of your Brave cookies.
  - P4: `navigate_page` to `https://github.com`, `file:///etc/passwd`, `chrome://settings` and `http://localhost:<port>.evil.example` is refused; to `app url` and `reload` it is allowed.
  - P5: inside the app page, `evaluate_script` running `fetch('https://example.com')` fails, a click on a link to `https://example.com` does not load it, and a `new RTCPeerConnection` with a public STUN server gathers no `srflx` candidate.
  - P6: `upload_file` and the five other AC-6 tools are denied. P6b: `take_snapshot` and `take_screenshot` with `filePath` `~/probe-wf` are refused, and with a path under the shots dir they succeed.
  - P7: `BROWSER_GUARD` run directly with malformed JSON, empty stdin, a foreign origin, a path outside the shots dir, and the app origin exits 2, 2, 2, 2, 0.
  Through `wf run` on a scratch repo: P8, a `/test` box after a checkpoint commit tests the committed files with no `No changes` question; P9, a Beta feature on a small scratch web app passes `/check verify` (PASS, screenshots cited) and `/test`, and ends `feature_done` with no leftover Brave, node or app process. If P2 to P7 fail, this spec goes back to `/architect` before the build continues. P2 to P9 run again after each Claude Code upgrade and each `MCP_BROWSER` version change.

## Decision

**Chosen option**: Option 1: `wf` starts the app in its own `bwrap` jail on the shared localhost, and only verify and debug calls get a locked down chrome-devtools MCP.

`/test` gets the branch base from `wf` in the prompt. Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (no new storage):
- Standing answers (spec 0006): `app start` (text) and `app url` (local URL), both or neither, frozen at start.
- `Run`: `browser` (null, or `{"start", "url", "npx", "brave", "shots"}` resolved at start), `mcp_browser` (the AC-4 JSON string), the running app (`Popen` or null), `run_id` for `WF_RUN`.
- Call record: `app`, `test_base` (AC-10). Run folder: `app-NN[-rK].log`, `shots/`.

**State transitions** (one browser call):
`snapshot (debug only)` -> `check port` -> `starting` -> `ready` -> call (retry, limit wait) -> `stopped` -> `sweep`. A decision wait goes `stopped` -> wait -> `check port` -> `starting` -> `ready` -> resume. From `check port`, a busy port stops the run. From `starting`, a failure parks `app_failed` (the app is stopped first). Any run exit goes through `stopped` and `sweep` in `cleanup()`.

**API surface** (CLI and argv only):
| Surface | Inputs | Output | Errors |
|---|---|---|---|
| `wf run <repo>` start | standing answers, `PATH`, the npm registry | `answers:` part shows the app keys | `refused: bad_answers: ...` or `refused: no_browser: <npx, brave or mcp: ...>`, exit 5 |
| browser call | `app start`, `app url`, frozen guard | jailed app, logs, AC-4 MCP flags and allowed tools, AC-6 denies, AC-7 hook, AC-8 prompt | park `app_failed: <detail>`, stop `app_port_busy: <detail>` |
| `/test` call | `HEAD`, `main` or `master` | AC-9 prompt sentence, `test_base` | none (no base adds nothing) |
| `BROWSER_GUARD` hook | hook JSON on stdin, `app url` and shots dir as argv | exit 0, or exit 2 and the refusal on stderr | |

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| start | app command, app url | `## Standing answers` keys `app start`, `app url` (AC-1), frozen at start |
| start | `npx`, `brave`, `bwrap`, `python3` paths | `shutil.which` plus `realpath` (AC-2, spec 0007 AC-6) |
| start | MCP reachable | `<npx> -y <MCP_PACKAGE> --version` exit code, 120 s timeout |
| browser call | is it one | call kind `debug`, or box command starting with `/check verify`, and the app keys present |
| app jail | write binds | repo path plus `~/.npm`, `~/.cache`, `~/.local/share/pnpm` |
| app jail | read only over the binds | `<repo>/.claude`, git common dir `config` and `hooks` (`git rev-parse --path-format=absolute --git-common-dir`) |
| app jail | hidden paths | `JAIL_HIDDEN`: spec 0007 AC-1 credential paths, spec 0008 AC-7 cloud paths, `~/.gnupg`, `~/.claude/.credentials.json`, `~/.config/BraveSoftware`; plus `/run` and `/tmp` as tmpfs |
| app jail | env | `call_env()` (specs 0007, 0008) plus `WF_RUN` |
| app jail | log path | run folder, the call's `seq`, `-rK` per resume restart |
| readiness | ready or not | first answer below 500 at `app url`; `APP_READY` 120 s, poll 0.5 s, request timeout 2 s (constants) |
| `app_failed` | tail, last status | last 20 log lines through `clean()`, first 1000 characters; the last HTTP status seen or `none` |
| sweep | leftovers | `/proc/*/environ` holding `WF_RUN=<run id>`, owned by `wf`'s user |
| MCP | package version | `chrome-devtools-mcp@1.10.1`, pinned constant, read from npm on 2026-10-12 |
| MCP | allowed tools | `BROWSER_TOOLS`, the 1.10.1 tool list from P3 minus the AC-6 six |
| MCP | proxy | constant `127.0.0.1:9` (nothing listens there; loopback skips the proxy in Chrome) |
| hook | allowed origin | `urlsplit(app url)`: scheme, host, port or the scheme's default |
| hook | allowed write folder | `<run folder>/shots/`, real path |
| `/test` | base sha | `git merge-base HEAD <main or master>` with the absolute `git` |

**Constants** (in `runner/run.py`): `MCP_PACKAGE = "chrome-devtools-mcp@1.10.1"`, `DEAD_PROXY = "127.0.0.1:9"`, `APP_READY = 120`, `BROWSER_TOOLS`, `BROWSER_DENIED` (the AC-6 names), `BROWSER_GUARD`, `JAIL_HIDDEN`. The credential and cloud paths in `JAIL_HIDDEN` come from the one list specs 0007 and 0008 already use, not a copy.

**Key invariants**:
- No call reaches the app or the browser unless the repo's standing answers name the app. A call without a browser gets exactly what specs 0006 to 0008 give it.
- The app never runs outside the jail, never runs during a decision wait, never outlives its call, and never outlives the run.
- The browser never attaches to your running Brave, never keeps a profile, never loads anything but loopback addresses, and never writes outside the shots dir.
- After a run ends, no process carrying its `WF_RUN` is left.
- `wf` still writes nothing in a repo. The app may write in the repo outside `.claude` and git config and hooks, as the calls already do.

**Security model**: The app is repo code that unattended calls may have written, so it gets the same bar as a call. It sees no credential (env stripped, key, token and real browser profile paths hidden, `/run` agent sockets gone), cannot write outside the repo and the caches, cannot touch the repo's settings, git config or hooks, and shares only the network. With nothing to log in with, it cannot push (spec 0007 threat model). The browser runs outside the Bash sandbox, so it is locked at four levels: a throwaway profile (no cookies or sessions), a dead proxy that only loopback skips with WebRTC UDP and QUIC off (no other host, IP literals included, whatever opened the request), the hook on every browser tool (navigation only to the app origin, file writes only into the shots dir), and tool denies (no local file uploads, no profiling dumps). Residual, accepted (see Threat model): the app can reach any host over the shared network (no credentials, same as spec 0007's IP literal residual); the browser can reach other services on your loopback (another dev server, a local database admin page); a Chrome or `bwrap` escape.

**Configuration required**: per repo, by hand, in `## Standing answers`:
- `- app start: <command>` for example `npm run dev`
- `- app url: http://localhost:<port>`

**Critical test scenarios**:
- Keys: both keys parse with spaces in `app start` and keep their case; one key alone, a remote host, no port, port 0 and 70000, `ftp://`, a space in `app url`, and a repeated `app url` each refuse `bad_answers` with the right detail; `run suite` and `done` parse as before; no keys means no browser call, verifies **AC-1**
- Start: app keys with no `brave` on `PATH`, and a fake `npx` that exits 1 for `--version`, each refuse `no_browser` exit 5 with no lock; without app keys neither is checked, verifies **AC-2**
- Jail argv: a fake home with `~/.ssh`, `~/.netrc`, `~/.gnupg` and no `~/.aws`, and a repo with `.claude/` and `.git/hooks`, gives the expected bwrap argv (order, tmpfs for existing dirs, `/dev/null` for files, read only binds over the repo's deny set, missing ones skipped), verifies **AC-3**
- Lifecycle: a fixture app (`python3 -m http.server`) becomes ready, the fake claude call runs, and the app's process group is gone afterwards; a decision wait stops it and the resume starts a new one with an `-r1` log; a retry keeps it; Ctrl C stops call and app within one `GRACE`; a fake leftover process carrying `WF_RUN` is killed by the sweep; a second verify call starts a new app with a new log, verifies **AC-3**
- Failures: an app that exits 1, an app that answers only 500 (patched `APP_READY`), and an app that never answers each park `app_failed` with the right detail, last status and tail, with no claude call; a port already answering stops `app_port_busy`, verifies **AC-3**
- Debug order: a debug call whose fixture app writes `tests/generated_x.py` while running does not park `debug_touched`; a snapshot taken after start would have, verifies **AC-3**
- Argv: a verify call and a debug call carry `MCP_BROWSER`, the `BROWSER_TOOLS` allowed list, the AC-6 denies and the AC-7 hook; a `/develop`, `/test` and `/sync` call carry `MCP_ALLOW` and none of them; the AC-5 checks on `MCP_BROWSER`, plus the same checks rejecting a copy with `--browserUrl`, `--user-data-dir`, a third `--chromeArg` and `@latest`, verifies **AC-4**, **AC-5**, **AC-6**
- Hook: `BROWSER_GUARD` run directly with the app origin, an upper case host, a default port form, `localhost:3000.evil.example`, another port, `file://`, `chrome://`, `reload` with no url, `back` with no url, a `url` type with no url, a `filePath` inside and outside the shots dir, a `..` path and a symlink escaping it, malformed JSON and empty stdin, verifies **AC-7**
- Prompt: a browser call's prompt ends with the AC-8 text; a verify call without app keys does not have it, verifies **AC-8**
- Base: in a temp repo with `main`, a branch, two commits and an uncommitted file, the `/test` prompt names the merge base sha; with only `master` it uses that; with neither it adds nothing and `test_base` is null, verifies **AC-9**
- Record: `app` (logs, `ready_s` rounding, `exit`, shared by a retry) and `test_base` in `run.json`, the answers part of the confirm line, verifies **AC-10**
- Real claude: P2 to P9, verifies **AC-11**

## Build plan

Skateboard: each step leaves `wf run` usable. Specs 0006, 0007 and 0008 are built first (this spec extends their key table, argv, env and park and stop sets).

1. Probe gate: run P2 to P7 with a hand built bwrap argv, MCP JSON, allowed and denied tools and hook, record them and the `BROWSER_TOOLS` list in `verify.md`. Go back to `/architect` if any fails, satisfies **AC-11**
2. `/test` base: find the base before `/test` calls, add the prompt sentence and `test_base`, with tests. This works on its own, before any browser work, satisfies **AC-9**, **AC-10**
3. App keys in the standing answers parser, the widened entry pattern, `bad_answers` details, the `no_browser` start checks including the `--version` run, with tests, satisfies **AC-1**, **AC-2**
4. App jail: argv builder, debug snapshot order, port check (`app_port_busy` stop), start, readiness, logs, stop around decision waits and on call end, `WF_RUN` and the shared `GRACE` stop and sweep in `cleanup()`, `app_failed` and `app_port_busy` added to the spec 0008 sets, with tests using a fixture app, satisfies **AC-3**, **AC-10**
5. Browser calls: `MCP_BROWSER`, `BROWSER_TOOLS` allowed list, the AC-6 denies, the `BROWSER_GUARD` hook entry and shots dir, the AC-8 prompt sentence, only on verify and debug calls with an app; the AC-5 checks in the argv test, satisfies **AC-4**, **AC-5**, **AC-6**, **AC-7**, **AC-8**
6. `app` in call records, answers part on the confirm line, with tests, satisfies **AC-10**
7. P8 and P9 through `wf run` on scratch repos, recorded in `verify.md`, satisfies **AC-11**

## Consequences

**Positive**:
- A Beta feature with a web UI can close overnight: verify drives the real app instead of reporting BLOCKED.
- `/test` no longer depends on what is committed, so checkpoint commits (feature 14) cost nothing here.
- The guard of spec 0007 still holds: neither the app nor the browser gets a credential or an agent socket, and the browser reaches only loopback.

**Negative / tradeoffs**:
- Third party assets (web fonts, CDN scripts, payment widgets, analytics) fail to load during verify. A behaviour that depends on one reports FAIL or BLOCKED, so such a feature verifies by hand.
- An app that needs a database, Docker or a second service must have those running already, or `app start` must start them inside the jail. Otherwise it parks `app_failed`. An app that writes its own `.claude` or git hooks fails in the jail.
- Restarting the app per call and per resume costs its boot time each time.
- A leftover server of yours on the app port ends the whole run (`app_port_busy`).
- `/test` on a branch with several features, or with a stale local `main`, covers more than the feature (AC-9 accepted limit).
- `/check verify`'s before and after capture (refactors) can still only reach a second app copy from Bash, over HTTP, not through the browser.
- Bound to chrome-devtools-mcp 1.10.1 behaviour, its tool names and Brave's proxy handling. A version bump reruns the probes and updates `BROWSER_TOOLS`. Each run start needs the npm registry once (the `--version` check), or the cached package.

**Neutral**:
- Amends spec 0006 (AC-2 key table, entry pattern and case rule; AC-3 hint), spec 0007 (AC-4: verify and debug calls get `MCP_BROWSER`; AC-2 settings gain the browser hook on those calls), and spec 0008 (AC-1 park set gains `app_failed`, stop set gains `app_port_busy`; AC-3 snapshot order with the app). `/develop` notes each amendment in the step that builds it.
- Architecture page: the components table gains the app jail and the browser, invariant 8 gains the 120 s readiness bound and the leftover sweep, the threat model line covers the app and browser, and the skills table row for `/check verify` says it drives the app when the repo names one.

## Follow-up

- [ ] Root `AGENTS.md` and the standing answers docs: document `app start` and `app url`; `/sync` owns this.
- [ ] `--allowedUrlPattern` (chrome-devtools-mcp, Chrome 149+, Brave 154 qualifies) could later add another layer under the dead proxy; not needed now.
- [ ] If third party assets turn out to break most verifies, revisit with an allow list of asset hosts through `--proxy-bypass-list` (a new decision, `/architect`).

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
