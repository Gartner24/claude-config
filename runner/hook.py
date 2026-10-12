# PreToolUse hook on AskUserQuestion (spec 0005 AC-4, AC-5). `wf run` passes it
# per call through --settings, so interactive sessions never see it. It answers
# a safe panel or one wf already got an answer for, and defers everything else.
import hashlib
import json
import os
import sys

# The safe list. "doc type" takes its one (recommended) option instead.
FIXED = {"save verify steps?": "Save to verify.md", "agent skills": "Not now, later"}


def safe_answer(q):
    """The AC-5 answer label for one question, or None when it is not safe."""
    if q.get("multiSelect"):
        return None
    header = str(q.get("header", "")).strip().casefold()
    labels = [str(o.get("label", "")).strip() for o in q.get("options", [])]
    if header == "doc type":
        picks = [l for l in labels if "(recommended)" in l]
        return picks[0] if len(picks) == 1 else None
    want = FIXED.get(header)
    return want if want in labels else None


def panel_key(questions):
    return hashlib.sha1(json.dumps(questions, sort_keys=True).encode()).hexdigest()


def out(decision, **extra):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision, **extra}}))


def main():
    run_dir = os.environ.get("WF_RUN_DIR")
    if not run_dir:
        return
    try:
        questions = json.load(sys.stdin)["tool_input"]["questions"]
        key = panel_key(questions)
        path = os.path.join(run_dir, "answers.json")
        stored = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        if key in stored:
            return out("allow", updatedInput={"questions": questions, "answers": stored[key]})
        answers = {q["question"]: safe_answer(q) for q in questions}
        if questions and all(answers.values()):
            with open(os.path.join(run_dir, "auto.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "questions": questions, "answers": answers}) + "\n")
            return out("allow", updatedInput={"questions": questions, "answers": answers})
        out("defer")
    except Exception as e:
        out("deny", permissionDecisionReason=f"wf hook error: {e}; end your final message with a DECISION NEEDED: line instead")


if __name__ == "__main__":
    main()
