# Context and links in every message (spec 0033). The runner builds each question's `from:` block from what it
# read itself (repo, feature, spec path, step, linked issues, PR URLs from gh, links from the git remote); only
# `did`, `why` and `steps` come from the call, and every piece of outside text is scrubbed and block list checked.
import os
import re
import urllib.parse

import ntfy
import run
import wf

WHY = re.compile(r"^[ \t>*-]*WHY:\**[ \t]*(\S.*)$")
STEP = re.compile(r"^[ \t>*-]*STEP:\**[ \t]*(?:\d+[.)][ \t]*)?(\S.*)$")
DID_MAX = 600
TELEGRAM_MAX = 4096
LABEL = "Question {} (its name, so your reply finds it)"
NO_STEPS = "I could not work out the steps; open a session in the {} repo ({}) and paste: {}"
# AC-7: blocked text that is really the run's own write protection.
DENY_WORDS = re.compile(r"\b(write[- ]?denied|denied|not writable|read[- ]only|permission)\b", re.I)
PATH_TOKEN = re.compile(r"(?<![\w.-])(~?/?[\w.-]+(?:/[\w.-]+)*/?)")


def label(did):
    """AC-5: the question's name on its first use in a message."""
    return LABEL.format(did)


def from_call(result, marker):
    """AC-1, AC-3, AC-6: what the call had done (its text above the marker line, last DID_MAX characters), its WHY
    line and its STEP lines after the marker. marker: a compiled line pattern (DECISION or BLOCKED)."""
    lines = str(result or "").split("\n")
    at = None
    for i, line in enumerate(lines):
        if marker.match(line):
            at = i
    if at is None:
        return {}
    did = run.flat(" ".join(lines[:at]))[-DID_MAX:]
    why = next((run.flat(m.group(1)) for m in map(WHY.match, lines[at + 1:]) if m), None)
    steps = [run.flat(m.group(1)) for m in map(STEP.match, lines[at + 1:]) if m]
    return {k: v for k, v in (("did", did), ("why", why), ("steps", steps)) if v}


def spec_link(origin, branch, rel):
    """AC-2: a blob link from the github.com remote the runner read, else the repo relative path."""
    if not rel:
        return None
    if origin and branch:
        return (f"https://github.com/{origin[0]}/{origin[1]}/blob/{urllib.parse.quote(branch, safe='/')}/"
                f"{urllib.parse.quote(rel, safe='/')}")
    return rel


def build(r, feature, step=None, extra=None):
    """AC-1: the context of a question about feature in the repo in use; missing parts are left out."""
    ctx = {"repo": r.c.display_name() if r.c else None, "feature": feature,
           "branch": (r.repo or {}).get("start_branch") or r.branch}
    try:
        f = r.feature_named(feature) if r.c else None
    except Exception:
        f = None
    import pr
    # As written in the repo's config (git remote get-url applies insteadOf rewrites).
    name = pr.origin_repo(r) if r.c else None
    origin = tuple(name.split("/", 1)) if name else None
    if f is not None:
        top = pr.spec_file(r.c.path, r.c.scope_dir, f.lines)
        rel = os.path.relpath(top, r.c.path) if top else None
        ctx["spec"] = spec_link(origin, ctx["branch"], rel)
        ctx["issues"] = [f"https://github.com/{o}/{n}/issues/{k}" for o, n, k in run.linked_issues(f.lines, origin)]
    if step:
        ctx["step"] = step
    ctx.update({k: v for k, v in (extra or {}).items() if v})
    return {k: v for k, v in ctx.items() if v}


def field(cfg, text, limit):
    return ntfy.scrub_field(cfg, str(text or ""), limit, "")


def link(cfg, url):
    """A runner built link, kept whole, dropped when it holds a block list entry or is no https link."""
    url = str(url or "")
    return url if url.startswith("https://") and not ntfy.blocked(cfg, url) and " " not in url else ""


def step_line(cfg, text):
    """AC-6 on Telegram: a step keeps its paths and commands (a private chat), loses control characters, is cut, and
    is hidden when it holds a block list entry."""
    s = ntfy.cut(wf.clean(" ".join(str(text or "").split())), 300)
    return "" if not s or ntfy.blocked(cfg, s) else s


def telegram_block(cfg, d, room):
    """AC-4: the from: block for a Telegram question, at most room characters (did cut first, then steps)."""
    c = d.get("context") or {}
    head = ["from:"]
    for key, name, n in (("repo", "repo", 80), ("feature", "feature", 120)):
        v = field(cfg, c.get(key), n)
        if v:
            head.append(f"{name}: {v}")
    spec = c.get("spec")
    if spec:
        v = link(cfg, spec) if spec.startswith("https://") else field(cfg, os.path.basename(spec), 120)
        if v:
            head.append(f"spec: {v}")
    if c.get("step"):
        v = step_line(cfg, c["step"])
        if v:
            head.append(f"step: {v}")
    tail = [f"issue: {u}" for u in map(lambda x: link(cfg, x), c.get("issues") or []) if u]
    if c.get("pr"):
        number, url = (c["pr"].get("number"), link(cfg, c["pr"].get("url"))) if isinstance(c["pr"], dict) else (None, "")
        if number or url:
            tail.append(f"PR: #{number} {url}".strip())
    why = field(cfg, c.get("why"), 300)
    if why:
        tail.append(f"why recommended: {why}")
    steps = [step_line(cfg, s) for s in c.get("steps") or []]
    steps = [f"{i}. {s}" for i, s in enumerate((s for s in steps if s), 1)]
    did = field(cfg, c.get("did"), DID_MAX)
    while True:
        lines = head + ([f"did: {did}"] if did else []) + tail + (["steps:"] + steps if steps else [])
        text = "\n".join(lines) if len(lines) > 1 else ""
        if len(text) <= room:
            return text
        if did:
            did = ntfy.cut(did, max(0, len(did) - (len(text) - room) - 4)) if len(did) > 40 else ""
        elif steps:
            steps.pop()
        else:
            return ""


def ntfy_lines(cfg, d):
    """AC-8: the short from: line and the why line for ntfy, scrubbed as today, no links."""
    c = d.get("context") or {}
    if not c:
        return []
    parts = [field(cfg, ntfy.repo_label(cfg, d.get("repo", "")), 40), field(cfg, c.get("feature"), 60),
             field(cfg, c.get("step"), 80)]
    out = ["from: " + " / ".join(p for p in parts if p)] if any(parts) else []
    why = field(cfg, c.get("why"), 200)
    steps = [field(cfg, s, 200) for s in c.get("steps") or []]
    return out + ([f"why: {why}"] if why else []) + [f"{i}. {s}" for i, s in enumerate((s for s in steps if s), 1)]


def blocked_steps(r, feature, box_text, command, blocked, steps):
    """AC-6: the call's steps, else the one line the runner can always give."""
    if steps:
        return steps
    resume = run.flat(f"continue {feature}: {command or box_text}; it was blocked on: {blocked}")[:300]
    return [NO_STEPS.format(r.c.display_name(), r.c.path, resume)]


def denied_in_text(repo, text):
    """AC-7: a path inside the repo named in blocked text that says it was denied, else None."""
    if not DENY_WORDS.search(str(text or "")):
        return None
    root = os.path.realpath(repo)
    for m in PATH_TOKEN.finditer(str(text)):
        raw = m.group(1)
        tok = raw.rstrip("/.")
        if "/" not in raw or not tok:
            continue
        p = os.path.realpath(os.path.expanduser(tok) if tok.startswith(("~", "/")) else os.path.join(root, tok))
        if p != root and run.under(p, [root]):
            return p
    return None
