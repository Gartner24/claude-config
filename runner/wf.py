#!/usr/bin/env python3
# The workflow runner (spec 0001). Stdlib only, so a fresh clone works with no
# install step. Subcommands land per release: `next` in Release 1, `run` later.
import argparse
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
# C0 and C1 control characters. Scope text and folder names come from repos you
# may have cloned; an ESC or CR in them used to reach the terminal and fzf as is.
# Lone surrogates are undecodable bytes in a folder name; printing one used to
# crash with UnicodeEncodeError under a UTF-8 locale.
CONTROL = re.compile(r"[\x00-\x1f\x80-\x9f\udc80-\udcff]")
# A planted core.fsmonitor or hook in a scanned repo used to run on `git status`.
GIT_SAFE = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")


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


class NextBox:
    def __init__(self, box, command, note):
        self.feature = DISPLAY_TAG.sub("", box.feature).strip() if box.feature else None
        self.box_text, self.command, self.note = box.text, command, note
        self.waiting = bool(note and WAITING.search(note))


def parse_text(text):
    # Comments go first, keeping their newlines so later lines stay in place.
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
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
        return NextBox(first, first.parent.command(), first.text)
    note = next((b.text for b in boxes if b.open and under(b, first)), None)
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
        return subprocess.run(["git", *GIT_SAFE, "-C", path, *args], capture_output=True, text=True, errors="replace")
    except FileNotFoundError:
        return None


def head_branch(path):
    # `git status` runs a repo's own filter drivers, so --list and the picker
    # read HEAD from the files and never run git in a scanned repo.
    dot = os.path.join(path, ".git")
    try:
        if os.path.isfile(dot):
            dot = os.path.join(path, read(dot).strip().removeprefix("gitdir:").strip())
        head = read(os.path.join(dot, "HEAD")).strip()
    except OSError:
        return "no git"
    if head.startswith("ref: refs/heads/"):
        name = head[len("ref: refs/heads/"):]
        # reftable repos keep the real HEAD elsewhere and write this placeholder
        return "-" if name == ".invalid" else clean(name)
    return "detached " + clean(head[:7])


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
    return f"{len(r.stdout.splitlines())} changes"


def worktrees(path):
    """(real path, branch or None) per worktree, main checkout first."""
    r = git(path, "worktree", "list", "--porcelain")
    if r is None or r.returncode:
        return []
    out = []
    for record in r.stdout.strip().split("\n\n"):
        fields = dict((line.split(" ", 1) + [""])[:2] for line in record.splitlines())
        if "worktree" in fields and "bare" not in fields:
            out.append((os.path.realpath(fields["worktree"]), fields.get("branch", "").removeprefix("refs/heads/") or None))
    return out


def worktree_label(path):
    if not os.path.isfile(os.path.join(path, ".git")):
        return ""
    for wt, br in worktrees(path)[1:]:
        if wt == path:
            return f"worktree {clean(br)}" if br else "worktree (detached)"
    return ""


def find_scope(path):
    found = [b for b in SCOPE_BASES if any(os.path.isfile(os.path.join(path, b, f)) for f in SCOPE_FILES)]
    if not found:
        return None, []
    warnings = ["both docs/scope and .workflow/scope exist, using docs/scope"] if len(found) == 2 else []
    return found[0], warnings


class Candidate:
    def __init__(self, path, scope_dir, warnings):
        self.path, self.scope_dir, self.warnings = path, scope_dir, warnings
        self.name = clean(os.path.basename(path))
        self.label = worktree_label(path)
        folder = os.path.join(path, scope_dir)
        main = next(os.path.join(folder, f) for f in SCOPE_FILES if os.path.isfile(os.path.join(folder, f)))
        self.text = read(main)
        first = next((l for l in self.text.splitlines() if l.startswith("#")), "")
        self.title = first[len("# Scope:"):].strip() if first.startswith("# Scope:") else None
        if main.endswith("index.md"):
            boxes = []
            for f in self.epics(folder):
                boxes += parse_text(read(f))
        else:
            boxes = parse_text(self.text)
        self.is_hub = not boxes
        self.next = pick_next(boxes)

    def epics(self, folder):
        real_folder, seen = os.path.realpath(folder), []
        for link in LINK.findall(self.text):
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
                self.warnings.append(f"missing epic file {clean(target)}")

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
        for wt, _ in worktrees(c.path)[1:]:
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
    if r.returncode != 0 or not r.stdout.strip():
        return None, 0
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


def launch(c, yes):
    nb = c.next
    if nb is None:
        print(f"nothing to run in {c.name}")
        if c.is_hub:
            for row in open_rows(c.text):
                print(f"  {row}")
        return 0
    if not nb.command:
        print(f"no command in this box, run it yourself: {nb.box_text}")
        return 3
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


def cmd_next(args):
    if args.list:
        for c in sorted(discover(), key=lambda c: (c.name.lower(), c.label)):
            print("\t".join(c.columns()))
        return 0
    c = None
    if args.target:
        p = os.path.expanduser(args.target)
        c = make_candidate(p) if os.path.isdir(p) else None
        if c is None:
            matches = match(discover(), args.target)
            if not matches:
                print(f"no scope matches '{args.target}'", file=sys.stderr)
                return 1
            c = matches[0] if len(matches) == 1 else None
            if c is None:
                c, rc = pick(matches)
                if c is None:
                    return rc
    else:
        c = from_cwd()
        if c is None:
            c, rc = pick(discover())
            if c is None:
                return rc
    return launch(c, args.yes)


def build_parser():
    parser = argparse.ArgumentParser(prog="wf", description="Workflow runner for repo scopes.")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    nxt = sub.add_parser("next", help="open a session running a repo's next scope step")
    nxt.add_argument("target", nargs="?", help="a path, folder name or scope title")
    nxt.add_argument("-y", "--yes", action="store_true", help="launch without the confirm prompt")
    nxt.add_argument("--list", action="store_true", help="print every repo's next step and exit")
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
    if args.list and (args.target or args.yes):
        nxt.error("--list takes no argument and no -y")
    return cmd_next(args)


if __name__ == "__main__":
    sys.exit(main())
