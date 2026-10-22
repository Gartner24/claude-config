#!/usr/bin/env python3
# Drive chrome-devtools-mcp over stdio: open a page, print Brave's full argv, run the P5 WebRTC test.
# argv: extra MCP args (each one a separate argv item).
import json, os, shutil, subprocess, sys, threading, time

npx, brave = (os.path.realpath(shutil.which(b)) for b in ("npx", "brave"))
args = ["-y", "chrome-devtools-mcp@1.10.1", "--isolated", "--headless", "--executablePath", brave,
        "--proxyServer", "127.0.0.1:9", "--no-usage-statistics", "--no-performance-crux", *sys.argv[1:]]
p = subprocess.Popen([npx, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
n = 0


def rpc(method, params=None, notify=False):
    global n
    msg = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        n += 1
        msg["id"] = n
    p.stdin.write(json.dumps(msg) + "\n")
    p.stdin.flush()
    if notify:
        return None
    while True:
        r = json.loads(p.stdout.readline())
        if r.get("id") == n:
            return r


def call(tool, a):
    r = rpc("tools/call", {"name": tool, "arguments": a})
    return " ".join(c.get("text", "") for c in r.get("result", {}).get("content", []))


rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "probe", "version": "0"}})
rpc("notifications/initialized", notify=True)
print("NEW:", call("new_page", {"url": "data:text/html,<title>x</title>"})[:300])
out = subprocess.run(["pgrep", "-u", str(os.getuid()), "-a", "brave"], capture_output=True, text=True).stdout
for line in out.splitlines():
    if "puppeteer_dev_chrome_profile" in line and "--type=" not in line:
        print("BRAVE:", " ".join(w for w in line.split()[1:] if w.startswith("--") and ("webrtc" in w or "quic" in w or "proxy" in w or "WebRtc" in w or "disable-features" in w or "enable-features" in w)))
js = ("async () => { const pc = new RTCPeerConnection({iceServers: [{urls: ['stun:74.125.250.129:19302', 'stun:stun.cloudflare.com:3478']}]}); "
      "pc.createDataChannel('x'); const c = []; pc.onicecandidate = e => { if (e.candidate) c.push(e.candidate.type + ' ' + e.candidate.protocol + ' ' + e.candidate.address) }; "
      "await pc.setLocalDescription(await pc.createOffer()); await new Promise(r => setTimeout(r, 5000)); pc.close(); return JSON.stringify(c) }")
print("RTC:", call("evaluate_script", {"function": js, "pageId": 2})[-400:])
p.stdin.close()
p.terminate()
p.wait(10)
