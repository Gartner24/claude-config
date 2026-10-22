#!/usr/bin/env python3
"""The chip-dash Plan view's data, as JSON on stdout: every repo scope under the scan roots, each feature with its
state and next step (spec 0060 AC-1). The scope parser is runner/wf.py's (parse_text, sections, pick_next,
feature_state, plan_scopes), trimmed to what the pane reads: the runner is retired, so the states it alone could
tell (building, to publish, in review) are gone. Stdlib only."""
import json
import os
import re

SCOPE_BASES = ("docs/scope", ".workflow/scope")
SCOPE_FILES = ("scope.md", "index.md")
BOX = re.compile(r"^(\s*)[-*+]\s+\[([ xX])\]\s?(.*)$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
GONE_TAG = re.compile(r"\(\s*(done|existing|dropped)\s*\)|·\s*(done|existing|dropped)\s*(?=·|$)", re.I)
DISPLAY_TAG = re.compile(r"\s*·[^·]*|\s*\(\s*(done|existing|dropped|planned|in-progress|needs a decision)\s*\)", re.I)
COMMAND = re.compile(r"^/[a-z][\w:-]*(\s|$)")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
# only the marker counts as a box only you can close (spec 0012, 0066); the near words are warned about
OWED = re.compile(r"·\s*waits on you\s*(?=·|$)", re.I)
NEAR_OWED = re.compile(r"waits on", re.I)
SKIP_AHEAD = re.compile(r"·\s*later boxes go on\s*(?=·|$)", re.I)
# scope text and folder names come from repos you may have cloned; an ESC in them used to reach the terminal
CONTROL = re.compile(r"[\x00-\x1f\x80-\x9f\udc80-\udcff]")
SPEC_LINK = re.compile(r"specs/(?:[^/)]*/)?(\d{4})-")
SPEC_STATUS = re.compile(r"^\*\*Status\*\*:\s*(.+)$", re.M)
STEP_STATE = {"/architect": "needs a design", "/develop": "ready to build"}


def clean(text):
    return CONTROL.sub("", text)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


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
    return (OWED.sub("", box.text).strip() or box.text.strip()) if box and OWED.search(box.text) else None


class NextBox:
    def __init__(self, box, command, note_box):
        self.box_text, self.command = box.text, command
        self.owed = owed_text(box) or owed_text(note_box)
        texts = dict.fromkeys(b.text for b in (box, note_box) if b)
        self.near_misses = [t for t in texts if NEAR_OWED.search(t) and not OWED.search(t)]


def uncomment(text):
    # comments go first, keeping their newlines so later lines stay in place
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)


def parse_text(text):
    boxes, stack = [], []
    feature, gone, deferred, fence = None, False, False, None
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
        if h and len(h.group(1)) <= 3:
            level, heading = len(h.group(1)), clean(h.group(2))
            stack = []
            feature = heading if level == 3 else None
            gone = bool(feature and GONE_TAG.search(feature))
            # a level 1 heading ends ## Deferred too; it used to keep every later feature deferred
            if level <= 2:
                deferred = level == 2 and heading.lower().startswith("deferred")
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
    """(heading, raw lines, under ## Deferred) per level 3 heading, up to the next heading of level 1 to 3."""
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
        if level <= 2:
            deferred = level == 2 and heading.lower().startswith("deferred")
        starts.append((i, heading if level == 3 else None, deferred))
    starts.append((len(raw), None, False))
    return [(h, raw[i:j], d) for (i, h, d), (j, _, _) in zip(starts, starts[1:]) if h is not None]


def under(box, ancestor):
    while box.parent:
        box = box.parent
        if box is ancestor:
            return True
    return False


def passed_over(box):
    """A box whose own text carries both waiting tags (spec 0014 AC-8), or a milestone under an open one."""
    while box:
        if box.open and OWED.search(box.text) and SKIP_AHEAD.search(box.text):
            return True
        box = box.parent
    return False


def pick_next(boxes):
    first = next((b for b in boxes if b.open and not b.skip), None)
    if first is None:
        return None
    if passed_over(first):
        later = boxes[boxes.index(first):]
        first = next((b for b in later if b.open and not b.skip and b.feature == first.feature and not passed_over(b)), first)
    # a milestone runs its parent's command; a top box notes its first open milestone
    if first.parent:
        return NextBox(first, first.parent.command(), first)
    return NextBox(first, first.command(), next((b for b in boxes if b.open and under(b, first)), None))


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


