# 0009 verify: probes and manual checks

Probes on the real `claude` (2.1.296). AC-11 lists the full set; each one gets its command and result here.

## P1. Sandboxed Bash and the host do not share localhost (run 2026-10-12, before acceptance)

Why: the chrome-devtools MCP runs outside the Bash sandbox, so the design depends on whether a dev server started inside a call can be reached from outside it.

Setup: a host server, `python3 -m http.server 8766 --bind 127.0.0.1`. Then, in a `mktemp -d` scratch dir:

```
claude -p '<run curl to 127.0.0.1:8766, then start python3 -m http.server 8767 --bind 127.0.0.1 in the background and sleep 30>' \
  --settings '{"sandbox": {"enabled": true, "failIfUnavailable": true, "autoAllowBashIfSandboxed": true, "allowUnsandboxedCommands": false, "network": {"allowedDomains": ["*"], "strictAllowlist": true}}}' \
  --strict-mcp-config --mcp-config '{"mcpServers": {}}' --permission-prompts none --max-budget-usd 1 --output-format json
```

While the call ran, the host polled `curl http://127.0.0.1:8767/` every 2 seconds for 60 tries.

Result:
- Inside the call: `curl 127.0.0.1:8766` printed `000 exit=7` (connection refused). The same curl from the host printed `200`.
- From the host: `127.0.0.1:8767` never answered (60 tries, all `000`) while the call slept 30 seconds with the server started (call took 49 s).
- So the sandbox has its own network namespace. A server started inside a call can only be reached from inside that call, and the browser cannot reach it.

## P2. App jail (run 2026-10-12): PASS

Command: `bash docs/specs/0009-headless-verify-test/probes/p2-jail.sh` (the AC-3 step 3 argv built by hand in a `mktemp -d` git repo, from a shell in the host network namespace, checked with `readlink /proc/self/ns/net` against a desktop process).

Result:
- A jailed `python3 -m http.server 8791 --bind 127.0.0.1` answered `200` from the host.
- Inside the jail: reading a file in `~/.ssh` refused, `touch ~/probe-wf` refused, `touch <repo>/probe` ok, `touch <git common dir>/hooks/probe` refused, writing `<repo>/.claude/settings.json` refused (`Read-only file system`), connecting to `/run/user/1000/gnupg/S.gpg-agent` and `S.gpg-agent.ssh` (the ssh agent here) refused. `~/probe-wf` absent afterwards.

## P3 to P7. Browser call (run 2026-10-12): P5 FAILS, build stopped

Command: `python3 -B docs/specs/0009-headless-verify-test/probes/p3-p7-browser.py`: one `claude -p` (2.1.296, sonnet) with the AC-4 `MCP_BROWSER` JSON, `--allowedTools mcp__chrome-devtools`, the AC-6 denies and the AC-7 hook (`run.BROWSER_GUARD`), against a plain local server on port 8792. It parses the stream-json events, so each result below is the tool's own answer, not the model's summary. Cost 0.27 USD.

