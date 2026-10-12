import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlparse

RUNNER = Path(__file__).resolve().parent.parent
WF = RUNNER / "wf.py"
sys.path.insert(0, str(RUNNER))
import ntfy  # noqa: E402

TOPIC = "T" * 32


class FakeNtfy:
    """A local ntfy: records JSON publishes, serves polls after `since`. Each pending
    reply is posted once a ping exists, with {id} set to that ping's decision id."""

    def __init__(self):
        self.messages, self.posts, self.polls = [], [], []
        self.replies, self.fail_posts, self.fail_polls, self.hold_polls = [], 0, 0, 0
        self.lock = threading.Lock()
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def send(self, code, body=b""):
                self.send_response(code)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                with fake.lock:
                    if self.path == "/":
                        fake.posts.append(json.loads(raw))
                        if fake.fail_posts:
                            fake.fail_posts -= 1
                            return self.send(500)
                        mid = fake.add(json.loads(raw)["message"])
                    else:
                        mid = fake.add(raw.decode())
                self.send(200, json.dumps({"id": mid}).encode())

            def do_GET(self):
                u = urlparse(self.path)
                with fake.lock:
                    fake.polls.append(self.path)
                    if fake.fail_polls:
                        fake.fail_polls -= 1
                        return self.send(500)
                    pings = [m for m in fake.messages if re.match(r"^[a-z0-9]{4}: ", m["message"])]
                    if pings and fake.replies and len(fake.polls) > fake.hold_polls:
                        did = pings[-1]["message"][:4]
                        for r in fake.replies:
                            fake.add(r.format(id=did, ID=did.upper()))
                        fake.replies = []
                    since = parse_qs(u.query).get("since", ["all"])[0]
                    ids = [m["id"] for m in fake.messages]
                    after = fake.messages[ids.index(since) + 1:] if since in ids else fake.messages
                self.send(200, "".join(json.dumps(m) + "\n" for m in after).encode())

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def add(self, text):
        mid = f"m{len(self.messages) + 1}"
        self.messages.append({"id": mid, "time": 0, "event": "message", "topic": TOPIC, "message": text})
        return mid

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def write_config(home, server, codes=("goodcode",), **extra):
    cfg = {"server": server, "topic": TOPIC, "codes": [hashlib.sha256(c.encode()).hexdigest() for c in codes],
           "aliases": {}, "block": []}
    cfg.update(extra)
    p = Path(home) / "wf" / "ntfy.json"
    p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    p.write_text(json.dumps(cfg))
    p.chmod(0o600)
    return p


class NtfyCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.config = self.tmp / "config"
        p = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.config)})
        p.start()
        self.addCleanup(p.stop)
        self.fake = FakeNtfy()
        self.addCleanup(self.fake.close)
        for name, value in (("RETRY_GAP", 0.05), ("POLL_EVERY", 0.05), ("SLICE", 0.01)):
            p = mock.patch.object(ntfy, name, value)
            p.start()
            self.addCleanup(p.stop)

    def cfg(self, **kw):
        write_config(self.config, self.fake.url, **kw)
        return ntfy.load()

    def decision(self, kind="panel", options=("Postgres", "SQLite", "Both"), multi=False, did="ab12"):
        return {"id": did, "kind": kind, "question": "Which storage engine?", "options": list(options),
                "multi": multi, "answer": None, "source": None, "answered": None, "ignored": 0, "sent": None}


