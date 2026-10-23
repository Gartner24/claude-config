"""Spec 0077 AC-1 to AC-3: the always loaded text is small, every moved rule has a home and a loader, and no line of
the old CLAUDE.md or rules/ was lost on the way."""
import json
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOME = REPO / "claude-home"
OND = HOME / "rules-on-demand"
# The commit before spec 0077a: the text the line homes check compares against.
BASE = "e361b3d51a63ad0ed64eeacb3446b7b41e2adabc"
LIMIT = 20000
KEPT_RULES = {"lessons.md", "no-attribution.md", "plain-questions.md", "new-number-replaces-old.md", "stop-and-reset.md"}
# Kept equal to map.json on purpose (AC-3): a key added to the map without adding it here fails.
KEYS = {"scope", "architect", "develop", "check", "test", "sync", "audit", "debug", "review", "review-stack", "review-fix",
        "jj-security-review", "security-review", "code-review", "rollover", "save-and-clear", "resume-from-clear",
        "workflow-builder", "build-features", "restructure-check", "design", "design-gate", "assets", "document",
        "write", "pr"}
# The situation pointer lines of AC-2: each file must be named by a "read ~/.claude/rules-on-demand/<file>" line.
POINTED = {"when-to-switch-on.md", "review-fix.md", "branch-pr.md", "handoff.md", "handover-carry.md",
           "second-review.md", "cheap-worker.md", "skill-map.md", "scope-contract.md", "workflow.md", "reviewers.md"}
# AC-5 removed the per-message reminder; the one old line that cited it, and what it became.
EDITED = {
    "| Session start in a repo, or plan / replan / enroll a feature | `/scope` | low | session | mod start at chat open; "
    "a reminder on every message to run `/scope <item>` for new work; catch: an edited file no spec names |":
    "| Session start in a repo, or plan / replan / enroll a feature | `/scope` | low | session | mod start at chat open; "
    "catch: an edited file no spec names |",
    # main's spec 0074 rewrote this line after the base commit; the text moved with the file.
    "- Parallel features (31). When: the owner says \"do these features\", or two or more features are ready. Do: one "
    "`isolation: worktree` agent per feature, never two whose spec `**Paths:**` overlap (run `spec-paths --overlap NNNN "
    "NNNN` for each pair before starting the second; exit 1 means they overlap, so the second waits), never two apps on "
    "one port. Pick model and effort per agent (effort at most high, at least low; haiku for lookup, sonnet for edits "
    "and review, opus for design and hard work). Writing the scope rows and the `/architect` questions for all of them "
    "comes first (`rules/runner-handoff.md`; the build starts in a fresh chat per `rules/fresh-chat-after-architect.md`)."
    " Gates before each extra agent: see the 32 line below.":
    "- Parallel features (31). When: the owner says \"do these features\", or two or more features are ready. Do: run "
    "`/build-features`, never hand started agents. It starts one `isolation: worktree` agent per picked row, never two "
    "whose spec `**Paths:**` overlap (`spec-paths --overlap NNNN NNNN`), and proposes model and effort per row (effort "
    "at most high, at least low; haiku for lookup, sonnet for edits and review, opus for design and hard work). Never "
    "two apps on one port. Writing the scope rows and the `/architect` questions for all of them comes first "
    "(`rules/runner-handoff.md`; the build starts in a fresh chat per `rules/fresh-chat-after-architect.md`). Gates "
    "before each extra agent: see the 32 line below.",
}


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True,
                          stdin=subprocess.DEVNULL).stdout


def always_loaded():
    files = [HOME / "CLAUDE.md"] + sorted((HOME / "rules").glob("*.md"))
    return {str(f.relative_to(HOME)): len(f.read_text()) for f in files}


def mapping():
    return json.loads((OND / "map.json").read_text())


