# Phone pings through ntfy (spec 0005): config, scrubbed pings, polling, reply
# rules and one time codes. Stdlib only. Tests patch the constants here.
import datetime
import fcntl
import hashlib
import json
import os
import re
import secrets
import tempfile
import time
import urllib.parse
import urllib.request

import wf

CODE_CHARS = "abcdefghjkmnpqrstuvwxyz23456789"
ID_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"
TOPIC = re.compile(r"^[A-Za-z0-9_-]{32,64}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REPLY = re.compile(r"^\s*([a-z0-9]{4})\s+(.+?)\s*$", re.S | re.I)
CODE_REPLY = re.compile(r"^(\S{8})\s+(\S.*)$", re.S)
SECRET = re.compile(r"/|\\|~|@|://")
RETRY_GAP = 10
POLL_EVERY = 15
SLICE = 0.2
TIMEOUT = 10


class Invalid(Exception):
    pass


class PingFailed(Exception):
    pass


def path():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "wf", "ntfy.json")


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def boottime():
    return time.clock_gettime(time.CLOCK_BOOTTIME)


def load(need_codes=True):
    """AC-2. The config dict, or Invalid(why). `wf ntfy codes` loads with no codes left."""
    p = path()
    try:
        mode = os.stat(p).st_mode
        with open(p, encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        raise Invalid(f"{p} is missing, run wf ntfy init")
    except OSError as e:
        raise Invalid(f"{p}: {e.strerror or e}")
    if mode & 0o077:
        raise Invalid(f"{p} is readable or writable by others, chmod 600 it")
    try:
        cfg = json.loads(raw)
    except ValueError:
        cfg = None
    if not isinstance(cfg, dict):
        raise Invalid(f"{p} is not a JSON object")
    server, codes = cfg.get("server"), cfg.get("codes")
    if not isinstance(cfg.get("topic"), str) or not TOPIC.match(cfg["topic"]):
        raise Invalid("topic must be 32 to 64 characters of A-Z a-z 0-9 _ -")
    # Parsed, not a prefix: http://localhost.example.com used to pass as local plain http.
    try:
        url = urllib.parse.urlsplit(server) if isinstance(server, str) else None
    except ValueError:
        # "https://[x" raised past every caller, a traceback instead of no_ntfy (review M6).
        url = None
    if not url or not url.hostname or not (url.scheme == "https" or
                                          (url.scheme == "http" and url.hostname in ("127.0.0.1", "localhost"))):
        raise Invalid("server must start with https://")
    if not isinstance(codes, list) or not all(isinstance(c, str) and HEX64.match(c) for c in codes) \
            or (need_codes and not codes):
        raise Invalid("codes must be a non empty list of sha256 hex strings, run wf ntfy codes")
    aliases, block = cfg.get("aliases"), cfg.get("block")
    if not isinstance(aliases, dict) or not all(isinstance(v, str) for v in aliases.values()):
        raise Invalid("aliases must be an object of strings")
    if not isinstance(block, list) or not all(isinstance(b, str) for b in block):
        raise Invalid("block must be a list of strings")
    cfg["server"] = server.rstrip("/")
    return cfg


def write(cfg, p=None):
    """Atomic, 0600 in a 0700 folder. Spec 0008's allowed.json goes through here too."""
    p = p or path()
    os.makedirs(os.path.dirname(p), mode=0o700, exist_ok=True)
    os.chmod(os.path.dirname(p), 0o700)
    # A fixed .tmp name let two writers truncate each other's file (review L5); mkstemp makes it 0600.
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), prefix=os.path.basename(p) + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def new_codes():
    plain = ["".join(secrets.choice(CODE_CHARS) for _ in range(8)) for _ in range(20)]
    return plain, [sha(c) for c in plain]


