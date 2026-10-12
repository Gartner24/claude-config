#!/usr/bin/env python3
# The workflow runner (spec 0001). Stdlib only, so a fresh clone works with no
# install step. Subcommands: `list`/`next` (spec 0002), `run` (0004, in run.py),
# `ntfy` (0005, in ntfy.py).
import argparse
import math
import os
import re
import shlex
import shutil
import subprocess
import sys

SCOPE_BASES = ("docs/scope", ".workflow/scope")
SCOPE_FILES = ("scope.md", "index.md")

BOX = re.compile(r"^(\s*)[-*+]\s+\[([ xX])\]\s?(.*)$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
GONE_TAG = re.compile(r"\(\s*(done|existing|dropped)\s*\)|\u00b7\s*(done|existing|dropped)\s*(?=\u00b7|$)", re.I)
DISPLAY_TAG = re.compile(r"\s*\u00b7[^\u00b7]*|\s*\(\s*(done|existing|dropped|planned|in-progress|needs a decision)\s*\)", re.I)
COMMAND = re.compile(r"^/[a-z][\w:-]*(\s|$)")
WAITING = re.compile(r"\b(after|waits on)\b", re.I)
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
# Scope header contract (spec 0003): field -> (display name, valid values, default).
HEADER_LINE = re.compile(r"^\*\*(Source of truth|Autopilot):\*\*\s*(.*)$", re.I)
HEADER_FIELDS = {"source of truth": ("Source of truth", ("scope", "issues", "mixed"), "scope"),
                 "autopilot": ("Autopilot", ("allowed", "off"), "off")}
# Spec 0011 AC-2: only a feature carrying it runs under wf run.
AUTO_TAG = re.compile(r"·\s*auto\s*(?=·|$)", re.I)
# A box only you can close (spec 0012). The `after` / `waits on` words missed a
# manual check once and a wf run looped /develop on it.
OWED = re.compile(r"·\s*waits on you\s*(?=·|$)", re.I)
NEAR_OWED = re.compile(r"waits on you", re.I)
# C0 and C1 control characters. Scope text and folder names come from repos you
# may have cloned; an ESC or CR in them used to reach the terminal and fzf as is.
# Lone surrogates are undecodable bytes in a folder name; printing one used to
# crash with UnicodeEncodeError under a UTF-8 locale.
CONTROL = re.compile(r"[\x00-\x1f\x80-\x9f\udc80-\udcff]")
# A detached HEAD: SHA-1 or SHA-256.
COMMIT_HASH = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
# A planted core.fsmonitor or hook in a scanned repo used to run on `git status`.
GIT_SAFE = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")
# `wf run` swaps in the absolute path it resolved at start (spec 0007 AC-6).
GIT = "git"


def clean(text):
    return CONTROL.sub("", text)


class Box:
    def __init__(self, indent, is_open, text, feature, parent, skip):
        self.indent, self.open, self.text = indent, is_open, text
        self.feature, self.parent, self.skip = feature, parent, skip

    def command(self):
        for span in re.findall(r"`([^`]+)`", self.text):
            if COMMAND.match(span):
                return span.strip()
        return None


def owed_text(box):
    return OWED.sub("", box.text).strip() if box and OWED.search(box.text) else None


class NextBox:
    def __init__(self, box, command, note_box):
        self.feature = DISPLAY_TAG.sub("", box.feature).strip() if box.feature else None
        note = note_box.text if note_box else None
        self.box_text, self.command, self.note = box.text, command, note
        self.owed = owed_text(box) or owed_text(note_box)
        self.waiting = self.owed is not None or bool(note and WAITING.search(note))
        texts = dict.fromkeys(b.text for b in (box, note_box) if b)
        self.near_misses = [t for t in texts if NEAR_OWED.search(t) and not OWED.search(t)]


def uncomment(text):
    # Comments go first, keeping their newlines so later lines stay in place.
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)


