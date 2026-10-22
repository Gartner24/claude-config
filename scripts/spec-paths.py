#!/usr/bin/env python3
"""spec-paths: warn when changed files touch an accepted spec's **Paths:** globs (spec 0015 AC-6).

Run inside a repo. `--spec NNNN` (repeatable) names the specs being synced; they never warn.
Prints `warning: <file> touches accepted spec <NNNN> <title> (<glob>)` per hit, exits 0 either way.
`--files <path>...` (spec 0070 AC-4) prints `<repo relative path>\t<NNNN,NNNN or ->` per path inside the
repo: the specs whose Paths globs match it, any status. Files under `docs/` never match (spec Paths never
name docs/), except in a document repo (AGENTS.md `**Deliverable:** documents`, AC-20), where only
`docs/scope/`, `docs/specs/`, `docs/briefs/` and `docs/reviews/` never match; `.workflow/` never matches.
`--overlap NNNN NNNN` (spec 0073 AC-4) prints `overlap: <glob of first> meets <glob of second>` and exits 1 when
any pair of their Paths globs meets (fnmatch either way, or one a folder prefix of the other), `overlap: NNNN has
no Paths line` and exits 1 when one has none, else `no overlap` and exits 0; `**Paths:** none` meets nothing.
Exits: `--spec` and `--files` 0, or 1 on a git failure (`spec-paths: <error>`); `--overlap` 0 none, 1 overlap,
2 unknown spec; a bad flag exits 2. `--test` runs the self checks.
"""
import argparse
import fnmatch
import os
import re
import subprocess
import sys
import tempfile

TOP = re.compile(r"^(\d{4})-[^/]*(\.md|/index\.md)$")
STATUS = re.compile(r"^\*\*Status\*\*:\s*(.*)$", re.M)
PATHS = re.compile(r"^\*\*Paths:\*\*(.*)$", re.M)
TITLE = re.compile(r"^#\s+\d{4}\s*[.:·-]?\s*(.*)$", re.M)
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
DELIVERABLE_DOCS = re.compile(r"^\*\*Deliverable:\*\*\s*documents\b", re.M)
PLAN_DIRS = ("docs/scope/", "docs/specs/", "docs/briefs/", "docs/reviews/")
WORKTREE = re.compile(r"^\.claude/worktrees/[^/]+/")


class GitError(Exception):
    pass


def git(top, *args):
    p = subprocess.run(["git", "-C", top, *args], capture_output=True, text=True)
    if p.returncode:
        raise GitError(f"git {' '.join(args)}: {(p.stderr or p.stdout).strip()}")
    return p.stdout


def lines(out):
    return [l for l in out.split("\n") if l]


def spec_number(value):
    if not re.fullmatch(r"\d{1,4}", value):
        raise argparse.ArgumentTypeError(f"not a spec number: {value}")
    return value.zfill(4)


def top_files(top):
    """{NNNN: repo relative path} of every spec top file (a flat NNNN-*.md or NNNN-*/index.md)."""
    for base in ("docs/specs", ".workflow/specs"):
        folder = os.path.join(top, base)
        if os.path.isdir(folder):
            break
    else:
        return {}
    found = {}
    for name in sorted(os.listdir(folder)):
        rel = name + "/index.md" if os.path.isdir(os.path.join(folder, name)) else name
        m = TOP.match(rel)
        if m and os.path.isfile(os.path.join(folder, rel)):
            found.setdefault(m.group(1), f"{base}/{rel}")
    return found


