#!/usr/bin/env python3
"""skill-rules: load a skill's own rules when it starts (spec 0077 AC-4).

PreToolUse (matcher Skill) takes `tool_input.skill`; UserPromptSubmit takes the first token of a prompt that starts
with `/` directly followed by a name (a typed `/architect` fires no Skill hook, probe P1). The name, lower cased, is
looked up in ~/.claude/rules-on-demand/map.json (CLAUDE_LIVE_DIR overrides ~/.claude): exact key only, so
`plugin:skill` matches only a `plugin:skill` key. Each mapped file is printed as additionalContext under a
`# rules for /<skill>: <file>` line. Unknown skill or any error: no output, exit 0. `--test` runs the self checks.
Python 3 stdlib only.
"""
import json
import os
import re
import sys

NAME = re.compile(r"/([A-Za-z0-9][\w:.-]*)")


def live():
    return os.environ.get("CLAUDE_LIVE_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def skill_of(data):
    event = data.get("hook_event_name")
    if event == "PreToolUse":
        name = (data.get("tool_input") or {}).get("skill")
    elif event == "UserPromptSubmit":
        m = NAME.match(str(data.get("prompt") or ""))
        name = m.group(1) if m else None
    else:
        return event, None
    return event, name.lower() if isinstance(name, str) and name else None


def context(data):
    event, skill = skill_of(data)
    if not skill:
        return None
    folder = os.path.join(live(), "rules-on-demand")
    with open(os.path.join(folder, "map.json")) as f:
        files = json.load(f).get(skill)
    if not files:
        return None
    parts = []
    for name in files:
        with open(os.path.join(folder, name)) as f:
            parts.append(f"# rules for /{skill}: {name}\n{f.read()}")
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": "\n".join(parts)}}


def self_test():
    import subprocess
    import tempfile
    failures = []

    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "rules-on-demand")
        os.makedirs(d)
        for n, body in (("a.md", "rule A\n"), ("b.md", "rule B\n"), ("p.md", "rule P\n")):
            with open(os.path.join(d, n), "w") as f:
                f.write(body)
        with open(os.path.join(d, "map.json"), "w") as f:
            json.dump({"architect": ["a.md", "b.md"], "code-review": ["a.md"], "sentry:find": ["p.md"],
                       "gone": ["missing.md"]}, f)

        def run(data, raw=None):
            p = subprocess.run([sys.executable, os.path.abspath(__file__)], input=raw if raw is not None else json.dumps(data),
                               capture_output=True, text=True, env={**os.environ, "CLAUDE_LIVE_DIR": tmp})
            return p.returncode, (json.loads(p.stdout) if p.stdout.strip() else None), p.stderr

        def ctx(out):
            return out[1]["hookSpecificOutput"]["additionalContext"] if out[1] else None

        def check(name, got, want):
            if got != want:
                failures.append(f"{name}: got {got!r}, want {want!r}")

        both = "# rules for /architect: a.md\nrule A\n\n# rules for /architect: b.md\nrule B\n"
        pre = {"hook_event_name": "PreToolUse", "tool_name": "Skill", "tool_input": {"skill": "architect"}}
        out = run(pre)
        check("Skill tool start loads every mapped file in order", ctx(out), both)
        check("Skill tool start names its event", out[1] and out[1]["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        ups = lambda prompt: {"hook_event_name": "UserPromptSubmit", "prompt": prompt}
        out = run(ups("/architect foo bar"))
        check("a typed /architect foo bar loads architect", ctx(out), both)
        check("a typed command names its event", out[1] and out[1]["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        check("a typed name is lower cased", ctx(run(ups("/Architect"))), both)
        check("/ architect gives nothing", run(ups("/ architect")), (0, None, ""))
        check("a plain prompt gives nothing", run(ups("please architect this")), (0, None, ""))
        check("an unknown skill gives nothing", run({**pre, "tool_input": {"skill": "nope"}}), (0, None, ""))
        check("plugin:skill does not fall back to the part after the colon",
              run({**pre, "tool_input": {"skill": "code-review:code-review"}}), (0, None, ""))
        check("an exact plugin:skill key loads", ctx(run({**pre, "tool_input": {"skill": "sentry:find"}})),
              "# rules for /sentry:find: p.md\nrule P\n")
        check("a mapped file that is missing gives nothing, exit 0", run({**pre, "tool_input": {"skill": "gone"}}), (0, None, ""))
        check("stdin that is not JSON gives nothing, exit 0", run(None, raw="not json"), (0, None, ""))
        check("another event gives nothing", run({"hook_event_name": "Stop"}), (0, None, ""))
        with open(os.path.join(d, "map.json"), "w") as f:
            f.write("{broken")
        check("a broken map gives nothing, exit 0", run(pre), (0, None, ""))

    for f in failures:
        print(f"FAIL {f}")
    print(f"skill-rules self checks: {'all passed' if not failures else f'{len(failures)} failed'}")
    return 1 if failures else 0


def main(argv):
    if argv[:1] == ["--test"]:
        return self_test()
    try:
        out = context(json.load(sys.stdin))
    except Exception:  # never stop a skill or a prompt because this hook broke
        return 0
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
