#!/usr/bin/env python3
"""Check every text/surface token pair for WCAG 2.2 contrast, in BOTH themes.

    contrast.py <tokens.css|any css> [--aaa]

Why a script: axe only sees pairs the rendered page happens to use, so a combination that
exists in the token set but is not on screen at audit time ships unchecked - and the dark
theme is where that bites, because it is usually authored second. This walks the token
matrix instead of the DOM.

Reads :root and the dark-theme block (`[data-theme="dark"]`, `.dark`, or
`prefers-color-scheme: dark`), resolves var() chains, converts oklch()/hex/rgb() to sRGB
luminance, and reports every failing pair with its ratio.

Exit 0 = all pairs pass. Exit 1 = at least one fails.
"""
import math
import re
import sys
import pathlib

AA_BODY, AA_LARGE, AAA_BODY = 4.5, 3.0, 7.0

# token name -> role. A pair is checked when a text role sits on a surface role.
# "muted" and "subtle" are MODIFIERS, not roles. shadcn uses --muted as a surface and
# --muted-foreground as the text on it; treating bare "muted" as text paired a background
# against other backgrounds and reported false failures on a compliant palette. A name
# carrying an explicit text word still classifies as text (--text-muted, --muted-foreground).
TEXT = ("text", "fg", "foreground", "ink", "body", "heading", "link",
        "on-", "label", "caption")
SURF = ("bg", "background", "surface", "canvas", "card", "panel", "elevated", "base",
        "paper", "muted", "subtle", "accent", "popover", "input")


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (srgb_to_lin(max(0.0, min(1.0, x))) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def oklch_to_srgb(L, C, H):
    h = math.radians(H)
    a, bb = C * math.cos(h), C * math.sin(h)
    l_ = L + 0.3963377774 * a + 0.2158037573 * bb
    m_ = L - 0.1055613458 * a - 0.0638541728 * bb
    s_ = L - 0.0894841775 * a - 1.2914855480 * bb
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return tuple(1.055 * (max(x, 0.0) ** (1 / 2.4)) - 0.055 if x > 0.0031308
                 else 12.92 * max(x, 0.0) for x in (r, g, b))


def parse_color(v):
    v = v.strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{3,8})", v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    m = re.match(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)", v)
    if m:
        return tuple(float(x) / 255 for x in m.groups())
    m = re.match(r"oklch\(\s*([\d.]+)%?\s+([\d.]+)\s+([\d.]+)", v)
    if m:
        L, C, H = (float(x) for x in m.groups())
        if L > 1.5:
            L /= 100
        return oklch_to_srgb(L, C, H)
    return None


def block(css, pattern):
    # non-greedy to the first closing brace. Custom-property blocks do not nest, and
    # requiring a newline before "}" made a single-line :root{...} invisible.
    m = re.search(pattern + r"\s*\{(.*?)\}", css, re.S)
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+)\s*;?", m.group(1))) if m else {}


def resolve(name, table, depth=0):
    if depth > 10 or name not in table:
        return None
    v = table[name].strip()
    m = re.match(r"var\(\s*(--[\w-]+)\s*(?:,\s*(.+?))?\s*\)$", v)
    if m:
        r = resolve(m.group(1), table, depth + 1)
        return r if r is not None else (parse_color(m.group(2)) if m.group(2) else None)
    return parse_color(v)


def role(name, keys):
    n = name.lower()
    return any(k in n for k in keys)


def check(theme, table, aaa):
    colors = {k: resolve(k, table) for k in table}
    colors = {k: v for k, v in colors.items() if v}
    texts = [k for k in colors if role(k, TEXT)]
    # Text wins a name collision. "--card-foreground" contains both "card" (SURF) and
    # "foreground" (TEXT); pairing it with itself reported 1.00:1 and made a compliant
    # stock shadcn palette unpassable.
    surfs = [k for k in colors if role(k, SURF) and not role(k, TEXT)]
    unclassified = [k for k in colors if k not in texts and k not in surfs]
    fails = []
    for t in sorted(texts):
        for s in sorted(surfs):
            r = ratio(colors[t], colors[s])
            need = AAA_BODY if aaa else AA_BODY
            if r < need:
                large_ok = r >= AA_LARGE
                fails.append((theme, t, s, r, "large-text only" if large_ok else "FAILS ALL"))
    return len(texts) * len(surfs), fails, unclassified


def main(path, aaa=False):
    css = pathlib.Path(path).read_text()
    light = block(css, r":root")
    dark, found_dark = dict(light), False
    for pat in (r'\[data-theme=["\']dark["\']\]', r"\.dark",
                r':root:not\(\[data-theme=["\']light["\']\]\)',
                r"prefers-color-scheme:\s*dark[^{]*\{[^{]*:root"):
        d = block(css, pat)
        if d:
            dark.update(d); found_dark = True
            break
    if not light:
        print("no :root block found - is this a token file?", file=sys.stderr)
        return 1
    colors_seen = {k for k in light}

    themes = (("light", light), ("dark", dark)) if found_dark else (("light", light),)
    total, fails, unclassified = 0, [], []
    for name, table in themes:
        n, f, u = check(name, table, aaa)
        total += n
        fails += f
        unclassified = u

    target = "AAA 7.0" if aaa else "AA 4.5"
    scope = "both themes" if found_dark else "light only - NO DARK BLOCK FOUND"

    if total == 0:
        print(f"contrast: NOT RUN - 0 token pairs matched the text/surface name heuristic",
              file=sys.stderr)
        print(f"  tokens seen: {', '.join(sorted(colors_seen)[:12]) or '(none parsed)'}",
              file=sys.stderr)
        print("  Rename to include a role word (text/fg/body/muted vs bg/surface/canvas/card),",
              file=sys.stderr)
        print("  or pass a token file that uses them. A green result here would mean nothing.",
              file=sys.stderr)
        return 2

    if unclassified:
        print(f"contrast: note - {len(unclassified)} token(s) matched neither role and were "
              f"NOT checked: {', '.join(sorted(unclassified)[:8])}")

    if not fails:
        print(f"contrast: {total} token pairs checked, {scope}, 0 below {target}")
        return 0
    print(f"contrast: {len(fails)} of {total} token pairs below {target} ({scope})")
    for theme, t, s, r, note in sorted(fails, key=lambda x: x[3])[:40]:
        print(f"  {theme:5s} {t} on {s}: {r:.2f}:1  ({note})")
    if len(fails) > 40:
        print(f"  ... and {len(fails) - 40} more")
    print("\nA pair that exists in the tokens but is not on screen today will ship unchecked.")
    return 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], "--aaa" in sys.argv))