def base_commit(top, specs, tops):
    """The commit the changed files are counted from (AC-6)."""
    branch = git(top, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch not in ("main", "master"):
        try:
            return git(top, "merge-base", "HEAD", "main").strip()
        except GitError:
            return git(top, "merge-base", "HEAD", "master").strip()
    added = [c for n in specs if n in tops
             for c in lines(git(top, "log", "--diff-filter=A", "--format=%H", "--", tops[n]))]
    # The oldest add across all named specs: the one with the fewest ancestors. No add found (or no --spec): HEAD's commit.
    oldest = min(added, key=lambda c: int(git(top, "rev-list", "--count", c).strip())) if added else "HEAD"
    parent = subprocess.run(["git", "-C", top, "rev-parse", "--verify", "-q", oldest + "^"],
                            capture_output=True, text=True)
    return parent.stdout.strip() if parent.returncode == 0 else EMPTY_TREE


def changed(top, specs, tops):
    base = base_commit(top, specs, tops)
    return set(lines(git(top, "diff", "--name-only", base))) | \
        set(lines(git(top, "ls-files", "-mo", "--exclude-standard", "--full-name")))


def warnings(top, specs):
    tops = top_files(top)
    files = changed(top, specs, tops)
    out = set()
    for n, rel in tops.items():
        if n in specs:
            continue
        text = open(os.path.join(top, rel), encoding="utf-8", errors="replace").read()
        status, paths = STATUS.search(text), PATHS.search(text)
        if not status or not status.group(1).startswith("Accepted") or not paths:
            continue
        globs = re.findall(r"`([^`]+)`", paths.group(1))
        title = TITLE.search(text)
        title = title.group(1).strip() if title else ""
        for f in files:
            g = next((g for g in globs if fnmatch.fnmatchcase(f, g)), None)
            if g:
                out.add(f"warning: {f} touches accepted spec {n} {title} ({g})")
    return sorted(out)


def document_repo(top):
    try:
        return bool(DELIVERABLE_DOCS.search(open(os.path.join(top, "AGENTS.md"), encoding="utf-8", errors="replace").read()))
    except OSError:
        return False


def file_specs(top, paths):
    """[(repo relative path, [NNNN, ...])] for each path inside the repo (AC-4, AC-20)."""
    docs = document_repo(top)
    specs = []
    for n, rel in sorted(top_files(top).items()):
        paths_line = PATHS.search(open(os.path.join(top, rel), encoding="utf-8", errors="replace").read())
        specs.append((n, re.findall(r"`([^`]+)`", paths_line.group(1)) if paths_line else []))
    out = []
    for p in paths:
        f = os.path.relpath(os.path.realpath(os.path.join(os.getcwd(), p)), os.path.realpath(top))
        if f == "." or f.startswith(".." + os.sep) or f == "..":
            continue
        # a nested worktree is a checkout of this repo: `.claude/worktrees/w1/src/a.py` is `src/a.py`
        f = WORKTREE.sub("", f.replace(os.sep, "/"))
        plan = f.startswith(".workflow/") or f.startswith(PLAN_DIRS if docs else ("docs/",))
        out.append((f, [] if plan else [n for n, globs in specs if any(fnmatch.fnmatchcase(f, g) for g in globs)]))
    return out


def under(path, dirs):
    """By whole path components: /a/bc is not under /a/b, and /a/b/ is /a/b (runner/run.py under)."""
    path = os.path.normpath(path)
    for d in dirs:
        d = os.path.normpath(d)
        if path == d or path.startswith(d.rstrip("/") + "/"):
            return True
    return False


def overlap(a, b):
    """The first (glob of a, glob of b) that meet, else None (runner/pr.py overlap, returning both globs)."""
    for x in a:
        for y in b:
            if fnmatch.fnmatchcase(x, y) or fnmatch.fnmatchcase(y, x) or under(x, [y]) or under(y, [x]):
                return x, y
    return None


def spec_globs(top, tops, n):
    """The globs on spec n's Paths line ([] for `none`), or None when it has no Paths line."""
    m = PATHS.search(open(os.path.join(top, tops[n]), encoding="utf-8", errors="replace").read())
    return re.findall(r"`([^`]+)`", m.group(1)) if m else None


def main(argv):
    ap = argparse.ArgumentParser(prog="spec-paths")
    ap.add_argument("--spec", action="append", type=spec_number, default=[])
    ap.add_argument("--files", nargs="+")
    ap.add_argument("--overlap", nargs=2, type=spec_number, metavar="NNNN")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args(argv)
    if a.test:
        return self_test()
    try:
        top = git(os.getcwd(), "rev-parse", "--show-toplevel").strip()
        if a.overlap:
            tops = top_files(top)
            for n in a.overlap:
                if n not in tops:
                    ap.error(f"no spec {n} in {top}")
            globs = [spec_globs(top, tops, n) for n in a.overlap]
            for n, g in zip(a.overlap, globs):
                if g is None:
                    print(f"overlap: {n} has no Paths line")
                    return 1
            hit = overlap(*globs)
            print(f"overlap: {hit[0]} meets {hit[1]}" if hit else "no overlap")
            return 1 if hit else 0
        if a.files:
            for f, ns in file_specs(top, a.files):
                print(f"{f}\t{','.join(ns) or '-'}")
            return 0
        for line in warnings(top, set(a.spec)):
            print(line)
    except GitError as e:
        print(f"spec-paths: {e}")
        return 1
    return 0


def self_test():
    failures = []

    def check(name, got, want):
        if got != want:
            failures.append(f"{name}: got {got!r}, want {want!r}")

    def sh(repo, *args):
        subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                       check=True, capture_output=True)

    def write(repo, rel, text):
        path = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def spec(n, status, paths, title="T"):
        return f"# {n}. {title}\n\n**Date**: x\n**Status**: {status}\n**Paths:** {paths}\n"

    def run(repo, *flags):
        p = subprocess.run([sys.executable, os.path.abspath(__file__), *flags], cwd=repo,
                           capture_output=True, text=True)
        return p.returncode, p.stdout.splitlines()

    hit = "warning: src/a.py touches accepted spec 0001 Src ({})"
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "r")
        os.makedirs(repo)
        sh(repo, "init", "-q", "-b", "main")
        write(repo, "docs/specs/0001-src.md", spec("0001", "Accepted", "`src/*.py`", "Src"))
        write(repo, "docs/specs/0002-lib/index.md", spec("0002", "Proposed", "`lib/**`"))
        write(repo, "docs/specs/0003-none.md", spec("0003", "Accepted", "none"))
        write(repo, "src/a.py", "a\n")
        write(repo, "lib/x.py", "x\n")
        sh(repo, "add", "-A")
        sh(repo, "commit", "-q", "-m", "init")

        sh(repo, "switch", "-q", "-c", "feat")
        write(repo, "src/a.py", "b\n")
        write(repo, "lib/x.py", "y\n")
        sh(repo, "commit", "-q", "-am", "change")
        check("branch warns once", run(repo), (0, [hit.format("src/*.py")]))
        check("--spec silences", run(repo, "--spec", "1"), (0, []))

        write(repo, "src/b.py", "new\n")
        check("untracked warns", run(repo)[1], [hit.format("src/*.py"),
                                                hit.replace("a.py", "b.py").format("src/*.py")])
        os.remove(os.path.join(repo, "src/b.py"))

        sh(repo, "switch", "-q", "main")
        sh(repo, "merge", "-q", "--ff-only", "feat")
        check("main, HEAD's commit", run(repo), (0, [hit.format("src/*.py")]))
        sh(repo, "commit", "-q", "--allow-empty", "-m", "later")
        check("main, HEAD's commit only", run(repo), (0, []))

        # On main with --spec: everything since the parent of the commit that added that spec.
        write(repo, "docs/specs/0004-new.md", spec("0004", "Accepted", "`docs/x`"))
        sh(repo, "add", "-A")
        sh(repo, "commit", "-q", "-m", "spec 4")
        write(repo, "src/a.py", "c\n")
        sh(repo, "commit", "-q", "-am", "work 1")
        sh(repo, "commit", "-q", "--allow-empty", "-m", "work 2")
        check("main, --spec 4", run(repo, "--spec", "4"), (0, [hit.format("src/*.py")]))
        check("--spec 4 equals --spec 0004", run(repo, "--spec", "0004"), run(repo, "--spec", "4"))
        write(repo, "docs/specs/0004-new.md", spec("0004", "Accepted", "`src/**`"))
        sh(repo, "commit", "-q", "-am", "spec 4 widened")
        check("own spec never warns", run(repo, "--spec", "4"), (0, [hit.format("src/*.py")]))
        # Several --spec: counted from the oldest add, so spec 5 added later does not narrow the window.
        write(repo, "docs/specs/0005-later.md", spec("0005", "Accepted", "`lib/**`"))
        sh(repo, "add", "-A")
        sh(repo, "commit", "-q", "-m", "spec 5")
        check("oldest add of several", run(repo, "--spec", "5", "--spec", "4"), (0, [hit.format("src/*.py")]))

        check("bad flag", run(repo, "--spec", "12345")[0], 2)
        check("bad flag word", run(repo, "--nope")[0], 2)

        wf = os.path.join(tmp, "w")
        os.makedirs(wf)
        sh(wf, "init", "-q", "-b", "main")
        write(wf, ".workflow/specs/0009-w.md", spec("0009", "Accepted (built in abc)", "`app/*`", "W"))
        write(wf, "app/m.js", "m\n")
        sh(wf, "add", "-A", "-f")
        sh(wf, "commit", "-q", "-m", "init")
        check(".workflow/specs", run(wf), (0, ["warning: app/m.js touches accepted spec 0009 W (app/*)"]))

        # A repo whose default branch is master: the merge base falls back to it.
        ms = os.path.join(tmp, "m")
        os.makedirs(ms)
        sh(ms, "init", "-q", "-b", "master")
        write(ms, "docs/specs/0001-src.md", spec("0001", "Accepted", "`src/*.py`", "Src"))
        write(ms, "src/a.py", "a\n")
        sh(ms, "add", "-A")
        sh(ms, "commit", "-q", "-m", "init")
        sh(ms, "switch", "-q", "-c", "feat")
        write(ms, "src/a.py", "b\n")
        sh(ms, "commit", "-q", "-am", "change")
        check("branch off master", run(ms), (0, [hit.format("src/*.py")]))

        # Spec 0070 AC-4 and AC-20: --files maps each path to the specs whose globs match it.
        fl = os.path.join(tmp, "f")
        os.makedirs(fl)
        sh(fl, "init", "-q", "-b", "main")
        write(fl, "docs/specs/0001-src.md", spec("0001", "Accepted", "`src/*.py`, `lib/**`"))
        write(fl, "docs/specs/0002-lib/index.md", spec("0002", "Proposed", "`lib/**`"))
        write(fl, "docs/specs/0003-none.md", spec("0003", "Accepted", "none"))
        write(fl, "docs/specs/0004-man.md", spec("0004", "Accepted", "`docs/manual/**`, `docs/specs/**`"))
        files = ["src/a.py", os.path.join(fl, "lib/x/y.py"), "README.md", "docs/manual/m.md",
                 "docs/specs/0003-none.md", ".workflow/scope/scope.md", os.path.join(tmp, "elsewhere.py")]
        check("--files", run(fl, "--files", *files), (0, [
            "src/a.py\t0001", "lib/x/y.py\t0001,0002", "README.md\t-", "docs/manual/m.md\t-",
            "docs/specs/0003-none.md\t-", ".workflow/scope/scope.md\t-"]))
        check("--files strips a nested worktree", run(fl, "--files", ".claude/worktrees/w1/src/a.py", ".claude/worktrees/w1/README.md")[1],
              ["src/a.py\t0001", "README.md\t-"])
        write(fl, "AGENTS.md", "# r\n\n**Deliverable:** documents\n")
        check("--files in a document repo", run(fl, "--files", "docs/manual/m.md", "docs/specs/0003-none.md", "docs/x.md")[1],
              ["docs/manual/m.md\t0004", "docs/specs/0003-none.md\t-", "docs/x.md\t-"])

        # Spec 0073 AC-4: --overlap on two specs' Paths globs.
        write(fl, "docs/specs/0005-all.md", spec("0005", "Accepted", "`**`"))
        write(fl, "docs/specs/0006-dir.md", spec("0006", "Accepted", "`bin/install.sh`, `src`"))
        write(fl, "docs/specs/0007-bare.md", "# 0007. Bare\n\n**Status**: Accepted\n")
        write(fl, "docs/specs/0008-other.md", spec("0008", "Accepted", "`bin/sync.sh`, `tests/*.py`"))
        check("--overlap glob meets glob", run(fl, "--overlap", "1", "2"), (1, ["overlap: lib/** meets lib/**"]))
        check("--overlap fnmatch the other way", run(fl, "--overlap", "5", "1"), (1, ["overlap: ** meets src/*.py"]))
        check("--overlap folder prefix", run(fl, "--overlap", "1", "6"), (1, ["overlap: src/*.py meets src"]))
        check("--overlap none meets nothing", run(fl, "--overlap", "3", "5"), (0, ["no overlap"]))
        check("--overlap apart", run(fl, "--overlap", "6", "8"), (0, ["no overlap"]))
        check("--overlap no Paths line", run(fl, "--overlap", "8", "7"), (1, ["overlap: 0007 has no Paths line"]))
        check("--overlap unknown spec", run(fl, "--overlap", "1", "99")[0], 2)
        check("--overlap needs two", run(fl, "--overlap", "1")[0], 2)

        bare = os.path.join(tmp, "nogit")
        os.makedirs(bare)
        code, out = run(bare)
        check("git failure", (code, bool(out) and out[0].startswith("spec-paths: ")), (1, True))

    for f in failures:
        print(f"FAIL {f}")
    print(f"spec-paths self checks: {'all passed' if not failures else f'{len(failures)} failed'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
