#!/usr/bin/env python3
"""Keeps private names (work orgs, clients, private tools) out of this public repo (spec 0013).

The names live in $CLAUDE_LIVE_DIR/private/names.txt (default ~/.claude/private/names.txt),
one per line, optionally `name==>replacement`. Matching is literal, case insensitive, as a
substring. Every hit prints `<where>:<line>: names.txt line <N>` and never the name itself,
so a session reading the output cannot copy a name onward into a commit, memory or doc.

  check [paths...]                      files or folders, default every file
                                        `git ls-files -co --exclude-standard` lists
  check-staged                          staged blobs and path names (the pre-commit hook)
  check-msg <file>                      one commit message (the commit-msg hook)
  check-history                         every object, path, message and ref name in the repo
  check-range <from> <to>               the commits in from..to about to be pushed: messages, author and
                                        committer names and emails, added or changed blobs, path names, and
                                        <to> as the branch name (spec 0026 AC-6)
  filter-expr <out>                     case insensitive `git filter-repo --replace-text` lines
  strip-settings <in> <out> <fragment>  move name bearing settings entries into a fragment
  merge-settings <settings> <fragment>  merge a fragment back (`-` reads it from stdin)
  --test                                self checks, temp files and made up names only

Copied to .git/hooks/pre-commit or .git/hooks/commit-msg it runs check-staged or check-msg.
"""
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile

SCRIPT = pathlib.Path(__file__).resolve()
MISSING = "private names list missing or empty: {}"


def live_dir():
    return pathlib.Path(os.environ.get("CLAUDE_LIVE_DIR") or pathlib.Path.home() / ".claude")


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def load_names():
    path = live_dir() / "private" / "names.txt"
    shown = str(path) if os.environ.get("CLAUDE_LIVE_DIR") else "~/.claude/private/names.txt"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        die(MISSING.format(shown))
    names = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # filter-repo would read these as patterns; a names list that silently turned
        # into a regex could match nothing, so it is refused instead
        if line.startswith(("regex:", "glob:")):
            die(f"names.txt line {n}: regex: and glob: lines are refused, names are literal")
        name, _, repl = line.partition("==>")
        if not name.strip():
            die(f"names.txt line {n}: empty name")
        names.append((n, name.strip().lower(), repl.strip() or "***REMOVED***"))
    if not names:
        die(MISSING.format(shown))
    return names


def scan(text, names):
    hits = []
    for i, line in enumerate(text.lower().splitlines(), 1):
        for n, name, _ in names:
            if name in line:
                hits.append((i, n))
    return hits


def mask(where, names):
    # a hit's path can itself hold the name (a client skill folder); the output must not
    for _, name, _ in sorted(names, key=lambda x: -len(x[1])):
        where = re.sub(re.escape(name), "***", where, flags=re.I)
    return where


def report(where, hits, names):
    for line, n in hits:
        print(f"{mask(where, names)}:{line}: names.txt line {n}")
    return len(hits)


def report_path(path, names):
    hits = scan(path, names)
    for _, n in hits:
        print(f"{mask(path, names)}: path name: names.txt line {n}")
    return len(hits)


def is_binary(data):
    return b"\0" in data[:8192]


def git(*args, cwd=None, data=None):
    r = subprocess.run(["git", *args], cwd=cwd, input=data, capture_output=True)
    if r.returncode != 0:
        die(f"git {args[0]} failed: {r.stderr.decode(errors='replace').strip()}")
    return r.stdout


def read_path(p):
    # a symlink is stored by git as its target string; reading through it would fail on a
    # linked folder and check a file the repo never holds
    if os.path.islink(p):
        return os.readlink(p).encode()
    return pathlib.Path(p).read_bytes()


def check_bytes(where, data, names):
    if is_binary(data):
        return 0
    return report(where, scan(data.decode("utf-8", errors="replace"), names), names)


def cmd_check(paths):
    names = load_names()
    bad = 0
    if not paths:
        listed = git("ls-files", "-co", "--exclude-standard", "-z").decode().split("\0")
        targets = [(p, p) for p in listed if p]
    else:
        targets = []
        for root in paths:
            if os.path.isdir(root) and not os.path.islink(root):
                for d, dirs, files in os.walk(root):
                    dirs.sort()
                    for f in sorted(files):
                        full = os.path.join(d, f)
                        targets.append((full, os.path.relpath(full, root)))
            else:
                targets.append((root, os.path.basename(root)))
    for full, rel in targets:
        if not os.path.lexists(full):
            continue  # listed by git as cached but deleted in the tree
        bad += report_path(rel, names)
        try:
            data = read_path(full)
        except OSError as e:
            print(f"{mask(full, names)}: unreadable ({e.strerror})")
            bad += 1
            continue
        bad += check_bytes(full, data, names)
    return 1 if bad else 0


REPAIR = "rm AGENTS.md && ln -s CLAUDE.md AGENTS.md && git add AGENTS.md"


def agents_link_bad():
    # Spec 0072 AC-9: `sed -i` replaces the AGENTS.md link with a copy of CLAUDE.md that then drifts, and the
    # Edit and Write tools cannot be trusted to be the only editors. Checked on the staged entry, not the disk.
    entry = git("ls-files", "-s", "--", "AGENTS.md").decode().split()
    if not entry:
        return False
    # entry = [mode, sha, stage, path]; a symlink blob is its target string
    return entry[0] != "120000" or git("cat-file", "blob", entry[1]).decode() != "CLAUDE.md"


def cmd_check_staged():
    if agents_link_bad():
        print(f"AGENTS.md must be a symlink to CLAUDE.md (spec 0072 AC-9). Repair: {REPAIR}")
        return 1
    names = load_names()
    bad = 0
    staged = git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR").decode()
    for p in filter(None, staged.split("\0")):
        bad += report_path(p, names)
        bad += check_bytes(p, git("show", f":{p}"), names)
    return 1 if bad else 0


def cmd_check_msg(path):
    names = load_names()
    text = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    return 1 if report("commit message", scan(text, names), names) else 0


