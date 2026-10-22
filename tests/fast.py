"""Spec 0043 AC-7: the runner suite, every test in its own process with its own temporary XDG_STATE_HOME,
as many at once as the machine has cores. `fast.py [module | module.Class]` runs only that part. Exit 0 only when
every test passed; each failing test's output is printed."""
import concurrent.futures
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
# A test that hangs fails instead of holding the whole run.
TIMEOUT = 600


def tests(only=None):
    """Every test id the loader finds in test_*.py here, or under `only` (a module or module.Class)."""
    def walk(suite):
        for t in suite:
            if isinstance(t, unittest.TestSuite):
                yield from walk(t)
            else:
                yield t.id()
    sys.path.insert(0, HERE)
    loader = unittest.defaultTestLoader
    suite = loader.loadTestsFromName(only) if only else loader.discover(HERE, pattern="test_*.py", top_level_dir=HERE)
    return list(dict.fromkeys(walk(suite)))


def run(test):
    with tempfile.TemporaryDirectory(prefix="wf-fast-") as tmp:
        # HOME stays: some tests read your git identity and the private names list from it.
        env = {**os.environ, "XDG_STATE_HOME": os.path.join(tmp, "state")}
        try:
            p = subprocess.run([sys.executable, "-m", "unittest", test], cwd=HERE, capture_output=True, text=True,
                               stdin=subprocess.DEVNULL, env=env, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            return test, 1, f"timed out after {TIMEOUT} s"
    return test, p.returncode, p.stdout + p.stderr


def workers():
    # Spec 0052 AC-6: up to 8 suites run at once under wf, each on its share of the cores (WF_CORES).
    return int(os.environ.get("WF_CORES") or 0) or os.cpu_count() or 4


def main(argv):
    t0 = time.monotonic()
    ids = tests(argv[0] if argv else None)
    with concurrent.futures.ThreadPoolExecutor(workers()) as pool:
        failed = [(t, out) for t, code, out in pool.map(run, ids) if code]
    for t, out in failed:
        print(f"=== {t} ===\n{out}")
    print(f"Ran {len(ids)} tests in {time.monotonic() - t0:.1f}s, {len(failed)} failed")
    print("FAILED" if failed else "OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
