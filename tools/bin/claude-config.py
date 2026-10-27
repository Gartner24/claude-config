#!/usr/bin/env python3
"""Keep this repo and ~/.claude in step (spec 0048). The /claude-config skill drives it.

  sync              ~/.claude -> repo for the copied kinds (tools/bin/sync.sh does the copy)
  install [--profile <name>] [--accept-overwrite] [--dry-run]
                    repo -> ~/.claude (tools/bin/install.sh does the copy and the links)
  profile [<name> | update | custom <short>]
                    list the profiles, switch to one (install, then open a new chat), pull and reinstall the active one,
                    or make your own copy of the active one and switch to it
  profile-resolve, stage, overwrite, write-state, profile-owner, sync-profile
                    steps tools/bin/install.sh and tools/bin/sync.sh call (spec 0081)
  drift             every item in one place and not the other, or different, by kind; exit 1 when any
  hook-files        exit 1 naming each live settings.json hook command whose file is missing (tools/bin/install.sh)
  update --plan     every git entry whose upstream moved, with its changed files; asks nothing
  update --apply <entry> [--resolved]
                    install upstream now for one entry, your patch merged in; exit 2 on a conflict
  restore           rebuild missing edited skills from upstream at pinned plus their patch; reapply a changed patch (tools/bin/install.sh)
  patches           (re)write the patch of every edited downloaded skill (tools/bin/sync.sh)
  build             manifest entries for every downloaded skill folder: lock file, traced brief, history walk
  docs              write docs/guides/SKILLS.md from the manifest, claude-home/ front matter and tools/config/routing.md
  hash <folder>     the folder hash the manifest's base_hash uses

CLAUDE_LIVE_DIR and CLAUDE_CONFIG_REPO point it at temp trees, for the self checks only.
Python 3 standard library only.
"""
import datetime
import difflib
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(os.environ.get("CLAUDE_CONFIG_REPO") or Path(__file__).resolve().parents[2])
LIVE = Path(os.environ.get("CLAUDE_LIVE_DIR") or Path.home() / ".claude")
HOME_DIR = REPO / "claude-home"
MANIFEST = REPO / "tools" / "config" / "manifest.json"
IGNORE = REPO / "tools" / "config" / "drift-ignore.json"
# The hand written hooks and scripts tools/bin/sync.sh copies; every other live hook belongs to a framework
# or has a manifest entry.
COPIED_FILES = ("hooks/block-destructive.sh", "hooks/review-stack-pre-push", "hooks/plain-panel.py",
                "hooks/context-monitor.js", "hooks/claude-config-reminder.py",
                "hooks/workflow-start.sh", "hooks/handover-start.sh", "hooks/no-jjstack-bar.py", "hooks/chain-catch.py",
                "hooks/live-tick.py", "hooks/skill-rules.py", "hooks/profile-lock.py", "MAP.md",
                "scripts/claude-ram-watch.sh")
# .in_use/<pid> is a marker Claude Code drops in a plugin folder per running session; it used to make 10
# of 12 plugin base_hash values go stale as soon as any session started.
SKIP = {".git", "__pycache__", "node_modules", ".plugin-version", ".in_use"}
# The home path settings.json is committed with; tools/bin/install.sh swaps it for $HOME.
AUTHOR_HOME = "/home/santiago"


def folder_hash(path):
    """sha256 over the sorted relative paths and contents of a folder (or one file), SKIP left out.
    One routine for the manifest's base_hash, drift and update: skills-audit.sh used to hash only
    SKILL.md, so an edit to a reference file or script inside a skill went unseen."""
    path = Path(path)
    h = hashlib.sha256()
    if path.is_file():
        h.update(b"\0" + hashlib.sha256(path.read_bytes()).digest())
        return h.hexdigest()
    files = []
    for root, dirs, names in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in SKIP)
        files += [Path(root) / n for n in names if n not in SKIP]
    for f in sorted(files, key=lambda p: p.relative_to(path).as_posix()):
        rel = f.relative_to(path).as_posix().encode()
        body = os.readlink(f).encode() if f.is_symlink() else f.read_bytes()
        h.update(rel + b"\0" + hashlib.sha256(body).digest())
    return h.hexdigest()


def load_manifest():
    if not MANIFEST.exists():
        return {"version": 1, "frameworks": {}, "entries": {}}
    return json.loads(MANIFEST.read_text())


def framework_dirs(manifest):
    return [Path(os.path.expanduser(f["dir"])).resolve() for f in manifest.get("frameworks", {}).values()
            if f.get("dir")]


def inside(path, dirs):
    return any(path == d or d in path.parents for d in dirs)


def live_items(kind):
    d = LIVE / kind
    return sorted(d.iterdir(), key=lambda p: p.name) if d.is_dir() else []


def linked_kind(kind, manifest, fw, out):
    """skills/, commands/ and workflows/: repo items are linked in, downloaded ones are named in the manifest."""
    label = kind.rstrip("s")
    own = {p.name for p in (HOME_DIR / kind).iterdir()} if (HOME_DIR / kind).is_dir() else set()
    private = LIVE / "private" / kind
    entries = {n: e for n, e in manifest.get("entries", {}).items() if e.get("kind") == label}
    owns = [g for f in manifest.get("frameworks", {}).values() for g in f.get("owns", [])]
    seen = set()
    for p in live_items(kind):
        name = p.name
        if kind == "skills" and name not in own and p.is_dir() and not (p / "SKILL.md").exists() \
                and name not in entries:
            # not a skill (shared files, Claude Code's synced folder); build skips it too. A manifest entry
            # (a mod has no SKILL.md) makes it ours: without that drift said "missing live" for it.
            continue
        seen.add(name)
        real = p.resolve()
        if name in own:
            if not (p.is_symlink() and real == (HOME_DIR / kind / name).resolve()):
                out.append((label, name, "in the repo, but live is not a link to it"))
        elif p.is_symlink() and not p.exists():
            out.append((label, name, "live link is broken"))
        elif inside(real, fw) or any(fnmatch.fnmatch(f"{kind}/{name}", g) for g in owns):
            continue
        elif name in entries:
            e = entries[name]
            if e.get("base_hash") and e["status"] in ("downloaded", "source-unknown") \
                    and folder_hash(p) != e["base_hash"]:
                why = "changed since its base hash (a local override was lost, or it was edited)" \
                    if e["status"] == "source-unknown" else "edited, no patch yet: run sync"
                out.append((label, name, why))
            elif e["status"] == "edited" and e.get("patch") and p.is_dir() and not git(
                    "apply", "-R", "--check", "--binary", "-", cwd=p, check=False,
                    data=patch_path(e).read_bytes() if patch_path(e).exists() else b"x").returncode == 0:
                # The old skills-audit.sh override guard: a reinstall over your edit drops the patch's changes.
                out.append((label, name, "your edit is no longer in it (reinstalled over it?), or its patch is stale: run sync"))
        elif (private / name).exists():
            continue
        else:
            out.append((label, name, "live only: not in the repo, the manifest, a framework or the private store"))
    for name in sorted((own | set(entries)) - seen):
        out.append((label, name, "missing live"))


def copied_files(rels, out, label=None):
    for rel in rels:
        a, b = HOME_DIR / rel, LIVE / rel
        lab = label or rel.split("/")[0].rstrip("s")
        if not a.exists() and not b.exists():
            continue
        if not b.exists():
            out.append((lab, rel, "missing live"))
        elif not a.exists():
            out.append((lab, rel, "live only"))
        elif a.read_bytes() != b.read_bytes():
            out.append((lab, rel, "differs"))


def tree_files(root):
    if not root.is_dir():
        return set()
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


def copied_trees(out):
    # spec 0081: live rules/ is what the active profile builds, not the whole core folder; a repo with no profiles
    # (the self checks' scratch repos) compares the whole folder
    p = current_profile()
    built = profile_rules(p) if p else {f"rules/{r}": HOME_DIR / "rules" / r for r in tree_files(HOME_DIR / "rules")}
    for rel in sorted(set(built) | {f"rules/{r}" for r in tree_files(LIVE / "rules")}):
        live = LIVE / rel
        if rel not in built:
            out.append(("rule", rel, "live only"))
        elif not live.exists():
            out.append(("rule", rel, "missing live"))
        elif built[rel].read_bytes() != live.read_bytes():
            out.append(("rule", rel, "differs"))
    for kind in ("agents", "rules-on-demand"):
        rels = tree_files(HOME_DIR / kind) | tree_files(LIVE / kind)
        copied_files(sorted(f"{kind}/{r}" for r in rels), out, kind.rstrip("s"))


