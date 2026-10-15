import os, shutil, subprocess, sys, tempfile
sys.path.insert(0, sys.argv[1])
import run

t = tempfile.mkdtemp(dir=os.environ["TMPDIR"])
o = os.path.join(t, "origin")


def g(d, *a):
    return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, check=True).stdout.strip()


def commit(d, name, msg):
    p = os.path.join(d, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(msg)
    g(d, "add", "-A")
    g(d, "commit", "-qm", msg)


os.makedirs(o)
g(o, "init", "-qb", "main")
g(o, "config", "user.email", "v@x")
g(o, "config", "user.name", "v")
commit(o, "src/components/Root.tsx", "m1")
g(o, "checkout", "-qb", "beta")
for i in range(3):
    commit(o, f"src/components/Beta{i}.tsx", f"b{i}")
beta = g(o, "rev-parse", "HEAD")
g(o, "checkout", "-qb", "work")
commit(o, "src/components/Work1.tsx", "w1")
commit(o, "src/components/Work2.tsx", "w2")
g(o, "checkout", "-q", "main")
for i in range(10):
    commit(o, f"src/components/Main{i}.tsx", f"m{i + 2}")

c = os.path.join(t, "clone")
subprocess.run(["git", "clone", "-q", "--depth", "4", "--no-single-branch", "-b", "work", f"file://{o}", c], check=True)
g(c, "branch", "-q", "main", "origin/main")
print("shallow:", g(c, "rev-parse", "--is-shallow-repository"))
print("merge-base main rc:", subprocess.run(["git", "-C", c, "merge-base", "HEAD", "main"], capture_output=True).returncode)
print("upstream:", g(c, "rev-parse", "--symbolic-full-name", "@{upstream}"))
base, changed = run.frontend_changed(c)
print("base is beta tip:", base == beta)
print("changed:", changed)
print("test_base same:", run.test_base(c) == base)
shutil.rmtree(t)
assert base == beta and changed == ['src/components/Work1.tsx', 'src/components/Work2.tsx']
