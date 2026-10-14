# Phone channel through your own Telegram bot (spec 0029). Same names as ntfy.py, so run.py holds either module
# as self.phone. Scrubbing, ids and naps stay ntfy's. Stdlib only. Tests patch API to a local fake Bot API.
import datetime
import fcntl
import getpass
import html
import json
import os
import re
import secrets
import sys
import tempfile
import time
import urllib.request

import context
import ntfy
import wf

API = "https://api.telegram.org"
TOKEN = re.compile(r"^\d{5,16}:[A-Za-z0-9_-]{30,64}$")
# Spec 0033 AC-5: the labeled first line, or the older `<id>:` one.
# Spec 0033 AC-5: the labeled first line, or the older `<id>:` one.
ASKED = re.compile(r"^(?:Question ([a-z0-9]{4}) \(|([a-z0-9]{4}):)")
TIMEOUT = 10
MAX = 4096
KEEP = 48 * 3600
LONG_POLL = 25
INIT_WAIT = 300
HINT = "reply to a question message (swipe it), or start with its 4 letter id"
# The run catches ntfy's exceptions; one class each keeps run.py's except lines as they are.
Invalid = ntfy.Invalid
PingFailed = ntfy.PingFailed


class ApiError(Exception):
    pass


def path():
    return os.path.join(os.path.dirname(ntfy.path()), "telegram.json")


def state_dir():
    # run.state_dir(); not imported, since run imports this module.
    return os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"), "wf")


class Refused(Exception):
    """(reason, why) for wf run's refusal line."""


def channel():
    """AC-2: (module, config) of the phone channel. telegram.json wins, and an invalid one refuses no_telegram:
    falling back would send your questions to a topic you may no longer watch."""
    if os.path.lexists(path()):
        try:
            return sys.modules[__name__], load()
        except Invalid as e:
            raise Refused("no_telegram", e)
    try:
        return ntfy, ntfy.load()
    except Invalid as e:
        raise Refused("no_ntfy", e if os.path.lexists(ntfy.path()) else
                      "no telegram.json or ntfy.json, run wf telegram init")


def redact(text, token):
    """AC-1: the token sits in every request URL, so any error text could echo it."""
    text = str(text)
    return text.replace(token, "<token>") if isinstance(token, str) and token else text


def load():
    """AC-1. The config dict, or Invalid(why). No why ever holds the token."""
    p = path()
    try:
        mode = os.stat(p).st_mode
        with open(p, encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        raise Invalid(f"{p} is missing, run wf telegram init")
    except OSError as e:
        raise Invalid(f"{p}: {e.strerror or type(e).__name__}")
    if mode & 0o077:
        raise Invalid(f"{p} is readable or writable by others, chmod 600 it")
    try:
        cfg = json.loads(raw)
    except ValueError:
        cfg = None
    if not isinstance(cfg, dict):
        raise Invalid(f"{p} is not a JSON object")
    if not isinstance(cfg.get("token"), str) or not TOKEN.match(cfg["token"]):
        raise Invalid("token must be the bot token BotFather gave you, run wf telegram init --rotate")
    if type(cfg.get("chat_id")) is not int:
        raise Invalid("chat_id must be an integer, run wf telegram init --rotate")
    aliases, block = cfg.get("aliases"), cfg.get("block")
    if not isinstance(aliases, dict) or not all(isinstance(v, str) for v in aliases.values()):
        raise Invalid("aliases must be an object of strings")
    if not isinstance(block, list) or not all(isinstance(b, str) for b in block):
        raise Invalid("block must be a list of strings")
    return cfg


def multipart(params, name, text):
    """AC-9: a sendDocument body by hand (no requests module): the fields, then one text file."""
    b = "wf" + secrets.token_hex(12)
    parts = [f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in params.items()]
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="document"; filename="{name}"\r\n'
                 f'Content-Type: text/plain; charset=utf-8\r\n\r\n'.encode() + text.encode() + b"\r\n")
    return b"".join(parts) + f"--{b}--\r\n".encode(), f"multipart/form-data; boundary={b}"


def api(token, method, params=None, wait=0, document=None):
    """AC-11: one Bot API call, 10 s beyond the long poll wait. The result, else ApiError with the token redacted."""
    if document:
        data, kind = multipart(params or {}, *document)
    else:
        data, kind = json.dumps(params or {}).encode(), "application/json"
    req = urllib.request.Request(f"{API}/bot{token}/{method}", data=data, headers={"Content-Type": kind}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT + wait) as r:
            body = json.loads(r.read())
    except Exception as e:
        # from None: a chained urllib error would carry the URL into a traceback.
        raise ApiError(redact(wf.clean(f"{method}: {e}"), token)) from None
    if not isinstance(body, dict) or not body.get("ok"):
        raise ApiError(redact(wf.clean(f"{method}: {body.get('description') if isinstance(body, dict) else body}"), token))
    return body["result"]


