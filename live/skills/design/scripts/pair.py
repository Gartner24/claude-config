import json, subprocess
from fontsearch import search, show, FAM, TAGS, quality
from enrich import metrics

def width_ratio(m):
    return round(m['n_advance_em'] / m['x_height_em'], 3) if m.get('n_advance_em') and m.get('x_height_em') else None

def body_candidates(display_m, seed='x', used=(), top=6):
    """Mechanical pairing: neutral workhorse, x-height within 8% of display,
       structurally different, real weight range, italic present."""
    pool = search(tags=['/Expressive/Calm', '/Expressive/Business'],
                  anti=['/Expressive/Loud', '/Expressive/Fancy', '/Expressive/Childlike',
                        '/Expressive/Awkward', '/Expressive/Artistic'],
                  category=['Sans Serif', 'Serif'], min_pop=40, min_quality=74,
                  axes=['wght'], needs_italic=True, exclude=used, seed=seed, top=40)
    out = []
    for score, fam, pop, q, contr, axes in pool:
        m = metrics(fam)
        if not m or not m['x_height_em']: continue
        dx = abs(m['x_height_em'] - display_m['x_height_em']) / display_m['x_height_em']
        if dx > 0.08: continue                                  # x-height match gate
        same_cat = FAM[fam]['category'] == FAM[display_m['family']]['category']
        wr = width_ratio(m)
        out.append((round(dx, 3), fam, m['x_height_em'], wr, m['glyphs'], m['tnum'], same_cat))
    out.sort()
    return out[:top]


if __name__ == '__main__':
    import argparse, sys
    ap = argparse.ArgumentParser(
        description="Pick a body face to pair with a chosen display face, by measurement.",
        epilog="e.g. pair.py 'Libre Bodoni' --seed acme-2026")
    ap.add_argument('display', help='the display face already chosen')
    ap.add_argument('--seed', default='default',
                    help='per-client seed, so two clients do not get the same body face')
    ap.add_argument('--top', type=int, default=6)
    ap.add_argument('--used', nargs='*', default=[],
                    help='faces already used on other projects, to exclude')
    a = ap.parse_args()

    dm = metrics(a.display)
    if not dm:
        sys.exit(f"{a.display}: not found in the Google corpus, or its TTF could not be read.\n"
                 f"Check the exact family name with:\n"
                 f"  python3 ~/.claude/skills/design/scripts/fontsearch.py --adjectives <x> --top 20")
    if not dm.get('x_height_em'):
        sys.exit(f"{a.display}: no x-height could be measured, so no pairing can be made.")

    rows = body_candidates(dm, seed=a.seed, used=tuple(a.used), top=a.top)
    if not rows:
        sys.exit(f"no body face within 8 percent x-height of {a.display} "
                 f"(x-height {dm['x_height_em']}). Widen the gate or pick another display face.\n"
                 f"Do NOT fall back to a default body face - that is the behaviour this replaces.")

    print(f"\n### body faces for {a.display}  (x-height {dm['x_height_em']}, seed {a.seed})")
    print(f"{'family':26s} {'dx':>6s} {'x-ht':>6s} {'width':>6s} {'glyphs':>7s} {'tnum':>5s}  same-cat")
    for dx, fam, xh, wr, glyphs, tnum, same in rows:
        print(f"{fam:26s} {dx:6.3f} {xh:6.3f} {str(wr):>6s} {glyphs:7d} {str(tnum):>5s}  {same}")
    print("\nPrefer a different category to the display face (same-cat False). A body face that is"
          "\nclose but not identical to the display is the pairing that fails.")