class TestAlwaysLoaded(unittest.TestCase):
    # covers: AC-1 (CLAUDE.md plus rules/*.md, not rules/ecc/, at most 20,000 characters; the total is printed)
    def test_under_limit(self):
        sizes = always_loaded()
        total = sum(sizes.values())
        self.assertLessEqual(total, LIMIT, f"always loaded text is {total} characters (limit {LIMIT}): {sizes}")

    # covers: AC-2 (rules/ keeps exactly the five files; CLAUDE.md keeps its sections and one Routing block)
    def test_kept(self):
        self.assertEqual({p.name for p in (HOME / "rules").glob("*.md")}, KEPT_RULES)
        text = (HOME / "CLAUDE.md").read_text()
        for h in ("## Approach", "## Output", "## Code Rules", "## The ticket is the spec", "## ASCII Only",
                  "## Agent Behavior", "## Hallucination Prevention", "## Shell Discipline", "## Debugging Rules",
                  "### Every review answers these two first"):
            self.assertIn(f"\n{h}\n", "\n" + text, h)
        for line in ("State the bug. Show the fix. Stop.", "No suggestions beyond the scope of the review.",
                     "No compliments on the code before or after the review."):
            self.assertIn(f"\n{line}\n", "\n" + text, line)
        self.assertEqual(re.findall(r"(?m)^## Routing$", text), ["## Routing"])
        self.assertIn("\n@~/.claude/private/work.md\n", text)
        for gone in ("## Review Rules", "### Which reviewer to use", "### Decision gate", "### Todos", "### Context",
                     "### Never in a repo", "## Language Rules", "## UI / design work", "### Route by situation"):
            self.assertNotIn(gone, text)

    # covers: AC-2 (one pointer line per situation, each naming the file to read)
    def test_pointer_lines(self):
        text = (HOME / "CLAUDE.md").read_text()
        missing = [f for f in sorted(POINTED) if f"read ~/.claude/rules-on-demand/{f}" not in text
                   and f"and ~/.claude/rules-on-demand/{f}" not in text]
        self.assertEqual(missing, [], f"{len(missing)} pointer files not named: {missing}")


class TestRulesOnDemand(unittest.TestCase):
    # covers: AC-3 (the map keys are the fixed list; every mapped file exists)
    def test_map(self):
        m = mapping()
        self.assertEqual(set(m), KEYS)
        gone = sorted({f for files in m.values() for f in files if not (OND / f).is_file()})
        self.assertEqual(gone, [], f"{len(gone)} mapped files do not exist: {gone}")

    # covers: AC-3 (a file no skill and no pointer line names fails)
    def test_every_file_is_loaded(self):
        named = {f for files in mapping().values() for f in files}
        text = (HOME / "CLAUDE.md").read_text()
        orphans = [p.name for p in sorted(OND.glob("*.md"))
                   if p.name not in named and f"~/.claude/rules-on-demand/{p.name}" not in text]
        self.assertEqual(orphans, [], f"{len(orphans)} files nothing loads: {orphans}")

    # covers: AC-3 (every line of the old CLAUDE.md and rules/*.md is in the kept text or rules-on-demand/, word for
    # word; AC-5's one edited line is in its new form)
    def test_line_homes(self):
        old = ["claude-home/CLAUDE.md"] + [p for p in git("ls-tree", "--name-only", BASE, "claude-home/rules/").split()
                                           if p.endswith(".md")]
        now = set()
        for f in [HOME / "CLAUDE.md", *(HOME / "rules").glob("*.md"), *OND.glob("*.md")]:
            now |= {l.rstrip() for l in f.read_text().splitlines()}
        lost = []
        for rel in old:
            for n, line in enumerate(git("show", f"{BASE}:{rel}").splitlines(), 1):
                line = line.rstrip()
                if not line.strip():
                    continue
                if line in EDITED:
                    line = EDITED[line]
                if line not in now:
                    lost.append(f"{rel}:{n}: {line[:80]}")
        self.assertEqual(lost, [], f"{len(lost)} old lines with no home:\n" + "\n".join(lost))


class TestHook(unittest.TestCase):
    # covers: AC-4 (the hook's own self checks pass)
    def test_self_checks(self):
        r = subprocess.run(["python3", "-B", str(HOME / "hooks/skill-rules.py"), "--test"], capture_output=True,
                           text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # covers: AC-4 (wired on PreToolUse Skill and UserPromptSubmit), AC-5 (the chain-catch --prompt entry is gone)
    def test_wired(self):
        hooks = json.loads((HOME / "settings.json").read_text())["hooks"]
        cmds = lambda event, matcher=None: [h["command"] for g in hooks.get(event, [])
                                            if matcher is None or g.get("matcher") == matcher for h in g["hooks"]]
        mine = "python3 /home/santiago/.claude/hooks/skill-rules.py"
        self.assertIn(mine, cmds("PreToolUse", "Skill"))
        self.assertIn(mine, cmds("UserPromptSubmit"))
        self.assertEqual([c for e in hooks for c in cmds(e) if "chain-catch.py --prompt" in c], [])


if __name__ == "__main__":
    unittest.main()