def burn(cfg, hashes):
    """Remove these code hashes from the file under a lock. Returns the ones that were still
    there: the file decides, since another run may have used a code after this one loaded it."""
    p = path()
    while True:
        fd = os.open(p, os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        # A run that rewrote the file while we waited left us holding the old inode.
        if os.fstat(fd).st_ino == os.stat(p).st_ino:
            break
        os.close(fd)
    try:
        with open(p, encoding="utf-8") as f:
            disk = json.load(f)
        live = set(disk.get("codes", [])) & hashes
        if live:
            disk["codes"] = [c for c in disk["codes"] if c not in hashes]
            write(disk)
    finally:
        os.close(fd)
    cfg["codes"] = disk.get("codes", [])
    return live


def scrub(text, limit):
    """AC-7: first line, no control characters, no backticked spans or path like tokens, cut to limit."""
    text = wf.clean(str(text or "").split("\n")[0])
    text = re.sub(r"`[^`]*`", " ", text)
    text = " ".join(t for t in text.split() if not SECRET.search(t))
    return cut(text, limit)


def cut(text, limit):
    """AC-7: at most limit characters, ending at a word boundary with `...` when cut.
    A hard cut mid word used to read on the phone as redacted text."""
    if len(text) <= limit:
        return text
    head = text[:limit - 3]
    if " " in head:
        head = head[:head.rindex(" ")]
    return head.rstrip() + "..."


def blocked(cfg, text):
    low = text.casefold()
    return any(b.strip() and b.strip().casefold() in low for b in cfg["block"])


def scrub_field(cfg, text, limit, fallback):
    """Spec 0018 AC-4: scrub cut to limit, else fallback when empty or holding a block list entry."""
    s = scrub(text, limit)
    return fallback if not s or blocked(cfg, s) else s


def private_names():
    """Spec 0021 AC-8: the names in the private names list scripts/private-names.py checks (private/names.txt in
    $CLAUDE_LIVE_DIR, $CLAUDE_CONFIG_DIR and ~/.claude; literal, lower cased, `==>` replacements cut). None when
    no list can be read or it holds no name: every repo name then stays hidden, as the checker fails closed."""
    home = os.path.join(os.path.expanduser("~"), ".claude")
    names = []
    for d in dict.fromkeys(filter(None, (os.environ.get("CLAUDE_LIVE_DIR"), os.environ.get("CLAUDE_CONFIG_DIR"), home))):
        try:
            with open(os.path.join(d, "private", "names.txt"), encoding="utf-8") as f:
                lines = f.read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        names += [l.strip().partition("==>")[0].strip().lower() for l in lines if l.strip() and not l.strip().startswith("#")]
    names = [n for n in names if n]
    return names or None


def repo_label(cfg, repo):
    """An alias, else (spec 0021 AC-8) the folder name unless the private names list or the block list holds it,
    else repo-<hash>."""
    real = os.path.realpath(repo)
    if cfg["aliases"].get(real):
        return cfg["aliases"][real]
    name, names = os.path.basename(real), private_names()
    if name and names is not None and not any(n in name.lower() for n in names) and not blocked(cfg, name):
        return name
    return "repo-" + hashlib.sha1(real.encode()).hexdigest()[:4]


def new_id(taken):
    while True:
        i = "".join(secrets.choice(ID_CHARS) for _ in range(4))
        if i not in taken:
            return i


def nap(seconds, stopped):
    """Sleep in SLICE steps. True when stopped() turned true."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if stopped():
            return True
        time.sleep(min(SLICE, max(0, end - time.monotonic())))
    return stopped()


class Topic:
    def __init__(self, cfg, label, feature):
        self.cfg = cfg
        feature = scrub(feature, 40)
        self.title = f"wf {label}: {'feature' if blocked(cfg, feature) else feature}"
        self.own = set()

    def post(self, body):
        req = urllib.request.Request(self.cfg["server"] + "/", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read())["id"]

    def publish(self, message, priority, actions=None, stopped=lambda: False, title=None, tags=("question",)):
        """AC-7: three tries RETRY_GAP apart. The message id, None when stopped, else PingFailed.
        Spec 0018 AC-4: the morning report passes its own title and tags."""
        body = {"topic": self.cfg["topic"], "title": self.title if title is None else title, "priority": priority,
                "tags": list(tags), "message": message}
        if actions:
            body["actions"] = actions
        for attempt in range(3):
            try:
                mid = self.post(body)
                self.own.add(mid)
                return mid
            except Exception as e:
                error = e
            if attempt < 2 and nap(RETRY_GAP, stopped):
                return None
        raise PingFailed(wf.clean(str(error)))

    def ping(self, d, stopped):
        """Send one decision's ping, record the scrubbed body in d["sent"]. The message id or None."""
        question = scrub(d["question"], 140)
        if blocked(self.cfg, question):
            question = "question waiting, see terminal"
        lines, actions = [f"{d['id']}: {question}"], []
        # Spec 0028 AC-11: the short explanation right under the question, scrubbed like a report field.
        learn = scrub_field(self.cfg, " ".join(str(d.get("learn") or "").split()), 300, "")
        if learn:
            lines.append(f"learn: {learn}")
        for n, label in enumerate(d["options"], 1):
            label = scrub(label, 100)
            # A label that was all paths or code used to send a blank button.
            if not label or blocked(self.cfg, label):
                label = f"option {n}"
            lines.append(f"{n} {label}")
            if n <= 3:
                actions.append({"action": "http", "label": f"{n} {cut(label, 40)}", "url": f"{self.cfg['server']}/{self.cfg['topic']}",
                                "method": "POST", "body": f"{d['id']} {n}", "clear": True})
        lines.append(f"reply {d['id']} <n>" if d["kind"] == "panel" else f"reply {d['id']} <code> <text>")
        d["sent"] = "\n".join(lines)
        return self.publish(d["sent"], 4, actions, stopped)

    def poll(self, cursor):
        url = f"{self.cfg['server']}/{self.cfg['topic']}/json?poll=1&since={cursor}"
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return [json.loads(l) for l in r.read().decode().splitlines() if l.strip()]

    def take(self, text, ds):
        """AC-8 for one message. The decision it answered, or None."""
        tokens = {sha(t) for t in text.split() if len(t) == 8}
        valid = burn(self.cfg, tokens) if tokens else set()
        m = REPLY.match(text)
        d = m and next((d for d in ds if d["id"] == m.group(1).lower() and d["answer"] is None), None)
        if not d:
            return None
        # A prose decision has no options, so only the code form can answer it.
        rest, labels, answer = m.group(2), d["options"], None
        if re.fullmatch(r"\d+(,\d+)*", rest):
            picks = [int(x) for x in rest.split(",")]
            if (len(picks) == 1 or d["multi"]) and len(set(picks)) == len(picks) \
                    and all(1 <= p <= len(labels) for p in picks):
                answer = ", ".join(labels[p - 1] for p in picks)
        else:
            answer = next((l for l in labels if l.strip().casefold() == rest.strip().casefold()), None)
        if answer is None:
            c = CODE_REPLY.match(rest)
            if c and sha(c.group(1)) in valid:
                answer = c.group(2)
        if answer is None:
            d["ignored"] += 1
            return None
        d.update(answer=answer, source="phone", answered=datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
        return d

    def wait(self, ds, cursor, max_wait_s, stopped, on_answer, warn):
        """AC-8, AC-9: poll until every decision in ds is answered.
        Returns "answered", "timeout" or "interrupted"."""
        start, failed, next_poll = boottime(), False, 0
        while True:
            if stopped():
                return "interrupted"
            t = boottime()
            if t - start >= max_wait_s:
                return "timeout"
            if t >= next_poll:
                next_poll = t + POLL_EVERY
                try:
                    msgs = self.poll(cursor)
                except Exception as e:
                    msgs = []
                    if not failed:
                        warn(f"ntfy poll failed: {wf.clean(str(e))}")
                        failed = True
                for msg in msgs:
                    cursor = msg.get("id", cursor)
                    if msg.get("event") != "message" or msg.get("id") in self.own:
                        continue
                    d = self.take(str(msg.get("message") or ""), ds)
                    if d:
                        on_answer(d)
                        try:
                            self.publish(f"{d['id']} accepted, resuming", 2, stopped=stopped)
                        except PingFailed:
                            pass
                if all(d["answer"] is not None for d in ds):
                    return "answered"
            time.sleep(SLICE)


# -- wf ntfy init | codes | test ---------------------------------------------

def show_codes(plain):
    print("one time codes, shown once (type `<id> <code> <text>` to answer in free text):")
    for c in plain:
        print(c)


def cmd_init(rotate):
    keep = {"server": "https://ntfy.sh", "aliases": {}, "block": []}
    if os.path.exists(path()):
        if not rotate:
            print(f"{path()} exists, use wf ntfy init --rotate to replace the topic and codes")
            return 2
        try:
            old = load(need_codes=False)
        except Invalid as e:
            print(f"refused: no_ntfy: {wf.clean(str(e))}")
            return 5
        keep = {k: old[k] for k in keep}
    plain, hashes = new_codes()
    cfg = {"server": keep["server"], "topic": secrets.token_urlsafe(24), "codes": hashes,
           "aliases": keep["aliases"], "block": keep["block"]}
    write(cfg)
    print(f"subscribe: {cfg['server']}/{cfg['topic']}")
    # The Android app has no way to type into a topic (spec 0005 verify.md check 5); its web page does.
    print("type replies: open that URL in your phone's browser and use the message box")
    show_codes(plain)
    return 0


def cmd_codes():
    try:
        cfg = load(need_codes=False)
    except Invalid as e:
        print(f"refused: no_ntfy: {wf.clean(str(e))}")
        return 5
    plain, cfg["codes"] = new_codes()
    write(cfg)
    show_codes(plain)
    return 0


def cmd_test():
    try:
        cfg = load()
    except Invalid as e:
        print(f"refused: no_ntfy: {wf.clean(str(e))}")
        return 5
    t = Topic(cfg, "test", "ntfy test")
    d = {"id": new_id(set()), "kind": "panel", "question": "Did this ping reach your phone?",
         "options": ["yes", "no"], "multi": False, "answer": None, "ignored": 0}
    try:
        first = t.ping(d, lambda: False)
        print(f"sent {d['id']}, waiting up to 5 minutes for a tap or a reply", flush=True)
        end = t.wait([d], first, 300, lambda: False, lambda d: None,
                     lambda w: print(f"warning: {w}", flush=True))
    except PingFailed as e:
        print(f"stopped: ping_failed: {e}")
        return 6
    except KeyboardInterrupt:
        print()
        return 130
    if end == "answered":
        print(f"accepted: {d['answer']}")
        return 0
    print("no reply")
    return 6