def other_hooks(manifest, fw, out):
    """Live hooks and scripts outside the copied list: framework links or manifest entries, else drift."""
    entries = manifest.get("entries", {})
    owns = [g for f in manifest.get("frameworks", {}).values() for g in f.get("owns", [])]
    for kind in ("hooks", "scripts"):
        for p in live_items(kind):
            rel = f"{kind}/{p.name}"
            if rel in COPIED_FILES or inside(p.resolve(), fw) or any(fnmatch.fnmatch(rel, g) for g in owns):
                continue
            e = entries.get(p.name)
            if e and e.get("kind") == kind.rstrip("s"):
                if e.get("base_hash") and folder_hash(p) != e["base_hash"]:
                    out.append((kind.rstrip("s"), rel, "changed since its base hash"))
                continue
            if (LIVE / "private" / kind / p.name).exists():
                continue
            out.append((kind.rstrip("s"), rel, "live only: not in the repo, the manifest, a framework or the private store"))


def drop(d, dotted):
    head, _, rest = dotted.partition(".")
    if isinstance(d, dict) and head in d:
        if rest:
            drop(d[head], rest)
        else:
            del d[head]


def settings(out):
    """AC-9: live settings after the same transform tools/bin/sync.sh applies, against the repo copy."""
    ignore = json.loads(IGNORE.read_text()) if IGNORE.exists() else []
    checker = REPO / "tools" / "scripts" / "private-names.py"
    for f in ("settings.json", "settings.local.json"):
        repo_f, live_f = HOME_DIR / f, LIVE / f
        if not live_f.exists() or not repo_f.exists():
            if live_f.exists() != repo_f.exists():
                out.append(("setting", f, "missing live" if repo_f.exists() else "live only"))
            continue
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, str(checker), "strip-settings", str(live_f), f"{tmp}/s", f"{tmp}/f"],
                               capture_output=True, text=True, env=dict(os.environ, CLAUDE_LIVE_DIR=str(LIVE)))
            if r.returncode:
                out.append(("setting", f, "could not apply the sync transform: " + (r.stdout + r.stderr).strip()
                            .splitlines()[-1]))
                continue
            live = json.loads(Path(f"{tmp}/s").read_text())
        repo = json.loads(repo_f.read_text().replace(AUTHOR_HOME, str(Path.home())))
        if f == "settings.json" and current_profile():
            repo = profile_settings(repo, current_profile())
        live = json.loads(json.dumps(live).replace(str(Path.home()), str(Path.home())))
        for key in ignore:
            drop(live, key)
            drop(repo, key)
        for key in sorted(set(live) | set(repo)):
            if live.get(key) != repo.get(key):
                out.append(("setting", f"{f}: {key}", "differs" if key in live and key in repo
                            else ("live only" if key in live else "missing live")))


INTERPRETERS = {"bash", "sh", "zsh", "python", "python3", "node"}


def missing_hook_files(settings_path):
    """Each hook command in settings.json whose script path (after `~`/`$HOME`) does not exist, as (path, command).
    A command that does not start with a path, or an interpreter and a path, is skipped."""
    if not settings_path.exists():
        return []
    out = []
    for groups in (json.loads(settings_path.read_text()).get("hooks") or {}).values():
        for g in groups if isinstance(groups, list) else []:
            for c in g.get("hooks") or [] if isinstance(g, dict) else []:
                cmd = c.get("command") if isinstance(c, dict) else None
                try:
                    words = shlex.split(cmd) if isinstance(cmd, str) else []
                except ValueError:
                    continue
                if len(words) > 1 and os.path.basename(words[0]) in INTERPRETERS:
                    words = words[1:]
                if not words:
                    continue
                path = re.sub(r"^(~|\$HOME|\$\{HOME\})(?=/)", lambda m: str(Path.home()), words[0])
                if path.startswith("/") and not Path(path).exists():
                    out.append((path, cmd))
    return out


def hook_files():
    """tools/bin/install.sh verify: exit 1 naming each hook command in live settings.json whose file is missing, skipping
    the live skills folder (jjstack and gstack hooks, which their own installers own); exit 2 when it does not parse."""
    try:
        missing = missing_hook_files(LIVE / "settings.json")
    except ValueError as e:
        print(f"hook-files: {LIVE / 'settings.json'} does not parse: {e}")
        return 2
    skills = LIVE / "skills"
    missing = [(p, c) for p, c in missing if not Path(p).is_relative_to(skills)]
    for path, cmd in missing:
        print(f"missing hook file: {path} (command: {cmd})")
    return 1 if missing else 0


TEMPLATES = HOME_DIR / "skills" / "workflow-builder" / "templates"


def follows_check(manifest):
    """Spec 0076 AC-10: each builder template names the icm-architect commit it was last reviewed against. A pin that
    moved asks for a review. Separate from the upstream hash check, so it stays until the follows lines change."""
    if not TEMPLATES.is_dir():
        return
    e = manifest.get("entries", {}).get("icm-architect")
    if not e:
        print("icm-architect not installed, templates not compared")
        return
    seen = set()
    for f in sorted(TEMPLATES.iterdir()):
        m = re.match(r"(?:<!--|//) follows icm-architect (\S+)", f.read_text().split("\n", 1)[0])
        seen.add(m.group(1) if m else "(no follows line)")
    for old in sorted(seen - {e.get("pinned")}):
        print(f"review workflow-builder templates: they follow icm-architect {old}, the pin is {e.get('pinned')}")


def drift():
    manifest = load_manifest()
    fw = framework_dirs(manifest)
    out = []
    copied_files(["CLAUDE.md"], out, "instructions")
    copied_trees(out)
    copied_files(COPIED_FILES, out)
    other_hooks(manifest, fw, out)
    linked_kind("skills", manifest, fw, out)
    linked_kind("commands", manifest, fw, out)
    # Spec 0076 AC-6: workflows have no manifest entries; a real folder where a link belongs is reported.
    linked_kind("workflows", manifest, fw, out)
    settings(out)
    for path, _ in missing_hook_files(LIVE / "settings.json"):
        out.append(("hook", path, "settings.json hook command names a missing file"))
    last = None
    for kind, name, why in sorted(out):
        if kind != last:
            print(f"{kind}:")
            last = kind
        print(f"  {name}: {why}")
    follows_check(manifest)
    print(f"drift: {len(out)} item(s)" if out else "drift: none")
    return 1 if out else 0


# ---------------------------------------------------------------- upstream (AC-7, AC-10)

STATE = LIVE / "state" / "claude-config.json"
CONFLICTS = LIVE / "state" / "claude-config-conflicts"
PRIVATE_PATCHES = LIVE / "private" / "patches"


class Gone(Exception):
    """A source that cannot be reached: no network, or the repo or commit is gone."""