def cmd_check_history():
    names = load_names()
    bad = 0
    shas, seen = [], set()
    for line in git("rev-list", "--all", "--objects").decode(errors="replace").splitlines():
        sha, _, path = line.partition(" ")
        shas.append(sha)
        if path and path not in seen:
            seen.add(path)
            bad += report_path(path, names)
    out = git("cat-file", "--batch", data="\n".join(shas).encode() + b"\n")
    i = 0
    while i < len(out):
        nl = out.index(b"\n", i)
        sha, kind, size = out[i:nl].decode().split()
        body = out[nl + 1:nl + 1 + int(size)]
        i = nl + 1 + int(size) + 1
        # commits and tags carry the message and author fields; trees are covered by the
        # path names above. Binary blobs are scanned too: filter-repo leaves them alone.
        if kind in ("blob", "commit", "tag"):
            text = body.decode("utf-8", errors="replace")
            bad += report(f"{kind} {sha[:12]}", scan(text, names), names)
    for ref in git("for-each-ref", "--format=%(refname)").decode().splitlines():
        hits = scan(ref, names)
        for _, n in hits:
            print(f"{mask(ref, names)}: ref name: names.txt line {n}")
        bad += len(hits)
    return 1 if bad else 0


def cmd_check_range(start, end):
    """Spec 0026 AC-6: what a push of start..end would publish. Output as every other command: names.txt line
    numbers, never a name."""
    names = load_names()
    bad = 0
    for _, n in scan(end, names):
        print(f"{mask(end, names)}: branch name: names.txt line {n}")
        bad += 1
    for sha in git("rev-list", f"{start}..{end}").decode().split():
        head = git("log", "-1", "--format=%an%n%ae%n%cn%n%ce%n%B", sha).decode("utf-8", errors="replace")
        bad += report(f"commit {sha[:12]}", scan(head, names), names)
        # raw -z output: ":<old mode> <new mode> <old sha> <new sha> <status>\0<path>\0" per entry
        raw = git("diff-tree", "-r", "--no-commit-id", "--root", "--diff-filter=ACMR", "-z", sha)
        fields = raw.decode("utf-8", errors="replace").split("\0")
        for meta, path in zip(fields[0::2], fields[1::2]):
            bad += report_path(path, names)
            # a submodule (gitlink, mode 160000) has no blob here; its own repo is scanned on its own push
            if meta.split()[1] != "160000":
                bad += check_bytes(f"commit {sha[:12]} {path}", git("show", f"{sha}:{path}"), names)
    return 1 if bad else 0


