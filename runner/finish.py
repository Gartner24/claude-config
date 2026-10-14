# `wf finish` (spec 0019): the live setup steps waiting on you, run at your keyboard after one Enter.
# Unattended calls never write ~/.claude, so these used to pile up as separate boxes run by hand.
import datetime
import filecmp
import glob
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import types
from contextlib import redirect_stdout
from io import StringIO

import report
import run
import wf

SPAN = re.compile(r"`([^`]+)`")
SPEC_LINK = re.compile(r"(?:^|/)specs/[^/]+/index\.md$")
PROBE = re.compile(r"docs/specs/[^/]+/probes/[^/]+")
# Spec 0020 AC-3: what the stage copies from the live dir; install.sh writes the first eight and reads the last two.
STAGED = ("agents", "rules", "hooks", "scripts", "commands", "skills", "settings.json", "settings.local.json",
          "CLAUDE.md", "private")
# AC-4: renamed last, settings.json very last (verify.md P1: a running call rereads settings mid call).
SETTINGS_LAST = ("settings.local.json", "settings.json")
HOOKS = ("pre-commit", "commit-msg")
KEEP_STAGES = 3
# Spec 0020 AC-8: a commit hitting a held index.lock.
COMMIT_TRIES = 3
COMMIT_GAP = 2
PICK = re.compile(r"\d+(-\d+)?")
SIGNALS = (signal.SIGINT, signal.SIGHUP, signal.SIGTERM)
NEVER_COPIED = ("settings.json", "settings.local.json")
PHASES = ("copy", "install", "check")
GRACE = 30
LIVE_HEADING = "## Live runs (wf finish)"


def refuse(reason, detail):
    print(f"refused: {reason}: {wf.clean(str(detail))}", flush=True)
    return 5


def live_dir():
    """Spec 0020 AC-3: run.live_dir(), resolved, so the swap, the guard and claude read the same folder."""
    return os.path.realpath(run.live_dir())


def inside(path, root):
    return path == root or path.startswith(root + os.sep)


def runner_checker(src):
    """Spec 0026 AC-6: the private names checker beside runner/, which the runner copy carries; None when absent."""
    p = os.path.join(os.path.dirname(os.path.abspath(src)), "scripts", "private-names.py")
    return p if os.path.isfile(p) else None


def runner_fp(src):
    """Spec 0020 AC-12: 12 hex of the sha256 over name, NUL, bytes, NUL of each runner/*.py in name order, then
    (spec 0026 AC-6) scripts/private-names.py the same way."""
    h = hashlib.sha256()
    for name in sorted(n for n in os.listdir(src) if n.endswith(".py")):
        with open(os.path.join(src, name), "rb") as f:
            h.update(name.encode() + b"\0" + f.read() + b"\0")
    if runner_checker(src):
        with open(runner_checker(src), "rb") as f:
            h.update(b"scripts/private-names.py\0" + f.read() + b"\0")
    return h.hexdigest()[:12]


def install_runner(repo, home, dry=False):
    """Spec 0020 AC-12: copy runner/*.py to <home>/.local/share/wf/<fp>/, link wf and next to it, prune.
    The link used to point into the repo, so the SessionStart hook's `wf` token made every call's guard
    deny Edit on runner/ (verify.md P2). Returns <fp>."""
    src = os.path.join(repo, "runner")
    fp = runner_fp(src)
    share = os.path.join(home, ".local", "share", "wf")
    dst = os.path.join(share, fp)
    binp = os.path.join(home, ".local", "bin")
    if dry:
        print(f"  would: copy runner/*.py to {dst}")
    elif not os.path.isdir(dst):
        tmp = f"{dst}.tmp-{os.getpid()}"
        os.makedirs(tmp)
        for name in sorted(os.listdir(src)):
            if name.endswith(".py"):
                shutil.copy2(os.path.join(src, name), tmp)
        if runner_checker(src):
            shutil.copy2(runner_checker(src), os.path.join(tmp, "private-names.py"))
        os.rename(tmp, dst)
    for link, target in runner_links(home, dst):
        if dry:
            print(f"  would: ln -sfn {target} {link}")
        else:
            print(f"  {os.path.basename(link)} -> {target}")
            os.makedirs(binp, exist_ok=True)
            tmp = f"{link}.tmp-{os.getpid()}"
            os.symlink(target, tmp)
            os.replace(tmp, link)
    if dry:
        print(f"  would: prune {share} folders unpicked for 7 days")
        return fp
    picked(home, dst)
    return fp


def runner_links(home, dst):
    """AC-12: [(link, target)] for wf and next at <dst>/wf.py; a real file in the way is skipped with `SKIP`."""
    out = []
    for name in ("wf", "next"):
        link = os.path.join(home, ".local", "bin", name)
        if os.path.exists(link) and not os.path.islink(link):
            print(f"  SKIP {name} (a real file is already at {link})")
        else:
            out.append((link, os.path.join(dst, "wf.py")))
    return out


def picked(home, dst):
    """AC-12: the chosen folder's mtime is its "last picked" time; every other folder under share/wf unpicked
    for 7 days and named by no ~/.local/bin link is deleted. A running wf keeps its own folder."""
    share, binp = os.path.dirname(dst), os.path.join(home, ".local", "bin")
    os.utime(dst)
    linked = set()
    for n in os.listdir(binp) if os.path.isdir(binp) else ():
        p = os.path.join(binp, n)
        if os.path.islink(p):
            linked.add(os.path.realpath(p))
    old = datetime.datetime.now().timestamp() - 7 * 86400
    for n in os.listdir(share):
        d = os.path.join(share, n)
        if os.path.isdir(d) and not os.path.islink(d) and ".wf-swap-" not in n and os.path.getmtime(d) < old \
                and not any(inside(t, os.path.realpath(d)) for t in linked):
            shutil.rmtree(d)