def git(*args, cwd=None, check=True, data=None):
    r = subprocess.run(["git", *args], cwd=cwd, input=data, capture_output=True,
                       env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
    if check and r.returncode:
        raise Gone(f"git {' '.join(args[:2])}: {r.stderr.decode(errors='replace').strip().splitlines()[-1:]}")
    return r


def url(source):
    """`github:owner/repo` is GitHub over https; anything else (a path, a file:// URL) is used as is."""
    return f"https://github.com/{source[7:]}.git" if source.startswith("github:") else source


def fetch(source, ref, tmp):
    """A shallow repo in tmp holding ref (a commit, or HEAD); returns (repo, commit)."""
    repo = Path(tempfile.mkdtemp(dir=tmp))
    git("init", "-q", cwd=repo)
    git("fetch", "-q", "--depth", "1", url(source), ref, cwd=repo)
    return repo, git("rev-parse", "FETCH_HEAD", cwd=repo).stdout.decode().strip()


def export(repo, commit, path, tmp):
    """The folder `path` at commit, copied out with the standard library (no checkout)."""
    import io
    import tarfile
    out = Path(tempfile.mkdtemp(dir=tmp))
    r = git("archive", "--format=tar", commit, "--", path, cwd=repo, check=False)
    if r.returncode:
        raise Gone(f"{path} is not in {commit[:12]}")
    with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
        t.extractall(out, filter="data")
    if (out / path).is_symlink():
        raise Gone(f"{path} is a link to {os.readlink(out / path)} in {commit[:12]}, renamed upstream")
    return out / path


def upstream(entry, ref, tmp):
    repo, commit = fetch(entry["source"], ref, tmp)
    return export(repo, commit, entry["path"], tmp), commit


def make_patch(base, mine, tmp):
    """AC-7: `git diff --no-index --binary` with relative a/ and b/ names; exit 1 means they differ."""
    work = Path(tempfile.mkdtemp(dir=tmp))
    shutil.copytree(base, work / "a", ignore=shutil.ignore_patterns(*SKIP))
    shutil.copytree(mine, work / "b", ignore=shutil.ignore_patterns(*SKIP))
    r = git("diff", "--no-index", "--binary", "--src-prefix=", "--dst-prefix=", "a", "b", cwd=work, check=False)
    if r.returncode not in (0, 1):
        raise Gone("git diff --no-index failed")
    return r.stdout


def apply_patch(folder, patch):
    """Apply a stored patch inside folder; False when it does not apply."""
    return git("apply", "--binary", "-", cwd=folder, check=False, data=patch).returncode == 0


def files(folder):
    return {p.relative_to(folder).as_posix() for p in Path(folder).rglob("*")
            if p.is_file() and not SKIP & set(p.relative_to(folder).parts)}


def binary(p):
    return b"\0" in p.read_bytes()[:8000]


def merge(base, mine, theirs, out):
    """AC-10: file by file three way merge into out; returns the conflicting paths."""
    conflicts = []
    for rel in sorted(files(base) | files(mine) | files(theirs)):
        b, m, t = (Path(d) / rel for d in (base, mine, theirs))
        dst = Path(out) / rel
        bb, mb, tb = (p.read_bytes() if p.exists() else None for p in (b, m, t))
        if mb == tb:
            result = mb
        elif mb == bb:
            result = tb  # only upstream changed it, added it, or deleted it
        elif tb == bb:
            result = mb  # only you changed it or added it
        elif mb is None or tb is None or bb is None or binary(m) or binary(t):
            # deleted on one side and edited on the other, added on both, or binary on both: yours, marked
            conflicts.append(rel)
            result = mb if mb is not None else tb
        else:
            r = subprocess.run(["git", "merge-file", "-p", "-L", "mine", "-L", "base", "-L", "theirs",
                                str(m), str(b), str(t)], capture_output=True)
            result = r.stdout
            if r.returncode:
                conflicts.append(rel)
        if result is not None:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(result)
            if m.exists() and os.access(m, os.X_OK):
                dst.chmod(0o755)
    return conflicts


def private_name_hit(blob):
    with tempfile.NamedTemporaryFile(suffix=".patch") as f:
        f.write(blob)
        f.flush()
        r = subprocess.run([sys.executable, str(REPO / "tools" / "scripts" / "private-names.py"), "check", f.name],
                           capture_output=True, env=dict(os.environ, CLAUDE_LIVE_DIR=str(LIVE)))
    return r.returncode != 0


def with_header(entry, blob):
    """AC-6: an Apache-2.0 patch opens with a line naming the files it changes (git apply skips it)."""
    if entry.get("license") != "Apache-2.0" or not blob:
        return blob
    changed = [ln.split(" b/", 1)[1] for ln in blob.decode(errors="replace").splitlines() if ln.startswith("diff --git ")]
    return f"# Changed from upstream: {', '.join(changed)}\n".encode() + blob


def store_patch(name, entry, blob):
    """AC-7, AC-8: the patch goes public only for a publish: true entry with no private name in it."""
    blob = with_header(entry, blob)
    public = entry.get("publish") and not private_name_hit(blob)
    path = (REPO / "tools" / "config" / "patches" if public else PRIVATE_PATCHES) / f"{name}.patch"
    for old in (REPO / "tools" / "config" / "patches" / f"{name}.patch", PRIVATE_PATCHES / f"{name}.patch"):
        if old != path and old.exists():
            old.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    entry["patch"] = f"tools/config/patches/{name}.patch" if public else f"~/.claude/private/patches/{name}.patch"


def patch_path(entry):
    p = entry["patch"]
    return Path(os.path.expanduser(p.replace("~/.claude", str(LIVE)))) if p.startswith("~") else REPO / p


def save_manifest(m):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")


def installed(entry, name):
    if entry["kind"] == "plugin":
        return Path((installed_plugins().get(name) or [{}])[0].get("installPath") or PLUGINS / "cache" / name)
    return LIVE / {"skill": "skills", "command": "commands", "hook": "hooks", "agent": "agents"}[entry["kind"]] / name


def numstat(a, b, tmp):
    work = Path(tempfile.mkdtemp(dir=tmp))
    shutil.copytree(a, work / "a", ignore=shutil.ignore_patterns(*SKIP))
    shutil.copytree(b, work / "b", ignore=shutil.ignore_patterns(*SKIP))
    r = git("diff", "--no-index", "--numstat", "--src-prefix=", "--dst-prefix=", "a", "b", cwd=work, check=False)
    return r.stdout.decode().strip().splitlines()


def update_plan():
    m = load_manifest()
    reached, todo = True, 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, e in sorted(m["entries"].items()):
            if e.get("status") == "source-unknown" or not e.get("source"):
                continue
            if e.get("fetch") != "git":
                print(f"{name}: update by hand, not checked ({e.get('install')})")
                continue
            try:
                now, commit = upstream(e, "HEAD", tmp)
            except Gone as err:
                reached = False
                print(f"{name}: source not reached, nothing changes: {err}")
                continue
            ref = e.get("base_hash") if e["status"] != "unpinned" else folder_hash(installed(e, name))
            if folder_hash(now) == ref:
                continue
            todo += 1
            base = installed(e, name) if e["status"] == "unpinned" else None
            if base is None:
                try:
                    base, _ = upstream(e, e["pinned"], tmp)
                except Gone as err:
                    print(f"{name}: pinned commit not reached: {err}")
                    continue
            print(f"{name} ({e['status']}): upstream {commit[:12]}")
            for line in numstat(base, now, tmp):
                added, removed, path = line.split("\t", 2)
                print(f"  +{added} -{removed} {path.split('/', 1)[1] if '/' in path else path}")
    if reached:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        import datetime
        STATE.write_text(json.dumps({"last_upstream_check": datetime.datetime.now(datetime.timezone.utc)
                                    .isoformat(timespec="seconds")}) + "\n")
    follows_check(m)
    print(f"update: {todo} entr{'y' if todo == 1 else 'ies'} to decide")
    return 0


def install_folder(src, dst):
    """Swap a folder in: copy beside, then rename, so a failure never leaves half a skill."""
    tmp = dst.with_name(f".{dst.name}.claude-config-new")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(src, tmp, symlinks=True)
    if dst.is_symlink() or dst.is_file():
        dst.unlink()
    elif dst.exists():
        shutil.rmtree(dst)
    tmp.rename(dst)


def scan(name, live, folder):
    """Spec 0054 AC-7: print what skillspector finds new in the folder about to go live. Never blocks."""
    tool = Path(__file__).resolve().parents[2] / "tools" / "scripts" / "skill-scan.py"
    r = subprocess.run([sys.executable, str(tool), "--against", str(live), str(folder)],
                       capture_output=True, text=True)
    lines = (r.stdout + r.stderr).strip().splitlines() or [f"exit {r.returncode}, no output"]
    if r.returncode == 1 and not lines[0].startswith("scan failed"):
        print(f"{name}: skill scan, new serious findings (static):")
        for line in lines:
            print(f"  {line}")
    else:
        print(f"{name}: skill scan: {lines[0]}")


def update_apply(name, resolved=False):
    m = load_manifest()
    e = m["entries"].get(name)
    if not e or e.get("status") == "source-unknown":
        print(f"{name}: not a manifest entry with a source", file=sys.stderr)
        return 1
    if e.get("fetch") != "git":
        print(f"{name}: update by hand: {e.get('install')}", file=sys.stderr)
        return 1
    live = installed(e, name)
    # Not installed yet (missing, or an empty folder): a first install, never "you deleted every file".
    fresh = not live.is_dir() or not any(live.iterdir())
    conflicts_dir = CONFLICTS / name
    with tempfile.TemporaryDirectory() as tmp:
        try:
            now, commit = upstream(e, "HEAD", tmp)
            if e["status"] in ("downloaded", "edited"):
                base, _ = upstream(e, e["pinned"], tmp)
                if folder_hash(base) != e["base_hash"]:
                    print(f"{name}: upstream at {e['pinned'][:12]} no longer hashes to base_hash; nothing changed")
                    return 1
        except Gone as err:
            print(f"{name}: source not reached, nothing changed: {err}")
            return 1
        if resolved:
            if not conflicts_dir.is_dir():
                print(f"{name}: no conflicts folder to install", file=sys.stderr)
                return 1
            marked = [r for r in files(conflicts_dir) if b"<<<<<<<" in (conflicts_dir / r).read_bytes()]
            if marked:
                print(f"{name}: conflict markers left in: {', '.join(marked)}")
                return 2
            result = conflicts_dir
        elif e["status"] == "edited" or (e["status"] == "downloaded" and fresh is False
                                         and folder_hash(live) != e["base_hash"]):
            # A downloaded entry edited since the last sync is merged too, never replaced.
            result = Path(tempfile.mkdtemp(dir=tmp))
            conflicts = merge(base, live, now, result)
            if conflicts:
                shutil.rmtree(conflicts_dir, ignore_errors=True)
                conflicts_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(result, conflicts_dir)
                print(f"{name}: conflict in {', '.join(conflicts)}; nothing installed, merged files in {conflicts_dir}")
                return 2
        else:
            result = now
        scan(name, live, result)
        install_folder(result, live)
        e["pinned"], e["base_hash"] = commit, folder_hash(now)
        patch = make_patch(now, live, tmp)
        if patch:
            e["status"] = "edited"
            store_patch(name, e, patch)
        else:
            if e.get("patch"):
                patch_path(e).unlink(missing_ok=True)
            e["status"], e["patch"] = "downloaded", None
        save_manifest(m)
    shutil.rmtree(conflicts_dir, ignore_errors=True)
    print(f"{name}: installed upstream {commit[:12]} ({e['status']})")
    return 0


def patches():
    """After a sync: a downloaded or edited entry whose installed copy differs from upstream at pinned
    gets its patch (re)written, and its status moves to edited (or back to downloaded)."""
    m = load_manifest()
    changed, bad = False, 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, e in sorted(m["entries"].items()):
            live = installed(e, name)
            if e["status"] not in ("downloaded", "edited") or e.get("fetch") != "git" or not live.exists():
                continue
            if e["status"] == "downloaded" and folder_hash(live) == e["base_hash"]:
                continue
            try:
                base, _ = upstream(e, e["pinned"], tmp)
            except Gone as err:
                print(f"  {name}: patch not refreshed, upstream not reached: {err}")
                bad = 1
                continue
            blob = make_patch(base, live, tmp)
            old = patch_path(e).read_bytes() if e.get("patch") and patch_path(e).exists() else None
            if blob and with_header(e, blob) != old:
                e["status"] = "edited"
                store_patch(name, e, blob)
                print(f"  {name}: patch written to {e['patch']}")
                changed = True
            elif not blob and e["status"] == "edited":
                patch_path(e).unlink(missing_ok=True)
                e["status"], e["patch"] = "downloaded", None
                print(f"  {name}: equal to upstream again, patch removed")
                changed = True
    if changed:
        save_manifest(m)
    return bad


def previous_patch(e):
    """The patch as of the last commit that changed it to something other than the current text, or None."""
    cur = patch_path(e)
    try:
        rel = cur.relative_to(REPO).as_posix()
    except ValueError:
        return None  # a private patch has no history
    now = cur.read_bytes() if cur.exists() else None
    for sha in git("log", "-n", "2", "--format=%H", "--", rel, cwd=REPO, check=False).stdout.decode().split():
        r = git("show", f"{sha}:{rel}", cwd=REPO, check=False)
        if r.returncode == 0 and r.stdout != now:
            return r.stdout
    return None


def with_patch(base, tmp, patch):
    """A copy of base with patch applied; None when it does not apply."""
    folder = Path(tempfile.mkdtemp(dir=tmp)) / "f"
    shutil.copytree(base, folder)
    return folder if apply_patch(folder, patch) else None


def reapply(name, e, live, tmp):
    """Live exists: equal to upstream plus the current patch stays; equal to plain upstream or to upstream plus
    the previous patch is moved to backups/skills and rebuilt; anything else is refused. Returns 1 on a failure."""
    try:
        base, _ = upstream(e, e["pinned"], tmp)
    except Gone as err:
        print(f"  {name}: skipped, upstream not reached: {err}")
        return 0
    cur = with_patch(base, tmp, patch_path(e).read_bytes())
    if cur is None:
        print(f"  {name}: REFUSED, its patch does not apply to upstream at {e['pinned'][:12]}")
        return 1
    have = folder_hash(live)
    if have == folder_hash(cur):
        return 0
    old = previous_patch(e)
    prev = with_patch(base, tmp, old) if old is not None else None
    if have != folder_hash(base) and not (prev is not None and have == folder_hash(prev)):
        print(f"  REFUSED {name}: live copy has edits not in any patch; run sync first")
        return 0
    backup = LIVE / "backups" / "skills" / f"{name}.{datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(live), str(backup))
    install_folder(cur, live)
    print(f"  {name}: rebuilt from upstream {e['pinned'][:12]} plus its current patch; old copy moved to {backup}")
    return 0


def restore():
    """AC-7: rebuild a missing edited skill from upstream at pinned plus its patch. An installed one is rebuilt
    only when it equals upstream or upstream plus the previous patch (moved to backups first), never otherwise."""
    m = load_manifest()
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, e in sorted(m["entries"].items()):
            live = installed(e, name)
            if e.get("framework"):
                continue
            if live.exists() or live.is_symlink():
                if e["status"] == "edited" and e.get("patch") and live.is_dir() and not live.is_symlink() \
                        and patch_path(e).exists():
                    bad |= reapply(name, e, live, tmp)
                continue
            if e["status"] == "edited":
                try:
                    folder, _ = upstream(e, e["pinned"], tmp)
                except Gone as err:
                    print(f"  {name}: REFUSED, upstream not reached: {err}")
                    bad = 1
                    continue
                if not apply_patch(folder, patch_path(e).read_bytes()):
                    print(f"  {name}: REFUSED, its patch does not apply to upstream at {e['pinned'][:12]}")
                    bad = 1
                    continue
                install_folder(folder, live)
                print(f"  {name}: rebuilt from upstream {e['pinned'][:12]} plus its patch")
            elif e["status"] == "downloaded" or e.get("fetch") == "manual":
                print(f"  {name}: missing; reinstall with: {e.get('install')}")
            else:
                print(f"  {name}: missing; no source to rebuild it from (step 0 backup or the private store)")
    return bad


# ---------------------------------------------------------------- manifest build (AC-5, AC-6, AC-8)

BRIEF = REPO / "docs" / "briefs" / "untraced-skills.md"
LOCK = Path(os.environ.get("CLAUDE_CONFIG_LOCK") or Path.home() / ".agents" / ".skill-lock.json")
CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "claude-config"
WALK = 200


def to_source(u):
    u = u.rstrip(",.;)")
    return "github:" + u[len("https://github.com/"):].removesuffix(".git") if u.startswith("https://github.com/") else u


def spdx(text):
    t = text.strip()
    for key, val in (("MIT", "MIT"), ("Apache-2.0", "Apache-2.0"), ("custom", "custom"), ("none", "none")):
        if t.startswith(key) or (key in ("MIT", "Apache-2.0") and f" {key}" in f" {t}"):
            return val
    return "unknown"


def first_sentence(text):
    text = " ".join(text.split())
    return text.split(". ")[0].rstrip(".") + "." if text else None


def parse_brief(text):
    """name -> {source, path, license, publish, install, fetch, pinned} from the traced brief's group blocks
    (names line, Source:, License:, Publish an edited copy:) and its bullet lines (- names: url, `path`. ...)."""
    import re
    out, block = {}, None

    def emit(b):
        for n in b.get("names", []):
            out[n] = {k: v for k, v in b.items() if k != "names"}

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            block = None
        elif line.startswith("- ") and re.match(r"- [a-z0-9_][a-z0-9_, -]*:", line):
            names, rest = line[2:].split(":", 1)
            u = re.search(r"(https://github\.com/[^\s,]+|file://[^\s,]+)", rest)
            if not u:
                out.update({n.strip(): {"source": None} for n in names.split(",")})  # packshot: author unknown
                continue
            path = re.match(r",\s*`([^`]+)`", rest[u.end():])  # only a path right after the URL
            pip = re.search(r"`(pip install [^`]+)` then `([^`]+)`.*?\(v([\d.]+)\)", rest)
            lic = re.findall(r"\b(MIT|Apache-2\.0)\b", rest)
            b = {"names": [n.strip() for n in names.split(",")], "source": to_source(u.group(1)),
                 "path": path.group(1) if path else ".", "license": lic[0] if lic else "unknown",
                 "publish": not re.search(r"Publish: no", rest, re.I)}
            if pip:
                b.update(fetch="manual", install=f"{pip.group(1)} && {pip.group(2)}", pinned=pip.group(3))
            emit(b)
        elif line.startswith("Source:") and block is not None:
            u = re.search(r"(https://github\.com/[^\s,]+|file://[^\s,]+)", line)
            path = re.search(r"`([^`]+)`", line)
            block.update(source=to_source(u.group(1)) if u else None, path=path.group(1) if path else ".")
            npm = re.search(r"`(npm pack [^`]+)` then `([^`]+)`", line)
            if npm:
                block["install"] = f"{npm.group(1)} && {npm.group(2)}"
        elif line.startswith("License:") and block is not None:
            block["license"] = spdx(line[len("License:"):])
        elif line.startswith("Publish an edited copy:") and block is not None:
            block["publish"] = not line.split(":", 1)[1].strip().upper().startswith("NO")
            emit(block)
            block = None
        elif line and not line.startswith(("#", "-", "3 skills", "Real folders", '"Publish', "Whole file")) \
                and "," in line + "," and " " not in line.replace(", ", ","):
            block = {"names": [n.strip() for n in line.split(",")]}
    for e in out.values():
        if e.get("path"):
            e["path"] = e["path"].removesuffix("/SKILL.md").rstrip("/")
    return out


def lock_entries():
    if not LOCK.exists():
        return {}
    skills = json.loads(LOCK.read_text()).get("skills", {})
    return {n: {"source": "github:" + s["source"] if s.get("sourceType") == "github" else s.get("sourceUrl"),
                "path": str(Path(s["skillPath"]).parent), "tree": s.get("skillFolderHash"),
                "install": f"npx skills add {s['source']}"} for n, s in skills.items()}


def clone(source):
    d = CACHE / source.replace(":", "_").replace("/", "_")
    if d.is_dir():
        git("fetch", "-q", "origin", cwd=d)
    else:
        d.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "-q", "--filter=blob:none", "--no-checkout", url(source), str(d))
    return d


