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


# Security review (steered authorization): questions whose answer widens what a call may write, merges, posts, pushes
# or clears a gate. Their why is the runner's fixed line, call text shows only quoted as unverified, never steps.
AUTH = frozenset(("denied", "approved", "review_draft", "foreign_commits", "guard_changed", "rebase", "private_names",
                  "attribution", "live_step"))
UNVERIFIED = "what the step said, unverified:"


def auth(d):
    return d.get("case") in AUTH


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


def safe(cfg, text, limit, paths=False):
    """Security review (block list bypass): the one gate every phone field passes. Control characters out,
    whitespace runs as one space, cut to limit, and hidden ("") when it holds a block list entry or a name of the
    private names list. Path like tokens are scrubbed as today, except with paths (Telegram only: runner built links
    and paths, a blocked step's commands)."""
    t = " ".join(str(text or "").split())
    s = ntfy.cut(wf.clean(t), limit) if paths else ntfy.scrub(t, limit)
    low, names = s.casefold(), ntfy.private_names()
    # No readable names list: links and paths carry owner and repo names, so they stay hidden (fail closed).
    if not s or ntfy.blocked(cfg, s) or (names is None and paths) or any(n in low for n in names or ()):
        return ""
    return s


def field(cfg, text, limit):
    return safe(cfg, text, limit)


def link(cfg, url):
    """A runner built link, kept whole, dropped when it is no https link or fails safe()."""
    url = str(url or "")
    return safe(cfg, url, 400, paths=True) if url.startswith("https://") and " " not in url else ""


def step_line(cfg, text):
    """AC-6 on Telegram: a step keeps its paths and commands (a private chat), through safe()."""
    return safe(cfg, text, 300, paths=True)


def telegram_block(cfg, d, room):
    """AC-4: the from: block for a Telegram question, at most room characters (did cut first, then steps)."""
    c = d.get("context") or {}
    head = ["from:"]
    # The alias or hashed label ntfy uses, never the raw folder name of a private repo.
    repo = ntfy.repo_label(cfg, d["repo"]) if d.get("repo") else c.get("repo")
    for name, v, n in (("repo", repo, 80), ("feature", c.get("feature"), 120)):
        v = field(cfg, v, n)
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
    if d.get("allow"):
        # The path F1 would allow, as the runner resolved it.
        v = step_line(cfg, d["allow"])
        if v:
            head.append(f"path: {v}")
    tail = [f"issue: {u}" for u in map(lambda x: link(cfg, x), c.get("issues") or []) if u]
    if c.get("pr"):
        number, url = (c["pr"].get("number"), link(cfg, c["pr"].get("url"))) if isinstance(c["pr"], dict) else (None, "")
        if number or url:
            tail.append(f"PR: #{number} {url}".strip())
    import plain
    gated = auth(d)
    why = field(cfg, plain.WHY.get(d.get("case")) if gated else c.get("why"), 300)
    if why:
        tail.append(f"why recommended: {why}")
    steps = [] if gated else [step_line(cfg, s) for s in c.get("steps") or []]
    steps = [f"{i}. {s}" for i, s in enumerate((s for s in steps if s), 1)]
    did = field(cfg, c.get("did"), DID_MAX)
    # Spec 0042 AC-3: what a step only you can do is, in plain words, right under where it comes from.
    what = "" if gated else field(cfg, c.get("what"), 500)
    head += [f"what this is: {what}"] if what else []
    while True:
        if gated:
            # The runner's facts first; the call's words last, quoted and marked unverified.
            lines = head + tail + ([UNVERIFIED, f"> {did}"] if did else [])
        else:
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
    import plain
    gated = auth(d)
    why = field(cfg, plain.WHY.get(d.get("case")) if gated else c.get("why"), 200)
    steps = [] if gated else [field(cfg, s, 200) for s in c.get("steps") or []]
    what = "" if gated else field(cfg, c.get("what"), 300)
    return out + ([f"what: {what}"] if what else []) + ([f"why: {why}"] if why else []) + \
        [f"{i}. {s}" for i, s in enumerate((s for s in steps if s), 1)]


def blocked_steps(r, feature, box_text, command, blocked, steps):
    """AC-6: the call's steps, else the one line the runner can always give."""
    if steps:
        return steps
    resume = run.flat(f"continue {feature}: {command or box_text}; it was blocked on: {blocked}")[:300]
    return [NO_STEPS.format(r.c.display_name(), r.c.path, resume)]


