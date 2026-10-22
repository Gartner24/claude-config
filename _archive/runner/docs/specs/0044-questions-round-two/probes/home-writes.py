"""Spec 0044 AC-8: under settings shaped like the runner's (sandbox allowWrite with the home folder, a denyWrite entry and
Edit deny rules for it), a real `claude -p` call may write a file in the home folder outside its repo, with the Write
tool and with Bash, and is denied both ways for the denied folder. Throwaway folders only; prints PASS or FAIL."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

home = os.path.expanduser("~")
ok_dir, deny_dir = os.path.join(home, "wf-probe-0044"), os.path.join(home, "wf-probe-0044-denied")
for d in (ok_dir, deny_dir):
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
repo = tempfile.mkdtemp(prefix="wf-probe-repo-")
rules = [f"{tool}(/{deny_dir}/**)" for tool in ("Edit", "Write", "MultiEdit")]
settings = {"sandbox": {"enabled": True, "failIfUnavailable": True, "autoAllowBashIfSandboxed": True,
                        "allowUnsandboxedCommands": False,
                        "filesystem": {"allowWrite": [repo, home], "denyWrite": [deny_dir]}},
            "permissions": {"deny": rules}}
prompt = (f"Do exactly these four things and nothing else, then report each result in one line. "
          f"1) Use the Write tool to create {ok_dir}/write.txt containing ok. "
          f"2) Use Bash to run: echo ok > {ok_dir}/bash.txt "
          f"3) Use the Write tool to create {deny_dir}/write.txt containing no. "
          f"4) Use Bash to run: echo no > {deny_dir}/bash.txt")
p = subprocess.run(["claude", "-p", prompt, "--output-format", "json", "--permission-mode", "auto",
                    "--settings", json.dumps(settings)], cwd=repo, capture_output=True, text=True, timeout=600,
                   stdin=subprocess.DEVNULL)
try:
    out = json.loads(p.stdout)
except ValueError:
    print("FAIL: no JSON from claude:", p.stdout[-500:], p.stderr[-500:])
    sys.exit(1)
got = {
    "home write tool": os.path.exists(os.path.join(ok_dir, "write.txt")),
    "home bash": os.path.exists(os.path.join(ok_dir, "bash.txt")),
    "denied write tool": os.path.exists(os.path.join(deny_dir, "write.txt")),
    "denied bash": os.path.exists(os.path.join(deny_dir, "bash.txt"))}
print(json.dumps(got))
print("denials:", json.dumps([d.get("tool_name") for d in out.get("permission_denials", [])]))
print("result:", str(out.get("result", ""))[:600])
passed = got["home write tool"] and got["home bash"] and not got["denied write tool"] and not got["denied bash"]
for d in (ok_dir, deny_dir, repo):
    shutil.rmtree(d, ignore_errors=True)
print("PASS" if passed else "FAIL")
sys.exit(0 if passed else 1)
