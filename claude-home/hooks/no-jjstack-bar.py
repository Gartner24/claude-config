#!/usr/bin/env python3
"""SessionStart: drop a jjstack status line from ~/.claude/settings.json.
jjstack's setup and upgrade reinstall their bar whenever the statusLine slot is empty, and a no-op
placeholder (`true`) still left an empty row on screen, so the slot stays empty and this puts it back."""
import json
import os
import sys
import tempfile


def clean(path):
    with open(path) as f:
        s = json.load(f)
    if "jjstack" not in str(s.get("statusLine", {}).get("command", "")):
        return False
    del s["statusLine"]
    tmp = f"{path}.tmp-{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)
    return True


def selftest():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "settings.json")
    with open(p, "w") as f:
        json.dump({"a": 1, "statusLine": {"type": "command", "command": "bash ~/.claude/skills/jjstack/bin/statusline.sh"}}, f)
    assert clean(p) is True
    assert json.load(open(p)) == {"a": 1}
    with open(p, "w") as f:
        json.dump({"statusLine": {"type": "command", "command": "mine.sh"}}, f)
    assert clean(p) is False
    assert json.load(open(p))["statusLine"]["command"] == "mine.sh"
    with open(p, "w") as f:
        json.dump({"a": 1}, f)
    assert clean(p) is False
    print("all self-checks passed")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        selftest()
    else:
        try:
            if clean(os.path.expanduser("~/.claude/settings.json")):
                print("removed jjstack status line from settings.json")
        except Exception:
            pass  # a SessionStart hook never fails the session
