# Autonomous mode (spec 0030): a Claude session drives the runner. `/auto on` writes <state>/auto.json; the session
# hooks tell that folder's sessions to start `wf -y` as a user unit and relay its questions; `/auto off` lets the
# running build finish its current features (run.py checks the file in pick() and end_wait()).
import datetime
import fcntl
import hashlib
import io
import json
import os
import subprocess
import sys
import time
import types
from contextlib import redirect_stdout

import ntfy
import report
import run
import wf

UNIT = "wf-auto"
WAIT_EVERY = 30
BAR_TIMEOUT = 2
GREEN, RESET = "\033[32m", "\033[0m"
USAGE = "usage: wf auto on | off [now] | status | start | wait | hook | bar"
# AC-4: printed as is.
DRIVE = ("Autonomous mode is on in this folder (the user turned it on with /auto on). You drive the wf runner: "
         "(1) when the status line says wf idle, run wf auto start; (2) then run wf auto wait with run_in_background "
         "and keep working or end your turn, never wait in chat; (3) when wf auto wait ends, act on its line: "
         "\"question <id>\" -> tell the user the question, its options and the recommended one, and say they answer "
         "on their phone; \"run ended\" -> run wf report and give its short list with the next command; \"work\" -> "
         "run wf auto start; \"off\" -> stop driving; then start wf auto wait again unless it said off; (4) never run "
         "wf auto on, never push or merge; (5) if wf auto start fails, say so once and do not retry until the user asks.")


def path():
    return os.path.join(run.state_dir(), "auto.json")


def load():
    """AC-1: the state, or None when missing or unreadable (the session side then treats it as off, AC-9 rationale 9)."""
    try:
        with open(path(), encoding="utf-8") as f:
            s = json.load(f)
    except (OSError, ValueError):
        return None
    return s if isinstance(s, dict) else None


def driving(s, folder):
    return bool(s and s.get("on") is True and s.get("folder") == os.path.realpath(folder))


