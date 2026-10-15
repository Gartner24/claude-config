import contextlib, fnmatch, io, json, os, re, subprocess, sys, tempfile
from unittest import mock

TREE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
WF = os.path.join(TREE, "runner", "wf.py")
sys.path.insert(0, os.path.join(TREE, "runner"))
results = []


def rec(name, ok, detail):
    results.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name + " :: " + detail)


def wf(state, *words, cwd=None, extra=None):
    env = dict(os.environ, XDG_STATE_HOME=state, **(extra or {}))
    env.pop("WF_RUN", None) if not extra or "WF_RUN" not in extra else None
    p = subprocess.run(["python3", "-B", WF, "auto", *words], capture_output=True, text=True, env=env, cwd=cwd or TREE)
    return p.returncode, (p.stdout + p.stderr).strip()


ON = "refused: user_only: type /auto on in the chat"
REL = "refused: user_only: type /auto release <names> in the chat"

# AC-1: every spelling refused, auto.json missing stays missing
state = tempfile.mkdtemp()
for words, line in [(["on"], ON), (["on", "x"], ON), (["on", "a", "b"], ON), (["release", "x"], REL), (["release"], REL)]:
    code, out = wf(state, *words)
    rec(f"AC-1 wf auto {' '.join(words)}", code == 5 and out == line and not os.path.exists(os.path.join(state, "wf", "auto.json")),
        f"exit {code}, out {out!r}, state files {os.listdir(state)}")
for words, line in [(["on"], ON), (["release", "x"], REL)]:
    code, out = wf(state, *words, extra={"WF_RUN": "1"})
    rec(f"AC-1 WF_RUN wf auto {' '.join(words)}", code == 5 and out == line, f"exit {code}, out {out!r}")
# odd spellings through a real shell: two spaces, quotes
for cmd in [f"python3 -B {WF} auto  on", f"python3 -B {WF} auto 'on' x", f'python3 -B {WF} "auto" "release" x']:
    p = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, env=dict(os.environ, XDG_STATE_HOME=state))
    rec(f"AC-1 spelling {cmd.split('wf.py')[1]!r}", p.returncode == 5 and p.stdout.strip() in (ON, REL), f"exit {p.returncode}, out {p.stdout.strip()!r}")