def repo_file(root, arg):
    """The real path of a repo file named by arg, else None: present, a regular file, inside the repo."""
    p = os.path.join(root, os.path.expanduser(arg))
    real = os.path.realpath(p)
    return real if inside(real, root) and os.path.isfile(real) else None


class Step:
    def __init__(self, phase, repo, span, argv=None, src=None, dst=None, rel=None):
        self.phase, self.repo, self.span = phase, repo, span
        self.argv, self.src, self.dst, self.rel = argv, src, dst, rel
        self.boxes, self.result, self.code, self.last, self.log = [], None, None, "", None

    def key(self):
        return (self.phase, self.repo.path, tuple(self.argv) if self.argv else (self.src, self.dst))


def shape(root, span):
    """AC-2: (phase, fields) for a span of one of the four shapes, else None."""
    try:
        t = shlex.split(span)
    except ValueError:
        return None
    if len(t) == 3 and t[0] == "cp" and not t[1].startswith("-") and not t[2].startswith("-"):
        p = os.path.join(root, os.path.expanduser(t[1]))
        src = os.path.realpath(p)
        if os.path.islink(p) or not inside(src, root) or src == root or not os.path.isfile(src):
            return None
        rel = os.path.relpath(src, root)
        if rel in NEVER_COPIED or rel.split(os.sep)[0] == "private":
            return None
        dst = os.path.join(live_dir(), rel)
        # Spec 0020 AC-3: `~/.claude/` names the live dir, $CLAUDE_CONFIG_DIR when set.
        target = run.expand(t[2])[0] if t[2].startswith("~/.claude/") else os.path.join(root, os.path.expanduser(t[2]))
        if os.path.realpath(target) != dst:
            return None
        return "copy", {"src": src, "dst": dst, "rel": rel}
    if t == ["./install.sh"] and repo_file(root, "install.sh"):
        return "install", {"argv": t}
    # Specs 0017, 0020 AC-11, 0027 AC-10: the e2e flags a live box may name.
    if t[:2] == ["python3", "runner/e2e/run.py"] and t[2:] in ([], ["--parallel"], ["--beside"], ["--same-repo"]) \
            and repo_file(root, t[1]):
        return "check", {"argv": t}
    if len(t) == 2 and (t[0], os.path.splitext(t[1])[1]) in (("python3", ".py"), ("bash", ".sh")) \
            and PROBE.fullmatch(t[1]) and repo_file(root, t[1]):
        return "check", {"argv": t}
    return None


def not_live(root, spans):
    """AC-2: why a box with these spans is yours, else None."""
    if not spans:
        return "no command in backticks"
    bad = next((s for s in spans if shape(root, s) is None), None)
    if bad is not None or len(spans) > 1:
        return f"not a live step: {bad if bad is not None else spans[1]}"
    return None


class LiveBox:
    def __init__(self, repo, scope_file, heading, line, text, spec):
        self.repo, self.scope_file, self.heading, self.line, self.text = repo, scope_file, heading, line, text
        self.feature = wf.DISPLAY_TAG.sub("", heading).strip()
        self.spec = spec
        self.steps = []


def scope_files(c):
    folder = os.path.join(c.path, c.scope_dir)
    main = next(os.path.join(folder, f) for f in wf.SCOPE_FILES if os.path.isfile(os.path.join(folder, f)))
    if not main.endswith("index.md"):
        return [main]
    return list(wf.epics(folder, wf.read(main), []))


def spec_of(scope_file, plain, root):
    """AC-5: the verify.md beside the section's first specs/<dir>/index.md link, else None."""
    for link in wf.LINK.findall("\n".join(plain)):
        target = link.split("#", 1)[0]
        if SPEC_LINK.search(target):
            real = os.path.realpath(os.path.join(os.path.dirname(scope_file), target))
            verify = os.path.join(os.path.dirname(real), "verify.md")
            # A verify.md planted as a link used to be a write anywhere you can write.
            return verify if inside(real, root) and not os.path.islink(verify) else None
    return None


def boxes(c):
    """AC-1: (live boxes, [(box, reason)] listed as yours), in scope file order."""
    live, yours = [], []
    for f in scope_files(c):
        for heading, raw, plain, deferred in wf.sections(wf.read(f)):
            if deferred or wf.GONE_TAG.search(heading):
                continue
            spec, fence = spec_of(f, plain, c.path), None
            for i, line in enumerate(plain):
                s = line.strip()
                if fence:
                    fence = None if s.startswith(fence) else fence
                    continue
                if s.startswith("```") or s.startswith("~~~"):
                    fence = s[:3]
                    continue
                m = wf.BOX.match(line)
                if not m or m.group(2) != " " or not wf.LIVE.search(m.group(3)):
                    continue
                b = LiveBox(c, f, heading, raw[i], wf.clean(m.group(3)).strip(), spec)
                b.spans = SPAN.findall(m.group(3))
                why = "live needs waits on you" if not wf.OWED.search(m.group(3)) else not_live(c.path, b.spans)
                (yours.append((b, why)) if why else live.append(b))
    return live, yours


def plan_steps(live):
    """AC-4: the steps by phase, an install once per repo and a check once per distinct command per repo."""
    steps = {}
    for b in live:
        span = b.spans[0].strip()
        phase, fields = shape(b.repo.path, span)
        s = Step(phase, b.repo, span, **fields)
        s = steps.setdefault(s.key(), s)
        s.boxes.append(b)
        b.steps.append(s)
    return [s for p in PHASES for s in steps.values() if s.phase == p]


