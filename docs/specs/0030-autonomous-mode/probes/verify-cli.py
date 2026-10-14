import json, os, stat, subprocess, sys, tempfile, time
from pathlib import Path

WF = "/home/santiago/claude-config/runner/wf.py"
T = Path(tempfile.mkdtemp(dir=os.environ["TMPDIR"])).resolve()
BIN, FAKES, A, B = T / "bin", T / "fakes", T / "work", T / "other"
for d in (BIN, FAKES, A, B):
    d.mkdir()
(BIN / "systemctl").write_text(f"""#!{sys.executable}
import json, os, sys
d = os.environ["FAKE_DIR"]
open(os.path.join(d, "systemctl.log"), "a").write(json.dumps(sys.argv[1:]) + "\\n")
if "is-active" in sys.argv:
    p = os.path.join(d, "states.txt")
    s = open(p).read().split() if os.path.exists(p) else ["inactive"]
    print(s[0])
    if len(s) > 1: open(p, "w").write("\\n".join(s[1:]))
    sys.exit(0 if s[0] == "active" else 3)
""")
(BIN / "systemd-run").write_text(f"""#!{sys.executable}
import json, os, sys
open(os.path.join(os.environ["FAKE_DIR"], "systemd-run.json"), "w").write(json.dumps(sys.argv[1:]))
if os.environ.get("FAKE_RUN_FAIL"):
    print("Failed to start transient service unit: Unit wf-auto.service already exists.", file=sys.stderr); sys.exit(1)
""")
for n in ("systemctl", "systemd-run"):
    (BIN / n).chmod(0o755)
ENV = {**{k: v for k, v in os.environ.items() if k not in ("WF_RUN", "XDG_CONFIG_HOME", "WF_AUTO")},
       "XDG_STATE_HOME": str(T / "state"), "XDG_CONFIG_HOME": str(T / "cfg"), "HOME": str(T),
       "FAKE_DIR": str(FAKES), "PATH": f"{BIN}:{os.environ['PATH']}", "PYTHONDONTWRITEBYTECODE": "1"}
STATE = T / "state" / "wf" / "auto.json"
results = []


def wf(*words, cwd=A, stdin="", env=None, timeout=60):
    p = subprocess.run([sys.executable, "-B", WF, "auto", *words], cwd=cwd, input=stdin, capture_output=True,
                       text=True, env={**ENV, **(env or {})}, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def check(name, ok, evidence):
    results.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} {name}\n    {evidence}")


def st():
    return json.loads(STATE.read_text())


def hook(event, folder=A, **extra):
    return wf("hook", stdin=json.dumps({"hook_event_name": event, "cwd": str(folder), **extra}))


def queue(*decisions):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    (STATE.parent / "queue.json").write_text(json.dumps({"version": 1, "parks": [], "decisions": list(decisions)}))


def decision(did, q="Which storage engine?", feature="demo feat"):
    return {"id": did, "repo": str(A), "feature": feature, "branch": "work", "session_id": "s",
            "call_kind": "box", "command": "/develop c", "box_text": "`/develop c`", "question": q,
            "options": ["Postgres (recommended)", "SQLite"], "kind": "panel", "multi": False, "sent": None,
            "pings": [], "acks": [], "asked": "2026-10-12T09:00:00+02:00", "answer": None, "source": None,
            "answered": None, "ignored": 0, "run": "/x"}


def states(*s):
    (FAKES / "states.txt").write_text("\n".join(s))


def sclog():
    p = FAKES / "systemctl.log"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


# AC-1 + AC-2 on
c, o, e = wf("on")
s = st()
mode = stat.S_IMODE(STATE.stat().st_mode)
check("AC-1/AC-2 on writes 0600 state with real folder", c == 0 and o.strip() == "autonomous: on in work"
      and s["on"] is True and s["folder"] == str(A) and s["since"] and s["relayed"] == [] and mode == 0o600,
      f"exit {c}, out {o.strip()!r}, mode {oct(mode)}, state {s}")
