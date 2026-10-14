#!/usr/bin/env python3
# /check verify telegram (spec 0029): drive runner/telegram.py, report.py, run.py and `wf telegram` against a
# local fake Bot API. Usage: drive.py <repo>
import fcntl, json, os, re, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = sys.argv[1]
RUNNER = os.environ.get("RUNNER") or os.path.join(REPO, "runner")
TOKEN = "123456:" + "Ab9_-" * 7
WORK = tempfile.mkdtemp(prefix="tgv.")
os.environ["XDG_CONFIG_HOME"] = os.path.join(WORK, "config")
os.environ["XDG_STATE_HOME"] = os.path.join(WORK, "state")
os.makedirs(os.environ["XDG_CONFIG_HOME"])
os.makedirs(os.environ["XDG_STATE_HOME"])


class S:
    reqs, updates, mid, refuse_html, lock = [], [], 100, False, threading.Lock()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        m = re.fullmatch(r"/bot(.+?)/(\w+)", self.path)
        method = m.group(2)
        kind = self.headers.get("Content-Type", "")
        p = json.loads(raw) if kind.startswith("application/json") else {"_raw": raw.decode()}
        with S.lock:
            S.reqs.append((method, p, m.group(1)))
        ok, res = True, True
        if method == "failme":
            ok, res = False, f"Not Found at {self.path}"
        elif method == "slow":
            time.sleep(14)
        elif method == "getMe":
            res = {"username": "fakebot"}
        elif method == "getUpdates":
            off = p.get("offset", 0)
            with S.lock:
                res = [u for u in S.updates if u["update_id"] >= off]
                # Telegram confirms (forgets) updates below the offset.
                S.updates[:] = res
        elif method in ("sendMessage", "sendDocument"):
            if method == "sendMessage" and p.get("parse_mode") == "HTML" and S.refuse_html:
                ok, res = False, "can't parse entities"
            else:
                S.mid += 1
                res = {"message_id": S.mid}
        body = json.dumps({"ok": True, "result": res} if ok else {"ok": False, "description": res}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["WF_TELEGRAM_API"] = f"http://127.0.0.1:{srv.server_address[1]}"
sys.path.insert(0, RUNNER)
import ntfy, telegram, report, run  # noqa: E402

ntfy.RETRY_GAP = 0.1
RESULTS = []


def step(name, ok, evidence):
    ok = bool(ok)
    RESULTS.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}: {evidence}")


def reqs(method=None):
    with S.lock:
        return [r for r in S.reqs if method is None or r[0] == method]


def clear():
    with S.lock:
        S.reqs.clear()
        S.updates.clear()


def write_cfg(cfg, mode=0o600, raw=None):
    p = telegram.path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(raw if raw is not None else json.dumps(cfg))
    os.chmod(p, mode)


CHAT = 4242
CFG = {"token": TOKEN, "chat_id": CHAT, "aliases": {}, "block": []}

# AC-1 load refusals, never the token
whys = []
for label, mode, raw in [("mode 0644", 0o644, json.dumps(CFG)), ("not json", 0o600, "[1]"),
                         ("bad token", 0o600, json.dumps({**CFG, "token": TOKEN + "!"})),
                         ("chat_id str", 0o600, json.dumps({**CFG, "chat_id": "4242"}))]:
    write_cfg(None, mode, raw)
    try:
        telegram.load()
        whys.append((label, "LOADED"))
    except telegram.Invalid as e:
        whys.append((label, str(e)))
write_cfg(CFG)
good = telegram.load()
step("AC-1 load refuses bad files", all(w != "LOADED" for _, w in whys) and all(TOKEN not in w for _, w in whys)
     and good["chat_id"] == CHAT, whys)

# AC-1 redact: an API error echoing the URL path never shows the token
try:
    telegram.api(TOKEN, "failme")
    e1 = "NO ERROR"
except telegram.ApiError as e:
    e1 = str(e)
t = telegram.Topic(CFG, "r", "f")
real_api = telegram.api
telegram.api = lambda tok, method, *a, **k: real_api(tok, "failme")
try:
    t.publish("x", 3)
    e2 = "NO ERROR"