def covered(args):
    """(repos, None), or (None, exit code)."""
    if args.target:
        c, rc = wf.resolve(args)
        if c is None:
            return None, rc
        problem = run.untrusted(c.path)
        return (None, refuse("untrusted", problem)) if problem else ([c], None)
    paths, problem = run.read_allowed()
    if problem:
        return None, refuse("untrusted", problem)
    repos = []
    for path in dict.fromkeys(os.path.realpath(p) for p in paths):
        try:
            c = wf.make_candidate(path) if os.path.isdir(path) else None
        except (OSError, StopIteration) as e:
            print(f"skipped: {wf.clean(path)}: scope unreadable: {wf.clean(str(e))}")
            continue
        if c is None:
            print(f"skipped: {wf.clean(path)}: no folder or no scope")
            continue
        repos.append(c)
    return repos, None


def backup(src, dst):
    """Copy src to dst, links kept as links, never overwriting a backup taken earlier."""
    if not os.path.lexists(src) or os.path.lexists(dst):
        if os.path.isdir(dst) and not os.path.islink(dst) and os.path.isdir(src) and not os.path.islink(src):
            for e in os.scandir(src):
                backup(e.path, os.path.join(dst, e.name))
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.islink(src):
        os.symlink(os.readlink(src), dst)
    elif os.path.isdir(src):
        os.makedirs(dst)
        for e in os.scandir(src):
            backup(e.path, os.path.join(dst, e.name))
    else:
        shutil.copy2(src, dst)



# -- staged setup and swap (spec 0020 AC-3, AC-4) ---------------------------------

def swap_lock():
    return os.path.join(run.state_dir(), "swap.lock")


def held_line(who):
    """AC-2: the one line for a held swap lock, from its holder line `<pid> <time> wf setup swap`."""
    words = who.split()
    return f"setup update already in progress, pid {words[0]} since {words[1]}" if len(words) >= 2 else \
        f"setup update already in progress, {who}"


def take_swap_lock():
    """(fd, None) holding the swap lock, or (None, holder line). Raises OSError."""
    os.makedirs(run.state_dir(), mode=0o700, exist_ok=True)
    return run.lock_file(swap_lock(), what="wf setup swap")


def copy_entry(src, dst):
    """src to dst, a link kept as a link, a folder whole, modes kept."""
    if os.path.islink(src):
        os.symlink(os.readlink(src), dst)
    elif os.path.isdir(src):
        shutil.copytree(src, dst, symlinks=True)
    else:
        shutil.copy2(src, dst)


def remove(p):
    if os.path.isdir(p) and not os.path.islink(p):
        shutil.rmtree(p)
    elif os.path.lexists(p):
        os.remove(p)


def make_stage(stage):
    """AC-3: a 0700 copy of the live dir's STAGED names, absent ones skipped."""
    os.makedirs(stage, mode=0o700)
    os.chmod(stage, 0o700)
    for n in STAGED:
        p = os.path.join(live_dir(), n)
        if os.path.lexists(p):
            copy_entry(p, os.path.join(stage, n))


def entries(root):
    """[rel] of every file and link under root, in walk order; a linked folder is not entered."""
    out = []
    for d, dirs, names in os.walk(root):
        dirs.sort()
        for n in sorted(names) + [x for x in dirs if os.path.islink(os.path.join(d, x))]:
            out.append(os.path.relpath(os.path.join(d, n), root))
    return out


def same(a, b):
    """AC-4: bytes and mode for a file, target for a link."""
    if os.path.islink(a) or os.path.islink(b):
        return os.path.islink(a) and os.path.islink(b) and os.readlink(a) == os.readlink(b)
    return os.path.isfile(b) and stat.S_IMODE(os.stat(a).st_mode) == stat.S_IMODE(os.stat(b).st_mode) \
        and filecmp.cmp(a, b, shallow=False)


def line2(path):
    try:
        with open(path, "rb") as f:
            return f.read().split(b"\n")[1:2]
    except OSError:
        return None


def hook_copies(repo, stage):
    """AC-4: [(checker, hook)] install.sh:159-187 would copy, with its replace rules; none without the names list."""
    if not os.path.exists(os.path.join(stage, "private", "names.txt")):
        return []
    # Plain git as install.sh runs it: wf.git sets core.hooksPath=/dev/null, which --git-path then names.
    try:
        r = subprocess.run(["git", "-C", repo, "rev-parse", "--git-path", "hooks"], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=wf.GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if r.returncode:
        return []
    hooks = os.path.join(repo, r.stdout.strip())
    checker = os.path.join(repo, "scripts", "private-names.py")
    out = []
    for h in HOOKS:
        dst = os.path.join(hooks, h)
        if os.path.islink(dst):
            act = os.path.realpath(dst) == os.path.realpath(checker)
        elif os.path.isfile(dst) and os.access(dst, os.X_OK) and filecmp.cmp(dst, checker, shallow=False):
            act = False
        elif os.path.isfile(dst) and line2(dst) == line2(checker):
            act = True
        else:
            act = not os.path.lexists(dst)
        if act:
            out.append((checker, dst))
    return out

def spec_paths_link(repo, home):
    """install.sh's spec-paths link (spec 0015 AC-6): [(link, target)], none when a real file is in the way."""
    link = os.path.join(home, ".local", "bin", "spec-paths")
    if os.path.exists(link) and not os.path.islink(link):
        print(f"  SKIP spec-paths (a real file is already at {link})")
        return []
    return [(link, os.path.join(repo, "scripts", "spec-paths.py"))]


def write_journal(path, renames, done):
    # Not a rename: a torn journal holds no rename that happened, and its asides are then strays (recover()).
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"renames": renames, "done": done}, f)