- **P3: PASS.** Tool list from the init event (this is `BROWSER_TOOLS`; the six AC-6 tools do not appear at all once denied): `click, close_page, drag, emulate, evaluate_script, fill, fill_form, get_console_message, get_css_styles, get_network_request, handle_dialog, hover, list_console_messages, list_network_requests, list_pages, navigate_page, new_page, press_key, resize_page, select_page, take_screenshot, take_snapshot, type_text, wait_for`. `new_page` to the app and `take_snapshot` ran with no prompt or denial. Brave ran as `--headless=new --proxy-server=127.0.0.1:9 --user-data-dir=/tmp/puppeteer_dev_chrome_profile-...` (a throwaway profile, not `~/.config/BraveSoftware`); no window. No Brave or MCP process was left afterwards.
- **P4: PASS.** `navigate_page` to `https://github.com`, `file:///etc/passwd`, `chrome://settings` and `http://localhost:8792.evil.example/` each refused by the hook; to the app url and `reload` allowed.
- **P5: FAIL.** `fetch('https://example.com')` failed (`TypeError: Failed to fetch`) and a click on the `https://example.com/` link landed on `chrome-error://chromewebdata/`: both pass. But `new RTCPeerConnection` with `stun:stun.l.google.com:19302` gathered `["host","srflx"]`: a server reflexive candidate, so UDP reached a public STUN server through `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`. The page can learn your public IP and send UDP to any host. This breaks the invariant "the browser never loads anything but loopback addresses". Not yet checked: whether the `--chromeArg` values reached Brave's command line (the probe printed only the profile, headless and proxy flags).
- **P6: PASS.** None of the six AC-6 tools exists for the call (a tool search for them found none). P6b: `take_snapshot` and `take_screenshot` with `filePath` in `~` refused by the hook; with a path in the shots dir both wrote their files.
- **P7: PASS.** `BROWSER_GUARD` run directly with malformed JSON, empty stdin, a foreign origin, a path outside the shots dir and the app origin exited `2 2 2 2 0`.

Per AC-11 the build stops here and the spec goes back to `/architect`: the WebRTC lock in AC-4 does not hold.

## P5 direct probe (run 2026-10-12, /architect): Brave ignores the `force-` switch

Command: `python3 -I docs/specs/0009-headless-verify-test/probes/p5-webrtc.py <--chromeArg values>`. It drives `chrome-devtools-mcp@1.10.1` over stdio with no `claude -p` (same flags as AC-4 otherwise), opens a `data:` page, prints Brave's real command line from `pgrep -a`, and gathers ICE candidates for 5 seconds.

| `--chromeArg` WebRTC value | Brave's command line has it | STUN server | Candidates |
|---|---|---|---|
| `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` (old AC-4) | yes | `stun.l.google.com:19302` | `host`, `srflx` (your public IP) |
| none (control) | n/a | `stun.l.google.com:19302` | `host`, `srflx` |
| `--webrtc-ip-handling-policy=disable_non_proxied_udp` | yes | `stun.l.google.com:19302` | none (twice) |
| `--webrtc-ip-handling-policy=disable_non_proxied_udp` | yes | `74.125.250.129:19302` (IP literal), `stun.cloudflare.com:3478` | none |
| none (control) | n/a | same IP literal and cloudflare | `host`, `srflx` |

So the flag reached Brave, and Brave 154 ignores that spelling. AC-4 amended to `--webrtc-ip-handling-policy`. The same script run with `npm_config_cache=<scratch>/npm` put and ran the package from `<scratch>/npm/_npx/.../chrome-devtools-mcp` (the `MCP_CACHE` amendment).

## P3 to P7 rerun with the amended AC-4 (run 2026-10-12): PASS

Command: `python3 -B docs/specs/0009-headless-verify-test/probes/p3-p7-browser.py`, now with `--webrtc-ip-handling-policy` and `"env": {"npm_config_cache": <work>/npm}`. Cost 0.26 USD.

- **P3: PASS.** Same 24 tools as before. Brave ran as `--headless=new --webrtc-ip-handling-policy=disable_non_proxied_udp --disable-quic --proxy-server=127.0.0.1:9 --user-data-dir=/tmp/puppeteer_dev_chrome_profile-...`. The MCP ran from the probe's own npm cache (`mcp from own cache: True`). No leftover process.
- **P4: PASS.** The four foreign navigations refused by the hook; the app url and `reload` allowed.
- **P5: PASS.** `fetch` failed, the link click landed on `chrome-error://chromewebdata/`, and `RTCPeerConnection` gathered `[]`. That last one ran on the error page the click left behind; in the failing run it ran in the same place and still gathered `srflx`, and the direct probe above shows `[]` on an ordinary page.
- **P6: PASS.** The six AC-6 tools do not exist for the call. P6b: snapshot and screenshot to `~` refused, into the shots dir written.
- **P7: PASS.** `2 2 2 2 0`.