class TestConfig(NtfyCase):
    # covers: AC-2 (every invalid case, the reason names it)
    def test_invalid(self):
        good = {"server": "https://ntfy.sh", "topic": TOPIC, "codes": ["a" * 64], "aliases": {}, "block": []}
        cases = [("missing", None, "is missing, run wf ntfy init"),
                 ("not object", [], "is not a JSON object"),
                 ("short topic", {**good, "topic": "x" * 31}, "topic"),
                 ("bad topic", {**good, "topic": "x" * 31 + "/"}, "topic"),
                 ("http server", {**good, "server": "http://ntfy.sh"}, "server"),
                 ("no codes", {**good, "codes": []}, "codes"),
                 ("bad code", {**good, "codes": ["A" * 64]}, "codes"),
                 ("aliases", {**good, "aliases": {"x": 1}}, "aliases"),
                 ("block", {**good, "block": "acme"}, "block")]
        p = self.config / "wf" / "ntfy.json"
        p.parent.mkdir(parents=True)
        for name, body, why in cases:
            with self.subTest(name):
                if body is None:
                    p.unlink(missing_ok=True)
                else:
                    p.write_text(json.dumps(body))
                    p.chmod(0o600)
                with self.assertRaisesRegex(ntfy.Invalid, re.escape(why)):
                    ntfy.load()
        p.write_text(json.dumps(good))
        for mode in (0o640, 0o604, 0o620):
            with self.subTest(oct(mode)):
                p.chmod(mode)
                with self.assertRaisesRegex(ntfy.Invalid, "readable or writable by others"):
                    ntfy.load()
        p.chmod(0o600)
        self.assertEqual(ntfy.load()["topic"], TOPIC)
        for server in ("http://127.0.0.1:8080", "http://localhost:1"):
            p.write_text(json.dumps({**good, "server": server}))
            self.assertEqual(ntfy.load()["server"], server)
        p.write_text(json.dumps({**good, "codes": []}))
        self.assertEqual(ntfy.load(need_codes=False)["codes"], [])


class TestScrub(NtfyCase):
    # covers: AC-7 (first line, paths, URLs, emails, backticks, control characters, length)
    def test_scrub(self):
        q = "Use `src/db.py` or ~/x, mail a@b.co, see https://x.io and C:\\temp now?\x1b[31m\nsecond line"
        self.assertEqual(ntfy.scrub(q, 140), "Use or mail see and now?[31m")
        self.assertEqual(len(ntfy.scrub("word " * 60, 140)), 139)

    # covers: AC-7 (alias, hashed label, block list replacements)
    def test_labels_and_block(self):
        repo = str(self.tmp)
        cfg = self.cfg(aliases={repo: "home"}, block=["Acme"])
        self.assertEqual(ntfy.repo_label(cfg, repo), "home")
        other = str(self.tmp / "other")
        self.assertEqual(ntfy.repo_label(cfg, other), "repo-" + hashlib.sha1(other.encode()).hexdigest()[:4])
        t = ntfy.Topic(cfg, "home", "Acme billing")
        self.assertEqual(t.title, "wf home: feature")
        d = self.decision(options=["Keep ACME api", "Drop it"])
        d["question"] = "Should acme pay?"
        t.ping(d, lambda: False)
        self.assertEqual(d["sent"], "ab12: question waiting, see terminal\n1 option 1\n2 Drop it\nreply ab12 <n>")

    # covers: spec 0005 AC-7 (a label that scrubs to nothing is sent as option <n>, never a blank button)
    def test_empty_label(self):
        t = ntfy.Topic(self.cfg(), "home", "x")
        d = self.decision(options=["/tmp/x", "`rm -rf`", "Keep"])
        t.ping(d, lambda: False)
        self.assertEqual(d["sent"], "ab12: Which storage engine?\n1 option 1\n2 option 2\n3 Keep\nreply ab12 <n>")
        self.assertEqual([a["label"] for a in self.fake.posts[0]["actions"]], ["1 option 1", "2 option 2", "3 Keep"])


