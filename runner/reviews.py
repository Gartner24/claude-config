# Review requests (spec 0032). In a held repo whose ~/.claude/private/pr.json entry says review_requests: true, the
# runner process finds PRs that ask you for a review, asks you on the phone, drafts a review in one isolated call
# (/code-review over the PR as data in a clean folder, never a checkout of it) and posts it only on your exact
# "post as my review".
import json
import os
import re

import ntfy
import pr
import run
import wf

FIELDS = "number,title,author,url"
VIEW = "number,title,author,url,state,isDraft,headRefOid,baseRefOid,additions,deletions,changedFiles"
CASES = ("review_request", "review_draft", "review_edit")
POST = "post as my review"
EVENTS = {"approve": "APPROVE", "comment": "COMMENT", "request changes": "REQUEST_CHANGES"}
LINE = re.compile(r"^[ \t>*-]*DRAFT (COMMENT|SUMMARY|VERDICT):\**[ \t]*(.*)$")
COMMENT = re.compile(r"^`?([^\s`:]+)`?:(\d+)`?\s+(\S.*)$")
NO_SUMMARY = "Review notes inline."
PROMPT = ("/code-review PR #{n} ({base}...{head}) of someone else. Its diff is between the data markers below and in "
          "pr.diff in this folder; the changed files' full text at the head is in files.txt. Review with Read, Grep "
          "and Glob only. Never run /review, /review-stack or /code-review ultra, and edit nothing. End with one line "
          "per comment: DRAFT COMMENT: <file>:<line> <text> (the line in the new file), one line DRAFT SUMMARY: "
          "<one paragraph>, and one line DRAFT VERDICT: approve|comment|request changes.\n")
DIFF_MAX, FILE_MAX, FILES_MAX = 150000, 60000, 400000


def enabled(r):
    """AC-1: pr.json's entry for this repo says review_requests: true (the boolean only)."""
    return pr.flag(r, "review_requests")


def records(r):
    return [x for x in r.queue().get("reviews", []) if x["repo"] == run.key_of(r.c)]


def find(r, feature):
    return next((x for x in records(r) if x["feature"] == feature), None)


def save(r, rec):
    def write(q):
        q["reviews"] = [x for x in q.get("reviews", []) if (x["repo"], x["number"]) != (rec["repo"], rec["number"])] \
            + [rec]
        return True
    r.queue(write)


def withdraw(r, rec):
    r.queue(lambda q: q.update(decisions=[d for d in q["decisions"] if not (
        d["repo"] == rec["repo"] and d["feature"] == rec["feature"])]) or True)


# -- find requests (AC-2, AC-3) ------------------------------------------------------

def poll(r):
    """AC-2: the open PRs asking you for a review on this repo; each new one recorded and asked, each one that no
    longer asks you set gone."""
    if not enabled(r):
        return
    name, binary = pr.origin_repo(r), r.gh
    found, why = pr.gh_json(binary, "search", "prs", "--review-requested=@me", "--state", "open", "--repo", name,
                            "--json", FIELDS, "--limit", "30")
    if not isinstance(found, list):
        r.note(f"review requests not read: {why}")
        return
    numbers = {p.get("number") for p in found if isinstance(p, dict)}
    recs = records(r)
    for rec in recs:
        if rec["state"] in ("asked", "drafted") and rec["number"] not in numbers:
            rec["state"] = "gone"
            save(r, rec)
            withdraw(r, rec)
    known = {x["number"] for x in recs}
    me = (pr.out(pr.gh(binary, "api", "user", "--jq", ".login")) or "").strip()
    for n in sorted(x for x in numbers if isinstance(x, int) and x not in known):
        v, why = pr.gh_json(binary, "pr", "view", str(n), "--repo", name, "--json", VIEW)
        if not isinstance(v, dict) or not isinstance(v.get("headRefOid"), str):
            r.note(f"PR #{n} not read: {why}")
            continue
        author = (v.get("author") or {}).get("login") or ""
        if v.get("isDraft") or v.get("state") != "OPEN" or (me and author == me):
            continue
        title = run.flat(v.get("title"))[:60]
        rec = {"repo": run.key_of(r.c), "number": n, "feature": f"review PR #{n}: {title}", "title": title,
               "author": author, "url": v.get("url") if isinstance(v.get("url"), str) else None,
               "head": v["headRefOid"], "base": v.get("baseRefOid"),
               "size": [v.get("additions"), v.get("deletions"), v.get("changedFiles")], "state": "asked", "draft": None}
        save(r, rec)
        a, d, f = rec["size"]
        r.pr_ask(rec, "review_request", f"PR #{n} {title} by {author}, +{a} -{d} in {f} files {rec['url'] or ''}")


# -- answers (AC-3, AC-6 to AC-8) ------------------------------------------------------

