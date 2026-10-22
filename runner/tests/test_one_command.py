"""Spec 0020 AC-10: no runner text, report, hook line or rule tells you to type a wf subcommand; they say `wf`."""
import ast
import re
import sys
import tempfile
import unittest
from pathlib import Path

RUNNER = Path(__file__).resolve().parent.parent
TYPE_IT = re.compile(r"\b(type|run|then|next:)\s+`?wf (finish|unpark|report|queue|run)\b", re.I)
TO_DO = re.compile(r"\bwf (finish|unpark|report|queue|run) to (retry|accept)\b", re.I)
RULES = ("claude-home/rules/runner-handoff.md", "claude-home/rules/scope-contract.md")


def constants(path):
    """Every string constant of a module, docstrings and build_parser's help texts left out: (line, text)."""
    tree = ast.parse(path.read_text(), str(path))
    skip = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body \
                and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            skip.add(id(node.body[0].value))
        if isinstance(node, ast.FunctionDef) and node.name == "build_parser":
            skip |= {id(n) for n in ast.walk(node) if isinstance(n, ast.Constant)}
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            out.append((node.lineno, node.value))
        # An f-string is matched whole, its holes as `{}`, so `next: wf {x}` still reads as one sentence.
        if isinstance(node, ast.JoinedStr):
            text = "".join(v.value if isinstance(v, ast.Constant) else "{}" for v in node.values)
            out.append((node.lineno, text))
    return out


def offenders(items):
    return [f"{where}: {text!r}" for where, text in items if TYPE_IT.search(text) or TO_DO.search(text)]


class TestOneCommand(unittest.TestCase):
    # covers: AC-10 (every string constant of runner/*.py and every line of the two rule copies: zero matches)
    def test_corpus(self):
        items = [(f"{p.name}:{n}", t) for p in sorted(RUNNER.glob("*.py")) for n, t in constants(p)]
        for rel in RULES:
            items += [(f"{rel}:{n}", line) for n, line in enumerate((RUNNER.parent / rel).read_text().splitlines(), 1)]
        bad = offenders(items)
        self.assertEqual(len(bad), 0, f"{len(bad)} text(s) tell you to type a wf subcommand:\n" + "\n".join(bad))

    # covers: AC-10 (red on a planted `wf finish` in a print; naming an internal as a thing is fine)
    def test_planted(self):
        planted = 'def f():\n    """Run wf finish here."""\n    print("next: wf finish")\n'
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d) / "planted.py"
            tmp.write_text(planted)
            self.assertEqual(len(offenders([(n, t) for n, t in constants(tmp)])), 1)
        self.assertEqual(offenders([("x", "a wf run holds this repo"), ("y", "`wf run` refuses"),
                                    ("z", "(wf unpark to retry)"), ("w", "then `wf finish`")]),
                         ["z: '(wf unpark to retry)'", "w: 'then `wf finish`'"])

    # covers: AC-10 (the rule texts the spec names)
    def test_rules(self):
        self.assertNotIn("wf finish", (RUNNER.parent / RULES[1]).read_text())


if __name__ == "__main__":
    sys.exit(unittest.main())