def renames_blocked(renames):
    """AC-4: every aside onto its live path with SIGINT, SIGHUP and SIGTERM blocked; a missing aside is skipped."""
    signal.pthread_sigmask(signal.SIG_BLOCK, SIGNALS)
    try:
        for a, d in renames:
            if os.path.lexists(a):
                os.replace(a, d)
    finally:
        signal.pthread_sigmask(signal.SIG_UNBLOCK, SIGNALS)


def swap(folder, stamp, stage, repos):
    """AC-4: rename the changed set into place. repos: the repos of the install steps, whose runner copy, bin links
    and git hooks install.sh left to wf under WF_STAGE. Order: journal, asides, ledger line, renames (runner folder,
    bin links, the rest, settings.local.json, settings.json). Nothing is deleted from the live dir. Raises OSError
    before any rename, the asides removed. Returns the number of renames."""
    live, home = live_dir(), os.path.expanduser("~")
    tail = [os.path.join(live, n) for n in SETTINGS_LAST]
    first, others, last, files, runners = {}, {}, {}, {}, []
    for c in repos:
        src = os.path.join(c.path, "runner")
        names = sorted(n for n in os.listdir(src) if n.endswith(".py")) if os.path.isdir(src) else []
        if names:
            dst = os.path.join(home, ".local", "share", "wf", runner_fp(src))
            runners.append(dst)
            # The ledger names every file of the copy, so a run accepts the new hook token's real path.
            files.update({os.path.join(dst, n): run.file_hash(os.path.join(src, n)) for n in names})
            if runner_checker(src):
                files[os.path.join(dst, "private-names.py")] = run.file_hash(runner_checker(src))
            if not os.path.isdir(dst):
                first[dst] = ("tree", src, dst, names)
            for link, target in runner_links(home, dst) + spec_paths_link(c.path, home):
                if not (os.path.islink(link) and os.readlink(link) == target):
                    first[link] = ("link", target, link, None)
                    # The content the link resolves to once the copy is in place: what the guard's file_hash reads.
                    files[link] = run.file_hash(os.path.join(src, "wf.py") if target.startswith(dst + "/") else target)
        for checker, hook in hook_copies(c.path, stage):
            others[hook] = ("hook", checker, hook, None)
            files[hook] = run.file_hash(checker)
    for rel in entries(stage):
        src, dst = os.path.join(stage, rel), os.path.join(live, rel)
        if os.path.lexists(dst) and same(src, dst):
            continue
        (last if dst in tail else others)[dst] = ("file", src, dst, None)
        files[dst] = run.file_hash(src)
    plan = list(first.values()) + list(others.values()) + sorted(last.values(), key=lambda x: tail.index(x[2]))
    if not plan:
        return 0
    renames = [[f"{d}.wf-swap-{stamp}", d] for _, _, d, _ in plan]
    journal = os.path.join(folder, "swap.json")
    write_journal(journal, renames, False)
    try:
        for (kind, src, dst, names), (aside, _) in zip(plan, renames):
            # AC-4: a backup of every changed path before the renames.
            rel = os.path.relpath(dst, live)
            backup(dst, os.path.join(folder, "claude", rel) if inside(dst, live) else
                   os.path.join(folder, "outside", dst.lstrip(os.sep)))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if kind == "tree":
                os.makedirs(aside)
                for n in names:
                    shutil.copy2(os.path.join(src, n), aside)
                if runner_checker(src):
                    shutil.copy2(runner_checker(src), os.path.join(aside, "private-names.py"))
            elif kind == "link":
                os.symlink(src, aside)
            else:
                copy_entry(src, aside)
                if kind == "hook":
                    os.chmod(aside, 0o755)
        fd = os.open(run.swaps_path(), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(json.dumps({"stamp": stamp, "pid": os.getpid(), "at": run.now(), "files": files}) + "\n")
    except OSError:
        for aside, _ in renames:
            remove(aside)
        write_journal(journal, renames, True)
        raise
    renames_blocked(renames)
    write_journal(journal, renames, True)
    for dst in runners:
        picked(home, dst)
    return len(renames)


def stray_places():
    """Where an aside can be: the staged parts of the live dir (links not entered), ~/.local/bin, ~/.local/share/wf.
    ponytail: a repo's git hooks folder is not walked; an aside left there by no journal stays until you delete it."""
    home, live = os.path.expanduser("~"), live_dir()
    for d in (os.path.join(home, ".local", "bin"), os.path.join(home, ".local", "share", "wf"), live):
        for n in os.listdir(d) if os.path.isdir(d) else ():
            yield os.path.join(d, n)
    for n in STAGED:
        top = os.path.join(live, n)
        if os.path.isdir(top) and not os.path.islink(top):
            for rel in entries(top):
                yield os.path.join(top, rel)
            for d, dirs, _ in os.walk(top):
                yield from (os.path.join(d, x) for x in dirs)


def recover():
    """AC-4, at a start, under the swap lock (held: left to its holder): a journal left `done: false` is finished
    forward when its ledger line exists, else its asides are deleted and nothing renamed; then every aside of a done
    journal and every aside named by no journal is deleted."""
    root = os.path.join(run.state_dir(), "finish")
    if not os.path.isdir(root):
        return
    fd, _ = take_swap_lock()
    if fd is None:
        return
    try:
        stamps, named = {st for st, _ in run.ledger()}, set()
        for path in sorted(glob.glob(os.path.join(glob.escape(root), "*", "swap.json"))):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                renames, done = [list(x) for x in data["renames"]], data["done"]
            except (OSError, ValueError, KeyError, TypeError):
                continue
            stamp = os.path.basename(os.path.dirname(path))
            named |= {a for a, _ in renames}
            if not done:
                if stamp in stamps:
                    renames_blocked(renames)
                    print(f"finished an interrupted swap from {wf.clean(stamp)}", flush=True)
                else:
                    print(f"dropped an interrupted swap from {wf.clean(stamp)}", flush=True)
                write_journal(path, renames, True)
            for a, _ in renames:
                remove(a)
        for p in list(stray_places()):
            if ".wf-swap-" in os.path.basename(p) and p not in named and os.path.lexists(p):
                remove(p)
    finally:
        os.close(fd)


def prune_stages():
    """AC-3: at most the KEEP_STAGES newest stage folders (failed ones, kept for you to read)."""
    stages = sorted(glob.glob(os.path.join(glob.escape(run.state_dir()), "finish", "*", "stage")))
    for d in stages[:-KEEP_STAGES]:
        shutil.rmtree(d, ignore_errors=True)


class Finish:
    def __init__(self, steps):
        self.steps = steps
        # Spec 0020 AC-4: the stamp names the journal, the ledger line and the asides, so it is never reused.
        while True:
            self.stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            self.folder = os.path.join(run.state_dir(), "finish", self.stamp)
            try:
                os.makedirs(self.folder, mode=0o700)
                break
            except FileExistsError:
                time.sleep(1)
        self.interrupted = False
        self.n = 0
        # The AC-2 line when another wf holds the swap lock.
        self.held = None
        # Spec 0020 AC-8: beside the builds the checks run in a thread, their output prefixed `[check]`.
        self.prefix, self.proc = b"", None

    def stop(self):
        """Spec 0020 AC-8: Ctrl C during the builds: SIGINT to the running check's group, no further check."""
        self.interrupted = True
        p = self.proc
        if p is not None and p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGINT)
            except ProcessLookupError:
                pass

    def run(self):
        """Spec 0019 AC-4, spec 0020 AC-3: the setup steps staged and swapped, then the checks, only when it passed."""
        print(f"backups and logs: {self.folder}", flush=True)
        if self.setup():
            self.checks()

    def setup(self):
        """Spec 0020 AC-3, AC-4: under the swap lock, the copy steps into a stage copy of the live dir, then each
        install step into it, then the swap. True when there was no setup step or the swap passed. A failed or held
        step leaves the live dir as it was; the failed stage is kept for you to read."""
        todo = [s for s in self.steps if s.phase != "check"]
        if not todo:
            return True
        fd, who = take_swap_lock()
        if fd is None:
            self.held = held_line(who)
            print(self.held, flush=True)
            return False
        swapped = False
        try:
            stage = os.path.join(self.folder, "stage")
            make_stage(stage)
            for phase in ("copy", "install"):
                for s in (s for s in todo if s.phase == phase):
                    if phase == "copy":
                        self.copy(s, stage)
                    else:
                        self.command(s, {"CLAUDE_LIVE_DIR": stage, "WF_STAGE": "1"})
                    if self.interrupted:
                        return False
                if any(s.result != "PASS" for s in todo if s.phase == phase):
                    return False
            repos = list({id(s.repo): s.repo for s in todo if s.phase == "install"}.values())
            swap(self.folder, self.stamp, stage, repos)
            swapped = True
            shutil.rmtree(stage)
            return True
        except OSError as e:
            print(f"swap failed: {wf.clean(str(e))}", flush=True)
            for s in todo:
                s.last = s.last if s.result == "FAIL" else f"swap: {e.strerror or e}"
            return False
        finally:
            # AC-4: a copy or install box counts as passed only once its swap is done.
            for s in todo:
                if not swapped and s.result == "PASS":
                    s.code, s.result, s.last = 1, "FAIL", s.last or "staged, not swapped"
            os.close(fd)
            prune_stages()

    def checks(self):
        for s in self.steps:
            if s.phase == "check":
                self.command(s)
                if self.interrupted:
                    return

    def copy(self, s, stage):
        print(f"copy: {s.repo.name}: {wf.clean(s.span)}", flush=True)
        dst = os.path.join(stage, s.rel)
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(s.src, dst)
            ok = filecmp.cmp(s.src, dst, shallow=False)
            s.last = "" if ok else "the copy differs from the source"
        except OSError as e:
            ok, s.last = False, f"{e.strerror or e}"
        s.code = 0 if ok else 1
        s.result = "PASS" if ok else "FAIL"

    def command(self, s, env=None):
        self.n += 1
        log = s.log = os.path.join(self.folder, f"step-{self.n:02d}.log")
        print(f"{self.prefix.decode()}{s.phase}: {s.repo.name}: {wf.clean(s.span)} (log {log})", flush=True)
        os.makedirs(self.folder, exist_ok=True)
        with open(log, "wb") as out:
            try:
                proc = subprocess.Popen(s.argv, cwd=s.repo.path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        start_new_session=True, env={**os.environ, **(env or {})})
            except OSError as e:
                s.code, s.result, s.last = 127, "FAIL", f"{e.strerror or e}"
                return
            self.proc = proc
            try:
                for chunk in iter(lambda: proc.stdout.readline(), b""):
                    sys.stdout.buffer.write(self.prefix + chunk)
                    sys.stdout.flush()
                    out.write(chunk)
                    if chunk.strip():
                        s.last = chunk.decode(errors="replace")
                proc.wait()
            except KeyboardInterrupt:
                # AC-4: the step runs in its own session, so Ctrl C reaches it only through here.
                self.interrupted = True
                os.killpg(proc.pid, signal.SIGINT)
                try:
                    proc.wait(GRACE)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                s.code, s.result = 130, "FAIL"
                return
            finally:
                self.proc = None
        if self.interrupted:
            s.code, s.result = 130, "FAIL"
            return
        s.code = proc.returncode if proc.returncode >= 0 else 128 - proc.returncode
        s.result = "PASS" if s.code == 0 else "FAIL"