def write_private(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(path, 0o600)


def cmd_filter_expr(out):
    names = load_names()
    out = pathlib.Path(out).resolve()
    # the expressions file holds every name; inside a repo one `git add -A` publishes it
    r = subprocess.run(["git", "-C", str(out.parent), "rev-parse", "--is-inside-work-tree"],
                       capture_output=True, text=True)
    if r.stdout.strip() == "true":
        die(f"filter-expr: {out} is inside a git work tree, write it to a scratch path outside any repo")
    lines = [f"regex:(?i){re.escape(name)}==>{repl}"
             for _, name, repl in sorted(names, key=lambda x: -len(x[1]))]
    write_private(out, "\n".join(lines) + "\n")
    return 0


def strip(node, has_name):
    if isinstance(node, dict):
        kept, dropped = {}, {}
        for k, v in node.items():
            if has_name(k):
                dropped[k] = v
                continue
            kv, dv = strip(v, has_name)
            kept[k] = kv
            if dv is not None:
                dropped[k] = dv
        return kept, dropped or None
    if isinstance(node, list):
        # ponytail: only string items are known spots; an object inside an array is kept
        # whole, so a name in it refuses the sync instead of leaving a half object to merge
        drop = [i for i in node if isinstance(i, str) and has_name(i)]
        return [i for i in node if i not in drop], drop or None
    return node, None


def dump(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def cmd_strip_settings(src, out, fragment):
    names = load_names()
    data = json.loads(pathlib.Path(src).read_text(encoding="utf-8"))
    data.pop("autoMode", None)  # carries client repo names, env-file names, internal domains
    kept, dropped = strip(data, lambda s: bool(scan(s, names)))
    text = dump(kept)
    if report(f"{src} (stripped)", scan(text, names), names):
        return 1
    pathlib.Path(out).write_text(text, encoding="utf-8")
    write_private(fragment, dump(dropped or {}))
    return 0


def merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = merge(a[k], v) if k in a else v
        return out
    if isinstance(a, list) and isinstance(b, list):
        return a + [i for i in b if i not in a]
    return b


def cmd_merge_settings(settings, fragment):
    try:
        frag = json.load(sys.stdin) if fragment == "-" else json.loads(
            pathlib.Path(fragment).read_text(encoding="utf-8"))
        path = pathlib.Path(settings)
        base = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except json.JSONDecodeError as e:
        die(f"merge-settings: bad JSON: {e}")
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(dump(merge(base, frag)), encoding="utf-8")
    os.chmod(tmp, mode)
    os.replace(tmp, path)
    return 0


# ---------------------------------------------------------------- self checks

def selftest():
    fails = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="private-names-test."))
    live = tmp / "live"
    (live / "private").mkdir(parents=True)
    names_file = live / "private" / "names.txt"
    env = dict(os.environ, CLAUDE_LIVE_DIR=str(live), GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    env.pop("GIT_INDEX_FILE", None)  # a test run from inside a hook must not use its index

    def run(*args, cwd=None, data=None, script=SCRIPT, extra=None):
        e = dict(env, **(extra or {}))
        cmd = [str(script), *args] if str(script).endswith(".sh") else [sys.executable, str(script), *args]
        r = subprocess.run(cmd, cwd=cwd, input=data, capture_output=True, text=True, env=e)
        return r.returncode, r.stdout + r.stderr

    def sh(*args, cwd):
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)

    def ok(cond, label):
        if not cond:
            fails.append(label)

    def leaks(out):
        return any(x in out.lower() for x in ("zorblex", "quux-labs"))

    def set_names(text):
        names_file.write_text(text)

    def new_repo(name):
        d = tmp / name
        d.mkdir()
        sh("git", "init", "-q", "-b", "main", cwd=d)
        return d

    clean = tmp / "clean.txt"
    clean.write_text("nothing private here\n")

    # AC-1: a missing, empty or comment only list never passes, for every command reading it
    for label, content in (("missing", None), ("empty", ""), ("comments", "# c\n\n  \n")):
        if content is None:
            names_file.unlink(missing_ok=True)
        else:
            set_names(content)
        repo = new_repo(f"ac1-{label}")
        msg = tmp / "msg.txt"
        msg.write_text("fine\n")
        for args in (("check", str(clean)), ("check-staged",), ("check-msg", str(msg)),
                     ("check-history",), ("filter-expr", str(tmp / "expr.txt")),
                     ("strip-settings", str(clean), str(tmp / "o"), str(tmp / "f"))):
            code, out = run(*args, cwd=repo)
            ok(code == 1 and MISSING.format(names_file) in out, f"AC-1 {label} list: {args[0]}")
    set_names("regex:zorb.*\n")
    code, out = run("check", str(clean))
    ok(code == 1 and "names.txt line 1: regex: and glob: lines are refused" in out, "AC-1 regex refused")
    set_names("glob:zorb*\n")
    ok(run("check", str(clean))[0] == 1, "AC-1 glob refused")

    set_names("# private names\n\nZorblex\nquux-labs ==> a-client\n")
    os.environ["CLAUDE_LIVE_DIR"] = str(live)
    try:
        ok(load_names() == [(3, "zorblex", "***REMOVED***"), (4, "quux-labs", "a-client")],
           "AC-1 parser: comments, blanks, ==> replacement, line numbers")
    finally:
        os.environ.pop("CLAUDE_LIVE_DIR")
    ok(run("check", str(clean))[0] == 0, "AC-1 clean file passes")
    hit = tmp / "hit.txt"
    hit.write_text("one\nthe ZORBLEXian way\nand Quux-Labs too\n")
    code, out = run("check", str(hit))
    ok(code == 1 and "hit.txt:2: names.txt line 3" in out and "hit.txt:3: names.txt line 4" in out,
       "AC-1 case insensitive substring hit, with line numbers")
    ok(not leaks(out), "checker output never holds a name")
    named_dir = tmp / "src" / "zorblex-site"
    named_dir.mkdir(parents=True)
    (named_dir / "SKILL.md").write_text("clean\n")
    code, out = run("check", str(tmp / "src"))
    ok(code == 1 and "path name: names.txt line 3" in out and not leaks(out),
       "a name in a path is a hit, masked in the output")
    binary = tmp / "bin.dat"
    binary.write_bytes(b"x\0zorblex")
    ok(run("check", str(binary))[0] == 0, "check skips a binary file")

    # AC-3: strip known spots into a fragment in the same nesting, refuse the rest
    settings = {
        "autoMode": {"rules": ["anything"]},
        "permissions": {"deny": ["Read(~/zorblex/**)", "Bash(rm:*)"],
                        "allow": ["WebFetch(domain:quux-labs.com)", "Read"],
                        "ask": ["Bash(zorblex-cli *)"]},
        "skillOverrides": {"Zorblex-site": {"on": True}, "other": 1},
        "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "true"}]}]},
    }
    src = tmp / "settings.json"
    src.write_text(json.dumps(settings))
    out_f, frag_f = tmp / "out.json", tmp / "frag.json"
    code, out = run("strip-settings", str(src), str(out_f), str(frag_f))
    stripped = json.loads(out_f.read_text()) if out_f.exists() else {}
    frag = json.loads(frag_f.read_text()) if frag_f.exists() else {}
    ok(code == 0, "AC-3 strip passes on known spots")
    ok(stripped == {"permissions": {"deny": ["Bash(rm:*)"], "allow": ["Read"], "ask": []},
                    "skillOverrides": {"other": 1}, "hooks": settings["hooks"]},
       "AC-3 out file: autoMode gone, names gone, emptied parents stay")
    ok(frag == {"permissions": {"deny": ["Read(~/zorblex/**)"],
                                "allow": ["WebFetch(domain:quux-labs.com)"],
                                "ask": ["Bash(zorblex-cli *)"]},
                "skillOverrides": {"Zorblex-site": {"on": True}}},
       "AC-3 fragment: exactly the dropped entries, same nesting")
    ok(frag_f.exists() and stat.S_IMODE(frag_f.stat().st_mode) == 0o600, "AC-3 fragment mode 0600")
    bad = dict(settings, hooks={"Stop": [{"hooks": [{"type": "command", "command": "zorblex run"}]}]})
    src.write_text(json.dumps(bad))
    out_f.unlink(missing_ok=True)
    frag_f.unlink(missing_ok=True)
    code, out = run("strip-settings", str(src), str(out_f), str(frag_f))
    ok(code == 1 and "(stripped):" in out and not leaks(out), "AC-3 a name in a hook command refuses")
    ok(not out_f.exists() and not frag_f.exists(), "AC-3 a refused strip writes nothing")

    # AC-6: merge appends missing array items, merges objects, replaces scalars, idempotent
    live_settings = tmp / "live-settings.json"
    live_settings.write_text(json.dumps({"permissions": {"deny": ["a"]}, "model": "x", "keep": 1}))
    frag_f.write_text(json.dumps({"permissions": {"deny": ["b", "c", "a"]}, "model": "y",
                                  "skillOverrides": {"s": {"on": True}}}))
    want = {"permissions": {"deny": ["a", "b", "c"]}, "model": "y", "keep": 1,
            "skillOverrides": {"s": {"on": True}}}
    ok(run("merge-settings", str(live_settings), str(frag_f))[0] == 0, "AC-6 merge exits 0")
    ok(json.loads(live_settings.read_text()) == want, "AC-6 merge gives the union")
    run("merge-settings", str(live_settings), str(frag_f))
    ok(json.loads(live_settings.read_text()) == want, "AC-6 merge rerun adds nothing")
    code, _ = run("merge-settings", str(live_settings), "-", data=json.dumps({"permissions": {"allow": ["d"]}}))
    ok(code == 0 and json.loads(live_settings.read_text())["permissions"]["allow"] == ["d"],
       "AC-6 fragment from stdin")
    missing_live = tmp / "absent.json"
    run("merge-settings", str(missing_live), str(frag_f))
    ok(json.loads(missing_live.read_text()) == json.loads(frag_f.read_text()), "AC-6 merge into an absent file")
    frag_f.write_text("{not json")
    ok(run("merge-settings", str(live_settings), str(frag_f))[0] == 1, "AC-6 bad JSON exits 1")
    names_file.rename(tmp / "names.bak")
    frag_f.write_text("{}")
    ok(run("merge-settings", str(live_settings), str(frag_f))[0] == 0, "AC-6 merge needs no names list")
    (tmp / "names.bak").rename(names_file)

    # AC-8: the hooks block a name in staged content, a path, a message, any case
    repo = new_repo("ac8")
    hooks = repo / ".git" / "hooks"
    hooks.mkdir(exist_ok=True)
    for h in ("pre-commit", "commit-msg"):
        shutil.copy(SCRIPT, hooks / h)

    def commit(path, body, message):
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(body)
        sh("git", "add", "-A", cwd=repo)
        r = sh("git", "commit", "-q", "-m", message, cwd=repo)
        sh("git", "reset", "-q", cwd=repo)
        return r.returncode, r.stdout + r.stderr

    code, out = commit("a.txt", "hello zorblex\n", "add a")
    ok(code != 0 and "a.txt:1: names.txt line 3" in out and not leaks(out), "AC-8 staged name blocks")
    code, _ = commit("a.txt", "hello ZORBLEX\n", "add a")
    ok(code != 0, "AC-8 upper case name blocks")
    code, out = commit("a.txt", "hello\n", "notes for Quux-Labs")
    ok(code != 0 and "commit message:1: names.txt line 4" in out, "AC-8 message name blocks")
    code, _ = commit("zorblex/b.txt", "hello\n", "add b")
    ok(code != 0, "AC-8 path name blocks")
    (repo / "zorblex").rename(tmp / "zorblex-moved")
    code, out = commit("a.txt", "hello\n", "clean commit")
    ok(code == 0, f"AC-8 clean commit passes: {out.strip()}")
    names_file.rename(tmp / "names.bak")
    code, out = commit("c.txt", "fine\n", "another clean commit")
    ok(code != 0 and "private names list missing" in out, "AC-8 missing list blocks a clean commit")
    (tmp / "names.bak").rename(names_file)

    # spec 0072 AC-9: a commit where AGENTS.md is not a link to CLAUDE.md is refused, with the repair command
    lrepo = new_repo("ac9")
    (lrepo / ".git" / "hooks").mkdir(exist_ok=True)
    shutil.copy(SCRIPT, lrepo / ".git" / "hooks" / "pre-commit")

    def lcommit(message):
        sh("git", "add", "-A", cwd=lrepo)
        r = sh("git", "commit", "-q", "-m", message, cwd=lrepo)
        return r.returncode, r.stdout + r.stderr

    (lrepo / "CLAUDE.md").write_text("entry\n")
    code, out = lcommit("no agents file")
    ok(code == 0, f"AC-9 no AGENTS.md at all: no-op: {out.strip()}")
    (lrepo / "AGENTS.md").symlink_to("CLAUDE.md")
    code, out = lcommit("link")
    ok(code == 0, f"AC-9 AGENTS.md linked to CLAUDE.md passes: {out.strip()}")
    (lrepo / "AGENTS.md").unlink()
    (lrepo / "AGENTS.md").write_text("entry\n")
    code, out = lcommit("sed -i replaced the link")
    ok(code != 0 and REPAIR in out, f"AC-9 a replaced link is refused with the repair command: {out.strip()}")
    sh("git", "reset", "-q", cwd=lrepo)
    (lrepo / "AGENTS.md").unlink()
    (lrepo / "AGENTS.md").symlink_to("other.md")
    code, out = lcommit("link to the wrong file")
    ok(code != 0 and REPAIR in out, "AC-9 a link to another file is refused")
    sh("git", "reset", "-q", cwd=lrepo)
    (lrepo / "AGENTS.md").unlink()
    (lrepo / "AGENTS.md").symlink_to("CLAUDE.md")
    (lrepo / "x.txt").write_text("x\n")
    code, out = lcommit("link restored")
    ok(code == 0, f"AC-9 the repaired link passes: {out.strip()}")

    # AC-10: expressions, history scan, and a real rewrite
    expr = tmp / "expr.txt"
    ok(run("filter-expr", str(expr))[0] == 0, "AC-10 filter-expr exits 0")
    ok(expr.read_text() == "regex:(?i)quux\\-labs==>a-client\nregex:(?i)zorblex==>***REMOVED***\n",
       "AC-10 filter-expr: escaped, case insensitive, longest first, default replacement")
    ok(stat.S_IMODE(expr.stat().st_mode) == 0o600, "AC-10 filter-expr file mode 0600")
    code, _ = run("filter-expr", str(repo / "expr.txt"))
    ok(code == 1 and not (repo / "expr.txt").exists(), "AC-10 filter-expr refuses a path inside a repo")

    hist = new_repo("ac10")

    def raw_commit(path, body, message):
        p = hist / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
        sh("git", "add", "-A", cwd=hist)
        sh("git", "commit", "-q", "--no-verify", "-m", message, cwd=hist)

    raw_commit("a.txt", b"clean\n", "start")
    ok(run("check-history", cwd=hist)[0] == 0, "AC-10 clean history passes")
    raw_commit("a.txt", b"Zorblex and zorblex and ZORBLEX\nsuperquux-labsish\n", "msg about Zorblex")
    code, out = run("check-history", cwd=hist)
    ok(code == 1 and "blob " in out and "commit " in out and not leaks(out),
       "AC-10 history hit in a blob and a message")
    if shutil.which("git-filter-repo") or sh("git", "filter-repo", "--version", cwd=hist).returncode == 0:
        r = sh("git", "filter-repo", "--replace-text", str(expr), "--replace-message", str(expr),
               "--force", cwd=hist)
        code, out = run("check-history", cwd=hist)
        ok(r.returncode == 0 and code == 0, f"AC-10 rewrite leaves a clean history: {out.strip()}")
    else:
        print("skip: git filter-repo not installed, rewrite scenario not run")
    for label, action in (
            ("binary blob", lambda: raw_commit("b.bin", b"x\0zorblex", "bin")),
            ("path name", lambda: raw_commit("zorblex.txt", b"clean\n", "path")),
            ("branch name", lambda: sh("git", "branch", "quux-labs-wip", cwd=hist))):
        snap = sh("git", "rev-parse", "HEAD", cwd=hist).stdout.strip()
        action()
        ok(run("check-history", cwd=hist)[0] == 1, f"AC-10 history hit in a {label}")
        sh("git", "reset", "-q", "--hard", snap, cwd=hist)
        sh("git", "branch", "-D", "quux-labs-wip", cwd=hist)
        sh("git", "reflog", "expire", "--expire=now", "--all", cwd=hist)
        sh("git", "gc", "-q", "--prune=now", cwd=hist)

    # spec 0026 AC-6: check-range scans only start..end: messages, authors, blobs, paths and the branch name
    rng = new_repo("range")

    def range_commit(path, body, message, author="t"):
        (rng / path).parent.mkdir(parents=True, exist_ok=True)
        (rng / path).write_text(body)
        sh("git", "add", "-A", cwd=rng)
        sh("git", "commit", "-q", "--no-verify", f"--author={author} <a@example.invalid>", "-m", message, cwd=rng)
        return sh("git", "rev-parse", "HEAD", cwd=rng).stdout.strip()

    old = range_commit("a.txt", "zorblex before the range\n", "start")
    sh("git", "checkout", "-q", "-b", "feat/x", cwd=rng)
    range_commit("b.txt", "clean\n", "clean change")
    code, out = run("check-range", old, "feat/x", cwd=rng)
    ok(code == 0, f"spec 0026 check-range ignores what lies before the range: {out.strip()}")
    for label, args in (("blob", ("c.txt", "Zorblex\n", "c")), ("message", ("d.txt", "x\n", "about quux-labs")),
                        ("path", ("zorblex/e.txt", "x\n", "e")), ("author", ("f.txt", "x\n", "f", "Zorblex Bot"))):
        snap = sh("git", "rev-parse", "HEAD", cwd=rng).stdout.strip()
        range_commit(*args)
        code, out = run("check-range", old, "feat/x", cwd=rng)
        ok(code == 1 and "names.txt line" in out and not leaks(out), f"spec 0026 check-range hit in a {label}")
        sh("git", "reset", "-q", "--hard", snap, cwd=rng)
    # a submodule entry has no blob to show; the scan must step over it and still reach later commits
    snap = sh("git", "rev-parse", "HEAD", cwd=rng).stdout.strip()
    sh("git", "update-index", "--add", "--cacheinfo", f"160000,{old},sub", cwd=rng)
    sh("git", "commit", "-q", "--no-verify", "-m", "add submodule", cwd=rng)
    code, out = run("check-range", old, "feat/x", cwd=rng)
    ok(code == 0, f"check-range steps over a submodule entry: {out.strip()}")
    range_commit("g.txt", "Zorblex\n", "g")
    code, out = run("check-range", old, "feat/x", cwd=rng)
    ok(code == 1 and "g.txt" in out and not leaks(out), "check-range scans past a submodule entry")
    sh("git", "reset", "-q", "--hard", snap, cwd=rng)
    sh("git", "checkout", "-q", "-b", "feat/zorblex-x", cwd=rng)
    code, out = run("check-range", old, "feat/zorblex-x", cwd=rng)
    ok(code == 1 and "branch name: names.txt line 3" in out and not leaks(out), "spec 0026 check-range branch name")

    # AC-3 to AC-5: tools/bin/sync.sh on a temp repo and a temp live tree
    sync_repo = new_repo("sync")
    for d in ("tools/scripts", "tools/bin"):
        (sync_repo / d).mkdir(parents=True)
    shutil.copy(SCRIPT.parents[2] / "tools/bin/sync.sh", sync_repo / "tools/bin/sync.sh")
    shutil.copy(SCRIPT, sync_repo / "tools" / "scripts" / "private-names.py")
    # this file holds the made up names, so the temp repo must not track its copy
    (sync_repo / ".git" / "info").mkdir(exist_ok=True)
    (sync_repo / ".git" / "info" / "exclude").write_text("/tools/scripts/\n")
    (sync_repo / "README.md").write_text("public\n")
    slive = tmp / "sync-live"
    for d in ("agents", "rules", "hooks", "scripts", "private"):
        (slive / d).mkdir(parents=True)
    shutil.copy(names_file, slive / "private" / "names.txt")
    (slive / "CLAUDE.md").write_text("# rules\n")
    (slive / "settings.json").write_text(json.dumps(settings))
    (slive / "settings.local.json").write_text(json.dumps({"permissions": {"allow": ["Read(~/quux-labs)", "Read"]}}))
    (slive / "agents" / "a.md").write_text("agent\n")
    (slive / "rules" / "r.md").write_text("rule\n")
    for f in ("hooks/block-destructive.sh", "hooks/review-stack-pre-push", "hooks/plain-panel.py", "hooks/context-monitor.js"):
        (slive / f).write_text("#!/bin/sh\n")
    sh("git", "add", "-A", cwd=sync_repo)
    sh("git", "commit", "-q", "--no-verify", "-m", "start", cwd=sync_repo)
    sync_env = {"CLAUDE_LIVE_DIR": str(slive)}

    def tree_state():
        files = sorted(p for p in sync_repo.rglob("*") if ".git" not in p.parts and p.is_file())
        return sh("git", "status", "--porcelain", cwd=sync_repo).stdout, \
            [(str(p), p.read_bytes()) for p in files]

    (slive / "rules" / "r.md").write_text("rule\nask the Zorblex bot\n")
    before = tree_state()
    code, out = run(script=sync_repo / "tools/bin/sync.sh", cwd=sync_repo, extra=sync_env)
    ok(code == 1 and f"{slive}/rules/r.md:2: names.txt line 3" in out and not leaks(out),
       f"AC-4 sync refuses a name in a live rule file: {out.strip()}")
    ok(tree_state() == before, "AC-4 refused sync leaves the repo byte for byte unchanged")
    ok(not (slive / "private" / "settings.json").exists(), "AC-3 refused sync writes no fragment")
    (slive / "rules" / "r.md").write_text("rule\n")
    # covers: AC-4, every source is checked, not only rules/
    for rel, body in (("CLAUDE.md", "# rules\nsee zorblex\n"), ("agents/a.md", "agent\nQuux-Labs\n"),
                      ("hooks/context-monitor.js", "#!/bin/sh\nzorblex\n")):
        (slive / rel).write_text(body)
        code, out = run(script=sync_repo / "tools/bin/sync.sh", cwd=sync_repo, extra=sync_env)
        ok(code == 1 and f"{slive}/{rel}:2: names.txt line" in out and not leaks(out)
           and tree_state() == before, f"AC-4 sync refuses a name in live {rel}")
    (slive / "CLAUDE.md").write_text("# rules\n")
    (slive / "agents" / "a.md").write_text("agent\n")
    (slive / "hooks" / "context-monitor.js").write_text("#!/bin/sh\n")
    (slive / "settings.json").write_text(json.dumps(dict(settings, env={"X": "zorblex"})))
    code, out = run(script=sync_repo / "tools/bin/sync.sh", cwd=sync_repo, extra=sync_env)
    ok(code == 1 and "settings.json (stripped):" in out and not leaks(out) and tree_state() == before,
       "AC-4 sync refuses a name in a settings string value")
    (slive / "settings.json").write_text(json.dumps(settings))
    (slive / "private" / "names.txt").unlink()
    code, out = run(script=sync_repo / "tools/bin/sync.sh", cwd=sync_repo, extra=sync_env)
    ok(code == 1 and "private names list missing" in out and tree_state() == before,
       "AC-1 sync refuses without a names list")
    shutil.copy(names_file, slive / "private" / "names.txt")
    code, out = run(script=sync_repo / "tools/bin/sync.sh", cwd=sync_repo, extra=sync_env)
    ok(code == 0, f"AC-3 clean sync passes: {out.strip()}")
    # covers: spec 0037 AC-7, sync copies the context monitor hook back into the repo
    synced_hook = sync_repo / "claude-home" / "hooks" / "context-monitor.js"
    ok(synced_hook.exists() and synced_hook.read_text() == (slive / "hooks" / "context-monitor.js").read_text(),
       "0037 AC-7 sync copies hooks/context-monitor.js")
    synced = [(sync_repo / "claude-home" / f).read_text() for f in ("settings.json", "settings.local.json")
              if (sync_repo / "claude-home" / f).exists()]
    ok(len(synced) == 2 and "autoMode" not in synced[0] and not leaks("".join(synced)),
       "AC-3 synced settings hold no name and no autoMode")
    pfrag = slive / "private" / "settings.json"
    ok(pfrag.exists() and json.loads(pfrag.read_text()) == frag
       and stat.S_IMODE(pfrag.stat().st_mode) == 0o600, "AC-3 sync writes the settings fragment, 0600")
    lfrag = slive / "private" / "settings.local.json"
    ok(lfrag.exists() and json.loads(lfrag.read_text()) == {"permissions": {"allow": ["Read(~/quux-labs)"]}},
       "AC-3 sync writes the settings.local fragment")
    ok(not (sync_repo / "private").exists(), "sync copies nothing from private/")
    # covers: AC-3, the fragment is replaced on every passing sync, never accumulated
    (slive / "settings.local.json").write_text(json.dumps({"permissions": {"allow": ["Read"]}}))
    code, _ = run(script=sync_repo / "tools/bin/sync.sh", cwd=sync_repo, extra=sync_env)
    ok(code == 0 and json.loads(lfrag.read_text()) == {}, "AC-3 a passing sync replaces the fragment")
    (sync_repo / "README.md").write_text("public\nby quux-labs\n")
    code, out = run(script=sync_repo / "tools/bin/sync.sh", cwd=sync_repo, extra=sync_env)
    ok(code == 1 and "README.md:2: names.txt line 4" in out and not leaks(out),
       "AC-5 sync final check catches a name already in the repo")

    # AC-6, AC-7: tools/bin/install.sh --dry-run on a temp HOME; writes nothing, real hooks untouched
    real_repo = SCRIPT.parents[2]
    hooks_dir = real_repo / ".git" / "hooks"
    hooks_before = sorted(os.listdir(hooks_dir)) if hooks_dir.is_dir() else []
    home = tmp / "home"
    ilive = home / ".claude"
    (ilive / "private").mkdir(parents=True)
    ienv = {"HOME": str(home), "CLAUDE_LIVE_DIR": str(ilive)}

    def files_under(d):
        return sorted(str(p) for p in d.rglob("*"))

    snap = files_under(home)
    code, out = run("--dry-run", script=real_repo / "tools/bin/install.sh", extra=ienv)
    ok(code == 0 and out.count("no private settings fragment, private entries not installed") == 2,
       "AC-6 install without fragments warns and goes on")
    ok("no private names list, exclude lines and commit hooks skipped" in out, "AC-7 install skips without names")
    shutil.copy(names_file, ilive / "private" / "names.txt")
    (ilive / "private" / "settings.json").write_text("{}")
    (ilive / "private" / "settings.local.json").write_text("{}")
    (ilive / "private" / "gitignore").write_text("skills/zorblex-site/\n")
    snap = files_under(home)
    code, out = run("--dry-run", script=real_repo / "tools/bin/install.sh", extra=ienv)
    ok(code == 0 and out.count("merge-settings") == 2, "AC-6 dry run prints both merges")
    ok("exclude:" in out and ("pre-commit" in out) and ("commit-msg" in out) and not leaks(out),
       "AC-7 dry run prints the exclude lines and hook links without a name")
    ok(files_under(home) == snap, "install --dry-run writes nothing")
    ok((sorted(os.listdir(hooks_dir)) if hooks_dir.is_dir() else []) == hooks_before,
       "install --dry-run leaves the real .git/hooks alone")

    # AC-6, AC-7: a real install, run from a scratch repo so the real .git and ~/.claude stay
    # untouched. It exits 1 at its own verify step (the scratch repo has no design scripts),
    # which runs after every spec 0013 part, so outcomes are asserted, not the exit code.
    irepo = new_repo("install")
    for d in ("claude-home/agents", "claude-home/rules", "claude-home/hooks", "claude-home/scripts", "tools/scripts", "tools/bin"):
        (irepo / d).mkdir(parents=True)
    shutil.copy(real_repo / "tools/bin/install.sh", irepo / "tools/bin/install.sh")
    shutil.copy(real_repo / "tools/bin/claude-config.py", irepo / "tools/bin/claude-config.py")
    shutil.copy(SCRIPT, irepo / "tools" / "scripts" / "private-names.py")
    # every file install.sh copies unconditionally: a missing one stops it under set -e before settings.json
    for f in ("hooks/block-destructive.sh", "hooks/review-stack-pre-push", "hooks/plain-panel.py", "hooks/context-monitor.js",
              "hooks/handover-start.sh", "hooks/no-jjstack-bar.py", "hooks/skill-rules.py", "hooks/chain-catch.py", "hooks/live-tick.py"):
        (irepo / "claude-home" / f).write_text("#!/bin/sh\n")
    (irepo / "claude-home" / "CLAUDE.md").write_text("# rules\n")
    (irepo / "claude-home" / "settings.json").write_text(json.dumps({"permissions": {"deny": ["Bash(rm:*)", "Read(~/x)"]}}))
    hooks = irepo / ".git" / "hooks"
    hooks.mkdir(exist_ok=True)
    ichecker = irepo / "tools" / "scripts" / "private-names.py"
    # without its execute bit, so the hook's 0755 has to come from install, not from cp
    ichecker.chmod(0o644)
    (ilive / "private" / "settings.json").write_text(json.dumps(
        {"permissions": {"deny": ["Read(/home/santiago/zorblex/**)", "Read(~/x)"]},
         "skillOverrides": {"zorblex-site": {"on": True}}}))
    (ilive / "private" / "settings.local.json").write_text(json.dumps({"permissions": {"allow": ["Read(~/quux-labs)"]}}))
    excl = irepo / ".git" / "info" / "exclude"
    excl_before = excl.read_text() if excl.exists() else ""
    code, out = run(script=irepo / "tools/bin/install.sh", extra=ienv)
    live_s = json.loads((ilive / "settings.json").read_text())
    ok(live_s.get("permissions", {}).get("deny") == ["Bash(rm:*)", "Read(~/x)", f"Read({home}/zorblex/**)"]
       and live_s.get("skillOverrides") == {"zorblex-site": {"on": True}},
       f"AC-6 install merges the fragment, /home/santiago swapped to $HOME, no doubles: {live_s}")
    ok(json.loads((ilive / "settings.local.json").read_text()) == {"permissions": {"allow": ["Read(~/quux-labs)"]}},
       "AC-6 install merges the settings.local fragment")
    ok(excl.read_text() == excl_before + "skills/zorblex-site/\n", "AC-7 install adds the private exclude line")

    def is_copy(h):
        p = hooks / h
        return (not p.is_symlink() and p.read_bytes() == ichecker.read_bytes()
                and stat.S_IMODE(p.stat().st_mode) == 0o755)

    ok(all(is_copy(h) and f"{h}: copied" in out for h in ("pre-commit", "commit-msg")),
       "AC-7 install copies both hooks, regular 0755 files equal to the checker")
    ok(not leaks(out), "install output never holds a name")
    # covers: spec 0037 AC-7, install copies the context monitor hook live, executable
    live_hook = ilive / "hooks" / "context-monitor.js"
    ok(live_hook.exists() and os.access(live_hook, os.X_OK), "0037 AC-7 install copies hooks/context-monitor.js, executable")
    code, out = run(script=irepo / "tools/bin/install.sh", extra=ienv)
    ok(excl.read_text().count("skills/zorblex-site/") == 1, "AC-7 install rerun adds no exclude line twice")
    ok(json.loads((ilive / "settings.json").read_text()) == live_s, "AC-6 install rerun gives the same settings")
    ok(all(f"{h}: up to date" in out and is_copy(h) for h in ("pre-commit", "commit-msg")),
       "AC-7 install rerun says up to date")
    # spec 0019 AC-9: the live autoMode survives an install; none in, none out; unreadable warns and goes on
    ok("autoMode" not in live_s, "0019 AC-9 a live file with no autoMode yields none")
    auto = {"environment": ["trusted repo"], "allow": ["x"]}
    (ilive / "settings.json").write_text(json.dumps({**live_s, "autoMode": auto}))
    code, out = run("--dry-run", script=irepo / "tools/bin/install.sh", extra=ienv)
    ok("would keep autoMode" in out, "0019 AC-9 dry run says it would keep autoMode")
    code, out = run(script=irepo / "tools/bin/install.sh", extra=ienv)
    kept = json.loads((ilive / "settings.json").read_text())
    ok(kept == {**live_s, "autoMode": auto}, f"0019 AC-9 install keeps the live autoMode: {kept}")
    (ilive / "settings.json").write_text("{not json")
    code, out = run(script=irepo / "tools/bin/install.sh", extra=ienv)
    ok("autoMode not kept: " in out and json.loads((ilive / "settings.json").read_text()) == live_s,
       "0019 AC-9 an unreadable live file warns and installs on")
    # the old install: a link to the checker, and an older copy recognized by line 2
    (hooks / "pre-commit").unlink()
    (hooks / "pre-commit").symlink_to(ichecker)
    lines = ichecker.read_text().splitlines(keepends=True)
    (hooks / "commit-msg").write_text("".join(lines[:2]) + "old\n")
    before_checker = ichecker.read_bytes()
    code, out = run(script=irepo / "tools/bin/install.sh", extra=ienv)
    ok(all(f"{h}: refreshed" in out and is_copy(h) for h in ("pre-commit", "commit-msg")),
       "AC-7 install refreshes a link to the checker and an older copy")
    ok(ichecker.read_bytes() == before_checker, "AC-7 refreshing a link never writes into the checker")
    # an identical copy missing its execute bit is refreshed, not up to date
    (hooks / "pre-commit").chmod(0o644)
    code, out = run(script=irepo / "tools/bin/install.sh", extra=ienv)
    ok("pre-commit: refreshed" in out and is_copy("pre-commit"), "AC-7 install restores a lost execute bit")
    # hand written hook and a link elsewhere are left alone; dry run writes nothing
    (hooks / "commit-msg").write_text("#!/bin/sh\nexit 0\n")
    (hooks / "pre-commit").unlink()
    (hooks / "pre-commit").symlink_to(irepo / "CLAUDE.md")
    code, out = run(script=irepo / "tools/bin/install.sh", extra=ienv)
    ok(all(f"hook exists, not replaced: {h}" in out for h in ("pre-commit", "commit-msg"))
       and (hooks / "commit-msg").read_text() == "#!/bin/sh\nexit 0\n"
       and os.readlink(hooks / "pre-commit") == str(irepo / "CLAUDE.md"),
       "AC-7 install leaves a hand written hook and a foreign link alone and says so")
    (hooks / "pre-commit").unlink()
    (hooks / "commit-msg").write_text("".join(lines[:2]) + "old\n")
    snap = files_under(irepo / ".git")
    old_msg = (hooks / "commit-msg").read_bytes()
    code, out = run("--dry-run", script=irepo / "tools/bin/install.sh", extra=ienv)
    ok("would: pre-commit: copied" in out and "would: commit-msg: refreshed" in out
       and files_under(irepo / ".git") == snap and (hooks / "commit-msg").read_bytes() == old_msg,
       "AC-7 install --dry-run prints the hook copies and writes nothing")
    # spec 0036 AC-4, AC-5: a repo settings.json that does not parse fails the dry run, naming
    # the file, and a real install leaves the live settings.json byte for byte unchanged
    # spec 0036 AC-6: a real install rebuilds the skill trigger index; a dry run and a staged one do not
    xt = ilive / "skills" / "jjstack" / "bin" / "jjstack-extract-triggers"
    xt.parent.mkdir(parents=True)
    xt.write_text(f"#!/bin/sh\necho x >> {tmp}/triggers.ran\n")
    xt.chmod(0o755)
    ran = tmp / "triggers.ran"
    code, out = run("--dry-run", script=irepo / "tools/bin/install.sh", extra=ienv)
    ok(f"would: {xt}" in out and not ran.exists(), "0036 AC-6 dry run names the trigger index rebuild, runs nothing")
    code, out = run(script=irepo / "tools/bin/install.sh", extra=dict(ienv, WF_STAGE="1"))
    ok(not ran.exists() and "skill trigger index not rebuilt" in out,
       "0036 AC-6 a staged install leaves the index to you and says so")
    code, out = run(script=irepo / "tools/bin/install.sh", extra=ienv)
    ok(ran.exists() and ran.read_text() == "x\n", "0036 AC-6 install rebuilds the skill trigger index")
    good = (irepo / "claude-home" / "settings.json").read_text()
    (irepo / "claude-home" / "settings.json").write_text('{"permissions": {"deny": ["Bash(rm:*)",]}}')
    code, out = run("--dry-run", script=irepo / "tools/bin/install.sh", extra=ienv)
    ok(code != 0 and f"{irepo}/claude-home/settings.json does not parse" in out,
       f"0036 AC-4 dry run refuses a settings.json that does not parse: {out.strip()[-200:]}")
    live_before = (ilive / "settings.json").read_bytes()
    code, out = run(script=irepo / "tools/bin/install.sh", extra=ienv)
    ok(code != 0 and (ilive / "settings.json").read_bytes() == live_before,
       "0036 AC-5 install of a settings.json that does not parse leaves the live file unchanged")
    (irepo / "claude-home" / "settings.json").write_text(good)
    (irepo / "claude-home" / "settings.local.json").write_text("{")
    code, out = run("--dry-run", script=irepo / "tools/bin/install.sh", extra=ienv)
    ok(code != 0 and f"{irepo}/claude-home/settings.local.json does not parse" in out,
       "0036 AC-4 dry run refuses a settings.local.json that does not parse")

    shutil.rmtree(tmp)
    for f in fails:
        print(f"FAIL: {f}")
    print(f"private-names: {'FAILED' if fails else 'all self checks passed'}")
    return 1 if fails else 0


def main(argv):
    prog = os.path.basename(argv[0])
    if prog == "pre-commit":
        return cmd_check_staged()
    if prog == "commit-msg":
        return cmd_check_msg(argv[1])
    cmds = {"check": (cmd_check, None), "check-staged": (cmd_check_staged, 0),
            "check-msg": (cmd_check_msg, 1), "check-history": (cmd_check_history, 0),
            "check-range": (cmd_check_range, 2),
            "filter-expr": (cmd_filter_expr, 1), "strip-settings": (cmd_strip_settings, 3),
            "merge-settings": (cmd_merge_settings, 2), "--test": (selftest, 0)}
    if len(argv) < 2 or argv[1] not in cmds:
        die(__doc__.strip())
    fn, nargs = cmds[argv[1]]
    args = argv[2:]
    if nargs is not None and len(args) != nargs:
        die(f"{argv[1]} takes {nargs} argument(s)")
    return fn(args) if nargs is None else fn(*args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
