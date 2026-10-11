import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WF = Path(__file__).resolve().parent.parent / "wf.py"
FIX = Path(__file__).resolve().parent / "fixtures"

spec = importlib.util.spec_from_file_location("wf", WF)
wf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wf)

FAKE_CLAUDE = '#!/bin/sh\n{ pwd; for a in "$@"; do printf "%s\\n" "$a"; done; } > "$FAKE_OUT"\n'
FAKE_TMUX = '#!/bin/sh\nfor a in "$@"; do printf "%s\\n" "$a"; done > "$FAKE_OUT"\n'
FAKE_FZF = """#!/bin/sh
first=""
while IFS= read -r l; do printf '%s\\n' "$l" >> "$FZF_IN"; [ -z "$first" ] && first="$l"; done
[ -n "$FZF_CANCEL" ] && exit 130
printf '%s\\n' "$first"
"""


def run(*args):
    return subprocess.run([sys.executable, str(WF), *args], capture_output=True, text=True)


class TestEntry(unittest.TestCase):
    def test_help_exits_zero(self):
        r = run("--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("usage: wf", r.stdout)

    def test_no_command_prints_usage_and_fails(self):
        r = run()
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage: wf", r.stderr)

    def test_unknown_command_fails(self):
        self.assertNotEqual(run("bogus").returncode, 0)


def parse(text):
    return wf.pick_next(wf.parse_text(text))


class TestParser(unittest.TestCase):
    def test_open_parent_takes_first_open_milestone_as_waiting_note(self):
        nb = parse((FIX / "dotfiles.md").read_text())
        self.assertEqual(nb.command, "/develop repo layout and linking method")
        self.assertEqual(nb.feature, "1. Repo layout and linking method")
        self.assertIn("claude-config as a submodule", nb.note)
        self.assertTrue(nb.waiting)

    def test_milestone_under_ticked_parent_runs_parent_command(self):
        nb = parse((FIX / "claude-config.md").read_text())
        self.assertEqual(nb.command, "/develop next repo command")
        self.assertEqual(nb.feature, "3. `next <repo>`")
        self.assertIn("fzf picker", nb.note)
        self.assertFalse(nb.waiting)

    def test_status_tags_comments_fences_and_deferred(self):
        text = """# Scope: x
### 1. A · done
- [ ] `/develop a`
### 2. B (existing)
- [ ] `/develop b`
### 3. C (DROPPED)
- [ ] `/develop c`
### 4. D · done · GA
- [ ] `/develop d`
## Section
- [ ] `/develop after-reset`
"""
        self.assertEqual(parse(text).command, "/develop after-reset")
        self.assertIsNone(parse(text).feature)
        text = """### 1. A (done criteria)
- [ ] `/develop a`
"""
        self.assertEqual(parse(text).command, "/develop a")
        text = """<!-- a comment
- [ ] `/develop in-comment`
-->
```
- [ ] `/develop in-fence`
```
## Deferred
- [ ] `/develop deferred`
## Next
* [X] `/develop ticked`
+ [ ] `/develop real`
"""
        self.assertEqual(parse(text).command, "/develop real")
        text = "## Deferred\n# Title\n### 1. A\n- [ ] `/develop still-deferred`\n## Next\n- [ ] `/develop real`\n"
        self.assertEqual(parse(text).command, "/develop real")

    def test_command_skips_paths_and_missing_command(self):
        self.assertEqual(parse("- [ ] fix `/etc/keyd` then `/develop x`\n").command, "/develop x")
        self.assertIsNone(parse("- [ ] call the vendor\n").command)
        self.assertIsNone(parse("### 1. A\n- [x] `/develop a`\n### 2. B\n  - [ ] indented\n").command)

    def test_tab_indented_milestone(self):
        nb = parse("- [x] `/develop p`\n\t- [ ] waits on the merge\n")
        self.assertEqual(nb.command, "/develop p")
        self.assertTrue(nb.waiting)

    def test_hub_rows(self):
        rows = wf.open_rows((FIX / "hub.md").read_text())
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0].startswith("1 | Decide"))
        self.assertTrue(rows[1].startswith("3 | File"))