def claude_version():
    try:
        r = subprocess.run(["claude", "--version"], capture_output=True, text=True, errors="replace", timeout=60)
        return wf.clean((r.stdout.split() or ["unknown"])[0]) if r.returncode == 0 else "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def record(steps, interrupted):
    """AC-5: one verify.md line per check result per feature spec. Returns the files written."""
    lines = {}
    version = None
    for s in steps:
        if s.phase != "check" or s.result is None or (interrupted and s.code == 130):
            continue
        version = version or claude_version()
        day = datetime.date.today().isoformat()
        result = "PASS" if s.result == "PASS" else \
            f"FAIL (exit {s.code}): {' '.join(wf.clean(s.last).split())[:200]}"
        for b in s.boxes:
            if b.spec is None:
                print(f"warning: {b.repo.name}: {b.feature}: no specs/<dir>/index.md link, result not recorded")
                continue
            line = f"- {day}, Claude Code {version}: `{s.span}` {result}"
            if line not in lines.setdefault(b.spec, []):
                lines[b.spec].append(line)
    for path, new in lines.items():
        text = wf.read(path) if os.path.exists(path) else ""
        rows = text.split("\n")
        if LIVE_HEADING not in rows:
            text = text.rstrip("\n") + ("\n\n" if text.strip() else "") + LIVE_HEADING + "\n\n" + "\n".join(new) + "\n"
        else:
            # Under the heading, before the next one, so a heading in the middle keeps its lines.
            i = rows.index(LIVE_HEADING) + 1
            end = next((j for j in range(i, len(rows)) if re.match(r"#{1,2}\s", rows[j])), len(rows))
            while end > i and not rows[end - 1].strip():
                end -= 1
            rows[end:end] = new
            text = "\n".join(rows)
            text = text if text.endswith("\n") else text + "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return list(lines)


