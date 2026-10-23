#!/usr/bin/env python3
"""live-tick: a scope box ending ` · live` is ticked only when its files are live (spec 0075).

PreToolUse hook on Edit|Write|MultiEdit. Reads the hook JSON on stdin; when the edit ticks a live
box in docs/scope/ or .workflow/scope/ of a repo holding tools/bin/claude-config.py, it compares the
files that box names with ~/.claude and with `claude-config drift`, and prints a PreToolUse deny
while any differ. Any error inside the hook lets the edit through and logs one line (AC-6).
`--test` runs the self checks. Python 3 stdlib only.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TIMEOUT = 60
MAX_LINES = 5
LIVE_BOX = re.compile(r"^[ \t]*- \[([ xX])\] .* · live( · .*)?$", re.M)
PATHS = re.compile(r"(?:claude-home/|~/\.claude/)[\w./-]*[\w/-]")
GROUP = {"rules": "rule", "agents": "agent", "hooks": "hook", "scripts": "script", "skills": "skill",
         "commands": "command", "CLAUDE.md": "instructions", "settings.json": "setting",
         "settings.local.json": "setting"}


def home():
    return os.environ.get("HOME") or os.path.expanduser("~")


def log_error(text):
    d = os.path.join(home(), ".claude", "state", "live-tick")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "errors.log"), "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {text}\n")


def find_repo(path):
    """The folder holding tools/bin/claude-config.py above path, and path relative to it."""
    real = Path(os.path.realpath(path))
    for d in real.parents:
        if (d / "tools" / "bin" / "claude-config.py").is_file():
            return d, real.relative_to(d).as_posix()
    return None, None


def is_trusted(repo):
    """Drift runs the repo's own script, so only the owner's clone and its worktrees (same git common dir) qualify."""
    clone = os.path.join(home(), "claude-config")
    if os.path.realpath(repo) == os.path.realpath(clone):
        return True
    try:
        r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--git-common-dir"],
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0 and os.path.realpath(os.path.join(repo, r.stdout.strip())) == \
        os.path.realpath(os.path.join(clone, ".git"))


def new_text(tool, ti, old):
    if tool == "Write":
        return ti["content"]
    edits = ti["edits"] if tool == "MultiEdit" else [ti]
    text = old
    for e in edits:
        n = -1 if e.get("replace_all") else 1
        text = text.replace(e["old_string"], e["new_string"], n)
    return text


def ticked(text):
    return {m.group(0).strip() for m in LIVE_BOX.finditer(text) if m.group(1) in "xX"}


def direct(rel, repo):
    """AC-2 (a): the repo file and the live file both exist and are byte equal."""
    parts = rel.split("/")
    first = parts[0]
    if first.startswith("settings") or first == "mods":
        return []  # settings differ by design (tools/bin/sync.sh strips them); mods are linked by hand; drift decides
    g = GROUP.get(first, first)
    a, live = repo / "claude-home" / rel, Path(home()) / ".claude"
    b = live / rel
    if first == "skills" and len(parts) > 1:
        rn, ln = repo / "claude-home" / "skills" / parts[1], live / "skills" / parts[1]
        if not rn.exists() and not os.path.lexists(ln):
            return [(g, parts[1], "not found")]
        if not rn.exists():
            return [(g, parts[1], "missing in the repo")]
        if not os.path.lexists(ln):
            return [(g, parts[1], "missing live")]
        if os.path.realpath(ln) != os.path.realpath(rn):
            return [(g, parts[1], "in the repo, but live is not a link to it")]
        return [] if a.exists() else [(g, parts[1], "not found")]
    if not a.exists() and not b.exists():
        return [(g, rel, "not found")]
    if not b.exists():
        return [(g, rel, "missing live")]
    if not a.exists():
        return [(g, rel, "missing in the repo")]
    pairs = [(rel, a, b)]
    if a.is_dir():
        pairs = [(f"{rel.rstrip('/')}/{f.relative_to(a).as_posix()}", f, b / f.relative_to(a))
                 for f in sorted(a.rglob("*"))
                 if f.is_file() and not {"__pycache__", ".in_use"} & set(f.relative_to(a).parts)]
    out = []
    for name, x, y in pairs:
        if not y.is_file():
            out.append((g, name, "missing live"))
        elif x.read_bytes() != y.read_bytes():
            out.append((g, name, "differs"))
    return out


def run_drift(repo):
    """Parsed drift lines (group, name, reason), or the string reason drift did not run.
    Only the trusted clone's script runs, and it reads only the trusted clone: drift's settings check runs
    REPO/tools/scripts/private-names.py, so CLAUDE_CONFIG_REPO would run the found repo's code. A worktree tick
    is therefore judged against the clone's main files, where live installs come from."""
    script = os.path.join(os.path.realpath(os.path.join(home(), "claude-config")), "tools", "bin", "claude-config.py")
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_REPO"}
    try:
        r = subprocess.run([sys.executable, "-I", script, "drift"], capture_output=True, text=True,
                           timeout=TIMEOUT, env=env)
    except subprocess.TimeoutExpired:
        return f"timed out after {TIMEOUT}s"
    if r.returncode not in (0, 1):
        last = (r.stderr + r.stdout).strip().splitlines()[-1:] or [""]
        return f"exit {r.returncode}: {last[0]}"
    out, group = [], ""
    for line in r.stdout.splitlines():
        if line.startswith("  ") and ": " in line:
            name, _, why = line[2:].rpartition(": ")
            out.append((group, name, why))
        elif line.endswith(":") and not line.startswith(" "):
            group = line[:-1]
    return out


