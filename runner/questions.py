# Open questions at the keyboard (spec 0039): the `wf` screen's questions section and `wf questions`. An answer
# tapped on the phone while wf was off used to be the only way in, and Telegram drops it after about a day.
import os

import run
import telegram
import wf


def open_list():
    """AC-1: the open questions in queue.json, oldest asked first. Raises run.QueueError."""
    return sorted((d for d in run.queue_transact()["decisions"] if d["answer"] is None), key=run.asked_at)


def lines(d, links=False):
    """AC-1, AC-5: a question's lines for the terminal (real names, control characters out)."""
    c = lambda t: wf.clean(str(t))
    out = [f"{c(d['id'])} {c(os.path.basename(d['repo']))}: {c(d['feature'])}: {c(d['question'])}"]
    out += [f"  {n} {c(o)}" + (" (recommended)" if n == 1 else "") for n, o in enumerate(d["options"], 1)] or \
        ["  (no options, type your answer)"]
    if links:
        ctx = d.get("context") if isinstance(d.get("context"), dict) else {}
        pr = ctx.get("pr") if isinstance(ctx.get("pr"), dict) else {}
        out += [f"  spec: {c(ctx['spec'])}"] if ctx.get("spec") else []
        out += [f"  issue: {c(u)}" for u in ctx.get("issues") or []]
        out += [f"  PR: #{c(pr.get('number'))} {c(pr.get('url') or '')}".rstrip()] if pr else []
        out.append(f"  asked: {c(d['asked'])}")
    return out


def answer(did, text):
    """AC-2, AC-3: the phone's record change, from the keyboard, under queue.lock; the record, or None when it is
    gone or already answered."""
    hit = []

    def change(q):
        d = next((d for d in q["decisions"] if d["id"] == did and d["answer"] is None), None)
        if d:
            d.update(answer=telegram.answer_text(d, text), source="keyboard", answered=run.now())
            hit.append(d)
        return bool(d)

    run.queue_transact(change)
    return hit[0] if hit else None


def screen(yes):
    """AC-1, AC-2: the section, then one prompt per question unless yes. 130 when you cancel, else None."""
    try:
        ds = open_list()
    except run.QueueError as e:
        print(f"warning: questions not read: {wf.clean(str(e))}")
        return None
    if not ds:
        return None
    print("questions:")
    for d in ds:
        for line in lines(d):
            print("  " + line)
    if yes:
        return None
    try:
        for d in ds:
            text = input(f"answer {d['id']} (number, text, Enter skips): ").strip()
            if not text:
                continue
            got = answer(d["id"], text)
            print(f"answered: {d['id']} {wf.clean(got['answer'])} (keyboard)" if got else f"already answered: {d['id']}")
    except (EOFError, KeyboardInterrupt):
        print()
        return 130
    except run.QueueError as e:
        print(f"warning: answer not written: {wf.clean(str(e))}")
    return None


def cmd_questions():
    """AC-5: read only."""
    try:
        ds = open_list()
    except run.QueueError as e:
        print(f"refused: queue_unreadable: {wf.clean(str(e))}")
        return 5
    if not ds:
        print("no open questions")
    for d in ds:
        print("\n".join(lines(d, links=True)))
    return 0