except telegram.PingFailed as e:
    e2 = str(e)
telegram.api = real_api
step("AC-1 errors redact the token", TOKEN not in e1 + e2 and "<token>" in e1 and "<token>" in e2
     and len(reqs("failme")) == 4, f"api: {e1!r}; ping after 3 tries: {e2!r}")
clear()

# AC-1 write: 0600 in 0700 folder via ntfy.write
wp = os.path.join(WORK, "wtest", "telegram.json")
ntfy.write(CFG, wp)
step("AC-1 file written 0600 in 0700 folder", oct(os.stat(wp).st_mode & 0o777) == "0o600"
     and oct(os.stat(os.path.dirname(wp)).st_mode & 0o777) == "0o700",
     f"{oct(os.stat(wp).st_mode & 0o777)} in {oct(os.stat(os.path.dirname(wp)).st_mode & 0o777)}")

# AC-2 channel choice (in process) and wf run refusals (real CLI)
mod, cfg = telegram.channel()
step("AC-2 valid telegram.json picks Telegram", mod is telegram and cfg["chat_id"] == CHAT, mod.__name__)
scratch = os.path.join(WORK, "repo")
os.makedirs(os.path.join(scratch, "docs", "scope"))
open(os.path.join(scratch, "docs", "scope", "scope.md"), "w").write("# Scope\n\n### 1. x · auto\n- [ ] Build: `/develop x`\n")
subprocess.run(["git", "init", "-q", scratch], check=True)
env = dict(os.environ)
os.chmod(telegram.path(), 0o644)
r = subprocess.run([sys.executable, os.path.join(RUNNER, "wf.py"), "run", scratch], capture_output=True, text=True,
                   env=env, timeout=60)
out = (r.stdout + r.stderr).strip()
step("AC-2 invalid telegram.json refuses no_telegram, no fallback", r.returncode == 5 and "refused: no_telegram:" in out
     and "readable or writable by others" in out and TOKEN not in out, f"exit {r.returncode}: {out[-300:]!r}")
os.unlink(telegram.path())
r = subprocess.run([sys.executable, os.path.join(RUNNER, "wf.py"), "run", scratch], capture_output=True, text=True,
                   env=env, timeout=60)
out = (r.stdout + r.stderr).strip()
step("AC-2 no file at all refuses no_ntfy naming both", r.returncode == 5 and
     "refused: no_ntfy: no telegram.json or ntfy.json, run wf telegram init" in out, f"exit {r.returncode}: {out[-300:]!r}")
write_cfg(CFG)

# AC-3 calls cannot read telegram.json
deny = [x for p in run.CREDENTIAL_PATHS for x in run.expand(p)]
rules = [r_ for x in deny for r_ in run.path_rules("Read", x)]
tp = telegram.path()
covered = [d for d in deny if tp == d or tp.startswith(d.rstrip("/") + "/")]
step("AC-3 sandbox denyRead and Read rules cover telegram.json", bool(covered)
     and any(os.path.dirname(tp) in r_ for r_ in rules), f"{tp} under {covered}; rules e.g. "
     f"{[r_ for r_ in rules if os.path.dirname(tp) in r_][:2]}")

# AC-4 question message
now = __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")
d = {"id": "abcd", "kind": "panel", "question": "Pick a colour for the header", "options": ["red", "green", "blue", "gold"],
     "multi": False, "answer": None, "ignored": 0, "asked": now, "repo": scratch, "feature": "x"}
mid = telegram.Topic(CFG, "repo", "feat").ping(d, lambda: False)
sm = reqs("sendMessage")
p = sm[-1][1] if sm else {}
rows = (p.get("reply_markup") or {}).get("inline_keyboard", [])
step("AC-4 panel: one message, every option a button, id returned", isinstance(mid, str) and len(sm) == 1
     and [r_[0]["callback_data"] for r_ in rows] == ["abcd 1", "abcd 2", "abcd 3", "abcd 4"]
     and d["sent"].endswith("tap a button, or reply to this message") and "4 gold" in d["sent"]
     and telegram.ASKED.match(d["sent"]),
     f"id {mid!r}, buttons {[r_[0]['text'] for r_ in rows]}, parse_mode {p.get('parse_mode')}, sent {d['sent']!r}")