def pin(repo, path, want_hash, tree, tmp):
    """AC-6: newest first, at most WALK commits touching path, the first whose folder hashes like the
    installed one. A lock file entry also matches on its recorded upstream tree hash, which finds the base
    of a skill you edited after installing it."""
    log = git("log", "--format=%H", f"-n{WALK}", "HEAD", "--", path, cwd=repo).stdout.decode().split()
    for c in log:
        if git("cat-file", "-e", f"{c}:{path}", cwd=repo, check=False).returncode:
            continue  # the commit that deleted or moved the folder away
        if tree and git("rev-parse", f"{c}:{path}", cwd=repo, check=False).stdout.decode().strip() == tree:
            return c, folder_hash(export(repo, c, path, tmp))
        if folder_hash(export(repo, c, path, tmp)) == want_hash:
            return c, want_hash
    return None, None


def license_of(t):
    if "Permission is hereby granted, free of charge" in t:
        return "MIT"
    if "Apache License" in t and "Version 2.0" in t:
        return "Apache-2.0"
    return "unknown"


def license_at(repo, commit):
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
        r = git("show", f"{commit}:{name}", cwd=repo, check=False)
        if r.returncode == 0:
            return license_of(r.stdout.decode(errors="replace"))
    return "unknown"


PLUGINS = LIVE / "plugins"