def header_warnings(text):
    return read_header(text)[1]


def header_values(text):
    """{"source of truth": value, "autopilot": value}, defaults filled in."""
    return read_header(text)[0]


def read_header(text):
    values = {k: f[2] for k, f in HEADER_FIELDS.items()}
    seen, warnings, fence = set(), [], None
    for line in uncomment(text).splitlines():
        s = line.strip()
        if fence:
            if s.startswith(fence):
                fence = None
            continue
        if s.startswith("```") or s.startswith("~~~"):
            fence = s[:3]
            continue
        h = HEADING.match(line)
        if (h and len(h.group(1)) in (2, 3)) or BOX.match(line):
            break
        m = HEADER_LINE.match(line)
        if not m:
            continue
        key = m.group(1).lower()
        name, valid, default = HEADER_FIELDS[key]
        if key in seen:
            msg = f"{name} set twice, using the first"
            if msg not in warnings:
                warnings.append(msg)
            continue
        seen.add(key)
        value = (m.group(2).split() or [""])[0].strip(".,;:!?()[]*_\"'").lower()
        if value in valid:
            values[key] = value
        else:
            warnings.append(f"unknown {name} value '{clean(value)}', using {default}")
    return values, warnings


def parse_text(text):
    text = uncomment(text)
    boxes, stack = [], []
    feature, gone, deferred, fence = None, False, False, None
    for line in text.splitlines():
        s = line.strip()
        if fence:
            if s.startswith(fence):
                fence = None
            continue
        if s.startswith("```") or s.startswith("~~~"):
            fence = s[:3]
            continue
        h = HEADING.match(line)
        if h and len(h.group(1)) <= 3:
            level, heading = len(h.group(1)), clean(h.group(2))
            stack = []
            feature = heading if level == 3 else None
            gone = bool(feature and GONE_TAG.search(feature))
            if level == 2:
                deferred = heading.lower().startswith("deferred")
            continue
        b = BOX.match(line)
        if not b:
            continue
        indent = len(b.group(1))
        while stack and stack[-1].indent >= indent:
            stack.pop()
        box = Box(indent, b.group(2) == " ", clean(b.group(3)).strip(), feature, stack[-1] if stack else None, gone or deferred)
        stack.append(box)
        boxes.append(box)
    return boxes


def sections(text):
    """Spec 0011 AC-3: (heading, raw lines, uncommented lines, under ## Deferred) per level 3 heading,
    from the heading to the next heading of level 1 to 3 or the end. Raw lines keep comments, so
    editing a comment changes the hash; headings inside a fence or a comment do not count."""
    raw, plain = text.split("\n"), uncomment(text).split("\n")
    starts, fence, deferred = [], None, False
    for i, line in enumerate(plain):
        s = line.strip()
        if fence:
            if s.startswith(fence):
                fence = None
            continue
        if s.startswith("```") or s.startswith("~~~"):
            fence = s[:3]
            continue
        h = HEADING.match(line)
        if not h or len(h.group(1)) > 3:
            continue
        level, heading = len(h.group(1)), clean(h.group(2))
        if level == 2:
            deferred = heading.lower().startswith("deferred")
        starts.append((i, heading if level == 3 else None, deferred))
    starts.append((len(raw), None, False))
    return [(h, raw[i:j], plain[i:j], d) for (i, h, d), (j, _, _) in zip(starts, starts[1:]) if h is not None]


def under(box, ancestor):
    while box.parent:
        box = box.parent
        if box is ancestor:
            return True
    return False


def pick_next(boxes):
    first = next((b for b in boxes if b.open and not b.skip), None)
    if first is None:
        return None
    # ponytail: a milestone is any box with a less indented box above it, so a
    # later sibling milestone still runs the parent command (spec AC-6 intent).
    if first.parent:
        return NextBox(first, first.parent.command(), first)
    note = next((b for b in boxes if b.open and under(b, first)), None)
    return NextBox(first, first.command(), note)


