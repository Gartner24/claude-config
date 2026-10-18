# Spec 0058: the bottom status bar, ported from jjstack's statusline.sh so the bar no longer needs jjstack. Same
# segments, order, colors and thresholds; unlike the script, a value it cannot read shows `?`, never 0.
import json
import os
import subprocess
import sys
import time

CACHE = "/tmp/claude-usage-cache.json"
CACHE_TTL = 300
GIT_TIMEOUT = 1
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CYAN, DIM, RESET = "\033[36m", "\033[2m", "\033[0m"
SEP = f"{DIM} | {RESET}"
EFFORT_COLORS = {"high": "\033[95m", "medium": "\033[93m", "low": "\033[92m", "xhigh": "\033[96m"}
# Runs detached: the script's own refresh, same token, same cache file, written whole or not at all.
REFRESH = """import json, os, sys, urllib.request
creds, cache, url = sys.argv[1:4]
token = json.load(open(creds))["claudeAiOauth"]["accessToken"]
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "anthropic-beta": "oauth-2025-04-20",
                                           "anthropic-version": "2023-06-01", "User-Agent": "claude-code/2.1.81",
                                           "Accept": "application/json"})
with urllib.request.urlopen(req, timeout=5) as resp:
    body = json.loads(resp.read())
with open(cache + ".tmp", "w") as f:
    json.dump(body, f)
os.replace(cache + ".tmp", cache)
"""


def creds_path():
    return os.path.expanduser("~/.claude/.credentials.json")


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def effort(data):
    e = (data.get("effort") or {}).get("level") or os.environ.get("CLAUDE_CODE_EFFORT_LEVEL")
    for f in ("~/.claude/settings.local.json", "~/.claude/settings.json"):
        if e:
            break
        s = read_json(os.path.expanduser(f))
        e = s.get("effortLevel") if isinstance(s, dict) else None
    return str(e or "auto")


def repo_root(cwd):
    """(work tree top, git dir) found by walking up from cwd, as git does, or (None, None); no extra git call."""
    d = os.path.realpath(cwd)
    while True:
        dot = os.path.join(d, ".git")
        if os.path.isdir(dot):
            return d, dot
        if os.path.isfile(dot):
            try:
                with open(dot) as f:
                    line = f.readline().strip()
            except OSError:
                return None, None
            if line.startswith("gitdir: "):
                return d, os.path.join(d, line[len("gitdir: "):])
            return None, None
        parent = os.path.dirname(d)
        if parent == d:
            return None, None
        d = parent