P2 to P7 now all pass, so the build continues from step 3 (the step 2 `/test` base is already in `177110c`).

## P10. npx and a planted `node_modules` (run 2026-10-12, /architect review amendment): finding 3 confirmed, fix works

Command: `python3 docs/specs/0009-headless-verify-test/probes/p10-npx-cwd.py <scratch npm cache>`. Inside a scratch repo with `node_modules/chrome-devtools-mcp` (version 1.10.1, a bin that prints `PLANTED`) and a `package.json` naming it:

```
cwd=repo: exit 0 out 'PLANTED' err ''
env -C clean: exit 0 out '1.10.1' err ''
```

## P11. Downloads (run 2026-10-12, /architect review amendment): no download saved

Command: `python3 docs/specs/0009-headless-verify-test/probes/p11-download.py <scratch npm cache> 3`. It drives chrome-devtools-mcp 1.10.1 over stdio with the AC-4 args (minus the chromeArgs) and a scratch HOME. A local server answers `/f` with `Content-Disposition: attachment`. Two cases: default, and an `XDG_CONFIG_HOME` whose `user-dirs.dirs` names a shots folder.

```
default: new_page 'Error: net::ERR_ABORTED at http://127.0.0.1:41645/f' click 'Script ran on page and returned: "clicked"' files []
XDG_CONFIG_HOME: new_page 'Error: net::ERR_ABORTED at http://127.0.0.1:41645/f' click 'Script ran on page and returned: "clicked"' files []
```

The click is an `<a download>` clicked from `evaluate_script` on an app page (page 3). After 8 s, no `p11-probe*` file was found under the scratch root, under `/tmp`, or in your real `~/Downloads`. The probe ran from a sandboxed Bash call; the real MCP runs outside it, so step 8 reruns P11 from the built code.

## Step 8: P2, P10, P11 through the built code (run 2026-10-12): P2 FAILS, build stopped

The probes now use `runner/run.py`'s own builders instead of a hand built argv.

**P2: FAIL.** Command: `python3 -B docs/specs/0009-headless-verify-test/probes/p2-built.py`. It freezes the guard of a scratch linked worktree with `Run.freeze_guard()`, then starts the app with `Run.start_app()`, which runs the real `jail_argv()` under bwrap with the app env. Result:

```
run.Stop: ('app_failed', "app exited 1: bwrap: Can't mount on symlink destination /home/santiago/.gitconfig")
```

The frozen `denyWrite` list holds `~/.gitconfig` and `~/.zshrc`, both symlinks into `~/dotfiles` on this machine. AC-3 step 3 binds each path as listed, and bwrap refuses a symlink as a bind destination. The jail checks inside the app (keys, home write, hooks, `.claude`, worktree pointer, sockets, login token, wf folders) did not run. Goes to `/architect` (brief finding 8).

**P10: PASS.** Command: `python3 -B docs/specs/0009-headless-verify-test/probes/p10-npx-cwd.py ~/.local/state/wf/npm`. The new third case runs the MCP command exactly as `run.mcp_browser()` builds it (`env -C <state dir> <npx>`), from the repo holding the planted package:

```
cwd=repo: exit 0 out 'PLANTED' err ''
env -C clean: exit 0 out '1.10.1' err ''
built MCP command: exit 0 out '1.10.1' err ''
```

**P11: PASS.** Command: `python3 -B docs/specs/0009-headless-verify-test/probes/p11-download.py ~/.local/state/wf/npm 3`. The new third case starts the MCP exactly as `run.mcp_browser()` builds it, with `run.call_env()` plus its `env`, your real HOME, and a scratch repo as cwd. The search now also covers your real `~/Downloads`.