def installed_plugins():
    try:
        return json.loads((PLUGINS / "installed_plugins.json").read_text()).get("plugins", {})
    except (OSError, ValueError):
        return {}


def plugin_entries():
    """AC-5: one `kind: plugin` entry per installed plugin, from Claude Code's own plugin files. Plugins are
    reinstalled by `claude plugin install`, never copied, so `publish` is false and `fetch` manual."""
    try:
        markets = json.loads((PLUGINS / "known_marketplaces.json").read_text())
    except (OSError, ValueError):
        markets = {}
    out = {}
    for key, installs in sorted(installed_plugins().items()):
        if not installs:
            continue
        i = installs[0]
        plugin, _, market = key.partition("@")
        repo = (markets.get(market) or {}).get("source", {}).get("repo")
        folder = Path(i.get("installPath", ""))
        try:
            desc = json.loads((folder / ".claude-plugin" / "plugin.json").read_text()).get("description")
        except (OSError, ValueError):
            desc = None
        lic = next((license_of(f.read_text(errors="replace")) for f in (folder / n for n in
                    ("LICENSE", "LICENSE.md", "LICENSE.txt")) if f.is_file()), "unknown")
        out[key] = {"kind": "plugin", "status": "downloaded", "source": f"github:{repo}" if repo else market,
                    "path": plugin, "pinned": i.get("gitCommitSha") or i.get("version"),
                    "base_hash": folder_hash(folder) if folder.is_dir() else None, "license": lic,
                    "publish": False, "patch": None, "description": first_sentence(desc) if desc else None,
                    "fetch": "manual", "install": f"claude plugin install {key}", "framework": None}
    return out


def description(folder):
    p = Path(folder)
    p = p / "SKILL.md" if p.is_dir() else p
    if not p.is_file():
        return None
    text = p.read_text(errors="replace")
    if not text.startswith("---"):
        return None
    lines = text.split("---", 2)[1].splitlines()
    for i, line in enumerate(lines):
        if line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            # A folded (`>`) or literal (`|`) block, or a value wrapped onto indented lines, goes on below.
            rest = []
            for more in lines[i + 1:]:
                if more and not more[0].isspace():
                    break
                rest.append(more.strip())
            value = " ".join([value.lstrip(">|-").strip()] + rest) if value[:1] in ">|" or rest else value
            return first_sentence(value.strip().strip("'\""))
    return None


def to_private(name, folder):
    dst = LIVE / "private" / "skills" / name
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(folder, dst, symlinks=True, ignore=shutil.ignore_patterns(*SKIP))


