#!/usr/bin/env python3
"""issue-reread: what changed in a linked GitHub issue since its spec was written? (spec 0073 AC-8, AC-9)

`issue-reread <issue> --spec <spec top file>`, the issue as a URL or `owner/repo#n`. The since time is the spec
file's first commit (`git log --follow --diff-filter=A`, oldest; a later amendment does not move it). One
`gh api graphql` read prints, per change after that time and in time order: `title or body edited <time>`,
`comment by <login> <time>: <first 200 characters>` (bot authors left out), `closed <time>`; exit 1. Nothing
changed: `no change since <time>`, exit 0. A failed read or a spec file git does not know prints
`issue not read: <reason>` and exits 2, never `no change`. `--test` runs the self checks.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

ISSUE_URL = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+)/issues/(\d+)/?$")
ISSUE_REF = re.compile(r"^([\w.-]+)/([\w.-]+)#(\d+)$")
QUERY = ("query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){closedAt "
         "userContentEdits(first:100){nodes{editedAt}} comments(last:100){nodes{createdAt body author{__typename login}}}}}}")
TIMEOUT = 30
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f\udc80-\udcff]")


class Unread(Exception):
    pass


def flat(text):
    return CONTROL.sub("", " ".join(str(text or "").split()))


def when(iso):
    try:
        t = datetime.datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.astimezone()


def parse_issue(text):
    m = ISSUE_URL.match(text) or ISSUE_REF.match(text)
    if not m:
        raise Unread(f"not an issue URL or owner/repo#n: {flat(text)}")
    return m.group(1), m.group(2), int(m.group(3))


def spec_time(spec, run):
    """The ISO time of the spec file's first commit."""
    folder, name = os.path.split(os.path.abspath(spec))
    try:
        r = run(["git", "-C", folder, "log", "--follow", "--diff-filter=A", "--format=%cI", "--", name],
                capture_output=True, text=True, errors="replace", timeout=TIMEOUT, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Unread(f"git failed: {type(e).__name__}")
    times = r.stdout.split() if r.returncode == 0 else []
    if not times or when(times[-1]) is None:
        raise Unread(f"git does not know {flat(spec)}")
    return times[-1]


def gh_reason(text, code):
    """Why gh could not read, in a few words (runner/run.py gh_reason)."""
    t = text.casefold()
    if "auth login" in t or "not logged" in t or "authentication" in t or "bad credentials" in t:
        return "not logged in"
    if "rate limit" in t:
        return "rate limited"
    if "could not resolve to" in t or "not found" in t:
        return "issue gone or private"
    if any(w in t for w in ("connect", "network", "dial tcp", "lookup", "timeout", "tls")):
        return "network error"
    return flat(text.strip().split("\n")[0])[:100] or f"exit {code}"


def read_issue(owner, name, n, run):
    argv = ["gh", "api", "graphql", "-f", "query=" + QUERY, "-f", f"o={owner}", "-f", f"r={name}", "-F", f"n={n}"]
    try:
        r = run(argv, capture_output=True, text=True, errors="replace", timeout=TIMEOUT, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise Unread("gh timed out")
    except OSError as e:
        raise Unread(f"gh missing: {e.strerror or e}")
    if r.returncode:
        raise Unread(gh_reason(r.stderr or r.stdout, r.returncode))
    try:
        issue = json.loads(r.stdout)["data"]["repository"]["issue"]
        edits = [e["editedAt"] for e in issue["userContentEdits"]["nodes"]]
        comments = issue["comments"]["nodes"]
        closed = issue["closedAt"]
    except (ValueError, KeyError, TypeError):
        raise Unread("answer unreadable")
    return edits, comments, closed


def changes(since, edits, comments, closed):
    """[(time, line)] after since, in time order."""
    t0, out = when(since), []
    for e in edits:
        t = when(e)
        if t and t > t0:
            out.append((t, f"title or body edited {e}"))
    for c in comments:
        author = c.get("author") or {}
        login = author.get("login") or "ghost"
        t = when(c.get("createdAt"))
        # a bot by its type, or GitHub's [bot] suffix no person's login can carry
        if author.get("__typename") == "Bot" or login.endswith("[bot]") or not t or t <= t0:
            continue
        out.append((t, f"comment by {flat(login)} {c['createdAt']}: {flat(c.get('body'))[:200]}"))
    if closed and when(closed) and when(closed) > t0:
        out.append((when(closed), f"closed {closed}"))
    return [line for _, line in sorted(out, key=lambda x: x[0])]


def main(argv, run=subprocess.run):
    ap = argparse.ArgumentParser(prog="issue-reread")
    ap.add_argument("issue", nargs="?")
    ap.add_argument("--spec")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args(argv)
    if a.test:
        return self_test()
    if not a.issue or not a.spec:
        ap.error("needs <issue> and --spec <spec top file>")
    try:
        owner, name, n = parse_issue(a.issue)
        since = spec_time(a.spec, run)
        lines = changes(since, *read_issue(owner, name, n, run))
    except Unread as e:
        print(f"issue not read: {e}")
        return 2
    for line in lines:
        print(line)
    if not lines:
        print(f"no change since {since}")
    return 1 if lines else 0


def self_test():
    import contextlib
    import io
    import tempfile
    failures = []

    def check(name, got, want):
        if got != want:
            failures.append(f"{name}: got {got!r}, want {want!r}")

    def sh(repo, *args, date=None):
        env = {**os.environ, **({"GIT_COMMITTER_DATE": date, "GIT_AUTHOR_DATE": date} if date else {})}
        subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                       check=True, capture_output=True, env=env)

    calls = []

    def fake(answer=None, code=0, err=""):
        def run(argv, **kw):
            if argv[0] == "git":
                return subprocess.run(argv, **kw)
            calls.append(argv)
            return subprocess.CompletedProcess(argv, code, json.dumps(answer) if answer is not None else "", err)
        return run

    def issue(edits=(), comments=(), closed=None):
        return {"data": {"repository": {"issue": {
            "closedAt": closed, "userContentEdits": {"nodes": [{"editedAt": e} for e in edits]},
            "comments": {"nodes": [{"createdAt": t, "body": b, "author": {"__typename": k, "login": l}}
                                   for t, l, k, b in comments]}}}}}

    def go(argv, run):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(argv, run)
        return code, out.getvalue().splitlines()

    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "r")
        os.makedirs(os.path.join(repo, "docs/specs"))
        sh(repo, "init", "-q", "-b", "main")
        spec = os.path.join(repo, "docs/specs/0001-x.md")
        with open(spec, "w") as f:
            f.write("# 0001. X\n")
        sh(repo, "add", "-A")
        sh(repo, "commit", "-q", "-m", "spec", date="2026-10-01T12:00:00+00:00")
        with open(spec, "a") as f:
            f.write("amended\n")
        sh(repo, "commit", "-q", "-am", "amend", date="2026-10-05T12:00:00+00:00")
        # removed and added back: the oldest add still counts
        sh(repo, "rm", "-q", spec)
        sh(repo, "commit", "-q", "-m", "drop", date="2026-10-06T12:00:00+00:00")
        os.makedirs(os.path.dirname(spec), exist_ok=True)
        with open(spec, "w") as f:
            f.write("# 0001. X again\n")
        sh(repo, "add", "-A")
        sh(repo, "commit", "-q", "-m", "back", date="2026-10-07T12:00:00+00:00")
        since = "2026-10-01T12:00:00Z"
        check("first commit time, not the amendment", spec_time(spec, subprocess.run), since)

        # AC-8: a comment after the spec commit prints and one before does not; bots are left out
        answer = issue(edits=["2026-09-30T00:00:00Z", "2026-10-03T09:00:00Z"],
                       comments=[("2026-09-29T00:00:00Z", "old", "User", "before the spec"),
                                 ("2026-10-02T10:00:00Z", "ann", "User", "please also\n handle " + "x" * 300),
                                 ("2026-10-02T11:00:00Z", "ci", "Bot", "bot text"),
                                 ("2026-10-02T12:00:00Z", "dependabot[bot]", "User", "bot by name")],
                       closed="2026-10-04T00:00:00Z")
        code, out = go(["https://github.com/o/r/issues/7", "--spec", spec], fake(answer))
        check("changes exit 1", code, 1)
        check("change lines", out, [f"comment by ann 2026-10-02T10:00:00Z: {('please also handle ' + 'x' * 300)[:200]}",
                                    "title or body edited 2026-10-03T09:00:00Z", "closed 2026-10-04T00:00:00Z"])
        check("one read only gh call", [c[:3] for c in calls], [["gh", "api", "graphql"]])
        check("owner, repo and number passed", calls[0][-6:], ["-f", "o=o", "-f", "r=r", "-F", "n=7"])
        code, out = go(["o/r#7", "--spec", spec], fake(issue(comments=[("2026-09-29T00:00:00Z", "old", "User", "x")])))
        check("no change", (code, out), (0, [f"no change since {since}"]))

        # AC-9: a failed read or an unknown spec never says no change
        code, out = go(["o/r#7", "--spec", spec], fake(code=1, err="HTTP 401: Bad credentials"))
        check("gh fails", (code, out), (2, ["issue not read: not logged in"]))
        code, out = go(["o/r#7", "--spec", spec], fake({"data": {"repository": {"issue": None}}}))
        check("odd answer", (code, out), (2, ["issue not read: answer unreadable"]))
        loose = os.path.join(repo, "docs/specs/0002-new.md")
        with open(loose, "w") as f:
            f.write("# 0002\n")
        code, out = go(["o/r#7", "--spec", loose], fake(issue()))
        check("uncommitted spec", (code, out), (2, [f"issue not read: git does not know {loose}"]))
        code, out = go(["o/r#7", "--spec", os.path.join(tmp, "x.md")], fake(issue()))
        check("spec outside git", code, 2)
        code, out = go(["o/r/7", "--spec", spec], fake(issue()))
        check("bad issue", (code, out), (2, ["issue not read: not an issue URL or owner/repo#n: o/r/7"]))

    for f in failures:
        print(f"FAIL {f}")
    print(f"issue-reread self checks: {'all passed' if not failures else f'{len(failures)} failed'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
