#!/usr/bin/env python3
"""handover-memory: the four kinds of item a handover keeps, each tied to a quote (spec 0069).

An index is a feature's brief (`docs/briefs/<slug>.md`), or `docs/briefs/general.md`, or
`~/.claude/state/handover/<project>/index.md` outside a repo. Items are one line each:
  - <id> | <status> | <date> | <text> | <who> <session8> "<quote>" | <detail>
in four sections (open questions, shown and still needed, agreed decisions, live state). Detail files
and `archive.md` sit in `<slug>/` beside the index (in the index's own folder for an `index.md`).

  path [--cwd D] [--transcript J]  the index for this chat (AC-14)
  messages <transcript>            owner and claude messages, the filter check uses (AC-16)
  add <index> <Q|S|D|L> --text T --who owner|claude --session ID --quote Q [--detail P] [--move F ...]
                                   new item with the next id (AC-17); --move puts files in the detail folder (AC-4, AC-19)
  done <index> <id> [--detail D]   mark an item done
  check <index> --transcript J     drop items of this session whose quote is not in it (AC-2, AC-15, AC-18)
  prune <index>                    done items to archive.md, archive lines done over 14 days ago deleted (AC-6)
  ages <index>                     `<id> open <n>d <text>` per open item (AC-7)
  close <index>                    exit 1 naming what is still open or not landed (AC-8)
  lint <repo>                      uncited briefs and broken brief links (AC-9)
A file it cannot parse prints `handover-memory: <path>:<line>: <why>` and exits 1. `--test` runs the self checks.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SECTIONS = {
    "Q": "## Open questions",
    "S": "## Shown to the owner, still needed",
    "D": "## Agreed so far, do not ask again",
    "L": "## Live state",
}
ITEM = re.compile(r"^- ([QSDL])(\d+) \| ")
WHO = re.compile(r'^(owner|claude) (\S{8}) "(.*)"$')
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
KEEP_DAYS = 14
MAX_CHARS = 2000  # about 500 tokens at 4 characters a token (owner figure)


class ParseError(Exception):
    pass


def today():
    return os.environ.get("HANDOVER_TODAY") or datetime.date.today().isoformat()


def days(a, b):
    return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days


def norm(s):
    # the item line splits on " | " and quotes on '"', so both are written replaced, and compared the same way
    return " ".join(s.replace("|", "/").replace('"', "'").split())


def detail_dir(index):
    base = os.path.basename(index)
    return os.path.dirname(index) if base == "index.md" else index[:-3]


def archive_of(index):
    return os.path.join(detail_dir(index), "archive.md")


def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return f.read().split("\n")


def write_lines(path, lines):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    text = "\n".join(lines)
    with open(path, "w") as f:
        f.write(text if text.endswith("\n") else text + "\n")


def parse_item(path, n, line, archive=False):
    f = line[2:].split(" | ")
    want = 7 if archive else 6
    if len(f) != want:
        raise ParseError(f"{path}:{n}: {len(f)} fields, want {want} (a '|' inside text or quote?)")
    m = WHO.match(f[4])
    if not m or f[1] not in ("open", "done") or not DATE.match(f[2]):
        raise ParseError(f"{path}:{n}: bad status, date or '<who> <session8> \"<quote>\"' field")
    if archive and not re.match(r"^done \d{4}-\d{2}-\d{2}$", f[6]):
        raise ParseError(f"{path}:{n}: archive line without '| done <date>'")
    return {"id": f[0], "kind": f[0][0], "num": int(f[0][1:]), "status": f[1], "date": f[2], "text": f[3],
            "who": m.group(1), "s8": m.group(2), "quote": m.group(3), "detail": f[5],
            "done": f[6][5:] if archive else None, "n": n}


def items_of(path, lines, archive=False):
    out, seen = [], set()
    for i, line in enumerate(lines):
        if ITEM.match(line):
            it = parse_item(path, i + 1, line, archive)
            if it["id"] in seen and not archive:
                raise ParseError(f"{path}:{i + 1}: id {it['id']} used twice")
            seen.add(it["id"])
            out.append(it)
    return out


def render(it):
    return f"- {it['id']} | {it['status']} | {it['date']} | {it['text']} | {it['who']} {it['s8']} \"{it['quote']}\" | {it['detail']}"


def load(index):
    lines = read_lines(index)
    return lines, items_of(index, lines)


def fill_none(lines):
    """A section left with no line gets '- none' back, and loses it once an item is in."""
    out, i = [], 0
    while i < len(lines):
        j = i + 1
        while j < len(lines) and not lines[j].startswith("## "):
            j += 1
        head, body = lines[i], lines[i + 1:j]
        if head in SECTIONS.values():
            if any(ITEM.match(l) for l in body):
                body = [l for l in body if l != "- none"]
            elif not any(l.strip() for l in body):
                body = ["- none", ""] if j < len(lines) else ["- none"]
        out += [head, *body]
        i = j
    return out


# --- transcript ---------------------------------------------------------------------------------

def owner_text(o):
    """AC-16: a type=user line with string or text content; no tool_result, no system-reminder, no
    skill or command expansion (those are isMeta, or start with a tag such as <command-name>)."""
    if o.get("type") != "user" or o.get("isMeta") or o.get("isCompactSummary"):
        return None
    c = (o.get("message") or {}).get("content")
    if isinstance(c, str):
        parts = [c]
    elif isinstance(c, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
            return None
        parts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
    else:
        return None
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", "\n".join(parts), flags=re.S).strip()
    return text if text and not text.startswith("<") else None


def read_transcript(path):
    sid, owner, claude, edits = "", [], [], []
    with open(path) as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue  # a live transcript can end in a half written line
            sid = sid or o.get("sessionId", "")
            t = owner_text(o)
            if t:
                owner.append(t)
            if o.get("type") == "assistant":
                for b in (o.get("message") or {}).get("content") or []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and b.get("text", "").strip():
                        claude.append(b["text"])
                    if b.get("type") == "tool_use" and b.get("name") in EDIT_TOOLS:
                        p = (b.get("input") or {}).get("file_path") or (b.get("input") or {}).get("notebook_path")
                        if p:
                            edits.append(p)
    sid = sid or os.path.basename(path).split(".")[0]
    return sid, owner, claude, edits


def edited(path, edits):
    rel = path.strip()
    # lstrip("./") used to eat the dot of `.workflow/` and `.claude/`, so those landed paths never matched
    rel = rel[2:] if rel.startswith("./") else rel
    return any(e == rel or e.endswith("/" + rel) for e in edits)


# --- commands -----------------------------------------------------------------------------------

def cmd_messages(transcript):
    sid, owner, claude, edits = read_transcript(transcript)
    print(f"session {sid[:8]}")
    with open(transcript) as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            t = owner_text(o)
            if t:
                print(f"\n=== owner\n{t}")
            elif o.get("type") == "assistant":
                for b in (o.get("message") or {}).get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip():
                        print(f"\n=== claude\n{b['text']}")
    # the writer marks a decision landed only on a file this chat edited (AC-13, AC-18)
    print("\n=== files this chat edited")
    for p in dict.fromkeys(edits):
        print(p)
    return 0


def next_id(index, kind):
    _, items = load(index)
    arch = items_of(archive_of(index), read_lines(archive_of(index)), archive=True)
    # shortcut: an id deleted from the archive after 14 days can come back; nothing points at it by then
    return f"{kind}{max([i['num'] for i in items + arch if i['kind'] == kind] or [0]) + 1}"


def cmd_add(index, kind, text, who, session, quote, detail, move, title, feature):
    lines = read_lines(index)
    items_of(index, lines)
    if not lines or lines == [""]:
        name = title or os.path.basename(detail_dir(index)) or "general"
        lines = [f"# {name}: brief and handover memory", f"**Feature:** {feature or 'none'}",
                 f"**Updated:** -", ""]
        for h in SECTIONS.values():
            lines += [h, "- none", ""]
    new = next_id(index, kind)
    if move:
        d = detail_dir(index)
        if len(move) == 1:
            dest = os.path.join(d, new + os.path.splitext(move[0])[1])
            os.makedirs(d, exist_ok=True)
            shutil.move(move[0], dest)
        else:
            dest = os.path.join(d, new)
            os.makedirs(dest, exist_ok=True)
            for m in move:
                shutil.move(m, os.path.join(dest, os.path.basename(m)))
        detail = os.path.relpath(dest, os.path.dirname(index) or ".")
    it = {"id": new, "status": "open", "date": today(), "text": norm(text)[:120], "who": who,
          "s8": session[:8], "quote": norm(quote)[:160], "detail": norm(detail or "-")}
    head = SECTIONS[kind]
    if head not in lines:
        lines += ["", head]
    at = lines.index(head) + 1
    while at < len(lines) and not lines[at].startswith("## "):
        at += 1
    while at > 0 and not lines[at - 1].strip():
        at -= 1
    lines.insert(at, render(it))
    now = datetime.datetime.now().strftime("%H:%M")
    lines = [f"**Updated:** {today()} {now} by {session[:8]}" if l.startswith("**Updated:**") else l for l in lines]
    write_lines(index, fill_none(lines))
    print(new)
    return 0


def cmd_done(index, ident, detail):
    lines, items = load(index)
    for it in items:
        if it["id"] == ident:
            it["status"] = "done"
            if detail:
                it["detail"] = norm(detail)
            lines[it["n"] - 1] = render(it)
            write_lines(index, lines)
            return 0
    print(f"handover-memory: no item {ident} in {index}")
    return 1


def cmd_check(index, transcript):
    lines, items = load(index)
    sid, owner, claude, edits = read_transcript(transcript)
    said = {"owner": [norm(t) for t in owner], "claude": [norm(t) for t in claude]}
    drop = set()
    for it in items:
        if it["s8"] == sid[:8] and not any(norm(it["quote"]) in t for t in said[it["who"]]):
            drop.add(it["n"])
            print(f"dropped: {it['id']} {it['text']}")
            continue
        # an index line still holds only marks set since the last prune, so in this session (AC-18)
        if it["detail"].startswith("landed: ") and not edited(it["detail"][8:], edits):
            print(f"unlanded: {it['id']} {it['detail'][8:]}")
            it["status"], it["detail"] = "open", "-"
            lines[it["n"] - 1] = render(it)
    write_lines(index, fill_none([l for i, l in enumerate(lines) if i + 1 not in drop]))
    return 0


def size_warning(index, lines, items):
    size = len("\n".join(lines))
    if size <= MAX_CHARS:
        return
    oldest = sorted((i for i in items if i["status"] == "open"), key=lambda i: (i["date"], i["n"]))[:3]
    longest = sorted(items, key=lambda i: -len(render(i)))[:3]
    print(f"warning: {index} is {size} characters, over {MAX_CHARS}; it is still read whole")
    print("  longest lines: " + ", ".join(i["id"] for i in longest))
    print("  oldest open items, candidates to archive by hand: "
          + ", ".join(f"{i['id']} open {days(i['date'], today())}d" for i in oldest))


def cmd_prune(index):
    lines, items = load(index)
    apath = archive_of(index)
    alines = read_lines(apath)
    arch = items_of(apath, alines, archive=True)
    t = today()
    keep = [l for i, l in enumerate(alines)
            if not any(a["n"] == i + 1 and days(a["done"], t) > KEEP_DAYS for a in arch)]
    moved = [it for it in items if it["status"] == "done"]
    if moved:
        if not any(l.strip() for l in keep):
            keep = [f"# {os.path.basename(detail_dir(index))}: archive", ""]
        while keep and not keep[-1].strip():
            keep.pop()
        keep += [render(it) + f" | done {t}" for it in moved]
    if moved or len(keep) != len(alines):
        write_lines(apath, keep)
    gone = {it["n"] for it in moved}
    lines = fill_none([l for i, l in enumerate(lines) if i + 1 not in gone])
    if moved:
        write_lines(index, lines)
    size_warning(index, lines, [i for i in items if i["n"] not in gone])
    return 0


def cmd_ages(index):
    lines, items = load(index)
    for it in items:
        if it["status"] == "open":
            print(f"{it['id']} open {days(it['date'], today())}d {it['text']}")
    size_warning(index, lines, items)
    return 0


def repo_root(start):
    p = subprocess.run(["git", "-C", start, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else start


def cmd_close(index):
    if not os.path.exists(index):
        return 0
    _, items = load(index)
    arch = items_of(archive_of(index), read_lines(archive_of(index)), archive=True)
    root = repo_root(os.path.dirname(os.path.abspath(index)))
    ids = {i["id"] for i in items + arch}
    bad = 0
    for it in items + arch:
        if it["status"] == "open":
            print(f"open: {it['id']} {it['text']}")
            bad += 1
        elif it["kind"] == "D":
            d = it["detail"]
            replaced = re.match(r"^replaced by (D\d+)$", d)
            if replaced and replaced.group(1) in ids:
                continue  # the newer decision carries the landing
            if not (d.startswith("landed: ") and os.path.exists(os.path.join(root, d[8:].strip()))):
                print(f"not landed: {it['id']} {it['text']} ({d})")
                bad += 1
    return 1 if bad else 0


def cmd_lint(repo):
    root = os.path.abspath(repo)
    base = "docs" if os.path.isdir(os.path.join(root, "docs", "scope")) else ".workflow"
    briefs = os.path.join(root, base, "briefs")
    scope = os.path.join(root, base, "scope")
    cited, out = set(), []
    for dirpath, _, files in os.walk(scope):
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            row = "-"
            for line in read_lines(path):
                h = re.match(r"^#{2,4} (\d+)\.", line)
                if h:
                    row = h.group(1)
                if "Source:" not in line:
                    continue
                src = line[line.index("Source:"):]
                for m in re.finditer(r"\]\(([^)\s]+/briefs/[^)\s]+\.md)\)(\s*@\s*[0-9a-f]{7,40}\b)?", src):
                    target = os.path.normpath(os.path.join(dirpath, m.group(1)))
                    cited.add(target)
                    if not m.group(2) and not os.path.exists(target):
                        out.append(f"warning: broken brief link {row} {os.path.relpath(target, root)}")
    if os.path.isdir(briefs):
        for name in sorted(os.listdir(briefs)):
            p = os.path.join(briefs, name)
            if name.endswith(".md") and name != "general.md" and os.path.isfile(p) and p not in cited:
                out.append(f"warning: uncited brief {os.path.relpath(p, root)}")
    for line in out:
        print(line)
    return 0


def slug(heading):
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


def cmd_path(cwd, transcript):
    """AC-14: the row of the checked out branch, else the row whose spec this chat edited last, else general.md."""
    root = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if root.returncode:
        real = os.path.realpath(cwd)
        print(os.path.join(os.path.expanduser("~/.claude/state/handover"), real.replace("/", "-"), "index.md"))
        return 0
    top = root.stdout.strip()
    base = "docs" if os.path.isdir(os.path.join(top, "docs", "scope")) else ".workflow"
    rows = []  # (number, heading, block text, scope file)
    for dirpath, _, files in os.walk(os.path.join(top, base, "scope")):
        for name in sorted(files):
            if name.endswith(".md"):
                p = os.path.join(dirpath, name)
                for block in re.split(r"(?m)^(?=### )", "\n".join(read_lines(p))):
                    h = re.match(r"^### (\d+)\. ([^\n]*)", block)
                    if h:
                        rows.append((h.group(1), h.group(2).split(" · ")[0].strip(), block, p))
    branch = subprocess.run(["git", "-C", top, "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
    found = None
    m = re.match(r"^(?:feat|fix)/(?:(\d{4})-)?(.+)$", branch)
    if m:
        found = next((r for r in rows if m.group(1) and f"specs/{m.group(1)}-" in r[2]), None) \
            or next((r for r in rows if slug(r[1]) == m.group(2)), None)
    if not found and transcript:
        specs = [re.search(r"/specs/(\d{4})-", e) for e in read_transcript(transcript)[3]]
        last = next((s.group(1) for s in reversed(specs) if s), None)
        found = last and next((r for r in rows if f"specs/{last}-" in r[2]), None)
    if not found:
        print(os.path.join(top, base, "briefs", "general.md"))
        return 0
    src = re.search(r"Source:.*?\]\(([^)\s]+/briefs/[^)\s]+\.md)\)", found[2])
    if src:
        print(os.path.normpath(os.path.join(os.path.dirname(found[3]), src.group(1))))
    else:
        print(os.path.join(top, base, "briefs", slug(found[1]) + ".md"))
    return 0


def main(argv):
    if argv == ["--test"]:
        return self_test()
    ap = argparse.ArgumentParser(prog="handover-memory")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("path"); p.add_argument("--cwd", default=os.getcwd()); p.add_argument("--transcript")
    p = sub.add_parser("messages"); p.add_argument("transcript")
    p = sub.add_parser("add"); p.add_argument("index"); p.add_argument("kind", choices=list(SECTIONS))
    p.add_argument("--text", required=True); p.add_argument("--who", choices=["owner", "claude"], required=True)
    p.add_argument("--session", required=True); p.add_argument("--quote", required=True)
    p.add_argument("--detail"); p.add_argument("--move", nargs="+"); p.add_argument("--title"); p.add_argument("--feature")
    p = sub.add_parser("done"); p.add_argument("index"); p.add_argument("id"); p.add_argument("--detail")
    p = sub.add_parser("check"); p.add_argument("index"); p.add_argument("--transcript", required=True)
    for name in ("prune", "ages", "close"):
        sub.add_parser(name).add_argument("index")
    sub.add_parser("lint").add_argument("repo")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "path":
            return cmd_path(a.cwd, a.transcript)
        if a.cmd == "messages":
            return cmd_messages(a.transcript)
        if a.cmd == "add":
            return cmd_add(a.index, a.kind, a.text, a.who, a.session, a.quote, a.detail, a.move, a.title, a.feature)
        if a.cmd == "done":
            return cmd_done(a.index, a.id, a.detail)
        if a.cmd == "check":
            return cmd_check(a.index, a.transcript)
        if a.cmd == "lint":
            return cmd_lint(a.repo)
        return {"prune": cmd_prune, "ages": cmd_ages, "close": cmd_close}[a.cmd](a.index)
    except ParseError as e:
        print(f"handover-memory: {e}")
        return 1


# --- self checks --------------------------------------------------------------------------------

def self_test():
    failures = []

    def check(name, got, want):
        if got != want:
            failures.append(f"{name}: got {got!r}, want {want!r}")

    def run(*args, cwd=None):
        p = subprocess.run([sys.executable, os.path.abspath(__file__), *args], capture_output=True, text=True,
                           cwd=cwd, env={**os.environ, "HANDOVER_TODAY": "2026-10-22"})
        return p.returncode, p.stdout.splitlines()

    def write(path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def read(path):
        with open(path) as f:
            return f.read()

    def jl(*objs):
        return "".join(json.dumps(o) + "\n" for o in objs)

    def user(text, **kw):
        return {"type": "user", "sessionId": "3f2a1b9c-0000", "message": {"role": "user", "content": text}, **kw}

    def said(text, tools=()):
        content = [{"type": "text", "text": text}] + [
            {"type": "tool_use", "name": n, "input": {"file_path": p}} for n, p in tools]
        return {"type": "assistant", "sessionId": "3f2a1b9c-0000", "message": {"role": "assistant", "content": content}}

    def item(i, status, date, text, who, s8, quote, detail="-"):
        return f'- {i} | {status} | {date} | {text} | {who} {s8} "{quote}" | {detail}'

    def index(*sections):
        heads = list(SECTIONS.values())
        body = "".join(f"\n{heads[k]}\n" + ("\n".join(v) or "- none") + "\n" for k, v in enumerate(sections))
        return f"# T: brief and handover memory\n**Feature:** none\n**Updated:** -\n{body}"

    with tempfile.TemporaryDirectory() as tmp:
        tr = os.path.join(tmp, "3f2a1b9c-0000.jsonl")
        write(tr, jl(
            user("Finished items are deleted\n  14 days after they are done | ok"),
            user([{"type": "text", "text": "<system-reminder>secret plan B</system-reminder>"}, {"type": "text", "text": "keep plan A"}]),
            user([{"type": "tool_result", "content": "x"}, {"type": "text", "text": "tool says ship it"}]),
            user("skill text says ship it", isMeta=True),
            user("<command-name>/scope</command-name> ship it"),
            said('Full table with a "recommendation" per feature', [("Edit", "/w/docs/specs/0063-auto-handoff.md")]),
        ) + "{half a line")
        idx = os.path.join(tmp, "repo", "docs", "briefs", "f.md")

        # AC-2, AC-15, AC-16, AC-18, AC-20: quote or drop, this session only, the message filter, landed marks, pipes
        write(idx, index(
            [item("Q1", "open", "2026-10-22", "made up", "owner", "3f2a1b9c", "the owner never said this"),
             item("Q2", "open", "2026-10-20", "older session", "owner", "99999999", "not in this transcript")],
            [item("S1", "open", "2026-10-22", "table", "claude", "3f2a1b9c", "Full table with a 'recommendation' per feature")],
            [item("D1", "open", "2026-10-22", "delete after 14 days", "owner", "3f2a1b9c", "Finished items are deleted 14 days after they are done / ok"),
             item("D2", "done", "2026-10-22", "from a reminder", "owner", "3f2a1b9c", "secret plan B"),
             item("D3", "done", "2026-10-22", "from a tool result", "owner", "3f2a1b9c", "tool says ship it"),
             item("D4", "done", "2026-10-22", "plan A", "owner", "3f2a1b9c", "keep plan A", "landed: docs/specs/0063-auto-handoff.md"),
             item("D5", "done", "2026-10-22", "plan A again", "owner", "3f2a1b9c", "keep plan A", "landed: docs/specs/0001-x.md"),
             item("D6", "open", "2026-10-22", "from a skill", "owner", "3f2a1b9c", "skill text says ship it"),
             item("D7", "open", "2026-10-22", "from a command", "owner", "3f2a1b9c", "ship it"),
             item("D8", "open", "2026-10-22", "said by claude", "owner", "3f2a1b9c", "Full table")],
            []))
        code, out = run("check", idx, "--transcript", tr)
        check("check exit", code, 0)
        check("AC-2 a made up quote is dropped", "dropped: Q1 made up" in out, True)
        check("AC-2 a real quote is kept, whitespace and a pipe collapsed", any(l.startswith("- D1 ") for l in read(idx).split("\n")), True)
        check("AC-2 a claude quote with a double quote is kept", "- S1 " in read(idx), True)
        check("AC-15 an older session's item is left alone", "- Q2 " in read(idx), True)
        check("AC-16 a system-reminder is not an owner message", "dropped: D2 from a reminder" in out, True)
        check("AC-16 a tool result is not an owner message", "dropped: D3 from a tool result" in out, True)
        check("AC-16 skill text is not an owner message", "dropped: D6 from a skill" in out, True)
        check("AC-16 a command expansion is not an owner message", "dropped: D7 from a command" in out, True)
        check("AC-16 claude text is not an owner message", "dropped: D8 said by claude" in out, True)
        check("AC-13 AC-18 a landed mark on an edited file stays", "landed: docs/specs/0063-auto-handoff.md" in read(idx), True)
        check("AC-18 a landed mark on a file never edited is removed", ("unlanded: D5 docs/specs/0001-x.md" in out,
              item("D5", "open", "2026-10-22", "plan A again", "owner", "3f2a1b9c", "keep plan A") in read(idx)), (True, True))

        dot_tr = os.path.join(tmp, "3f2a1b9c-0001.jsonl")
        write(dot_tr, jl(user("keep plan A"), said("x", [("Write", "/w/.workflow/specs/0002-y.md")])))
        dot = os.path.join(tmp, "dot.md")
        landed = item("D1", "done", "2026-10-22", "plan A", "owner", "3f2a1b9c", "keep plan A", "landed: .workflow/specs/0002-y.md")
        write(dot, index([], [], [landed], []))
        code, out = run("check", dot, "--transcript", dot_tr)
        check("AC-18 a landed path under .workflow/ that this chat wrote stays", (out, landed in read(dot)), ([], True))

        code, out = run("messages", tr)
        check("AC-16 messages shows owner text, never the hidden ones", ("keep plan A" in "\n".join(out),
              "secret plan B" in "\n".join(out), "tool says" in "\n".join(out), "=== claude" in out), (True, False, False, True))
        check("AC-13 messages lists the files this chat edited", out[-2:], ["=== files this chat edited", "/w/docs/specs/0063-auto-handoff.md"])

        # AC-6: prune moves done items, deletes archive lines done over 14 days ago, never an open item
        arch = archive_of(idx)
        write(arch, "# f: archive\n\n" + "\n".join([
            item("D9", "done", "2026-09-01", "old", "owner", "11111111", "q") + " | done 2026-10-07",
            item("D10", "done", "2026-09-01", "kept", "owner", "11111111", "q") + " | done 2026-10-09"]) + "\n")
        write(idx, index([item("Q1", "open", "2026-01-01", "very old question", "owner", "11111111", "q")], [],
                         [item("D11", "done", "2026-10-21", "landed one", "owner", "11111111", "q", "landed: README.md")], []))
        code, out = run("prune", idx)
        a = read(arch)
        check("AC-6 a 15 day old done line is deleted", "- D9 " in a, False)
        check("AC-6 a 13 day old done line is kept", "- D10 " in a, True)
        check("AC-6 a done item moves to the archive with its done date", (
            item("D11", "done", "2026-10-21", "landed one", "owner", "11111111", "q", "landed: README.md") + " | done 2026-10-22" in a,
            "- D11 " in read(idx)), (True, False))
        check("AC-6 an open item of any age stays", "- Q1 " in read(idx), True)
        check("AC-6 an emptied section gets '- none'", "## Agreed so far, do not ask again\n- none" in read(idx), True)

        # AC-7 ages
        code, out = run("ages", idx)
        check("AC-7 ages", out, ["Q1 open 294d very old question"])

        # AC-17 ids over index plus archive; AC-19 detail files keep their extension, a folder for several
        rep = os.path.join(tmp, "s.txt")
        write(rep, "62 rows\n")
        code, out = run("add", idx, "D", "--text", "a | b", "--who", "owner", "--session", "3f2a1b9c-x", "--quote", 'say "x" | y')
        check("AC-17 the next D id counts the archive", out, ["D12"])
        check("AC-20 a pipe and a double quote are replaced", item("D12", "open", "2026-10-22", "a / b", "owner", "3f2a1b9c", "say 'x' / y") in read(idx), True)
        code, out = run("add", idx, "S", "--text", "list", "--who", "claude", "--session", "3f2a1b9c", "--quote", "q", "--move", rep)
        check("AC-4 AC-19 one file moves in as S1 with its extension", (out, os.path.exists(os.path.join(detail_dir(idx), "S1.txt")),
              os.path.exists(rep), '"q" | f/S1.txt' in read(idx)), (["S1"], True, False, True))
        two = [os.path.join(tmp, n) for n in ("a.md", "b.png")]
        for t in two:
            write(t, "x")
        run("add", idx, "S", "--text", "pair", "--who", "claude", "--session", "3f2a1b9c", "--quote", "q", "--move", *two)
        check("AC-19 several files go in a folder S2/", os.path.exists(os.path.join(detail_dir(idx), "S2", "b.png")), True)
        new = os.path.join(tmp, "repo", "docs", "briefs", "g.md")
        run("add", new, "Q", "--text", "first", "--who", "owner", "--session", "3f2a1b9c", "--quote", "q", "--title", "G", "--feature", "docs/scope/scope.md row 1")
        g = read(new)
        check("add makes a new index with the four sections", (g.startswith("# G: brief and handover memory\n**Feature:** docs/scope/scope.md row 1\n"),
              all(h in g for h in SECTIONS.values()), "## Open questions\n- Q1 |" in g, "## Live state\n- none" in g), (True, True, True, True))
        check("done marks an item", (run("done", new, "Q1")[0], "- Q1 | done |" in read(new)), (0, True))

        # AC-20 size: over 2000 characters a warning names the oldest items, nothing archived
        big = os.path.join(tmp, "big.md")
        write(big, index([item(f"Q{n}", "open", f"2026-10-{10 + n:02d}", "x" * 100, "owner", "11111111", "y" * 150) for n in range(1, 10)], [], [], []))
        code, out = run("ages", big)
        check("AC-20 over 2000 characters it warns with the oldest", (any(l.startswith(f"warning: {big} is ") for l in out),
              any("Q1 open 11d" in l for l in out), read(big).count("| open |")), (True, True, 9))

        # AC-8 close
        root = os.path.join(tmp, "repo")
        subprocess.run(["git", "init", "-q", root], check=True)
        write(os.path.join(root, "docs", "specs", "0063-auto-handoff.md"), "x")
        c = os.path.join(root, "docs", "briefs", "c.md")
        write(c, index([], [], [item("D1", "done", "2026-10-22", "landed", "owner", "11111111", "q", "landed: docs/specs/0063-auto-handoff.md"),
                                item("D2", "done", "2026-10-22", "replaced", "owner", "11111111", "q", "replaced by D1")], []))
        check("AC-8 every decision landed: exit 0", run("close", c), (0, []))
        write(c, index([item("Q1", "open", "2026-10-22", "still asked", "owner", "11111111", "q")], [], [], []))
        check("AC-8 an open item exits 1 and is named", run("close", c), (1, ["open: Q1 still asked"]))
        write(c, index([], [], [item("D1", "done", "2026-10-22", "unlanded", "owner", "11111111", "q", "-")], []))
        check("AC-8 a decision with no landed path exits 1", run("close", c), (1, ["not landed: D1 unlanded (-)"]))
        write(c, index([], [], [item("D1", "done", "2026-10-22", "gone", "owner", "11111111", "q", "landed: docs/specs/9999-none.md")], []))
        check("AC-8 a landed path that does not exist exits 1", run("close", c)[0], 1)

        # AC-9 lint
        lr = os.path.join(tmp, "lint")
        write(os.path.join(lr, "docs", "briefs", "used.md"), "x")
        write(os.path.join(lr, "docs", "briefs", "lonely.md"), "x")
        write(os.path.join(lr, "docs", "briefs", "general.md"), "x")
        write(os.path.join(lr, "docs", "briefs", "used", "S1.md"), "x")
        write(os.path.join(lr, "docs", "scope", "scope.md"), "\n".join([
            "### 3. A", "Source: [brief](../briefs/used.md)", "### 4. B", "Spec x · Source: [brief](../briefs/missing.md)",
            "### 5. C", "Source: [brief](../briefs/closed.md) @ 1a2b3c4", "See [brief](../briefs/nosource.md)"]) + "\n")
        check("AC-9 AC-21 both warnings, general.md and a closed brief exempt", run("lint", lr),
              (0, ["warning: broken brief link 4 docs/briefs/missing.md", "warning: uncited brief docs/briefs/lonely.md"]))

        # AC-14 path
        pr = os.path.join(tmp, "pathrepo")
        subprocess.run(["git", "init", "-q", "-b", "main", pr], check=True)
        write(os.path.join(pr, "docs", "scope", "scope.md"), "\n".join([
            "### 91. Handover memory · in-progress", "- [ ] Design: spec [0069](../specs/0069-handover-memory.md)",
            "Source: [brief](../briefs/handover-memory.md)", "### 92. Skills start · in-progress",
            "- [ ] spec [0070](../specs/0070-skills.md)"]) + "\n")
        check("AC-14 no feature branch, no transcript: general.md", run("path", "--cwd", pr)[1], [os.path.join(pr, "docs/briefs/general.md")])
        str2 = os.path.join(tmp, "t2.jsonl")
        write(str2, jl(said("x", [("Edit", f"{pr}/docs/specs/0069-handover-memory.md"), ("Write", f"{pr}/docs/specs/0070-skills.md")])))
        check("AC-14 the row whose spec was edited last", run("path", "--cwd", pr, "--transcript", str2)[1], [os.path.join(pr, "docs/briefs/skills-start.md")])
        subprocess.run(["git", "-C", pr, "checkout", "-q", "-b", "feat/0069-handover-memory"], check=True)
        check("AC-14 the checked out branch's row, its Source brief", run("path", "--cwd", pr, "--transcript", str2)[1], [os.path.join(pr, "docs/briefs/handover-memory.md")])
        nr = os.path.join(tmp, "norepo")
        os.makedirs(nr)
        check("AC-14 no repo: ~/.claude/state/handover/<project>/index.md", run("path", "--cwd", nr)[1],
              [os.path.join(os.path.expanduser("~/.claude/state/handover"), os.path.realpath(nr).replace("/", "-"), "index.md")])

        # AC-2 exit 1 only on a file it cannot parse, naming the line
        write(c, index([item("Q1", "open", "2026-10-22", "a | b", "owner", "11111111", "q")], [], [], []))
        code, out = run("check", c, "--transcript", tr)
        check("a line it cannot parse exits 1 and names the line", (code, out[0].startswith(f"handover-memory: {c}:6: 7 fields, want 6")), (1, True))

    for f in failures:
        print(f"FAIL {f}")
    print(f"handover-memory self checks: {'all passed' if not failures else f'{len(failures)} failed'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
