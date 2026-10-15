"""Spec 0046: autonomous mode per chat, each chat drives the runner for its own repos."""
import io
import json
import os
import sys
import time
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import auto  # noqa: E402
import finish  # noqa: E402
import questions  # noqa: E402
import run  # noqa: E402
import wf  # noqa: E402
from test_auto import AutoCase  # noqa: E402
from test_parallel import ParallelCase  # noqa: E402
from test_queue import ONE, decision  # noqa: E402

OLD = "2026-10-15T00:00:00+02:00"


class ChatCase(AutoCase):
    def idle(self, folder):
        """The chat of folder has not had its bar run for an hour."""
        auto.change(lambda s: s["chats"][str(folder)].update(seen=OLD))

    def in_folder(self, folder, *words):
        os.chdir(folder)
        try:
            return self.cli(*words)
        finally:
            os.chdir(self.folder)


class TestMigration(ChatCase):
    # covers: AC-1 (a version 1 file that is on reads as one chat for its folder holding every allowed repo, seen =
    # since, and is written back as version 2 on the next change; off reads as no chats; unreadable stays off)
    def test_v1_on(self):
        Path(auto.path()).parent.mkdir(parents=True, exist_ok=True)
        Path(auto.path()).write_text(json.dumps({"on": True, "folder": str(self.folder), "since": OLD,
                                                 "started": "fp", "relayed": ["ab12"]}))
        s = auto.load()
        self.assertEqual(s["version"], 2)
        self.assertEqual(s["chats"], {str(self.folder): {"repos": [str(self.folder), str(self.other)], "since": OLD,
                                                         "seen": OLD, "started": "fp", "relayed": ["ab12"],
                                                         "suggested": True}})
        self.assertEqual(json.loads(Path(auto.path()).read_text())["on"], True)
        auto.change(lambda s: None)
        self.assertEqual(self.state()["version"], 2)
        self.assertNotIn("on", self.state())

    def test_v1_off_and_broken(self):
        Path(auto.path()).parent.mkdir(parents=True, exist_ok=True)
        Path(auto.path()).write_text(json.dumps({"on": False, "folder": str(self.folder)}))
        self.assertEqual(auto.load(), {"version": 2, "chats": {}})
        self.assertEqual(self.cli("status"), (0, "autonomous: off\n"))
        for text in ("{broken", "[]", '{"version": 2, "chats": {"/a": {"repos": "x"}}}'):
            Path(auto.path()).write_text(text)
            self.assertIsNone(auto.load(), text)
            self.assertEqual(self.cli("status"), (0, "autonomous: off\n"))


