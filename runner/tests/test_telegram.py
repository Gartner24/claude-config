import ast
import fcntl
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

RUNNER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RUNNER))
import ntfy  # noqa: E402
import telegram  # noqa: E402

TOKEN = "123456789:" + "A" * 35
CHAT = 4242


class FakeBot:
    """A local Bot API: records every call, numbers sent messages, serves queued updates from `offset`."""

    def __init__(self):
        self.calls, self.updates, self.fail, self.mid = [], [], 0, 100
        self.lock = threading.Lock()
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                method = self.path.rsplit("/", 1)[1]
                kind = self.headers.get("Content-Type", "")
                params = json.loads(raw) if kind == "application/json" else {"raw": raw.decode(), "type": kind}
                with fake.lock:
                    fake.calls.append((self.path, method, params))
                    if fake.fail:
                        fake.fail -= 1
                        # A real error can echo the request URL, token included.
                        body = {"ok": False, "description": f"broken at {self.path}"}
                    elif method == "getUpdates":
                        off = params.get("offset", 0)
                        body = {"ok": True, "result": [u for u in fake.updates if u["update_id"] >= off]}
                    elif method in ("sendMessage", "sendDocument"):
                        fake.mid += 1
                        body = {"ok": True, "result": {"message_id": fake.mid}}
                    elif method == "getMe":
                        body = {"ok": True, "result": {"username": "wf_test_bot"}}
                    else:
                        body = {"ok": True, "result": True}
                out = json.dumps(body).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()

    def sent(self, method="sendMessage"):
        return [p for _, m, p in self.calls if m == method]


def write_cfg(config, **over):
    cfg = {"token": TOKEN, "chat_id": CHAT, "aliases": {}, "block": ["acme"], **over}
    p = Path(config) / "wf" / "telegram.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg))
    p.chmod(0o600)
    return p


def msg_update(uid, text, chat=CHAT, sender=CHAT, reply_to=None, date=None):
    m = {"message_id": uid, "chat": {"id": chat}, "from": {"id": sender}, "date": date or int(time.time()), "text": text}
    if reply_to is not None:
        m["reply_to_message"] = {"from": {"id": 1, "is_bot": True}, "text": reply_to}
    return {"update_id": uid, "message": m}


def tap_update(uid, data, chat=CHAT, sender=CHAT, date=None):
    return {"update_id": uid, "callback_query": {"id": f"cq{uid}", "from": {"id": sender}, "data": data,
                                                  "message": {"chat": {"id": chat}, "date": date or int(time.time())}}}


class TelegramCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        env = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.tmp / "config"),
                                           "XDG_STATE_HOME": str(self.tmp / "state")})
        env.start()
        self.addCleanup(env.stop)
        self.bot = FakeBot()
        self.addCleanup(self.bot.close)
        for name, value in (("API", self.bot.url),):
            p = mock.patch.object(telegram, name, value)
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch.object(ntfy, "RETRY_GAP", 0.01)
        p.start()
        self.addCleanup(p.stop)
        self.cfg_path = write_cfg(self.tmp / "config")
        self.cfg = telegram.load()

    def decision(self, kind="panel", options=("yes", "no"), multi=False, asked=None):
        return {"id": "ab12", "kind": kind, "question": "Ship it?", "options": list(options) if kind == "panel" else [],
                "multi": multi, "answer": None, "ignored": 0,
                "asked": asked or ntfy.datetime.datetime.now().astimezone().isoformat(timespec="seconds")}


class TestLoad(TelegramCase):
    # covers: spec 0029 AC-1 (each refusal; no why ever holds the token)
    def test_refusals(self):
        self.assertEqual(self.cfg["chat_id"], CHAT)
        self.cfg_path.chmod(0o640)
        with self.assertRaisesRegex(telegram.Invalid, "readable or writable by others"):
            telegram.load()
        for over, why in (({"token": "nope" + TOKEN}, "token must be"), ({"chat_id": "4242"}, "chat_id must be"),
                          ({"chat_id": True}, "chat_id must be"), ({"aliases": []}, "aliases must be"),
                          ({"block": "x"}, "block must be")):
            write_cfg(self.tmp / "config", **over)
            with self.assertRaises(telegram.Invalid) as e:
                telegram.load()
            self.assertIn(why, str(e.exception))
            self.assertNotIn(TOKEN, str(e.exception))
        self.cfg_path.write_text("[1]")
        with self.assertRaisesRegex(telegram.Invalid, "not a JSON object"):
            telegram.load()
        self.cfg_path.unlink()
        with self.assertRaisesRegex(telegram.Invalid, "is missing"):
            telegram.load()

    # covers: spec 0029 AC-1 (an API error echoing the URL is redacted, in ApiError and PingFailed)
    def test_token_redacted(self):
        self.bot.fail = 3
        t = telegram.Topic(self.cfg, "demo", "loop")
        with self.assertRaises(telegram.PingFailed) as e:
            t.publish("hello", 3)
        self.assertIn("<token>", str(e.exception))
        self.assertNotIn(TOKEN, str(e.exception))
        self.assertIsNone(e.exception.__cause__)
        self.assertEqual(len(self.bot.sent()), 3)

    # covers: spec 0029 AC-11 (standard library, ntfy and wf only)
    def test_stdlib_only(self):
        tree = ast.parse((RUNNER / "telegram.py").read_text())
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(names - set(sys.stdlib_module_names), {"ntfy", "wf"})

    # covers: spec 0029 AC-3 (every call's sandbox denies reading telegram.json)
    def test_calls_cannot_read(self):
        import run
        denied = [x for p in run.CREDENTIAL_PATHS for x in run.expand(p)]
        self.assertTrue(any(telegram.path().startswith(d.rstrip("/") + "/") for d in denied), denied)


