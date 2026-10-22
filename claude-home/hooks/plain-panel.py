#!/usr/bin/env python3
# A PreToolUse hook on AskUserQuestion (rules/plain-questions.md). The decision is explained in chat text first
# (DECISION / OPTIONS / I PICK, one Undo: per option); the panel only collects the answer. This hook checks the
# panel shape only (at most 3 options, first one "(Recommended)", short labels, one line descriptions, no internal
# codes). It does not check the chat text: at PreToolUse time the transcript lags behind the current message, so
# the explanation is not in it yet (live test 2026-10-22). It no longer bans words.
# It never blocks input it cannot read, and a crash lets the panel through.
import json
import re
import sys

MAX_OPTIONS = 3
FIX = ('ask with at most 3 options, the first labelled "(Recommended)", labels 1 to 5 words, '
       "descriptions 6 to 30 words")
CODE = re.compile(r"\bspec \d{4}\b|\bAC-?\d+\b|\b[a-z]+(?:_[a-z0-9]+)+\b", re.I)


def words(s):
    return len(str(s).split())


def problems(data):
    """The stderr lines for a panel; [] when it passes or is not the AskUserQuestion shape."""
    questions = (data.get("tool_input") or {}).get("questions") if isinstance(data, dict) else None
    if not isinstance(questions, list):
        return []
    out = []
    for n, q in enumerate(questions, 1):
        if not isinstance(q, dict) or not isinstance(q.get("options"), list):
            continue
        opts = [o if isinstance(o, dict) else {} for o in q["options"]]
        bad = []
        if len(opts) > MAX_OPTIONS:
            bad.append(f"{len(opts)} options, at most {MAX_OPTIONS}")
        if opts and not str(opts[0].get("label", "")).rstrip().endswith("(Recommended)"):
            bad.append('first option does not end with "(Recommended)"')
        for o in opts:
            label = str(o.get("label", "")).replace("(Recommended)", "")
            if not 1 <= words(label) <= 5:
                bad.append(f"label needs 1 to 5 words: {label.strip()[:30]}")
            if not 6 <= words(o.get("description", "")) <= 30:
                bad.append(f"description needs 6 to 30 words: {label.strip()[:30]}")
        text = " ".join([str(q.get("question", ""))] + [str(o.get(k, "")) for o in opts for k in ("label", "description")])
        codes = sorted({m.group(0) for m in CODE.finditer(text)})
        if codes:
            bad.append(f"internal codes: {', '.join(codes)}")
        if bad:
            out.append(f"panel: question {n}: {'; '.join(bad)}; {FIX}")
    return out


def selftest():
    def panel(*qs, **extra):
        return {**extra, "tool_input": {"questions": [
            {"question": q, "header": "h", "multiSelect": False,
             "options": [{"label": l, "description": "you get one thing; you risk another"} for l in labels]}
            for q, labels in qs]}}
    rec = "Recommended"
    ok = ["A (Recommended)", "B"]
    assert problems(panel(("Pick one?", ok))) == []
    assert problems(panel(("Pick one?", ["A", "B"])))  # no (Recommended)
    assert problems(panel(("Pick one?", ["A (Recommended)", "B", "C", "D"])))  # 4 options
    assert problems(panel(("Pick one?", ["A (Recommended)", "one two three four five six"])))  # 6 word label
    short = panel(("Pick one?", ok))
    short["tool_input"]["questions"][0]["options"][1]["description"] = "too short"
    assert problems(short)
    code = panel(("Retry after verify_failed?", ok))
    assert "internal codes: verify_failed" in problems(code)[0]
    two = problems(panel(("Pick one?", ok), ("Pick two?", ["A", "B"])))
    assert len(two) == 1 and two[0].startswith("panel: question 2: "), two
    # real terms are no longer banned
    assert problems(panel(("Park the guard in bwrap?", ["Park it (Recommended)", "Keep it"]))) == []
    assert problems("not a dict") == [] and problems({"tool_input": {}}) == []
    assert main_text("{not json") == 0
    assert main_text(json.dumps(panel(("Pick one?", ["A", "B"])))) == 2
    # a crash in a check lets the panel through
    assert main_text(json.dumps(panel(("Pick one?", ok))), lambda d: 1 / 0) == 0
    print("plain-panel: all checks passed")


def main_text(raw, check=problems):
    try:
        lines = check(json.loads(raw))
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
