#!/usr/bin/env python3
# Spec 0009 AC-11 P2 through the built code (build step 8): run.Run.freeze_guard builds the frozen guard of a
# linked worktree, start_app starts the real bwrap jail with jail_argv and the app env. The "app" runs every
# check first, prints the results to its log, then serves, so start_app's own readiness proves the host reaches it.
import os, shlex, shutil, subprocess, sys, tempfile
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../runner"))
import ntfy, run  # noqa: E402

PORT = int(os.environ.get("PORT", "8791"))
os.environ.setdefault("CLAUDE_CODE_OAUTH_TOKEN", "p2-probe-token")
root = os.path.realpath(tempfile.mkdtemp(prefix="p2-"))
main, wt = os.path.join(root, "main"), os.path.join(root, "wt")
g = lambda *a: subprocess.run(["git", "-c", "user.name=p", "-c", "user.email=p@example.invalid", *a], check=True,
                              capture_output=True)
g("init", "-q", main)
os.makedirs(os.path.join(main, ".claude"))
with open(os.path.join(main, ".claude", "settings.json"), "w") as f:
    f.write("{}\n")
g("-C", main, "add", "-A")
g("-C", main, "commit", "-qm", "p2")
g("-C", main, "worktree", "add", "-q", "-b", "p2wt", wt)

r = run.Run.__new__(run.Run)
r.c, r.record, r.refuse = SimpleNamespace(path=wt), {}, lambda reason, detail: sys.exit(f"refused: {reason}: {detail}")
assert r.freeze_guard() is None
common = r.guard_settings["sandbox"]["filesystem"]["denyWrite"][-1].rsplit("/", 1)[0]
ssh = sorted(os.listdir(os.path.expanduser("~/.ssh")) or ["none"])[0]
runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
cfg, state = os.path.dirname(ntfy.path()), run.state_dir()
checks = f"""
cat ~/.ssh/{shlex.quote(ssh)} >/dev/null 2>&1 && echo 'ssh read: OPEN' || echo 'ssh read: refused'
touch ~/probe-wf 2>/dev/null && echo 'home write: OPEN' || echo 'home write: refused'
touch {wt}/probe 2>/dev/null && echo 'repo write: ok' || echo 'repo write: FAILED'
touch {common}/hooks/probe 2>/dev/null && echo 'git hooks write: OPEN' || echo 'git hooks write: refused'
echo x > {wt}/.claude/settings.json 2>/dev/null && echo '.claude write: OPEN' || echo '.claude write: refused'
echo 'gitdir: /tmp/x' > {wt}/.git 2>/dev/null && echo 'worktree .git pointer write: OPEN' || echo 'worktree .git pointer write: refused'
for s in {runtime}/gnupg/S.gpg-agent {runtime}/gnupg/S.gpg-agent.ssh ${{SSH_AUTH_SOCK:-/nonexistent}}; do
  python3 -c 'import socket,sys; s=socket.socket(socket.AF_UNIX); s.connect(sys.argv[1])' $s 2>/dev/null \\
    && echo "socket $s: OPEN" || echo "socket $s: refused"
done
echo "oauth token in env: ${{CLAUDE_CODE_OAUTH_TOKEN:+PRESENT}}${{CLAUDE_CODE_OAUTH_TOKEN:-absent}}"
echo "wf config folder entries: $(ls -A {cfg} 2>/dev/null | wc -l)"
echo "wf state dir entries: $(ls -A {state} 2>/dev/null | wc -l)"
exec python3 -m http.server {PORT} --bind 127.0.0.1
"""
r.browser = {"start": checks, "url": f"http://127.0.0.1:{PORT}",
             "wf_dirs": list(dict.fromkeys(os.path.realpath(p) for p in (cfg, os.path.dirname(run.allowed_path()), state)))}
r.folder, r.run_id, r.interrupted, r.app, r.app_term_at = root, "p2-probe", False, None, None
app = {"url": r.browser["url"], "logs": [], "ready_s": None, "exit": None}
try:
    r.start_app(app, "app.log")
    print(f"app from host: {run.http_status(r.browser['url'])} (ready after {app['ready_s']} s)")
finally:
    try:
        r.stop_app(check=False)
    except Exception as e:
        print("stop:", e)
print(open(os.path.join(root, "app.log")).read().split("Serving HTTP")[0].strip())
print(f"after: ~/probe-wf {'exists' if os.path.exists(os.path.expanduser('~/probe-wf')) else 'absent'}; "
      f"{wt}/probe {'exists' if os.path.exists(wt + '/probe') else 'absent'}")
jail = r.jail_argv()
print("ro binds:", [a for i, a in enumerate(jail) if i and jail[i - 1] == "--ro-bind" and a not in ("/", "/dev/null")])
shutil.rmtree(root, ignore_errors=True)