def open_rows(text):
    rows, in_glance, header = [], False, False
    for line in text.splitlines():
        if line.startswith("#"):
            in_glance, header = "at a glance" in line.lower(), True
            continue
        if not (in_glance and line.strip().startswith("|")):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header:
            header = False
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        words = cells[-1].lower().split()
        if words and words[0] in ("done", "dropped", "existing"):
            continue
        rows.append(clean(" | ".join(cells)))
    return rows


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def git(path, *args):
    try:
        return subprocess.run([GIT, *GIT_SAFE, "-C", path, *args], capture_output=True, text=True, errors="replace")
    except FileNotFoundError:
        return None


def dot_git(path):
    """The git folder of a checkout: its .git folder, or the one its .git file names. Raises OSError."""
    dot = os.path.join(path, ".git")
    if os.path.isfile(dot):
        dot = os.path.join(path, read(dot).strip().removeprefix("gitdir:").strip())
    return dot


def head_branch(path):
    # `git status` runs a repo's own filter drivers, so --list and the picker
    # read HEAD from the files and never run git in a scanned repo.
    try:
        head = read(os.path.join(dot_git(path), "HEAD")).strip()
    except OSError:
        return "no git"
    if head.startswith("ref: refs/heads/"):
        name = head[len("ref: refs/heads/"):]
        # reftable repos keep the real HEAD elsewhere and write this placeholder
        return "-" if name in ("", ".invalid") else clean(name)
    # an empty or unknown HEAD used to show "detached " with no sha
    return "detached " + head[:7] if COMMIT_HASH.fullmatch(head) else "-"


def branch(path):
    r = git(path, "rev-parse", "--abbrev-ref", "HEAD")
    if r is None:
        return "no git"
    if r.returncode == 0:
        name = r.stdout.strip()
        if name != "HEAD":
            return clean(name)
        return "detached " + git(path, "rev-parse", "--short", "HEAD").stdout.strip()
    return "no commits" if git(path, "rev-parse", "--git-dir").returncode == 0 else "no git"


def changes(path):
    r = git(path, "status", "--porcelain")
    if r is None or r.returncode:
        return "-"
    n = len(r.stdout.splitlines())
    return "1 change" if n == 1 else f"{n} changes"


def worktrees(main):
    """Real paths of a main checkout's linked worktrees, read from git's files (AC-2)."""
    # This used to run `git worktree list`, which runs git in every scanned repo.
    base = os.path.join(main, ".git", "worktrees")
    try:
        ids = sorted(os.listdir(base))
    except OSError:
        return []
    out = []
    for i in ids:
        entry = os.path.join(base, i)
        try:
            # <id>/gitdir is relative to <id>, unlike a .git file's path
            wt = os.path.dirname(os.path.join(entry, read(os.path.join(entry, "gitdir")).strip()))
            # skips prunable entries, and a folder reused after its worktree was deleted
            if os.path.realpath(dot_git(wt)) == os.path.realpath(entry):
                out.append(os.path.realpath(wt))
        except OSError:
            continue
    return out


def worktree_label(path):
    if not os.path.isfile(os.path.join(path, ".git")):
        return ""
    try:
        gd = dot_git(path)
    except OSError:
        return ""
    # a submodule's git folder has no commondir
    if not os.path.isfile(os.path.join(gd, "commondir")):
        return ""
    try:
        head = read(os.path.join(gd, "HEAD")).strip()
    except OSError:
        head = ""
    if head.startswith("ref: refs/heads/") and head != "ref: refs/heads/.invalid":
        return f"worktree {clean(head[len('ref: refs/heads/'):])}"
    if COMMIT_HASH.fullmatch(head):
        return "worktree (detached)"
    return "worktree (branch unknown)"


def find_scope(path):
    found = [b for b in SCOPE_BASES if any(os.path.isfile(os.path.join(path, b, f)) for f in SCOPE_FILES)]
    if not found:
        return None, []
    warnings = ["both docs/scope and .workflow/scope exist, using docs/scope"] if len(found) == 2 else []
    return found[0], warnings


