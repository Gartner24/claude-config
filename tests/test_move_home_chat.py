"""Spec 0067: tools/bin/move-home-chat.sh against a fake HOME and a stub pgrep; never the real ~/.claude."""
import datetime
import fcntl
import json
import os
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

REAL = Path(__file__).resolve().parents[1]
SCRIPT = REAL / "tools" / "bin" / "move-home-chat.sh"

LIVE = "-home-santiago-dotfiles-claude-config"
OLD = "-home-santiago--claude"
COPY = "-home-santiago-claude-config"
HEAD = "# Runner rules for the home chat (private, not committed; spec 0067)"
# -f matches the script's real pattern against the command line in $STUB_WF, so the regex itself is tested
PGREP = ("#!/bin/sh\n"
         "if [ \"$1\" = -f ]; then [ -s \"$STUB_WF\" ] && grep -qE -- \"$2\" \"$STUB_WF\" && echo 515151 && exit 0; exit 1; fi\n"
         "[ -s \"$STUB_PIDS\" ] && cat \"$STUB_PIDS\" && exit 0\nexit 1\n")


def put(p, text, mtime=None):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    if mtime:
        os.utime(p, (mtime, mtime))


def snapshot(home):
    """Everything under home except what a run may legitimately add before a refusal (lock file, archive, .git)."""
    out = {}
    for root, dirs, files in os.walk(home):
        dirs[:] = [d for d in dirs if d != ".git"]
        for n in dirs + files:
            p = Path(root, n)
            rel = str(p.relative_to(home))
            if rel == ".claude/move-home-chat.lock" or rel.startswith("Documents/claude-chats-backup-"):
                continue
            if p.is_symlink():
                out[rel] = ("l", os.readlink(p))
            elif p.is_dir():
                out[rel] = ("d",)
            elif not p.is_file():
                out[rel] = ("o",)  # fifo: never read it, that blocks
            else:
                out[rel] = ("f", p.read_bytes(), stat.S_IMODE(p.stat().st_mode), p.stat().st_mtime)
    return out


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        self.stubs = self.tmp / "stubs"
        self.stubs.mkdir()
        (self.stubs / "pgrep").write_text(PGREP)
        (self.stubs / "pgrep").chmod(0o755)
        self.pids = self.tmp / "pids"
        self.proj = self.home / ".claude" / "projects"
        self.live, self.old, self.copy = self.proj / LIVE, self.proj / OLD, self.proj / COPY
        self.cc = self.home / "claude-config"
        self.docs = self.home / "Documents"
        self.docs.mkdir(parents=True)
        self.cc.mkdir(parents=True)
        for cmd in (["git", "init", "-q"],):
            subprocess.run(cmd, cwd=self.cc, check=True)
        put(self.cc / ".gitignore", ".claude/settings.local.json\nCLAUDE.local.md\n")
        put(self.cc / ".claude" / "keep", "")
        self.fixture()

    def fixture(self):
        put(self.live / "a.jsonl", "live-a", 1_000_000)
        put(self.live / "chat1" / "x.txt", "x")
        put(self.live / "rollover" / "r1", "r1")
        put(self.live / "memory" / "MEMORY.md", "# Index\n- [A](a.md) - alpha\n")
        put(self.live / "memory" / "a.md", "---\nname: a\n---\na")
        put(self.old / "a.jsonl", "live-a", 2_000_000)
        put(self.old / "old.jsonl", "old")
        put(self.old / "rollover" / "r2", "r2")
        put(self.old / "newdir" / "f", "nf")
        put(self.old / "memory" / "MEMORY.md", "# Index\n- [A](a.md) - alpha\n- [B](b.md) - beta\n\n- [C](c.md) - gamma  \n")
        put(self.old / "memory" / "b.md", "---\nname: b\n---\nb")
        put(self.copy / "a.jsonl", "live-a", 3_000_000)
        put(self.copy / "c.jsonl", "copy")
        put(self.copy / "memory" / "MEMORY.md", "# Index\n- [A](a.md) - alpha\n")
        put(self.home / ".claude" / ".claude" / "CLAUDE.md", "# Old title\nrule1\nrule2\n")
        put(self.home / ".claude" / ".claude" / "settings.local.json",
            json.dumps({"permissions": {"allow": ["a", "b", "c"]}, "other": 1}))

    def run_script(self, pids=None, wf=None):
        if pids:
            self.pids.write_text(pids)
        if wf:
            (self.tmp / "wf").write_text(wf)
        env = dict(os.environ, HOME=str(self.home), PATH=f"{self.stubs}:{os.environ['PATH']}",
                   STUB_PIDS=str(self.pids), STUB_WF=str(self.tmp / "wf"))
        self.assertTrue(SCRIPT.exists(), f"{SCRIPT} is missing")
        return subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=120)

    def refuses(self, **kw):
        before = snapshot(self.home)
        r = self.run_script(**kw)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(snapshot(self.home), before)
        return r

    def ok(self):
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def rules(self):
        return self.cc / "CLAUDE.local.md"

    def settings(self):
        return self.cc / ".claude" / "settings.local.json"

    def allow_src(self):
        return self.home / ".claude" / ".claude" / "settings.local.json"


