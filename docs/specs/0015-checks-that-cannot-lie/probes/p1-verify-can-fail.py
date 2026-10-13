#!/usr/bin/env python3
"""Spec 0015 AC-10 P1 (AC-2): a verify step planted to pass on broken code is rewritten or dropped.

One real `claude -p "/check verify add"` in a scratch repo whose verify.md plants a step that cannot fail
(`test -f calc.py`) next to a real one. Needs the live rule (~/.claude/rules/check-gates.md). Run it yourself
with ! (a few minutes). Expect: the result ends with `CAN FAIL CHECKED: <n>`, a `can fail:` note per step, and
the planted step named as rewritten or dropped, never counted as a plain pass.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

FILES = {
    "calc.py": "def add(a, b):\n    return a + b\n",
    "AGENTS.md": "# probe\n\nOne Python module, `calc.py`. No test runner.\n",
    "docs/scope/scope.md": "# Scope: probe\n**Workflow:** Alpha\n\n### 1. Add · in-progress\n- [x] Build it: `/develop add`\n"
                           "- [ ] Verify it: `/check verify add`\nSpec [0001](../specs/0001-add/index.md)\n",
    "docs/specs/0001-add/index.md": "# 0001. Add\n\n**Status**: In Progress\n**Paths:** `calc.py`\n\n## Requirements\n"
                                    "- **AC-1**: `calc.add(a, b)` returns the sum of two integers.\n",
    "docs/specs/0001-add/verify.md": "# Verify: add\n## Commands\n- [ ] `test -f calc.py` -> exits 0 -> AC-1\n"
                                     "- [ ] `python3 -c 'import calc; print(calc.add(2, 3))'` -> prints 5 -> AC-1\n",
}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        for rel, text in FILES.items():
            os.makedirs(os.path.join(tmp, os.path.dirname(rel)), exist_ok=True)
            open(os.path.join(tmp, rel), "w").write(text)
        subprocess.run(["git", "init", "-q", "-b", "feat/add", tmp], check=True)
        subprocess.run(["git", "-C", tmp, "add", "-A"], check=True)
        subprocess.run(["git", "-C", tmp, "-c", "user.name=p", "-c", "user.email=p@example.invalid",
                        "commit", "-qm", "base"], check=True)
        p = subprocess.run(["claude", "-p", "/check verify add", "--output-format", "json",
                            "--permission-mode", "auto"], cwd=tmp, capture_output=True, text=True)
        result = (json.loads(p.stdout or "{}").get("result") or "") if p.returncode == 0 else p.stdout + p.stderr
        reports = "".join(open(os.path.join(d, f)).read() for d, _, fs in os.walk(os.path.join(tmp, "docs"))
                          for f in fs if f.endswith(".md"))
    print(result[-3000:])
    line = [m for m in re.finditer(r"^[ \t>*-]*CAN FAIL CHECKED:\**[ \t]*(\d+)", result, re.M)]
    checks = {
        "ends with CAN FAIL CHECKED": bool(line),
        # One note per step that passed: a dropped planted step leaves 1, a rewritten one 2.
        "a can fail note per step": bool(line) and int(line[-1].group(1)) >= 1
        and len(re.findall(r"can fail:", result + reports, re.I)) >= int(line[-1].group(1)),
        "planted step rewritten or dropped": bool(re.search(r"test -f calc\.py.{0,300}(rewr|drop)|(rewr|drop).{0,300}"
                                                            r"test -f calc\.py", result + reports, re.I | re.S)),
    }
    for k, v in checks.items():
        print(f"{'PASS' if v else 'FAIL'} {k}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
