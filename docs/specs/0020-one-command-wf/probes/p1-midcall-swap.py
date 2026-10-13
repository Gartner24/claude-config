#!/usr/bin/env python3
# Spec 0020 P1: what does a claude -p call already running see when its config is swapped mid call?
# A temp CLAUDE_CONFIG_DIR (your login copied in, nothing of your live ~/.claude changed) holds a
# PreToolUse hook script that logs "v1". About 15 s into the call, the script is swapped by rename to
# log "v2", and settings.json is swapped to add a PostToolUse hook that logs "post". The log answers:
#   v1 then v2  -> hook scripts are read per tool use (a running call uses new hook scripts)
#   post seen   -> settings.json is reread mid call
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time

C = tempfile.mkdtemp(prefix="p1-swap-")
LOG = os.path.join(C, "hook.log")
HOOK = os.path.join(C, "hook.sh")
POST = os.path.join(C, "post.sh")
creds = os.path.expanduser("~/.claude/.credentials.json")
if os.path.exists(creds):
    shutil.copy2(creds, os.path.join(C, ".credentials.json"))


def put(path, text, mode=0o644):
    tmp = path + ".new"
    with open(tmp, "w") as f:
        f.write(text)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def settings(post):
    hooks = {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": f"bash {HOOK}"}]}]}
    if post:
        hooks["PostToolUse"] = [{"matcher": "Bash", "hooks": [{"type": "command", "command": f"bash {POST}"}]}]
    return json.dumps({"hooks": hooks}, indent=2)


put(HOOK, f"#!/bin/bash\necho \"v1 $(date +%s)\" >> {LOG}\n", 0o755)
put(POST, f"#!/bin/bash\necho \"post $(date +%s)\" >> {LOG}\n", 0o755)
put(os.path.join(C, "settings.json"), settings(False))


def swap():
    time.sleep(15)
    put(HOOK, f"#!/bin/bash\necho \"v2 $(date +%s)\" >> {LOG}\n", 0o755)
    put(os.path.join(C, "settings.json"), settings(True))
    with open(LOG, "a") as f:
        f.write(f"swapped {int(time.time())}\n")


threading.Thread(target=swap, daemon=True).start()
prompt = ("Run these Bash commands, each as its own separate Bash tool call, in order, waiting for each: "
          "`echo one`, `sleep 12`, `echo two`, `sleep 12`, `echo three`, `echo four`. Then say done.")
env = {**os.environ, "CLAUDE_CONFIG_DIR": C}
# Only echo and sleep, from the empty temp folder: the first version bypassed every permission.
r = subprocess.run(["claude", "-p", prompt, "--allowedTools", "Bash(echo:*)", "Bash(sleep:*)", "--max-turns", "15"],
                   env=env, cwd=C, capture_output=True, text=True, timeout=600)
print("claude exit", r.returncode, (r.stdout or r.stderr).strip()[-300:])
log = open(LOG).read() if os.path.exists(LOG) else ""
print(log)
lines = log.split()
v1, v2, post = "v1" in lines, "v2" in lines, "post" in lines
after = log.split("swapped", 1)[1] if "swapped" in log else ""
print(f"RESULT hooks_per_tool_use={v1 and v2} settings_reread_mid_call={'post' in after}")
# The first run left a copy of your login in /tmp; nothing of it stays now.
shutil.rmtree(C, ignore_errors=True)