class TestSessions(unittest.TestCase):
    def test_counts_claude_in_and_below_repo_only(self):
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t, "repo")
            (repo / "sub").mkdir(parents=True)
            proc = Path(t, "proc")
            for pid, comm, cmd, cwd in [
                ("1", "claude", b"claude\0", repo),
                ("2", "claude", b"claude\0-c\0", repo / "sub"),
                ("3", "claude", b"claude\0--chrome-native-host\0", repo),
                ("4", "zsh", b"zsh\0", repo),
                ("5", "claude", b"claude\0", Path(t)),
            ]:
                d = proc / pid
                d.mkdir(parents=True)
                (d / "comm").write_text(comm + "\n")
                (d / "cmdline").write_bytes(cmd)
                os.symlink(cwd, d / "cwd")
            (proc / "self").mkdir()
            self.assertEqual(wf.open_sessions(str(repo.resolve()), str(proc)), 2)


class CliCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.root = self.tmp / "root"
        self.root.mkdir()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.out = self.tmp / "out"
        self.fzf_in = self.tmp / "fzf_in"
        self.fake("claude", FAKE_CLAUDE)
        self.env = {
            "HOME": str(self.tmp),
            "WF_ROOTS": str(self.root),
            "PATH": f"{self.bin}:/usr/bin:/bin",
            "FAKE_OUT": str(self.out),
            "FZF_IN": str(self.fzf_in),
        }

    def fake(self, name, body):
        p = self.bin / name
        p.write_text(body)
        p.chmod(0o755)

    def repo(self, rel, fixture, base="docs/scope", fname="scope.md"):
        d = self.root / rel / base
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIX / fixture, d / fname)
        return self.root / rel

    def wf(self, *args, tty=False, stdin="", cwd=None, prog=WF, **env):
        e = {**self.env, **env}
        cmd = [sys.executable, str(prog), *args]
        if not tty:
            return subprocess.run(cmd, input=stdin, capture_output=True, text=True, env=e, cwd=cwd)
        master, slave = os.openpty()
        p = subprocess.Popen(cmd, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=e, cwd=cwd)
        os.close(slave)
        os.write(master, stdin.encode())
        out, err = p.communicate(timeout=20)
        os.close(master)
        return subprocess.CompletedProcess(cmd, p.returncode, out, err)

    def launched(self):
        return self.out.read_text().splitlines() if self.out.exists() else None