MIT_TEXT = """Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction, including without
limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
NOTICE_START, NOTICE_END = "<!-- manifest:start -->", "<!-- manifest:end -->"


def legal_texts(repo, commit, source, license):
    """(license text, NOTICE text or None) at commit. A source with an MIT README sentence and no LICENSE
    file (three.js) gets the MIT text with its owner as the copyright holder."""
    def show(name):
        r = git("show", f"{commit}:{name}", cwd=repo, check=False)
        return r.stdout.decode(errors="replace").strip() if r.returncode == 0 else None
    text = show("LICENSE") or show("LICENSE.md") or show("LICENSE.txt")
    if not text and license == "MIT":
        text = f"MIT License\n\nCopyright (c) {source.removeprefix('github:').split('/')[0]}\n\n{MIT_TEXT}"
    return text, (show("NOTICE") or show("NOTICE.md")) if license == "Apache-2.0" else None


def write_notice(m, texts):
    """AC-6: one block per source with a public patch, and every cite only or unlicensed entry named."""
    lines = [NOTICE_START, "", "## Downloaded skills with a public patch", "",
             "Written by `tools/bin/claude-config.py build` from `tools/config/manifest.json`; edit the manifest, not this part.", ""]
    by_source = {}
    for n, e in sorted(m["entries"].items()):
        if e.get("patch", "") and e["patch"].startswith("tools/config/"):
            by_source.setdefault(e["source"], []).append(n)
    for src, names in sorted(by_source.items()):
        license_text, notice = texts.get(src, (None, None))
        copyright = next((x.strip() for x in (license_text or "").splitlines() if x.strip().lower().startswith("copyright")),
                         "copyright line not found")
        lines += [f"### {src.removeprefix('github:')}", "", f"Patched here: {', '.join(names)}.", copyright,
                  f"SPDX-License-Identifier: {m['entries'][names[0]]['license']}", "", "```",
                  license_text or "license text not reached at build", "```", ""]
        if notice:
            lines += ["Its NOTICE:", "", "```", notice, "```", ""]
    lines += ["## Not redistributed", "", "Named in the manifest only; no file or patch of these is in this repo.", ""]
    lines += [f"- {n}: {(e.get('source') or 'source unknown').removeprefix('github:')} ({e.get('license')})"
              for n, e in sorted(m["entries"].items())
              if e["kind"] != "plugin" and (not e.get("publish") or e.get("license") in ("unknown", "none"))]
    lines += ["", NOTICE_END]
    path = REPO / "docs" / "NOTICE.md"
    old = path.read_text() if path.exists() else "# Notice\n"
    if NOTICE_START in old:
        old = old.split(NOTICE_START)[0].rstrip("\n") + "\n" + old.split(NOTICE_END, 1)[1].lstrip("\n")
    path.write_text(old.rstrip("\n") + "\n\n" + "\n".join(lines) + "\n")


def build():
    """Write tools/config/manifest.json entries for every real downloaded skill folder in ~/.claude/skills."""
    m = load_manifest()
    fw = framework_dirs(m)
    fw_by_source = {f.get("source"): k for k, f in m.get("frameworks", {}).items()}
    own = {p.name for p in (HOME_DIR / "skills").iterdir()} if (HOME_DIR / "skills").is_dir() else set()
    traced, locked = parse_brief(BRIEF.read_text()) if BRIEF.exists() else {}, lock_entries()
    report, bad = [], 0
    texts, gone = {}, set()
    with tempfile.TemporaryDirectory() as tmp:
        for p in live_items("skills"):
            name = p.name
            if name in own or inside(p.resolve(), fw):
                continue
            if not (p / "SKILL.md").exists():
                continue
            if private_name_hit(b"".join(f.read_bytes() for f in sorted(p.rglob("*"))
                                         if f.is_file() and not SKIP & set(f.relative_to(p).parts))):
                to_private(name, p)  # AC-8: no manifest entry, the drift check reads the private store
                report.append(f"{name}: private name, copied to the private store only")
                continue
            src = {**traced.get(name, {}), **({k: v for k, v in locked[name].items()} if name in locked else {})}
            if not src.get("source"):
                if (LIVE / "private" / "skills" / name).exists() and name not in traced:
                    continue  # yours or private, kept in the private store
                to_private(name, p)
                m["entries"][name] = {"kind": "skill", "status": "source-unknown", "source": None, "path": None,
                                      "pinned": None, "base_hash": folder_hash(p), "license": "unknown",
                                      "publish": False, "patch": None, "description": description(p),
                                      "fetch": "manual", "install": None, "framework": None}
                report.append(f"{name}: source unknown, copied to the private store")
                continue
            fetch_kind = src.get("fetch") or ("git" if src["source"].startswith(("github:", "file://", "/"))
                                               else "manual")
            path = name if src.get("path") == "<name>" else src.get("path", ".").replace("<name>", name)
            e = {"kind": "skill", "source": src["source"], "path": path, "license": src.get("license", "unknown"),
                 "publish": bool(src.get("publish", False)), "patch": None, "description": description(p),
                 "fetch": fetch_kind, "framework": fw_by_source.get(src["source"]),
                 "install": src.get("install") or f"npx skills add {src['source'].removeprefix('github:')}/{path}"}
            if fetch_kind == "manual":
                e.update(status="downloaded", pinned=src.get("pinned"), base_hash=folder_hash(p))
            else:
                try:
                    repo = clone(src["source"])
                    commit, base = pin(repo, path, folder_hash(p), src.get("tree"), tmp)
                except Gone as err:
                    report.append(f"{name}: source not reached, entry left as it was: {err}")
                    gone.add(name)
                    bad = 1
                    continue
                if name in locked:
                    e["license"] = license_at(repo, commit or "HEAD")
                    e["publish"] = e["license"] in ("MIT", "Apache-2.0")
                e.update(status="downloaded" if commit else "unpinned", pinned=commit, base_hash=base)
                if commit and base != folder_hash(p):
                    e["status"] = "edited"
                    store_patch(name, e, make_patch(export(repo, commit, path, tmp), p, tmp))
                    if e["patch"].startswith("tools/config/"):
                        texts[src["source"]] = legal_texts(repo, commit, src["source"], e["license"])
            if not e["publish"] and e["status"] in ("edited", "unpinned"):
                to_private(name, p)  # cite only: no public files, so the private store keeps your copy
            m["entries"][name] = e
            report.append(f"{name}: {e['status']}")
    # A hand written entry for a folder with no SKILL.md (a mod) is skipped by the loop above, so its source got
    # no license text and the notice said "not reached at build".
    for name, e in sorted(m["entries"].items()):
        # A source the main loop already reported unreachable is not cloned and reported a second time.
        if e.get("fetch") == "git" and (e.get("patch") or "").startswith("tools/config/") and e.get("pinned") \
                and e["source"] not in texts and name not in gone:
            try:
                texts[e["source"]] = legal_texts(clone(e["source"]), e["pinned"], e["source"], e["license"])
            except Gone as err:
                report.append(f"{name}: license text not reached: {err}")
                bad = 1
    for key, e in plugin_entries().items():
        m["entries"][key] = e
        report.append(f"{key}: plugin {e['pinned']}")
    save_manifest(m)
    write_notice(m, texts)
    print("\n".join(report))
    out = []
    linked_kind("skills", m, fw, out)
    left = [f"  {n}: {why}" for k, n, why in out if "live only" in why]
    print(f"accounting: {len(left)} skill(s) not accounted for" + ("".join("\n" + x for x in left)))
    return 1 if bad or left else 0


# ---------------------------------------------------------------- docs (AC-13)

SKILLS_DOC = REPO / "docs" / "guides" / "SKILLS.md"
ROUTING = REPO / "tools" / "config" / "routing.md"


def ascii_text(text):
    """The house ASCII rule on text copied from upstream front matter (tools/scripts/asciify.py's table)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("asciify", REPO / "tools" / "scripts" / "asciify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.convert(text)[0]


def cell(text):
    return (text or "no description").replace("|", "/").replace("\n", " ")


def docs_text():
    """docs/guides/SKILLS.md from the manifest, claude-home/skills/ and claude-home/commands/ front
    matter and tools/config/routing.md only: no read of ~/.claude, so the committed file is reproducible."""
    m = load_manifest()
    out = ["# Skills", "Type: reference", "",
           "Every skill and command in this setup: your own, the frameworks, and every downloaded one with its",
           "source and license. Generated by `python3 tools/bin/claude-config.py docs` from `tools/config/manifest.json`,",
           "the front matter in `claude-home/` and `tools/config/routing.md`; edit those, never this file.", ""]
    out += ["## Your own skills", "", "Linked from `claude-home/skills/`; editing the repo copy is live.", "",
            "| Skill | What it does |", "|---|---|"]
    for d in sorted(p for p in (HOME_DIR / "skills").iterdir() if (p / "SKILL.md").is_file()):
        out.append(f"| `{d.name}` | {cell(description(d))} |")
    out += ["", "## Your own commands", "", "Linked from `claude-home/commands/`.", "",
            "| Command | What it does |", "|---|---|"]
    for f in sorted((HOME_DIR / "commands").glob("*.md")):
        out.append(f"| `/{f.stem}` | {cell(description(f))} |")
    out += ["", "## Frameworks", "", "Installed by their own installer, never copied here. The skills each one owns are",
            "not listed below.", "", "| Framework | Source | Version | License | Install |", "|---|---|---|---|---|"]
    for name, f in sorted(m.get("frameworks", {}).items()):
        out.append(f"| {name} | {cell(f.get('source'))} | {cell(f.get('pinned') or 'not pinned')} | "
                   f"{cell(f.get('license'))} | `{cell(f.get('install'))}` |")
    plugins = sorted((n, e) for n, e in m.get("entries", {}).items() if e.get("kind") == "plugin")
    out += ["", "## Plugins", "", "Installed by Claude Code's plugin system, never copied here.", "",
            "| Plugin | Source | Version | License | What it does |", "|---|---|---|---|---|"]
    for name, e in plugins:
        out.append(f"| `{name}` | {cell(e.get('source').removeprefix('github:'))} | {cell(e.get('pinned'))} | "
                   f"{cell(e.get('license'))} | {cell(e.get('description'))} |")
    by_source = {}
    for name, e in sorted(m.get("entries", {}).items()):
        if e.get("kind") == "plugin":
            continue
        by_source.setdefault(e.get("source") or "source unknown", []).append((name, e))
    out += ["", "## Downloaded skills", "",
            "Status: `downloaded` is upstream as is, `edited` is upstream plus your patch, `unpinned` matches no",
            "upstream commit, `source-unknown` has no known source (kept in the private store). `cite only` means",
            "the license forbids publishing, so no file or patch of it is in this repo.", ""]
    for src, items in sorted(by_source.items(), key=lambda kv: kv[0].lower()):
        lic = sorted({e.get("license") or "unknown" for _, e in items})
        out += [f"### {src.removeprefix('github:')}", "", f"License: {', '.join(lic)}.", "",
                "| Skill | Status | What it does |", "|---|---|---|"]
        for name, e in items:
            status = e.get("status") + ("" if e.get("publish") else ", cite only")
            out.append(f"| `{name}` | {status} | {cell(e.get('description'))} |")
        out.append("")
    out += ["## Routing", "",
            "Copied from `tools/config/routing.md`, the reference of which skill fits which task. Typing a skill's name",
            "always wins; routing is for a task described in plain words. Check edits with",
            "`python3 tools/scripts/check-routing.py`.", ""]
    routing = ROUTING.read_text().splitlines() if ROUTING.exists() else []
    out += routing[1:] if routing[:1] and routing[0].startswith("# ") else routing
    return ascii_text("\n".join(out).rstrip("\n") + "\n")


def docs():
    SKILLS_DOC.parent.mkdir(parents=True, exist_ok=True)
    SKILLS_DOC.write_text(docs_text())
    print(f"wrote {SKILLS_DOC.relative_to(REPO)}")
    return 0


# ---------------------------------------------------------------- profiles (spec 0081)

PROFILES = REPO / "profiles"
PROFILE_STATE = LIVE / "state" / "profile.json"
# the copied files every install needs; the rest of COPIED_FILES may be absent from a scratch copy (the self checks)
REQUIRED_FILES = ("CLAUDE.md", "settings.json", "hooks/block-destructive.sh", "hooks/review-stack-pre-push",
                  "hooks/plain-panel.py", "hooks/context-monitor.js", "hooks/handover-start.sh", "hooks/no-jjstack-bar.py",
                  "hooks/skill-rules.py", "hooks/chain-catch.py", "hooks/live-tick.py")
PROFILE_FIELDS = {"name": str, "description": str, "owner": bool, "base": str, "skills": dict, "rules": list,
                  "hooks_off": list, "editable": list}


def profile_names():
    return sorted(p.parent.name for p in PROFILES.glob("*/profile.json")) if PROFILES.is_dir() else ["engineer"]


def load_profile(name):
    if not PROFILES.is_dir() and name == "engineer":
        # a repo with no profiles/ (a scratch copy in the self checks) installs as before profiles: every core rule,
        # the settings as they are
        skills = json.loads((HOME_DIR / "settings.json").read_text()).get("skillOverrides", {})
        return {"name": "engineer", "description": "every core rule", "owner": True, "base": "", "skills": skills,
                "rules": sorted(p.name for p in (HOME_DIR / "rules").glob("*.md")), "hooks_off": [], "editable": ["**"]}
    return json.loads((PROFILES / name / "profile.json").read_text())


def profile_problems(name):
    """AC-1: every reason the profile file is not valid; [] when it is."""
    try:
        p = load_profile(name)
    except (OSError, ValueError) as e:
        return [f"{name}: profile.json does not load: {e}"]
    out = [f"{name}: {k} missing or not {t.__name__}" for k, t in PROFILE_FIELDS.items() if not isinstance(p.get(k), t)]
    if out:
        return out
    if p["name"] != name:
        out.append(f"{name}: name is {p['name']!r}, not the folder name")
    out += [f"{name}: rule {r} is not in claude-home/rules/" for r in p["rules"] if not (HOME_DIR / "rules" / r).is_file()]
    out += [f"{name}: skill {s} is {v!r}, not on or name-only" for s, v in p["skills"].items() if v not in ("on", "name-only")]
    if p["base"] and not (PROFILES / p["base"] / "profile.json").is_file():
        out.append(f"{name}: base {p['base']} is not a profile")
    for h in p["hooks_off"]:
        if h == "profile-lock.py" or not (HOME_DIR / "hooks" / str(h)).is_file():
            out.append(f"{name}: hooks_off {h} is not a core hook script that may be turned off")
    return out


def read_state():
    try:
        return json.loads(PROFILE_STATE.read_text())
    except (OSError, ValueError):
        return None


def active_profile():
    """AC-4: the name in state/profile.json, else engineer."""
    s = read_state()
    return s["name"] if isinstance(s, dict) and isinstance(s.get("name"), str) else "engineer"


def current_profile():
    """The active profile's file, or None in a repo with no profiles/ folder."""
    name = active_profile()
    return load_profile(name) if PROFILES.is_dir() and (PROFILES / name / "profile.json").is_file() else None


def hook_script(cmd):
    """The file name of the script a hook command runs, interpreter skipped; '' when there is none."""
    try:
        words = shlex.split(cmd) if isinstance(cmd, str) else []
    except ValueError:
        return ""
    if len(words) > 1 and os.path.basename(words[0]) in INTERPRETERS:
        words = words[1:]
    return os.path.basename(words[0]) if words else ""


def profile_settings(d, p):
    """AC-2: skillOverrides from the profile, then every hook command in hooks_off removed (empty groups dropped)."""
    if p["skills"] or "skillOverrides" in d:
        d["skillOverrides"] = dict(p["skills"])
    off = set(p["hooks_off"])
    hooks = d.get("hooks") or {}
    for event in list(hooks):
        groups = []
        for g in hooks[event]:
            g["hooks"] = [c for c in g.get("hooks", []) if hook_script(c.get("command")) not in off]
            if g["hooks"]:
                groups.append(g)
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]
    return d


