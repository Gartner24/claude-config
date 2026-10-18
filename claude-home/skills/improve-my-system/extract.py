#!/usr/bin/env python3
"""Spec 0061 AC-9: your typed messages and tool names from the session history of the projects on
~/.claude/private/history-allow.txt, with keys, emails and private names replaced before any model reads them.
Writes ~/claude-improve/extract/<project>.jsonl, one line per session since the last report. Stdlib only."""
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
LIVE = os.path.abspath(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(HOME, ".claude"))
OUT = os.path.join(HOME, "claude-improve")
TOKENS = re.compile(r"sk-[\w-]{8,}|gh[pousr]_\w{8,}|xox[a-z]-[\w-]{8,}|\b[0-9a-fA-F]{32,}\b|[A-Za-z0-9+/=_-]{40,}")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def die(msg):
    print(f"extract: {msg}", file=sys.stderr)
    sys.exit(1)


def encode(path):
    # Claude Code names a project folder after its path with every other character turned into "-".
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def allowed():
    p = os.path.join(LIVE, "private", "history-allow.txt")
    try:
        with open(p, encoding="utf-8") as f:
            lines = [l.strip() for l in f]
    except OSError:
        die(f"{p} is missing: write one absolute path per line, only your own projects")
    return {encode(os.path.normpath(l)): l for l in lines if l.startswith("/")}


def names():
    p = os.path.join(LIVE, "private", "names.txt")
    try:
        with open(p, encoding="utf-8") as f:
            lines = [l.strip() for l in f]
    except OSError:
        die(f"{p} is missing; without it private names could reach the model, so nothing is read")
    out = [l.partition("==>")[0].strip() for l in lines if l and not l.startswith("#")]
    out = [n for n in out if n]
    if not out:
        die(f"{p} has no names; nothing is read")
    return re.compile("|".join(re.escape(n) for n in sorted(out, key=len, reverse=True)), re.I)


def redact(text, private):
    return private.sub("[REDACTED]", EMAIL.sub("[REDACTED]", TOKENS.sub("[REDACTED]", text)))


def in_git(path):
    p = path
    while True:
        if os.path.exists(os.path.join(p, ".git")):
            return True
        up = os.path.dirname(p)
        if up == p:
            return False
        p = up


def typed(msg):
    """Your own words in a user line: a string, or its text blocks; never tool results."""
    c = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(c, str):
        return [c]
    return [b["text"] for b in c or [] if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)]


def session(path):
    date, said, tools = None, [], []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("isSidechain") or d.get("isMeta"):
                continue
            date = date or (d.get("timestamp") or "")[:10] or None
            msg = d.get("message")
            if d.get("type") == "user":
                said += [t for t in typed(msg) if t.strip()]
            elif d.get("type") == "assistant" and isinstance(msg, dict) and isinstance(msg.get("content"), list):
                tools += [b.get("name") for b in msg["content"] if isinstance(b, dict) and b.get("type") == "tool_use"]
    return date, said, [t for t in tools if isinstance(t, str)]


def propose(lines):
    """Up to 3 top findings into the runner's inbox, keyed like its own proposals (runner/insights.py), never twice."""
    import fcntl
    import hashlib
    import tempfile
    d = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.join(HOME, ".local", "state"), "wf", "insights")
    os.makedirs(d, mode=0o700, exist_ok=True)
    lock = os.open(os.path.join(d, "lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        inbox, known = os.path.join(d, "inbox.md"), os.path.join(d, "proposed.json")
        text = open(inbox, encoding="utf-8").read() if os.path.exists(inbox) else \
            "# wf proposals\n\nWritten by the runner (spec 0061) from problems that repeat across runs. Nothing here " \
            "is applied; promote a good one to a plan row, then run `wf insights --seen`.\n\n"
        try:
            seen = set(json.load(open(known, encoding="utf-8")))
        except (OSError, ValueError, TypeError):
            seen = set()
        seen |= set(re.findall(r"^- \[([0-9a-f]{12})\]", text, re.M))
        added, private = 0, names()
        for line in lines[:3]:
            line = redact(" ".join(line.split()), private)
            h = hashlib.sha256(f"history\0{line}".encode()).hexdigest()[:12]
            if not line or h in seen:
                continue
            text += f"- [{h}] from improve-my-system: {line} (see {os.path.join(OUT, 'report.md')})\n"
            seen.add(h)
            added += 1
        for path, body in ((inbox, text), (known, json.dumps(sorted(seen)))):
            fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(body)
            os.replace(tmp, path)
        print(f"propose: {added} added to {inbox}")
    finally:
        os.close(lock)


def main():
    if sys.argv[1:2] == ["--propose"]:
        return propose(sys.argv[2:])
    if in_git(OUT):
        die(f"{OUT} is inside a git repo; the extract and report must never enter one")
    allow, private = allowed(), names()
    report = os.path.join(OUT, "report.md")
    since = os.path.getmtime(report) if os.path.exists(report) else 0
    projects = os.path.join(LIVE, "projects")
    out_dir = os.path.join(OUT, "extract")
    os.makedirs(out_dir, mode=0o700, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.endswith(".jsonl"):
            os.remove(os.path.join(out_dir, old))
    total, n = 0, 0
    for folder in sorted(os.listdir(projects)) if os.path.isdir(projects) else []:
        if folder not in allow:
            continue
        project = redact(allow[folder], private)
        rows = []
        # Only the top level: subagent transcripts live in <session>/subagents/ and are not your words.
        for name in sorted(os.listdir(os.path.join(projects, folder))):
            p = os.path.join(projects, folder, name)
            if not name.endswith(".jsonl") or not os.path.isfile(p) or os.path.getmtime(p) <= since:
                continue
            date, said, tools = session(p)
            if said:
                rows.append({"project": project, "session": name[:-6], "date": date,
                             "messages": [redact(t, private) for t in said],
                             "tools": [redact(t, private) for t in tools]})
        if rows:
            # Numbered, since the folder name is the project path and may hold a private name.
            n += 1
            with open(os.path.join(out_dir, f"project-{n:02d}.jsonl"), "w", encoding="utf-8") as f:
                f.writelines(json.dumps(r) + "\n" for r in rows)
            total += len(rows)
            print(f"{project}: {len(rows)} sessions")
    print(f"extract: {total} sessions in {out_dir}")


if __name__ == "__main__":
    main()
