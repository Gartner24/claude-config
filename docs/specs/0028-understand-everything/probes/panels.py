#!/usr/bin/env python3
"""Spec 0028 AC-16: every AskUserQuestion panel asked since the hook was installed passes the AC-3 check.
Reads ~/.claude/projects/*/*.jsonl, prints counts and file:line of failures, never panel text."""
import datetime
import glob
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
spec = importlib.util.spec_from_file_location("plain_panel", os.path.join(HERE, "..", "..", "..", "..", "live", "hooks",
                                                                          "plain-panel.py"))
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)
QUESTION = re.compile(r"^panel: question (\d+): ")


def main():
    home = os.path.expanduser("~/.claude")
    hook = os.path.join(home, "hooks", "plain-panel.py")
    if not os.path.exists(hook):
        print("hook not installed: run bin/install.sh first")
        return 1
    since = datetime.datetime.fromtimestamp(os.path.getmtime(hook), datetime.timezone.utc)
    n, fails = 0, []
    for path in sorted(glob.glob(os.path.join(home, "projects", "*", "*.jsonl"))):
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                try:
                    rec = json.loads(line)
                    at = datetime.datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
                    content = rec["message"]["content"]
                except (ValueError, KeyError, TypeError, AttributeError):
                    continue
                if at <= since or not isinstance(content, list):
                    continue
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "AskUserQuestion":
                        n += 1
                        for p in panel.problems({"tool_input": c.get("input")}):
                            fails.append(f"{path}:{i}: question {QUESTION.match(p).group(1)}")
    if n == 0:
        print("no panels since the hook was installed, ask one first")
        return 1
    print(f"panels: {n}, failing: {len(fails)}")
    for x in fails:
        print(x)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
