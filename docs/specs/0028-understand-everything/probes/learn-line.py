#!/usr/bin/env python3
"""Spec 0028 P2: a real `claude -p` under the unattended prompt ends a decision with a plain LEARN: line.
Calls the real claude (a live step, run by wf finish, never by an unattended call); sends no ping."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "runner"))
import plain  # noqa: E402
import run  # noqa: E402

TASK = ("Task: this project needs a database. Do not write any file. Ask the user which of two database engines "
        "to use, Postgres or SQLite.")


def main():
    with tempfile.TemporaryDirectory() as d:
        p = subprocess.run(["claude", "-p", "--append-system-prompt", run.unattended_prompt({}, False), TASK], cwd=d,
                           capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=600)
    asked = run.read_decision(p.stdout)
    if not asked:
        print(f"FAIL: no DECISION NEEDED line (exit {p.returncode})")
        return 1
    question, options, learn = asked
    hits = plain.jargon(" ".join([question, *options, learn or ""]))
    print(f"options: {len(options)}, learn: {len(learn or '')} characters, jargon: {', '.join(hits) or 'none'}")
    if options and learn and len(learn) <= 300 and not hits:
        print("PASS")
        return 0
    print("FAIL: options, a LEARN: line of at most 300 characters and no jargon are all needed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
