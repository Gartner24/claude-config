#!/usr/bin/env python3
"""Spec 0015 AC-10 P3 (AC-9): a brief agreeing an item and a spec that drops it make the /architect cross check
name it.

One real `claude -p "/architect retries: ..."` in a scratch repo: the scope row's Source names a brief whose
`## Agreed so far, do not ask again` section caps retries at 3; the Proposed spec retries forever. Needs the live
rule. Run it yourself with ! (a few minutes). Expect: the result names the dropped retry cap as a gap with a fix,
and the spec file is left unedited (the call cannot ask, so nothing is answered).
"""
import json
import os
import re
import subprocess
import sys
import tempfile

SPEC = ("# 0001. Retries\n\n**Status**: Proposed\n**Paths:** `fetch.py`\n\n## What you're agreeing to\n\n"
        "- A failed fetch is retried until it works.\n\n## Requirements\n"
        "- **AC-1**: a failed fetch is retried, with no limit on attempts, one second apart.\n")
FILES = {
    "fetch.py": "def fetch():\n    pass\n",
    "AGENTS.md": "# probe\n\nOne Python module.\n",
    "docs/briefs/retries.md": "# Brief: retries\n\n## Agreed so far, do not ask again\n\n"
                              "- Retries are capped at 3 attempts, then the fetch fails loudly.\n"
                              "- Retries wait one second apart.\n",
    "docs/scope/scope.md": "# Scope: probe\n**Workflow:** Alpha\n\n### 1. Retries · needs a decision\n"
                           "- [ ] Design it (spec): `/architect retries`\nSpec [0001](../specs/0001-retries.md)\n"
                           "Source: [docs/briefs/retries.md](../briefs/retries.md)\n",
    "docs/specs/0001-retries.md": SPEC,
}
PROMPT = ("/architect retries: a draft spec exists at docs/specs/0001-retries.md. Run only its cross check now and "
          "report the cross check gaps with a recommended fix for each. Do not edit any file.")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        for rel, text in FILES.items():
            os.makedirs(os.path.join(tmp, os.path.dirname(rel)), exist_ok=True)
            open(os.path.join(tmp, rel), "w").write(text)
        subprocess.run(["git", "init", "-q", "-b", "feat/retries", tmp], check=True)
        subprocess.run(["git", "-C", tmp, "add", "-A"], check=True)
        subprocess.run(["git", "-C", tmp, "-c", "user.name=p", "-c", "user.email=p@example.invalid",
                        "commit", "-qm", "base"], check=True)
        p = subprocess.run(["claude", "-p", PROMPT, "--output-format", "json", "--permission-mode", "auto"],
                           cwd=tmp, capture_output=True, text=True)
        result = (json.loads(p.stdout or "{}").get("result") or "") if p.returncode == 0 else p.stdout + p.stderr
        spec = open(os.path.join(tmp, "docs/specs/0001-retries.md")).read()
    print(result[-3000:])
    checks = {
        "names the dropped retry cap": bool(re.search(r"(3|three)[ \w]{0,20}(attempt|retr)|(cap|limit)\w*[^\n]{0,80}"
                                                      r"(3|three)", result, re.I)),
        "points at the brief": bool(re.search(r"brief|agreed", result, re.I)),
        "spec unedited": spec == SPEC,
    }
    for k, v in checks.items():
        print(f"{'PASS' if v else 'FAIL'} {k}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