clear()
S.refuse_html = True
d2 = dict(d, id="efgh", kind="prose", options=[], answer=None)
mid2 = telegram.Topic(CFG, "repo", "feat").ping(d2, lambda: False)
sm = reqs("sendMessage")
step("AC-4 prose, styled refused: plain resend, no buttons", mid2 and len(sm) == 2 and "parse_mode" not in sm[1][1]
     and "reply_markup" not in sm[1][1] and sm[1][1]["text"].startswith(d2["sent"])
     and d2["sent"].endswith("reply to this message with your answer"), f"second text {sm[1][1]['text']!r}")
S.refuse_html = False
clear()

# AC-5 other messages
t = telegram.Topic(CFG, "repo", "feat")
t.publish("abcd accepted, resuming", 2)
t.publish("body", 4, title="Head")
sm = reqs("sendMessage")
step("AC-5 ack silent, title first line", sm[0][1].get("disable_notification") is True
     and "disable_notification" not in sm[1][1] and sm[1][1]["text"] == "Head\nbody"
     and sm[0][1]["text"].startswith("wf repo: feat\n"), [(x[1]["text"], x[1].get("disable_notification")) for x in sm])
clear()

# AC-6 fetch
bot = {"id": 1, "is_bot": True}
me = {"id": CHAT, "is_bot": False}
S.updates[:] = [
    {"update_id": 10, "callback_query": {"id": "cq1", "from": me, "data": "abcd 1",
                                         "message": {"chat": {"id": CHAT}, "date": 2000000000}}},
    {"update_id": 11, "message": {"chat": {"id": 999}, "from": {"id": 999}, "text": "abcd 2", "date": 2000000000}},
    {"update_id": 12, "message": {"chat": {"id": CHAT}, "from": me, "text": "use the blue one", "date": 2000000001,
                                  "reply_to_message": {"from": bot, "text": d["sent"]}}},
    {"update_id": 13, "message": {"chat": {"id": CHAT}, "from": me, "text": "hello", "date": 2000000002}},
    {"update_id": 14, "message": {"chat": {"id": CHAT}, "from": me, "text": "abcd 3", "date": 2000000003}},
    {"update_id": 15, "callback_query": {"id": "cq2", "from": {"id": 999}, "data": "abcd 4",
                                         "message": {"chat": {"id": CHAT}, "date": 2000000000}}},
]
telegram.fetch(CFG)
log = telegram.read_log()
msgs = [(l["id"], l["event"], l.get("message")) for l in log]
gu = reqs("getUpdates")[0][1]
acq = [x[1]["callback_query_id"] for x in reqs("answerCallbackQuery")]
hints = [x[1]["text"] for x in reqs("sendMessage")]
step("AC-6 fetch keeps only your chat, maps replies and taps", msgs == [
    ("u10", "message", "abcd 1"), ("u11", "skip", None), ("u12", "message", "abcd use the blue one"),
    ("u13", "message", "hello"), ("u14", "message", "abcd 3"), ("u15", "skip", None)]
     and gu.get("timeout") == 0 and gu.get("allowed_updates") == ["message", "callback_query"], msgs)
step("AC-6 every tap answered, one hint for the stray message", acq == ["cq1", "cq2"] and hints == [telegram.HINT],
     f"answerCallbackQuery {acq}, hints {hints}")
lm = oct(os.stat(telegram.log_path()).st_mode & 0o777)
clear()
telegram.fetch(CFG)
step("AC-6 next fetch starts past the log, log 0600", reqs("getUpdates")[0][1].get("offset") == 16 and lm == "0o600",
     f"offset {reqs('getUpdates')[0][1].get('offset')}, log mode {lm}")
