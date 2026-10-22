# A silent Telegram Bot API for the e2e checks: the same Telegram path your runs use, but nothing reaches your phone
# and every question is answered at once by a button tap, so a check never waits on you. The tap stops the repo or
# skips when that is offered, else takes option 1. wf finds it through WF_TELEGRAM_API (127.0.0.1 only).
import http.server
import json
import re
import threading
import time

TOKEN = "123456:" + "e2e" * 12
CHAT = 4242
PREFER = ("stop this repo", "skip")


def tap(markup):
    """The callback_data of the button the fake taps on a question's inline keyboard, else None."""
    buttons = [b for row in (markup or {}).get("inline_keyboard") or [] for b in row]
    labels = {re.sub(r"^\d+ ", "", b.get("text", "")): b.get("callback_data") for b in buttons}
    for p in PREFER:
        if p in labels:
            return labels[p]
    return buttons[0].get("callback_data") if buttons else None


class Server:
    def __init__(self):
        self.updates, self.sent, self.lock, self.mid = [], [], threading.Lock(), 100
        fake = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
                method = self.path.rsplit("/", 1)[-1]
                try:
                    params = json.loads(raw) if self.headers.get("Content-Type") == "application/json" else {}
                except ValueError:
                    params = {}
                body = fake.handle(method, params)
                out = json.dumps({"ok": True, "result": body}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def handle(self, method, params):
        with self.lock:
            if method in ("sendMessage", "sendDocument"):
                self.mid += 1
                self.sent.append(params)
                data = tap(params.get("reply_markup"))
                if data:
                    n = len(self.updates) + 1000
                    # Dated a second later: a tap never predates the question it answers.
                    self.updates.append({"update_id": n, "callback_query": {
                        "id": f"cq{n}", "from": {"id": CHAT}, "data": data,
                        "message": {"chat": {"id": CHAT}, "date": int(time.time()) + 1}}})
                return {"message_id": self.mid}
            if method == "getUpdates":
                off = params.get("offset", 0)
                return [u for u in self.updates if u["update_id"] >= off]
            if method == "getMe":
                return {"username": "wf_e2e_bot"}
            return True

    def config(self):
        return {"token": TOKEN, "chat_id": CHAT, "aliases": {}, "block": []}

    def close(self):
        self.httpd.shutdown()


if __name__ == "__main__":
    kb = {"inline_keyboard": [[{"text": "1 accept the new setup and go on", "callback_data": "ab12 1"}],
                              [{"text": "2 stop this repo", "callback_data": "ab12 2"}]]}
    assert tap(kb) == "ab12 2", tap(kb)
    assert tap({"inline_keyboard": [[{"text": "1 Postgres", "callback_data": "cd34 1"}]]}) == "cd34 1"
    assert tap(None) is None
    s = Server()
    import urllib.request

    def call(method, params):
        req = urllib.request.Request(f"{s.url}/bot{TOKEN}/{method}", data=json.dumps(params).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        return json.loads(urllib.request.urlopen(req).read())["result"]
    assert call("sendMessage", {"chat_id": CHAT, "text": "q", "reply_markup": kb}) == {"message_id": 101}
    [u] = call("getUpdates", {"offset": 0})
    assert u["callback_query"]["data"] == "ab12 2"
    assert call("getUpdates", {"offset": u["update_id"] + 1}) == []
    s.close()
    print("ok")