def epics(folder, text, warnings):
    real_folder, seen = os.path.realpath(folder), []
    for link in LINK.findall(text):
        target = link.split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:") or not target.endswith(".md"):
            continue
        f = os.path.realpath(os.path.join(folder, target))
        if not f.startswith(real_folder + os.sep) or f in seen:
            continue
        seen.append(f)
        if os.path.isfile(f):
            yield f
        else:
            warnings.append(f"missing epic file {clean(target)}")


def load_scope(folder, warnings):
    """(top file text, boxes). Raises StopIteration or OSError when the scope is gone."""
    main = next(os.path.join(folder, f) for f in SCOPE_FILES if os.path.isfile(os.path.join(folder, f)))
    text = read(main)
    if not main.endswith("index.md"):
        return text, parse_text(text)
    boxes = []
    for f in epics(folder, text, warnings):
        boxes += parse_text(read(f))
    return text, boxes


class Candidate:
    def __init__(self, path, scope_dir, warnings):
        self.path, self.scope_dir, self.warnings = path, scope_dir, warnings
        self.name = clean(os.path.basename(path))
        self.label = worktree_label(path)
        self.text, boxes = load_scope(os.path.join(path, scope_dir), self.warnings)
        first = next((l for l in self.text.splitlines() if l.startswith("#")), "")
        self.title = first[len("# Scope:"):].strip() if first.startswith("# Scope:") else None
        self.is_hub = not boxes
        if not self.is_hub:
            self.warnings += header_warnings(self.text)
        self.next = pick_next(boxes)
        for t in self.next.near_misses if self.next else []:
            self.warnings.append(f'"waits on you" is not the marker here, end the box with " · waits on you": {t}')

    def display_name(self):
        return f"{self.name} ({self.label})" if self.label else self.name

    def columns(self):
        nb = self.next
        cmd = "nothing to run" if nb is None else nb.command or "no command"
        feature = nb.feature if nb and nb.feature else ""
        return [self.name, self.label, feature, cmd, head_branch(self.path), "-"]


def make_candidate(path):
    path = os.path.realpath(path)
    scope_dir, warnings = find_scope(path)
    return Candidate(path, scope_dir, warnings) if scope_dir else None


def scan_roots():
    env = os.environ.get("WF_ROOTS")
    if env:
        return [(os.path.expanduser(p), 0, 3) for p in env.split(":") if p]
    home = os.path.expanduser("~")
    return [(home, 1, 1), (os.path.join(home, "projects"), 0, 3)]


def walk(folder, lo, hi, depth=0):
    if depth >= lo:
        yield folder
    if depth == hi:
        return
    try:
        entries = sorted(os.scandir(folder), key=lambda e: e.name)
    except OSError:
        return
    for e in entries:
        if not e.name.startswith(".") and e.name != "node_modules" and e.is_dir():
            yield from walk(e.path, lo, hi, depth + 1)


def discover():
    found = {}
    for root, lo, hi in scan_roots():
        for d in walk(root, lo, hi):
            real = os.path.realpath(d)
            if real not in found:
                found[real] = make_candidate(real)
    for c in [c for c in found.values() if c and os.path.isdir(os.path.join(c.path, ".git"))]:
        for wt in worktrees(c.path):
            if wt not in found:
                found[wt] = make_candidate(wt)
    return [c for c in found.values() if c]


def match(cands, name):
    needle = name.lower()
    keys = lambda c: (c.name.lower(), (c.title or "").lower())
    exact = [c for c in cands if needle in keys(c)]
    return exact or [c for c in cands if any(needle in k for k in keys(c))]