clear()
fd = os.open(os.path.join(telegram.state_dir(), "telegram.lock"), os.O_RDWR)
fcntl.flock(fd, fcntl.LOCK_EX)
t0 = time.time()
telegram.fetch(CFG)
held = time.time() - t0
os.close(fd)
step("AC-6 a held lock returns at once, no getUpdates", not reqs("getUpdates") and held < 1, f"{held:.3f}s")
old = telegram.read_log()
old.insert(0, {"id": "u5", "time": int(time.time()) - 49 * 3600, "event": "skip"})
telegram.write_log(old)
S.updates[:] = [{"update_id": 16, "message": {"chat": {"id": CHAT}, "from": me, "text": "abcd 2", "date": int(time.time())}}]
telegram.fetch(CFG)
ids = [l["id"] for l in telegram.read_log()]
step("AC-6 lines older than 48 hours dropped", "u5" not in ids and "u16" in ids, ids)
clear()

# AC-7 poll cursor
t = telegram.Topic(CFG, "", "")
after = [l["id"] for l in t.poll("u12")]
every = [l["id"] for l in t.poll("bogus")]
step("AC-7 poll returns lines after the cursor", after == ["u13", "u14", "u15", "u16"] and every[0] == "u10" and
     len(every) == 7, f"after u12 {after}; no cursor {len(every)} lines")

# AC-8 take
base = int(time.time())
mk = lambda **k: {"id": "abcd", "kind": "panel", "options": ["red", "green"], "multi": True, "answer": None,
                  "ignored": 0, "asked": __import__("datetime").datetime.fromtimestamp(base).astimezone().isoformat(), **k}
cases = []
for text, dd, when in [("abcd 1", mk(), base - 60), ("abcd 2", mk(), base + 1), ("abcd 1,2", mk(), base + 1),
                       ("abcd GREEN", mk(), base + 1), ("abcd use blue", mk(), base + 1),
                       ("abcd hello there", mk(kind="prose", options=[]), base + 1), ("zzzz 1", mk(), base + 1)]:
    got = t.take(text, [dd], {"time": when})
    cases.append((text, got and got["answer"], got and got["source"]))
step("AC-8 take: old reply ignored, numbers, labels, free text", cases == [
    ("abcd 1", None, None), ("abcd 2", "green", "phone"), ("abcd 1,2", "red, green", "phone"),
    ("abcd GREEN", "green", "phone"), ("abcd use blue", "use blue", "phone"),
    ("abcd hello there", "hello there", "phone"), ("zzzz 1", None, None)], cases)
clear()

# AC-9 morning report through report.send
line = "built: feature number {} finished and merged into the branch, ready for review " + "x" * 40
for n_lines, want in [(10, "one"), (60, "split"), (200, "file")]:
    clear()
    body = "wf report: head line\n" + "\n".join(line.format(i) for i in range(n_lines)) + "\nnext: review"
    res = report.send(CFG, body)
    sm, sd = reqs("sendMessage"), reqs("sendDocument")
    texts = [x[1]["text"] for x in sm]
    if want == "one":
        ok = res == "sent" and len(sm) == 1 and texts[0] == body and not sd
    elif want == "split":
        ok = res == "sent" and 1 < len(sm) <= 3 and all(len(x) <= 4096 for x in texts) and "\n".join(texts) == body and not sd
    else:
        raw = sd[0][1]["_raw"] if sd else ""
        ok = res == "sent" and len(sm) == 1 and texts[0] == "wf report: head line\nnext: review\nfull report attached" \
            and 'filename="wf-report.txt"' in raw and body in raw
    step(f"AC-9 report {len(body)} chars -> {want}", ok,
         f"{res}, {len(sm)} messages {[len(x) for x in texts]}, {len(sd)} documents")
clear()

# AC-10 wf telegram init and test (real CLI)
os.unlink(telegram.path())
wfpy = os.path.join(RUNNER, "wf.py")
r = subprocess.run([sys.executable, wfpy, "telegram", "init"], input="not-a-token\n", capture_output=True, text=True,
                   env=dict(os.environ), timeout=30)
