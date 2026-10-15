import ast
import fcntl
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

RUNNER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RUNNER))
import ntfy  # noqa: E402
import telegram  # noqa: E402
import test_ntfy  # noqa: E402

TOKEN = "123456789:" + "A" * 35
CHAT = 4242


class FakeBot:
    """A local Bot API: records every call, numbers sent messages, serves queued updates from `offset`."""

    def __init__(self):
        self.calls, self.updates, self.taps, self.fail, self.mid = [], [], [], 0, 100
        self.refuse = set()
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
                    elif method in fake.refuse:
                        body = {"ok": False, "description": "refused"}
                    elif method == "getUpdates":
                        # Pending taps arrive once a question was sent, carrying its id.
                        # Spec 0033 AC-5: question messages start with the labeled id.
                        pings = [m_.group(1) for _, m, p in fake.calls if m == "sendMessage"
                                 for m_ in [re.match(r"^(?:<b>)?Question ([a-z0-9]{4}) \(", p["text"])] if m_]
                        if pings and fake.taps:
                            fake.updates += [tap_update(1000 + len(fake.updates), t.format(id=pings[-1]))
                                             for t in fake.taps]
                            fake.taps = []
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
        self.assertEqual(names - set(sys.stdlib_module_names), {"context", "ntfy", "wf"})

    # covers: spec 0029 AC-11 (a bot that never answers ends the call at the timeout, the error redacted)
    def test_hung_call_times_out(self):
        import socket
        s = socket.socket()
        self.addCleanup(s.close)
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        start = time.monotonic()
        with mock.patch.object(telegram, "API", f"http://127.0.0.1:{s.getsockname()[1]}"), \
                mock.patch.object(telegram, "TIMEOUT", 0.3):
            with self.assertRaises(telegram.ApiError) as e:
                telegram.api(TOKEN, "getMe")
        self.assertLess(time.monotonic() - start, 3)
        self.assertNotIn(TOKEN, str(e.exception))

    # covers: the e2e override reaches only a fake bot on this machine; any other value keeps the real API (the
    # token rides in the URL)
    def test_api_base(self):
        for value, want in (("http://127.0.0.1:8123", "http://127.0.0.1:8123"), ("https://evil.example", telegram.API),
                            ("http://127.0.0.1.evil.example:80", telegram.API), ("http://localhost:80", telegram.API),
                            ("http://127.0.0.1:8123/x", telegram.API), ("", telegram.API)):
            with mock.patch.dict(os.environ, {"WF_TELEGRAM_API": value}):
                self.assertEqual(telegram.api_base(), want, value)

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
        self.assertEqual(p["parse_mode"], "HTML")
        self.assertEqual(d["sent"], "Question ab12 (its name, so your reply finds it):\nShip it?\n1 yes\n2 no\n3 later\n4 see\n5 option 5\n"
                                    "tap a button, or reply to this message")
        self.assertTrue(p["text"].startswith("<b>Question ab12 (its name, so your reply finds it):</b>\n<b>Ship it?</b>\n"
                                             "1 yes\n"), p["text"])
        self.assertEqual(p["reply_markup"]["inline_keyboard"],
                         [[{"text": f"{n} {l}", "callback_data": f"ab12 {n}"}]
                          for n, l in enumerate(["yes", "no", "later", "see", "option 5"], 1)])
        self.assertNotIn("disable_notification", p)
        d = self.decision(kind="prose")
        d["question"] = "Acme wants what?"
        t.ping(d, lambda: False)
        p = self.bot.sent()[1]
        self.assertNotIn("reply_markup", p)
        self.assertEqual(d["sent"], "Question ab12 (its name, so your reply finds it):\nquestion waiting, see terminal\nreply to this message with your answer")

    # covers: spec 0038 AC-1, AC-2, AC-4 (every inserted value escaped, runner links are anchors whose text is the
    # href, the unverified words in a collapsed quote, d["sent"] stays plain)
    def test_styled(self):
        from unittest import mock
        t = telegram.Topic(self.cfg, "demo", "loop")
        d = self.decision(options=['<a href=x>ok', "no & <b>"])
        d.update(question="Ship <i>it & go?", learn="a <tag> & more", case="denied", allow="/r/x", context={
            "repo": "demo", "feature": "1. <b>Loop", "spec": "https://github.com/o/r/blob/main/a.md",
            "pr": {"number": 7, "url": "https://github.com/o/r/pull/7"}, "did": "see <script>x"})
        with mock.patch.object(ntfy, "private_names", return_value=["zzz"]):
            t.ping(d, lambda: False)
        html_ = self.bot.sent()[0]["text"]
        self.assertNotIn("<i>it", html_)
        self.assertIn("<b>Ship &lt;i&gt;it &amp; go?</b>", html_)
        self.assertIn("\nfeature: 1. &lt;b&gt;Loop\n", html_)
        self.assertIn("<blockquote expandable>see &lt;script&gt;x</blockquote>", html_)
        self.assertIn("\n1 &lt;a href=x&gt;ok\n2 no &amp; &lt;b&gt;\n", html_)
        self.assertIn("<i>learn: a &lt;tag&gt; &amp; more</i>", html_)
        self.assertIn('spec: <a href="https://github.com/o/r/blob/main/a.md">https://github.com/o/r/blob/main/a.md</a>', html_)
        self.assertIn('PR: #7 <a href="https://github.com/o/r/pull/7">https://github.com/o/r/pull/7</a>', html_)
        self.assertIn("<blockquote expandable>", html_)
        self.assertEqual(re.findall(r"<a href", html_), ["<a href"] * 2)
        self.assertTrue(d["sent"].startswith("Question ab12 (its name, so your reply finds it):\nShip <i>it & go?"))

    # covers: spec 0038 AC-5 (a refused HTML message goes once more as plain text)
    def test_styled_fallback(self):
        self.bot.fail = 1
        t = telegram.Topic(self.cfg, "demo", "loop")
        d = self.decision()
        self.assertEqual(t.ping(d, lambda: False), "101")
        first, second = self.bot.sent()
        self.assertEqual(first.get("parse_mode"), "HTML")
        self.assertNotIn("parse_mode", second)
        self.assertTrue(second["text"].startswith(d["sent"] + "\n"))

    # covers: spec 0038 AC-3 (the 4096 limit holds for the visible text, the escaping is not counted against it)
    def test_styled_length(self):
        import html
        t = telegram.Topic(self.cfg, "demo", "loop")
        d = self.decision()
        d.update(question='& < > " ' * 250, case="denied", allow="/r/x", context={
            "repo": "demo", "did": '& < > " ' * 400,
            "issues": [f"https://github.com/o/r/issues/{n}" for n in range(1000, 1100)]})
        with mock.patch.object(ntfy, "private_names", return_value=["zzz"]):
            t.ping(d, lambda: False)
        p = self.bot.sent()[0]
        self.assertEqual(p["parse_mode"], "HTML")
        visible = html.unescape(re.sub(r"<[^>]+>", "", p["text"]))
        self.assertLessEqual(len(visible), telegram.MAX)
        self.assertGreater(len(p["text"]), len(visible) + 1500)

    # covers: spec 0038 AC-4 (d["sent"] stays plain; a reply to the styled message still finds the question)
    def test_styled_reply(self):
        import html
        t = telegram.Topic(self.cfg, "demo", "loop")
        d = self.decision()
        d["question"] = "Ship <b>it</b> & go?"
        t.ping(d, lambda: False)
        self.assertEqual(d["sent"].split("\n")[:2], ["Question ab12 (its name, so your reply finds it):",
                                                     "Ship <b>it</b> & go?"])
        visible = html.unescape(re.sub(r"<[^>]+>", "", self.bot.sent()[0]["text"]))
        line, _, hint = telegram.entry(self.cfg, msg_update(5, "2", reply_to=visible))
        self.assertEqual((line["message"], hint), ("ab12 2", False))

    # covers: spec 0038 AC-6 (acks and reports keep plain text, no parse_mode)
    def test_acks_reports_plain(self):
        telegram.Topic(self.cfg, "demo", "loop").publish("ab12 accepted <b>x</b> & y", 2)
        telegram.send_report(self.cfg, "wf report <b>x</b> & y\nnext: wf")
        ack, report = self.bot.sent()
        self.assertNotIn("parse_mode", ack)
        self.assertNotIn("parse_mode", report)
        self.assertEqual(ack["text"], "wf demo: loop\nab12 accepted <b>x</b> & y")
        self.assertEqual(report["text"], "wf report <b>x</b> & y\nnext: wf")

    # covers: spec 0029 AC-4 (a send that fails while the run is stopping gives None after one try, no PingFailed)
    def test_ping_stopped(self):
        self.bot.fail = 3
        t = telegram.Topic(self.cfg, "demo", "loop")
        self.assertIsNone(t.ping(self.decision(), lambda: True))
        self.assertEqual(len(self.bot.sent()), 2)  # the styled try and its plain retry, once

    # covers: spec 0029 AC-4 (question cut at 1000, label at 200)
    def test_cuts(self):
        t = telegram.Topic(self.cfg, "demo", "loop")
        d = self.decision(options=["word " * 100])
        d["question"] = "word " * 400
        t.ping(d, lambda: False)
        q, label = d["sent"].split("\n")[1:3]
        self.assertLessEqual(len(q), 1000)
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

    # covers: spec 0029 AC-6, AC-8 (a tap keeps its question message's date, so a button on an older question
    # never answers a newer one that reused its id)
    def test_old_tap(self):
        d = self.decision()
        when = int(ntfy.datetime.datetime.fromisoformat(d["asked"]).timestamp())
        self.bot.updates = [tap_update(1, "ab12 1", date=when - 600)]
        t = telegram.Topic(self.cfg, "", "")
        line = t.poll(None)[0]
        self.assertIsNone(t.take(line["message"], [d], line))
        self.bot.updates.append(tap_update(2, "ab12 2", date=when))
        line = t.poll("u1")[0]
        self.assertIs(t.take(line["message"], [d], line), d)
        self.assertEqual(d["answer"], "no")

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


