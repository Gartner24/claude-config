"""Spec 0038 verify can-fail check: each mutant breaks a copy of runner/telegram.py one way, and the step it names
must go FAIL in verify-styled.py. The repo's runner/ is never touched."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE.parents[3] / "runner"
MUTANTS = [
    ("V1", "the from: lines go in unescaped", "            out.append(e(line))", "            out.append(line)"),
    ("V1", "the question goes in unescaped", 'f"<b>{e(question)}</b>"', 'f"<b>{question}</b>"'),
    ("V2", "a link shows other text than it opens", "\">{e(m.group(2))}</a>", "\">link</a>"),
    ("V2", "the unverified words lose their collapsed quote", "\\n<blockquote expandable>", "\\n<blockquote>"),
    ("V3", "the from: room ignores the 4096 limit", "MAX - len(\"\\n\".join(lines)) - options_len",
     "3 * MAX - len(\"\\n\".join(lines)) - options_len"),
    ("V4", "sent holds the escaped text", 'd["sent"] = "\\n".join(lines)', 'd["sent"] = "\\n".join(map(html.escape, lines))'),
    ("V5", "a refused HTML message is not resent plain", "                except ApiError:\n                    pass",
     "                except ApiError:\n                    raise"),
    ("V6", "acks and reports go as HTML too", '{**p, "text": styled, "parse_mode": "HTML"}',
     '{**p, "text": styled or p["text"], "parse_mode": "HTML"}'),
]
bad = 0
for vid, what, old, new in MUTANTS:
    tmp = Path(tempfile.mkdtemp())
    copy = tmp / "runner"
    shutil.copytree(RUNNER, copy, ignore=shutil.ignore_patterns("__pycache__"))
    f = copy / "telegram.py"
    src = f.read_text()
    assert src.count(old) == 1, f"mutant anchor not found once: {old!r}"
    src = src.replace(old, new)
    if vid == "V6":
        src = src.replace("            if styled:\n                try:", "            if True:\n                try:")
    f.write_text(src)
    out = subprocess.run([sys.executable, "-B", str(HERE / "verify-styled.py"), str(copy)], capture_output=True,
                         text=True).stdout
    red = any(l.startswith(f"FAIL {vid} ") for l in out.splitlines())
    bad += not red
    print(f"{'RED ' if red else 'GREEN'} {vid} {what}")
    shutil.rmtree(tmp)
sys.exit(bad)