def is_worktree(path):
    """A linked worktree: a .git file whose git folder has a commondir (a submodule's has none)."""
    dot = os.path.join(path, ".git")
    if not os.path.isfile(dot):
        return False
    try:
        gd = os.path.join(path, read(dot).strip().removeprefix("gitdir:").strip())
    except OSError:
        return False
    return os.path.isfile(os.path.join(gd, "commondir"))


def bare(heading):
    return DISPLAY_TAG.sub("", heading or "").strip()


def spec_status(repo, scope_dir, num):
    specs = os.path.join(repo, os.path.dirname(scope_dir), "specs")
    try:
        names = sorted(os.listdir(specs))
    except OSError:
        return "unknown"
    for n in names:
        if not n.startswith(num + "-"):
            continue
        f = os.path.join(specs, n, "index.md") if os.path.isdir(os.path.join(specs, n)) else os.path.join(specs, n)
        if not f.endswith(".md"):
            continue
        try:
            m = SPEC_STATUS.search(read(f))
        except OSError:
            continue
        if m:
            return clean(m.group(1).strip())
    return "unknown"


def feature_state(heading, nb):
    """First match wins: a box only you can close, a gone tag, no open box, else the next step's kind."""
    if nb is not None and nb.owed is not None:
        return "waits on you"
    gone = GONE_TAG.search(heading)
    if gone:
        return next(g for g in gone.groups() if g).lower()
    if nb is None:
        return "done (untagged)"
    return STEP_STATE.get((nb.command or "").split(" ")[0], "in progress")


def plan_entry(path):
    """None when the folder has no scope; else its hub rows or its features."""
    found = [b for b in SCOPE_BASES if any(os.path.isfile(os.path.join(path, b, f)) for f in SCOPE_FILES)]
    if not found:
        return None
    scope_dir = found[0]
    warnings = ["both docs/scope and .workflow/scope exist, using docs/scope"] if len(found) == 2 else []
    folder = os.path.join(path, scope_dir)
    main = next(os.path.join(folder, f) for f in SCOPE_FILES if os.path.isfile(os.path.join(folder, f)))
    top = read(main)
    texts = list(read(f) for f in epics(folder, top, warnings)) if main.endswith("index.md") else [top]
    feats = []
    for text in texts:
        for heading, raw, deferred in sections(text):
            boxes = parse_text("\n".join(raw))
            if not boxes:
                continue
            nb = pick_next(boxes)
            if nb:
                warnings += [f'"waits on" is not the marker here, end the box with " · waits on you": {t}' for t in nb.near_misses]
            m = SPEC_LINK.search("\n".join(raw))
            feats.append({
                "heading": bare(heading), "state": feature_state(heading, nb), "next": nb.box_text if nb else None,
                "command": nb.command if nb else None, "spec": m.group(1) if m else None,
                "specStatus": spec_status(path, scope_dir, m.group(1)) if m else None, "deferred": deferred,
            })
    out = {"name": clean(os.path.basename(path)), "path": path, "hub": not feats, "warnings": [clean(w) for w in warnings]}
    if feats:
        out["features"] = feats
    else:
        out["rows"] = open_rows(top)
    return out


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


def plan_scopes():
    """Each scope read in its own try, so one broken scope never hides the rest; a worktree is left out, its repo's
    entry is the main checkout's."""
    seen, out = set(), []
    for root, lo, hi in scan_roots():
        for d in walk(root, lo, hi):
            real = os.path.realpath(d)
            if real in seen:
                continue
            seen.add(real)
            try:
                if is_worktree(real):
                    continue
                e = plan_entry(real)
                if e:
                    out.append(e)
            except Exception as err:  # a broken scope is listed with its error, never dropped
                out.append({"name": clean(os.path.basename(real)), "path": real, "error": clean(str(err) or type(err).__name__)})
    return out


if __name__ == "__main__":
    print(json.dumps({"repos": plan_scopes(), "warnings": []}))
