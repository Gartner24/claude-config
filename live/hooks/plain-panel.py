#!/usr/bin/env python3
# Spec 0028 AC-3 to AC-6: a PreToolUse hook on AskUserQuestion. Every question needs a last option "Learn this first"
# and at most 3 real options; with the runner's plain.py importable, its words are checked for jargon too.
# It never blocks a panel it cannot read, and a crash lets the panel through (AC-17).
import importlib.util
import json
import os
import sys

LEARN = "learn this first"
FIX = ('add a last option "Learn this first" (explain the ideas here from zero with an example, then ask again), '
       "split a question with more than 3 real options")


def load_jargon(folder=None):
    """AC-4: plain.jargon from the folder of the real ~/.local/bin/wf, else None."""
    try:
        folder = folder or os.path.dirname(os.path.realpath(os.path.expanduser("~/.local/bin/wf")))
        spec = importlib.util.spec_from_file_location("wf_plain", os.path.join(folder, "plain.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.jargon
    except Exception:
        return None


def problems(data, jargon=None):
    """The stderr lines for a panel; [] when it passes or is not the AskUserQuestion shape."""
    questions = (data.get("tool_input") or {}).get("questions") if isinstance(data, dict) else None
    if not isinstance(questions, list):
        return []
    out = []
    for n, q in enumerate(questions, 1):
        if not isinstance(q, dict) or not isinstance(q.get("options"), list):
            continue
        opts = [o if isinstance(o, dict) else {} for o in q["options"]]
        last = str(opts[-1].get("label", "")).casefold().strip() if opts else ""
        missing = []
        if not last.startswith(LEARN):
            missing.append('no last option "Learn this first"')
        if len(opts) > 4:
            missing.append(f"{len(opts) - (not missing)} real options, at most 3")
        if missing:
            out.append(f"panel: question {n}: {', '.join(missing)}; {FIX}")
        if jargon:
            text = " ".join([str(q.get("question", ""))] + [str(o.get(k, "")) for o in opts
                                                              for k in ("label", "description")])
            hits = jargon(text)
            if hits:
                out.append(f"panel: question {n}: plain words: {', '.join(hits)}")
    return out


def selftest():
    def panel(*qs):
        return {"tool_input": {"questions": [{"question": q, "header": "h", "multiSelect": False,
                                              "options": [{"label": l, "description": "d"} for l in labels]}
                                             for q, labels in qs]}}
    learn = "Learn this first"
    assert problems(panel(("Pick one?", ["A", "B"])))
    assert problems(panel(("Pick one?", ["A", "B", learn]))) == []
    assert problems(panel(("Pick one?", ["A", "B", "C", "D", learn])))
    two = problems(panel(("Pick one?", ["A", learn]), ("Pick two?", ["A", "B"])))
    assert len(two) == 1 and two[0].startswith("panel: question 2: "), two
    assert problems("not a dict") == [] and problems({"tool_input": {}}) == []
    bad = panel(("Retry after verify_failed?", ["A", learn]))
    jargon = load_jargon()
    if jargon is None:
        assert problems(bad, jargon) == []
    else:
        assert problems(bad, jargon) == ["panel: question 1: plain words: verify_failed"], problems(bad, jargon)
    repo = load_jargon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "runner"))
    if repo:
        assert problems(bad, repo) == ["panel: question 1: plain words: verify_failed"]
    assert main_text("{not json") == 0
    # AC-17: a crash in the check lets the panel through.
    assert main_text(json.dumps(panel(("Pick one?", ["A", learn]))), lambda: lambda t: 1 / 0) == 0
    print("plain-panel: all checks passed")


def main_text(raw, jargon=load_jargon):
    try:
        lines = problems(json.loads(raw), jargon())
    except Exception:
        return 0
    for line in lines:
        print(line, file=sys.stderr)
    return 2 if lines else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        selftest()
        sys.exit(0)
    sys.exit(main_text(sys.stdin.read()))