class TestSend(TelegramCase):
    # covers: spec 0029 AC-4 (plain text body, every option a button, d["sent"], message id; prose has no keyboard)
    def test_ping(self):
        t = telegram.Topic(self.cfg, "demo", "loop")
        d = self.decision(options=["yes", "no", "later", "see `src/x.py` /etc/passwd", ""])
        self.assertEqual(t.ping(d, lambda: False), "101")
        p = self.bot.sent()[0]
        self.assertEqual(p["chat_id"], CHAT)
        self.assertNotIn("parse_mode", p)
        self.assertEqual(d["sent"], "ab12: Ship it?\n1 yes\n2 no\n3 later\n4 see\n5 option 5\n"
                                    "tap a button, or reply to this message")
        self.assertTrue(p["text"].startswith(d["sent"] + "\n"))
        self.assertEqual(p["reply_markup"]["inline_keyboard"],
                         [[{"text": f"{n} {l}", "callback_data": f"ab12 {n}"}]
                          for n, l in enumerate(["yes", "no", "later", "see", "option 5"], 1)])
        self.assertNotIn("disable_notification", p)
        d = self.decision(kind="prose")
        d["question"] = "Acme wants what?"
        t.ping(d, lambda: False)
        p = self.bot.sent()[1]
        self.assertNotIn("reply_markup", p)
        self.assertEqual(d["sent"], "ab12: question waiting, see terminal\nreply to this message with your answer")

    # covers: spec 0029 AC-4 (question cut at 1000, label at 200)
    def test_cuts(self):
        t = telegram.Topic(self.cfg, "demo", "loop")
        d = self.decision(options=["word " * 100])
        d["question"] = "word " * 400
        t.ping(d, lambda: False)
        q, label = d["sent"].split("\n")[:2]
        self.assertLessEqual(len(q), len("ab12: ") + 1000)
        self.assertGreater(len(q), 900)
        self.assertLessEqual(len(label), 2 + 200)

    # covers: spec 0029 AC-5 (title first line, priority 2 silent)
    def test_publish(self):
        t = telegram.Topic(self.cfg, "demo", "loop")
        self.assertEqual(t.publish("ab12 accepted", 2), "101")
        p = self.bot.sent()[0]
        self.assertEqual(p["text"], "wf demo: loop\nab12 accepted")
        self.assertIs(p["disable_notification"], True)
        t.publish("body", 3, title="wf report", tags=[], actions=[{"x": 1}])
        p = self.bot.sent()[1]
        self.assertEqual(p["text"], "wf report\nbody")
        self.assertNotIn("disable_notification", p)
        self.assertNotIn("reply_markup", p)