def from_cwd():
    d = os.path.realpath(os.getcwd())
    home = os.path.realpath(os.path.expanduser("~"))
    while True:
        c = make_candidate(d)
        if c and not c.is_hub:
            return c
        parent = os.path.dirname(d)
        # Stop at $HOME: a folder above it (/tmp, /home, /) can hold a scope
        # someone else planted. Outside $HOME only the cwd itself is checked.
        if d == home or not (parent + os.sep).startswith(home + os.sep):
            return None
        d = parent


def pick(cands):
    """fzf over cands: (candidate, None), or (None, exit code)."""
    if not shutil.which("fzf"):
        print("fzf not found on PATH (needed to pick between scopes)", file=sys.stderr)
        return None, 1
    cands = sorted(cands, key=lambda c: c.name.lower())
    lines = "".join(f"{i}\t" + "\t".join(c.columns()) + "\n" for i, c in enumerate(cands))
    r = subprocess.run(["fzf", "--delimiter=\t", "--with-nth=2..", "--prompt=next> "],
                       input=lines, stdout=subprocess.PIPE, text=True)
    if r.returncode in (1, 130):
        return None, 0
    # this used to treat every non zero exit as a cancel, so fzf failing to
    # open a terminal (exit 2) exited 0 like an Esc
    if r.returncode != 0 or not r.stdout.strip():
        print(f"fzf failed (exit {r.returncode}), nothing picked", file=sys.stderr)
        return None, 1
    return cands[int(r.stdout.split("\t", 1)[0])], None


def open_sessions(path, proc="/proc"):
    count = 0
    for pid in os.listdir(proc):
        if not pid.isdigit():
            continue
        d = os.path.join(proc, pid)
        try:
            if read(os.path.join(d, "comm")).strip() != "claude":
                continue
            with open(os.path.join(d, "cmdline"), "rb") as f:
                if b"--chrome-native-host" in f.read():
                    continue
            cwd = os.path.realpath(os.readlink(os.path.join(d, "cwd")))
        except OSError:
            continue
        if cwd == path or cwd.startswith(path + os.sep):
            count += 1
    return count


def no_start(c):
    """Exit code when there is nothing to start (spec 0002 AC-6, AC-7), else None."""
    nb = c.next
    if nb is None:
        print(f"nothing to run in {c.name}")
        if c.is_hub:
            for row in open_rows(c.text):
                print(f"  {row}")
    elif nb.owed:
        print(f"waits on you: {nb.owed}")
    elif not nb.command:
        print(f"no command in this box, run it yourself: {nb.box_text}")
    else:
        return None
    for w in c.warnings:
        print(f"warning: {w}")
    return 0 if nb is None else 3


def launch(c, yes):
    nb = c.next
    rc = no_start(c)
    if rc is not None:
        return rc
    if not shutil.which("claude"):
        print("claude not found on PATH", file=sys.stderr)
        return 1
    parts = [c.display_name(), branch(c.path), changes(c.path), nb.feature or "-", nb.command]
    if nb.note:
        parts.append(("waiting: " if nb.waiting else "note: ") + nb.note)
    sessions = open_sessions(c.path)
    warnings = c.warnings + ([f"{sessions} session(s) already open here"] if sessions else [])
    parts += [f"warning: {w}" for w in warnings]
    print(" | ".join(parts), flush=True)

    tty = os.isatty(0)
    if not yes:
        if not tty:
            return 130
        try:
            if input("Enter to launch, anything else cancels: ") != "":
                return 130
        except (EOFError, KeyboardInterrupt):
            print()
            return 130
    if os.environ.get("TMUX"):
        try:
            # tmux expands #{...} formats in -c and -n, so a folder named
            # `#{...}` used to be evaluated; ## is tmux's literal #.
            r = subprocess.run(["tmux", "new-window", "-c", c.path.replace("#", "##"),
                                "-n", c.name.replace("#", "##"), "claude", nb.command])
        except FileNotFoundError:
            print("tmux not found", file=sys.stderr)
            return 1
        if r.returncode == 0:
            print(f"opened tmux window {c.name}")
        return r.returncode
    if not tty:
        print(f"cd {shlex.quote(clean(c.path))} && claude {shlex.quote(nb.command)}")
        return 4
    os.chdir(c.path)
    os.execvp("claude", ["claude", nb.command])


