#!/usr/bin/env python3
"""Reference check for file moves (spec 0072 AC-1): prove no path that points into this repo broke.

  ref-check.py snapshot --out FILE [--repo DIR] [--home DIR] [--link-root DIR]
      every pointer into the repo that resolves now: tracked text tokens, spec **Paths:** globs, links under
      ~/.claude/skills, ~/.claude/commands, ~/.local/bin, strings in ~/.claude/settings.json
  ref-check.py verify SNAPSHOT (--map FILE | --map-from-git BASE) [--repo DIR] [--home DIR]
      exit 1 and list each pointer that no longer resolves, unless its referrer now names the mapped new path.
      FILE has `old -> new` lines; --map-from-git reads them from `git diff -M --name-status BASE`.
  ref-check.py check FILE...      list the pointers in these files that do not resolve (a card's citations)
  ref-check.py --test

--link-root is the checkout the live links point into (default: the repo's realpath); set it when the repo is
a worktree and the links still point at the main checkout. Python 3 standard library only."""
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TOP = ("bin", "config", "claude-home", "runner", "scripts", "tools", "docs", "tests", "map", "_archive")
# The fourth is how ~/.claude/settings.json really names the repo (the ~/claude-config link, expanded).
SPELLINGS = ("~/claude-config/", "$HOME/claude-config/", "/home/santiago/dotfiles/claude-config/",
             "/home/santiago/claude-config/")
# History and frozen or vendored trees are not read for references (AC-1).
SKIP_PREFIX = ("docs/specs/", "docs/reviews/", "docs/briefs/", "_archive/", "claude-home/agents/",
               "claude-home/rules/ecc/", "claude-home/skills/anti-ai-writing/")
LIVE_LINK_DIRS = (".claude/skills", ".claude/commands", ".local/bin")
GLOB = re.compile(r"[*?\[]")
LINE = re.compile(r"^(.*?):(\d+)(?:-(\d+))?$")
SPAN = re.compile(r"`([^`\n]+)`|\]\(([^)\s]+)\)")


def sh(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout


class Tree:
    """The tracked files of a repo (the index, so staged moves count) and what exists in it."""

    def __init__(self, repo):
        self.repo = Path(repo)
        self.files = [f for f in sh(["git", "ls-files", "-z"], self.repo).split("\0") if f]
        self.set = set(self.files)
        self.dirs = {str(p) for f in self.files for p in Path(f).parents}

    def exists(self, target):
        """target is repo relative, maybe `path:line`, maybe a glob, maybe a directory."""
        m = LINE.match(target)
        line = None
        if m:
            target, line = m.group(1), int(m.group(2))
        target = target.rstrip("/")
        if GLOB.search(target):
            return any(fnmatch.fnmatchcase(f, target) for f in self.files)
        if target in self.dirs:
            return line is None
        if target not in self.set:
            return False
        if line is not None:
            try:
                return len((self.repo / target).read_text(errors="replace").splitlines()) >= line
            except OSError:
                return False
        return True


def repo_target(word):
    """The repo relative path a token points at, or None when it is not a pointer into this repo."""
    word = word.strip("\"'()[]<>,;.:!")
    for s in SPELLINGS:
        if word.startswith(s):
            word = word[len(s):]
            break
    else:
        if not any(word.startswith(t + "/") for t in TOP):
            return None
    word = word.split("#", 1)[0]
    if not word or re.search(r"[<>{}$|\"']|\.\.\.", word):
        return None
    return word


def text_pointers(repo, files, skip=SKIP_PREFIX):
    """(referrer, target) for every backticked or link token in these tracked files, fenced blocks left out."""
    out = []
    for f in files:
        p = Path(repo) / f
        if f.startswith(skip) or p.is_symlink():
            continue
        try:
            if p.stat().st_size > 2_000_000:
                continue
            text = p.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        fenced = False
        for ln in text.splitlines():
            if f.endswith(".md") and ln.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            for m in SPAN.finditer(ln):
                for word in (m.group(1) or m.group(2)).split():
                    t = repo_target(word)
                    if t:
                        out.append((f, t))
    return out


def spec_pointers(tree):
    out = []
    for f in tree.files:
        if not (f.startswith("docs/specs/") and f.endswith(".md")):
            continue
        for ln in (tree.repo / f).read_text(errors="replace").splitlines():
            if ln.startswith("**Paths:**"):
                out += [(f, g) for g in re.findall(r"`([^`]+)`", ln)]
                break
    return out


def link_pointers(home, link_root):
    out = []
    root = os.path.realpath(link_root)
    for d in (Path(home) / x for x in LIVE_LINK_DIRS):
        if not d.is_dir():
            continue
        for e in sorted(d.iterdir()):
            if e.is_symlink():
                real = os.path.realpath(e)
                if real.startswith(root + os.sep):
                    out.append((str(e), os.path.relpath(real, root)))
    return out


def settings_pointers(home, spellings=None):
    p = Path(home) / ".claude" / "settings.json"
    out = []
    if not p.is_file():
        return out
    sp = tuple(spellings or SPELLINGS)

    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str):
            for word in v.split():
                if word.startswith(sp):
                    for s in sp:
                        if word.startswith(s):
                            out.append((str(p), word[len(s):]))
                            break
    walk(json.loads(p.read_text()))
    return out


