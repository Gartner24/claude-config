"""Spec 0035: the repo shape, the README map and the single load of the global instructions, checked on the
real tracked files, never on a fixture."""
import os
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Spec 0048 AC-1: four files plus folders. `live` is allowed only as the temporary link to claude-home (AC-15).
TOP = {"README.md", "AGENTS.md", "CLAUDE.md", "LICENSE", "tools", "claude-home", "docs",
       ".claude", ".gitignore", "tests", "map", "_archive"}
# Spec 0048 AC-3: the old paths, outside the doc folders that record history.
OLD = re.compile(r"(?<![\w./~-])live[/]|(?<![\w/.-])\.[/](install|sync)\.sh\b|(?<![\w/.-])(mcp-config|test-preferences)\.json")
HISTORY = ("docs/specs/", "docs/reviews/", "docs/briefs/", "_archive/")
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
    # covers: spec 0048 AC-1 (the repo top holds only the listed entries; scripts in tools/bin/, configs in tools/config/, spec 0077 AC-10)
    def test_top(self):
        top = {p.split("/")[0] for p in tracked()}
        if "live" in top and os.path.islink(REPO / "live") and os.readlink(REPO / "live") == "claude-home":
            top.discard("live")
        extra = sorted(top - TOP)
        self.assertEqual(extra, [], f"{len(extra)} top level entries outside spec 0048 AC-1: {extra}")
        for rel in ("tools/bin/install.sh", "tools/bin/sync.sh", "tools/config/mcp-config.json", "tools/config/test-preferences.json",
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
            # _archive/ is frozen (spec 0072 AC-13): its links were written for the old layout.
            if rel.startswith(VENDORED + ("_archive/",)) or "/node_modules/" in rel:
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

    # covers: spec 0072 AC-8 (CLAUDE.md is the one real entry file, AGENTS.md a symlink to it; .claude/CLAUDE.md is
    # gone, claude-home/CLAUDE.md is the payload)
    def test_single_load(self):
        self.assertTrue((REPO / "CLAUDE.md").is_file() and not (REPO / "CLAUDE.md").is_symlink())
        self.assertTrue((REPO / "AGENTS.md").is_symlink())
        self.assertEqual(os.readlink(REPO / "AGENTS.md"), "CLAUDE.md")
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


GUIDES = {"SETUP.md", "DAILY-USE.md", "SKILLS.md", "HOOKS.md", "DESIGN-PIPELINE.md"}
TYPES = {"Type: tutorial", "Type: how to", "Type: reference", "Type: explanation"}
REWRITTEN = ["README.md", "AGENTS.md", "docs/architecture.md", "tools/config/routing.md"] + [f"docs/guides/{g}" for g in GUIDES]


def load(rel):
    import importlib.util
    spec = importlib.util.spec_from_file_location(Path(rel).stem.replace("-", "_"), REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestDocs(unittest.TestCase):
    # covers: spec 0048 AC-12 (AGENTS.md under 200 lines, README and AGENTS.md each open with who they are for)
    def test_readers(self):
        agents = (REPO / "AGENTS.md").read_text().splitlines()
        self.assertLess(len(agents), 200, f"AGENTS.md has {len(agents)} lines")
        self.assertRegex(agents[2], r"^For an AI agent")
        self.assertRegex((REPO / "README.md").read_text().splitlines()[2], r"^For you")

    # covers: AC-13 (exactly the 5 guides, each with its type on line 2; the evaluation log moved to research)
    def test_guides(self):
        have = {Path(p).name for p in tracked("docs/guides/")}
        self.assertEqual(have, GUIDES)
        for g in sorted(GUIDES):
            self.assertIn((REPO / "docs/guides" / g).read_text().splitlines()[1], TYPES, g)
        self.assertEqual(tracked("docs/research/SKILLS-EVALUATION.md"), ["docs/research/SKILLS-EVALUATION.md"])

    # covers: AC-13 (the committed SKILLS.md equals a fresh `tools/bin/claude-config.py docs`, which reads the repo only)
    def test_skills_generated(self):
        tool = load("tools/bin/claude-config.py")
        self.assertEqual((REPO / "docs/guides/SKILLS.md").read_text(), tool.docs_text(),
                         "docs/guides/SKILLS.md is stale: run python3 tools/bin/claude-config.py docs")

    # covers: AC-13 (every rewritten file passes the ASCII rule)
    def test_ascii(self):
        asciify = load("tools/scripts/asciify.py")
        bad = [rel for rel in REWRITTEN if asciify.convert((REPO / rel).read_text())[0] != (REPO / rel).read_text()]
        self.assertEqual(bad, [])

    # covers: AC-12 (every old item has a row in docs-map.md, no row lands nowhere, every target file exists)
    def test_docs_map(self):
        rows = [r for r in (REPO / "docs/specs/0048-organize-and-sync/docs-map.md").read_text().splitlines()
                if re.match(r"\| [A-Z]+\d+ \|", r)]
        self.assertGreater(len(rows), 300)
        bad = []
        for r in rows:
            cells = [c.strip() for c in r.strip("|").split("|")]
            target, heading = cells[3].strip("`"), cells[4]
            # spec 0077 AC-10: the map is history; its old top level tool targets now live under tools/
            if target.split("/")[0] in ("bin", "scripts", "config"):
                target = "tools/" + target
            if "nowhere" in heading.lower() or not heading:
                bad.append(r)
            elif not heading.startswith("dropped:") and not (REPO / target).exists():
                bad.append(r)
        self.assertEqual(bad, [], f"{len(bad)} rows land nowhere:\n" + "\n".join(bad[:20]))


if __name__ == "__main__":
    unittest.main()
