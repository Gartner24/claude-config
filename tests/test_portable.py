"""Spec 0082 AC-3: no Linux only or bash 4 construct in live shell and Python code, so it runs on a stock Mac.
Known test data is excused by tests/portable-allow.txt (path | pattern | reason), one line per excuse."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ALLOW = REPO / "tests" / "portable-allow.txt"
SCANNED = re.compile(r"^(tools/|claude-home/hooks/|claude-home/scripts/|claude-home/skills/[^/]+/scripts/)")
# name -> regular expression over one non comment line
BANNED = {
    "bash 4 case change": r"\$\{\w+(\^\^?|,,?)\}",
    "declare -A": r"\bdeclare\s+-\w*A",
    "find -printf": r"\s-printf\b",
    "readlink -f": r"\breadlink\s+-\w*f",
    "realpath command": r"(?<![\w./-])realpath\s+([\"'$]|-\w)|\$\(\s*realpath\b",
    "flock command": r"(?<![\w.])flock\b",
    "timeout command": r"(?<![\w.$-])timeout\s+-?\d",
    "touch -d": r"\btouch\s+(-\w+\s+)*-\w*d\b",
    "sed -i without suffix": r"\bsed\s+(-\w+\s+)*-\w*i(\s|$)",
    "date -d": r"\bdate\s+(-\w+\s+)*-\w*d\b",
    "date %N": r"\bdate\s+[^|;]*%\d*N",
    "stat -c": r"\bstat\s+(-\w+\s+)*-\w*c\b",
    "grep -P": r"\bgrep\s+(-\w+\s+)*-\w*P",
    "xargs -r": r"\bxargs\s+(-\w+\s+)*-\w*r\b",
    "base64 -w": r"\bbase64\s+(-\w+\s+)*-\w*w",
    "/proc/": r"/proc/",
    "sched_getaffinity": r"sched_getaffinity",
    "/home/santiago": r"/home/santiago",
}


def live_files():
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True, text=True, check=True,
                         stdin=subprocess.DEVNULL).stdout
    for rel in out.split("\0"):
        p = REPO / rel
        if not SCANNED.match(rel) or "node_modules/" in rel or p.is_symlink() or not p.is_file():
            continue
        text = p.read_text(errors="replace")
        first = text.split("\n", 1)[0]
        if rel.endswith((".sh", ".py")) or (first.startswith("#!") and re.search(r"\b(ba)?sh\b|python", first)):
            yield rel, text


def allow_entries():
    out = []
    for n, line in enumerate(ALLOW.read_text().splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        path, pattern, reason = (s.strip() for s in line.split(" | ", 2))
        out.append((n, path, re.compile(pattern), reason))
    return out


def hits(files, entries):
    """(hits not excused, allow line numbers that excused something)"""
    found, used = [], set()
    for rel, text in files:
        for n, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            for name, rx in BANNED.items():
                if not re.search(rx, line):
                    continue
                ok = [e[0] for e in entries if e[1] == rel and e[2].search(line)]
                used.update(ok)
                if not ok:
                    found.append(f"{rel}:{n}: {name}: {line.strip()[:120]}")
    return found, used


class TestPortable(unittest.TestCase):
    # covers: AC-1, AC-2, AC-3 (every banned construct on a live line is fixed or excused, count 0)
    def test_no_linux_only_constructs(self):
        entries = allow_entries()
        found, _ = hits(list(live_files()), entries)
        print(f"portable: {len(found)} hit(s)")
        self.assertEqual(found, [], f"{len(found)} Linux only or bash 4 constructs:\n" + "\n".join(found))

    # an excuse that matches nothing is stale: the code it covered was fixed, so the line goes
    def test_no_stale_allow_lines(self):
        entries = allow_entries()
        _, used = hits(list(live_files()), entries)
        stale = [f"portable-allow.txt:{n}: {p}" for n, p, _, _ in entries if n not in used]
        self.assertEqual(stale, [], f"{len(stale)} allow lines excuse nothing:\n" + "\n".join(stale))

    def test_patterns_catch_each_construct(self):
        samples = {
            "bash 4 case change": 'n="${name^^}"', "declare -A": "declare -A M=(", "find -printf": "find . -printf '%P'",
            "readlink -f": 'readlink -f "$x"', "realpath command": 'd="$(realpath "$0")"',
            "flock command": "flock -n 9", "timeout command": "timeout 2 cmd", "touch -d": "touch -d @1 f",
            "sed -i without suffix": "sed -i 's/a/b/' f", "date -d": "date -d yesterday", "date %N": "date -u +%H:%M:%S.%3NZ", "stat -c": "stat -c %Y f",
            "grep -P": "grep -oP 'x'", "xargs -r": "xargs -r rm", "base64 -w": "base64 -w0 f",
            "/proc/": "cat /proc/meminfo", "sched_getaffinity": "os.sched_getaffinity(0)",
            "/home/santiago": "/home/santiago/x",
        }
        self.assertEqual(sorted(samples), sorted(BANNED))
        missed = [k for k, s in samples.items() if not re.search(BANNED[k], s)]
        self.assertEqual(missed, [])
        clean = ["sed -i.bak 's/a/b/' f", "os.path.realpath(p)", "fcntl.flock(fd, 1)", "run(x, timeout=60)",
                 "gtimeout 2 cmd", 'with_timeout 2 "$@"', "touch f", "date +%s"]
        wrong = [s for s in clean for k, rx in BANNED.items() if re.search(rx, s)]
        self.assertEqual(wrong, [])


class TestRamWatch(unittest.TestCase):
    """Spec 0082 AC-4: claude-ram-watch.sh exits 0 at its start on Darwin and logs under $HOME."""
    SCRIPT = REPO / "claude-home" / "scripts" / "claude-ram-watch.sh"

    def run_watch(self, system, *args):
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "bin").mkdir()
        (tmp / "bin" / "uname").write_text(f"#!/bin/sh\necho {system}\n")
        (tmp / "bin" / "uname").chmod(0o755)
        env = {**os.environ, "HOME": str(tmp / "home"), "PATH": f"{tmp / 'bin'}{os.pathsep}{os.environ['PATH']}",
               "DRY_RUN": "1"}
        for k in ("LOG", "UNITDIR"):
            env.pop(k, None)
        r = subprocess.run(["bash", str(self.SCRIPT), *args], env=env, capture_output=True, text=True, timeout=20,
                           stdin=subprocess.DEVNULL)
        return tmp / "home", r

    def test_darwin_exits_at_start(self):
        # no --once: past the check it would watch forever, so the timeout fails the test
        home, r = self.run_watch("Darwin")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(home.exists())

    def test_log_under_home(self):
        home, r = self.run_watch("Linux", "--once")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((home / ".claude" / "logs").is_dir())


def stub_bin(test, system, *tools):
    """A temp bin folder: uname prints system, each tool logs its argv to calls.log. (bin, calls.log)"""
    tmp = Path(tempfile.mkdtemp()).resolve()
    test.addCleanup(shutil.rmtree, tmp)
    (tmp / "bin").mkdir()
    log = tmp / "calls.log"
    (tmp / "bin" / "uname").write_text(f"#!/bin/sh\necho {system}\n")
    for t in tools:
        (tmp / "bin" / t).write_text(f'#!/bin/sh\necho "{t} $*" >> "{log}"\n')
    for f in (tmp / "bin").iterdir():
        f.chmod(0o755)
    return tmp / "bin", log


def calls(log):
    return log.read_text().splitlines() if log.exists() else []


class TestNotifySound(unittest.TestCase):
    """Spec 0082 AC-8: notify-sound.sh plays afplay Glass.aiff on Darwin, the paplay file on Linux, exit 0 without."""
    SCRIPT = REPO / "claude-home" / "hooks" / "notify-sound.sh"
    SOUNDS = {"Darwin": ("afplay", "/System/Library/Sounds/Glass.aiff"),
              "Linux": ("paplay", "/usr/share/sounds/ocean/stereo/outcome-success.oga")}

    def run_hook(self, system, *players):
        # PATH is the stub folder only, so a real afplay or paplay is never found
        b, log = stub_bin(self, system, *players)
        r = subprocess.run([shutil.which("bash"), str(self.SCRIPT)], env={**os.environ, "PATH": str(b)},
                           capture_output=True, text=True, timeout=20, input="{}")
        return r, calls(log)

    def test_player_per_system(self):
        # the sound file is the real one: played where it exists (Glass.aiff on a Mac), else nothing and exit 0
        for system, (player, sound) in self.SOUNDS.items():
            r, ran = self.run_hook(system, "afplay", "paplay")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(ran, [f"{player} {sound}"] if os.path.exists(sound) else [], system)

    def test_no_player_exits_0(self):
        for system in self.SOUNDS:
            r, _ = self.run_hook(system)
            self.assertEqual((r.returncode, r.stderr), (0, ""), system)

    def test_wired(self):
        cmds = [h["command"] for g in json.loads((REPO / "claude-home/settings.json").read_text())["hooks"]["Notification"]
                for h in g["hooks"]]
        self.assertIn("bash ~/.claude/hooks/notify-sound.sh", cmds)
        self.assertEqual([c for c in cmds if "paplay" in c], [])


class TestGeminiKey(unittest.TestCase):
    """Spec 0082 AC-9: gemini-key.sh uses the macOS security tool on Darwin, secret-tool on Linux, and checks for
    gnome-keyring only on Linux."""
    SCRIPT = REPO / "claude-home" / "skills" / "assets" / "scripts" / "gemini-key.sh"

    def run_key(self, system, *args):
        b, log = stub_bin(self, system, "security", "secret-tool", "pgrep")
        env = {**os.environ, "PATH": f"{b}{os.pathsep}{os.environ['PATH']}"}
        env.pop("GEMINI_API_KEY", None)
        r = subprocess.run([shutil.which("bash"), str(self.SCRIPT), *args], env=env, capture_output=True, text=True,
                           timeout=20, stdin=subprocess.DEVNULL)
        return r, calls(log)

    def test_darwin(self):
        r, ran = self.run_key("Darwin", "get")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(ran, ["security find-generic-password -s gemini -a api -w"])
        r, ran = self.run_key("Darwin", "set")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(ran, ["security add-generic-password -U -l Gemini API key -s gemini -a api -w"])
        r, ran = self.run_key("Darwin", "rm")
        self.assertEqual(ran, ["security delete-generic-password -s gemini -a api"])

    def test_linux(self):
        r, ran = self.run_key("Linux", "get")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(ran, ["pgrep -x gnome-keyring-d", "secret-tool lookup service gemini key api"])
        r, ran = self.run_key("Linux", "rm")
        self.assertEqual(ran, ["secret-tool clear service gemini key api"])


if __name__ == "__main__":
    unittest.main()
