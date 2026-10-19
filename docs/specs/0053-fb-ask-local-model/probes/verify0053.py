"""Spec 0053 verify driver: run the real fb-ask CLI against a fake proxy that records every request.
Usage: python3 -B verify0053.py [worktree]; no claude, no real proxy, never port 4000."""
import json, os, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

wt = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 4))
fbask = os.path.join(wt, "scripts", "fb-ask.py")
tmp = tempfile.mkdtemp(prefix="v0053-")
key = "sk-verify-" + "Z9" * 10
st = {"models": ["fb-safe", "fb-any", "fb-local"], "usage": {"input_tokens": 200}, "sleep": 0,
      "reply": "the deploy failed on step 3", "gets": [], "posts": []}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        st["gets"].append(self.path)
        if self.path == "/health/liveliness":
            return self.send(200, "ok")
        return self.send(200, {"data": [{"id": m} for m in st["models"]]})

    def do_POST(self):
        st["posts"].append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        time.sleep(st["sleep"])
        r = {"model": "ollama/qwen", "content": [{"type": "text", "text": st["reply"]}]}
        if st["usage"] is not None:
            r["usage"] = st["usage"]
        self.send(200, r)


srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
srv.handle_error = lambda *a: None
threading.Thread(target=srv.serve_forever, daemon=True).start()

home = os.path.join(tmp, "home")
live = os.path.join(home, ".claude", "private")
os.makedirs(live)
open(os.path.join(tmp, "k.env"), "w").write(f"LITELLM_MASTER_KEY={key}\n")
open(os.path.join(live, "fb-ask.conf"), "w").write(f"key file: {tmp}/k.env\n")
open(os.path.join(live, "names.txt"), "w").write("quixotron\n")
# no fb-ok.txt: the origin gate refuses every repo without --local
state_home = os.path.join(tmp, "state")
client = os.path.join(tmp, "client")
genv = {"HOME": home, "PATH": os.environ["PATH"], "GIT_CONFIG_NOSYSTEM": "1"}
subprocess.run(["git", "init", "-q", client], check=True, env=genv)
subprocess.run(["git", "-C", client, "remote", "add", "origin", "git@github.com:someclient/app.git"], check=True, env=genv)
wrapper = ("import importlib.util, json, sys\n"
           "s = importlib.util.spec_from_file_location('fb', sys.argv[1]); m = importlib.util.module_from_spec(s)\n"
           "s.loader.exec_module(m)\n"
           "for k, v in json.loads(sys.argv[2]).items(): setattr(m, k, v)\n"
           "sys.exit(m.main(sys.argv[3:]))\n")


def fb(*args, stdin="client log: payment job crashed", env=None, **patch):
    consts = {"PROXY": f"http://127.0.0.1:{srv.server_port}", "START": "/nonexistent", **patch}
    e = {**genv, "CLAUDE_LIVE_DIR": os.path.join(home, ".claude"), "XDG_STATE_HOME": state_home, **(env or {})}
    r = subprocess.run([sys.executable, "-B", "-c", wrapper, fbask, json.dumps(consts), *args], cwd=client,
                       input=stdin, capture_output=True, text=True, env=e, timeout=60)
    return r.returncode, r.stdout, r.stderr.strip()


results = []


def step(name, cond, evidence):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + name + "  | " + evidence)


# V1 AC-1, AC-2, AC-6: client repo + private name, --local answers through fb-local
n = len(st["posts"])
code, out, err = fb("summarize", "--local", stdin="quixotron payment job crashed")
p = st["posts"][-1] if len(st["posts"]) > n else {}
step("V1 --local in client repo with private name answers via fb-local",
     code == 0 and out == "the deploy failed on step 3\n" and p.get("model") == "fb-local"
     and err.startswith("fb-ask: local fb-local "),
     f"exit={code} out={out!r} err={err!r} model={p.get('model')} max_tokens={p.get('max_tokens')}")
step("V2 summarize max_tokens 1024 locally", p.get("max_tokens") == 1024, f"max_tokens={p.get('max_tokens')}")

# V3 AC-2 without --local: client repo refused, zero requests
n = len(st["posts"])
code, out, err = fb("summarize")
step("V3 client repo refused without --local, no request", code == 4 and out == "" and
     err == "fb-ask: refused: client_repo" and len(st["posts"]) == n, f"exit={code} err={err!r} posts+={len(st['posts'])-n}")

# V4 AC-2 names gate without --local (outside any repo)
plain = os.path.join(tmp, "plain")
os.makedirs(plain)
r = subprocess.run([sys.executable, "-B", "-c", wrapper, fbask,
                    json.dumps({"PROXY": f"http://127.0.0.1:{srv.server_port}", "START": "/nonexistent"}), "summarize"],
                   cwd=plain, input="call with Quixotron", capture_output=True, text=True,
                   env={**genv, "CLAUDE_LIVE_DIR": os.path.join(home, ".claude"), "XDG_STATE_HOME": state_home})
step("V4 private name refused without --local", r.returncode == 4 and r.stderr.strip() == "fb-ask: refused: private_name"
     and "quixotron" not in r.stderr.lower(), f"exit={r.returncode} err={r.stderr.strip()!r}")