class TestInit(TelegramCase):
    def setUp(self):
        super().setUp()
        self.cfg_path.unlink()
        for name, value in (("INIT_WAIT", 1), ("LONG_POLL", 0)):
            p = mock.patch.object(telegram, name, value)
            p.start()
            self.addCleanup(p.stop)

    def init(self, token=TOKEN, rotate=False):
        out = io.StringIO()
        with mock.patch.object(telegram.getpass, "getpass", return_value=token), \
                mock.patch.object(telegram.secrets, "choice", return_value="k"), redirect_stdout(out):
            code = telegram.cmd_init(rotate)
        return code, out.getvalue()

    # covers: spec 0029 AC-10 (getMe, deleteWebhook, link and code, only a private exact /start binds the chat,
    # aliases and block from ntfy.json, wf connected, 0600 file, the token never printed)
    def test_init(self):
        test_ntfy.write_config(self.tmp / "config", "https://ntfy.sh", codes=["a1234567"])
        nc = json.loads((self.tmp / "config" / "wf" / "ntfy.json").read_text())
        nc.update(aliases={"/r": "home"}, block=["acme"])
        ntfy.write(nc)
        self.bot.updates = [msg_update(1, "/start kkkkkj", chat=77, sender=77),
                            msg_update(2, "/start kkkkkk", chat=-5, sender=88),
                            msg_update(3, "/start kkkkkk", chat=555, sender=555)]
        for u in self.bot.updates:
            u["message"]["chat"]["type"] = "group" if u["update_id"] == 2 else "private"
        code, out = self.init()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines()[:3], ["bot: @wf_test_bot", "open https://t.me/wf_test_bot?start=kkkkkk",
                                                "or send /start kkkkkk to @wf_test_bot"])
        self.assertEqual(out.splitlines()[-1], f"saved {telegram.path()}")
        self.assertNotIn(TOKEN, out)
        self.assertEqual(json.loads(Path(telegram.path()).read_text()),
                         {"token": TOKEN, "chat_id": 555, "aliases": {"/r": "home"}, "block": ["acme"]})
        self.assertEqual(os.stat(telegram.path()).st_mode & 0o777, 0o600)
        self.assertEqual([m for _, m, _ in self.bot.calls][:2], ["getMe", "deleteWebhook"])
        self.assertEqual(self.bot.sent(), [{"chat_id": 555, "text": "wf connected"}])
        self.assertEqual(self.bot.sent("getUpdates")[-1]["offset"], 4)
        self.assertEqual(self.init()[0], 2)
        self.assertEqual(self.init(rotate=True)[0], 0)

    # covers: spec 0029 AC-10 (a malformed token is refused before any call; no /start in time writes nothing)
    def test_refused(self):
        code, out = self.init(token="12345:short")
        self.assertEqual((code, self.bot.calls), (2, []))
        self.assertNotIn("12345:short", out)
        code, out = self.init()
        self.assertEqual((code, out.splitlines()[-1]), (6, "no /start kkkkkk received"))
        self.assertFalse(Path(telegram.path()).exists())

    # covers: spec 0029 AC-10 (wf telegram test: one question, a tap, accepted: <answer>)
    def test_test(self):
        write_cfg(self.tmp / "config")
        self.bot.taps = ["{id} 1"]
        out = io.StringIO()
        with mock.patch.object(ntfy, "POLL_EVERY", 0.01), redirect_stdout(out):
            self.assertEqual(telegram.cmd_test(), 0)
        self.assertEqual(out.getvalue().splitlines()[-1], "accepted: yes")
        self.assertEqual(self.bot.sent()[0]["reply_markup"]["inline_keyboard"][1][0]["text"], "2 no")

    # covers: spec 0029 AC-10 (wf telegram init|test are wired; test refuses without a file)
    def test_cli(self):
        r = subprocess.run([sys.executable, str(RUNNER / "wf.py"), "telegram", "test"], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, env={**os.environ, "HOME": str(self.tmp)})
        self.assertEqual((r.returncode, r.stdout.split(": ")[:2]), (5, ["refused", "no_telegram"]))
        write_cfg(self.tmp / "config")
        r = subprocess.run([sys.executable, str(RUNNER / "wf.py"), "telegram", "init"], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, env={**os.environ, "HOME": str(self.tmp)})
        self.assertEqual(r.returncode, 2)
        self.assertIn("use wf telegram init --rotate", r.stdout)