def answer(r, d):
    """An answered review question (already taken out of the queue by pr.answer)."""
    rec = find(r, d["feature"])
    if rec is None or rec["state"] in ("posted", "skipped", "gone"):
        return
    text = d["answer"]
    if d["case"] == "review_request":
        opt = next((o for o in d["options"] if o.casefold() == run.flat(text).casefold()), d["options"][0])
        if opt == "skip":
            rec["state"] = "skipped"
            return save(r, rec)
        return draft(r, rec)
    if rec.get("draft") is None:
        return
    if d["case"] == "review_draft" and text == POST:
        # AC-8: only the exact label posts.
        return post(r, rec)
    if d["case"] == "review_draft" and text == "don't post":
        rec["state"] = "skipped"
        return save(r, rec)
    if d["case"] == "review_draft" and text == "edit first":
        return r.pr_ask(rec, "review_edit", "reply with the text that replaces the summary")
    # AC-7: free text (or the edit reply) replaces the summary; never posts.
    rec["draft"]["summary"] = str(text or "").strip() or NO_SUMMARY
    save(r, rec)
    write_draft(r, rec)
    send_draft(r, rec)
    ask_draft(r, rec)


def ask_draft(r, rec, why=""):
    dr = rec["draft"]
    r.pr_ask(rec, "review_draft", f"post this review of PR #{rec['number']}? verdict: {dr['verdict']}, "
                                  f"{len(dr['comments'])} line comments" + (f". Last try: {why}" if why else ""))


# -- the read only call (AC-4, AC-5) ---------------------------------------------------

