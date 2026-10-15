#!/usr/bin/env python3
"""SessionStart hook (spec 0048 AC-11): one line when upstream skills were not checked for 7 days.

It only reads ~/.claude/state/claude-config.json, which `claude-config.py update --plan` writes; it never
fetches and never runs the drift check, so a session start stays instant and offline.
"""
import datetime
import json
import os
import sys
from pathlib import Path

DAYS = 7


def line(state, now):
    try:
        last = datetime.datetime.fromisoformat(json.loads(state.read_text())["last_upstream_check"])
    except (OSError, ValueError, KeyError, TypeError):
        return "claude-config: upstream never checked, run /claude-config update"
    days = (now - last).days
    if days >= DAYS:
        return f"claude-config: upstream not checked for {days} days, run /claude-config update"
    return None


def main():
    live = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    msg = line(live / "state" / "claude-config.json", datetime.datetime.now(datetime.timezone.utc))
    if msg:
        print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
