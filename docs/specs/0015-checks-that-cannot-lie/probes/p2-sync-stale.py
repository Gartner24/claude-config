#!/usr/bin/env python3
"""Spec 0015 AC-10 P2 (AC-7): a commit touching an accepted spec's paths makes /sync list it under
`Specs possibly stale`.

One real `claude -p "/sync two"` in a scratch repo on main: spec 0001 is Accepted and covers `src/*.py`, spec 0002
is the feature being synced and covers `lib/*`. After spec 0002 is added, one commit changes both. Needs the live
rule and `spec-paths` on PATH (./install.sh). Run it yourself with ! (a few minutes). Expect: the result has a
`Specs possibly stale` section naming src/a.py and spec 0001, nothing for 0002, and spec 0001 left unedited.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

SPEC = "# {n}. {t}\n\n**Status**: {s}\n**Paths:** {p}\n\n## Requirements\n- **AC-1**: {t}.\n"
FIRST = {
    "src/a.py": "A = 1\n",
    "lib/b.py": "B = 1\n",
    "AGENTS.md": "# probe\n\nTwo Python files.\n",
    "docs/specs/0001-one.md": SPEC.format(n="0001", t="One", s="Accepted", p="`src/*.py`"),
    "docs/scope/scope.md": "# Scope: probe\n**Workflow:** Alpha\n\n### 1. One · done\nSpec [0001](../specs/0001-one.md)\n\n"
                           "### 2. Two · in-progress\n- [x] Build it: `/develop two`\n- [ ] Sync docs: `/sync two`\n"
                           "Spec [0002](../specs/0002-two.md) · code in `lib/b.py`\n",
}
SECOND = {"docs/specs/0002-two.md": SPEC.format(n="0002", t="Two", s="In Progress", p="`lib/*`")}
THIRD = {"src/a.py": "A = 2\n", "lib/b.py": "B = 2\n"}


def commit(repo, files, msg):
    for rel, text in files.items():
        os.makedirs(os.path.join(repo, os.path.dirname(rel)), exist_ok=True)
        open(os.path.join(repo, rel), "w").write(text)
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
    subprocess.run(["git", "-C", repo, "-c", "user.name=p", "-c", "user.email=p@example.invalid",
                    "commit", "-qm", msg], check=True)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", "-b", "main", tmp], check=True)
        commit(tmp, FIRST, "one")
        commit(tmp, SECOND, "spec two")
        commit(tmp, THIRD, "two, and a touch of one")
        direct = subprocess.run(["spec-paths", "--spec", "0002"], cwd=tmp, capture_output=True, text=True)
        print("spec-paths says:", direct.stdout.strip() or direct.stderr.strip())
        p = subprocess.run(["claude", "-p", "/sync two", "--output-format", "json", "--permission-mode", "auto"],
                           cwd=tmp, capture_output=True, text=True)
        result = (json.loads(p.stdout or "{}").get("result") or "") if p.returncode == 0 else p.stdout + p.stderr
        spec_one = open(os.path.join(tmp, "docs/specs/0001-one.md")).read()
    print(result[-3000:])
    stale = result[result.find("Specs possibly stale"):] if "Specs possibly stale" in result else ""
    checks = {
        "spec-paths warns src/a.py for 0001": "warning: src/a.py touches accepted spec 0001" in direct.stdout,
        "report has Specs possibly stale": bool(stale),
        "it names src/a.py and 0001": "src/a.py" in stale and "0001" in stale,
        "nothing for 0002": not re.search(r"accepted spec 0002", stale),
        "spec 0001 unedited": spec_one == FIRST["docs/specs/0001-one.md"],
    }
    for k, v in checks.items():
        print(f"{'PASS' if v else 'FAIL'} {k}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
