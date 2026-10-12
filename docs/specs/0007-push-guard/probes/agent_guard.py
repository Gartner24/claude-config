import json, sys
try:
    d = json.load(sys.stdin)
    i = d["tool_input"]
    ok = d["tool_name"] == "Agent" and isinstance(i, dict) and i.get("isolation") in (None, "worktree")
except Exception:
    ok = False
if not ok:
    print("wf run: remote agents are refused", file=sys.stderr)
    sys.exit(2)
