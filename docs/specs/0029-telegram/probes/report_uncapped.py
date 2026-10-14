# AC-9: report.render keeps every item for Telegram, ntfy keeps its 12 line cap.
import datetime, os, sys, tempfile
w = tempfile.mkdtemp()
os.environ["XDG_STATE_HOME"] = os.path.join(w, "state")
os.environ["XDG_CONFIG_HOME"] = os.path.join(w, "config")
sys.path.insert(0, os.path.join(sys.argv[1], "runner"))
import report  # noqa: E402

repo = os.path.join(w, "demo")
os.makedirs(repo)
rec = {"ended": datetime.datetime.now().astimezone().isoformat(), "stop_reason": "queue_done", "calls": [],
       "features": [{"outcome": "feature_done", "feature": f"feature {i:02d}"} for i in range(30)]}
src = [{"path": repo, "name": "demo", "folder": os.path.join(w, "run"), "code": 0, "rec": rec}]
base = {"aliases": {}, "block": []}
_, tg = report.render(src, {**base, "chat_id": 4242, "token": "123456:" + "a" * 35})
_, nt = report.render(src, {**base, "topic": "t" * 40, "server": "https://ntfy.sh", "codes": []})
tg_built, nt_lines = sum(l.startswith("built:") for l in tg.split("\n")), nt.split("\n")
print(f"telegram: {len(tg.split(chr(10)))} lines, {tg_built} built lines; ntfy: {len(nt_lines)} lines, last item {nt_lines[-2]!r}")
ok = tg_built == 30 and len(nt_lines) <= 12 and "more on the wf screen" in nt and w not in tg
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