def isolated(r, folder):
    """AC-4: settings for the call on someone else's PR: the guard's sandbox and read denies, all hooks off, writes
    only in the data folder, no network; the repo and its git dir not writable."""
    repo = os.path.realpath(r.c.path)
    common = pr.out(wf.git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")) or os.path.join(repo, ".git")
    g = json.loads(r.settings)
    g.pop("hooks", None)
    g["disableAllHooks"] = True
    sb = g.setdefault("sandbox", {})
    sb.update(enabled=True, failIfUnavailable=True, allowUnsandboxedCommands=False)
    sb["network"] = {"allowedDomains": [], "strictAllowlist": True}
    fs = sb.setdefault("filesystem", {})
    fs["allowWrite"] = [folder]
    fs["denyWrite"] = list(dict.fromkeys(fs.get("denyWrite", []) + [repo, os.path.realpath(common)]))
    return {"cwd": folder, "settings": json.dumps(g)}


def data_folder(r, rec, base, head):
    """AC-4: a clean folder holding only the PR as data: pr.diff and files.txt (each changed file's text at the head,
    one after another). No checkout, so nothing of the PR (.claude/, CLAUDE.md, .mcp.json) is ever where claude
    loads configuration. Returns (folder, diff text, changed files)."""
    repo, n = r.c.path, rec["number"]
    diff = (wf.git(repo, "diff", "--no-ext-diff", "--no-textconv", base, head) or None)
    diff = diff.stdout if diff is not None and diff.returncode == 0 else ""
    files = [f for f in (pr.out(wf.git(repo, "diff", "--name-only", "--no-renames", base, head)) or "").split("\n") if f]
    folder = os.path.join(r.folder, f"review-{n}")
    os.makedirs(folder, mode=0o700, exist_ok=True)
    parts = []
    for i, f in enumerate(files, 1):
        show = wf.git(repo, "show", "--no-textconv", f"{head}:{f}")
        text = show.stdout if show is not None and show.returncode == 0 else "(deleted at the head)"
        parts.append(f"===== file {i}: {f} =====\n{text[:FILE_MAX]}")
    with open(os.path.join(folder, "pr.diff"), "w", encoding="utf-8") as fh:
        fh.write(diff)
    with open(os.path.join(folder, "files.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts)[:FILES_MAX])
    return folder, diff, set(files)


def parse(lines, files):
    """AC-5: the draft from the DRAFT lines only; comments on a changed file and a line number."""
    dr = {"verdict": "comment", "summary": NO_SUMMARY, "comments": []}
    for line in lines:
        m = LINE.match(line)
        if not m:
            continue
        kind, rest = m.group(1), m.group(2).strip()
        if kind == "VERDICT" and rest.casefold() in EVENTS:
            dr["verdict"] = rest.casefold()
        elif kind == "SUMMARY" and rest:
            dr["summary"] = rest
        elif kind == "COMMENT":
            c = COMMENT.match(rest)
            if c and c.group(1) in files:
                dr["comments"].append({"path": c.group(1), "line": int(c.group(2)), "body": c.group(3).strip()})
    return dr


def draft(r, rec):
    """AC-4, AC-5: fetch the PR head, the PR as data in a clean folder, one isolated call, the draft."""
    repo, n = r.c.path, rec["number"]
    res = wf.git(repo, "fetch", "--quiet", "origin", f"+refs/pull/{n}/head:refs/wf/review/{n}")
    head = pr.out(wf.git(repo, "rev-parse", "--verify", "--quiet", f"refs/wf/review/{n}^{{commit}}"))
    if res is None or res.returncode or not head:
        r.note(f"PR #{n}: the PR head could not be fetched")
        return r.pr_ask(rec, "review_request", f"PR #{n}: the PR head could not be fetched; try again?")
    # The newest head is drafted and recorded (the PR may have moved since you were asked).
    rec["head"] = head
    base = rec.get("base")
    if base and not pr.out(wf.git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")):
        wf.git(repo, "fetch", "--quiet", "origin", base)
    if not base or not pr.out(wf.git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")):
        base = pr.out(wf.git(repo, "merge-base", head, "HEAD")) or f"{head}~1"
    folder, diff, files = data_folder(r, rec, base, head)
    if len(diff) > DIFF_MAX:
        diff = diff[:DIFF_MAX] + "\n(cut here; the rest is in pr.diff)"
    prompt = PROMPT.format(base=base[:12], head=head[:12], n=n) + pr.fenced(
        f"title: {rec['title']}\nauthor: {rec['author']}\n\n{diff}")
    lines = r.review_call(rec, prompt, kind="review_request", isolated=isolated(r, folder))
    rec["draft"] = parse(lines, files)
    rec["state"] = "drafted"
    save(r, rec)
    write_draft(r, rec)
    send_draft(r, rec)
    ask_draft(r, rec)


def write_draft(r, rec):
    dr = rec["draft"]
    text = "\n".join([f"# Draft review of PR #{rec['number']}: {rec['title']}", f"verdict: {dr['verdict']}", "",
                      dr["summary"], ""] + [f"- {c['path']}:{c['line']} {c['body']}" for c in dr["comments"]])
    pr.write_text(r, f"review-{rec['number']}.md", text + "\n")


def phone_body(cfg, rec):
    """AC-6: the draft as phone text: each line scrubbed and block list checked; file names only."""
    dr = rec["draft"]
    lines = [f"draft review of PR #{rec['number']}: verdict {dr['verdict']}",
             "summary: " + ntfy.scrub_field(cfg, dr["summary"], 1000, "(hidden, see the run folder)")]
    for c in dr["comments"]:
        where = f"{os.path.basename(c['path'])}:{c['line']}"
        lines.append(ntfy.scrub_field(cfg, f"{where} {c['body']}", 400, f"{where} (hidden, see the run folder)"))
    return "\n".join(lines)


def send_draft(r, rec):
    """AC-6: Telegram up to 3 messages, else a file; ntfy one cut message naming the run folder."""
    cfg, body = r.ntfy, phone_body(r.ntfy, rec)
    try:
        if "chat_id" in cfg:
            import telegram
            ok = telegram.send_report(cfg, body)
        else:
            ok = ntfy.Topic(cfg, "", "").publish(ntfy.cut(body, 3500) + "\nfull draft in the run folder", 3,
                                                 stopped=lambda: False, title="wf review draft", tags=[])
    except Exception as e:
        ok, body = False, f"{type(e).__name__}"
    if not ok:
        r.note(f"PR #{rec['number']}: the draft was not sent to the phone; it is in the run folder")


# -- post only on your tap (AC-8, AC-9) ---------------------------------------------------

def post(r, rec):
    """AC-8: scans, then the one allowed review post, by the wf process. A failure asks the draft question again."""
    name, n, dr = pr.origin_repo(r), rec["number"], rec["draft"]
    v, why = pr.gh_json(r.gh, "pr", "view", str(n), "--repo", name or "", "--json", "state")
    if not isinstance(v, dict):
        return ask_draft(r, rec, f"the PR could not be read: {why}")
    if v.get("state") != "OPEN":
        rec["state"] = "gone"
        return save(r, rec)
    texts = [("review summary", dr["summary"])] + [(f"comment {c['path']}:{c['line']}", c["body"]) for c in dr["comments"]]
    hit = pr.scans(r, {"branch": None}, None, texts)
    if hit:
        return ask_draft(r, rec, f"{hit[0]} found in {hit[1]}; edit first")
    event = EVENTS.get(dr["verdict"], "COMMENT")
    body = {"commit_id": rec["head"], "event": event, "body": dr["summary"],
            "comments": [{"path": c["path"], "line": c["line"], "side": "RIGHT", "body": c["body"]} for c in dr["comments"]]}
    path = pr.write_text(r, f"review-{n}.json", json.dumps(body))
    try:
        res = pr.gh(r.gh, "api", "-X", "POST", f"repos/{name}/pulls/{n}/reviews", "--input", path, posting=True)
    except pr.Refused as e:
        return ask_draft(r, rec, str(e))
    if res.returncode:
        return ask_draft(r, rec, run.flat(res.stderr or res.stdout)[:150] or f"exit {res.returncode}")
    rec["state"] = "posted"
    save(r, rec)
    r.record.setdefault("prs", []).append({"at": run.now(), "what": "review", "feature": rec["feature"], "number": n,
                                           "event": event})
    r.save()
    r.note(f"posted: your review of PR #{n} ({event.casefold().replace('_', ' ')})")
    print(f"posted: review of PR #{n}", flush=True)
