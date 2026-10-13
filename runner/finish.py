# `wf finish` (spec 0019): the live setup steps waiting on you, run at your keyboard after one Enter.
# Unattended calls never write ~/.claude, so these used to pile up as separate boxes run by hand.
import datetime
import fcntl
import filecmp
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys

import run
import wf

SPAN = re.compile(r"`([^`]+)`")
SPEC_LINK = re.compile(r"(?:^|/)specs/[^/]+/index\.md$")
PROBE = re.compile(r"docs/specs/[^/]+/probes/[^/]+")
# What install.sh overwrites (AC-4).
INSTALL_BACKUP = ("rules", "agents", "hooks", "scripts", "settings.json")
NEVER_COPIED = ("settings.json", "settings.local.json")
PHASES = ("copy", "install", "check")
GRACE = 30
LIVE_HEADING = "## Live runs (wf finish)"


def refuse(reason, detail):
    print(f"refused: {reason}: {wf.clean(str(detail))}", flush=True)
    return 5


def live_dir():
    return os.path.realpath(os.path.expanduser(os.environ.get("CLAUDE_LIVE_DIR") or "~/.claude"))


def inside(path, root):
    return path == root or path.startswith(root + os.sep)


def repo_file(root, arg):
    """The real path of a repo file named by arg, else None: present, a regular file, inside the repo."""
    p = os.path.join(root, os.path.expanduser(arg))
    real = os.path.realpath(p)
    return real if inside(real, root) and os.path.isfile(real) else None


class Step:
    def __init__(self, phase, repo, span, argv=None, src=None, dst=None, rel=None):
        self.phase, self.repo, self.span = phase, repo, span
        self.argv, self.src, self.dst, self.rel = argv, src, dst, rel
        self.boxes, self.result, self.code, self.last = [], None, None, ""

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
        if os.path.realpath(os.path.join(root, os.path.expanduser(t[2]))) != dst:
            return None
        return "copy", {"src": src, "dst": dst, "rel": rel}
    if t == ["./install.sh"] and repo_file(root, "install.sh"):
        return "install", {"argv": t}
    if t in (["python3", "runner/e2e/run.py"], ["python3", "runner/e2e/run.py", "--parallel"]) \
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
            return os.path.join(os.path.dirname(real), "verify.md") if inside(real, root) else None
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


def lock_all(repos):
    """AC-3: refuse while any wf lock is held, then hold every covered repo's. (fds, None) or (None, exit code)."""
    locks = os.path.join(run.state_dir(), "locks")
    try:
        os.makedirs(locks, mode=0o700, exist_ok=True)
        for name in sorted(os.listdir(locks)):
            if not name.endswith(".lock"):
                continue
            try:
                fd = os.open(os.path.join(locks, name), os.O_RDONLY)
            except FileNotFoundError:
                continue
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return None, refuse("locked", f"a wf run is going: {run.holder(fd)}")
            finally:
                os.close(fd)
        fds = []
        for c in repos:
            fd, who = run.repo_lock(c.path)
            if who:
                return None, refuse("locked", f"a wf run is going: {who}")
            fds.append(fd)
    except OSError as e:
        return None, refuse("state_unwritable", f"{run.state_dir()}: {e.strerror or e}")
    return fds, None


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


class Finish:
    def __init__(self, steps):
        self.steps = steps
        self.folder = os.path.join(run.state_dir(), "finish", datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        self.interrupted = False
        self.n = 0

    def run(self):
        """AC-4: each phase in order; a failed copy or install ends the phases, a failed check does not."""
        print(f"backups and logs: {self.folder}", flush=True)
        for phase in PHASES:
            todo = [s for s in self.steps if s.phase == phase]
            if not todo:
                continue
            if phase == "copy":
                for s in todo:
                    backup(s.dst, os.path.join(self.folder, "claude", s.rel))
            if phase == "install":
                for name in INSTALL_BACKUP:
                    backup(os.path.join(live_dir(), name), os.path.join(self.folder, "claude", name))
            for s in todo:
                self.copy(s) if phase == "copy" else self.command(s)
                if self.interrupted:
                    return
            if phase != "check" and any(s.result != "PASS" for s in todo):
                return

    def copy(self, s):
        print(f"copy: {s.repo.name}: {wf.clean(s.span)}", flush=True)
        try:
            os.makedirs(os.path.dirname(s.dst), exist_ok=True)
            shutil.copyfile(s.src, s.dst)
            ok = filecmp.cmp(s.src, s.dst, shallow=False)
            s.last = "" if ok else "the copy differs from the source"
        except OSError as e:
            ok, s.last = False, f"{e.strerror or e}"
        s.code = 0 if ok else 1
        s.result = "PASS" if ok else "FAIL"

    def command(self, s):
        self.n += 1
        log = os.path.join(self.folder, f"step-{self.n:02d}.log")
        print(f"{s.phase}: {s.repo.name}: {wf.clean(s.span)} (log {log})", flush=True)
        os.makedirs(self.folder, exist_ok=True)
        with open(log, "wb") as out:
            try:
                proc = subprocess.Popen(s.argv, cwd=s.repo.path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        start_new_session=True)
            except OSError as e:
                s.code, s.result, s.last = 127, "FAIL", f"{e.strerror or e}"
                return
            try:
                for chunk in iter(lambda: proc.stdout.readline(), b""):
                    sys.stdout.buffer.write(chunk)
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
        r = subprocess.run(argv, capture_output=True, text=True, errors="replace")
        if r.returncode:
            print(f"commit failed in {c.name}: {wf.clean((r.stderr or r.stdout).strip())}")
            return False
    print(f"committed in {c.name}: {msg}")
    return True


def seen():
    try:
        open(os.path.join(run.state_dir(), "report.seen"), "a").close()
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
    fds, rc = lock_all(repos)
    if fds is None:
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
        print(f"{s.result or 'FAIL'}: {s.repo.name}: {wf.clean(s.span)}" + ("" if s.result else " (not run)"))
    passed = all(s.result == "PASS" for s in steps)
    print("next: wf run" if passed else "next: fix the FAIL lines, then wf finish")
    if f.interrupted:
        return 130
    seen()
    return 0 if passed and ok else 1
