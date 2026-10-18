#!/usr/bin/env python3
"""Design preview facts for the /plan pane, as JSON on stdout.

shortcut: stands in for `wf plan --json` (spec 0060 AC-1) until row 73 builds it; it reads the scopes through the
runner's own functions, but skips the `in review` state (prs records) and merges worktrees by skipping them.
"""
import glob
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "runner"))

SPEC = re.compile(r"specs/(?:[^/)]*/)?(\d{4})-")
STATUS = re.compile(r"^\*\*Status\*\*:\s*(.+)$", re.M)


def spec_status(repo, num):
    for f in glob.glob(f"{repo}/docs/specs/{num}-*.md") + glob.glob(f"{repo}/docs/specs/{num}-*/index.md"):
        try:
            m = STATUS.search(Path(f).read_text())
        except OSError:
            continue
        if m:
            import wf
            return wf.clean(m.group(1).strip())
    return "unknown"


REVIEW = {"draft", "ready", "approved"}


def state(heading, boxes, building, prs):
    import wf
    if wf.GONE_TAG.search(heading):
        return wf.GONE_TAG.search(heading).group(0).strip("\u00b7() ").lower(), None, None
    nb = wf.pick_next(boxes)
    name = wf.DISPLAY_TAG.sub("", heading).strip()
    pr = prs.get(name)
    if nb is None:
        return "done (untagged)", None, pr
    if name in building:
        return "building", nb, pr
    if nb.owed is not None:
        return "waits on you", nb, pr
    # spec 0060 AC-1 rule 3; `local` is built on its branch but not pushed: waiting to publish
    if pr and pr["state"] in REVIEW:
        return "in review", nb, pr
    if pr and pr["state"] == "local":
        return "to publish", nb, pr
    cmd = (nb.command or "").split()[0] if nb.command else ""
    return {"/architect": "needs a design", "/develop": "ready to build"}.get(cmd, "in progress"), nb, pr


def repo_prs(path):
    """{feature name: newest PR record} for this repo from queue.json; {} when it cannot be read."""
    import run
    import wf
    try:
        recs = run.queue_transact()["prs"]
    except Exception:
        return {}
    real = os.path.realpath(path)
    out = {}
    for r in recs:
        if os.path.realpath(r.get("repo") or "") == real and r.get("feature"):
            out[wf.DISPLAY_TAG.sub("", r["feature"]).strip()] = r
    return out


def repo_entry(c, building):
    import wf
    out = {"name": wf.clean(c.name), "path": c.path, "hub": c.is_hub, "warnings": [wf.clean(w) for w in c.warnings]}
    if c.is_hub:
        out["rows"] = wf.open_rows(c.text)
        return out
    feats = []
    prs = repo_prs(c.path)
    for heading, raw, _plain, deferred in wf.sections(c.text):
        boxes = wf.parse_text("\n".join(raw))
        if not boxes:
            continue
        st, nb, pr = state(heading, boxes, building, prs)
        m = SPEC.search("\n".join(raw))
        feats.append({
            "heading": wf.clean(wf.DISPLAY_TAG.sub("", heading).strip()),
            "state": st,
            "next": wf.clean(nb.box_text) if nb else None,
            "command": wf.clean(nb.command) if nb and nb.command else None,
            "spec": m.group(1) if m else None,
            "specStatus": spec_status(c.path, m.group(1)) if m else None,
            "deferred": deferred,
            "pr": pr.get("number") if pr else None,
            "prState": wf.clean(str(pr.get("state"))) if pr and pr.get("state") else None,
        })
    out["features"] = feats
    return out


def main():
    import auto
    import run
    import wf
    try:
        building = {wf.DISPLAY_TAG.sub("", a.get("feature") or "").strip() for a in run.read_active() if auto.entry_running(a)}
    except Exception:
        building = set()
    repos = []
    for c in wf.discover():
        if c.label:  # a worktree of a repo already listed
            continue
        try:
            repos.append(repo_entry(c, building))
        except Exception as e:  # a broken scope is listed with its error, never dropped
            repos.append({"name": wf.clean(c.name), "path": c.path, "error": wf.clean(str(e))})
    print(json.dumps({"repos": repos}))


if __name__ == "__main__":
    main()