def profile_rules(p):
    """Live rules/ path -> repo source: the core files the profile lists, every core subfolder (rules/ecc/) whole,
    then the profile's own rules/*.md."""
    core = HOME_DIR / "rules"
    out = {f"rules/{r}": core / r for r in p["rules"]}
    for f in core.rglob("*"):
        if f.is_file() and f.parent != core:
            out[f"rules/{f.relative_to(core).as_posix()}"] = f
    for f in sorted((PROFILES / p["name"] / "rules").glob("*.md")):
        out[f"rules/{f.name}"] = f
    return out


def stage(name, out):
    """AC-2: the profile built into `out`, everything install writes but the private and autoMode steps on settings.json."""
    out = Path(out)
    problems = profile_problems(name)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2
    # a missing one used to stop install half way through the copy; here it stops before anything is written
    missing = [rel for rel in REQUIRED_FILES if not (HOME_DIR / rel).exists()]
    if missing:
        print("\n".join(f"claude-home/{rel} is missing" for rel in missing), file=sys.stderr)
        return 2
    p = load_profile(name)
    shutil.copy2(HOME_DIR / "CLAUDE.md", out / "CLAUDE.md")
    for d in ("agents", "rules-on-demand"):
        if (HOME_DIR / d).is_dir():
            shutil.copytree(HOME_DIR / d, out / d, symlinks=True)
    for rel, src in profile_rules(p).items():
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out / rel)
    for rel in COPIED_FILES:
        if (HOME_DIR / rel).exists():
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(HOME_DIR / rel, out / rel)
    d = json.loads((HOME_DIR / "settings.json").read_text().replace(AUTHOR_HOME, str(Path.home())))
    (out / "settings.json").write_text(json.dumps(profile_settings(d, p), indent=2) + "\n")
    return 0


def changed_lines(live_text, repo_text):
    """Lines the live copy adds and removes against the build: what an overwrite would lose."""
    add = rem = 0
    for line in difflib.ndiff(repo_text.splitlines(), live_text.splitlines()):
        add += line.startswith("+ ")
        rem += line.startswith("- ")
    return add, rem


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def settings_sha(d, ignore):
    d = json.loads(json.dumps(d))
    for key in ignore:
        drop(d, key)
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()


