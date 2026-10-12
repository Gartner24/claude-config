#!/usr/bin/env python3
# Spec 0009 AC-11 P3 to P7: one claude -p browser call built by hand with the AC-4 MCP JSON, the AC-6 denies and
# the AC-7 hook, against a plain local server. Prints every chrome-devtools tool call with its result, the tool
# list from the init event (P3, BROWSER_TOOLS), the Brave command lines seen while it ran, then P7 directly.
import json, os, shlex, shutil, subprocess, sys, tempfile, threading, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../runner"))
import run  # noqa: E402

PORT = int(os.environ.get("PORT", "8792"))
APP = f"http://localhost:{PORT}/"
work = tempfile.mkdtemp()
site, shots = os.path.join(work, "site"), os.path.join(work, "shots")
os.makedirs(site), os.makedirs(shots)
with open(os.path.join(site, "index.html"), "w") as f:
    f.write('<!doctype html><title>probe app</title><h1>Probe app</h1><a id="out" href="https://example.com/">out</a>')
server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1", "-d", site],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

npx, brave, py = (os.path.realpath(shutil.which(b)) for b in ("npx", "brave", "python3"))
mcp = {"mcpServers": {"chrome-devtools": {"type": "stdio", "command": npx, "args": [
    "-y", "chrome-devtools-mcp@1.10.1", "--isolated", "--headless", "--executablePath", brave,
    "--proxyServer", "127.0.0.1:9", "--chromeArg=--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
    "--chromeArg=--disable-quic", "--no-usage-statistics", "--no-performance-crux"]}}}
denied = ["upload_file", "take_heapsnapshot", "performance_start_trace", "performance_stop_trace",
          "performance_analyze_insight", "lighthouse_audit"]
hook = f"{shlex.quote(py)} -c {shlex.quote(run.BROWSER_GUARD)} {shlex.quote(APP)} {shlex.quote(shots + '/')} || exit 2"
settings = {"hooks": {"PreToolUse": [{"matcher": "mcp__chrome-devtools__.*",
                                      "hooks": [{"type": "command", "timeout": 10, "command": hook}]}]}}
H = os.path.expanduser("~")
prompt = f"""Browser probe for the machine owner. Use only the chrome-devtools tools. Run each step once as written, report each numbered result with the exact output or error, never retry or work around a refusal.
1. new_page to {APP}, then take_snapshot.
2. navigate_page type url to https://github.com ; then to file:///etc/passwd ; then to chrome://settings ; then to http://localhost:{PORT}.evil.example/ ; then to {APP} ; then navigate_page type reload.
3. evaluate_script: async () => {{ try {{ const r = await fetch('https://example.com'); return 'fetched ' + r.status }} catch (e) {{ return 'fetch failed: ' + e }} }}
4. click the link with text out (from a fresh take_snapshot), wait 3 seconds, then evaluate_script () => location.href
5. evaluate_script: async () => {{ const pc = new RTCPeerConnection({{iceServers: [{{urls: 'stun:stun.l.google.com:19302'}}]}}); pc.createDataChannel('x'); const types = []; pc.onicecandidate = e => {{ if (e.candidate) types.push(e.candidate.type) }}; await pc.setLocalDescription(await pc.createOffer()); await new Promise(r => setTimeout(r, 5000)); pc.close(); return JSON.stringify(types) }}
6. Try each of these once: upload_file, take_heapsnapshot, performance_start_trace, performance_stop_trace, performance_analyze_insight, lighthouse_audit (any arguments). Report each result.
7. take_snapshot with filePath {H}/probe-wf ; take_screenshot with filePath {H}/probe-wf.png ; take_snapshot with filePath {shots}/snap.txt ; take_screenshot with filePath {shots}/shot.png
8. evaluate_script () => document.cookie + ' | ' + localStorage.length"""

argv = [shutil.which("claude"), "-p", prompt, "--model", "sonnet", "--output-format", "stream-json", "--verbose",
        "--permission-mode", "auto", "--permission-prompts", "none", "--max-budget-usd", "2",
        "--strict-mcp-config", "--mcp-config", json.dumps(mcp), "--settings", json.dumps(settings),
        "--allowedTools", "mcp__chrome-devtools",
        "--disallowedTools", ",".join("mcp__chrome-devtools__" + d for d in denied)]
seen, done = set(), threading.Event()


def watch():
    while not done.is_set():
        out = subprocess.run(["pgrep", "-u", str(os.getuid()), "-a", "brave"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if "--user-data-dir" in line and "--type=" not in line:
                seen.add(" ".join(w for w in line.split()[1:] if w.startswith(("--user-data-dir", "--headless", "--proxy"))))
        time.sleep(1)


threading.Thread(target=watch, daemon=True).start()
try:
    r = subprocess.run(argv, cwd=work, env=run.call_env(), capture_output=True, text=True, timeout=900)
finally:
    done.set()
    server.terminate()
uses = {}
for line in r.stdout.splitlines():
    try:
        e = json.loads(line)
    except ValueError:
        continue
    if e.get("type") == "system" and e.get("subtype") == "init":
        tools = sorted(t for t in e.get("tools", []) if t.startswith("mcp__chrome-devtools__"))
        print("P3 tools:", json.dumps([t.removeprefix("mcp__chrome-devtools__") for t in tools]))
    for c in (e.get("message") or {}).get("content") or []:
        if not isinstance(c, dict):
            continue
        if c.get("type") == "tool_use":
            uses[c["id"]] = (c["name"].removeprefix("mcp__chrome-devtools__"), json.dumps(c["input"])[:160])
        if c.get("type") == "tool_result" and c.get("tool_use_id") in uses:
            body = c.get("content")
            text = body if isinstance(body, str) else " ".join(x.get("text", "") for x in body or [] if isinstance(x, dict))
            name, given = uses[c["tool_use_id"]]
            print(f"{'ERR' if c.get('is_error') else 'ok '} {name} {given} -> {' '.join(text.split())[:200]}")
    if e.get("type") == "result":
        print("result:", e.get("subtype"), "cost", e.get("total_cost_usd"), "denials",
              [d.get("tool_name") for d in e.get("permission_denials") or []])
        print("final:", (e.get("result") or "")[-1500:])
print("stderr tail:", r.stderr[-500:])
print("brave seen:", sorted(seen))
print("files: shots", sorted(os.listdir(shots)), "| ~/probe-wf", os.path.exists(H + "/probe-wf"),
      "| ~/probe-wf.png", os.path.exists(H + "/probe-wf.png"))
left = subprocess.run(["pgrep", "-u", str(os.getuid()), "-af", "chrome-devtools-mcp@1.10.1|" + work],
                      capture_output=True, text=True).stdout
print("left over:", left.strip() or "none")

print("P7 (expect 2 2 2 2 0):", end=" ")
for stdin in ("not json", "", json.dumps({"tool_name": "mcp__chrome-devtools__navigate_page", "tool_input": {"url": "https://github.com"}}),
              json.dumps({"tool_name": "mcp__chrome-devtools__take_screenshot", "tool_input": {"filePath": "/etc/x.png"}}),
              json.dumps({"tool_name": "mcp__chrome-devtools__new_page", "tool_input": {"url": APP}})):
    p = subprocess.run(["sh", "-c", hook], input=stdin, capture_output=True, text=True)
    print(p.returncode, end=" ")
print()
shutil.rmtree(work, ignore_errors=True)
