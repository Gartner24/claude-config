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

## P8 and P9

Not run: they come after the build, which stopped at P5.

Tool facts read on 2026-10-12 (`npx -y chrome-devtools-mcp@latest --help`, `--version`): version 1.10.1; flags `--isolated`, `--headless`, `--executablePath`, `--proxyServer`, `--chromeArg`, `--browserUrl` (`-u`), `--wsEndpoint` (`-w`), `--autoConnect`, `--userDataDir`, `--allowedUrlPattern` (Chrome 149+). Brave installed: 154.1.96.60.