c, o, e = wf("on", cwd=B)
check("AC-1 on in a second folder replaces folder", st()["folder"] == str(B) and o.strip() == "autonomous: on in other",
      f"out {o.strip()!r}, folder {st()['folder']}")
wf("on")

# AC-6 status three forms
queue(decision("ab12"), {**decision("ef56", feature="done feat"), "answer": "SQLite", "source": "phone", "answered": "2026-10-12T10:00:00+02:00"})
o1 = wf("status")[1].strip()
o2 = wf("status", cwd=B)[1].strip()
check("AC-6 status in the folder and elsewhere", o1 == "autonomous: on, wf idle, 1 questions open"
      and o2 == "autonomous: on in work", f"in folder {o1!r}; other {o2!r}")

# AC-4 SessionStart
c, o, e = hook("SessionStart")
lines = o.splitlines()
check("AC-4 SessionStart in folder prints drive text, status, open question",
      c == 0 and lines[0].startswith("Autonomous mode is on in this folder") and "never push or merge" in lines[0]
      and lines[1] == "autonomous: on, wf idle, 1 questions open" and any(l.startswith("question ab12:") for l in lines),
      f"exit {c}, {len(lines)} lines, line2 {lines[1] if len(lines) > 1 else None!r}, last {lines[-1][:90]!r}")
c, o, e = hook("SessionStart", folder=B)
c2, o2, _ = wf("hook", stdin="not json")
check("AC-4 other folder silent; bad stdin silent, exit 0", c == 0 and o == "" and c2 == 0 and o2 == "",
      f"other folder exit {c} out {o!r}; bad stdin exit {c2} out {o2!r}")
# AC-7
c, o, e = hook("UserPromptSubmit", prompt="hello")
check("AC-7 UserPromptSubmit prints only the status line", o.strip() == "autonomous: on, wf idle, 1 questions open",
      f"out {o!r}")
c, o, e = hook("UserPromptSubmit", prompt="/auto off")
check("Security: /auto off typed from a non interactive Claude is not switched by the hook", st()["on"] is True,
      f"state on={st()['on']} after hook prompt '/auto off' from this headless process")

# AC-3
before = STATE.read_bytes()
wf("off")
before = STATE.read_bytes()
c, o, e = wf("on", env={"WF_RUN": "1"})
check("AC-3 on refused under WF_RUN, nothing written", c == 5 and o.strip() == "refused: user_only"
      and STATE.read_bytes() == before, f"exit {c}, out {o.strip()!r}, state unchanged {STATE.read_bytes() == before}")
c, o, e = wf("start", env={"WF_RUN": "1"})
check("AC-3 start refused under WF_RUN", c == 5 and o.strip() == "refused: user_only", f"exit {c}, out {o.strip()!r}")

# AC-6 off, AC-4 silent when off
o = wf("status")[1].strip()
c, oh, _ = hook("SessionStart")
check("AC-6/AC-4 off: status says off, hook silent", o == "autonomous: off" and oh == "", f"status {o!r}, hook {oh!r}")

# AC-5
(FAKES / "systemd-run.json").unlink(missing_ok=True)
c, o, e = wf("start")
check("AC-5 start refused when off", c == 5 and o.strip() == "refused: off"
      and not (FAKES / "systemd-run.json").exists(), f"exit {c}, out {o.strip()!r}")
wf("on")
states("active")
c, o, e = wf("start")
check("AC-5 active unit not started twice", c == 0 and o.strip() == "wf already running"
      and not (FAKES / "systemd-run.json").exists(), f"exit {c}, out {o.strip()!r}")
states("inactive")
c, o, e = wf("start")
argv = json.loads((FAKES / "systemd-run.json").read_text())
want = ["--user", "--unit", "wf-auto", "--collect", "--working-directory", str(A), "--setenv",
        f"PATH={ENV['PATH']}", "--setenv", "WF_AUTO=1", "--setenv", f"XDG_STATE_HOME={T / 'state'}",
        "--setenv", f"XDG_CONFIG_HOME={T / 'cfg'}", "--", WF, "-y"]