def git(cwd):
    """`branch state` from one `git status`, or "" when it fails or times out (AC-3, AC-5)."""
    if not cwd:
        return ""
    try:
        # --untracked-files=all: the script counted every untracked file, plain status shows a new folder as one line
        p = subprocess.run(["git", "-C", cwd, "status", "--porcelain=v1", "-b", "-z",
                            "--untracked-files=all"],
                           capture_output=True, text=True, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return ""
    if p.returncode != 0:
        return ""
    # -z: without it git quotes and escapes accented or quoted names ("\303\251d/a"), so no path matched the prefix
    lines = p.stdout.split("\0")
    head = lines[0][3:] if lines and lines[0].startswith("## ") else ""
    if head.startswith("No commits yet on "):
        branch = head[len("No commits yet on "):]
    elif head.startswith("HEAD (no branch)"):
        branch = "HEAD"
    else:
        branch = head.split("...")[0].split(" ")[0]
    top, gitdir = repo_root(cwd)
    if branch == "HEAD" and gitdir:
        # the script fell back to `rev-parse --short HEAD`; status only says "no branch", HEAD holds the id
        # shortcut: always 7 characters, git grows it in huge repos; upgrade only if a detached bar ever looks off
        try:
            with open(os.path.join(gitdir, "HEAD")) as f:
                sha = f.read().strip()
        except OSError:
            sha = ""
        branch = sha[:7] if len(sha) == 40 else branch
    # the script's `ls-files --others` counted only untracked files below the working folder; status lists the repo
    prefix = os.path.relpath(os.path.realpath(cwd), top) if top else "."
    prefix = "" if prefix == "." else prefix + "/"
    rows, rest = [], iter(lines[1:])
    for ln in rest:
        if len(ln) > 3:
            rows.append((ln[:2], ln[3:]))
            if set(ln[:2]) & set("RC"):
                # -z puts a rename's or copy's old path in its own field; a working tree rename (git add -N) is " R"
                next(rest, None)
    staged = sum(1 for r, _ in rows if r[0] not in " ?!")
    # the script's `git diff --name-only` lists a both modified or both added conflict twice
    # shortcut: true only while the file still differs from our side (it has conflict markers), as is typical
    modified = sum(1 + (r in ("UU", "AA")) for r, _ in rows if r[1] not in " ?!")
    untracked = sum(1 for r, p in rows if r == "??" and p.startswith(prefix))
    state = " ".join(f"{c}{n}" for c, n in (("+", staged), ("~", modified), ("?", untracked)) if n) or "clean"
    return f"{branch} {state}"


def progress(pct, label, width=0):
    """The script's create_progress_bar: label inside a colored bar, filled share by percent, percent after."""
    pct = int(pct)
    if len(label) < width:
        left = (width - len(label)) // 2
        label = " " * left + label + " " * (width - len(label) - left)
    if pct >= 90:
        color = "\033[41m\033[97m"
    elif pct >= 70:
        color = "\033[43m\033[30m"
    else:
        color = "\033[42m\033[30m"
    padded = f" {label} "
    filled = min(int(pct / 100 * len(padded) + 0.5), len(padded))
    return "".join(f"{color if i < filled else DIM}{ch}{RESET}" for i, ch in enumerate(padded)) + f" {pct}%"


def number(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def refresh(creds):
    subprocess.Popen([sys.executable, "-c", REFRESH, creds, CACHE, USAGE_URL], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def usage(data):
    """The trailing segments: `via <host>` through a provider, the 5 hour and weekly bars on a subscription login,
    else the session cost."""
    base = os.environ.get("ANTHROPIC_BASE_URL", "")
    if base and "anthropic.com" not in base:
        host = base.split("://", 1)[-1].split("/", 1)[0].rsplit("@", 1)[-1].split(":", 1)[0]
        return [f"\033[95mvia {os.environ.get('CLAUDE_PROVIDER_LABEL') or host}{RESET}"]
    creds = creds_path()
    c = read_json(creds)
    if isinstance(c, dict) and (c.get("claudeAiOauth") or {}).get("accessToken"):
        try:
            stale = time.time() - os.path.getmtime(CACHE) >= CACHE_TTL
        except OSError:
            stale = True
        if stale:
            try:
                refresh(creds)
            except OSError:
                pass
        cache = read_json(CACHE)
        cache = cache if isinstance(cache, dict) else {}
        out = []
        for key, label, unknown in (("five_hour", "5h", "5h ?"), ("seven_day", "week", "wk ?")):
            v = cache.get(key)
            v = number(v.get("utilization")) if isinstance(v, dict) else None
            out.append(progress(v, label, 5) if v is not None else f"{DIM}{unknown}{RESET}")
        return out
    cost = number((data.get("cost") or {}).get("total_cost_usd"))
    if cost is None:
        return [f"{DIM}$?{RESET}"]
    color = "\033[95m" if cost >= 5 else "\033[93m" if cost >= 1 else "\033[92m"
    return [f"{color}${cost:.2f}{RESET}"]


def render(data, short=False):
    """The bar for the status line stdin JSON `data`; "" on any failure, so bar() never sees an exception."""
    try:
        cwd = str(data.get("cwd") or (data.get("workspace") or {}).get("current_dir") or "")
        folder = os.path.basename(cwd)
        if short:
            return folder
        e = effort(data)
        model = (data.get("model") or {}).get("display_name") or "unknown"
        line = f"{CYAN}{model}{RESET} {DIM}·{RESET}{EFFORT_COLORS.get(e, DIM)}{e}{RESET}{SEP}{folder}"
        used = number((data.get("context_window") or {}).get("used_percentage"))
        parts = [git(cwd), progress(used, "context") if used is not None else ""] + usage(data)
        return SEP.join([line] + [p for p in parts if p])
    except Exception:
        return ""