def drift_matches(rel, items):
    parts = rel.split("/")
    first = parts[0]
    if first.startswith("settings"):
        return [i for i in items if i[0] == "setting" and i[1].split(":")[0] == first]
    if first == "skills" and len(parts) > 1:
        return [i for i in items if i[0] == "skill" and i[1] == parts[1]]
    base = rel.rstrip("/")
    return [i for i in items if i[0] == GROUP.get(first, first) and (i[1] == base or i[1].startswith(base + "/"))]


def deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def check(data):
    tool, ti = data["tool_name"], data["tool_input"]
    if tool not in ("Edit", "Write", "MultiEdit"):
        return None
    path = ti["file_path"]
    repo, rel = find_repo(path)
    if repo is None or not is_trusted(repo) or not rel.startswith(("docs/scope/", ".workflow/scope/")):
        return None
    real = os.path.realpath(path)
    old = Path(real).read_text(encoding="utf-8") if os.path.isfile(real) else ""
    new = new_text(tool, ti, old)
    boxes = ticked(new) - ticked(old)
    if not boxes:
        return None
    rels, install = [], False
    for box in sorted(boxes):
        install = install or "tools/bin/install.sh" in box
        for p in PATHS.findall(box):
            r = re.sub(r"^(?:claude-home/|~/\.claude/)", "", p)
            if r and r not in rels:
                rels.append(r)
    if not rels and not install:
        return None
    items = run_drift(repo)
    if isinstance(items, str):
        return deny(f"drift did not run: {items}")
    fails = []
    for r in rels:
        fails += direct(r, repo) + drift_matches(r, items)
    if install:
        fails += [i for i in items if i[2] in ("differs", "missing live")]
    seen, lines = set(), []
    for g, n, why in fails:
        if (g, n) not in seen:
            seen.add((g, n))
            lines.append(f"{g} {n}: {why}")
    if not lines:
        return None
    more = [f"and {len(lines) - MAX_LINES} more"] if len(lines) > MAX_LINES else []
    return deny("\n".join(["live box not live yet:", *lines[:MAX_LINES], *more, "copy or install it, then tick again"]))


def guarded(data):
    try:
        return check(data)
    except Exception as err:  # AC-6: a broken hook must not block every scope edit
        try:
            log_error(f"{type(err).__name__}: {err}")
        except OSError:
            pass
        return None


# ---------------------------------------------------------------- self checks

