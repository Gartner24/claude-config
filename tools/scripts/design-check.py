#!/usr/bin/env python3
"""design-check: does every changed frontend file have a passing design-gate report at least as new? (spec 0073
AC-5, AC-6)

`design-check [repo]` (default the current folder). The logic is the retired runner's (runner/run.py test_base,
nearest_base, frontend_changed, is_frontend, is_test_file, git_paths, report_verdict, content_time,
design_problems), copied verbatim with its own git call. Prints `design-check: ok, <n> frontend files covered` or
`design-check: no frontend files changed` and exits 0; else `<path>: <problem>` per uncovered file and exits 1.
A git command that fails prints `design-check: git failed: <error>` and exits 2, never ok. `--test` runs the
self checks.
"""
import os
import re
import subprocess
import sys

GIT_SAFE = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")
GIT_TIMEOUT = 120
CONTROL = re.compile(r"[\x00-\x1f\x80-\x9f\udc80-\udcff]")
FRONTEND_EXT = (".html", ".htm", ".css", ".scss", ".sass", ".less", ".jsx", ".tsx", ".vue", ".svelte", ".astro")
FRONTEND_SCRIPT_EXT = (".js", ".mjs", ".ts")
FRONTEND_DIRS = ("components", "pages")
FRONTEND_PREFIX = "src/ui/"
FRONTEND_SKIP_DIRS = (".design", "dist", "build", ".next", "node_modules")
TEST_DIRS = ("test", "tests", "__tests__", "spec")
TEST_NAME = re.compile(r"^test_|_test\.|\.test\.|\.spec\.")
DESIGN_VERDICT = re.compile(r"^\s*\**verdict:\**\s*(PASS WITH FINDINGS|PASS|FAIL|STOP)\s*(\(.*)?$", re.I)
DESIGN_PASS = ("PASS", "PASS WITH FINDINGS")
DESIGN_REPORT = os.path.join(".design", "audit-report.md")