class TestPublish(NtfyCase):
    # covers: AC-7 (JSON at the server root, actions for 3 options, commas and non ASCII intact)
    def test_ping_shape(self):
        cfg = self.cfg()
        t = ntfy.Topic(cfg, "demo", "5. Parking")
        d = self.decision(options=["Yes, find them for me", "Ñandú ü", "C", "D"])
        mid = t.ping(d, lambda: False)
        body = self.fake.posts[0]
        self.assertEqual(body["topic"], TOPIC)
        self.assertEqual((body["title"], body["priority"], body["tags"]), ("wf demo: 5. Parking", 4, ["question"]))
        self.assertEqual(body["message"], "ab12: Which storage engine?\n1 Yes, find them for me\n2 Ñandú ü\n3 C\n4 D\nreply ab12 <n>")
        self.assertEqual(body["actions"], [
            {"action": "http", "label": f"{n} {l}", "url": f"{self.fake.url}/{TOPIC}", "method": "POST",
             "body": f"ab12 {n}", "clear": True}
            for n, l in ((1, "Yes, find them for me"), (2, "Ñandú ü"), (3, "C"))])
        self.assertIn(mid, t.own)
        p = self.decision(kind="prose", options=())
        t.ping(p, lambda: False)
        self.assertNotIn("actions", self.fake.posts[1])
        self.assertTrue(self.fake.posts[1]["message"].endswith("\nreply ab12 <code> <text>"))

    # covers: AC-7 (two retries, then PingFailed; a stop during the gap returns None)
    def test_retries(self):
        t = ntfy.Topic(self.cfg(), "demo", "f")
        self.fake.fail_posts = 2
        self.assertIsNotNone(t.ping(self.decision(), lambda: False))
        self.assertEqual(len(self.fake.posts), 3)
        self.fake.fail_posts = 3
        with self.assertRaisesRegex(ntfy.PingFailed, "500"):
            t.ping(self.decision(), lambda: False)
        self.fake.fail_posts = 3
        self.assertIsNone(t.ping(self.decision(), lambda: True))