def self_test():
    failed = []

    def ok(name, cond):
        if not cond:
            failed.append(name)
        print(("ok   " if cond else "FAIL ") + name)

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        os.environ["HOME"] = str(t / "home")
        repo, live = t / "repo", t / "home" / ".claude"
        (repo / "tools" / "bin").mkdir(parents=True)
        (repo / "docs" / "scope").mkdir(parents=True)
        (repo / "claude-home" / "rules").mkdir(parents=True)
        (repo / "claude-home" / "hooks").mkdir()
        (live / "rules").mkdir(parents=True)
        (live / "hooks").mkdir()
        # fake drift: prints drift.out, exits drift.rc, sleeps drift.sleep seconds
        (repo / "tools" / "bin" / "claude-config.py").write_text(
            "import sys,time,pathlib,os\n"
            "r=os.environ.get('CLAUDE_CONFIG_REPO')  # like drift's settings check: runs REPO/tools/scripts/private-names.py\n"
            "if r and os.path.exists(r+'/tools/scripts/private-names.py'): exec(open(r+'/tools/scripts/private-names.py').read())\n"
            "try:\n import hijack\nexcept ImportError:\n pass\np=pathlib.Path(__file__).parent\n"
            "time.sleep(float((p/'sleep').read_text()))\n"
            "sys.stdout.write((p/'out').read_text())\nsys.exit(int((p/'rc').read_text()))\n")
        (t / "home" / "claude-config").symlink_to(repo)  # the one trusted clone
        (repo / "tools" / "bin" / "hijack.py").write_text("import sys\nsys.exit(3)\n")
        scope = repo / "docs" / "scope" / "scope.md"

        def drift(out="drift: none\n", rc=0, sleep=0):
            (repo / "tools" / "bin" / "out").write_text(out)
            (repo / "tools" / "bin" / "rc").write_text(str(rc))
            (repo / "tools" / "bin" / "sleep").write_text(str(sleep))

        def edit(old, new, text, tool="Edit", path=None, **kw):
            (path or scope).write_text(text)
            ti = {"file_path": str(path or scope), "old_string": old, "new_string": new, **kw}
            return guarded({"tool_name": tool, "tool_input": ti})

        def reason(r):
            return r["hookSpecificOutput"]["permissionDecisionReason"] if r else ""

        drift()
        box = "- [ ] Copy it live: `cp claude-home/rules/x.md ~/.claude/rules/x.md` · live\n"
        tick = box.replace("[ ]", "[x]")
        (repo / "claude-home" / "rules" / "x.md").write_text("new")
        (live / "rules" / "x.md").write_text("old")
        drift("rule:\n  rules/x.md: differs\ndrift: 1 item(s)\n", 1)
        r = edit(box, tick, box)
        ok("AC-3 tick of a differing rule is refused", r and r["hookSpecificOutput"]["permissionDecision"] == "deny"
           and "rule rules/x.md: differs" in reason(r) and "copy or install it, then tick again" in reason(r))
        (live / "rules" / "x.md").write_text("new")
        drift()
        ok("AC-2 passes once equal", edit(box, tick, box) is None)

        drift("rule:\n  rules/x.md: differs\ndrift: 1 item(s)\n", 1)
        ok("AC-2b drift line refuses although bytes are equal", "rules/x.md" in reason(edit(box, tick, box)))
        drift()

        hbox = "- [ ] Copy: claude-home/hooks/h.py · live\n"
        (repo / "claude-home" / "hooks" / "h.py").write_text("x")
        r = edit(hbox, hbox.replace("[ ]", "[x]"), hbox)
        ok("AC-2a hook missing live, not in drift, is refused", "hook hooks/h.py: missing live" in reason(r))

        tbox = "- [ ] Copy: ~/.claude/rules/typo.md · live\n"
        ok("AC-2 typo path refused as not found", "not found" in reason(edit(tbox, tbox.replace("[ ]", "[x]"), tbox)))

        ibox = "- [ ] Run `tools/bin/install.sh` · live\n"
        itick = ibox.replace("[ ]", "[x]")
        drift("hook:\n  hooks/gsd.sh: live only\ndrift: 1 item(s)\n", 1)
        ok("AC-2 install box ignores a live only extra", edit(ibox, itick, ibox) is None)
        drift("hook:\n  hooks/gsd.sh: live only\n  hooks/h.py: missing live\ndrift: 2 item(s)\n", 1)
        r = edit(ibox, itick, ibox)
        ok("AC-2 install box refuses a missing file, not the extra",
           "hook hooks/h.py: missing live" in reason(r) and "gsd.sh" not in reason(r))
        drift()

        nbox = "- [ ] Run the e2e probe · live\n"
        drift("rule:\n  rules/x.md: differs\n", 1)
        ok("AC-4 box naming nothing passes", edit(nbox, nbox.replace("[ ]", "[x]"), nbox) is None)

        drift("", 2)
        ok("AC-5 failing drift refuses", "drift did not run: exit 2" in reason(edit(box, tick, box)))
        drift("", 0, 3)
        global TIMEOUT
        TIMEOUT = 1
        try:
            ok("AC-5 timed out drift refuses", "drift did not run: timed out" in reason(edit(box, tick, box)))
        finally:
            TIMEOUT = 60
        drift()

        ok("drift runs isolated (-I): a planted module beside it is not imported", edit(box, tick, box) is None)

        stranger = t / "stranger"
        (stranger / "tools" / "bin").mkdir(parents=True)
        (stranger / "docs" / "scope").mkdir(parents=True)
        (stranger / "tools" / "bin" / "claude-config.py").write_text(f"open({str(t / 'marker')!r}, 'w').write('ran')\n")
        subprocess.run(["git", "-C", str(stranger), "init", "-q"], capture_output=True, check=True)
        sscope = stranger / "docs" / "scope" / "scope.md"
        ok("untrusted repo is never run", edit(box, tick, box, path=sscope) is None and not (t / "marker").exists())

        # a real worktree of the trusted repo is checked (AC-1); the stranger above shares no git dir with it
        g = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
        drift("rule:\n  rules/x.md: differs\n", 1)
        scope.write_text(box)
        for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "x"],
                    ["worktree", "add", "-q", str(repo / ".claude" / "worktrees" / "w")]):
            subprocess.run(g + cmd, capture_output=True, check=True)
        wscope = repo / ".claude" / "worktrees" / "w" / "docs" / "scope" / "scope.md"
        ok("worktree of the trusted repo is checked", "rules/x.md" in reason(edit(box, tick, box, path=wscope)))
        drift()

        # a crafted repo whose .git file points into the trusted clone passes is_trusted but its script never runs
        crafted = t / "crafted"
        (crafted / "tools" / "bin").mkdir(parents=True)
        (crafted / "docs" / "scope").mkdir(parents=True)
        (crafted / ".git").write_text(f"gitdir: {repo}/.git/worktrees/w\n")
        (crafted / "tools" / "bin" / "claude-config.py").write_text(f"open({str(t / 'marker2')!r}, 'w').write('ran')\n")
        (crafted / "tools" / "scripts").mkdir()
        (crafted / "tools" / "scripts" / "private-names.py").write_text(f"open({str(t / 'marker3')!r}, 'w').write('ran')\n")
        drift("hook:\n  hooks/zz.py: differs\n", 1)
        r = edit(ibox, itick, ibox, path=crafted / "docs" / "scope" / "scope.md")
        ok("found repo's own script never runs, the trusted drift does",
           not (t / "marker2").exists() and "hooks/zz.py" in reason(r))
        ok("drift never reads the found repo (its private-names.py never runs)", not (t / "marker3").exists())
        drift()

        mbox = "- [ ] Link: claude-home/mods/m/x.ts · live\n"
        ok("mods box left to drift", edit(mbox, mbox.replace("[ ]", "[x]"), mbox) is None)

        (repo / "claude-home" / "rules" / "d" / "__pycache__").mkdir(parents=True)
        (live / "rules" / "d").mkdir()
        (repo / "claude-home" / "rules" / "d" / "a.md").write_text("a")
        (live / "rules" / "d" / "a.md").write_text("a")
        (repo / "claude-home" / "rules" / "d" / "__pycache__" / "c.pyc").write_text("c")
        dbox = "- [ ] Copy: claude-home/rules/d · live\n"
        ok("folder box skips __pycache__", edit(dbox, dbox.replace("[ ]", "[x]"), dbox) is None)

        ok("AC-1 unticking edit passes", edit(tick, box, tick) is None)
        other = repo / "notes.md"
        drift("rule:\n  rules/x.md: differs\n", 1)
        ok("AC-1 edit in a non scope file passes", edit(box, tick, box, path=other) is None)

        drift("rule:\n  rules/x.md: differs\n", 1)
        ok("AC-1 already ticked box left alone", edit("ZZ", "b", tick + "ZZ\n") is None)
        ok("AC-1 tick plus text change caught", edit(box, tick.replace("Copy it", "Copied it"), box) is not None)
        ibx = "  - [ ] Copy it live: `cp claude-home/rules/x.md ~/.claude/rules/x.md` · live\n"
        ok("AC-1 indented box caught", edit(ibx, ibx.replace("[ ]", "[x]"), ibx) is not None)
        ok("AC-1 replace_all caught", edit("[ ]", "[x]", "- [ ] a note\n" + box, replace_all=True) is not None)
        ok("AC-1 MultiEdit caught", edit(None, None, "a\n" + box, tool="MultiEdit",
                                         edits=[{"old_string": "a", "new_string": "b"},
                                                {"old_string": box, "new_string": tick}]) is not None)
        two = box + box.replace("rules/x.md", "rules/y.md")
        (repo / "claude-home" / "rules" / "y.md").write_text("n")
        (live / "rules" / "y.md").write_text("o")
        drift("rule:\n  rules/x.md: differs\n  rules/y.md: differs\n", 1)
        scope.write_text("")
        r = guarded({"tool_name": "Write", "tool_input": {"file_path": str(scope),
                                                          "content": two.replace("[ ]", "[x]")}})
        ok("AC-3 Write ticking two boxes lists both", "rules/x.md" in reason(r) and "rules/y.md" in reason(r))

        errlog = live / "state" / "live-tick" / "errors.log"
        ok("AC-6 crash passes", guarded({"tool_name": "Edit", "tool_input": None}) is None)
        ok("AC-6 crash logs one line", errlog.is_file() and len(errlog.read_text().splitlines()) == 1)

    print("live-tick self checks: " + ("FAILED " + str(len(failed)) if failed else "all passed"))
    return 1 if failed else 0


def main(argv):
    if argv[:1] == ["--test"]:
        return self_test()
    try:
        out = guarded(json.load(sys.stdin))
    except Exception as err:
        try:
            log_error(f"{type(err).__name__}: {err}")
        except OSError:
            pass
        return 0
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