def resolve(args):
    """(candidate, None), or (None, exit code)."""
    if args.target:
        p = os.path.expanduser(args.target)
        c = make_candidate(p) if os.path.isdir(p) else None
        if c is not None:
            return c, None
        matches = match(discover(), args.target)
        if not matches:
            print(f"no scope matches '{args.target}'", file=sys.stderr)
            return None, 1
        return (matches[0], None) if len(matches) == 1 else pick(matches)
    c = from_cwd()
    return (c, None) if c else pick(discover())


def cmd_next(args):
    if args.list:
        for c in sorted(discover(), key=lambda c: (c.name.lower(), c.label)):
            print("\t".join(c.columns()))
        return 0
    c, rc = resolve(args)
    return rc if c is None else launch(c, args.yes)


def positive(kind):
    def parse(s):
        try:
            v = kind(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"not a number: {s}")
        if not math.isfinite(v) or v <= 0:
            raise argparse.ArgumentTypeError(f"must be a positive finite number: {s}")
        return v
    return parse


def build_parser():
    parser = argparse.ArgumentParser(prog="wf", description="Workflow runner for repo scopes.")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    nxt = sub.add_parser("next", help="open a session running a repo's next scope step")
    nxt.add_argument("target", nargs="?", help="a path, folder name or scope title")
    nxt.add_argument("-y", "--yes", action="store_true", help="launch without the confirm prompt")
    nxt.add_argument("--list", action="store_true", help="print every repo's next step and exit")
    run = sub.add_parser("run", help="build one feature unattended, a fresh claude -p call per box")
    run.add_argument("target", nargs="?", help="a path, folder name or scope title")
    run.add_argument("-y", "--yes", action="store_true", help="start without the confirm prompt")
    run.add_argument("--budget", type=positive(float), default=20, help="USD per call (default 20)")
    run.add_argument("--call-timeout", type=positive(float), default=60, help="minutes per call (default 60)")
    run.add_argument("--max-calls", type=positive(int), default=20, help="calls per run (default 20)")
    run.add_argument("--max-hours", type=positive(float), default=8, help="hours per run (default 8)")
    run.add_argument("--max-wait", type=positive(float), default=12, help="hours to wait for each phone reply (default 12)")
    allow = sub.add_parser("allow", help="let wf run start in this repo (spec 0008 trust list)")
    allow.add_argument("target", nargs="?", help="a path, folder name or scope title")
    ntfy = sub.add_parser("ntfy", help="set up and test phone pings for wf run")
    nsub = ntfy.add_subparsers(dest="action", metavar="<action>", required=True)
    init = nsub.add_parser("init", help="create the topic and one time codes")
    init.add_argument("--rotate", action="store_true", help="replace the topic and codes of an existing config")
    nsub.add_parser("codes", help="replace the one time codes")
    nsub.add_parser("test", help="send one ping and wait up to 5 minutes for the reply")
    return parser, nxt


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
        # `next` is a symlink to this file (spec 0001), and means `wf next`.
        if os.path.basename(sys.argv[0]) == "next":
            argv = ["next", *argv]
    parser, nxt = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help(sys.stderr)
        return 2
    if args.command == "run":
        import run
        return run.cmd_run(args)
    if args.command == "allow":
        import run
        return run.cmd_allow(args)
    if args.command == "ntfy":
        import ntfy
        if args.action == "init":
            return ntfy.cmd_init(args.rotate)
        return ntfy.cmd_codes() if args.action == "codes" else ntfy.cmd_test()
    if args.list and (args.target or args.yes):
        nxt.error("--list takes no argument and no -y")
    return cmd_next(args)


if __name__ == "__main__":
    sys.exit(main())