import test_run  # noqa: E402  (as a module, so its own test classes do not run twice)


class TestRunChannel(test_run.RunCase):
    """wf run end to end with the fake bot: test_run's wrapper with telegram.API pointed at it."""

    def setUp(self):
        super().setUp()
        self.bot = FakeBot()
        self.addCleanup(self.bot.close)

    def cmd(self, *args, grace=30, mode="-"):
        if "--max-wait" not in args:
            args = (*args, "--max-wait", "0.0001")
        wrapper = test_run.WRAPPER.replace("import ntfy, run, wf",
                                           f"import ntfy, run, wf, telegram\ntelegram.API = {self.bot.url!r}")
        return [sys.executable, "-c", wrapper, str(RUNNER), str(grace), mode, "run", *args]

    # covers: spec 0029 AC-2 (an invalid telegram.json refuses no_telegram and never falls back; no file -> ntfy)
    def test_refusals(self):
        p = write_cfg(self.tmp / "config", chat_id="x")
        r = self.wf("demo", "-y")
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertIn("refused: no_telegram: chat_id must be an integer", r.stdout)
        self.assertNotIn(TOKEN, r.stdout + r.stderr)
        self.assertEqual(self.calls(), [])
        p.unlink()
        self.ntfy_config.unlink()
        r = self.wf("demo", "-y")
        self.assertIn("refused: no_ntfy: no telegram.json or ntfy.json, run wf telegram init", r.stdout)

    # covers: spec 0029 AC-2, AC-7, AC-8 (the question goes to the bot, a tap answers it, the run resumes;
    # no one time code warning for Telegram)
    def test_tap_resumes(self):
        write_cfg(self.tmp / "config")
        test_run.write_config(self.tmp / "config", "http://127.0.0.1:9", codes=["a1234567"] * 4)
        self.bot.taps = ["{id} 2"]
        self.steps([test_run.ask(), {}, {}, {"tick": False}])
        r = self.wf("demo", "-y", "--max-wait", "0.01", mode="fast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("one time codes left", r.stdout)
        _, rec = self.run_record()
        d = rec["decisions"][0]
        self.assertEqual((d["answer"], d["source"]), ("SQLite", "phone"))
        self.assertEqual(self.argv(2)["argv"][1], "The user answered your DECISION NEEDED question: SQLite")
        texts = [p["text"] for p in self.bot.sent()]
        # Spec 0038: the question message is styled HTML.
        self.assertTrue(texts[0].startswith(f"<b>Question {d['id']} (its name, so your reply finds it):</b>\n"
                                            "<b>Which storage engine?</b>\n"), texts[0])
        self.assertIn("\n1 Postgres (recommended)\n2 SQLite\n", texts[0])
        # Spec 0033 AC-4: the from block, with the repo and feature.
        # No names list in the test home: the repo shows by its hashed label (security review, information disclosure).
        self.assertRegex(texts[0], r"\n<b>from:</b>\nrepo: repo-[0-9a-f]{4}\nfeature: 1\. Loop\n")
        self.assertTrue(any(t.endswith(f"\nGot your answer to question {d['id']}: SQLite. Resuming.") for t in texts))
        self.assertEqual(self.bot.sent("answerCallbackQuery"), [{"callback_query_id": "cq1000"}])

    # covers: spec 0040 AC-1 (telegram.json set up while the run waits on an ntfy question: the run switches, logs
    # it once, sends the open question again on Telegram, and a tap there resumes it)
    def test_switch_while_waiting(self):
        self.bot.taps = ["{id} 2"]
        self.steps([test_run.ask(), {}, {}, {"tick": False}])
        p = self.start("demo", "-y", "--max-wait", "0.01", mode="fast")
        end = time.monotonic() + 20
        while not any(re.match(r"^[a-z0-9]{4}: ", m["message"]) for m in self.report_ntfy.messages):
            self.assertLess(time.monotonic(), end, "no question on ntfy")
            time.sleep(0.05)
        write_cfg(self.tmp / "config")
        out, err = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 0, out + err)
        folder, rec = self.run_record()
        d = rec["decisions"][0]
        self.assertEqual((d["answer"], d["source"]), ("SQLite", "phone"))
        log = (folder / "log.txt").read_text()
        self.assertEqual(log.count("phone channel now Telegram, open questions sent again there"), 1, log)
        self.assertTrue(any(t.startswith(f"<b>Question {d['id']} (") for t in (p_["text"] for p_ in self.bot.sent())))


if __name__ == "__main__":
    unittest.main()
