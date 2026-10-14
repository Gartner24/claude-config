# Spec 0028 probe P1: the shape of real AskUserQuestion panels, read from local session transcripts.
# Read only, calls nothing. Prints counts only, never panel text (transcripts hold private names).
import collections
import glob
import json
import os

files = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
panels, keys, optkeys, per, learn = 0, collections.Counter(), collections.Counter(), collections.Counter(), 0
for f in files:
    try:
        lines = open(f, encoding="utf-8").read().splitlines()
    except (OSError, UnicodeDecodeError):
        continue
    for line in lines:
        if '"AskUserQuestion"' not in line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        for c in (d.get("message") or {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "AskUserQuestion":
                panels += 1
                keys.update(c["input"].keys())
                for q in c["input"].get("questions", []):
                    per[len(q.get("options", []))] += 1
                    for o in q.get("options", []):
                        optkeys.update(o.keys())
                        learn += o.get("label", "").lower().startswith(("learn", "explain"))
print("transcripts", len(files), "panels", panels)
print("input keys", dict(keys))
print("option keys", dict(optkeys))
print("options per question", dict(sorted(per.items())))
print("options starting learn or explain", learn)
