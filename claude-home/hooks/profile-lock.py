#!/usr/bin/env python3
"""PreToolUse on Edit, Write, MultiEdit, NotebookEdit (spec 0081 AC-10, AC-11, AC-14): the active profile's edit list.

The target path is resolved through links. Outside the repo and outside ~/.claude: allowed (your own projects).
Under ~/.claude: Claude's own working folders are allowed; everything else (core copies, state/, private/) is denied;
a path that resolves into the repo is judged as a repo path, one in a framework folder (jjstack, gstack) is denied.
Inside the repo: allowed when it matches the profile's `editable`. A profile.json is written only through
claude-config.py commands (unless the profile may edit everything), and a profile that is not an owner never writes
its own shared folder: the person gets a custom copy instead.

Fails open on bad input. The one exception: no readable state/profile.json while this hook is wired (install wires
it and writes the state together) denies writes in the repo and ~/.claude, since allowing would unlock the core.
Exit 2 with the reason on stderr blocks the call. `--test` runs the self checks.
"""
import fnmatch
import json
import os
import sys
import tempfile
from pathlib import Path

# Claude's own working folders under ~/.claude (memory, plans, todos, background job scratch). Everything else there is
# denied: many live files run code (settings.local.json hooks, plugins/, a status line script), so a deny list leaks.
OWN_LIVE = {"projects", "plans", "todos", "jobs"}


def under(path, root):
    return path == root or root in path.parents


def framework_dirs(repo):
    try:
        m = json.loads((repo / "tools" / "config" / "manifest.json").read_text())
        return [Path(os.path.expanduser(f["dir"])).resolve() for f in m.get("frameworks", {}).values() if f.get("dir")]
    except (OSError, ValueError, AttributeError, TypeError):
        return []


def judge_repo(rel, s):
    name, editable = s.get("name"), s.get("editable") or []
    if fnmatch.fnmatch(rel, "profiles/*/profile.json") and editable != ["**"]:
        return f"locked core (profile {name}): a profile file changes only through claude-config.py profile commands"
    if s.get("owner") is not True and rel.startswith(f"profiles/{name}/"):
        return (f"{name} is shared. Make the person's own copy now: propose a short name, let them change it, then run "
                f"claude-config.py profile custom <name> and apply the change there.")
    if any(fnmatch.fnmatch(rel, p) for p in editable):
        return None
    return f"locked core (profile {name}): ask the owner to change {rel}"


def decide(data, live, state):
    """The reason to deny the write, or None to allow it. `state` is the parsed state file, or None when missing."""
    ti = data.get("tool_input") or {}
    raw = ti.get("file_path") or ti.get("notebook_path")
    if not isinstance(raw, str) or not raw:
        return None
    p = Path(os.path.expanduser(raw))
    if not p.is_absolute():
        p = Path(data.get("cwd") or os.getcwd()) / p
    real = Path(os.path.realpath(p))
    live = Path(os.path.realpath(live))
    if not isinstance(state, dict):
        guess = live / "skills" / "claude-config"
        repo = Path(os.path.realpath(guess)).parents[2] if guess.is_symlink() else None
        if under(real, live) or (repo and under(real, repo)):
            return "profile state missing: run install"
        return None
    repo = Path(os.path.realpath(state.get("repo") or "/nonexistent"))
    if under(real, repo):
        return judge_repo(real.relative_to(repo).as_posix(), state)
    if under(real, live):
        top = real.relative_to(live).parts[0] if real != live else ""
        if top in OWN_LIVE:
            return None
        return f"locked core (profile {state.get('name')}): {real} is live config; change the repo and run install"
    if any(under(real, d) for d in framework_dirs(repo)):
        return f"locked core (profile {state.get('name')}): {real} belongs to a framework"
    return None


def read_state(live):
    try:
        s = json.loads((Path(live) / "state" / "profile.json").read_text())
        return s if isinstance(s, dict) else None
    except (OSError, ValueError):
        return None


