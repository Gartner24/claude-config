#!/usr/bin/env python3
"""Spec 0064 AC-5: serves the handover pages as /<first 8 of the session id>-<16 hex>.

The pages hold handover text, which can name private repos, so the server refuses any
address but loopback or a Tailscale one (100.64.0.0/10), and a page is served only when
the key in the link matches the key the page itself carries; a path never reaches the disk.
Design from alexknowshtml/claude-auto-handoff (MIT), written fresh here.
"""
import argparse
import http.client
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import signal
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

LINK = re.compile(r"^/([A-Za-z0-9]{8})-([0-9a-f]{16})$")
TAILNET = ipaddress.ip_network("100.64.0.0/10")


def allowed(bind):
    try:
        ip = ipaddress.ip_address(bind)
    except ValueError:
        return False
    return ip.version == 4 and (ip.is_loopback or ip in TAILNET)


def find(pages, prefix, key):
    mark = f'<meta name="wf-handoff-key" content="{key}">'
    try:
        names = sorted(os.listdir(pages))
    except OSError:
        return None
    for name in names:
        if not (name.startswith(prefix) and name.endswith(".html")):
            continue
        try:
            with open(os.path.join(pages, name), encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        if mark in text:
            return text
    return None


def sign(token, nonce, bind, port, pid):
    # the address, port and pid are signed too, so a relay cannot pass off our answer as its own
    return hmac.new(token.encode(), f"{nonce}|{bind}|{port}|{pid}".encode(), hashlib.sha256).hexdigest()


def make_handler(pages, bind, token=""):
    class Handler(BaseHTTPRequestHandler):
        def send(self, code, body, kind):
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/__wf-handoff":
                # challenge and response: the token itself never leaves this process, so a caller that
                # reads this answer cannot replay it to pose as the server later
                nonce = parse_qs(url.query).get("n", [""])[0][:64]
                port = self.server.server_address[1]
                mac = sign(token, nonce, bind, port, os.getpid()) if token and nonce else ""
                return self.send(200, json.dumps({"server": "wf-handoff", "bind": bind, "pid": os.getpid(), "mac": mac}), "application/json")
            m = LINK.match(self.path)
            text = find(pages, m.group(1), m.group(2)) if m else None
            if text is None:
                return self.send(404, "not found\n", "text/plain")
            self.send(200, text, "text/html; charset=utf-8")

        def log_message(self, *args):
            pass  # one line per request would fill the session's log

    return Handler


def write_token(path):
    # A process that only answers /__wf-handoff cannot pose as this server: the mod checks an HMAC
    # of its nonce under this token, which only the owner can read. A new token on every start.
    token = secrets.token_hex(16)
    tmp = f"{path}.{os.getpid()}"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(token + "\n")
    os.replace(tmp, path)
    return token


def probe(host, port, token_file, nonce=None):
    """Who answers on host:port: "none", "foreign", or "ours" with its bind and pid.

    Ours means it signed a fresh nonce with the token in token_file; an answer read earlier
    cannot be replayed, and a listener that only says "wf-handoff" is foreign.
    """
    # the mod picks a fresh nonce per probe; anything but 16 to 64 hex characters gets our own
    if not (nonce and re.fullmatch(r"[0-9a-f]{16,64}", nonce)):
        nonce = secrets.token_hex(8)
    # a plain connection: no proxy from the env, no redirect followed
    conn = http.client.HTTPConnection(host, int(port), timeout=2)
    try:
        conn.connect()
    except OSError:
        conn.close()
        return {"state": "none"}
    # something listens: from here every failure means a listener that is not ours
    try:
        conn.request("GET", f"/__wf-handoff?n={nonce}")
        r = conn.getresponse()
        status, body = r.status, r.read(4096)
    except (OSError, ValueError, http.client.HTTPException):
        return {"state": "foreign"}
    finally:
        conn.close()
    if status != 200:
        return {"state": "foreign"}
    try:
        info = json.loads(body)
        with open(token_file, encoding="utf-8") as f:
            token = f.read().strip()
    except (ValueError, OSError):
        return {"state": "foreign"}
    if not (isinstance(info, dict) and info.get("server") == "wf-handoff" and token
            and info.get("bind") == host and isinstance(info.get("pid"), int)):
        return {"state": "foreign"}
    if not hmac.compare_digest(str(info.get("mac", "")), sign(token, nonce, host, int(port), info["pid"])):
        return {"state": "foreign"}
    return {"state": "ours", "bind": host, "pid": info["pid"]}


def serve(bind, port, pages, token_file=None):
    if not allowed(bind):
        print(f"refused bind {bind}: only loopback or a Tailscale address", flush=True)
        return 2
    handler = make_handler(pages, bind)
    try:
        httpd = ThreadingHTTPServer((bind, port), handler)
    except OSError as e:
        print(f"port {port} on {bind} not free ({e.strerror})", flush=True)
        return 1
    if token_file:
        httpd.RequestHandlerClass = make_handler(pages, bind, write_token(token_file))
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    print(f"serving {pages} on {bind}:{port}", flush=True)
    try:
        httpd.serve_forever()
    finally:
        if token_file:
            try:
                os.remove(token_file)
            except OSError:
                pass
    return 0


def selftest():
    import tempfile
    import threading
    import urllib.error
    import urllib.request

    assert allowed("127.0.0.1") and allowed("100.101.102.103")
    for bad in ("0.0.0.0", "192.168.1.5", "::1", "tailscale", "100.128.0.1"):
        assert not allowed(bad), bad
    assert serve("0.0.0.0", 0, "/nonexistent") == 2
    with tempfile.TemporaryDirectory() as pages:
        key = "0123456789abcdef"
        with open(os.path.join(pages, "abcdefgh-1111.html"), "w") as f:
            f.write(f'<meta name="wf-handoff-key" content="{key}">page one')
        with open(os.path.join(pages, "secret.txt"), "w") as f:
            f.write("never served")
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(pages, "127.0.0.1"))
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{httpd.server_address[1]}"

        def get(path):
            try:
                with urllib.request.urlopen(base + path) as r:
                    return r.status, r.read().decode()
            except urllib.error.HTTPError as e:
                return e.code, ""

        assert get(f"/abcdefgh-{key}") == (200, f'<meta name="wf-handoff-key" content="{key}">page one')
        assert get("/abcdefgh-fedcba9876543210")[0] == 404, "a wrong key must not serve"
        assert get(f"/zzzzzzzz-{key}")[0] == 404, "a wrong session prefix must not serve"
        assert get("/secret.txt")[0] == 404
        assert get("/../secret.txt")[0] == 404
        info = json.loads(get("/__wf-handoff?n=abc")[1])
        assert info["server"] == "wf-handoff" and info["bind"] == "127.0.0.1" and info["pid"] == os.getpid()
        assert info["mac"] == "" and "token" not in info, "a server with no token proves nothing"
        httpd.shutdown()
        signed = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(pages, "127.0.0.1", "s3cret"))
        threading.Thread(target=signed.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{signed.server_address[1]}"
        body = get("/__wf-handoff?n=n1")[1]
        assert "s3cret" not in body, "the token never leaves the server"
        assert json.loads(body)["mac"] == sign("s3cret", "n1", "127.0.0.1", signed.server_address[1], os.getpid())
        assert json.loads(get("/__wf-handoff?n=n2")[1])["mac"] != json.loads(body)["mac"], "each nonce its own answer"
        tok2 = os.path.join(pages, "t2")
        with open(tok2, "w") as f:
            f.write("s3cret\n")
        port = signed.server_address[1]
        assert probe("127.0.0.1", port, tok2) == {"state": "ours", "bind": "127.0.0.1", "pid": os.getpid()}
        with open(tok2, "w") as f:
            f.write("other\n")
        assert probe("127.0.0.1", port, tok2) == {"state": "foreign"}, "a server signing with another token is not ours"
        assert probe("127.0.0.1", port, os.path.join(pages, "missing")) == {"state": "foreign"}
        with open(tok2, "w") as f:
            f.write("s3cret\n")
        replayed = json.loads(get("/__wf-handoff?n=n1")[1])

        # listeners that are not ours: a replay of an answer once seen, the same with another pid, a page
        # that is not ours at all, a relay that asks our real server with the probe's own nonce, a redirect
        def relay(h):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            conn.request("GET", h.path)
            return 200, conn.getresponse().read().decode()

        fakes = [
            lambda h: (200, json.dumps(replayed)),
            lambda h: (200, json.dumps({**replayed, "pid": 1})),
            lambda h: (200, "<html>other</html>"),
            relay,
            lambda h: (302, ""),
        ]
        for i, act in enumerate(fakes):
            class Fake(BaseHTTPRequestHandler):
                def do_GET(self, act=act):
                    code, text = act(self)
                    self.send_response(code)
                    if code == 302:
                        self.send_header("Location", f"http://127.0.0.1:{port}{self.path}")
                    self.end_headers()
                    self.wfile.write(text.encode())

                def log_message(self, *args):
                    pass
            fake = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
            threading.Thread(target=fake.serve_forever, daemon=True).start()
            assert probe("127.0.0.1", fake.server_address[1], tok2) == {"state": "foreign"}, f"fake {i}"
            fake.shutdown()
            fake.server_close()
        assert probe("127.0.0.1", port, tok2)["state"] == "ours", "the real one still passes"
        import socket
        mute = socket.socket()
        mute.bind(("127.0.0.1", 0))
        mute.listen(1)
        assert probe("127.0.0.1", mute.getsockname()[1], tok2) == {"state": "foreign"}, "a listener that never answers is not free"
        mute.close()
        signed.shutdown()
        signed.server_close()
        assert probe("127.0.0.1", port, tok2) == {"state": "none"}, "a closed port answers nothing"
        tok = os.path.join(pages, "server.token")
        t = write_token(tok)
        assert open(tok).read().strip() == t and len(t) == 32
        assert os.stat(tok).st_mode & 0o077 == 0, "the token file must be the owner's only"
        assert write_token(tok) != t, "each server start gets a new token"
        os.remove(tok)
        import subprocess
        child = subprocess.Popen([sys.executable, __file__, "--bind", "127.0.0.1", "--port", "0", "--dir", pages, "--token-file", tok], stdout=subprocess.PIPE, text=True)
        assert child.stdout.readline().startswith("serving"), "the server starts"
        assert os.path.exists(tok), "a started server holds its token file"
        child.terminate()
        child.wait(timeout=10)
        assert not os.path.exists(tok), "a stopped server leaves no token behind"
        busy = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(pages, "127.0.0.1"))
        assert serve("127.0.0.1", busy.server_address[1], pages) == 1, "a taken port must not crash"
        busy.server_close()
    print("server.py: all checks pass")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--bind")
    p.add_argument("--port", type=int)
    p.add_argument("--dir")
    p.add_argument("--token-file")
    p.add_argument("--probe", nargs=4, metavar=("HOST", "PORT", "TOKEN_FILE", "NONCE"))
    a = p.parse_args()
    if a.test:
        return selftest()
    if a.probe:
        print(json.dumps(probe(*a.probe)))
        return 0
    return serve(a.bind, a.port, a.dir, a.token_file)


if __name__ == "__main__":
    sys.exit(main())
