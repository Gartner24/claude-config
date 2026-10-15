#!/usr/bin/env python3
"""skill-keep: only the skills in skill-keep.txt keep their description in every session (spec 0050).

Sets every other installed own skill and command to `name-only` in `$CLAUDE_LIVE_DIR/settings.json`
(default ~/.claude), and reports every installed plugin. `--dry-run` prints the changes, writes nothing.
Run `bin/sync.sh` right after a real run: `bin/install.sh` rebuilds the live file from the repo copy.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

KEEP = Path(__file__).resolve().parent / "skill-keep.txt"
HELD = ("off", "user-invocable-only")


def read_keep(path=KEEP):
    names = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.append(line)
    return names


def installed(live):
    names = set()
    skills = live / "skills"
    if skills.is_dir():
        names |= {d.name for d in skills.iterdir() if (d / "SKILL.md").is_file()}
    commands = live / "commands"
    if commands.is_dir():
        names |= {f.stem for f in commands.glob("*.md") if f.is_file()}
    return names


def plan(overrides, names, keep):
    """Return the new overrides dict and the change lines; existing key order is kept."""
    new = dict(overrides)
    changes = []
    for name in sorted(names):
        cur = new.get(name)
        if name in keep:
            if cur == "name-only":
                del new[name]
                changes.append(f"described: {name}")
            elif cur in HELD:
                changes.append(f"kept as {cur}: {name}")
        elif cur is None:
            new[name] = "name-only"
            changes.append(f"name-only: {name}")
    return new, changes


def count(folder):
    k = len(list(folder.glob("skills/*/SKILL.md")))
    c = len(list(folder.glob("commands/*.md")))
    return k, c


def plugins(live, settings):
    """(name, enabled, folder) for every installed plugin, both sources."""
    out = []
    reg = live / "plugins" / "installed_plugins.json"
    if reg.is_file():
        enabled = settings.get("enabledPlugins") or {}
        for key, entries in (json.loads(reg.read_text()).get("plugins") or {}).items():
            path = entries[0].get("installPath") if entries else None
            out.append((key, enabled.get(key) is True, Path(path) if path else None))
    skills = live / "skills"
    if skills.is_dir():
        for meta in sorted(skills.glob("*/.claude-plugin/plugin.json")):
            out.append((json.loads(meta.read_text())["name"], True, meta.parent.parent))
    return out


def report(live, settings, names, keep):
    overrides = settings.get("skillOverrides") or {}
    own = sum(1 for n in names if n not in overrides)
    lines = [f"described: {own} own skills"]
    total = own
    for name, on, folder in plugins(live, settings):
        if folder is None or not folder.is_dir():
            lines.append(f"plugin {name}: folder missing")
        elif not on:
            lines.append(f"plugin {name}: off")
        else:
            k, c = count(folder)
            total += k
            lines.append(f"plugin {name}: {k} skills, {c} commands (not controlled)")
    lines.append(f"total described: {total}")
    lines += [f"warning: kept skill not installed: {n}" for n in keep if n not in names]
    return lines


def write(path, data):
    # Same backup folder as bin/install.sh (spec 0035 AC-7).
    bak = path.parent / "backups" / "settings"
    bak.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, bak / f"settings.json.bak.{time.strftime('%Y%m%d-%H%M%S')}")
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".settings.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        with open(tmp) as f:
            json.load(f)
        os.chmod(tmp, path.stat().st_mode & 0o7777)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    live = Path(os.environ.get("CLAUDE_LIVE_DIR") or Path.home() / ".claude")
    path = live / "settings.json"
    try:
        settings = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        print(f"skill-keep: cannot read {path}: {e}", file=sys.stderr)
        return 1
    keep = read_keep(KEEP)
    names = installed(live)
    new, changes = plan(settings.get("skillOverrides") or {}, names, set(keep))
    for line in changes:
        print(line)
    if not args.dry_run and new != (settings.get("skillOverrides") or {}):
        write(path, {**settings, "skillOverrides": new})
    for line in report(live, {**settings, "skillOverrides": new}, names, keep):
        print(line)
    if not args.dry_run:
        print("next: run bin/sync.sh now, before any bin/install.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