class TestOnNames(ChatCase):
    # covers: AC-2 (names match an allowed repo by its exact folder name, any case; a substring, an unknown name or
    # one matching two repos refuses the whole command with the allowed names and writes nothing; a name starting
    # with - or holding shell characters refuses)
    def test_names(self):
        a, b = self.repo("api", "work2"), self.repo("api", "work3")
        web = self.repo("Web")
        self.allow(self.folder, self.other, a, b, web)
        for words, line in ((("we",), "refused: we matches no allowed repo"),
                            (("api",), "refused: api matches more than one allowed repo"),
                            (("-y",), 'refused: "-y" is not a repo name'),
                            (("web;rm",), 'refused: "web;rm" is not a repo name'),
                            (("web$(x)",), 'refused: "web$(x)" is not a repo name')):
            code, out = self.cli("on", *words)
            self.assertEqual(code, 5, words)
            self.assertTrue(out.startswith(line), out)
            self.assertFalse(os.path.exists(auto.path()), words)
        self.assertIn("allowed: work, other, api, api, Web", self.cli("on", "we")[1])
        self.assertEqual(self.cli("on", "WEB", "other"), (0, "autonomous: on in work: work, Web, other\n"))
        self.assertEqual(self.chat()["repos"], [str(self.folder), str(web), str(self.other)])

    # covers: AC-2 (a folder in no allowed repo with no names turns on with no repos and lists the allowed names; the
    # typed hook form takes names too and refuses a bad one)
    def test_no_repo_folder_and_typed_names(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        self.assertEqual(self.on_in(plain), (0, "autonomous: on in plain: no repos\n"
                                                "allowed repos to name: work, other\n"))
        self.assertEqual(self.chat(plain)["repos"], [])
        typed = lambda text: self.cli("hook", stdin=json.dumps({"hook_event_name": "UserPromptSubmit",
                                                                "cwd": str(plain), "prompt": text}))
        with mock.patch.object(auto, "interactive", return_value=True):
            self.assertTrue(typed("/auto on other")[1].startswith("autonomous: on in plain: other\n"))
            self.assertTrue(typed("/auto on other|x")[1].startswith('refused: "other|x" is not a repo name'))
            # /auto online is no switch at all.
            typed("/auto online")
        self.assertEqual(self.chat(plain)["repos"], [str(self.other)])


class TestWorktree(ChatCase):
    # covers: AC-1, AC-2 (/auto on in a git worktree holds its main checkout, and the worktree folder is the chat key)
    def test_worktree_is_its_main(self):
        admin = self.folder / ".git" / "worktrees" / "wt"
        admin.mkdir(parents=True)
        (admin / "commondir").write_text("../..\n")
        wt = self.tmp / "wt"
        (wt / "sub").mkdir(parents=True)
        (wt / ".git").write_text(f"gitdir: {admin}\n")
        self.assertEqual(self.on_in(wt / "sub"), (0, "autonomous: on in sub: work\n"))
        self.assertEqual(self.chat(wt / "sub")["repos"], [str(self.folder)])


class TestDrive(unittest.TestCase):
    # covers: AC-3, AC-4, spec 0047 AC-3 (the session is told to ask with a multiple choice panel and take the picks,
    # to write the agreed decisions into the brief and then ask you to release, and never to turn a chat on or release)
    def test_text(self):
        d = auto.DRIVE
        self.assertIn("multiple choice panel", d)
        self.assertLess(d.index("suggested repos"), d.index("wf auto take"))
        self.assertRegex(d, r"when a repo should move to another chat, first write [^;]*brief under \"Agreed so far\", "
                            r"then ask the user to type /auto release <name> here;")
        self.assertIn("never run wf auto on or wf auto release", d)


class TestTypedRelease(ChatCase):
    def typed(self, folder, text):
        return self.cli("hook", stdin=json.dumps({"hook_event_name": "UserPromptSubmit", "cwd": str(folder),
                                                  "prompt": text}))

    # covers: spec 0047 AC-1 (/auto release typed by you drops the repos from the chat of the hook's folder, not the
    # process's; a bare one prints its usage on stdout; Claude's own claude -p typing it releases nothing)
    def test_release_typed(self):
        self.cli("on", "other")
        side = self.tmp / "side"
        side.mkdir()
        with mock.patch.object(auto, "interactive", return_value=True):
            self.assertTrue(self.typed(self.folder, "/auto release OTHER")[1].startswith("released: other\n"))
            self.assertEqual(self.chat()["repos"], [str(self.folder)])
            code, out = self.typed(self.folder, "/auto release")
            self.assertTrue(out.startswith("usage: /auto release <names>\n"), out)
            self.assertTrue(self.typed(self.folder, "/auto release nope")[1].startswith(
                "refused: nope matches no chat's repo"))
            # A folder with no chat: the hook's folder decides, so this chat keeps its repo.
            self.assertEqual(self.typed(side, "/auto release work"), (0, "refused: off\n"))
            self.assertEqual(self.chat()["repos"], [str(self.folder)])
        with mock.patch.object(auto, "interactive", return_value=False):
            self.typed(self.folder, "/auto release work")
        self.assertEqual(self.chat()["repos"], [str(self.folder)])
        with mock.patch.object(auto, "interactive", return_value=True), mock.patch.dict(os.environ, {"WF_RUN": "1"}):
            self.typed(self.folder, "/auto release work")
            self.assertEqual(self.cli("release", "work"), (5, "refused: user_only\n"))
        self.assertEqual(self.chat()["repos"], [str(self.folder)])


class TestRunningCount(ChatCase):
    # covers: spec 0047 AC-5 (a stale entry of an unlocked tree beside a running sibling tree of the same repo is not
    # counted; an entry with no tree counts by its repo's lock; an unreadable lock counts as running)
    def test_own_lock(self):
        live, stale = self.tmp / "live", self.tmp / "stale"
        act = [{"repo": str(self.folder), "tree": str(live), "feature": "1. A"},
               {"repo": str(self.folder), "tree": str(stale), "feature": "2. B"},
               {"repo": str(self.other), "feature": "1. C"}]
        lock = Path(run.state_dir()) / "locks" / (run.hashlib.sha1(str(live).encode()).hexdigest() + ".lock")
        lock.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
        run.fcntl.flock(fd, run.fcntl.LOCK_EX)
        try:
            with mock.patch("run.read_active", lambda: act):
                self.assertEqual(auto.counts({str(self.folder), str(self.other)})[0], "1 feature(s) in 1 repo(s)")
                self.assertFalse(auto.entry_running(act[2]))
                with mock.patch("run.repo_lock", side_effect=OSError("x")):
                    self.assertEqual(auto.counts({str(self.folder)})[0], "2 feature(s) in 1 repo(s)")
        finally:
            os.close(fd)
        with mock.patch("run.read_active", lambda: act):
            self.assertEqual(auto.counts({str(self.folder)})[0], "")


class TestOneOwner(ChatCase):
    # covers: AC-2, AC-4 (a repo a live chat holds is left out of another chat's /auto on and named; an idle chat's
    # repo is taken because you typed it, with that repo's open features' briefs named)
    def test_on_live_and_idle_holder(self):
        self.cli("on", "other")
        self.assertEqual(self.chat()["repos"], [str(self.folder), str(self.other)])
        side = self.tmp / "side"
        side.mkdir()
        os.chdir(side)
        self.assertEqual(self.cli("on", "other"), (0, "autonomous: on in side: no repos\n"
                                                      "left out other: held by the chat in work: ask the user to type "
                                                      "/auto release other in that chat\n"
                                                      "allowed repos to name: work, other\n"))
        self.idle(self.folder)
        scope = self.other / "docs" / "scope"
        scope.mkdir(parents=True)
        (self.other / "docs" / "briefs").mkdir()
        (self.other / "docs" / "briefs" / "b.md").write_text("## Agreed so far, do not ask again\n")
        (self.other / "docs" / "briefs" / "done.md").write_text("x\n")
        (scope / "scope.md").write_text(
            "# Plan\n\n### 1. Open\n- [ ] Build it: `/develop x`\nSource: [brief](../briefs/b.md).\n\n"
            "### 2. Shut · done\n- [x] Build it: `/develop y`\nSource: [brief](../briefs/done.md).\n")
        code, out = self.cli("on", "other")
        self.assertEqual(code, 0)
        self.assertEqual(out, "autonomous: on in side: other\nother: taken from the chat in work, idle since "
                              f"{OLD}; its briefs: docs/briefs/b.md\n")
        self.assertEqual(self.chat()["repos"], [str(self.folder)])
        self.assertEqual(self.chat(side)["repos"], [str(self.other)])

    # covers: AC-3, AC-4 (take refuses a repo another chat holds, live or idle, and says how it moves; release drops
    # it, then take adds it; take and release name each repo; with this chat's unit running they apply at the next
    # start)
    def test_take_and_release(self):
        self.cli("on")
        self.in_folder(self.other, "on")
        self.assertEqual(self.cli("take", "other"), (5, "refused: other is held by the chat in other: ask the user to "
                                                        "type /auto release other in that chat\n"))
        self.idle(self.other)
        self.assertEqual(self.cli("take", "other"), (5, "refused: other is held by the chat in other, idle: only the "
                                                        "user moves it, by typing /auto release other there or "
                                                        "/auto on other here\n"))
        self.assertEqual(self.in_folder(self.other, "release", "nope"),
                         (5, "refused: nope matches no chat's repo; chat's: other\n"))
        self.assertEqual(self.in_folder(self.other, "release", "other"), (0, "released: other\n"))
        self.assertEqual(self.chat(self.other)["repos"], [])
        self.states("active")
        self.assertEqual(self.cli("take", "other"), (0, "taken: other\napplies at the next wf auto start\n"))
        self.assertEqual(self.chat()["repos"], [str(self.folder), str(self.other)])
        self.states("inactive")
        self.assertEqual(self.cli("release", "OTHER"), (0, "released: other\n"))

    # covers: AC-3 (take refuses with this folder's chat off, a - argument, more than 6 names, a name not on the
    # allow list, and a repo whose runner lock another unit holds, its own or a feature worktree's)
    def test_take_refusals(self):
        self.assertEqual(self.cli("take", "other"), (5, "refused: off\n"))
        self.cli("on")
        self.assertEqual(self.cli("take", "--all"), (5, 'refused: "--all" is not a repo name\n'))
        self.assertEqual(self.cli("take", *["other"] * 7), (5, "refused: at most 6 repos at once\n"))
        self.assertTrue(self.cli("take", "elsewhere")[1].startswith("refused: elsewhere matches no allowed repo"))
        lock = Path(run.state_dir()) / "locks" / (run.hashlib.sha1(str(self.other).encode()).hexdigest() + ".lock")
        lock.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
        run.fcntl.flock(fd, run.fcntl.LOCK_EX)
        self.assertEqual(self.cli("take", "other"), (5, "refused: other is being built by another runner\n"))
        os.close(fd)
        tree = self.tmp / "tree"
        with mock.patch("run.read_active", lambda: [{"repo": str(self.other), "tree": str(tree)}]):
            lock = Path(run.state_dir()) / "locks" / (run.hashlib.sha1(str(tree).encode()).hexdigest() + ".lock")
            fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
            run.fcntl.flock(fd, run.fcntl.LOCK_EX)
            self.assertEqual(self.cli("take", "other"), (5, "refused: other is being built by another runner\n"))
            os.close(fd)
        self.assertEqual(self.chat()["repos"], [str(self.folder)])
        # A build step inside a wf run call can neither widen nor shrink the chat (review 2026-10-15).
        with mock.patch.dict(os.environ, {"WF_RUN": "1"}):
            self.assertEqual(self.cli("take", "other"), (5, "refused: user_only\n"))
            self.assertEqual(self.cli("release", "work"), (5, "refused: user_only\n"))
        self.assertEqual(self.chat()["repos"], [str(self.folder)])
        self.assertEqual(self.cli("take", "other"), (0, "taken: other\n"))

    # covers: a chat with no repos has no work, so wait never answers `work` for every allowed repo (review 2026-10-15)
    def test_no_repos_no_work(self):
        with mock.patch.object(finish, "covered") as covered:
            self.assertEqual(auto.fingerprint([]), "")
        covered.assert_not_called()


class TestLive(ChatCase):
    # covers: AC-4 (the bar marks the chat live at most once a minute; a chat is live for 10 minutes after)
    def test_bar_seen(self):
        self.cli("on")
        self.idle(self.folder)
        c = self.chat()
        self.assertFalse(auto.live(c))
        self.cli("bar", stdin=json.dumps({"workspace": {"current_dir": str(self.folder)}}))
        seen = self.chat()["seen"]
        self.assertNotEqual(seen, OLD)
        self.assertTrue(auto.live(self.chat()))
        self.cli("bar", stdin=json.dumps({"workspace": {"current_dir": str(self.folder)}}))
        self.assertEqual(self.chat()["seen"], seen)
        with mock.patch("time.time", lambda: auto.secs(seen) + auto.LIVE_FOR + 1):
            self.assertFalse(auto.live(self.chat()))


class TestSuggest(ChatCase):
    def hook_lines(self, folder=None):
        return [x for x in self.hook("UserPromptSubmit", folder)[1].splitlines() if x.startswith("suggested")]

    # covers: AC-3 (allowed repos held by no chat sharing a parent folder or the GitHub owner of one of the chat's
    # repos, at most 6, names that cannot be taken left out; once only)
    def test_filters_and_cap(self):
        near = [self.repo(f"n{i}") for i in range(7)]
        far = self.repo("far", "elsewhere")
        owned = self.repo("owned", "elsewhere")
        odd = self.repo("has space")
        self.allow(self.folder, self.other, owned, far, *near, odd)
        self.in_folder(self.other, "on")
        origin = {str(self.folder): ("me", "work"), str(owned): ("ME", "owned"), str(far): ("you", "far")}
        with mock.patch("run.github_origin", lambda p: origin.get(str(p))):
            self.cli("on")
            # A mid-session /auto on: the line comes with the text that says to ask and take (review 2026-10-15).
            out = self.hook("UserPromptSubmit")[1]
            self.assertIn(auto.DRIVE, out)
            self.assertEqual([x for x in out.splitlines() if x.startswith("suggested")],
                             ['suggested repos: "owned", "n0", "n1", "n2", "n3", "n4"'])
            out = self.hook("UserPromptSubmit")[1]
            self.assertNotIn("suggested", out)
            self.assertNotIn(auto.DRIVE, out)

    # covers: AC-3 (a chat with no repos gets every allowed repo held by no chat, at most 6)
    def test_no_repos(self):
        plain = self.tmp / "x" / "plain"
        plain.mkdir(parents=True)
        self.in_folder(self.other, "on")
        self.on_in(plain)
        self.assertEqual(self.hook_lines(plain), ['suggested repos: "work"'])


class TestRepos(ParallelCase):
    # covers: AC-5 (--repos limits bare wf's plan to those repos: the other repo is not held, so it is neither built
    # nor waited on; the questions screen shows only their questions)
    def test_plan_and_questions(self):
        a, b = self.make_repo("ra", ONE), self.make_repo("rb", ONE)
        self.trust(a, b)
        ka, kb = os.path.realpath(a), os.path.realpath(b)
        with mock.patch.dict(os.environ, self.env, clear=True):
            for repos, held in ((None, [ka, kb]), ([ka], [ka]), ([kb, ka], [ka, kb])):
                args = wf.build_parser()[0].parse_args(["-y", *[x for p in repos or () for x in ("--repos", p)]])
                r = run.Run(None, args)
                with redirect_stdout(io.StringIO()):
                    self.assertIsNone(r.bare_checks())
                self.assertEqual([run.key_of(h["c"]) for h in r.held], held, repos)
                for h in r.held:
                    if h["lock_fd"] is not None:
                        os.close(h["lock_fd"])
                got, _ = finish.covered(types.SimpleNamespace(target=None, repos=repos))
                self.assertEqual([c.path for c in got], held, repos)
            q = Path(run.state_dir()) / "queue.json"
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_text(json.dumps({"version": 1, "parks": [], "decisions": [
                decision(ka, "1. A", did="ab12"), decision(kb, "1. A", did="cd34")]}))
            out = io.StringIO()
            with redirect_stdout(out):
                questions.screen(True, [ka])
            self.assertIn("ab12", out.getvalue())
            self.assertNotIn("cd34", out.getvalue())
            self.assertEqual([d["id"] for d in questions.open_list()], ["ab12", "cd34"])


class TestSwapWait(unittest.TestCase):
    # covers: AC-5 (a unit that meets the setup swap lock waits for it, then goes on; outside a unit it is skipped as
    # before)
    def test_wait(self):
        polls = iter([(None, "1 t wf setup swap"), (None, "1 t wf setup swap"), (None, None)])
        calls = []

        def lock_file(path, create=True, what=None):
            calls.append(path)
            return next(polls)
        args = types.SimpleNamespace(yes=True, repos=None)
        env = {k: v for k, v in os.environ.items() if k != "WF_RUN"}
        with mock.patch.dict(os.environ, {**env, "WF_AUTO_FOLDER": "/chat"}, clear=True), \
                mock.patch.object(finish, "recover"), mock.patch("questions.screen", return_value=None), \
                mock.patch.object(finish, "covered", return_value=([types.SimpleNamespace(name="r")], None)), \
                mock.patch.object(finish, "boxes", return_value=([types.SimpleNamespace()], [])), \
                mock.patch.object(finish, "plan_steps", return_value=[types.SimpleNamespace(phase="copy")]), \
                mock.patch("run.lock_file", lock_file), mock.patch("time.sleep") as nap, \
                mock.patch.object(finish, "retakes", side_effect=run.QueueError("stop here")):
            out = io.StringIO()
            with redirect_stdout(out):
                finish.cmd_wf(args)
        self.assertIn("setup update already in progress, pid 1 since t, waiting for it", out.getvalue())
        self.assertEqual(len(calls), 3)
        self.assertEqual(nap.call_count, 2)


if __name__ == "__main__":
    unittest.main()