def git(path, *args):
    argv = ["git", *GIT_SAFE, "-C", path, *args]
    try:
        return subprocess.run(argv, capture_output=True, text=True, errors="replace", timeout=GIT_TIMEOUT,
                              stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(argv, 124, "", f"timed out after {GIT_TIMEOUT:g} s")


def flat(text):
    return CONTROL.sub("", " ".join(str(text or "").split()))


def test_base(repo):
    """Spec 0009 AC-9: the merge base of HEAD with local main, else master, else None."""
    for b in ("main", "master"):
        r = git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{b}")
        if r and r.returncode == 0:
            m = git(repo, "merge-base", "HEAD", b)
            # Spec 0040 AC-3: a shallow clone of a branch cut from another branch shares no commit with main in its
            # depth; no base made every frontend file of the repo count (93 files parked a one component feature).
            return (m.stdout.strip() or None) if m.returncode == 0 else nearest_base(repo)
    return None


def nearest_base(repo):
    """Spec 0040 AC-3: the merge base with another branch that has the fewest commits up to HEAD, else None. HEAD's own
    branch, its namesakes on remotes, its upstream, */HEAD and any branch holding HEAD are skipped: their merge base
    would be HEAD or a commit of this branch, and committed work would go unchecked."""
    head = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    name = head.stdout.strip() if head and head.returncode == 0 else ""
    up = git(repo, "rev-parse", "--symbolic-full-name", "@{upstream}")
    up = up.stdout.strip() if up and up.returncode == 0 else ""
    refs = git(repo, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes")
    best = None
    for ref in refs.stdout.split() if refs and refs.returncode == 0 else ():
        if ref in (f"refs/heads/{name}", up) or ref.endswith("/HEAD") or \
                (name and ref.startswith("refs/remotes/") and ref.split("/", 3)[3:] == [name]):
            continue
        if git(repo, "merge-base", "--is-ancestor", "HEAD", ref).returncode == 0:
            continue
        m = git(repo, "merge-base", "HEAD", ref)
        n = m.returncode == 0 and git(repo, "rev-list", "--count", f"{m.stdout.strip()}..HEAD")
        if n and n.returncode == 0 and (best is None or int(n.stdout) < best[0]):
            best = (int(n.stdout), m.stdout.strip())
    return best and best[1]


def is_test_file(rel):
    parts = rel.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME.search(parts[-1]))


def is_frontend(rel):
    """Spec 0010 AC-2."""
    parts = rel.split("/")
    name = parts[-1]
    ext = os.path.splitext(name)[1].lower()
    if is_test_file(rel) or any(p in FRONTEND_SKIP_DIRS for p in parts[:-1]) or ".min." in name:
        return False
    return ext in FRONTEND_EXT or ext in FRONTEND_SCRIPT_EXT and (
        any(p in FRONTEND_DIRS for p in parts[:-1]) or rel.startswith(FRONTEND_PREFIX))


def git_paths(repo, *args):
    r = git(repo, *args)
    # An empty list here would let /sync run unchecked, so a git failure ends the run instead.
    if r is None or r.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {flat(r and r.stderr)}")
    return [p for p in r.stdout.split("\0") if p]


def frontend_changed(repo):
    """Spec 0010 AC-1: (base or None, frontend files changed since the merge base, sorted)."""
    base = test_base(repo)
    if base:
        # --relative: diff paths are from the git top, ls-files from the cwd; a scope repo in a subfolder of a
        # git repo used to lose every committed frontend file here (review M3).
        paths = git_paths(repo, "diff", "--relative", "--name-only", "--diff-filter=ACMR", "-z", base) + \
                git_paths(repo, "ls-files", "--others", "--exclude-standard", "-z")
    else:
        paths = git_paths(repo, "ls-files", "-co", "--exclude-standard", "-z")
    return base, sorted(p for p in set(paths) if is_frontend(p) and os.path.isfile(os.path.join(repo, p))
                        and not os.path.islink(os.path.join(repo, p)))


def report_verdict(path):
    """Spec 0010 AC-4: the last verdict line's value, upper cased, else "no verdict"."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return "no verdict"
    found = [m for m in map(DESIGN_VERDICT.match, lines) if m and "|" not in m.string]
    return " ".join(found[-1].group(1).upper().split()) if found else "no verdict"


def content_time(repo, rel):
    """The committer time (ns) of the last commit that changed rel, when the file equals HEAD's copy; else None."""
    same = git(repo, "diff", "--quiet", "HEAD", "--", rel)
    if same is None or same.returncode:
        return None
    r = git(repo, "log", "-1", "--format=%ct", "HEAD", "--", rel)
    return int(r.stdout) * 10 ** 9 if r is not None and r.returncode == 0 and r.stdout.strip() else None


def design_problems(repo, changed):
    """Spec 0010 AC-3: ({report: verdict}, [{path, problem}]) for the changed frontend files, in path order."""
    reports, problems = {}, []
    for rel in changed:
        mtime = os.stat(os.path.join(repo, rel)).st_mtime_ns
        d, candidates = os.path.dirname(rel), []
        while True:
            report = os.path.join(d, DESIGN_REPORT)
            if os.path.exists(os.path.join(repo, report)):
                if report not in reports:
                    reports[report] = report_verdict(os.path.join(repo, report))
                candidates.append(report)
            if not d:
                break
            d = os.path.dirname(d)
        passing = [r for r in candidates if reports[r] in DESIGN_PASS]
        if any(os.stat(os.path.join(repo, r)).st_mtime_ns >= mtime for r in passing):
            continue
        known = passing and content_time(repo, rel)
        if known and any(max(os.stat(os.path.join(repo, r)).st_mtime_ns, content_time(repo, r) or 0) >= known
                         for r in passing):
            # Row 81 parked "older than the file" on files a test step had backed up and restored with cp: same
            # bytes, a new date. A file equal to its last commit is as old as that commit, and so is a report
            # (one committed with the page used to lose to that commit's time).
            continue
        problem = "no report" if not candidates else "older than the file" if passing else \
            "no verdict" if reports[candidates[0]] == "no verdict" else "verdict " + reports[candidates[0]]
        problems.append({"path": rel, "problem": problem})
    return dict(sorted(reports.items())), problems


def check(repo):
    """(exit code, lines)."""
    try:
        _, changed = frontend_changed(repo)
    except RuntimeError as e:
        return 2, [f"design-check: git failed: {e}"]
    if not changed:
        return 0, ["design-check: no frontend files changed"]
    _, problems = design_problems(repo, changed)
    if problems:
        return 1, [f"{flat(p['path'])}: {p['problem']}" for p in problems]
    return 0, [f"design-check: ok, {len(changed)} frontend files covered"]


def main(argv):
    if argv == ["--test"]:
        return self_test()
    if len(argv) > 1 or argv and argv[0].startswith("-"):
        print("usage: design-check [repo] | --test", file=sys.stderr)
        return 2
    code, lines = check(os.path.abspath(argv[0] if argv else os.getcwd()))
    for line in lines:
        print(line)
    return code


def self_test():
    import tempfile
    failures = []

    def expect(name, got, want):
        if got != want:
            failures.append(f"{name}: got {got!r}, want {want!r}")

    def sh(repo, *args):
        subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                       check=True, capture_output=True)

    def write(repo, rel, text, when=None):
        path = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        if when is not None:
            os.utime(path, (when, when))

    def run(repo):
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), repo], capture_output=True, text=True)
        return p.returncode, p.stdout.splitlines()

    t = 1_700_000_000
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "r")
        os.makedirs(repo)
        sh(repo, "init", "-q", "-b", "main")
        write(repo, "README.md", "r\n")
        sh(repo, "add", "-A")
        sh(repo, "commit", "-q", "-m", "init")
        sh(repo, "switch", "-q", "-c", "feat")
        expect("nothing changed", run(repo), (0, ["design-check: no frontend files changed"]))

        expect("is_frontend", [is_frontend(p) for p in ("app/page.tsx", "src/ui/a.ts", "lib/a.ts", "pages/x.js",
                                                        "app/a.test.tsx", "dist/a.css", "a.min.css")],
               [True, True, False, True, False, False, False])

        # AC-5: a frontend file newer than a passing report fails; an older one passes
        write(repo, "web/.design/audit-report.md", "# audit\n\nverdict: PASS\n", t)
        write(repo, "web/app.css", "a{}\n", t + 100)
        write(repo, "web/old.css", "b{}\n", t - 100)
        expect("newer file fails", run(repo), (1, ["web/app.css: older than the file"]))
        write(repo, "web/.design/audit-report.md", "# audit\n\nverdict: PASS\n", t + 200)
        expect("report newer passes", run(repo), (0, ["design-check: ok, 2 frontend files covered"]))
        write(repo, "other/x.html", "<p>\n", t)
        expect("no report", run(repo), (1, ["other/x.html: no report"]))
        write(repo, "other/.design/audit-report.md", "# a\n\nverdict: FAIL (3 blockers)\n", t + 300)
        expect("failing verdict", run(repo), (1, ["other/x.html: verdict FAIL"]))
        write(repo, "other/.design/audit-report.md", "# a\n\n| verdict: PASS |\n", t + 300)
        expect("table row is no verdict", run(repo), (1, ["other/x.html: no verdict"]))
        # a parent folder's passing report covers it; the last verdict line wins
        write(repo, ".design/audit-report.md", "verdict: FAIL\n\nverdict: PASS WITH FINDINGS\n", t + 400)
        os.remove(os.path.join(repo, "other/.design/audit-report.md"))
        expect("parent report", run(repo), (0, ["design-check: ok, 3 frontend files covered"]))

        # row 81: a file equal to its last commit is as old as that commit
        sh(repo, "add", "-A")
        sh(repo, "commit", "-q", "-m", "ui")
        os.utime(os.path.join(repo, "web/app.css"), (t + 10 ** 9, t + 10 ** 9))
        expect("committed copy, new mtime", run(repo)[0], 0)
        write(repo, "web/app.css", "a{color:red}\n", t + 10 ** 9)
        expect("uncommitted edit uses mtime", run(repo), (1, ["web/app.css: older than the file"]))

        # AC-6: a git failure exits 2 and never says ok
        bare = os.path.join(tmp, "nogit")
        os.makedirs(bare)
        code, out = run(bare)
        expect("git failure", (code, len(out) == 1 and out[0].startswith("design-check: git failed: ")), (2, True))
        expect("bad flag", run("--nope")[0], 2)

    for f in failures:
        print(f"FAIL {f}")
    print(f"design-check self checks: {'all passed' if not failures else f'{len(failures)} failed'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