```
default: new_page 'Error: net::ERR_ABORTED at http://127.0.0.1:40857/f' click '... "clicked" ...' files []
XDG_CONFIG_HOME: new_page 'Error: net::ERR_ABORTED at http://127.0.0.1:40857/f' click '... "clicked" ...' files []
built MCP, real HOME: new_page 'Error: net::ERR_ABORTED at http://127.0.0.1:40857/f' click '... "clicked" ...' files []
```

**P3 to P7: PASS.** Command: `python3 -B docs/specs/0009-headless-verify-test/probes/p3-p7-browser.py`. The MCP JSON is `run.mcp_browser()` (`env -C <state dir> <npx> ...`, cache `MCP_CACHE`), the hook settings are `run.browser_settings()`, and `--allowedTools`/`--disallowedTools` come from `BROWSER_TOOLS` and `BROWSER_DENIED`. Cost 0.27 USD.
- **P3: PASS.** The same 24 tools. `new_page` to the app and `take_snapshot` ran with no prompt. Brave ran as `--headless=new --webrtc-ip-handling-policy=disable_non_proxied_udp --disable-quic --proxy-server=127.0.0.1:9 --user-data-dir=/tmp/puppeteer_dev_chrome_profile-...`. `mcp from MCP_CACHE: True`, left over: none.
- **P4: PASS.** `github.com`, `file:///etc/passwd`, `chrome://settings` and `localhost:8792.evil.example` refused by the hook; the app url and `reload` allowed.
- **P5: PASS.** `fetch` failed, the link click landed on `chrome-error://chromewebdata/`, and `RTCPeerConnection` gathered `[]`.
- **P6: PASS.** The six AC-6 tools do not exist for the call. P6b: snapshot and screenshot to `~` refused (`filePath must be a plain path under <shots>`), into the shots dir written.
- **P7: PASS.** `2 2 2 2 0 2 2 2`: the five original cases, then the amended three (`http://localhost:22\@localhost:<port>/`, a path through a symlink into the shots dir, a `..` path ending in the shots dir).

## Step 9: P2 through the built code after findings 8 and 9 (run 2026-10-12): PASS

**P2: PASS.** Command: `python3 -B docs/specs/0009-headless-verify-test/probes/p2-built.py`. Same scratch linked worktree as step 8, now with the real path binds. The probe gained two checks: appending to the real file behind `~/.gitconfig` from inside the jail, and a second scratch checkout made with `git init --template=` (no `.git/hooks`) whose app plants `.git/hooks/post-commit`, then `Run.stop_app()` with its guard check. On this machine `~/.gitconfig` and `~/.zshrc` are symlinks into `~/dotfiles`.

```
app from host: 200 (ready after 0.5 s)
ssh read: refused
home write: refused
repo write: ok
git hooks write: refused
.claude write: refused
real ~/.gitconfig write: refused        (/home/santiago/dotfiles/home/git/.gitconfig: Read-only file system)
worktree .git pointer write: refused
socket /run/user/1000/gnupg/S.gpg-agent: refused
socket /run/user/1000/gnupg/S.gpg-agent.ssh: refused
socket /nonexistent: refused
oauth token in env: absent
wf config folder entries: 0
wf state dir entries: 0
after: ~/probe-wf absent; <wt>/probe exists
ro binds: [... '/home/santiago/dotfiles/home/git/.gitconfig', ... '/home/santiago/dotfiles/home/zsh/.zshrc', ...]
absent_denied: ['<tmp>/plain/.claude', '<tmp>/plain/.git/hooks']
hook planted: guard_changed: <tmp>/plain/.git/hooks appeared during the run; inspect or delete it before opening a session in this repo
```

The read only binds name the real dotfiles, never the links, and the app starts. Every P2 item from step 8 still holds.

## Step 10: P8 and P9 through `wf run` (run 2026-10-12): FAIL, build stopped