def snapshot(repo, home, link_root, out, spellings=None):
    tree = Tree(repo)
    kinds = {"text": text_pointers(repo, tree.files), "spec-paths": spec_pointers(tree),
             "link": link_pointers(home, link_root), "settings": settings_pointers(home, spellings)}
    pointers, dangling = [], []
    for kind, items in kinds.items():
        for ref, target in sorted(set(items)):
            # a link resolved when it was read; a spec saying `none` governs no file
            ok = kind == "link" or (kind == "spec-paths" and target == "none") or tree.exists(target)
            (pointers if ok else dangling).append({"kind": kind, "referrer": ref, "target": target})
    Path(out).write_text(json.dumps({"pointers": pointers, "dangling_before": dangling}, indent=1) + "\n")
    counts = {k: sum(p["kind"] == k for p in pointers) for k in kinds}
    print(f"snapshot: {len(pointers)} pointers {counts}, {len(dangling)} already dangling (left out)")
    return 0


def parse_map(text):
    m = {}
    for ln in text.splitlines():
        if " -> " in ln:
            old, new = ln.split(" -> ", 1)
            m[old.strip()] = new.strip()
    return m


def map_from_git(repo, base):
    m = {}
    for ln in sh(["git", "diff", "-M", "--name-status", base], repo).splitlines():
        parts = ln.split("\t")
        if parts[0].startswith("R"):
            m[parts[1]] = parts[2]
    return m


def mapped(target, moves):
    """The new spelling of a file, directory or glob target, from per file moves; None when nothing moved."""
    m = LINE.match(target)
    suffix = ""
    if m:
        target, suffix = m.group(1), target[len(m.group(1)):]
    t = target.rstrip("/")
    lit = GLOB.split(t, 1)[0]
    if not lit:
        return None
    for old, new in moves.items():
        if old.startswith(lit):
            tail = old[len(lit):]
            if new.endswith(tail):
                # a folder token keeps its slash, so `bin/` maps to `tools/bin/`, the token the referrer now holds
                return new[:len(new) - len(tail)] + t[len(lit):] + ("/" if target.endswith("/") else "") + suffix
    return None


def _token(text, path):
    """path appears as a whole path in text, bare or after a home spelling (`~/claude-config/<path>`): not inside a
    longer path, and not as path:line of another pointer."""
    lead = "".join("|(?<=" + re.escape(s) + ")" for s in SPELLINGS)
    return re.search(r"(?:(?<![\w./-])" + lead + ")" + re.escape(path) + r"(?![\w/-]|:\d)", text) is not None


def verify(snap, moves, repo):
    tree = Tree(repo)
    bad = []
    for p in json.loads(Path(snap).read_text())["pointers"]:
        kind, ref, target = p["kind"], p["referrer"], p["target"]
        if kind in ("text", "spec-paths"):
            ref = moves.get(ref, ref)
            if ref.startswith("_archive/"):
                continue  # frozen
        if kind == "spec-paths" and target == "none":
            continue
        if tree.exists(target):
            continue
        new = mapped(target, moves)
        if new and tree.exists(new):
            if kind in ("text", "spec-paths"):
                # whole tokens, and the old one gone: a fixed pointer beside a stale one still breaks
                if kind == "text":
                    f = tree.repo / ref
                    text = f.read_text(errors="replace") if f.is_file() else ""
                    if _token(text, new) and not _token(text, target):
                        continue
                else:
                    toks = {t for f, t in spec_pointers(tree) if f == ref}
                    if new in toks and target not in toks:
                        continue
            elif kind == "settings":
                if new in Path(ref).read_text():
                    continue
            elif os.path.relpath(os.path.realpath(ref), os.path.realpath(repo)) == new:
                continue
        bad.append(f"{kind}: {ref} -> {target}" + (f" (moved to {new})" if new else ""))
    for b in bad:
        print("BROKEN", b)
    print(f"verify: {len(bad)} broken pointers")
    return 1 if bad else 0