class TestFetch(TelegramCase):
    def log(self):
        return [json.loads(l) for l in Path(telegram.log_path()).read_text().splitlines()]

    # covers: spec 0029 AC-6 (chat and sender filter, callback and reply-to mapping, hint, offset, 0600 log)
    def test_fetch(self):
        self.bot.updates = [msg_update(1, "ab12 1", chat=999, sender=999),
                            msg_update(2, "ab12 1", sender=999),
                            tap_update(3, "ab12 2"),
                            msg_update(4, "use the blue one", reply_to="ab12: Ship it?\n1 yes"),
                            msg_update(5, "hello there"),
                            msg_update(6, "ab12 yes"),
                            tap_update(7, "ab12 1", sender=999)]
        telegram.fetch(self.cfg)
        log = self.log()
        self.assertEqual([(l["id"], l["event"], l.get("message")) for l in log],
                         [("u1", "skip", None), ("u2", "skip", None), ("u3", "message", "ab12 2"),
                          ("u4", "message", "ab12 use the blue one"), ("u5", "message", "hello there"),
                          ("u6", "message", "ab12 yes"), ("u7", "skip", None)])
        self.assertEqual(os.stat(telegram.log_path()).st_mode & 0o777, 0o600)
        get = self.bot.sent("getUpdates")[0]
        self.assertEqual((get["timeout"], get["allowed_updates"]), (0, ["message", "callback_query"]))
        self.assertNotIn("offset", get)
        self.assertEqual(self.bot.sent("answerCallbackQuery"), [{"callback_query_id": "cq3"},
                                                                {"callback_query_id": "cq7"}])
        self.assertEqual(self.bot.sent(), [{"chat_id": CHAT, "text": telegram.HINT}])
        telegram.fetch(self.cfg)
        self.assertEqual(self.bot.sent("getUpdates")[1]["offset"], 8)
        self.assertEqual(len(self.log()), 7)

    # covers: spec 0029 AC-6 (lines older than 48 hours dropped, the newest kept for the offset)
    def test_prune(self):
        old = int(time.time()) - telegram.KEEP - 10
        self.bot.updates = [msg_update(1, "ab12 1", date=old), msg_update(2, "ab12 2", date=old)]
        telegram.fetch(self.cfg)
        telegram.fetch(self.cfg)
        self.assertEqual([l["id"] for l in self.log()], ["u2"])
        self.bot.updates.append(msg_update(3, "ab12 3"))
        telegram.fetch(self.cfg)
        self.assertEqual([l["id"] for l in self.log()], ["u3"])

    # covers: spec 0029 AC-6 (a second fetcher returns at once while one holds the lock)
    def test_one_reader(self):
        os.makedirs(telegram.state_dir(), exist_ok=True)
        fd = os.open(os.path.join(telegram.state_dir(), "telegram.lock"), os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            telegram.fetch(self.cfg)
        finally:
            os.close(fd)
        self.assertEqual(self.bot.sent("getUpdates"), [])
        telegram.fetch(self.cfg)
        self.assertEqual(len(self.bot.sent("getUpdates")), 1)

    # covers: spec 0029 AC-7 (u<N> cursor returns later lines, any other cursor every line)
    def test_poll_cursor(self):
        self.bot.updates = [tap_update(5, "ab12 1"), tap_update(6, "ab12 2")]
        t = telegram.Topic(self.cfg, "", "")
        self.assertEqual([l["id"] for l in t.poll("1760000000")], ["u5", "u6"])
        self.assertEqual([l["id"] for l in t.poll("u5")], ["u6"])
        self.assertEqual(t.poll("u6"), [])


class TestTake(TelegramCase):
    # covers: spec 0029 AC-8 (number, numbers with multi, label, free text, prose; source phone)
    def test_forms(self):
        t = telegram.Topic(self.cfg, "", "")
        now = int(time.time()) + 5
        for text, multi, want in (("ab12 2", False, "no"), ("ab12 1,2", True, "yes, no"), ("ab12 NO", False, "no"),
                                  ("ab12 the blue one", False, "the blue one"), ("ab12 1,2", False, "1,2")):
            d = self.decision(options=["yes", "no"], multi=multi)
            self.assertIs(t.take(text, [d], {"time": now}), d, text)
            self.assertEqual((d["answer"], d["source"]), (want, "phone"))
        d = self.decision(kind="prose")
        t.take("AB12 use the blue one", [d], {"time": now})
        self.assertEqual(d["answer"], "use the blue one")
        self.assertIsNone(t.take("zz99 1", [self.decision()], {"time": now}))

    # covers: spec 0029 AC-8 (a reply older than the question never answers it)
    def test_old_reply(self):
        t = telegram.Topic(self.cfg, "", "")
        d = self.decision()
        when = int(ntfy.datetime.datetime.fromisoformat(d["asked"]).timestamp())
        self.assertIsNone(t.take("ab12 1", [d], {"time": when - 1}))
        self.assertIsNone(d["answer"])
        self.assertIs(t.take("ab12 1", [d], {"time": when}), d)

    # covers: spec 0029 AC-7, AC-8 (ntfy.Topic.wait drives the bot: tap answers, ack sent silently)
    def test_wait(self):
        p = mock.patch.object(ntfy, "POLL_EVERY", 0.01)
        p.start()
        self.addCleanup(p.stop)
        t = telegram.Topic(self.cfg, "test", "telegram test")
        d = self.decision()
        first = t.ping(d, lambda: False)
        self.bot.updates = [tap_update(9, "ab12 2", date=int(time.time()) + 1)]
        self.assertEqual(t.wait([d], first, 5, lambda: False, lambda d: None, lambda w: None), "answered")
        self.assertEqual(d["answer"], "no")
        self.assertTrue(self.bot.sent()[-1]["disable_notification"])


if __name__ == "__main__":
    unittest.main()