def tick(live):
    """AC-6: [ ] to [x] on a box whose every step passed, when its line is still in its feature section."""
    changed = []
    for b in live:
        if not b.steps or any(s.result != "PASS" for s in b.steps):
            continue
        text = wf.read(b.scope_file)
        rows, pos, hit = text.split("\n"), 0, None
        for heading, raw, _, _ in wf.sections(text):
            start = rows.index(raw[0], pos)
            pos = start + 1
            if heading == b.heading and b.line in raw:
                hit = start + raw.index(b.line)
                break
        if hit is None:
            print(f"box changed, not ticked: {b.text}")
            continue
        rows[hit] = re.sub(r"\[ \]", "[x]", rows[hit], count=1)
        with open(b.scope_file, "w", encoding="utf-8") as f:
            f.write("\n".join(rows))
        changed.append(b.scope_file)
    return changed


def commit(c, files, ran):
    """AC-7: one local commit of only these files, never on main, master or a detached head. True when fine."""
    name = wf.branch(c.path)
    if name in ("main", "master", "no git", "no commits") or name.startswith("detached"):
        print(f"edits left uncommitted on {name}")
        return True
    rel = [os.path.relpath(f, c.path) for f in files]
    msg = f"chore(wf): wf finish ran {ran} live step(s)"
    # Plain git, not wf.git: the repo's own commit hooks run as they do for you.
    for argv in (["git", "-C", c.path, "add", "--", *rel], ["git", "-C", c.path, "commit", "-m", msg, "--", *rel]):
        for n in range(COMMIT_TRIES + 1):
            r = subprocess.run(argv, capture_output=True, text=True, errors="replace", stdin=subprocess.DEVNULL)
            err = wf.clean((r.stderr or r.stdout).strip())
            # Spec 0020 AC-8: a build beside this one holds git's index lock for a moment.
            if not r.returncode or "index.lock" not in err:
                break
            if n < COMMIT_TRIES:
                time.sleep(COMMIT_GAP)
        if r.returncode and "index.lock" in err:
            print(f"edits left uncommitted in {c.name}: {err}")
            return False
        if r.returncode:
            print(f"commit failed in {c.name}: {err}")
            return False
    print(f"committed in {c.name}: {msg}")
    return True


def seen():
    try:
        report.mark_seen()
    except OSError as e:
        print(f"warning: report.seen not written: {e.strerror or e}")