class TestNext(CliCase):
    def test_happy_path_execs_claude_in_repo(self):
        repo = self.repo("dotfiles", "dotfiles.md")
        r = self.wf("next", "dotfiles", "-y", tty=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("waiting: claude-config as a submodule", r.stdout)
        self.assertIn("no git", r.stdout)
        self.assertEqual(self.launched(), [str(repo), "/develop repo layout and linking method"])

    def test_no_command_box_exits_3_even_with_y(self):
        d = self.root / "x" / "docs" / "scope"
        d.mkdir(parents=True)
        (d / "scope.md").write_text("# Scope: x\n- [ ] call the vendor\n")
        r = self.wf("next", "x", "-y", tty=True)
        self.assertEqual(r.returncode, 3)
        self.assertIn("no command in this box, run it yourself", r.stdout)
        self.assertIsNone(self.launched())

    def test_index_epics_in_link_order_with_missing_warning(self):
        d = self.root / "big" / "docs" / "scope"
        d.mkdir(parents=True)
        (d / "index.md").write_text(
            "# Scope: big\n- [ ] `/develop ignored`\n"
            "[out](../out.md) [one](one.md) [web](https://x.test/a.md) [gone](gone.md) [two](two.md#top)\n")
        (d / "one.md").write_text("### 1. One · done\n- [ ] `/develop one`\n")
        (d / "two.md").write_text("### 2. Two\n- [ ] `/develop two`\n")
        (self.root / "big" / "docs" / "out.md").write_text("- [ ] `/develop out`\n")
        r = self.wf("next", "big", "-y")
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertEqual(r.stdout.count("missing epic file gone.md"), 1)
        self.assertIn("cd ", r.stdout)
        self.assertTrue(r.stdout.rstrip().endswith("claude '/develop two'"))

    def test_hub_and_brownfield_have_nothing_to_run(self):
        self.repo("projects", "hub.md")
        d = self.root / "old" / "docs" / "scope"
        d.mkdir(parents=True)
        (d / "scope.md").write_text("# Scope: old\n### A. Thing (existing)\n- [ ] `/develop thing`\n")
        r = self.wf("next", "personal")
        self.assertEqual(r.returncode, 0)
        self.assertIn("nothing to run in projects", r.stdout)
        self.assertIn("1 | Decide the plugin", r.stdout)
        self.assertNotIn("Finish the workflow", r.stdout)
        r = self.wf("next", "old", "-y", tty=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("nothing to run in old", r.stdout)
        self.assertIsNone(self.launched())

    def test_discovery_depth_and_symlink_dedupe(self):
        self.repo("a/b/three", "team.md")
        self.repo("a/b/c/four", "team.md")
        self.repo("two", "team.md")
        os.symlink(self.root / "two", self.root / "alias")
        hidden = self.repo(".hidden/x", "team.md")
        names = [l.split("\t")[0] for l in self.wf("next", "--list").stdout.splitlines()]
        self.assertEqual(names, ["three", "two"])
        self.assertTrue(hidden.exists())

    def test_path_argument_outside_roots(self):
        d = self.tmp / "elsewhere" / "docs" / "scope"
        d.mkdir(parents=True)
        shutil.copy(FIX / "team.md", d / "scope.md")
        r = self.wf("next", str(self.tmp / "elsewhere"))
        self.assertEqual(r.returncode, 130)
        self.assertIn("/develop return 401", r.stdout)

    def test_exact_name_beats_substring_and_no_match(self):
        self.repo("work", "team.md")
        self.repo("workflow-automation", "dotfiles.md")
        r = self.wf("next", "WORK")
        self.assertIn("/develop return 401", r.stdout)
        r = self.wf("next", "zzz")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no scope matches 'zzz'", r.stderr)

    def test_several_matches_go_to_fzf_and_cancel_exits_0(self):
        self.fake("fzf", FAKE_FZF)
        self.repo("api-one", "team.md")
        self.repo("api-two", "dotfiles.md")
        r = self.wf("next", "api", FZF_CANCEL="1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(len(self.fzf_in.read_text().splitlines()), 2)
        r = self.wf("next", "api")
        self.assertEqual(r.returncode, 130)
        self.assertIn("api-one", r.stdout)

    def test_no_argument_uses_cwd_repo(self):
        repo = self.repo("dotfiles", "dotfiles.md")
        (repo / "deep").mkdir()
        r = self.wf("next", "-y", cwd=repo / "deep")
        self.assertEqual(r.returncode, 4)
        self.assertIn(f"cd {repo} && claude", r.stdout)

    def test_no_argument_below_hub_opens_picker_over_all(self):
        self.fake("fzf", FAKE_FZF)
        hub = self.repo("projects", "hub.md")
        self.repo("projects/dotfiles", "dotfiles.md")
        (hub / "plain").mkdir()
        r = self.wf("next", cwd=hub / "plain", FZF_CANCEL="1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(len(self.fzf_in.read_text().splitlines()), 2)

    def test_confirm_line_inputs(self):
        repo = self.repo("dotfiles", "dotfiles.md")
        self.assertEqual(self.wf("next", "dotfiles", tty=True, stdin="n\n").returncode, 130)
        self.assertEqual(self.wf("next", "dotfiles", tty=True, stdin="\x04").returncode, 130)
        self.assertIsNone(self.launched())
        r = self.wf("next", "dotfiles", tty=True, stdin="\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.launched()[0], str(repo))

    def test_both_bases_docs_wins(self):
        self.repo("both", "dotfiles.md")
        self.repo("both", "team.md", base=".workflow/scope")
        r = self.wf("next", "both")
        self.assertIn("/develop repo layout", r.stdout)
        self.assertIn("warning: both docs/scope and .workflow/scope exist", r.stdout)

    def test_workflow_base_alone(self):
        self.repo("team", "team.md", base=".workflow/scope")
        self.assertIn("/develop return 401", self.wf("next", "team").stdout)

    def test_worktrees_listed_with_labels(self):
        main = self.repo("main", "team.md")
        git = lambda *a: subprocess.run(["git", "-C", str(main), *a], check=True, capture_output=True,
                                        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
        git("init", "-q", "-b", "main")
        git("add", ".")
        git("commit", "-qm", "init")
        git("worktree", "add", "-q", str(self.tmp / "wt-branch"), "-b", "feat/x")
        git("worktree", "add", "-q", "--detach", str(self.tmp / "wt-detached"))
        lines = [l.split("\t") for l in self.wf("next", "--list").stdout.splitlines()]
        got = sorted((l[0], l[1], l[4]) for l in lines)
        self.assertEqual(got[0], ("main", "", "main"))
        self.assertEqual(got[1], ("wt-branch", "worktree feat/x", "feat/x"))
        self.assertEqual(got[2][:2], ("wt-detached", "worktree (detached)"))
        self.assertTrue(got[2][2].startswith("detached "))

    def test_list_sorted_and_usage_errors(self):
        self.repo("zeta", "team.md")
        self.repo("alpha", "dotfiles.md")
        self.repo("projects", "hub.md")
        r = self.wf("next", "--list")
        self.assertEqual(r.returncode, 0)
        lines = [l.split("\t") for l in r.stdout.splitlines()]
        self.assertEqual([l[0] for l in lines], ["alpha", "projects", "zeta"])
        self.assertEqual(len(lines[0]), 6)
        self.assertEqual(lines[1][3], "nothing to run")
        self.assertEqual(self.wf("next", "--list", "x").returncode, 2)
        self.assertEqual(self.wf("next", "--list", "-y").returncode, 2)

    def test_next_shortcut_equals_wf_next(self):
        self.repo("dotfiles", "dotfiles.md")
        link = self.bin / "next"
        os.symlink(WF, link)
        self.assertEqual(self.wf("--list", prog=link).stdout, self.wf("next", "--list").stdout)

    def test_missing_claude_fzf_and_git(self):
        self.repo("api-one", "team.md")
        self.repo("api-two", "team.md")
        (self.bin / "claude").unlink()
        r = self.wf("next", "api-one", PATH=str(self.bin))
        self.assertEqual(r.returncode, 1)
        self.assertIn("claude not found", r.stderr)
        self.assertNotIn("|", r.stdout)
        r = self.wf("next", "api", PATH=str(self.bin))
        self.assertEqual(r.returncode, 1)
        self.assertIn("fzf not found", r.stderr)
        self.fake("claude", FAKE_CLAUDE)
        r = self.wf("next", "api-one", PATH=str(self.bin))
        self.assertIn("| no git | - |", r.stdout)

    def test_launch_modes(self):
        repo = self.repo("dotfiles", "dotfiles.md")
        self.fake("tmux", FAKE_TMUX)
        r = self.wf("next", "dotfiles", "-y", TMUX="/tmp/fake,1,0")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("opened tmux window dotfiles", r.stdout)
        self.assertEqual(self.launched(), ["new-window", "-c", str(repo), "-n", "dotfiles", "claude",
                                           "/develop repo layout and linking method"])
        self.out.unlink()
        r = self.wf("next", "dotfiles", "-y")
        self.assertEqual(r.returncode, 4)
        self.assertIn(f"cd {repo} && claude '/develop repo layout and linking method'", r.stdout)
        r = self.wf("next", "dotfiles", stdin="\n", TMUX="/tmp/fake,1,0")
        self.assertEqual(r.returncode, 130)
        self.assertIsNone(self.launched())

    # covers: AC-1 (default roots: direct children of ~, and ~/projects plus three levels)
    def test_default_roots_without_wf_roots(self):
        home = self.tmp
        for rel, fixture in [("alpha", "team.md"), ("alpha/inner", "team.md"), ("projects", "hub.md"),
                             ("projects/x/y/deep3", "team.md"), ("projects/x/y/z/deep4", "team.md"),
                             ("projects/node_modules/pkg", "team.md"), (".hidden", "team.md")]:
            d = home / rel / "docs" / "scope"
            d.mkdir(parents=True)
            shutil.copy(FIX / fixture, d / "scope.md")
        r = self.wf("next", "--list", WF_ROOTS="")
        self.assertEqual([l.split("\t")[0] for l in r.stdout.splitlines()], ["alpha", "deep3", "projects"])

    # covers: AC-1 (WF_ROOTS is a colon separated list)
    def test_several_wf_roots(self):
        other = self.tmp / "other"
        d = other / "beta" / "docs" / "scope"
        d.mkdir(parents=True)
        shutil.copy(FIX / "team.md", d / "scope.md")
        self.repo("alpha", "team.md")
        r = self.wf("next", "--list", WF_ROOTS=f"{self.root}:{other}")
        self.assertEqual([l.split("\t")[0] for l in r.stdout.splitlines()], ["alpha", "beta"])

    # covers: AC-3 (one substring match, by folder name or by title, is used directly)
    def test_single_substring_match_needs_no_picker(self):
        self.repo("workflow-automation", "team.md")
        for name in ("flow", "BACKEND"):
            r = self.wf("next", name, PATH=str(self.bin))
            self.assertEqual(r.returncode, 130, r.stderr)
            self.assertIn("workflow-automation |", r.stdout)

    # covers: AC-3 (`next .` is a path)
    def test_dot_is_a_path(self):
        repo = self.repo("team", "team.md")
        r = self.wf("next", ".", "-y", cwd=repo)
        self.assertEqual(r.returncode, 4)
        self.assertIn(f"cd {repo} && claude '/develop return 401 for a rejected token'", r.stdout)

    # covers: AC-8 (branch, change count and detached state on the confirm line)
    def test_confirm_line_shows_git_state(self):
        repo = self.repo("team", "team.md")
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True,
                                        text=True, env=env).stdout.strip()
        git("init", "-q", "-b", "trunk")
        r = self.wf("next", "team")
        self.assertIn("team | no commits | 1 changes | 1. Return 401 for a rejected token |", r.stdout)
        git("add", ".")
        git("commit", "-qm", "init")
        (repo / "a.txt").write_text("a")
        (repo / "b.txt").write_text("b")
        self.assertIn("team | trunk | 2 changes |", self.wf("next", "team").stdout)
        git("checkout", "-q", "--detach")
        sha = git("rev-parse", "--short", "HEAD")
        self.assertIn(f"team | detached {sha} | 2 changes |", self.wf("next", "team").stdout)

    # covers: AC-12, AC-14 (--list needs neither fzf nor git, and shows boxes without a command)
    def test_list_without_fzf_or_git_and_no_command_column(self):
        d = self.root / "manual" / "docs" / "scope"
        d.mkdir(parents=True)
        (d / "scope.md").write_text("# Scope: manual\n### 1. Call\n- [ ] call the vendor\n")
        r = self.wf("next", "--list", PATH=str(self.bin))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "manual\t\t1. Call\tno command\tno git\t-\n")

    # covers: AC-9, AC-16 and the key invariant: scope text never reaches a shell
    def test_command_with_shell_characters_stays_one_argument(self):
        d = self.root / "evil" / "docs" / "scope"
        d.mkdir(parents=True)
        (d / "scope.md").write_text("# Scope: evil\n- [ ] `/develop x; touch PWNED $(touch PWNED2)` \n")
        cmd = "/develop x; touch PWNED $(touch PWNED2)"
        r = self.wf("next", "evil", "-y", tty=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.launched(), [str(self.root / "evil"), cmd])
        r = self.wf("next", "evil", "-y")
        self.assertEqual(r.returncode, 4)
        self.assertIn(f"claude '{cmd}'", r.stdout)
        self.assertEqual(list(self.root.rglob("PWNED*")) + list(self.tmp.glob("PWNED*")), [])

    # covers: AC-16 (a failing tmux passes its exit code back)
    def test_tmux_failure_exit_code_is_returned(self):
        self.repo("dotfiles", "dotfiles.md")
        self.fake("tmux", "#!/bin/sh\nexit 3\n")
        r = self.wf("next", "dotfiles", "-y", TMUX="/tmp/fake,1,0")
        self.assertEqual(r.returncode, 3)
        self.assertNotIn("opened tmux window", r.stdout)

    def test_missing_tmux(self):
        self.repo("dotfiles", "dotfiles.md")
        r = self.wf("next", "dotfiles", "-y", PATH=str(self.bin), TMUX="/tmp/fake,1,0")
        self.assertEqual(r.returncode, 1)
        self.assertIn("tmux not found", r.stderr)
        self.assertIsNone(self.launched())


def header(*lines, body="### 1. A\n- [ ] `/develop a`\n"):
    return wf.header_warnings("# Scope: x\n\n" + "".join(l + "\n" for l in lines) + "\n" + body)


UNKNOWN_AUTO = "unknown Autopilot value '{}', using off"


class TestHeaderContract(unittest.TestCase):
    # covers: AC-1 (first token, ends stripped, lowercased, exact compare)
    def test_valid_values_give_no_warning(self):
        self.assertEqual(header("**Autopilot:** Allowed (client signed off)", "**Source of truth:** ISSUES."), [])
        self.assertEqual(header("**autopilot:** **allowed**", "**SOURCE OF TRUTH:** mixed"), [])
        self.assertEqual(header("**Autopilot:** off", "**Source of truth:** scope"), [])

    # covers: AC-1 (never reads as allowed: suffixes, empty, colon outside the bold, indented)
    def test_malformed_values(self):
        self.assertEqual(header("**Autopilot:** allowed-ish"), [UNKNOWN_AUTO.format("allowed-ish")])
        self.assertEqual(header("**Autopilot:**"), [UNKNOWN_AUTO.format("")])
        self.assertEqual(header("**Autopilot:**   "), [UNKNOWN_AUTO.format("")])
        self.assertEqual(header("**Autopilot**: on"), [])
        self.assertEqual(header(" **Autopilot:** on"), [])

    # covers: AC-1 (comments and fences are removed before reading the header)
    def test_comments_and_fences_ignored(self):
        self.assertEqual(header("<!-- **Autopilot:** on -->", "```", "**Autopilot:** on", "```"), [])
        self.assertEqual(header("<!--", "**Autopilot:** on", "-->", "**Autopilot:** off"), [])

    # covers: AC-1 (header ends at the first level 2 or 3 heading or box line)
    def test_header_ends_at_heading_or_box(self):
        self.assertEqual(header(body="### 1. A\n**Autopilot:** on\n- [ ] `/develop a`\n"), [])
        self.assertEqual(header(body="## Section\n**Autopilot:** on\n"), [])
        self.assertEqual(header(body="- [ ] `/develop a`\n**Autopilot:** on\n"), [])
        self.assertEqual(header(body="#### Note\n**Autopilot:** on\n"), [UNKNOWN_AUTO.format("on")])

    # covers: AC-2 (missing means defaults; first line wins; one warning per problem)
    def test_defaults_and_duplicates(self):
        self.assertEqual(header(), [])
        self.assertEqual(header("**Autopilot:** on"), [UNKNOWN_AUTO.format("on")])
        self.assertEqual(header("**Autopilot:** on", "**Autopilot:** allowed"),
                         [UNKNOWN_AUTO.format("on"), "Autopilot set twice, using the first"])
        self.assertEqual(header("**Source of truth:** github", "**Source of truth:** scope", "**Source of truth:** scope"),
                         ["unknown Source of truth value 'github', using scope",
                          "Source of truth set twice, using the first"])

    # covers: AC-5 (whole segment only) and AC-7 (ticked skipped boxes are done), next box unchanged
    def test_auto_tag_and_skipped_boxes(self):
        text = (FIX / "contract.md").read_text()
        self.assertEqual(wf.header_warnings(text), [])
        nb = parse(text)
        self.assertEqual(nb.feature, "4. Headless step loop")
        self.assertEqual(nb.command, "/develop headless step loop")
        self.assertEqual(nb.note, "Budget caps (AC-4)")
        without = parse(text.replace(" · auto", ""))
        self.assertEqual((nb.feature, nb.command, nb.note), (without.feature, without.command, without.note))
        self.assertTrue(wf.AUTO_TAG.search("4. Loop · in-progress · AUTO "))
        self.assertTrue(wf.AUTO_TAG.search("4. Loop · auto · GA"))
        self.assertFalse(wf.AUTO_TAG.search("4. Loop · auto-merge"))
        self.assertFalse(wf.AUTO_TAG.search("4. Autopilot offer"))


def scope(folder, text):
    d = folder / "docs" / "scope"
    d.mkdir(parents=True)
    (d / "scope.md").write_text(text)
    return folder


class TestHostileFolders(CliCase):
    def assert_no_control(self, text):
        bad = sorted({hex(ord(ch)) for ch in text if ch not in "\t\n" and wf.CONTROL.match(ch)})
        self.assertEqual(bad, [], repr(text))

    # tmux expands #{...} in -c and -n; a folder name must reach it as literal text
    def test_tmux_escapes_hash(self):
        repo = scope(self.root / "a#{pane_pid}", "# Scope: a\n- [ ] `/develop x`\n")
        self.fake("tmux", FAKE_TMUX)
        r = self.wf("next", str(repo), "-y", TMUX="/tmp/fake,1,0")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.launched()[:5], ["new-window", "-c", str(self.root / "a##{pane_pid}"),
                                               "-n", "a##{pane_pid}"])

    # a planted core.fsmonitor used to run on `git status` for every scanned repo
    def test_git_never_runs_repo_fsmonitor_or_hooks(self):
        repo = scope(self.root / "planted", "# Scope: p\n- [ ] `/develop x`\n")
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env)
        git("init", "-q", "-b", "main")
        git("add", ".")
        git("commit", "-qm", "init")
        marker = self.tmp / "PWNED"
        hook = self.tmp / "monitor.sh"
        hook.write_text(f"#!/bin/sh\ntouch {marker}\n")
        hook.chmod(0o755)
        git("config", "core.fsmonitor", str(hook))
        self.wf("next", "--list")
        self.wf("next", "planted")
        self.assertFalse(marker.exists())
        self.fake("git", '#!/bin/sh\nprintf "%s " "$@" >> "$FAKE_OUT"; echo >> "$FAKE_OUT"; exit 1\n')
        self.wf("next", "--list")
        self.wf("next", "planted")
        calls = self.out.read_text().splitlines()
        self.assertTrue(calls)
        for call in calls:
            self.assertTrue(call.startswith("-c core.fsmonitor=false -c core.hooksPath=/dev/null -C "), call)

    def test_control_characters_never_reach_terminal_or_fzf(self):
        self.fake("fzf", FAKE_FZF)
        scope(self.root / "evil\x1b]0;x\x07",
              "# Scope: t\u009bitle\n### 1. F\x1b[2J\n- [x] `/develop f\x1b[31m`\n  - [ ] note \x1b[31mred\x00\n")
        scope(self.root / "hub", "# Scope: h\n## At a glance\n| # | Work | Status |\n|---|---|---|\n"
                                 "| 1 | bad\x1b[2J | planned |\n")
        manual = scope(self.root / "manual", "# Scope: m\n- [ ] call \x1b[2Jthe vendor\n")
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        git = lambda *a: subprocess.run(["git", "-C", str(manual), *a], check=True, capture_output=True, env=env)
        git("init", "-q", "-b", "m\u009b2J")
        git("add", ".")
        git("commit", "-qm", "init")
        git("worktree", "add", "-q", str(self.root / "wt"), "-b", "w\u009b2J")
        outs = [self.wf("next", "--list").stdout,
                self.wf("next", "evil", "-y").stdout,
                self.wf("next", "evil").stdout,
                self.wf("next", "hub").stdout,
                self.wf("next", "manual").stdout]
        self.wf("next", cwd=self.tmp, FZF_CANCEL="1")
        outs.append(self.fzf_in.read_text())
        for out in outs:
            self.assert_no_control(out)
        self.assertIn("evil]0;x | no git | - | 1. F[2J | /develop f[31m | note: note [31mred", outs[2])
        self.assertIn("bad[2J", outs[3])
        self.assertIn("call [2Jthe vendor", outs[4])

    # git status runs a repo's own filter drivers; --list and the picker used to run it in every scanned repo
    def test_list_and_picker_never_run_git_status(self):
        self.fake("fzf", FAKE_FZF)
        repo = scope(self.root / "planted", "# Scope: p\n- [ ] `/develop x`\n")
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env)
        git("init", "-q", "-b", "main")
        (repo / ".gitattributes").write_text("* filter=evil\n")
        git("add", ".")
        git("commit", "-qm", "init")
        marker = self.tmp / "PWNED"
        git("config", "filter.evil.clean", f"touch {marker}; cat")
        os.utime(repo / "docs" / "scope" / "scope.md", (0, 0))
        r = self.wf("next", "--list")
        self.assertEqual(r.stdout, "planted\t\t\t/develop x\tmain\t-\n")
        self.wf("next", cwd=self.tmp, FZF_CANCEL="1")
        self.assertIn("\tmain\t-\n", self.fzf_in.read_text())
        self.assertFalse(marker.exists())
        self.assertIn("planted | main | 0 changes |", self.wf("next", "planted").stdout)

    def test_undecodable_folder_and_branch_names(self):
        self.assertEqual(wf.clean("a\udc80b\udcff\x1bc"), "abc")
        env = {**self.env, "LC_ALL": "C.UTF-8"}
        folder = os.fsencode(self.root) + b"/bad\xff"
        os.mkdir(folder)
        scope(Path(os.fsdecode(folder)), "# Scope: b\n- [ ] `/develop b`\n")
        r = subprocess.run([sys.executable, str(WF), "next", "--list"], capture_output=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.decode(), "bad\t\t\t/develop b\tno git\t-\n")
        repo = scope(self.root / "branchy", "# Scope: g\n- [ ] `/develop g`\n")
        subprocess.run([b"git", b"-C", os.fsencode(repo), b"init", b"-q", b"-b", b"m\xff"], check=True)
        r = subprocess.run([sys.executable, str(WF), "next", "branchy"], capture_output=True, env=env)
        self.assertEqual(r.returncode, 130, r.stderr)
        self.assertIn("branchy | no commits |", r.stdout.decode())
        r = subprocess.run([sys.executable, str(WF), "next", "--list"], capture_output=True, env=env)
        self.assertIn("branchy\t\t\t/develop g\tm\ufffd\t-\n", r.stdout.decode())

    # a scope planted above $HOME (/tmp, /home) is never picked by the parent walk
    def test_parent_walk_stops_at_home(self):
        self.fake("fzf", FAKE_FZF)
        home = self.tmp / "home"
        (home / "sub").mkdir(parents=True)
        scope(self.tmp, "# Scope: planted\n- [ ] `/develop planted`\n")
        r = self.wf("next", "-y", cwd=home / "sub", HOME=str(home), FZF_CANCEL="1")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("planted", r.stdout)
        (self.tmp / "out" / "sub").mkdir(parents=True)
        scope(self.tmp / "out", "# Scope: out\n- [ ] `/develop out`\n")
        r = self.wf("next", "-y", cwd=self.tmp / "out" / "sub", HOME=str(home), FZF_CANCEL="1")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("/develop out", r.stdout)
        scope(home, "# Scope: mine\n- [ ] `/develop mine`\n")
        r = self.wf("next", "-y", cwd=home / "sub", HOME=str(home))
        self.assertIn(f"cd {home} && claude '/develop mine'", r.stdout)


class TestHeaderWarnings(CliCase):
    # covers: AC-3 (warning on the confirm line and both early paths; --list unchanged)
    def test_warning_on_every_path(self):
        scope(self.root / "run", "# Scope: r\n**Autopilot:** on\n- [ ] `/develop r`\n")
        scope(self.root / "empty", "# Scope: e\n**Autopilot:** on\n- [x] `/develop e`\n")
        scope(self.root / "manual", "# Scope: m\n**Autopilot:** on\n- [ ] call the vendor\n")
        r = self.wf("next", "run")
        self.assertIn("| /develop r | warning: unknown Autopilot value 'on', using off", r.stdout)
        r = self.wf("next", "empty")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "nothing to run in empty\nwarning: unknown Autopilot value 'on', using off\n")
        r = self.wf("next", "manual", "-y", tty=True)
        self.assertEqual(r.returncode, 3)
        self.assertTrue(r.stdout.endswith("call the vendor\nwarning: unknown Autopilot value 'on', using off\n"))
        self.assertEqual(self.wf("next", "--list").stdout,
                         "empty\t\t\tnothing to run\tno git\t-\n"
                         "manual\t\t\tno command\tno git\t-\n"
                         "run\t\t\t/develop r\tno git\t-\n")

    # covers: AC-3 (hubs are skipped)
    def test_hub_header_not_checked(self):
        hub = self.repo("projects", "hub.md")
        f = hub / "docs" / "scope" / "scope.md"
        f.write_text(f.read_text().replace("\n", "\n**Autopilot:** on\n", 1))
        r = self.wf("next", "projects")
        self.assertIn("nothing to run in projects", r.stdout)
        self.assertNotIn("warning", r.stdout)

    # covers: AC-1 (an epic split reads its header from index.md only)
    def test_epic_split_reads_index_only(self):
        d = self.root / "big" / "docs" / "scope"
        d.mkdir(parents=True)
        (d / "index.md").write_text("# Scope: big\n**Autopilot:** maybe\n\n[one](one.md)\n")
        (d / "one.md").write_text("**Source of truth:** github\n### 1. One\n- [ ] `/develop one`\n")
        r = self.wf("next", "big")
        self.assertIn("warning: unknown Autopilot value 'maybe', using off", r.stdout)
        self.assertNotIn("Source of truth", r.stdout)


if __name__ == "__main__":
    unittest.main()
