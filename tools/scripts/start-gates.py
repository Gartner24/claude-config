#!/usr/bin/env python3
"""start-gates: may one more agent start now? (spec 0073 AC-1 to AC-3)

`start-gates [--running N]` (N = agents already running, default 0) prints
`go: <gib> GiB free, 5 hour use <p>%, cores per suite <c>` and exits 0, or `wait: <reason>` and exits 1.
Free memory is MemAvailable in /proc/meminfo (on a Mac, from sysctl and vm_stat); the 5 hour use is read from your account the way the retired
runner's usage.py read it (one GET, no cache). The login token is read for that one request and never printed,
logged or written. A value that cannot be read is unknown, and unknown means wait. `--test` runs the self checks.
"""
import argparse
import io
import json
import math
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

MEMINFO = "/proc/meminfo"
MIN_FREE_GB = 4.5
MAX_FIVE_HOUR = 80
URL = "https://api.anthropic.com/api/oauth/usage"
TIMEOUT = 5
NOT_LOGIN = "not a subscription login"
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def free_gb(path=MEMINFO):
    """MemAvailable in GiB (kB / 1024 / 1024), None when unread."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / 1024 / 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


def mac_free_gb(memsize, vm_stat):
    """Darwin (spec 0082 AC-5): `sysctl -n hw.memsize` and `vm_stat` output; (free + inactive + speculative pages)
    times the page size from vm_stat's first line, in GiB, never above the total; None when unread."""
    try:
        total = int(memsize.strip())
        page = int(re.search(r"page size of (\d+) bytes", vm_stat.split("\n", 1)[0]).group(1))
        pages = dict(re.findall(r"^(Pages [a-z ]+):\s+(\d+)\.", vm_stat, re.M))
        avail = sum(int(pages[k]) for k in ("Pages free", "Pages inactive", "Pages speculative")) * page
    except (ValueError, AttributeError, KeyError):
        return None
    return min(avail, total) / 1024 ** 3


def read_free_gb():
    if sys.platform != "darwin":
        return free_gb()
    try:
        out = [subprocess.run(c, capture_output=True, text=True, timeout=10, stdin=subprocess.DEVNULL, check=True).stdout
               for c in (["sysctl", "-n", "hw.memsize"], ["vm_stat"])]
    except (OSError, subprocess.SubprocessError):
        return None
    return mac_free_gb(*out)


def token(env):
    """The subscription login's access token, else None (copied from runner/usage.py token())."""
    if env.get("ANTHROPIC_API_KEY"):
        return None
    base = env.get("ANTHROPIC_BASE_URL")
    if base:
        host = (urllib.parse.urlsplit(base).hostname or "").casefold()
        if host != "anthropic.com" and not host.endswith(".anthropic.com"):
            return None
    folder = env.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    try:
        with open(os.path.join(folder, ".credentials.json"), encoding="utf-8") as f:
            t = json.load(f)["claudeAiOauth"]["accessToken"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return t if isinstance(t, str) and t else None


def claude_version():
    try:
        r = subprocess.run(["claude", "--version"], capture_output=True, text=True, errors="replace", timeout=60,
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    words = r.stdout.split()
    return CONTROL.sub("", words[0]) or "unknown" if r.returncode == 0 and words else "unknown"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    # urllib carries the Authorization header across a redirect, to any host (PR 172 review); a 3xx is an error here
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def five_hour(env=None, urlopen=OPENER.open, version=claude_version, url=URL):
    """(percent, None) or (None, reason)."""
    tok = token(os.environ if env is None else env)
    if tok is None:
        return None, NOT_LOGIN
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {tok}", "anthropic-beta": "oauth-2025-04-20", "anthropic-version": "2023-06-01",
        "Accept": "application/json", "User-Agent": f"claude-code/{version()}"})
    del tok
    try:
        with urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        code = e.code
        e.close()
        return None, f"usage service: {code}"
    except Exception as e:
        # The class name only: an exception's text is never shown, so nothing of the request can leak through it.
        return None, f"usage service: {type(e).__name__}"
    finally:
        req.headers.clear()
    try:
        u = json.loads(raw)["five_hour"]["utilization"]
    except (ValueError, KeyError, TypeError):
        return None, "unreadable"
    # runner/usage.py:73 read a null utilization as 0; unknown is never zero here
    if isinstance(u, bool) or not isinstance(u, (int, float)) or not (math.isfinite(u) and 0 <= u <= 100):
        return None, "unreadable"
    return float(u), None


