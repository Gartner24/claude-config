#!/usr/bin/env python3
# Finding 6: where does a download from a chrome-devtools-mcp 1.10.1 page land, and does an
# XDG_CONFIG_HOME holding user-dirs.dirs (XDG_DOWNLOAD_DIR=<shots>) move it there?
# argv: the npm cache to use. Each case gets a scratch HOME so nothing lands in your real ~/Downloads.
import http.server, json, os, shutil, subprocess, sys, tempfile, threading, time

npx, brave = (os.path.realpath(shutil.which(b)) for b in ("npx", "brave"))


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/page":
            body = b"<title>p</title><body>p</body>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = b"probe"
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", 'attachment; filename="p11-probe.bin"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/f"


def case(name, xdg):
    root = tempfile.mkdtemp(prefix="p11-")
    home, shots = os.path.join(root, "home"), os.path.join(root, "shots")
    os.makedirs(home)
    os.makedirs(shots)
    env = dict(os.environ, HOME=home, npm_config_cache=sys.argv[1])
    if xdg:
        cfg = os.path.join(root, "cfg")
        os.makedirs(cfg)
        with open(os.path.join(cfg, "user-dirs.dirs"), "w") as f:
            f.write(f'XDG_DOWNLOAD_DIR="{shots}"\n')
        env["XDG_CONFIG_HOME"] = cfg
    args = ["-y", "chrome-devtools-mcp@1.10.1", "--isolated", "--headless", "--executablePath", brave,
            "--proxyServer", "127.0.0.1:9", "--no-usage-statistics", "--no-performance-crux"]
    p = subprocess.Popen([npx, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         text=True, env=env)
    n = [0]

    def rpc(method, params=None, notify=False):
        msg = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if not notify:
            n[0] += 1
            msg["id"] = n[0]
        p.stdin.write(json.dumps(msg) + "\n")
        p.stdin.flush()
        while not notify:
            r = json.loads(p.stdout.readline())
            if r.get("id") == n[0]:
                return r

    rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "p", "version": "0"}})
    rpc("notifications/initialized", notify=True)
    r = rpc("tools/call", {"name": "new_page", "arguments": {"url": url}})
    text = " ".join(c.get("text", "") for c in r.get("result", {}).get("content", []))
    r = rpc("tools/call", {"name": "new_page", "arguments": {"url": url.replace("/f", "/page")}})
    print(" ".join(c.get("text", "") for c in r.get("result", {}).get("content", []))[:400])
    r = rpc("tools/call", {"name": "evaluate_script", "arguments": {"pageId": int(sys.argv[2]),
        "function": "() => { const a = document.createElement('a'); a.href = '/f'; a.download = 'p11-probe-click.bin';"
                    " document.body.append(a); a.click(); return 'clicked' }"}})
    click = " ".join(c.get("text", "") for c in r.get("result", {}).get("content", []))
    time.sleep(8)
    found = []
    for top in (root, "/tmp"):
        for d, _, fs in os.walk(top, onerror=lambda e: None):
            found += [os.path.join(d, f) for f in fs if f.startswith("p11-probe")]
    print(f"{name}: new_page {text[:120]!r} click {click[-80:]!r} files {found}")
    p.terminate()
    p.wait(10)
    shutil.rmtree(root, ignore_errors=True)


case("default", False)
case("XDG_CONFIG_HOME", True)