def retry(cfg, send, stopped):
    """Spec 0005 AC-7: three tries RETRY_GAP apart. The message id, None when stopped, else PingFailed."""
    for attempt in range(3):
        try:
            return send()
        except Exception as e:
            error = e
        if attempt < 2 and ntfy.nap(ntfy.RETRY_GAP, stopped):
            return None
    raise PingFailed(redact(wf.clean(str(error)), cfg["token"]))


# -- the update log (AC-6) ------------------------------------------------------

def log_path():
    return os.path.join(state_dir(), "telegram-updates.jsonl")


def read_log():
    try:
        with open(log_path(), encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
    except (OSError, ValueError):
        return []
    return sorted((l for l in lines if isinstance(l, dict) and re.fullmatch(r"u\d+", str(l.get("id")))),
                  key=lambda l: int(l["id"][1:]))


def write_log(lines):
    fd, tmp = tempfile.mkstemp(dir=state_dir(), prefix="telegram-updates.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("".join(json.dumps(l) + "\n" for l in lines))
        os.replace(tmp, log_path())
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def entry(cfg, u):
    """One update as a log line, plus the callback id to answer and whether it earns the hint."""
    line, cq, hint = {"id": f"u{u['update_id']}", "time": int(time.time()), "event": "skip"}, None, False
    mine = lambda chat, sender: chat == cfg["chat_id"] and sender == cfg["chat_id"]
    if isinstance(u.get("callback_query"), dict):
        c = u["callback_query"]
        msg = c.get("message") or {}
        cq = c.get("id")
        if mine((msg.get("chat") or {}).get("id"), (c.get("from") or {}).get("id")):
            # The question message's date: a tap on an older question's button never answers a reused id (AC-8).
            line.update(event="message", message=str(c.get("data") or ""), time=msg.get("date") or line["time"])
    elif isinstance(u.get("message"), dict):
        m = u["message"]
        if mine((m.get("chat") or {}).get("id"), (m.get("from") or {}).get("id")):
            text, to = str(m.get("text") or ""), m.get("reply_to_message") or {}
            asked = ASKED.match(str(to.get("text") or "")) if (to.get("from") or {}).get("is_bot") else None
            if asked:
                text = f"{asked.group(1) or asked.group(2)} {text}"
            else:
                hint = not ntfy.REPLY.match(text)
            line.update(event="message", message=text, time=m.get("date") or line["time"])
    return line, cq, hint


def quiet(cfg, method, params):
    try:
        api(cfg["token"], method, params)
    except ApiError:
        pass


def fetch(cfg):
    """AC-6: one reader at a time under a lock; every accepted update becomes a log line. Another process holding
    the lock returns at once. getUpdates errors raise ApiError; a failed hint or callback answer is dropped."""
    os.makedirs(state_dir(), mode=0o700, exist_ok=True)
    fd = os.open(os.path.join(state_dir(), "telegram.lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        lines = read_log()
        params = {"timeout": 0, "allowed_updates": ["message", "callback_query"]}
        if lines:
            params["offset"] = int(lines[-1]["id"][1:]) + 1
        updates = api(cfg["token"], "getUpdates", params)
        new = []
        for u in updates if isinstance(updates, list) else []:
            if not isinstance(u, dict) or type(u.get("update_id")) is not int:
                continue
            line, cq, hint = entry(cfg, u)
            new.append(line)
            # Answered at once so the button stops spinning; a failure here costs a spinner, never the reply.
            if cq:
                quiet(cfg, "answerCallbackQuery", {"callback_query_id": cq})
            if hint:
                quiet(cfg, "sendMessage", {"chat_id": cfg["chat_id"], "text": HINT})
        cutoff = time.time() - KEEP
        # A dropped update stays as a `skip` line, so the offset moves past it; old lines go after 48 hours,
        # but the newest always stays: without it the offset would start from 0 again.
        kept = [l for l in lines if l.get("time", 0) >= cutoff]
        if lines and not kept and not new:
            kept = lines[-1:]
        if new or len(kept) != len(lines):
            write_log(kept + new)
    finally:
        os.close(fd)


LINKED = re.compile(r"^((?:spec|issue|PR): (?:#\d+ )?)(https://\S+)$")


def styled_block(block):
    """Spec 0038 AC-2: the from: block as escaped HTML; a spec, issue or PR link is an anchor whose text is its
    href, and the step's unverified words go in a collapsed quote."""
    e, out, quote = html.escape, [], []
    for line in block.split("\n"):
        m = LINKED.match(line)
        if quote or line == context.UNVERIFIED:
            quote.append(line)
        elif line == "from:":
            out.append("<b>from:</b>")
        elif m:
            out.append(f'{e(m.group(1))}<a href="{e(m.group(2))}">{e(m.group(2))}</a>')
        else:
            out.append(e(line))
    if quote:
        out.append(f"<b>{e(quote[0])}</b>\n<blockquote expandable>{e(chr(10).join(q[2:] for q in quote[1:]))}</blockquote>")
    return "\n".join(out)


class Topic(ntfy.Topic):
    """ntfy.Topic's title and wait(); sending, polling and taking go through the bot."""

    def publish(self, message, priority, actions=None, stopped=lambda: False, title=None, tags=("question",),
                markup=None, styled=None):
        """AC-5: the title is the first line, priority 2 or lower is silent, actions and tags are ignored.
        Spec 0038: styled, the same message as escaped HTML, is sent instead, and as message once more if refused."""
        title = self.title if title is None else title
        p = {"chat_id": self.cfg["chat_id"], "text": ntfy.cut(f"{title}\n{message}" if title else message, MAX)}
        if priority <= 2:
            p["disable_notification"] = True
        if markup:
            p["reply_markup"] = markup

        def send():
            if styled:
                try:
                    return str(api(self.cfg["token"], "sendMessage", {**p, "text": styled, "parse_mode": "HTML"})
                               ["message_id"])
                except ApiError:
                    pass
            return str(api(self.cfg["token"], "sendMessage", p)["message_id"])
        mid = retry(self.cfg, send, stopped)
        if mid:
            self.own.add(mid)
        return mid

    def ping(self, d, stopped):
        """AC-4: one message, every option a button. d["sent"] is the body; the title goes last, so a swiped reply
        still finds the `<id>:` the message starts with."""
        # Spec 0033 security review: every field through context.safe.
        question = context.safe(self.cfg, d["question"], 1000) or "question waiting, see terminal"
        # Spec 0033 AC-5: the id labeled on its first use, never a bare `<id>:` prefix; ASKED still finds it.
        lines, rows = [f"{context.label(d['id'])}:", question], []
        # Spec 0028 AC-11: the short explanation right under the question, as on ntfy.
        learn = context.safe(self.cfg, d.get("learn"), 300)
        if learn:
            lines.append(f"learn: {learn}")
        # Spec 0033 AC-4: where it comes from, with links, in what room the message has left.
        options_len = sum(len(o) + 4 for o in d["options"]) + 200 + len(self.title)
        block = context.telegram_block(self.cfg, d, MAX - len("\n".join(lines)) - options_len)
        if block:
            lines.append(block)
        for n, label in enumerate(d["options"], 1):
            label = context.safe(self.cfg, label, 200) or f"option {n}"
            lines.append(f"{n} {label}")
            rows.append([{"text": f"{n} {ntfy.cut(label, 40)}", "callback_data": f"{d['id']} {n}"}])
        panel = d["kind"] == "panel"
        lines.append("tap a button, or reply to this message" if panel else "reply to this message with your answer")
        d["sent"] = "\n".join(lines)
        e = html.escape
        styled = [f"<b>{e(lines[0])}</b>", f"<b>{e(question)}</b>"] + ([f"<i>{e(lines[2])}</i>"] if learn else []) + \
            ([styled_block(block)] if block else []) + [e(x) for x in lines[len(lines) - len(rows) - 1:]] + [e(self.title)]
        return self.publish(d["sent"] + "\n" + self.title, 4, stopped=stopped, title="",
                            markup={"inline_keyboard": rows} if panel and rows else None, styled="\n".join(styled))

    def poll(self, cursor):
        """AC-7: fetch, then the log lines after a `u<N>` cursor, else every line."""
        fetch(self.cfg)
        lines = read_log()
        if isinstance(cursor, str) and re.fullmatch(r"u\d+", cursor):
            return [l for l in lines if int(l["id"][1:]) > int(cursor[1:])]
        return lines

    def take(self, text, ds, msg=None):
        """AC-8 for one log line. The decision it answered, or None. No one time code: only your chat is read."""
        m = ntfy.REPLY.match(text)
        when = (msg or {}).get("time")
        d = m and next((d for d in ds if d["id"] == m.group(1).lower() and d["answer"] is None
                        and (not isinstance(when, (int, float)) or asked(d) <= when)), None)
        if not d:
            return None
        rest, labels, answer = m.group(2), d["options"], None
        if labels and re.fullmatch(r"\d+(,\d+)*", rest):
            picks = [int(x) for x in rest.split(",")]
            if (len(picks) == 1 or d["multi"]) and len(set(picks)) == len(picks) \
                    and all(1 <= p <= len(labels) for p in picks):
                answer = ", ".join(labels[p - 1] for p in picks)
        if answer is None:
            answer = next((l for l in labels if l.strip().casefold() == rest.strip().casefold()), rest)
        d.update(answer=answer, source="phone", answered=datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
        return d


def chunks(body):
    """AC-9: messages of at most MAX characters, split at line boundaries."""
    out = [""]
    for line in body.split("\n"):
        line = ntfy.cut(line, MAX)
        if out[-1] and len(out[-1]) + 1 + len(line) > MAX:
            out.append(line)
        else:
            out[-1] = f"{out[-1]}\n{line}" if out[-1] else line
    return out


def send_report(cfg, body):
    """AC-9: up to 3 messages; longer, the head line, the next: line and the same scrubbed body as wf-report.txt
    (never the local report.txt, which holds real names and paths). True when every send returned an id."""
    t, parts = Topic(cfg, "", ""), chunks(body)
    if len(parts) <= 3:
        return all([t.publish(p, 3, title="") for p in parts])
    lines = body.split("\n")
    first = t.publish("\n".join([lines[0], lines[-1], "full report attached"]), 3, title="")
    doc = retry(cfg, lambda: str(api(cfg["token"], "sendDocument", {"chat_id": cfg["chat_id"]},
                                     document=("wf-report.txt", body))["message_id"]), lambda: False)
    return bool(first and doc)


def asked(d):
    try:
        return int(datetime.datetime.fromisoformat(d["asked"]).timestamp())
    except (KeyError, TypeError, ValueError):
        return 0


# -- wf telegram init | test (AC-10) --------------------------------------------

def wait_start(token, code):
    """The chat id of the first private `/start <code>`, long polling for INIT_WAIT seconds; None when none came.
    The code keeps anyone who guesses the bot's name in those minutes from binding their own chat."""
    end, offset = time.monotonic() + INIT_WAIT, None
    while time.monotonic() < end:
        params = {"timeout": max(0, min(LONG_POLL, int(end - time.monotonic()))), "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        try:
            updates = api(token, "getUpdates", params, wait=params["timeout"])
        except ApiError:
            time.sleep(min(2, max(0, end - time.monotonic())))
            continue
        for u in updates if isinstance(updates, list) else []:
            offset = max(offset or 0, u.get("update_id", 0) + 1)
            m = u.get("message") or {}
            if (m.get("chat") or {}).get("type") == "private" and str(m.get("text") or "").strip() == f"/start {code}":
                # Confirmed, so the first wf run does not log it and answer it with the hint.
                quiet({"token": token}, "getUpdates", {"offset": offset, "timeout": 0})
                return m["chat"]["id"]
    return None


def cmd_init(rotate):
    p = path()
    if os.path.lexists(p) and not rotate:
        print(f"{p} exists, use wf telegram init --rotate to replace it")
        return 2
    # getpass: never on the command line, in shell history or a process list.
    token = getpass.getpass("bot token from BotFather (not shown): ").strip()
    if not TOKEN.match(token):
        print("refused: that is not a bot token (digits, a colon, then the key BotFather gave you)")
        return 2
    try:
        name = wf.clean(str(api(token, "getMe").get("username") or ""))
        # getUpdates refuses while a webhook is set.
        api(token, "deleteWebhook")
    except (ApiError, AttributeError) as e:
        print(f"refused: no_telegram: {redact(e, token)}")
        return 5
    code = "".join(secrets.choice(ntfy.CODE_CHARS) for _ in range(6))
    print(f"bot: @{name}")
    print(f"open https://t.me/{name}?start={code}")
    print(f"or send /start {code} to @{name}", flush=True)
    try:
        chat = wait_start(token, code)
    except KeyboardInterrupt:
        print()
        return 130
    if type(chat) is not int:
        print(f"no /start {code} received")
        return 6
    keep = {"aliases": {}, "block": []}
    try:
        old = ntfy.load(need_codes=False)
        keep = {k: old[k] for k in keep}
    except Invalid:
        pass
    try:
        api(token, "sendMessage", {"chat_id": chat, "text": "wf connected"})
    except ApiError as e:
        print(f"warning: {e}")
    ntfy.write({"token": token, "chat_id": chat, **keep}, p)
    print(f"saved {p}")
    return 0


def cmd_test():
    try:
        cfg = load()
    except Invalid as e:
        print(f"refused: no_telegram: {e}")
        return 5
    t = Topic(cfg, "test", "telegram test")
    d = {"id": ntfy.new_id(set()), "kind": "panel", "question": "Did this message reach your phone?",
         "options": ["yes", "no"], "multi": False, "answer": None, "ignored": 0,
         "asked": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    try:
        first = t.ping(d, lambda: False)
        print(f"sent {d['id']}, waiting up to 5 minutes for a tap or a reply", flush=True)
        end = t.wait([d], first, INIT_WAIT, lambda: False, lambda d: None,
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