class Refusals(Case):  # AC-1
    def test_busy_pid_exits_1_names_pid_changes_nothing(self):
        r = self.refuses(pids="424242\n")
        self.assertIn("424242", r.stdout + r.stderr)

    def test_running_wf_exits_1(self):
        for cmd in ("python3 /home/u/.local/bin/wf -y --repos /r\n",
                    "/usr/bin/python3 -u /home/u/.local/share/wf/e1cb/wf.py run /r -y\n"):
            with self.subTest(cmd=cmd):
                r = self.refuses(wf=cmd)
                self.assertIn("515151 (wf)", r.stderr)

    def test_other_python_is_not_wf(self):
        self.ok_with(wf="python3 /home/u/tools/wflow.py\n")

    def ok_with(self, **kw):
        r = self.run_script(**kw)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_rules_file_not_git_ignored(self):
        put(self.cc / ".gitignore", ".claude/settings.local.json\n")
        self.refuses()

    def test_old_name_is_a_link_elsewhere(self):
        shutil.rmtree(self.copy)
        self.copy.symlink_to(f"../{LIVE}")
        self.refuses()

    def test_unparseable_approvals_refused_before_anything_moves(self):
        put(self.settings(), "{not json")
        self.refuses()

    def test_source_deny_rules_refused(self):
        put(self.allow_src(), json.dumps({"permissions": {"allow": ["a"], "deny": ["x"]}}))
        self.refuses()

    def test_kept_backup_that_does_not_read_back(self):
        put(self.docs / f"claude-chats-backup-{datetime.date.today().isoformat()}.tar.gz", "garbage")
        self.refuses()

    def test_lock_held_exits_1_changes_nothing(self):
        lock = self.home / ".claude" / "move-home-chat.lock"
        with open(lock, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.refuses()

    def test_chat_clash_exits_1_changes_nothing(self):
        put(self.old / "a.jsonl", "different")
        self.refuses()

    def test_clash_between_old_and_copy(self):
        put(self.old / "same.jsonl", "one")
        put(self.copy / "same.jsonl", "two")
        self.refuses()

    def test_memory_note_clash(self):
        put(self.live / "memory" / "b.md", "other")
        self.refuses()

    def test_rules_clash(self):
        put(self.rules(), "something else\n")
        self.refuses()

    def test_settings_not_git_ignored(self):
        put(self.cc / ".gitignore", "nothing\n")
        self.refuses()

    def test_entry_neither_file_nor_folder(self):
        os.mkfifo(self.old / "fifo")
        self.refuses()


class Backup(Case):  # AC-2
    def test_archive_mode_600_and_holds_the_originals(self):
        self.ok()
        arc = self.docs / f"claude-chats-backup-{datetime.date.today().isoformat()}.tar.gz"
        self.assertEqual(stat.S_IMODE(arc.stat().st_mode), 0o600)
        with tarfile.open(arc) as t:
            names = t.getnames()
        for tail in (f"{OLD}/old.jsonl", f"{COPY}/c.jsonl", f"{LIVE}/a.jsonl",
                     ".claude/.claude/CLAUDE.md", ".claude/.claude/settings.local.json"):
            self.assertTrue(any(n.endswith(tail) for n in names), f"{tail} not in {names}")

    def test_archive_holds_the_targets_it_overwrites(self):
        put(self.settings(), json.dumps({"permissions": {"allow": ["c"]}}))
        put(self.rules(), HEAD + "\nrule1\nrule2\n")
        self.ok()
        arc = self.docs / f"claude-chats-backup-{datetime.date.today().isoformat()}.tar.gz"
        with tarfile.open(arc) as t:
            names = t.getnames()
        for tail in ("claude-config/.claude/settings.local.json", "claude-config/CLAUDE.local.md"):
            self.assertTrue(any(n.endswith(tail) for n in names), f"{tail} not in {names}")


class Chats(Case):  # AC-3
    def test_merge_skip_and_move(self):
        self.ok()
        self.assertEqual((self.live / "a.jsonl").read_text(), "live-a")
        self.assertEqual((self.live / "a.jsonl").stat().st_mtime, 1_000_000)  # identical file left alone
        for rel, text in (("old.jsonl", "old"), ("c.jsonl", "copy"), ("newdir/f", "nf"),
                          ("rollover/r1", "r1"), ("rollover/r2", "r2"), ("chat1/x.txt", "x")):
            self.assertEqual((self.live / rel).read_text(), text, rel)

    def test_memory_notes_merge(self):
        self.ok()
        self.assertEqual((self.live / "memory" / "b.md").read_text(), "---\nname: b\n---\nb")
        self.assertEqual((self.live / "memory" / "a.md").read_text(), "---\nname: a\n---\na")


class Index(Case):  # AC-4
    def test_new_lines_appended_once_under_heading(self):
        self.ok()
        lines = [x.rstrip() for x in (self.live / "memory" / "MEMORY.md").read_text().splitlines()]
        self.assertEqual(lines[:2], ["# Index", "- [A](a.md) - alpha"])
        self.assertEqual(lines.count("- [A](a.md) - alpha"), 1)
        self.assertEqual(lines.count("- [B](b.md) - beta"), 1)
        self.assertEqual(lines.count("- [C](c.md) - gamma"), 1)
        heads = [x for x in lines if x.startswith("## From ~/.claude (moved ")]
        self.assertEqual(heads, [f"## From ~/.claude (moved {datetime.date.today().isoformat()})"])
        self.assertLess(lines.index(heads[0]), lines.index("- [B](b.md) - beta"))

    def test_no_heading_when_nothing_to_append(self):
        put(self.old / "memory" / "MEMORY.md", "- [A](a.md) - alpha  \n\n")
        self.ok()
        self.assertEqual((self.live / "memory" / "MEMORY.md").read_text(), "# Index\n- [A](a.md) - alpha\n")

    def test_copy_index_that_differs_is_appended(self):
        put(self.copy / "memory" / "MEMORY.md", "# Index\n- [D](d.md) - delta\n")
        self.ok()
        text = (self.live / "memory" / "MEMORY.md").read_text()
        self.assertEqual(text.count("- [D](d.md) - delta"), 1)


class Links(Case):  # AC-5
    def test_links_then_rerun_says_already_moved(self):
        self.ok()
        for p in (self.old, self.copy):
            self.assertTrue(p.is_symlink(), p)
            self.assertEqual(os.readlink(p), str(self.live))
        for arc in self.docs.glob("claude-chats-backup-*"):
            arc.unlink()
        before = snapshot(self.home)
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("already moved", r.stdout)
        self.assertEqual(list(self.docs.glob("claude-chats-backup-*")), [])
        self.assertEqual(snapshot(self.home), before)

    def test_leftover_in_old_folder_is_kept_not_linked(self):
        shutil.rmtree(self.old / "memory")
        shutil.rmtree(self.live / "memory")
        shutil.rmtree(self.copy / "memory")
        put(self.old / "memory", "a file where a folder was")
        r = self.run_script()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual((self.old / "memory").read_text(), "a file where a folder was")
        self.assertFalse(self.old.is_symlink())


class Rules(Case):  # AC-6
    def test_written_with_new_first_line_and_source_removed(self):
        self.ok()
        self.assertEqual(self.rules().read_text(), HEAD + "\nrule1\nrule2\n")
        self.assertEqual(stat.S_IMODE(self.rules().stat().st_mode), 0o600)
        self.assertFalse((self.home / ".claude" / ".claude" / "CLAUDE.md").exists())

    def test_identical_target_is_skipped_not_a_clash(self):
        put(self.rules(), HEAD + "\nrule1\nrule2\n")
        self.ok()
        self.assertEqual(self.rules().read_text(), HEAD + "\nrule1\nrule2\n")
        self.assertFalse((self.home / ".claude" / ".claude" / "CLAUDE.md").exists())


class Approvals(Case):  # AC-7
    def test_union_keeps_order_and_other_keys(self):
        put(self.settings(), json.dumps({"permissions": {"allow": ["c", "d"], "deny": ["z"]}, "model": "m"}))
        self.ok()
        got = json.loads(self.settings().read_text())
        self.assertEqual(got["permissions"]["allow"], ["c", "d", "a", "b"])
        self.assertEqual(got["permissions"]["deny"], ["z"])
        self.assertEqual(got["model"], "m")
        self.assertNotIn("other", got)
        self.assertFalse(self.allow_src().exists())

    def test_missing_target(self):
        self.ok()
        self.assertEqual(json.loads(self.settings().read_text()), {"permissions": {"allow": ["a", "b", "c"]}})
        self.assertFalse(self.allow_src().exists())

    def test_target_without_permissions_key(self):
        put(self.settings(), json.dumps({"model": "m"}))
        self.ok()
        self.assertEqual(json.loads(self.settings().read_text()),
                         {"model": "m", "permissions": {"allow": ["a", "b", "c"]}})

    def test_unparseable_target_exits_1_and_leaves_both_files(self):
        put(self.settings(), "{not json")
        self.refuses_or_unchanged()

    def refuses_or_unchanged(self):
        src, tgt = self.allow_src().read_bytes(), self.settings().read_bytes()
        r = self.run_script()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.allow_src().read_bytes(), src)
        self.assertEqual(self.settings().read_bytes(), tgt)


if __name__ == "__main__":
    unittest.main()