check("AC-5 systemd-run argv and started recorded", c == 0 and o.strip() == "wf started" and argv == want
      and "started" in st(), f"exit {c}, out {o.strip()!r}, argv tail {argv[-6:]}, started {st()['started']!r}")
c, o, e = wf("start", env={"FAKE_RUN_FAIL": "1"})
check("AC-5 systemd-run failure reported, exit 1", c == 1 and o.startswith("failed: Failed to start transient"),
      f"exit {c}, out {o.strip()!r}")

# AC-2 off, off now, usage
(FAKES / "systemctl.log").unlink(missing_ok=True)
c, o, e = wf("off")
check("AC-2 off keeps unit, prints finish line", c == 0 and o.strip() == "autonomous: off, a running build finishes "
      "its current features" and st()["on"] is False and ["--user", "stop", "wf-auto"] not in sclog(),
      f"exit {c}, out {o.strip()!r}, systemctl calls {sclog()}")
wf("on")
c, o, e = wf("off", "now")
check("AC-2 off now stops the unit", c == 0 and o.strip() == "autonomous: off, build stopped"
      and ["--user", "stop", "wf-auto"] in sclog(), f"exit {c}, out {o.strip()!r}, systemctl calls {sclog()}")
c, o, e = wf("bogus")
check("AC-2 other argument prints usage, exit 2", c == 2 and e.startswith("usage: wf auto"), f"exit {c}, err {e.strip()!r}")

# AC-8 wait (real CLI, the first three exit before any sleep)
wf("off")
c, o, e = wf("wait", timeout=20)
check("AC-8 wait prints off", c == 0 and o.strip() == "off", f"out {o!r}")
wf("on")
queue(decision("ab12"), decision("cd34", feature="other feat"))
c, o, e = wf("wait", timeout=20)
c2, o2, _ = wf("wait", timeout=20)
check("AC-8 wait relays each new question once", o.strip() == "question ab12" and o2.strip() == "question cd34"
      and st()["relayed"] == ["ab12", "cd34"], f"first {o.strip()!r}, second {o2.strip()!r}, relayed {st()['relayed']}")
states("active", "inactive")
c, o, e = wf("wait", timeout=20)
check("AC-8 run ended when unit was active and now is not", o.strip() == "run ended", f"out {o!r}")
states("inactive")
STATE.write_text(json.dumps({**st(), "started": None}))
try:
    wf("wait", timeout=5)
    check("AC-8 idle with empty plan never exits", False, "wait exited")
except subprocess.TimeoutExpired:
    check("AC-8 idle with empty plan never exits", True, "still waiting after 5 s (idle, no plan, no question)")

# AC-10 bar
jj = T / ".claude" / "skills" / "jjstack" / "bin"
jj.mkdir(parents=True)
(jj / "statusline.sh").write_text('in=$(cat)\necho "top"\necho "model ${#in}"\n')
bar_in = json.dumps({"workspace": {"current_dir": str(A)}})
c, o, e = wf("bar", stdin=bar_in)
check("AC-10 bar keeps jjstack lines, green AUTO on last", c == 0 and o == f"top\nmodel {len(bar_in)} \033[32mAUTO idle\033[0m\n",
      f"out {o!r}")
c, o, e = wf("bar", stdin=json.dumps({"workspace": {"current_dir": str(B)}}))
check("AC-10 other folder: plain auto: segment", o.endswith(" auto: work\n") and "\033[32m" not in o, f"out {o!r}")
(jj / "statusline.sh").unlink()
c, o, e = wf("bar", stdin=bar_in)
check("AC-10 missing jjstack: only the segment, exit 0", c == 0 and o == "\033[32mAUTO idle\033[0m\n", f"exit {c}, out {o!r}")
wf("off")
c, o, e = wf("bar", stdin=bar_in)
check("AC-10 off: nothing", c == 0 and o == "", f"out {o!r}")

print(f"\n{sum(ok for _, ok in results)}/{len(results)} passed; scratch {T}")
sys.exit(0 if all(ok for _, ok in results) else 1)