def change(fn):
    """Read, change and write auto.json under auto.lock, so a wait marking a question relayed never undoes an off."""
    os.makedirs(run.state_dir(), mode=0o700, exist_ok=True)
    fd = os.open(os.path.join(run.state_dir(), "auto.lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        s = {"on": False, "folder": None, "since": None, "started": None, "relayed": [], **(load() or {})}
        fn(s)
        ntfy.write(s, path())
        return s
    finally:
        os.close(fd)


def active():
    """AC-5: the wf-auto unit is running."""
    try:
        return subprocess.run(["systemctl", "--user", "is-active", UNIT], capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=10).stdout.strip() == "active"
    except (OSError, subprocess.SubprocessError):
        return False


def open_questions():
    """Unanswered decisions in queue.json, or None when it cannot be read."""
    try:
        return [d for d in run.queue_transact()["decisions"] if d["answer"] is None]
    except run.QueueError:
        return None


def counts():
    q = open_questions()
    return report.locks_held(), "?" if q is None else len(q)


def status_line(folder):
    """AC-6."""
    s = load()
    if not (s and s.get("on") is True):
        return "autonomous: off"
    if not driving(s, folder):
        return f"autonomous: on in {wf.clean(os.path.basename(s.get('folder') or ''))}"
    n, q = counts()
    return f"autonomous: on, wf {f'running {n} repos' if n else 'idle'}, {q} questions open"


def fingerprint():
    """AC-5: a hash of the (repo, feature) pairs bare `wf` would build, as finish.cmd_wf plans them; '' for none."""
    import finish
    args = wf.build_parser()[0].parse_args(["-y"])
    try:
        with redirect_stdout(io.StringIO()):
            repos, _ = finish.covered(types.SimpleNamespace(target=None))
            if repos is None:
                return ""
            back, _ = finish.retakes(args, repos)
            r = run.Run(None, args)
            r.retaken = {(p["repo"], p["feature"]) for p, _ in back}
            if r.bare_checks() is not None:
                return ""
            r.plan()
    except (run.QueueError, run.Stop, OSError):
        return ""
    pairs = sorted([h["c"].path, f] for h in r.held if h.get("has_work") for f in h["queued"])
    return hashlib.sha256(json.dumps(pairs).encode()).hexdigest() if pairs else ""


def wf_path():
    """The wf this process runs as (~/.local/bin/wf links to the newest runner copy, spec 0020 AC-12)."""
    me = sys.argv[0]
    if os.path.basename(me) in ("wf", "wf.py"):
        return os.path.abspath(me)
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "wf.py")


# -- commands -----------------------------------------------------------------

def on():
    # AC-3: Claude can never turn it on; a wf run call would start unattended runs on its own.
    if os.environ.get("WF_RUN"):
        print("refused: user_only")
        return 5
    folder = os.path.realpath(os.getcwd())
    change(lambda s: s.update(on=True, folder=folder, since=datetime.datetime.now().astimezone().isoformat()))
    print(f"autonomous: on in {wf.clean(os.path.basename(folder))}")
    return 0


def off(now):
    change(lambda s: s.update(on=False))
    if not now:
        print("autonomous: off, a running build finishes its current features")
        return 0
    try:
        subprocess.run(["systemctl", "--user", "stop", UNIT], capture_output=True, stdin=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"warning: systemctl: {run.flat(str(e))}")
    print("autonomous: off, build stopped")
    return 0


def start():
    """AC-5: wf -y as a user unit outside the session."""
    s = load()
    if os.environ.get("WF_RUN"):
        print("refused: user_only")
        return 5
    if not (s and s.get("on") is True):
        print("refused: off")
        return 5
    if active():
        print("wf already running")
        return 0
    argv = ["systemd-run", "--user", "--unit", UNIT, "--collect", "--working-directory", s["folder"],
            "--setenv", f"PATH={os.environ.get('PATH', '')}", "--setenv", "WF_AUTO=1"]
    for k in ("XDG_STATE_HOME", "XDG_CONFIG_HOME"):
        if os.environ.get(k):
            argv += ["--setenv", f"{k}={os.environ[k]}"]
    fp = fingerprint()
    try:
        p = subprocess.run([*argv, "--", wf_path(), "-y"], capture_output=True, text=True, stdin=subprocess.DEVNULL,
                           timeout=60)
        error = None if p.returncode == 0 else run.flat(p.stderr) or f"exit {p.returncode}"
    except (OSError, subprocess.SubprocessError) as e:
        error = run.flat(str(e))
    if error:
        print(f"failed: {error}")
        return 1
    change(lambda s: s.update(started=fp))
    print("wf started")
    return 0


def wait(every=WAIT_EVERY):
    """AC-8: the first of off, question <id>, run ended, work; never exits otherwise."""
    was = active()
    while True:
        s = load()
        if not (s and s.get("on") is True):
            print("off", flush=True)
            return 0
        new = [d["id"] for d in open_questions() or [] if d["id"] not in s.get("relayed", [])]
        if new:
            change(lambda s: s["relayed"].append(new[0]))
            print(f"question {new[0]}", flush=True)
            return 0
        if active():
            was = True
        elif was:
            print("run ended", flush=True)
            return 0
        else:
            fp = fingerprint()
            if fp and fp != s.get("started"):
                print("work", flush=True)
                return 0
        time.sleep(every)


def question_line(d):
    opts = " / ".join(d["options"])
    rec = f"; recommended: {d['options'][0]}" if d["options"] else ""
    return wf.clean(f"question {d['id']}: {d['feature']}: {d['question']} (options: {opts}{rec})")


def hook():
    """AC-4, AC-7: prints only in the driving folder while on, never inside a wf run call."""
    data = json.loads(sys.stdin.read() or "{}")
    if os.environ.get("WF_RUN") or not isinstance(data, dict):
        return
    folder = data.get("cwd") or os.getcwd()
    s = load()
    if not driving(s, folder):
        return
    event = data.get("hook_event_name")
    if event == "SessionStart":
        print(DRIVE)
        print(status_line(folder))
        for d in open_questions() or []:
            if d["id"] not in s.get("relayed", []):
                print(question_line(d))
    elif event == "UserPromptSubmit":
        print(status_line(folder))


def bar():
    """AC-10: jjstack's status line, unchanged, with the autonomous segment on its last line."""
    raw = sys.stdin.read()
    try:
        out = subprocess.run(["bash", os.path.expanduser("~/.claude/skills/jjstack/bin/statusline.sh")], input=raw,
                             capture_output=True, text=True, timeout=BAR_TIMEOUT)
        out = out.stdout.rstrip("\n") if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        out = ""
    seg = ""
    try:
        data = json.loads(raw or "{}")
        data = data if isinstance(data, dict) else {}
        folder = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or os.getcwd()
        s = load()
        if driving(s, folder):
            n, q = counts()
            seg = f" {GREEN}AUTO {f'running {n} repos, {q} question(s)' if n else 'idle'}{RESET}"
        elif s and s.get("on") is True:
            seg = f" auto: {wf.clean(os.path.basename(s.get('folder') or ''))}"
    except Exception:
        pass
    text = out + seg if out else seg.lstrip(" ")
    if text:
        print(text)


def cmd_auto(words):
    if words == ["on"]:
        return on()
    if words and words[0] == "off" and words[1:] in ([], ["now"], ["--now"]):
        return off(bool(words[1:]))
    if words == ["status"]:
        print(status_line(os.getcwd()))
        return 0
    if words == ["start"]:
        return start()
    if words == ["wait"]:
        return wait()
    if words in (["hook"], ["bar"]):
        # AC-4, AC-10: a hook or the status bar never fails the session.
        try:
            hook() if words == ["hook"] else bar()
        except Exception:
            pass
        return 0
    print(USAGE, file=sys.stderr)
    return 2