class TestReplies(NtfyCase):
    def wait(self, t, ds, replies, max_wait=5):
        first = t.ping(ds[0], lambda: False)
        self.fake.replies = replies
        warns = []
        end = t.wait(ds, first, max_wait, lambda: False, lambda d: None, warns.append)
        return end, warns

    # covers: AC-8 (numbers, n,m on multi, label, ack published and skipped)
    def test_forms(self):
        for options, multi, reply, answer in [
                (("Postgres", "SQLite"), False, "{id} 2", "SQLite"),
                (("A", "B", "C"), True, "{id} 1,3", "A, C"),
                (("Postgres", "SQLite"), False, "  {ID}   sQLite ", "SQLite")]:
            with self.subTest(reply):
                self.fake.messages.clear()
                t = ntfy.Topic(self.cfg(), "demo", "f")
                d = self.decision(options=options, multi=multi)
                end, _ = self.wait(t, [d], [reply])
                self.assertEqual((end, d["answer"], d["source"]), ("answered", answer, "phone"))
                self.assertEqual(self.fake.messages[-1]["message"], f"{d['id']} accepted, resuming")
                self.assertEqual(self.fake.posts[-1]["priority"], 2)

    # covers: AC-8 (a second reply to an answered id changes nothing)
    def test_answered_once(self):
        t = ntfy.Topic(self.cfg(), "demo", "f")
        d = self.decision(options=("A", "B"))
        end, _ = self.wait(t, [d], ["{id} 2", "{id} 1"])
        self.assertEqual((end, d["answer"]), ("answered", "B"))

    # covers: AC-8 (wf's own second ping is skipped, so a code-like word in it is not burned)
    def test_own_skipped(self):
        t = ntfy.Topic(self.cfg(codes=("goodcode",)), "demo", "f")
        d1 = self.decision(options=("A", "B"))
        d2 = self.decision(kind="prose", options=(), did="cd34")
        d2["question"] = "keep goodcode here?"
        first = t.ping(d1, lambda: False)
        t.ping(d2, lambda: False)
        self.fake.replies = ["ab12 1", "{id} goodcode free text"]
        end = t.wait([d1, d2], first, 5, lambda: False, lambda d: None, print)
        self.assertEqual((end, d1["answer"], d2["answer"]), ("answered", "A", "free text"))

    # covers: AC-8 (ignored replies: unknown id, out of range, n,m on single, prose number, bad code, maybe)
    def test_ignored(self):
        t = ntfy.Topic(self.cfg(), "demo", "f")
        d = self.decision(options=("A", "B"))
        end, _ = self.wait(t, [d], ["zz99 1", "{id} 3", "{id} 1,2", "{id} maybe", "{id} badcode1 text", "hello"],
                           max_wait=0.3)
        self.assertEqual((end, d["answer"], d["ignored"]), ("timeout", None, 4))
        t = ntfy.Topic(self.cfg(), "demo", "f")
        p = self.decision(kind="prose", options=())
        end, _ = self.wait(t, [p], ["{id} 1"], max_wait=0.3)
        self.assertEqual((end, p["ignored"]), ("timeout", 1))

    # covers: AC-8 (a good code answers once, is removed from the file, mode kept; a reuse is ignored)
    def test_code(self):
        cfg = self.cfg(codes=("goodcode", "spare123"))
        t = ntfy.Topic(cfg, "demo", "f")
        p = self.decision(kind="prose", options=())
        end, _ = self.wait(t, [p], ["{id} goodcode Use Postgres, please"])
        self.assertEqual((end, p["answer"]), ("answered", "Use Postgres, please"))
        f = self.config / "wf" / "ntfy.json"
        self.assertEqual(json.loads(f.read_text())["codes"], [hashlib.sha256(b"spare123").hexdigest()])
        self.assertEqual(stat.S_IMODE(f.stat().st_mode), 0o600)
        q = self.decision(kind="prose", options=(), did="cd34")
        end, _ = self.wait(t, [q], ["{id} goodcode again"], max_wait=0.3)
        self.assertEqual((end, q["ignored"]), ("timeout", 1))

    # covers: AC-8 (a code another run used after this one loaded the config is dead here too)
    def test_code_used_elsewhere(self):
        cfg = self.cfg(codes=("goodcode", "spare123"))
        t = ntfy.Topic(cfg, "demo", "f")
        other = ntfy.load()
        self.assertEqual(ntfy.burn(other, {hashlib.sha256(b"goodcode").hexdigest()}),
                         {hashlib.sha256(b"goodcode").hexdigest()})
        p = self.decision(kind="prose", options=())
        end, _ = self.wait(t, [p], ["{id} goodcode replayed"], max_wait=0.3)
        self.assertEqual((end, p["answer"], p["ignored"]), ("timeout", None, 1))

    # covers: AC-8 (phishing: a code typed for an unknown id is burned anyway)
    def test_phishing(self):
        cfg = self.cfg(codes=("goodcode",))
        t = ntfy.Topic(cfg, "demo", "f")
        p = self.decision(kind="prose", options=())
        end, _ = self.wait(t, [p], ["zz99 goodcode yes", "{id} goodcode run rm"], max_wait=0.3)
        self.assertEqual((end, p["answer"]), ("timeout", None))
        self.assertEqual(json.loads((self.config / "wf" / "ntfy.json").read_text())["codes"], [])

    # covers: AC-9 (a poll failure warns once and keeps polling)
    def test_poll_failure(self):
        t = ntfy.Topic(self.cfg(), "demo", "f")
        self.fake.fail_polls = 3
        d = self.decision()
        end, warns = self.wait(t, [d], ["{id} 1"])
        self.assertEqual(end, "answered")
        self.assertEqual(len(warns), 1)
        self.assertTrue(warns[0].startswith("ntfy poll failed: "))

    # covers: AC-8 (the poll starts at the first ping and moves its cursor)
    def test_cursor(self):
        t = ntfy.Topic(self.cfg(), "demo", "f")
        d = self.decision()
        self.wait(t, [d], ["{id} 1"])
        self.assertIn("since=m1", self.fake.polls[0])
        self.assertTrue(all("poll=1" in p for p in self.fake.polls))

    # covers: AC-9 (a stop during the wait returns at once)
    def test_stop(self):
        t = ntfy.Topic(self.cfg(), "demo", "f")
        d = self.decision()
        first = t.ping(d, lambda: False)
        self.assertEqual(t.wait([d], first, 60, lambda: True, lambda d: None, print), "interrupted")


