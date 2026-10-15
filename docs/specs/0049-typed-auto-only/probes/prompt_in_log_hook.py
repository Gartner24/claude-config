# Probe P1 hook side: records, at UserPromptSubmit time, whether the typed prompt is already in the transcript and
# what the transcript's last entry is.
import json
import os
import sys

data = json.load(sys.stdin)
out = {"prompt": data.get("prompt"), "transcript_path": data.get("transcript_path"), "keys": sorted(data)}
try:
    with open(data["transcript_path"], encoding="utf-8") as f:
        lines = [json.loads(x) for x in f if x.strip()]
    out["entries"] = len(lines)
    out["last"] = [{"type": e.get("type"), "content": str((e.get("message") or {}).get("content"))[:120]}
                   for e in lines[-3:]]
    out["prompt_in_log"] = any(e.get("type") == "user" and data.get("prompt") in json.dumps(e) for e in lines)
except (OSError, KeyError, ValueError) as e:
    out["error"] = repr(e)
with open(os.environ["PROBE_OUT"], "a", encoding="utf-8") as f:
    f.write(json.dumps(out) + "\n")