Scratch repos `p8` and `p9` under the session scratchpad, each with `main` plus a `work` branch holding one checkpoint commit and no uncommitted change, Beta tier, `test-preferences.json` (unittest), `- run suite: yes`. `p9` adds `- app start: python3 server.py 8793` and `- app url: http://127.0.0.1:8793` (stdlib server plus `index.html`). `XDG_CONFIG_HOME` and `XDG_STATE_HOME` in the scratchpad with a copied `ntfy.json`, `wf allow` on both, then `wf.py run <repo> -y --budget 3 --call-timeout 20 --max-calls 6 --max-wait 0.25` (P9: 25 and 8). Nested `claude -p` was logged in.

```
p8: [1/6] /test calc helpers -> success, 0.69 USD, 1.0m, next: /sync
p8: stopped: guard_changed: <scratch>/p8/.claude appeared during the run; inspect or delete it before opening a session in this repo
p9: stopped: guard_changed: <scratch>/p9/.claude appeared during the run; inspect or delete it before opening a session in this repo
```

Both repos had no `.claude` at start. After the first call, `<repo>/.claude/.cc-writes/` exists, an empty folder Claude Code made inside a new `.claude`. `.claude` is in `absent_denied` and is not an empty folder, so the step 9 check trips. P9 passed the start checks (real `npx`, `brave`, `MCP_CACHE`) and stopped right after its `/check verify` call. Goes to `/architect` (brief finding 10).

## Step 11: P2, P8 and P9 after findings 10 and 13 (run 2026-10-12): PASS

Built in `cababf1`: `only_dirs()` (a tree of real folders passes, any file, symlink or unreadable folder trips), an absent guarded file that is now a symlink trips, `file_hash()` returns `unreadable` on `OSError`. Six mutants (each guard removed alone), all red; full runner suite 223 tests OK.

**P2: PASS.** Command: `python3 -B docs/specs/0009-headless-verify-test/probes/p2-built.py`. Same items as step 9, all hold: app answers from the host in 0.5 s, ssh read, home write, git hooks, `.claude`, the real `~/.gitconfig` and the worktree `.git` pointer writes refused, agent sockets refused, no OAuth token, wf config and state folders empty, and in the checkout with no `.git/hooks` the planted hook stops `guard_changed: <scratch>/plain/.git/hooks appeared during the run`.

**P8: PASS.** Fresh scratch repos from the step 10 setup (no `.claude` at start), same flags. Output:

```
[1/6] /test calc helpers -> success, 0.70 USD, 1.0m, next: /sync
[2/6] /sync -> success, 0.53 USD, 0.5m, next: -
done: 1. Calc helpers
```

`test_base` `0b97be9`, `/test` wrote `tests/test_calc.py` for the committed `calc.py` with no `No changes` question. `<repo>/.claude/.cc-writes/` exists afterwards and no longer trips.

**P9: PASS.** Output:

```
[1/8] /check verify greeter page -> success, 0.71 USD, 0.9m, next: /test greeter page
[2/8] /test greeter page -> success, 0.74 USD, 1.4m, next: /sync
[3/8] /sync -> success, 0.47 USD, 0.4m, next: -
done: 1. Greeter page
```

The verify call reported `PASS`, all four ACs, driven in the headless browser, screenshot cited (`shots/ac2-ada.png`, present in the run folder). Its call record: `app {"url": "http://127.0.0.1:8793", "logs": ["app-01.log"], "ready_s": 0.5, "exit": -15}`. After the run, no process carries `WF_RUN=<run id>` (`grep -sl` over `/proc/*/environ`, no match), and no `server.py 8793` or headless Brave runs. The only chrome-devtools processes left are your own sessions' `@latest` MCPs (not pinned, not headless, started before the run).

Tool facts read on 2026-10-12 (`npx -y chrome-devtools-mcp@latest --help`, `--version`): version 1.10.1; flags `--isolated`, `--headless`, `--executablePath`, `--proxyServer`, `--chromeArg`, `--browserUrl` (`-u`), `--wsEndpoint` (`-w`), `--autoConnect`, `--userDataDir`, `--allowedUrlPattern` (Chrome 149+). Brave installed: 154.1.96.60.

