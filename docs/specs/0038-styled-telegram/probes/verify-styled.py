"""Spec 0038 verify driver: real Topic.ping and send_report against a local fake Bot API (WF_TELEGRAM_API), then
checks what Telegram would receive. Usage: verify-styled.py [RUNNER_DIR]  (default: this repo's runner/).
Prints one PASS/FAIL line per step, exits 1 on any FAIL."""
import html
import html.parser
import json
import os
import re
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RUNNER = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[4] / "runner").resolve()
sys.path.insert(0, str(RUNNER))
tmp = Path(tempfile.mkdtemp())
os.environ.update(XDG_CONFIG_HOME=str(tmp / "config"), XDG_STATE_HOME=str(tmp / "state"))
calls, refuse_html = [], [0]


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        method = self.path.rsplit("/", 1)[1]
        kind = self.headers.get("Content-Type", "")
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        p = json.loads(raw) if kind == "application/json" else {"raw": raw.decode()}
        calls.append((method, p))
        if method == "sendMessage" and p.get("parse_mode") == "HTML" and refuse_html[0]:
            refuse_html[0] -= 1
            body = {"ok": False, "description": "Bad Request: can't parse entities: unsupported start tag"}
        else:
            body = {"ok": True, "result": {"message_id": len(calls)}}
        out = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["WF_TELEGRAM_API"] = f"http://127.0.0.1:{srv.server_port}"
cfgp = tmp / "config" / "wf" / "telegram.json"
cfgp.parent.mkdir(parents=True)
cfgp.write_text(json.dumps({"token": "123456789:" + "A" * 35, "chat_id": 4242, "aliases": {}, "block": ["acme"]}))
cfgp.chmod(0o600)

import ntfy  # noqa: E402
import telegram  # noqa: E402
ntfy.private_names = lambda: ["zzz"]
ntfy.RETRY_GAP = 0.01
cfg = telegram.load()


class Tags(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.stack, self.text, self.anchors, self.cur = [], [], [], [], None

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, attrs))
        self.stack.append(tag)
        if tag == "a":
            self.cur = [dict(attrs).get("href"), ""]

    def handle_endtag(self, tag):
        assert self.stack and self.stack.pop() == tag, f"unbalanced </{tag}>"
        if tag == "a":
            self.anchors.append(tuple(self.cur))
            self.cur = None

    def handle_data(self, data):
        self.text.append(data)
        if self.cur:
            self.cur[1] += data


def parse(s):
    t = Tags()
    t.feed(s)
    t.close()
    assert not t.stack, f"unclosed {t.stack}"
    return t


results = []


def step(name, fn):
    try:
        fn()
        results.append(f"PASS {name}")
    except Exception as e:
        results.append(f"FAIL {name}: {type(e).__name__}: {e}")


SPEC = "https://github.com/o/r/blob/main/docs/specs/0038-x/index.md"
PR = "https://github.com/o/r/pull/7"
ISSUE = "https://github.com/o/r/issues/3"


def evil(**over):
    d = {"id": "ab12", "kind": "panel", "multi": False, "answer": None, "ignored": 0, "repo": None,
         "asked": "2026-10-14T10:00:00-05:00", "case": "denied", "allow": "/r/x",
         "question": 'Ship <a href="https://evil.example">it</a> & <b>go</b>?',
         "learn": "a <i>tag</i> & more", "options": ['<a href="https://evil.example">ok</a>', "no & <b>"],
         "context": {"repo": "demo", "feature": 'Loop & <b> "q" <i>', "spec": SPEC, "issues": [ISSUE],
                     "pr": {"number": 7, "url": PR}, "did": 'see <a href="https://evil.example">here</a> &amp; <script>'}}
    d.update(over)
    return d


def sent_last():
    return [p for m, p in calls if m == "sendMessage"][-1]


def v1():
    calls.clear()
    telegram.Topic(cfg, "demo", "loop").ping(evil(), lambda: False)
    p = sent_last()
    assert p.get("parse_mode") == "HTML", p.get("parse_mode")
    t = parse(p["text"])
    names = {tag for tag, _ in t.tags}
    assert names <= {"b", "i", "a", "blockquote"}, names
    for tag, attrs in t.tags:
        if tag == "blockquote":
            assert attrs == [("expandable", None)], attrs
        elif tag == "a":
            assert [k for k, _ in attrs] == ["href"], attrs
        else:
            assert attrs == [], (tag, attrs)
    hrefs = sorted(h for h, _ in t.anchors)
    assert hrefs == sorted([SPEC, PR, ISSUE]), hrefs
    vis = "".join(t.text)
    # Earlier specs' scrub drops path like tokens from scrubbed fields first; what is left must arrive as text.
    for raw in ('Ship <a href="https://evil.example">it</a> & <b>go</b>?', "1 <a\n", "2 no & <b>\n",
                "see <a &amp; <script>", "learn: a & more", 'feature: Loop & <b> "q" <i>\n'):
        assert raw in vis, f"injected text not shown as plain: {raw!r}"