def cmd_finish(args):
    if os.environ.get("WF_RUN"):
        return refuse("unattended", "wf finish runs only at your keyboard, never inside a wf run call")
    if not args.yes and not os.isatty(0):
        return refuse("no_tty", "stdin is not a terminal, pass -y to run without the confirm prompt")
    try:
        repos, rc = covered(args)
    except KeyboardInterrupt:
        print()
        return 130
    if repos is None:
        return rc
    # Spec 0020 AC-4: an interrupted swap is finished forward or dropped before anything is planned.
    try:
        recover()
    except OSError as e:
        print(f"warning: interrupted swap not finished: {e.strerror or e}")
    live, yours = [], []
    for c in repos:
        try:
            more, mine = boxes(c)
        except (OSError, StopIteration) as e:
            print(f"skipped: {c.name}: scope unreadable: {wf.clean(str(e))}")
            continue
        live += more
        yours += mine
    steps = plan_steps(live)
    for s in steps:
        features = ", ".join(dict.fromkeys(b.feature for b in s.boxes))
        print(f"{s.phase}: {s.repo.name}: {features}: {wf.clean(s.span)}")
    for b, why in yours:
        print(f"yours: {b.repo.name}: {b.feature}: {b.text} ({wf.clean(why)})")
    if not steps:
        print("no live steps")
        seen()
        return 0
    if not args.yes:
        try:
            if input("Enter to run these steps, anything else cancels: ") != "":
                return 130
        except (EOFError, KeyboardInterrupt):
            print()
            return 130
    f = Finish(steps)
    try:
        f.run()
    except KeyboardInterrupt:
        # Ctrl C between steps (a copy or a backup): no further step runs.
        f.interrupted = True
    ok = True
    for c in repos:
        mine = [s for s in steps if s.repo is c]
        files = record(mine, f.interrupted) + tick([b for b in live if b.repo is c])
        if files:
            ok = commit(c, list(dict.fromkeys(files)), sum(s.result is not None for s in mine)) and ok
    for s in steps:
        print(f"{s.result or 'FAIL'}: {s.repo.name}: {wf.clean(s.span)}" + ("" if s.result else " (not run)")
              + (f" (log {s.log})" if s.result == "FAIL" and s.log else ""))
    passed = all(s.result == "PASS" for s in steps)
    # Spec 0020 AC-10: one command.
    print("next: wf" if passed else "next: fix the FAIL lines, then wf")
    if f.interrupted:
        return 130
    seen()
    return 0 if passed and ok else 1


# -- bare `wf` (spec 0020 AC-1, AC-2, AC-6 to AC-8, AC-13) -----------------------

def picks(text, n):
    """AC-13: the 1-based numbers in `1 2 4` or `1-3,5`, each on the list of n, else None (cancel)."""
    out = []
    for t in re.split(r"[,\s]+", text.strip()):
        if not PICK.fullmatch(t):
            return None
        a, _, b = t.partition("-")
        lo, hi = int(a), int(b or a)
        if not 1 <= lo <= hi <= n:
            return None
        out += range(lo, hi + 1)
    return sorted(set(out)) or None


def section(name, lines):
    if lines:
        print(f"{name}:")
        for line in lines:
            print("  " + line)


def retakes(args, repos):
    """AC-6: ([(park, what changed)] to take back, [(park, retaken on)] kept) over the trusted repos' parks."""
    q = run.queue_transact()
    paths = {c.path for c in repos}
    mine = [p for p in q["parks"] if p["repo"] in paths]
    newest = run.newest_setup()
    version = run.claude_version() if any(p["reason"] in run.SETUP_PARKS for p in mine) else None
    back, kept = [], []
    for p in mine:
        why = run.what_changed(p, newest, version)
        # A cap park clears in the build by applies(); `wf` only names it.
        if why is None and run.cap_park(p) and p["cap"] is not None and getattr(args, p["reason"]) > p["cap"]:
            why = run.retaken_on(p)
        (back.append((p, why)) if why else kept.append((p, run.retaken_on(p))))
    return back, kept


def usage_fit(numbered, chosen=None):
    """Spec 0022 AC-5 to AC-7: usage.plan over the numbered features (the chosen ones when given), with a week
    percent for every numbered line it covers; None with nothing numbered. Any failure reads as unknown, starts now."""
    if not numbered:
        return None
    # Imported here: install.sh loads this module from a runner folder that may not hold usage.py yet.
    import usage
    idx = list(range(len(numbered))) if not chosen else [i - 1 for i in chosen]
    try:
        picked = []
        for i in idx:
            h, name = numbered[i]
            _, feats = run.repo_features(h["c"].path, h["c"].scope_dir)
            picked.append((h["c"].path, next(f for f in feats if f.name == name)))
        fit = usage.plan(picked)
    except Exception as e:
        return {"lines": [f"unknown ({type(e).__name__}), starts now"], "start": None, "week": [None] * len(numbered)}
    week = [None] * len(numbered)
    for i, w in zip(idx, fit["week"]):
        week[i] = w
    return {**fit, "week": week}