class TestCommands(NtfyCase):
    def wf(self, *args):
        env = {**os.environ, "XDG_CONFIG_HOME": str(self.config)}
        return subprocess.run([sys.executable, str(WF), "ntfy", *args], capture_output=True, text=True, env=env, timeout=60)

    # covers: AC-1 (init: modes, fields, codes printed once and stored hashed; refusal; rotate keeps fields)
    def test_init(self):
        r = self.wf("init")
        self.assertEqual(r.returncode, 0, r.stderr)
        f = self.config / "wf" / "ntfy.json"
        self.assertEqual(stat.S_IMODE(f.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(f.parent.stat().st_mode), 0o700)
        cfg = json.loads(f.read_text())
        self.assertEqual(sorted(cfg), ["aliases", "block", "codes", "server", "topic"])
        self.assertEqual((cfg["server"], cfg["aliases"], cfg["block"]), ("https://ntfy.sh", {}, []))
        self.assertEqual(len(cfg["topic"]), 32)
        self.assertIn(f"subscribe: https://ntfy.sh/{cfg['topic']}", r.stdout)
        codes = re.findall(r"^[a-z2-9]{8}$", r.stdout, re.M)
        self.assertEqual(len(codes), 20)
        self.assertTrue(all(set(c) <= set(ntfy.CODE_CHARS) for c in codes))
        self.assertEqual(cfg["codes"], [hashlib.sha256(c.encode()).hexdigest() for c in codes])
        self.assertNotIn(codes[0], f.read_text())
        r = self.wf("init")
        self.assertEqual(r.returncode, 2)
        cfg.update(aliases={"/r": "r"}, block=["acme"], server="https://example.org")
        f.write_text(json.dumps(cfg))
        r = self.wf("init", "--rotate")
        self.assertEqual(r.returncode, 0, r.stdout)
        new = json.loads(f.read_text())
        self.assertNotEqual(new["topic"], cfg["topic"])
        self.assertNotEqual(new["codes"], cfg["codes"])
        self.assertEqual((new["server"], new["aliases"], new["block"]), ("https://example.org", {"/r": "r"}, ["acme"]))

    # covers: AC-1 (codes replaces only the codes, also once they ran out)
    def test_codes(self):
        write_config(self.config, self.fake.url, codes=())
        r = self.wf("codes")
        self.assertEqual(r.returncode, 0, r.stdout)
        cfg = json.loads((self.config / "wf" / "ntfy.json").read_text())
        self.assertEqual(len(cfg["codes"]), 20)
        self.assertEqual(cfg["topic"], TOPIC)
        self.assertEqual(len(re.findall(r"^[a-z2-9]{8}$", r.stdout, re.M)), 20)
        (self.config / "wf" / "ntfy.json").unlink()
        self.assertEqual(self.wf("codes").returncode, 5)

    # covers: AC-1 (test pings yes/no as `test`, prints accepted)
    def test_test(self):
        write_config(self.config, self.fake.url)
        self.fake.replies = ["{id} 1"]
        r = self.wf("test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("accepted: yes", r.stdout)
        self.assertEqual(self.fake.posts[0]["title"], "wf test: ntfy test")
        self.assertEqual([a["label"] for a in self.fake.posts[0]["actions"]], ["1 yes", "2 no"])

    # covers: AC-1 (test exits 6 on ping_failed)
    def test_test_fails(self):
        write_config(self.config, "http://127.0.0.1:1")
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(ntfy.cmd_test(), 6)
        self.assertIn("stopped: ping_failed: ", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