def gates(running, gb, use, cpus):
    """(exit code, line)."""
    if gb is None:
        return 1, "wait: free memory unknown"
    if gb < MIN_FREE_GB:
        return 1, f"wait: {gb:.1f} GiB free, needs {MIN_FREE_GB:g}"
    used, why = use()
    if used is None:
        return 1, f"wait: 5 hour use unknown ({why})"
    if used >= MAX_FIVE_HOUR:
        return 1, f"wait: 5 hour use {used:g}%, needs under {MAX_FIVE_HOUR}"
    return 0, f"go: {gb:.1f} GiB free, 5 hour use {used:g}%, cores per suite {max(2, cpus // (running + 1))}"


def main(argv):
    ap = argparse.ArgumentParser(prog="start-gates")
    ap.add_argument("--running", type=int, default=0)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args(argv)
    if a.test:
        return self_test()
    if a.running < 0:
        ap.error("--running must be 0 or more")
    # a Mac has no sched_getaffinity (spec 0082 AC-5)
    cpus = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count() or 1
    code, line = gates(a.running, read_free_gb(), five_hour, cpus)
    print(line)
    return code


def self_test():
    import tempfile
    failures = []

    def check(name, got, want):
        if got != want:
            failures.append(f"{name}: got {got!r}, want {want!r}")

    class Answer(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            self.close()

    seen = []

    def fake_open(body=None, exc=None):
        def urlopen(req, timeout):
            seen.append((req.full_url, dict(req.header_items()), timeout))
            if exc:
                raise exc
            return Answer(body)
        return urlopen

    with tempfile.TemporaryDirectory() as tmp:
        mem = os.path.join(tmp, "meminfo")
        with open(mem, "w") as f:
            f.write("MemTotal:       16000000 kB\nMemFree:  100 kB\nMemAvailable:    3145728 kB\n")
        check("3.0 GiB read", free_gb(mem), 3.0)
        check("missing meminfo", free_gb(os.path.join(tmp, "nope")), None)
        with open(mem, "w") as f:
            f.write("MemTotal: 1 kB\n")
        check("no MemAvailable line", free_gb(mem), None)

        # spec 0082 AC-5: an Apple silicon vm_stat, 16384 byte pages; 65536 + 98304 + 32768 pages = 3.0 GiB
        vm = ("Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free:                               65536.\n"
              "Pages active:                            400000.\nPages inactive:                           98304.\n"
              "Pages speculative:                        32768.\nPages throttled:                              0.\n"
              "Pages wired down:                        150000.\n")
        check("mac 3.0 GiB read", mac_free_gb("17179869184\n", vm), 3.0)
        check("mac page size from line 1", mac_free_gb("17179869184\n", vm.replace("16384", "4096", 1)), 0.75)
        check("mac capped at total", mac_free_gb("1073741824\n", vm), 1.0)
        check("mac no speculative line", mac_free_gb("17179869184\n", vm.replace("Pages speculative", "Pages x")), None)
        check("mac no page size", mac_free_gb("17179869184\n", vm.split("\n", 1)[1]), None)
        check("mac no total", mac_free_gb("", vm), None)
        # the Darwin branch runs sysctl and vm_stat, faked here on PATH
        fake = os.path.join(tmp, "bin")
        os.makedirs(fake)
        for name, body in (("sysctl", "17179869184"), ("vm_stat", vm)):
            with open(os.path.join(fake, name), "w") as f:
                f.write(f"#!/bin/sh\ncat <<'EOF'\n{body}\nEOF\n")
            os.chmod(os.path.join(fake, name), 0o755)
        saved = sys.platform, os.environ["PATH"]
        sys.platform, os.environ["PATH"] = "darwin", fake + os.pathsep + os.environ["PATH"]
        try:
            check("darwin reads sysctl and vm_stat", read_free_gb(), 3.0)
        finally:
            sys.platform, os.environ["PATH"] = saved

        cfg = os.path.join(tmp, "cfg")
        os.makedirs(cfg)
        with open(os.path.join(cfg, ".credentials.json"), "w") as f:
            json.dump({"claudeAiOauth": {"accessToken": "tok-SECRET-123"}}, f)
        env = {"CLAUDE_CONFIG_DIR": cfg}
        ver = lambda: "9.9.9"

        # AC-3: one GET with the runner's headers, the token in the Authorization header only
        got = five_hour(env, fake_open(b'{"five_hour": {"utilization": 50.0}}'), ver)
        check("usage read", got, (50.0, None))
        check("one GET", len(seen), 1)
        url, headers, timeout = seen[0]
        check("url and timeout", (url, timeout), (URL, 5))
        check("headers", headers, {"Authorization": "Bearer tok-SECRET-123", "Anthropic-beta": "oauth-2025-04-20",
                                   "Anthropic-version": "2023-06-01", "Accept": "application/json",
                                   "User-agent": "claude-code/9.9.9"})
        # AC-2: null, missing or odd utilization is unknown, never 0
        check("null utilization", five_hour(env, fake_open(b'{"five_hour": {"utilization": null}}'), ver),
              (None, "unreadable"))
        check("missing window", five_hour(env, fake_open(b'{"seven_day": {"utilization": 1}}'), ver), (None, "unreadable"))
        check("not json", five_hour(env, fake_open(b"<html>"), ver), (None, "unreadable"))
        check("bool utilization", five_hour(env, fake_open(b'{"five_hour": {"utilization": true}}'), ver),
              (None, "unreadable"))
        # PR 172 review: NaN, infinite or out of range is unknown, never a percent
        for raw in (b"NaN", b"Infinity", b"-1", b"100.5"):
            check(f"utilization {raw.decode()}", five_hour(env, fake_open(b'{"five_hour": {"utilization": %s}}' % raw), ver),
                  (None, "unreadable"))
        check("utilization 100 kept", five_hour(env, fake_open(b'{"five_hour": {"utilization": 100}}'), ver), (100.0, None))
        check("the default opener", five_hour.__defaults__[1], OPENER.open)

        # PR 172 review: a redirect is never followed, so the token never reaches the other place
        import http.server
        import threading
        hits = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append((self.path, self.headers.get("Authorization")))
                if self.path == "/usage":
                    self.send_response(302)
                    self.send_header("Location", f"http://127.0.0.1:{srv.server_port}/elsewhere")
                    self.end_headers()
                else:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'{"five_hour": {"utilization": 1}}')

            def log_message(self, *a):
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            got = five_hour(env, version=ver, url=f"http://127.0.0.1:{srv.server_port}/usage")
        finally:
            srv.shutdown()
            srv.server_close()
        check("redirect not followed", (got, [p for p, _ in hits]), ((None, "usage service: 302"), ["/usage"]))

        err = urllib.error.HTTPError(URL, 429, "too many", {}, io.BytesIO(b"x"))
        check("http error", five_hour(env, fake_open(exc=err), ver), (None, "usage service: 429"))
        check("network error", five_hour(env, fake_open(exc=TimeoutError("tok-SECRET-123")), ver),
              (None, "usage service: TimeoutError"))
        n = len(seen)
        check("api key", five_hour({**env, "ANTHROPIC_API_KEY": "k"}, fake_open(b"{}"), ver), (None, NOT_LOGIN))
        check("foreign base url", five_hour({**env, "ANTHROPIC_BASE_URL": "http://localhost:4000"}, fake_open(b"{}"), ver),
              (None, NOT_LOGIN))
        check("anthropic base url kept", token({**env, "ANTHROPIC_BASE_URL": "https://api.anthropic.com"}), "tok-SECRET-123")
        check("no credentials", five_hour({"CLAUDE_CONFIG_DIR": tmp}, fake_open(b"{}"), ver), (None, NOT_LOGIN))
        check("no request without a login", len(seen), n)

        # AC-1, AC-2: the gate lines and exits
        use = lambda p: (lambda: (p, None))
        check("6.0 GiB, 50% goes", gates(0, 6.0, use(50.0), 8), (0, "go: 6.0 GiB free, 5 hour use 50%, cores per suite 8"))
        check("cores split", gates(3, 6.0, use(50.0), 8)[1], "go: 6.0 GiB free, 5 hour use 50%, cores per suite 2")
        check("cores floor 2", gates(7, 6.0, use(50.0), 8)[1], "go: 6.0 GiB free, 5 hour use 50%, cores per suite 2")
        check("cores 16 by 2", gates(1, 6.0, use(10.0), 16)[1], "go: 6.0 GiB free, 5 hour use 10%, cores per suite 8")
        check("4.5 exactly goes", gates(0, 4.5, use(79.9), 4)[0], 0)
        check("3.0 GiB waits", gates(0, 3.0, use(50.0), 8), (1, "wait: 3.0 GiB free, needs 4.5"))
        check("80% waits", gates(0, 6.0, use(80.0), 8), (1, "wait: 5 hour use 80%, needs under 80"))
        check("memory unknown", gates(0, None, use(10.0), 8), (1, "wait: free memory unknown"))
        check("use unknown", gates(0, 6.0, lambda: (None, "usage service: URLError"), 8),
              (1, "wait: 5 hour use unknown (usage service: URLError)"))

        # the real command, run with no login: it waits and never prints the token
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--running", "1"], capture_output=True,
                           text=True, env={"PATH": os.environ.get("PATH", ""), "HOME": tmp,
                                           "CLAUDE_CONFIG_DIR": tmp, "ANTHROPIC_API_KEY": "k"})
        check("command waits on unknown", (p.returncode, p.stdout.startswith("wait: ")), (1, True))
        check("bad --running", subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--running", "-1"],
                                              capture_output=True).returncode, 2)

    for f in failures:
        print(f"FAIL {f}")
    print(f"start-gates self checks: {'all passed' if not failures else f'{len(failures)} failed'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