def cmd_wf(args):
    """AC-1: the one command. Refusals, an interrupted swap finished, the screen, one confirm, then report seen,
    the setup swap, the retakes, the builds side by side and the checks beside them, records, ticks, commits."""
    if os.environ.get("WF_RUN"):
        return refuse("unattended", "wf runs only at your keyboard, never inside a wf run call")
    if not args.yes and not os.isatty(0):
        return refuse("no_tty", "stdin is not a terminal, pass -y to run without the confirm prompt")
    try:
        recover()
    except OSError as e:
        print(f"warning: interrupted swap not finished: {e.strerror or e}")
    try:
        repos, rc = covered(types.SimpleNamespace(target=None))
        if repos is None:
            return rc
        live, yours = [], []
        for c in repos:
            try:
                more, mine = boxes(c)
            except (OSError, StopIteration) as e:
                print(f"skipped: {c.name}: scope unreadable: {wf.clean(str(e))}")
                continue
            live += more
            yours += mine
        steps = plan_steps(live)
        fd, who = run.lock_file(swap_lock(), create=False)
        if fd is not None:
            os.close(fd)
        # AC-3: the swap lock matters only when there is a setup step to swap.
        held = held_line(who) if who and any(s.phase != "check" for s in steps) else None
        try:
            back, kept = retakes(args, repos)
        except run.QueueError as e:
            return refuse("queue_unreadable", e)
        # AC-2, AC-7: the build plan bare `wf run` prints, no repo lock kept, the retaken parks planned as gone.
        r = run.Run(None, args)
        r.retaken = {(p["repo"], p["feature"]) for p, _ in back}
        out = StringIO()
        with redirect_stdout(out):
            refused = r.bare_checks()
            if refused is None:
                r.plan()
    except KeyboardInterrupt:
        print()
        return 130
    work = [h for h in r.held if h.get("has_work")] if refused is None else []
    numbered = [(h, name) for h in work for name in h["queued"]]
    text, seen_path, _ = report.paths()
    shown = report.read_text(text) if not os.path.exists(seen_path) else None
    killed = report.killed_line()
    setup = [s for s in steps if s.phase != "check"]
    checks = [s for s in steps if s.phase == "check"]
    line = lambda s: f"{s.phase}: {s.repo.name}: {', '.join(dict.fromkeys(b.feature for b in s.boxes))}: {wf.clean(s.span)}"
    section("report", (report.shown(shown).split("\n") if shown else []) + ([killed] if killed else []))
    if not (setup or checks or back or work):
        if refused is not None:
            section("build", out.getvalue().rstrip("\n").split("\n"))
        print("nothing to do")
        seen()
        return 0
    section("setup", [held] if held and setup else [line(s) for s in setup])
    section("checks", [held] if held and checks else [line(s) for s in checks])
    name = lambda p: wf.clean(os.path.basename(p["repo"]))
    section("retake", [f"{name(p)}: {p['feature']}: {p['reason']} ({why})" for p, why in back])
    section("parked", [f"{name(p)}: {p['feature']}: {p['reason']}: retaken on {on}" for p, on in kept])
    # Spec 0022 AC-8: --only picks before the fit is worked out.
    fit = usage_fit(numbered, picks(args.only, len(numbered)) if args.only is not None and numbered else None)
    section("build", [x for x in out.getvalue().rstrip("\n").split("\n") if x] +
            [f"{n}. {h['c'].name}: {f}" + (f" ~{fit['week'][n - 1]:.0f}% week" if fit and fit["week"][n - 1] is not None
                                            else "") for n, (h, f) in enumerate(numbered, 1)])
    # AC-7: after build, when there is one.
    section("usage", fit["lines"] if fit else [])
    start = fit and fit["start"]
    section("running", [f"{e['name']}: {e['skip'][len('running: '):]}" for e in r.record["repos"]
                        if (e["skip"] or "").startswith("running: ")])
    section("yours", [f"{b.repo.name}: {b.feature}: {b.text} ({wf.clean(why)})" for b, why in yours])
    sys.stdout.flush()
    chosen = None
    try:
        if args.only is not None:
            chosen = picks(args.only, len(numbered))
            if chosen is None:
                print(f"not on the list: {wf.clean(args.only)}")
                return 130
        if not args.yes and start is not None:
            # AC-8: a run that does not fit waits, never refuses; numbers pick, now starts at once.
            answer = input(f"Enter waits and starts at {start.astimezone().strftime('%a %H:%M')}, numbers to pick (1 2 4 or 1-3,5), "
                           "now starts at once, anything else cancels: ")
            if answer.strip().casefold() == "now":
                start = None
            elif answer != "":
                chosen = picks(answer, len(numbered))
                if chosen is None:
                    return 130
                fit = usage_fit(numbered, chosen)
                section("usage", fit["lines"])
                start = fit["start"]
        elif not args.yes:
            ask = "Enter for all, numbers to pick (1 2 4 or 1-3,5), anything else cancels: " \
                if numbered and chosen is None else "Enter to go, anything else cancels: "
            answer = input(ask)
            if answer != "":
                chosen = picks(answer, len(numbered)) if numbered and chosen is None else None
                if chosen is None:
                    return 130
    except (EOFError, KeyboardInterrupt):
        print()
        return 130
    # AC-13: a repo with no picked feature gets no child; the others stay queued.
    if chosen is not None:
        wanted = [numbered[i - 1] for i in chosen]
        for h in work:
            h["only"] = [f for g, f in wanted if g is h]
            h["has_work"] = bool(h["only"])
    seen()
    f = Finish(steps) if steps else None
    swapped = not setup
    if setup and not held:
        print(f"backups and logs: {f.folder}", flush=True)
        try:
            swapped = f.setup()
        except KeyboardInterrupt:
            f.interrupted, swapped = True, False
    # AC-6: under queue.lock only.
    if back:
        gone = {(p["repo"], p["feature"], p["parked_at"]) for p, _ in back}
        try:
            run.queue_transact(lambda q: q.update(parks=[p for p in q["parks"] if
                                                          (p["repo"], p["feature"], p["parked_at"]) not in gone]) or True)
        except run.QueueError as e:
            print(f"warning: retakes not written: {wf.clean(str(e))}")
    child = None
    run_checks = f is not None and checks and swapped and not held
    if any(h.get("has_work") for h in work):
        # AC-8: the checks run in the parent beside the children, one at a time.
        t = None
        if run_checks:
            f.prefix = b"[check] "
            t = threading.Thread(target=f.checks, daemon=True)
            t.start()
        child = run.parallel(r, on_signal=f.stop if f else None, start=start)
        if t:
            t.join()
    elif run_checks:
        try:
            f.checks()
        except KeyboardInterrupt:
            f.interrupted = True
    ok = True
    for c in repos:
        mine = [s for s in steps if s.repo is c]
        files = record(mine, bool(f and f.interrupted)) + tick([b for b in live if b.repo is c])
        if files:
            ok = commit(c, list(dict.fromkeys(files)), sum(s.result is not None for s in mine)) and ok
    failed = [s for s in steps if s.result == "FAIL" or (s.result is None and not held)]
    for s in failed:
        print(f"FAIL: {s.repo.name}: {wf.clean(s.span)}" + (f" (log {s.log})" if s.log else " (not run)"))
    if (f and f.interrupted) or r.interrupted or child == 130:
        return 130
    if child:
        return 6
    return 1 if failed or not ok else 5 if refused is not None else 0
