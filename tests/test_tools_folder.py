"""Spec 0077 PR B (AC-10, AC-12, AC-13): bin/, scripts/ and config/ live under tools/, on the real tracked files."""
import os
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OLD = ("bin", "scripts", "config")
# AC-13: the folders and files whose path uses must name tools/.
SCANNED = ("claude-home/", "map/", "tests/", "tools/", "docs/guides/")
SCANNED_FILES = ("CLAUDE.md", "README.md")
# Upstream trees: their bin/ and scripts/ are their own, not this repo's.
VENDORED = ("claude-home/agents/", "claude-home/rules/ecc/", "claude-home/skills/anti-ai-writing/", "node_modules/")
BARE = re.compile(r"(?<![\w.~/$-])((?:bin|scripts|config)/[^\s`'\"),;]*)")
UP = re.compile(r"((?:\.\./)+)(?:bin|scripts|config)/")
HOMED = re.compile(r"claude-config/(?:bin|scripts|config)\b")
JOINED = re.compile(r"\b(?:REPO|REAL|ROOT|repo|real_repo|irepo|sync_repo|crafted|stranger|self\.repo) / \"(?:bin|scripts|config)\""
                    r"|\"\.\.\", \"(?:bin|scripts|config)\"")
# (file, token prefix): text that is not a path into this repo, with the reason.
EXEMPT = {
    ("tests/test_tools_folder.py", ""): "this test's own patterns",
    ("tools/scripts/ref-check.py", ""): "self check fixtures: a scratch repo with its own bin/ and scripts/",
    ("tests/test_skill_scan.py", "scripts/a.py"): "a finding path inside a scanned skill",
    ("tests/test_skill_scan.py", "bin/CHANGELOG/run.sh"): "a finding path inside a scanned skill",
    ("tests/test_claude_config.py", "scripts/a.py"): "a finding path inside a scanned skill",
    ("claude-home/mods/chip-dash/panes.test.ts", "bin/deploy.sh"): "box text fixture of some other repo",
    ("docs/guides/SETUP.md", "bin/jjstack-gbrain-phi-lib.sh"): "a jjstack file",
    ("docs/guides/SETUP.md", "scripts/"): "ECC and turnstile-spin folders, not this repo's",
    ("claude-home/skills/design/references/stacks.md", "config/TS"): "prose: config files of a target stack",
    ("claude-home/skills/design/references/reference-lock.md", "config/docs"): "prose about another repo",
}


def tracked():
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True, text=True, check=True,
                         stdin=subprocess.DEVNULL).stdout
    return [f for f in out.split("\0") if f]


def exempt(rel, token):
    if any(f == rel and token.startswith(p) for f, p in EXEMPT):
        return True
    # a path relative to claude-home/ (the live ~/.claude layout), for example scripts/claude-ram-watch.sh
    if (REPO / "claude-home" / token.rstrip(".:")).exists():
        return True
    # a skill's own scripts/ folder, cited from inside that skill
    m = re.match(r"claude-home/skills/([^/]+)/", rel)
    return bool(m and token.startswith("scripts/") and (REPO / "claude-home/skills" / m.group(1) / "scripts").is_dir())


def old_path_hits(files):
    hits = []
    for rel in files:
        p = REPO / rel
        if p.is_symlink() or not p.is_file() or any(v in rel for v in VENDORED):
            continue
        try:
            text = p.read_text()
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            found = [m.group(1) for m in BARE.finditer(line)] + HOMED.findall(line) + JOINED.findall(line)
            # a relative link that climbs to the repo root, for example ../../config/manifest.json from docs/guides/
            found += [m.group(0) for m in UP.finditer(line) if (p.parent / m.group(1)).resolve() == REPO]
            hits += [f"{rel}:{n}: {t}" for t in found if not exempt(rel, t)]
    return hits


def root_finders(rel, text):
    """(line number, folder the expression resolves to) for each way a moved file finds a folder above itself."""
    here = (REPO / rel).resolve().parent
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"\.parents\[(\d)\]|\.parent\.parent", line):
            if "__file__" in line or "SCRIPT" in line:
                out.append((n, (REPO / rel).resolve().parents[int(m.group(1) or 1)]))
        for m in re.finditer(r"(?:dirname [^)]*\)\"?|\$HERE)((?:/\.\.)+)", line):
            out.append((n, (here / m.group(1).lstrip("/")).resolve()))
    return out


class TestToolsFolder(unittest.TestCase):
    # covers: AC-10 (no bin, scripts or config at the root, not even a link; the three live under tools/)
    def test_moved(self):
        left = [d for d in OLD if os.path.lexists(REPO / d)]
        self.assertEqual(left, [], f"{len(left)} old folders at the repo root: {left}")
        top = {f.split("/")[0] for f in tracked()}
        self.assertEqual(sorted(top & set(OLD)), [])
        for d in OLD:
            self.assertTrue((REPO / "tools" / d).is_dir(), f"tools/{d} missing")

    # covers: AC-12 (every moved script that finds the repo from its own path lands on the repo root)
    def test_root_finders(self):
        found, wrong = 0, []
        for rel in tracked():
            if not rel.startswith("tools/") or not rel.endswith((".py", ".sh")):
                continue
            for n, d in root_finders(rel, (REPO / rel).read_text()):
                found += 1
                if d != REPO:
                    wrong.append(f"{rel}:{n} resolves to {d}")
        self.assertGreater(found, 5, "the root finders were not found; the patterns no longer match")
        self.assertEqual(wrong, [], f"{len(wrong)} root finders off the repo root:\n" + "\n".join(wrong))

    # covers: AC-13 (no path use of bin/, scripts/ or config/ outside tools/, in the live folders and files)
    def test_no_old_paths(self):
        files = [f for f in tracked() if f.startswith(SCANNED) or f in SCANNED_FILES or f == "claude-home/CLAUDE.md"]
        hits = old_path_hits(files)
        self.assertEqual(hits, [], f"{len(hits)} old path uses:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