def main_text(raw, live):
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return 0
        reason = decide(data, live, read_state(live))
    except Exception:
        return 0
    if reason:
        print(reason, file=sys.stderr)
        return 2
    return 0


def selftest():
    with tempfile.TemporaryDirectory() as t:
        t = Path(os.path.realpath(t))
        repo, live, own = t / "repo", t / "live", t / "work"
        for d in (repo / "claude-home/skills/design", repo / "tools/bin", repo / "profiles/creator/rules",
                  live / "skills", live / "projects", live / "state", own):
            d.mkdir(parents=True)
        (live / "skills" / "design").symlink_to(repo / "claude-home/skills/design")
        (live / "skills" / "claude-config").symlink_to(repo / "claude-home/skills/design")
        creator = {"name": "creator", "owner": False, "editable": ["claude-home/skills/design/**", "profiles/custom-*/**"],
                   "repo": str(repo)}
        engineer = {"name": "engineer", "owner": True, "editable": ["**"], "repo": str(repo)}
        w = lambda path: {"tool_name": "Write", "tool_input": {"file_path": str(path)}}

        def check(label, got, want):
            assert (got is None) == (want is None) and (want is None or want in got), f"{label}: {got!r}"

        check("allowed outside", decide(w(own / "a.txt"), live, creator), None)
        check("allowed editable", decide(w(repo / "claude-home/skills/design/SKILL.md"), live, creator), None)
        check("denied core", decide(w(repo / "tools/bin/install.sh"), live, creator),
              "locked core (profile creator): ask the owner to change tools/bin/install.sh")
        check("denied own shared profile", decide(w(repo / "profiles/creator/rules/x.md"), live, creator),
              "creator is shared. Make the person's own copy now")
        check("denied profile file", decide(w(repo / "profiles/custom-ana/profile.json"), live, creator),
              "a profile file changes only through claude-config.py")
        check("allowed with owner", decide(w(repo / "tools/bin/install.sh"), live, engineer), None)
        check("link into the repo resolved", decide(w(live / "skills/design/SKILL.md"), live, creator), None)
        check("link into the repo judged", decide(
            {"tool_name": "Edit", "tool_input": {"file_path": "x.md"}, "cwd": str(live / "skills/design")}, live,
            dict(creator, editable=[])), "locked core (profile creator)")
        check("live copy denied", decide(w(live / "settings.json"), live, engineer), "is live config")
        check("state denied", decide(w(live / "state/profile.json"), live, engineer), "is live config")
        check("local settings denied", decide(w(live / "settings.local.json"), live, creator), "is live config")
        check("plugins denied", decide(w(live / "plugins/p/hooks/h.json"), live, creator), "is live config")
        check("memory allowed", decide(w(live / "projects/x/memory/m.md"), live, creator), None)
        check("job scratch allowed", decide(w(live / "jobs/j1/tmp/a.py"), live, creator), None)
        check("notebook", decide({"tool_name": "NotebookEdit", "tool_input": {"notebook_path": str(repo / "tools/n.ipynb")}},
                                 live, creator), "locked core")
        check("state missing in live", decide(w(live / "projects/m.md"), live, None), "profile state missing: run install")
        check("state missing in repo", decide(w(repo / "README.md"), live, None), "profile state missing: run install")
        check("state missing outside", decide(w(own / "a.txt"), live, None), None)
        assert main_text("{not json", live) == 0
        assert main_text(json.dumps({"tool_input": "x"}), live) == 0
        (live / "state" / "profile.json").write_text(json.dumps(creator))
        assert main_text(json.dumps(w(repo / "tools/bin/install.sh")), live) == 2
        assert main_text(json.dumps(w(own / "a.txt")), live) == 0
    print("profile-lock: all self-checks passed")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        selftest()
        sys.exit(0)
    sys.exit(main_text(sys.stdin.read(), os.environ.get("CLAUDE_LIVE_DIR") or os.path.expanduser("~/.claude")))
