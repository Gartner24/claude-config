# A silent ntfy server for the e2e checks: no ping reaches your phone, and every question gets an answer at once,
# so a check never waits on you. The answer stops the repo or skips when that is offered, else takes option 1.
import http.server
import json
import re
import threading

QUESTION = re.compile(r"^([a-z0-9]{4}): ")
OPTION = re.compile(r"^(\d) (.+)$")
PREFER = ("stop this repo", "skip")


def answer(message):
    """The reply the fake sends to a question ping, else None."""
    lines = message.split("\n")
    m = QUESTION.match(lines[0])
    if not m:
        return None
    options = {o.group(2): o.group(1) for o in map(OPTION.match, lines[1:]) if o}
    if not options:
        return None
    pick = next((options[p] for p in PREFER if p in options), "1")
    return f"{m.group(1)} {pick}"


class Server:
    def __init__(self):
        self.messages, self.lock = [], threading.Lock()
        fake = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                mid = fake.add(str(body.get("message") or ""))
                reply = answer(str(body.get("message") or ""))
                if reply:
                    fake.add(reply)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"id": mid}).encode())

            def do_GET(self):
                since = re.search(r"since=([^&]*)", self.path)
                with fake.lock:
                    ids = [m["id"] for m in fake.messages]
                    start = ids.index(since.group(1)) + 1 if since and since.group(1) in ids else 0
                    out = fake.messages[start:]
                self.send_response(200)
                self.end_headers()
                self.wfile.write("".join(json.dumps(m) + "\n" for m in out).encode())

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def add(self, message):
        with self.lock:
            mid = f"m{len(self.messages)}"
            self.messages.append({"id": mid, "event": "message", "message": message})
            return mid

    def close(self):
        self.httpd.shutdown()


if __name__ == "__main__":
    q = "ab12: Keep going?\nlearn: x\n1 accept the new setup and go on\n2 stop this repo\nreply ab12 <n>"
    assert answer(q) == "ab12 2", answer(q)
    assert answer("ab12: Pick?\n1 retry\n2 skip") == "ab12 2"
    assert answer("cd34: Which?\n1 Postgres\n2 SQLite") == "cd34 1"
    assert answer("wf report: all done") is None
    s = Server()
    import urllib.request
    req = urllib.request.Request(s.url + "/", data=json.dumps({"message": "cd34: Which?\n1 Postgres"}).encode(),
                                 method="POST")
    first = json.loads(urllib.request.urlopen(req).read())["id"]
    got = urllib.request.urlopen(f"{s.url}/t/json?poll=1&since={first}").read().decode().splitlines()
    assert [json.loads(g)["message"] for g in got] == ["cd34 1"], got
    s.close()
    print("ok")