def overwrite(out):
    """AC-5: every live file the staged build would change, and every live rule it would not write. Exit 3 when any.
    A live file still as the last install wrote it (its hash in state/profile.json `installed`) is not a live change:
    without that, every profile switch listed the old profile's own rules and settings."""
    out = Path(out)
    ignore = json.loads(IGNORE.read_text()) if IGNORE.exists() else []
    installed = (read_state() or {}).get("installed") or {}
    items = []
    for f in sorted(p for p in out.rglob("*") if p.is_file()):
        rel = f.relative_to(out).as_posix()
        live = LIVE / rel
        if not live.is_file():
            continue
        if rel == "settings.json":
            try:
                a, b = json.loads(live.read_text()), json.loads(f.read_text())
            except ValueError:
                # spec 0019 AC-9: an unreadable live file holds nothing sync could carry; install warns and goes on
                print(f"overwrite: live {rel} does not parse; it is replaced")
                continue
            if installed.get(rel) == settings_sha(a, ignore):
                continue
            for key in ignore:
                drop(a, key)
                drop(b, key)
            if a != b:
                add, rem = changed_lines(json.dumps(a, indent=2, sort_keys=True), json.dumps(b, indent=2, sort_keys=True))
                items.append(f"overwrite: changed {rel} +{add}/-{rem}")
        elif live.read_bytes() != f.read_bytes() and installed.get(rel) != sha(live):
            add, rem = changed_lines(live.read_text(errors="replace"), f.read_text(errors="replace"))
            items.append(f"overwrite: changed {rel} +{add}/-{rem}")
    for d in ("rules", "rules-on-demand"):
        for rel in sorted(tree_files(LIVE / d)):
            if not (out / d / rel).exists() and installed.get(f"{d}/{rel}") != sha(LIVE / d / rel):
                items.append(f"overwrite: lost {d}/{rel}")
    print("\n".join(items) if items else "overwrite: nothing to lose")
    return 3 if items else 0


def write_state(name, out=None):
    """AC-2: the active profile file plus the repo's path, written atomically, and the hash of every file the install
    just wrote (`out`, the staging folder) so the next overwrite check can tell a live edit from its own files."""
    s = dict(load_profile(name), repo=str(REPO.resolve()))
    if out:
        ignore = json.loads(IGNORE.read_text()) if IGNORE.exists() else []
        files = [p.relative_to(out).as_posix() for p in Path(out).rglob("*") if p.is_file()]
        s["installed"] = {rel: settings_sha(json.loads((LIVE / rel).read_text()), ignore) if rel == "settings.json"
                          else sha(LIVE / rel) for rel in sorted(files) if (LIVE / rel).is_file()}
    PROFILE_STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROFILE_STATE.with_name(PROFILE_STATE.name + ".tmp")
    tmp.write_text(json.dumps(s, indent=2) + "\n")
    os.replace(tmp, PROFILE_STATE)
    return 0


def resolve(name):
    """AC-4, AC-2: the profile install uses, and where the name came from; exit 2 naming the known ones."""
    src = "--profile"
    if not name:
        name, src = active_profile(), ("state/profile.json" if read_state() else "default")
    if name not in profile_names():
        print(f"unknown profile: {name}; known: {', '.join(profile_names())}", file=sys.stderr)
        return 2
    print(f"{name} {src}")
    return 0


def install(*args):
    return subprocess.run(["bash", str(REPO / "tools" / "bin" / "install.sh"), *args]).returncode


def profile_cmd(rest):
    """AC-7, AC-8: list, switch, update. A trailing --accept-overwrite goes to install (AC-5, after the user's answers)."""
    accept = ["--accept-overwrite"] if rest[-1:] == ["--accept-overwrite"] else []
    rest = rest[:len(rest) - len(accept)]
    if not rest:
        cur = active_profile()
        for n in profile_names():
            print(f"{'*' if n == cur else ' '} {n}: {load_profile(n).get('description', '')}")
        return 0
    if rest == ["update"]:
        dirty = git("status", "--porcelain", cwd=REPO).stdout.decode().strip()
        if dirty:
            print(f"profile update: the repo has uncommitted changes, nothing installed:\n{dirty}")
            return 1
        r = git("pull", "--ff-only", cwd=REPO, check=False)
        if r.returncode:
            print(f"profile update: git pull failed, nothing installed:\n{(r.stdout + r.stderr).decode().strip()}")
            return 1
        return install("--profile", active_profile(), *accept)
    if len(rest) == 2 and rest[0] == "custom":
        return custom_profile(rest[1], accept)
    if len(rest) == 1:
        if rest[0] not in profile_names():
            print(f"unknown profile: {rest[0]}; known: {', '.join(profile_names())}", file=sys.stderr)
            return 2
        rc = install("--profile", rest[0], *accept)
        if rc == 0:
            print(f"profile {rest[0]} active: open a new chat")
        return rc
    print(f"claude-config: unknown command: profile {' '.join(rest)}", file=sys.stderr)
    return 2


def custom_profile(short, accept):
    """AC-12: the person's own copy of the active profile, profiles/custom-<short>/, then switched to it. It is an owner
    profile limited to its base's edit list plus its own rules; its profile.json changes only through this tool."""
    if not re.fullmatch(r"[a-z0-9-]{1,30}", short):
        print(f"profile custom: {short!r} is not 1 to 30 of a-z, 0-9 and -; pick another name", file=sys.stderr)
        return 2
    name = f"custom-{short}"
    dst = PROFILES / name
    if dst.exists():
        print(f"profile custom: {name} exists; pick another name", file=sys.stderr)
        return 2
    base = active_profile()
    shutil.copytree(PROFILES / base, dst)
    p = load_profile(base)
    p.update(name=name, base=base, owner=True, editable=p["editable"] + [f"profiles/{name}/rules/**"],
             description=f"{short}'s own copy of {base}")
    (dst / "profile.json").write_text(json.dumps(p, indent=2) + "\n")
    print(f"made {dst.relative_to(REPO)} from {base}")
    rc = install("--profile", name, *accept)
    if rc == 0:
        print(f"profile {name} active: open a new chat")
    return rc


def sync_profile(stripped):
    """AC-6, owner profiles: live skillOverrides go into the active profile's skills, not the core settings.json;
    each live rule goes back to where the profile takes it from. A new live rule goes to the core and the profile's
    list, as it reached the core before profiles. A repo with no profiles copies every live rule to the core."""
    p = current_profile()
    if p is not None:
        s = json.loads(Path(stripped).read_text())
        if "skillOverrides" in s:
            p["skills"] = s.pop("skillOverrides")
            Path(stripped).write_text(json.dumps(s, indent=2) + "\n")
    own = PROFILES / p["name"] / "rules" if p else None
    for rel in sorted(tree_files(LIVE / "rules")):
        src = LIVE / "rules" / rel
        if own and "/" not in rel and (own / rel).exists():
            dst = own / rel
        else:
            dst = HOME_DIR / "rules" / rel
            if p and "/" not in rel and rel not in p["rules"]:
                p["rules"].append(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    if p is None:
        return 0
    (PROFILES / p["name"] / "profile.json").write_text(json.dumps(p, indent=2) + "\n")
    # tools/bin/sync.sh names the orphans of agents/ and rules-on-demand/; a core rule this profile does not list is not one
    for rel, src in profile_rules(p).items():
        if not (LIVE / rel).exists():
            print(f"  ORPHAN: {src.relative_to(REPO)} is built into {rel} but gone from {LIVE} - delete it by hand")
    return 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "sync" and not rest:
        return subprocess.run(["bash", str(REPO / "tools" / "bin" / "sync.sh")]).returncode
    if cmd == "install":
        return install(*rest)
    if cmd == "profile":
        return profile_cmd(rest)
    if cmd == "profile-resolve" and len(rest) <= 1:
        return resolve(rest[0] if rest else "")
    if cmd == "stage" and len(rest) == 2:
        return stage(*rest)
    if cmd == "overwrite" and len(rest) == 1:
        return overwrite(rest[0])
    if cmd == "write-state" and len(rest) in (1, 2):
        return write_state(*rest)
    if cmd == "profile-owner" and not rest:
        p = current_profile()
        if p is None or p.get("owner") is True:
            return 0
        print(f"sync: {p['name']} is not an owner profile; changes reach the repo through a PR")
        return 3
    if cmd == "sync-profile" and len(rest) == 1:
        return sync_profile(rest[0])
    if cmd == "drift" and not rest:
        return drift()
    if cmd == "hook-files" and not rest:
        return hook_files()
    if cmd == "update" and rest == ["--plan"]:
        return update_plan()
    if cmd == "update" and len(rest) in (2, 3) and rest[0] == "--apply" and rest[2:] in ([], ["--resolved"]):
        return update_apply(rest[1], resolved=bool(rest[2:]))
    if cmd == "restore" and not rest:
        return restore()
    if cmd == "patches" and not rest:
        return patches()
    if cmd == "build" and not rest:
        return build()
    if cmd == "docs" and not rest:
        return docs()
    if cmd == "hash" and len(rest) == 1:
        print(folder_hash(rest[0]))
        return 0
    print(f"claude-config: unknown command: {' '.join(argv)}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
