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

## P2 to P9

Not run yet. Build step 1 runs probes P2 to P7 before any other code; if any fails, the build stops and the spec goes back to /architect. Step 7 runs P8 and P9 through `wf run`.

Tool facts read on 2026-10-12 (`npx -y chrome-devtools-mcp@latest --help`, `--version`): version 1.10.1; flags `--isolated`, `--headless`, `--executablePath`, `--proxyServer`, `--chromeArg`, `--browserUrl` (`-u`), `--wsEndpoint` (`-w`), `--autoConnect`, `--userDataDir`, `--allowedUrlPattern` (Chrome 149+). Brave installed: 154.1.96.60.