## /check verify (run 2026-10-12): PASS

Every AC exercised through the real `wf.py run` on scratch repos (`wf11`), with a stand-in `claude` first on `PATH` where the check needed the exact argv or a decision, and the real `claude` for P8 and P9 above. Scripts in the session scratchpad: `run_v.sh`, `check_argv.py`, `hook_cases.py`, `ac1_ac2.py`, `decision_run.py`, `ac3_fail.py`, `debug_order.py`, `ac5_real.py`.

- [x] AC-1: only `app start`, a remote host, no port, port 70000 and a repeated `app url` each refuse `bad_answers` exit 5 with the spec detail and the `expected:` hint naming both keys; the confirm line shows `app start python3 server.py 8793, app url http://127.0.0.1:8793` with case and spaces kept.
- [x] AC-2: a fake `npx` failing `--version` refuses `no_browser: mcp: npm ERR! fake failure`; `XDG_STATE_HOME` inside the repo refuses `no_browser: state dir is writable by calls` and creates nothing there; with real tools the start check passes.
- [x] AC-3: P2 (jail) above; a busy port stops `app_port_busy: something already answers at http://127.0.0.1:8793` and an app exiting 3 parks `app_failed: app exited 3: boom`, both with no claude call; during a call the app answers 200, the call has `WF_RUN` and no OAuth token, and after the run the port is closed; a decision wait stops the app (port down from 1.7 s to 91.9 s while the local ntfy stand in held the answer), restarts it for the resume (`logs [app-01.log, app-01-r1.log]`, 200 during the resume; that `-r1` log is the pre 0011 behavior, a resume now writes its own `app-<seq>.log`); a debug call whose app rewrote `tests/generated_x.py` (new timestamp) while it ran did not park `debug_touched`.
- [x] AC-4: the captured verify call argv has `--strict-mcp-config` and `MCP_BROWSER` exactly as specified (`env -C <state dir>`, resolved `npx`, `chrome-devtools-mcp@1.10.1`, `--isolated --headless`, dead proxy, both chromeArgs, `npm_config_cache` the state dir `npm`), and `--allowedTools` lists the 24 `BROWSER_TOOLS`; the debug call gets the browser MCP too.
- [x] AC-5: `check_mcp` passes on the real captured config and rejects it with `--browserUrl` added; `test_argv` and `test_check_rejects` pass.
- [x] AC-6: `--disallowedTools` holds the six chrome-devtools names.
- [x] AC-7: the real hook command from the argv: app origin and `reload` exit 0, a screenshot inside shots exit 0; github, `file://`, the backslash form, `8793.evil.example`, a home path, a `..` path and malformed JSON exit 2 with `wf run: browser tool call refused`.
- [x] AC-8: the prompt ends with the AC-8 text naming `http://127.0.0.1:8793` and the real shots dir.
- [x] AC-9: P8 `test_base` `0b97be9`, P9 `886af04`, `/test` covered the committed files.
- [x] AC-10: call records carry `app` (`url`, `logs`, `ready_s 0.5`, `exit -15`) and `test_base`; `run.json` `answers` shows the app keys.
- [x] AC-11: P1 to P11 recorded in this file, P2, P8, P9 rerun today after the last code change.

## P2 rerun after the review stack fixes (2026-10-12): PASS

- [x] `python3 -B probes/p2-built.py`, updated for the spec 0011 repo entry (`hold()`) and with a read check per hidden secret: the jail starts on this machine's symlinked dotfiles (review M10); `~/.ssh`, `~/.config/gh`, `~/.aws`, `~/.gnupg`, `~/.config/BraveSoftware` read empty, `~/.git-credentials`, `~/.claude/.credentials.json` and your own `Read` denies (three secret files of your own) are refused (review M7); writes to `.claude`, the real `~/.gitconfig`, git hooks and the worktree pointer are refused; no OAuth token in the env; the hook planted in a checkout with no hooks folder stops `guard_changed`.
