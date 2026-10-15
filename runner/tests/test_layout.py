"""Spec 0035: the repo shape, the README map and the single load of the global instructions, checked on the
real tracked files, never on a fixture."""
import os
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
# Spec 0048 AC-1: four files plus folders. `live` is allowed only as the temporary link to claude-home (AC-15).
TOP = {"README.md", "AGENTS.md", "CLAUDE.md", "LICENSE", "bin", "config", "claude-home", "runner", "scripts", "docs",
       ".claude", ".gitignore"}
# Spec 0048 AC-3: the old paths, outside the doc folders that record history.
OLD = re.compile(r"(?<![\w./~-])live[/]|(?<![\w/.-])\.[/](install|sync)\.sh\b|(?<![\w/.-])(mcp-config|test-preferences)\.json")
HISTORY = ("docs/specs/", "docs/reviews/", "docs/briefs/")
# Vendored trees are not repo owned (AGENTS.md `## Rules`), so their links are upstream's.
VENDORED = ("claude-home/agents/", "claude-home/rules/ecc/", "claude-home/skills/anti-ai-writing/")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def tracked(*paths):
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z", "--", *paths], capture_output=True, text=True,
                         check=True, stdin=subprocess.DEVNULL).stdout
    return [p for p in out.split("\0") if p]


def links(text):
    text = re.sub(r"(?ms)^\s*```.*?^\s*```", "", text)
    return LINK.findall(re.sub(r"`[^`\n]*`", "", text))


class TestShape(unittest.TestCase):
    # covers: spec 0048 AC-1 (the repo top holds only the listed entries; scripts in bin/, configs in config/)
    def test_top(self):
        top = {p.split("/")[0] for p in tracked()}
        if "live" in top and os.path.islink(REPO / "live") and os.readlink(REPO / "live") == "claude-home":
            top.discard("live")
        extra = sorted(top - TOP)
        self.assertEqual(extra, [], f"{len(extra)} top level entries outside spec 0048 AC-1: {extra}")
        for rel in ("bin/install.sh", "bin/sync.sh", "config/mcp-config.json", "config/test-preferences.json",
                    "docs/NOTICE.md"):
            self.assertEqual(tracked(rel), [rel])

    # covers: spec 0048 AC-3 (no file outside docs/specs, docs/reviews, docs/briefs names an old path)
    def test_old_paths(self):
        hits = []
        for rel in tracked():
            p = REPO / rel
            if rel.startswith(HISTORY) or p.is_symlink() or not p.is_file():
                continue
            try:
                text = p.read_text()
            except UnicodeDecodeError:
                continue
            hits += [f"{rel}:{n}: {line.strip()[:80]}" for n, line in enumerate(text.splitlines(), 1)
                     if OLD.search(line)]
        self.assertEqual(hits, [], f"{len(hits)} old path hits:\n" + "\n".join(hits))

    # covers: AC-3 (every relative markdown link in repo owned markdown resolves; a link out of the repo is
    # checked from ~/claude-config by hand, migrate.md step 12)
    def test_links(self):
        bad = []
        for rel in tracked("*.md"):
            if rel.startswith(VENDORED) or "/node_modules/" in rel:
                continue
            src = REPO / rel
            # The staged copy, not the file on disk: under wf the plan file is main's live copy, whose new rows
            # link specs this branch does not have yet.
            text = subprocess.run(["git", "-C", str(REPO), "show", f":{rel}"], capture_output=True, text=True,
                                  errors="replace", check=True, stdin=subprocess.DEVNULL).stdout
            for target in links(text):
                path = target.split("#")[0]
                if not path or re.match(r"[a-z]+:", path) or path.startswith(("/", "~")):
                    continue
                dst = Path(os.path.normpath(src.parent / path))
                if dst.is_relative_to(REPO) and not dst.exists():
                    bad.append(f"{rel}: {target}")
        self.assertEqual(bad, [], f"{len(bad)} broken links:\n" + "\n".join(bad))

    # covers: AC-4 (root CLAUDE.md only imports AGENTS.md, .claude/CLAUDE.md is gone, claude-home/CLAUDE.md is the payload)
    def test_single_load(self):
        self.assertEqual((REPO / "CLAUDE.md").read_text().strip(), "@AGENTS.md")
        self.assertEqual(tracked(".claude/CLAUDE.md"), [])
        self.assertEqual(tracked("claude-home/CLAUDE.md"), ["claude-home/CLAUDE.md"])


class TestReadme(unittest.TestCase):
    # covers: AC-1 (opens with the Where things live map, one row per kind, under 1200 words), AC-2 (each kind's
    # source of truth as the rule says)
    def test_map(self):
        text = (REPO / "README.md").read_text()
        self.assertLess(len(text.split()), 1200)
        self.assertEqual(re.findall(r"(?m)^## .*", text)[0], "## Where things live")
        section = text.split("## Where things live", 1)[1].split("\n## ", 1)[0]
        rows = {r.split("|")[1].strip().split(" (")[0]: r.split("|")[4].strip()
                for r in section.splitlines() if r.startswith("| ") and not r.startswith("| Kind")}
        for kind, truth in (("Copied", "live wins"), ("Linked", "repo wins"), ("Runner", "repo wins"),
                            ("Frameworks", "their installer wins"), ("Private", "live only"),
                            ("Claude Code state", "Claude Code only")):
            self.assertEqual(rows.get(kind), truth, kind)


if __name__ == "__main__":
    unittest.main()
