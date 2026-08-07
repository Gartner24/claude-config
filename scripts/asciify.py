#!/usr/bin/env python3
"""Enforce the ASCII-only house rule (CLAUDE.md) on repo-owned markdown.

Skips vendored trees - agents/ and rules/ecc/ are ECC cherry-picks and
skills/anti-ai-writing is third-party; all are overwritten on reinstall, so
editing them is diff noise. Proper nouns keep their accents.

Usage:
  python3 scripts/asciify.py --check    # list offenders, exit 1 if any (CI-safe)
  python3 scripts/asciify.py            # rewrite in place
"""
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

SKIP_PREFIXES = ("agents/", "rules/")
SKIP_SUBSTR = ("anti-ai-writing",)

# Accented characters inside real names. Stripping these corrupts the name.
KEEP = {"Â", "é"}  # A-circumflex (TACHES), e-acute (cafes)

# Dashes are handled by regex before the char table, so that surrounding spaces
# are absorbed instead of doubled: " - " must not become "  -  ".
DASH_RE = [
    (r"[ \t]*—[ \t]*", " - "),  # em dash
    (r"[ \t]*–[ \t]*", "-"),    # en dash (usually a range: 3-5)
]

SUBS = {
    "−": "-",     # minus sign
    "→": "->",    # rightwards arrow
    "↔": "<->",   # left right arrow
    "…": "...",   # ellipsis
    "×": "x",     # multiplication sign
    "§": "sec. ", # section sign
    "≥": ">=",
    "≤": "<=",
    "≈": "~",
    "²": "^2",
    "’": "'",     # right single quote
    "‘": "'",
    "“": '"',
    "”": '"',
    "✓": "[x]",   # check mark
    "─": "-",     # box drawing horizontal
    "│": "|",     # box drawing vertical
    "├": "+",     # tee right
    "└": "\\",    # up and right
    "┬": "+",
    "┐": "+",
    "┌": "+",
    "┘": "+",
    "•": "-",     # bullet
    "\U0001f447": "",  # down pointing hand
}


def owned(rel):
    return not (rel.startswith(SKIP_PREFIXES) or any(s in rel for s in SKIP_SUBSTR))


def convert(text):
    for pat, rep in DASH_RE:
        text = re.sub(pat, rep, text)
    out = []
    left = []
    for ch in text:
        if ord(ch) < 127 or ch in KEEP:
            out.append(ch)
        elif ch in SUBS:
            out.append(SUBS[ch])
        else:
            out.append(ch)
            left.append(ch)
    return "".join(out), left


def main():
    check = "--check" in sys.argv
    files = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=REPO, capture_output=True, text=True
    ).stdout.split()
    changed, unmapped = [], {}
    for rel in files:
        if not owned(rel):
            continue
        p = REPO / rel
        src = p.read_text(encoding="utf-8")
        new, left = convert(src)
        if left:
            unmapped.setdefault(rel, set()).update(left)
        if new != src:
            changed.append(rel)
            if not check:
                p.write_text(new, encoding="utf-8")

    verb = "would change" if check else "changed"
    print(f"{verb} {len(changed)} owned file(s)")
    for rel in changed:
        print("  " + rel)
    if unmapped:
        print("\nunmapped non-ASCII (add to SUBS or KEEP):")
        for rel, chars in unmapped.items():
            print(f"  {rel}: " + " ".join(f"U+{ord(c):04X} {c!r}" for c in sorted(chars)))
        return 1
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