# V5 extract 512
st["reply"] = '{"job": "payment"}'
code, out, err = fb("extract", "--fields", "job", "--local")
step("V5 extract locally 512 tokens, fb-local", code == 0 and st["posts"][-1]["max_tokens"] == 512
     and st["posts"][-1]["model"] == "fb-local", f"exit={code} out={out!r} max_tokens={st['posts'][-1]['max_tokens']}")
st["reply"] = "the deploy failed on step 3"

# V6 AC-4 no fb-local in /v1/models -> wrong_proxy, no POST at all (so never fb-safe)
st["models"] = ["fb-safe", "fb-any"]
n = len(st["posts"])
code, out, err = fb("summarize", "--local")
step("V6 proxy without fb-local -> wrong_proxy, zero requests", code == 3 and err == "fb-ask: fall back: wrong_proxy"
     and len(st["posts"]) == n, f"exit={code} err={err!r} posts+={len(st['posts'])-n}")
st["models"] = ["fb-safe", "fb-any", "fb-local"]

# V7 AC-5 input cap
n = len(st["posts"])
ok30 = fb("summarize", "--local", stdin="a" * 30_000)[0]
code, out, err = fb("summarize", "--local", stdin="a" * 30_001)
step("V7 30,000 passes, 30,001 too_large with no request", ok30 == 0 and code == 3 and
     err == "fb-ask: fall back: too_large" and len(st["posts"]) == n + 1, f"30000 exit={ok30} 30001 err={err!r}")

# V8 AC-5b truncation
st["usage"] = {"input_tokens": 15_500}
c1, o1, e1 = fb("summarize", "--local")
st["usage"] = None
c2, o2, e2 = fb("summarize", "--local")
st["usage"] = {"input_tokens": 15_499}
c3, _, _ = fb("summarize", "--local")
step("V8 15,500 and missing usage -> truncated, no answer; 15,499 answers",
     c1 == 3 and o1 == "" and e1 == "fb-ask: fall back: truncated" and c2 == 3 and o2 == "" and c3 == 0,
     f"15500={c1}/{e1!r} missing={c2}/{e2!r} 15499={c3}")
st["usage"] = {"input_tokens": 200}

# V9 AC-5 timeout on LOCAL_WAIT, not ANSWER_WAIT
st["sleep"] = 2
code, out, err = fb("summarize", "--local", LOCAL_WAIT=1, ANSWER_WAIT=30)
step("V9 timeout uses LOCAL_WAIT", code == 3 and err == "fb-ask: fall back: timeout", f"exit={code} err={err!r}")
st["sleep"] = 0

# V10 AC-3 WF_RUN
n = len(st["gets"])
code, out, err = fb("summarize", "--local", env={"WF_RUN": "r9"})
step("V10 WF_RUN -> in_call before any request", code == 3 and err == "fb-ask: fall back: in_call" and
     len(st["gets"]) == n, f"exit={code} err={err!r} gets+={len(st['gets'])-n}")

# V11 AC-3 a lock held by the runner's own repo_lock -> wf_building; runner's entry_running agrees
tree = os.path.join(tmp, "trees", "feat-x")
os.makedirs(os.path.join(state_home, "wf", "locks"), exist_ok=True)
json.dump([{"repo": client, "feature": "x", "tree": tree, "globs": []}], open(os.path.join(state_home, "wf", "active.json"), "w"))
holder = ("import sys, time; sys.path.insert(0, sys.argv[1]); import run\n"
          "fd, who = run.repo_lock(sys.argv[2], create=True, what='verify'); print('held', fd is not None, flush=True)\n"
          "time.sleep(30)\n")
check = ("import sys, json; sys.path.insert(0, sys.argv[1]); import run, auto\n"
         "print(any(auto.entry_running(a) for a in run.read_active()))\n")
renv = {**os.environ, "XDG_STATE_HOME": state_home, "HOME": home}
runner = os.path.join(wt, "runner")
h = subprocess.Popen([sys.executable, "-B", "-c", holder, runner, tree], stdout=subprocess.PIPE, text=True, env=renv)
line = h.stdout.readline().strip()
try:
    rc = subprocess.run([sys.executable, "-B", "-c", check, runner], capture_output=True, text=True, env=renv)
    n = len(st["gets"])
    code, out, err = fb("summarize", "--local")
    step("V11 runner lock held -> wf_building, runner agrees it runs", line == "held True" and code == 3 and
         err == "fb-ask: fall back: wf_building" and rc.stdout.strip() == "True" and len(st["gets"]) == n,
         f"holder={line!r} runner_says={rc.stdout.strip()!r}{rc.stderr.strip()[-200:]} fb={code}/{err!r}")
    code, out, err = fb("summarize", stdin="x")
    step("V12 cloud mode skips the build check (reaches the origin gate)", err == "fb-ask: refused: client_repo",
         f"exit={code} err={err!r}")
finally:
    h.kill()
    h.wait()
code, out, err = fb("summarize", "--local")
step("V13 lock released -> answers again", code == 0, f"exit={code} err={err!r}")

srv.shutdown()
print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
