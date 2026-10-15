"""Spec 0039 /check verify driver: the real `wf` command in temp HOME and XDG folders, a fake claude, the e2e fake
Telegram bot (WF_TELEGRAM_API) and a fake systemctl on PATH. Prints one PASS or FAIL line per step.
Run: python3 -B docs/specs/0039-questions-while-off/probes/drive.py"""
import fcntl
import json
import os
import select
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "runner" / "tests"), str(ROOT / "runner"), str(ROOT / "runner" / "e2e")]
import fake_telegram  # noqa: E402
import pr  # noqa: E402
import run  # noqa: E402
from test_queue import DecisionCase, ONE, decision  # noqa: E402
from test_run import WF  # noqa: E402
from test_wf_bare import BareCase  # noqa: E402

RESULTS = []
SYSTEMCTL = "#!/bin/sh\necho \"$*\" >> \"$FAKE_DIR/systemctl.log\"\n[ -n \"$SYSTEMCTL_FAIL\" ] && { echo boom >&2; exit 1; }\nexit 0\n"


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"{name} {'PASS' if ok else 'FAIL'}" + ("" if ok else f": {detail}"), flush=True)


class Drive(DecisionCase, BareCase):
    def queue_file(self):
        return self.state / "wf" / "queue.json"

    def put(self, decisions):
        self.queue_file().parent.mkdir(parents=True, exist_ok=True)
        self.queue_file().write_text(json.dumps({"version": 1, "parks": [], "decisions": decisions}))

    def decisions(self):
        return json.loads(self.queue_file().read_text())["decisions"]

    def sub(self, *args, env=None):
        return subprocess.run([sys.executable, "-B", str(WF), *args], capture_output=True, text=True,
                              env={**self.env, **(env or {})}, timeout=60, stdin=subprocess.DEVNULL)

    def interactive(self, *args):
        """Bare wf with a terminal on stdin; returns (proc, master, read_until)."""
        master, slave = os.openpty()
        p = subprocess.Popen([sys.executable, "-B", str(WF), *args], stdin=slave, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, env=self.env)
        os.close(slave)
        self.addCleanup(lambda: p.poll() is None and p.kill())
        self.addCleanup(p.stdout.close)
        buf = bytearray()

        def until(text, timeout=30):
            end = time.monotonic() + timeout
            while text.encode() not in buf and time.monotonic() < end:
                r, _, _ = select.select([p.stdout], [], [], 0.2)
                if r:
                    chunk = os.read(p.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    buf.extend(chunk)
            return buf.decode(errors="replace")
        return p, master, until

    def test_all(self):
        demo = self.make_repo("quux", ONE)
        ctx = {"spec": "https://github.com/acme/demo/blob/work/docs/specs/0001-x/index.md",
               "issues": ["https://github.com/acme/demo/issues/3"],
               "pr": {"number": 7, "url": "https://github.com/acme/demo/pull/7"}}

        # V1 AC-5: nothing open, read only.
        r = self.sub("questions")
        check("V1 wf questions, none open, no state folder made",
              r.returncode == 0 and r.stdout == "no open questions\n" and not (self.state / "wf").exists(), r)

        # V2 AC-5: oldest first, answered ones left out, links, control characters cleaned.
        self.put([decision(demo, "1. A", did="ab12", asked="2026-10-12T11:00:00+02:00", context=ctx),
                  decision(demo, "2. B", did="cd34", options=[], kind="prose", question="Name it\x1b[31m?",
                           asked="2026-10-12T08:00:00+02:00"),
                  decision(demo, "3. C", did="ef56", answer="SQLite", source="phone")])
        before = self.queue_file().read_bytes()
        r = self.sub("questions")
        want = ["cd34 quux: 2. B: Name it[31m?", "  (no options, type your answer)",
                "  asked: 2026-10-12T08:00:00+02:00",
                "ab12 quux: 1. A: Which storage engine?", "  1 Postgres (recommended) (recommended)", "  2 SQLite",
                f"  spec: {ctx['spec']}", "  issue: https://github.com/acme/demo/issues/3",
                "  PR: #7 https://github.com/acme/demo/pull/7", "  asked: 2026-10-12T11:00:00+02:00"]
        check("V2 wf questions lists open ones oldest first with links, changes nothing",
              r.returncode == 0 and r.stdout.splitlines() == want and "\x1b" not in r.stdout
              and self.queue_file().read_bytes() == before, r.stdout)

        # V3 AC-5: unreadable queue.
        self.queue_file().write_text("{")
        r = self.sub("questions")
        check("V3 wf questions refuses an unreadable queue",
              r.returncode == 5 and r.stdout.startswith("refused: queue_unreadable: "), r)

        # V4 AC-1: an unreadable queue on bare wf -y is one warning line, then the screen goes on.
        r = self.bare("-y")
        out = r.stdout.splitlines()
        check("V4 bare wf -y with an unreadable queue warns once and goes on",
              len([l for l in out if l.startswith("warning: questions not read:")]) == 1
              and out[0].startswith("warning: questions not read:") and len(out) > 1, r.stdout + r.stderr)

        # V5 AC-1, AC-2: -y lists the section first and asks nothing. Repo untrusted so nothing builds.
        self.put([decision("/nowhere/quux", "1. A", did="ab12")])
        r = self.bare("-y")
        check("V5 bare wf -y prints the questions section first and writes nothing",
              r.stdout.startswith("questions:\n  ab12 quux: 1. A: Which storage engine?\n"
                                  "    1 Postgres (recommended) (recommended)\n    2 SQLite\n")
              and "answer ab12" not in r.stdout and self.decisions()[0]["answer"] is None, r.stdout + r.stderr)

        # V6 AC-2: Enter skips, a label typed in other case matches, source keyboard, answered set.
        self.put([decision("/nowhere/quux", "1. A", did="ab12", asked="2026-10-12T08:00:00+02:00"),
                  decision("/nowhere/quux", "2. B", did="cd34")])
        p, master, until = self.interactive()
        until("answer ab12 (number, text, Enter skips): ")
        os.write(master, b"\n")
        until("answer cd34 (number, text, Enter skips): ")
        os.write(master, b"sqlite\n")
        out = until("answered: cd34")
        time.sleep(0.5)
        p.send_signal(signal.SIGINT)
        p.wait(30)
        os.close(master)
        ds = {d["id"]: d for d in self.decisions()}
        check("V6 Enter skips, a typed label is written with source keyboard",
              "answered: cd34 SQLite (keyboard)" in out and ds["ab12"]["answer"] is None
              and (ds["cd34"]["answer"], ds["cd34"]["source"]) == ("SQLite", "keyboard") and ds["cd34"]["answered"],
              out + json.dumps(ds))

        # V7 AC-2: the phone got there first while the prompt waited.
        self.put([decision("/nowhere/quux", "1. A", did="ab12")])
        p, master, until = self.interactive()
        until("answer ab12 (number, text, Enter skips): ")
        q = json.loads(self.queue_file().read_text())
        q["decisions"][0].update(answer="SQLite", source="phone", answered="2026-10-14T09:00:00+02:00")
        self.queue_file().write_text(json.dumps(q))
        os.write(master, b"1\n")
        out = until("already answered")
        p.send_signal(signal.SIGINT)
        p.wait(30)
        os.close(master)
        d = self.decisions()[0]
        check("V7 a question the phone answered first says already answered and keeps the phone answer",
              "already answered: ab12" in out and (d["answer"], d["source"]) == ("SQLite", "phone"), out)

        # V8 AC-2: end of input and Ctrl C cancel with 130; an answer already written stays.
        self.put([decision("/nowhere/quux", "1. A", did="ab12", asked="2026-10-12T08:00:00+02:00"),
                  decision("/nowhere/quux", "2. B", did="cd34")])
        p, master, until = self.interactive()
        until("answer ab12 (number, text, Enter skips): ")
        os.write(master, b"2\n")
        until("answer cd34 (number, text, Enter skips): ")
        os.write(master, b"\x04")
        rc_eof = p.wait(30)
        os.close(master)
        ds = {d["id"]: d for d in self.decisions()}
        self.put([decision("/nowhere/quux", "1. A", did="ab12")])
        p, master, until = self.interactive()
        until("answer ab12 (number, text, Enter skips): ")
        p.send_signal(signal.SIGINT)
        rc_int = p.wait(30)
        os.close(master)
        check("V8 end of input and Ctrl C exit 130, the earlier answer stays",
              (rc_eof, rc_int) == (130, 130) and ds["ab12"]["answer"] == "SQLite" and ds["cd34"]["answer"] is None,
              (rc_eof, rc_int, ds))

    def test_resume(self):
        # V9 AC-3: a real run asks, the wf screen answers at the keyboard, the next run resumes the call with it.
        demo = self.make_repo("quux", ONE)
        later = self.make_repo("later", ONE)
        self.commit(later)
        self.trust(later)
        d = self.open_one("later")
        r = self.bare(stdin="2\nx\n")
        from test_queue import DONE_A, TICK_A
        self.steps([TICK_A, DONE_A])
        r2 = self.wf("later", "-y", mode="fast")
        resumed = [json.loads(p.read_text())["argv"][:4] for p in self.calls()]
        check("V9 a keyboard answer resumes the parked call on the next run",
              f"answered: {d['id']} SQLite (keyboard)" in r.stdout and r2.returncode == 0
              and f"  resume: {d['id']} 1. A: Which storage engine?\n" in r2.stdout
              and ["-p", run.ANSWERED + "SQLite", "--resume", d["session_id"]] in resumed,
              r.stdout + r2.stdout + str(resumed) + d["session_id"])

    def test_strong(self):
        demo = self.make_repo("quux", ONE)

        # V10 AC-4: a keyboard answer can approve a merge where only coded phone answers can.
        r = type("R", (), {"ntfy": {"topic": "x"}})()
        check("V10 a keyboard answer is strong, an uncoded phone answer is not",
              pr.strong(r, {"source": "keyboard"}) and not pr.strong(r, {"source": "phone"})
              and run.queue_problem({"version": 1, "parks": [], "decisions": [
                  decision(demo, "1. A", answer="x", source="keyboard", answered="t")]}) is None)

    def test_tap_kept(self):
        # V15 Done when: a reply sent while wf is off, saved by `wf telegram fetch`, resumes the call on the next
        # run even after Telegram has dropped the update.
        fake_telegram.tap = lambda markup: None
        bot = fake_telegram.Server()
        self.addCleanup(bot.close)
        self.env["WF_TELEGRAM_API"] = bot.url
        cfg = self.tmp / "config" / "wf" / "telegram.json"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps(bot.config()))
        cfg.chmod(0o600)
        later = self.make_repo("later", ONE)
        self.commit(later)
        d = self.open_one("later")
        asked = bool(bot.sent)
        bot.updates.append({"update_id": 900, "message": {
            "chat": {"id": fake_telegram.CHAT}, "from": {"id": fake_telegram.CHAT}, "text": f"{d['id']} 2",
            "date": int(time.time()) + 5}})
        r = self.sub("telegram", "fetch")
        bot.updates.clear()
        from test_queue import DONE_A, TICK_A
        self.steps([TICK_A, DONE_A])
        r2 = self.wf("later", "-y", mode="fast")
        calls = [json.loads(p.read_text())["argv"][:4] for p in self.calls()]
        check("V15 a reply sent while wf is off is kept by the fetch and resumes the call on the next run",
              asked and r.returncode == 0 and r2.returncode == 0
              and ["-p", run.ANSWERED + "SQLite", "--resume", d["session_id"]] in calls,
              (asked, r, r2.stdout, calls))

    def test_telegram(self):
        bot = fake_telegram.Server()
        self.addCleanup(bot.close)
        env = {"WF_TELEGRAM_API": bot.url}
        cfg = self.tmp / "config" / "wf" / "telegram.json"
        log = self.state / "wf" / "telegram-updates.jsonl"
        msg = lambda n, text: {"update_id": n, "message": {"chat": {"id": fake_telegram.CHAT},
                                                           "from": {"id": fake_telegram.CHAT}, "text": text,
                                                           "date": int(time.time())}}

        # V11 AC-6: no telegram.json: exit 0, nothing made.
        r = self.sub("telegram", "fetch", env=env)
        check("V11 telegram fetch with no telegram.json exits 0 and makes nothing",
              r.returncode == 0 and r.stdout == r.stderr == "" and not log.exists(), r)

        # V12 AC-6: a fetch saves the updates silently; a second fetch adds nothing twice; a new one is added.
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps(bot.config()))
        cfg.chmod(0o600)
        bot.updates.append(msg(500, "ab12 2"))
        r1 = self.sub("telegram", "fetch", env=env)
        r2 = self.sub("telegram", "fetch", env=env)
        bot.updates.append(msg(501, "cd34 1"))
        r3 = self.sub("telegram", "fetch", env=env)
        ids = [json.loads(l)["id"] for l in log.read_text().splitlines()] if log.exists() else []
        msgs = [json.loads(l).get("message") for l in log.read_text().splitlines()] if log.exists() else []
        check("V12 telegram fetch saves updates silently and never twice",
              [x.returncode for x in (r1, r2, r3)] == [0, 0, 0] and all(x.stdout == x.stderr == "" for x in (r1, r2, r3))
              and ids == ["u500", "u501"] and msgs == ["ab12 2", "cd34 1"], (ids, msgs, r1, r3))

        # V13 AC-6: while a run holds telegram.lock, the fetch returns and reads nothing.
        bot.updates.append(msg(502, "ef56 1"))
        fd = os.open(self.state / "wf" / "telegram.lock", os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            t0 = time.monotonic()
            r = self.sub("telegram", "fetch", env=env)
            took = time.monotonic() - t0
        finally:
            os.close(fd)
        n = len(log.read_text().splitlines())
        check("V13 telegram fetch under a held lock returns at once and saves nothing",
              r.returncode == 0 and n == 2 and took < 10, (r, n, took))

        # V14 AC-6: invalid telegram.json: one stderr line, exit 1.
        cfg.chmod(0o644)
        r = self.sub("telegram", "fetch", env=env)
        check("V14 telegram fetch with an invalid telegram.json exits 1 with one stderr line",
              r.returncode == 1 and len(r.stderr.splitlines()) == 1 and r.stdout == "", r)
        cfg.chmod(0o600)

        # V16 AC-7: timer on writes both units with this state folder and enables it.
        self.fake("systemctl", SYSTEMCTL)
        units = self.tmp / "config" / "systemd" / "user"
        slog = self.fakes / "systemctl.log"
        r = self.sub("telegram", "timer", "on")
        service = (units / "wf-telegram-fetch.service").read_text() if (units / "wf-telegram-fetch.service").exists() else ""
        timer = (units / "wf-telegram-fetch.timer").read_text() if (units / "wf-telegram-fetch.timer").exists() else ""
        calls = slog.read_text().splitlines() if slog.exists() else []
        check("V16 timer on writes the service and timer and enables it",
              r.returncode == 0 and "Type=oneshot\n" in service
              and f'Environment="XDG_STATE_HOME={self.state}"\n' in service
              and f'Environment="XDG_CONFIG_HOME={self.tmp / "config"}"\n' in service
              and f'ExecStart="{sys.executable}" "{os.path.realpath(WF)}" telegram fetch\n' in service
              and "OnBootSec=1min\n" in timer and "OnUnitActiveSec=5min\n" in timer
              and "WantedBy=timers.target\n" in timer
              and calls == ["--user daemon-reload", "--user enable --now wf-telegram-fetch.timer"],
              (r, service, timer, calls))
        (self.fakes / "units").mkdir(exist_ok=True)
        for f in units.iterdir():
            (self.fakes / "units" / f.name).write_text(f.read_text())

        # V17 AC-7: the service's own command line works: run it as systemd would.
        exec_line = next(l for l in service.splitlines() if l.startswith("ExecStart="))
        argv = [a.strip('"') for a in exec_line[len("ExecStart="):].split(" ")]
        bot.updates.append(msg(503, "gh78 1"))
        # Only what the unit sets, as systemd would: a missing Environment= line reads another state folder.
        clean = {"HOME": str(self.tmp), "PATH": "/usr/bin:/bin", "WF_TELEGRAM_API": bot.url}
        for l in service.splitlines():
            if l.startswith("Environment="):
                k, v = l[len("Environment="):].strip('"').split("=", 1)
                clean[k] = v
        r = subprocess.run(argv, capture_output=True, text=True, env=clean, timeout=60)
        ids = [json.loads(l)["id"] for l in log.read_text().splitlines()]
        check("V17 the unit's ExecStart fetches into the state folder a run reads",
              r.returncode == 0 and ids[-1] == "u503", (r, ids))

        # V18 AC-7: off disables, removes both files, reloads.
        slog.unlink()
        r = self.sub("telegram", "timer", "off")
        check("V18 timer off disables and removes both units",
              r.returncode == 0 and list(units.iterdir()) == []
              and slog.read_text().splitlines() == ["--user disable --now wf-telegram-fetch.timer", "--user daemon-reload"],
              (r, list(units.iterdir())))

        # V19 AC-7: refusals and a failed systemctl.
        slog.unlink()
        r1 = self.sub("telegram", "timer", "on", env={"WF_RUN": "x"})
        r3 = self.sub("telegram", "timer", "on", env={"SYSTEMCTL_FAIL": "1"})
        r4 = self.sub("telegram", "timer", "off", env={"SYSTEMCTL_FAIL": "1"})
        cfg.unlink()
        r2 = self.sub("telegram", "timer", "on")
        check("V19 timer on refuses under WF_RUN and without telegram.json; a failed systemctl exits 1",
              (r1.returncode, r2.returncode, r3.returncode, r4.returncode) == (5, 5, 1, 1)
              and r1.stdout.startswith("refused: unattended") and r2.stdout.startswith("refused: no_telegram: ")
              and "systemctl: boom" in r3.stdout and "systemctl: boom" in r4.stdout, (r1, r2, r3, r4))


if __name__ == "__main__":
    os.environ.pop("WF_RUN", None)
    prog = unittest.main(argv=[sys.argv[0]], exit=False, verbosity=0)
    bad = [n for n, ok in RESULTS if not ok]
    # A step that crashed takes the rest of its method with it; those never count as passing.
    ran = {n.split()[0] for n, _ in RESULTS}
    for n in (f"V{i}" for i in range(1, 20)):
        if n not in ran:
            print(f"{n} FAIL: never ran")
            bad.append(n)
    if not prog.result.wasSuccessful():
        bad.append("a step crashed")
    print(f"{len(RESULTS) - len(bad)} of {len(RESULTS)} steps pass" + (f", failed: {', '.join(bad)}" if bad else ""))
    sys.exit(1 if bad else 0)
