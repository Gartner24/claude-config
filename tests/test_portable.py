"""Spec 0082 AC-3: no Linux only or bash 4 construct in live shell and Python code, so it runs on a stock Mac.
Known test data is excused by tests/portable-allow.txt (path | pattern | reason), one line per excuse."""
import re
import subprocess
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
            "sed -i without suffix": "sed -i 's/a/b/' f", "date -d": "date -d yesterday", "stat -c": "stat -c %Y f",
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


if __name__ == "__main__":
    unittest.main()