def v2():
    calls.clear()
    telegram.Topic(cfg, "demo", "loop").ping(evil(), lambda: False)
    s = sent_last()["text"]
    lines = s.split("\n")
    assert lines[0] == "<b>Question ab12 (its name, so your reply finds it):</b>", lines[0]
    assert lines[1].startswith("<b>Ship &lt;a href=") and lines[1].endswith("</b>"), lines[1]
    assert lines[2].startswith("<i>learn: ") and lines[2].endswith("</i>"), lines[2]
    assert lines[3] == "<b>from:</b>", lines[3]
    for h in (SPEC, PR, ISSUE):
        assert f'<a href="{h}">{h}</a>' in s, h
    t = parse(s)
    assert all(h == txt for h, txt in t.anchors), t.anchors
    m = re.search(r"<blockquote expandable>(.*?)</blockquote>", s, re.S)
    assert m and m.group(1) == "see &lt;a &amp;amp; &lt;script&gt;", s
    assert re.search(r"<b>what the step said, unverified:</b>\n<blockquote expandable>", s), s
    assert "\n1 &lt;a\n" in s and "\n2 no &amp; &lt;b&gt;\n" in s, s
    assert "\ntap a button, or reply to this message\nwf demo: loop" in s, s


def v3():
    calls.clear()
    d = evil(question='& < > " ' * 250, learn='& < > " ' * 80)
    d["context"]["did"] = '& < > " ' * 400
    d["context"]["why"] = "x"
    # Over 4000 characters of runner links: the from: block no longer fits and must go.
    d["context"]["issues"] = [f"https://github.com/o/r/issues/{n}" for n in range(1000, 1100)]
    telegram.Topic(cfg, "demo", "loop").ping(d, lambda: False)
    p = sent_last()
    assert p.get("parse_mode") == "HTML"
    vis = "".join(parse(p["text"]).text)
    assert len(vis) <= telegram.MAX, (len(vis), telegram.MAX)
    assert len(p["text"]) > len(vis) + 1500, "the question should be heavily escaped"


def v4():
    calls.clear()
    d = evil()
    telegram.Topic(cfg, "demo", "loop").ping(d, lambda: False)
    assert "<b>" not in d["sent"].split("\n")[0] and d["sent"].startswith("Question ab12 (its name"), d["sent"]
    assert 'Ship <a href="https://evil.example">it</a> & <b>go</b>?' in d["sent"], d["sent"]
    assert "&amp;" not in d["sent"].split("\n")[1], d["sent"]
    vis = "".join(parse(sent_last()["text"]).text)
    upd = {"update_id": 5, "message": {"message_id": 9, "chat": {"id": 4242}, "from": {"id": 4242}, "date": 1,
                                        "text": "2", "reply_to_message": {"from": {"id": 1, "is_bot": True}, "text": vis}}}
    line, _, hint = telegram.entry(cfg, upd)
    assert line["message"] == "ab12 2" and not hint, line


def v5():
    calls.clear()
    refuse_html[0] = 1
    d = evil()
    mid = telegram.Topic(cfg, "demo", "loop").ping(d, lambda: False)
    sm = [p for m, p in calls if m == "sendMessage"]
    assert mid and len(sm) == 2, (mid, len(sm))
    assert sm[0].get("parse_mode") == "HTML" and "parse_mode" not in sm[1], sm
    assert sm[1]["text"] == d["sent"] + "\nwf demo: loop", sm[1]["text"]


def v6():
    calls.clear()
    t = telegram.Topic(cfg, "demo", "loop")
    t.publish("ab12 accepted <b>x</b>", 2)
    telegram.send_report(cfg, "wf report <b>x</b> & y\nnext: wf")
    sm = [p for m, p in calls if m == "sendMessage"]
    assert len(sm) == 2 and all("parse_mode" not in p for p in sm), sm
    assert sm[0]["text"] == "wf demo: loop\nab12 accepted <b>x</b>", sm[0]["text"]
    assert sm[1]["text"] == "wf report <b>x</b> & y\nnext: wf", sm[1]["text"]


for n, f in (("V1 AC-1 HTML mode, only runner tags, injected markup shown as text", v1),
             ("V2 AC-2 layout, links open what they show, quote collapsed", v2),
             ("V3 AC-3 visible text within 4096 with heavy escaping", v3),
             ("V4 AC-4 sent stays plain, a swiped reply still finds the id", v4),
             ("V5 AC-5 parse error resends plain once", v5),
             ("V6 AC-6 acks and reports unchanged plain", v6)):
    step(n, f)
srv.shutdown()
print("\n".join(results))
sys.exit(any(r.startswith("FAIL") for r in results))