step("AC-10 malformed token refused", r.returncode == 2 and "refused" in r.stdout and not os.path.exists(telegram.path()),
     f"exit {r.returncode}: {r.stdout.strip()!r}")
pr = subprocess.Popen([sys.executable, wfpy, "telegram", "init"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE, text=True, env=dict(os.environ))
pr.stdin.write(TOKEN + "\n")
pr.stdin.flush()
out_lines, code = [], None
for l in pr.stdout:
    out_lines.append(l.rstrip())
    m = re.match(r"or send /start (\S+) to @fakebot", l)
    if m:
        code = m.group(1)
        with S.lock:
            S.updates[:] = [{"update_id": 50, "message": {"chat": {"id": 777, "type": "private"}, "text": "/start wrong1"}},
                            {"update_id": 51, "message": {"chat": {"id": 555, "type": "group"}, "text": f"/start {code}"}},
                            {"update_id": 52, "message": {"chat": {"id": CHAT, "type": "private"}, "text": f"/start {code}"}}]
        break
rest, err = pr.communicate(timeout=120)
out_lines += rest.splitlines()
saved = json.load(open(telegram.path())) if os.path.exists(telegram.path()) else {}
conn = [x[1] for x in reqs("sendMessage")]
allout = "\n".join(out_lines) + err
step("AC-10 init binds the /start chat, saves 0600, never prints the token", pr.returncode == 0 and code
     and re.fullmatch(f"[{ntfy.CODE_CHARS}]{{6}}", code) and saved.get("chat_id") == CHAT and saved.get("token") == TOKEN
     and oct(os.stat(telegram.path()).st_mode & 0o777) == "0o600" and conn == [{"chat_id": CHAT, "text": "wf connected"}]
     and [x[0] for x in reqs() if x[0] in ("getMe", "deleteWebhook")] == ["getMe", "deleteWebhook"]
     and TOKEN not in allout and "bot: @fakebot" in allout and f"open https://t.me/fakebot?start={code}" in allout,
     f"exit {pr.returncode}, stdout {out_lines}, chat {saved.get('chat_id')}")
r = subprocess.run([sys.executable, wfpy, "telegram", "init"], input=TOKEN + "\n", capture_output=True, text=True,
                   env=dict(os.environ), timeout=30)
step("AC-10 existing file refused without --rotate", r.returncode == 2 and "--rotate" in r.stdout,
     f"exit {r.returncode}: {r.stdout.strip()!r}")
clear()
pr = subprocess.Popen([sys.executable, wfpy, "telegram", "test"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      text=True, env=dict(os.environ))
out_lines = []
for l in pr.stdout:
    out_lines.append(l.rstrip())
    m = re.match(r"sent (\w{4}),", l)
    if m:
        with S.lock:
            S.updates[:] = [{"update_id": 60, "callback_query": {"id": "cq9", "from": me, "data": f"{m.group(1)} 1",
                                                                 "message": {"chat": {"id": CHAT}, "date": int(time.time()) + 5}}}]
        break
rest, err = pr.communicate(timeout=120)
out_lines += rest.splitlines()
step("AC-10 wf telegram test takes a tap", pr.returncode == 0 and "accepted: yes" in out_lines,
     f"exit {pr.returncode}, stdout {out_lines}")

# AC-11 stdlib only, 10 s timeout
src = open(os.path.join(RUNNER, "telegram.py")).read()
mods = {m.split(".")[0] for m in re.findall(r"^(?:import|from) (\S+)", src, re.M)}
nonstd = sorted(m for m in mods if m not in sys.stdlib_module_names)
t0 = time.time()
try:
    telegram.api(TOKEN, "slow")
    e3 = "NO ERROR"
except telegram.ApiError as e:
    e3 = str(e)
took = time.time() - t0
step("AC-11 stdlib only, a hung call ends after 10 s", set(nonstd) <= {"context", "ntfy", "wf"} and 9 < took < 12
     and TOKEN not in e3, f"non stdlib imports {nonstd}; hung call {took:.1f}s: {e3!r}")

srv.shutdown()
print(f"\n{sum(RESULTS)}/{len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