def check(repo, files):
    """A card is checked wherever it lives, so no folder is skipped here."""
    tree = Tree(repo)
    rels = [os.path.relpath(os.path.realpath(f), os.path.realpath(repo)) for f in files]
    bad = 0
    for ref, target in sorted(set(text_pointers(repo, rels, skip=()))):
        if not tree.exists(target):
            print(f"MISSING {ref}: {target}")
            bad += 1
    print(f"check: {bad} missing")
    return 1 if bad else 0


def _git(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


def _out(fn, *a):
    """(exit code, printed text) of fn(*a)."""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


def selftest():
    fails = []

    def expect(name, cond):
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        repo, home = tmp / "repo", tmp / "home"
        files = {
            "bin/tool.sh": "echo\n",
            "scripts/old.py": "a\nb\nc\n",
            "scripts/fenced.py": "x\n",
            "docs/guide.md": "See `scripts/old.py` and [t](bin/tool.sh) and `scripts/old.py:3` and `scripts/*.py`.\n"
                             "```\n`scripts/fenced.py`\n```\nPlaceholder `docs/<x>.md`. Outside `src/other.md`.\n",
            "docs/specs/0001-a/index.md": "# a\n**Paths:** `scripts/old.py`, `bin/**`\n",
            "docs/specs/0002-b.md": "**Paths:** none\n",
            "docs/specs/0003-c/index.md": "history `bin/tool.sh` is not read\n",
            "_archive/frozen.md": "`bin/tool.sh` frozen\n",
            "claude-home/agents/v.md": "`bin/tool.sh` vendored\n",
        }
        for f, c in files.items():
            (repo / f).parent.mkdir(parents=True, exist_ok=True)
            (repo / f).write_text(c)
        _git(repo, "init", "-q")
        _git(repo, "add", ".")
        _git(repo, "commit", "-qm", "base")
        for d in (".claude/skills", ".claude/commands", ".local/bin"):
            (home / d).mkdir(parents=True)
        os.symlink(repo / "scripts/old.py", home / ".claude/skills/s")
        os.symlink(repo / "bin/tool.sh", home / ".local/bin/tool")
        os.symlink("/usr/bin/env", home / ".local/bin/elsewhere")
        spell = SPELLINGS + (f"{repo}/",)
        (home / ".claude/settings.json").write_text(json.dumps(
            {"hooks": [{"command": f"{repo}/scripts/old.py --x"}, {"command": "~/claude-config/bin/tool.sh"},
                       {"command": "ls"}]}))
        snap = tmp / "snap.json"
        snapshot(repo, home, repo, snap, spell)
        by = {}
        for p in json.loads(snap.read_text())["pointers"]:
            by.setdefault(p["kind"], []).append((p["referrer"], p["target"]))
        t = by.get("text", [])
        expect("text token kept", ("docs/guide.md", "scripts/old.py") in t)
        expect("text link kept", ("docs/guide.md", "bin/tool.sh") in t)
        expect("path:line kept", ("docs/guide.md", "scripts/old.py:3") in t)
        expect("glob kept", ("docs/guide.md", "scripts/*.py") in t)
        expect("fenced block skipped", not any("fenced" in x[1] for x in t))
        expect("placeholder skipped", not any("<x>" in d["target"] for d in json.loads(snap.read_text())["dangling_before"]))
        expect("non repo token skipped", not any("src/other" in x[1] for x in t))
        expect("history, archive, vendored skipped", not any(x[0].startswith(SKIP_PREFIX) for x in t))
        expect("spec paths kept", ("docs/specs/0001-a/index.md", "bin/**") in by.get("spec-paths", []))
        expect("link under repo kept, link elsewhere left out", len(by.get("link", [])) == 2)
        expect("settings kept", len(by.get("settings", [])) == 2)
        expect("verify clean", verify(snap, {}, repo) == 0)

        (repo / "scripts/old.py").write_text("a\n")
        expect("path:line breaks when the line is gone", _out(verify, snap, {}, repo)[0] == 1)
        (repo / "scripts/old.py").write_text("a\nb\nc\n")

        (repo / "lib").mkdir()
        _git(repo, "mv", "scripts/old.py", "lib/old.py")
        moves = {"scripts/old.py": "lib/old.py"}
        rc, body = _out(verify, snap, moves, repo)
        expect("verify exit 1 after a move", rc == 1)
        for kind in ("text:", "spec-paths:", "link:", "settings:"):
            expect(f"{kind} pointer reported", f"BROKEN {kind}" in body)
        expect("report names the new path", "moved to lib/old.py" in body)

        with (repo / "docs/guide.md").open("a") as f:
            f.write("See `lib/old.py` too.\n")
        rc, body = _out(verify, snap, moves, repo)
        expect("a stale pointer beside a fixed one is still reported",
               "BROKEN text: docs/guide.md -> scripts/old.py (moved to lib/old.py)\n" in body)

        g = (repo / "docs/guide.md").read_text().replace("scripts/old.py", "lib/old.py").replace(
            "scripts/*.py", "lib/*.py")
        (repo / "docs/guide.md").write_text(g)
        s = (repo / "docs/specs/0001-a/index.md").read_text().replace("scripts/old.py", "lib/old.py")
        (repo / "docs/specs/0001-a/index.md").write_text(s)
        os.remove(home / ".claude/skills/s")
        os.symlink(repo / "lib/old.py", home / ".claude/skills/s")
        (home / ".claude/settings.json").write_text(json.dumps(
            {"hooks": [{"command": f"{repo}/lib/old.py --x"}, {"command": "~/claude-config/bin/tool.sh"}]}))
        rc, body = _out(verify, snap, moves, repo)
        expect("verify clean once referrers name the new path", rc == 0)

        _git(repo, "mv", "docs/guide.md", "_archive/guide.md")
        (repo / "_archive/guide.md").write_text("`scripts/old.py` frozen\n")
        expect("a referrer moved into _archive is frozen",
               verify(snap, {**moves, "docs/guide.md": "_archive/guide.md"}, repo) == 0)

        (repo / "docs/card.md").write_text("`bin/tool.sh` `bin/nope.sh` `bin/tool.sh:99`\n")
        _git(repo, "add", "docs/card.md")
        rc, body = _out(check, repo, [repo / "docs/card.md"])
        expect("check exit 1", rc == 1)
        expect("check lists both missing citations", "bin/nope.sh" in body and "bin/tool.sh:99" in body)
        expect("check lists only the missing", "docs/card.md: bin/tool.sh\n" not in body)

        # spec 0077 AC-14: a whole folder moves one level down; a home spelled token and a folder token follow it
        r2 = tmp / "repo2"
        (r2 / "bin").mkdir(parents=True)
        (r2 / "bin/t.sh").write_text("echo\n")
        (r2 / "docs").mkdir()
        (r2 / "docs/h.md").write_text("Run `~/claude-config/bin/t.sh` from `bin/`.\n")
        _git(r2, "init", "-q")
        _git(r2, "add", ".")
        _git(r2, "commit", "-qm", "base")
        snap2 = tmp / "snap2.json"
        _out(snapshot, r2, tmp / "nohome", r2, snap2)
        (r2 / "tools").mkdir()
        _git(r2, "mv", "bin", "tools/bin")
        moves2 = {"bin/t.sh": "tools/bin/t.sh"}
        rc, body = _out(verify, snap2, moves2, r2)
        expect("folder move: stale home and folder tokens reported",
               rc == 1 and "-> bin/t.sh" in body and "-> bin/ (moved to tools/bin/)" in body)
        (r2 / "docs/h.md").write_text("Run `~/claude-config/tools/bin/t.sh` from `tools/bin/`.\n")
        expect("folder move: home spelled and folder tokens naming the new path pass", verify(snap2, moves2, r2) == 0)
    for f in fails:
        print("FAIL", f)
    print("ref-check self check:", "FAILED" if fails else "ok")
    return 1 if fails else 0


def main(argv):
    if argv and argv[0] == "--test":
        return selftest()
    import argparse
    ap = argparse.ArgumentParser(prog="ref-check.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("snapshot", "verify", "check"):
        s = sub.add_parser(name)
        s.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
        s.add_argument("--home", default=str(Path.home()))
        if name == "snapshot":
            s.add_argument("--out", required=True)
            s.add_argument("--link-root")
        elif name == "verify":
            s.add_argument("snapshot")
            g = s.add_mutually_exclusive_group(required=True)
            g.add_argument("--map")
            g.add_argument("--map-from-git", metavar="BASE")
        else:
            s.add_argument("files", nargs="+")
    a = ap.parse_args(argv)
    if a.cmd == "snapshot":
        return snapshot(a.repo, a.home, a.link_root or a.repo, a.out)
    if a.cmd == "verify":
        moves = parse_map(Path(a.map).read_text()) if a.map else map_from_git(a.repo, a.map_from_git)
        return verify(a.snapshot, moves, a.repo)
    return check(a.repo, a.files)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