# AC-1: existing auto.json byte for byte unchanged; state_dir untouched
import auto, run
folder = tempfile.mkdtemp()
state2 = tempfile.mkdtemp()
with mock.patch.dict(os.environ, {"XDG_STATE_HOME": state2}):
    os.environ.pop("WF_RUN", None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        c_on = auto.on(folder, [])
    path = os.path.join(run.state_dir(), "auto.json")
    before = open(path, "rb").read()
    code1, out1 = wf(state2, "on", cwd=tempfile.mkdtemp())
    code2, out2 = wf(state2, "release", os.path.basename(folder), cwd=folder)
    rec("AC-1 existing auto.json unchanged", code1 == 5 and code2 == 5 and open(path, "rb").read() == before,
        f"direct on() -> {c_on} {buf.getvalue().strip()!r}; on exit {code1}, release exit {code2}, bytes equal {open(path, 'rb').read() == before}")
    with mock.patch.object(run, "state_dir", side_effect=AssertionError("state_dir called")):
        with contextlib.redirect_stdout(io.StringIO()):
            r = auto.cmd_auto(["on"]), auto.cmd_auto(["release", "x"])
    rec("AC-1 refusal before state_dir", r == (5, 5), f"returns {r}")

    # AC-3: off from the command still turns this chat off
    code, out = wf(state2, "status", cwd=folder)
    rec("AC-3 status while on", code == 0 and "on" in out, f"exit {code}, out {out!r}")
    code, out = wf(state2, "off", cwd=folder)
    s = json.load(open(path))
    rec("AC-3 wf auto off turns chat off", code == 0 and not s["chats"], f"exit {code}, out {out!r}, chats {list(s['chats'])}")

# AC-1 usage and help
code, out = wf(state, "bogus")
rec("AC-1 unknown word usage", code == 2 and out == "usage: wf auto off [now] | status | start | wait | take <repos> | hook | bar", f"exit {code}, out {out!r}")
p = subprocess.run(["python3", "-B", WF, "--help"], capture_output=True, text=True)
helpline = [l for l in p.stdout.splitlines() if "autonomous mode" in l or "hook | bar" in l]
p2 = subprocess.run(["python3", "-B", WF, "auto", "--help"], capture_output=True, text=True)
rec("AC-1 argparse help drops on/release", "on [repos]" not in p.stdout + p2.stdout and "release <repos>" not in p.stdout + p2.stdout,
    f"main help: {helpline}; auto help words: {[l.strip() for l in p2.stdout.splitlines() if 'off' in l]}")

# AC-2: hook typed path still switches (interactive patched; the real process chain is the live box)
folder3 = tempfile.mkdtemp()
state3 = tempfile.mkdtemp()
with mock.patch.dict(os.environ, {"XDG_STATE_HOME": state3}), mock.patch.object(auto, "interactive", return_value=True):
    os.environ.pop("WF_RUN", None)
    def hook(prompt):
        buf = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": prompt, "cwd": folder3}))), \
                contextlib.redirect_stdout(buf):
            auto.cmd_auto(["hook"])
        return buf.getvalue()
    out = hook("/auto on")
    c = auto.chat(auto.load(), folder3)[1]
    rec("AC-2 typed /auto on switches", c is not None and "autonomous:" in out, f"chat {c is not None}, out {out.strip().splitlines()[:2]}")
    other = tempfile.mkdtemp()
    with contextlib.redirect_stdout(io.StringIO()):
        auto.on(folder3, [])
    out = hook("/auto release")
    rec("AC-2 bare /auto release usage", "usage: /auto release <names>" in out, f"out {out.strip().splitlines()[:1]}")
    out = hook("/auto release nosuchrepo")
    rec("AC-2 typed /auto release reaches release()", "release" in out.lower() or "refused" in out, f"out {out.strip().splitlines()[:2]}")
    out = hook("/auto off")
    c = auto.chat(auto.load(), folder3)[1]
    rec("AC-2 typed /auto off switches", c is None, f"chat after off {c}, out {out.strip()!r}")
with mock.patch.dict(os.environ, {"XDG_STATE_HOME": state3, "WF_RUN": "1"}):
    with contextlib.redirect_stdout(io.StringIO()) as b:
        r = auto.on(folder3, []), auto.release(["x"], folder3)
    rec("AC-2 on()/release() keep WF_RUN refusal", r == (5, 5), f"returns {r}, out {b.getvalue().strip()!r}")

# AC-1b / AC-3: deny rules
s = json.load(open(os.path.join(TREE, "live", "settings.json")))
bash = [r[5:-1].replace(":*", "*") for r in s["permissions"]["deny"] if r.startswith("Bash(")]
for cmd in ["wf auto hook", "echo x | wf auto hook", "python3 runner/wf.py auto hook", "wf auto on", "wf auto release x"]:
    rec(f"AC-1b deny {cmd!r}", any(fnmatch.fnmatchcase(cmd, p) for p in bash), "matched")
for cmd in ["wf auto off", "wf auto status", "wf auto take x"]:
    rec(f"AC-3 not denied {cmd!r}", not any(fnmatch.fnmatchcase(cmd, p) for p in bash), "unmatched")

# AC-4: no text anywhere offers `! wf auto on|release`
hits = subprocess.run(["grep", "-rnE", r"! wf auto (on|release)", "live", "runner", "AGENTS.md", "docs/architecture.md"],
                      capture_output=True, text=True, cwd=TREE).stdout.strip()
rec("AC-4 no `! wf auto on/release` offered", hits == "", f"hits {hits!r}")

print(f"\n{sum(ok for _, ok in results)}/{len(results)} passed")
