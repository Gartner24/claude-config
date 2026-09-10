import json, csv, sys, hashlib, random
from collections import defaultdict

import os
CACHE = os.environ.get('GFONTS_CACHE') or os.path.expanduser('~/.cache/gfonts')
def _c(n):
    p = os.path.join(CACHE, n)
    if not os.path.exists(p):
        sys.exit(f"missing {p}\nrun: bash ~/.claude/skills/design/scripts/fontdata.sh")
    return p

_raw = open(_c('gfmeta.txt')).read()
meta = json.loads(_raw[_raw.index('{'):])
FAM = {f['family']: f for f in meta['familyMetadataList']}
TAGS = defaultdict(dict)
for f, _, t, s in csv.reader(open(_c('gftags.csv'))):
    TAGS[f][t] = float(s)
QUANT = defaultdict(dict)
for r in csv.reader(open(_c('quant.csv'))):
    if len(r) == 4:
        QUANT[r[0]].setdefault(r[2].split('/')[-1], []).append(float(r[3]))

def contrast(fam):
    q = QUANT.get(fam, {})
    lo, hi = q.get('stroke_width_min'), q.get('stroke_width_max')
    if not lo or not hi: return None
    return round(max(hi) / min(lo), 2)

def quality(fam):
    t = TAGS.get(fam, {})
    ks = [t.get(f'/Quality/{k}') for k in ('Concept','Drawing','Spacing','Wordspace')]
    ks = [k for k in ks if k is not None]
    return round(sum(ks)/len(ks), 1) if len(ks) == 4 else None

def search(*, tags=(), anti=(), category=None, min_pop=None, max_pop=None,
           min_quality=70, axes=(), width=None, thickness=None, exclude=(),
           needs_italic=False, min_weights=0, top=10, seed='x'):
    out = []
    for fam, m in FAM.items():
        if fam in exclude or m['isNoto']: continue
        if category and m['category'] not in category: continue
        p = m['popularity']
        if min_pop and p < min_pop: continue          # min_pop=51 excludes the top 50
        if max_pop and p > max_pop: continue
        q = quality(fam)
        if min_quality and (q is None or q < min_quality): continue
        have = {a['tag'] for a in m['axes']}
        if any(a not in have for a in axes): continue
        # NOTE: thickness/slant/width are populated for STATIC families only.
        # Variable families carry null there - use the wdth/wght axis range instead.
        insts = [v for v in m['fonts'].values() if v['width'] is not None]
        bonus = 0
        wd_ax = [a for a in m['axes'] if a['tag'] == 'wdth']
        if width:
            if insts and any(width[0] <= v['width'] <= width[1] for v in insts): bonus += 12
            elif wd_ax and wd_ax[0]['min'] <= 87.5 and width[0] <= 4: bonus += 12
        if thickness:
            wg = [a for a in m['axes'] if a['tag'] == 'wght']
            if insts and any(thickness[0] <= v['thickness'] <= thickness[1] for v in insts): bonus += 12
            elif wg and wg[0]['max'] >= 800 and thickness[1] >= 8: bonus += 12
        if needs_italic and not any(k.endswith('i') for k in m['fonts']): continue
        if len({k.rstrip('i') for k in m['fonts']}) < min_weights and 'wght' not in have: continue
        t = TAGS.get(fam, {})
        pos = [t.get(k, 0) for k in tags]
        if tags and max(pos) < 50: continue   # at least one adjective must land hard
        if tags and min(pos) < 10: continue   # and none may be actively ABSENT. Not "quiet" -
                                              # a >=25 gate here collapses a 189-family pool to 4.
        neg = max([t.get(k, 0) for k in anti], default=0)
        if neg >= 50: continue                          # anti-adjective veto
        score = (sum(pos)/len(pos) if pos else 0) - neg*0.5 + min(q-70, 15) + bonus
        out.append((round(score,1), fam, p, q, contrast(fam), sorted(have)))
    out.sort(reverse=True)
    # collapse near-duplicate siblings (Bitcount Grid Double Ink / Bitcount Prop Single / ...)
    seen, dedup = set(), []
    for row in out:
        stem = row[1].split()[0]
        if stem in seen: continue
        seen.add(stem); dedup.append(row)
    # Everything in `dedup` already passed every hard gate, so any of them is a legitimate
    # answer. Ranking then always taking the head is what made every project look the same.
    # Sample the qualifying band with a per-client seed instead: same quality bar, different
    # outcome per client, reproducible for a given seed.
    band = dedup[:max(top * 4, 24)]
    rng = random.Random(hashlib.sha256(seed.encode()).hexdigest())
    rng.shuffle(band)
    return sorted(band[:top], reverse=True)

def show(title, rows):
    print(f'\n### {title}')
    print(f"{'family':28s} {'pop':>5s} {'qual':>5s} {'contr':>6s}  axes")
    for s, fam, p, q, c, ax in rows:
        print(f"{fam:28s} {p:5d} {q:5.1f} {str(c):>6s}  {','.join(ax) or '-'}")


# ---------------------------------------------------------------------------
def _tags_for(words):
    """Map plain brief adjectives onto the /Expressive/* tag names that exist."""
    avail = {t.split('/')[-1].lower(): t for fam in TAGS for t in TAGS[fam]}
    out = []
    for w in words:
        t = avail.get(w.strip().lower())
        if t:
            out.append(t)
        else:
            print(f"  note: no tag '{w}' - ignored. try: "
                  f"{', '.join(sorted(k for k in avail if k.startswith(w[:2].lower()))[:6])}",
                  file=sys.stderr)
    return tuple(out)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(
        description="Search the whole Google Fonts corpus by brief, not by lookup table.",
        epilog="e.g. fontsearch.py --adjectives loud active --anti calm "
               "--category Display --seed acme-2026")
    ap.add_argument('--adjectives', nargs='+', default=[], help='brief adjectives')
    ap.add_argument('--anti', nargs='+', default=[], help='anti-adjective(s) - hard veto')
    ap.add_argument('--category', nargs='+',
                    default=None, help='Display | Serif | "Sans Serif" | Monospace | Handwriting')
    ap.add_argument('--min-pop', type=int, default=300,
                    help='popularity floor. 300 excludes Inter(5) Roboto(2) Poppins(8) '
                         'Montserrat(7) Playfair(25) by construction. Default 300.')
    ap.add_argument('--min-quality', type=float, default=72,
                    help="Google's own /Quality mean, 0-100. Default 72.")
    ap.add_argument('--seed', default='default',
                    help='per-client seed. Same brief + different seed = different shortlist.')
    ap.add_argument('--top', type=int, default=8)
    ap.add_argument('--list-tags', action='store_true')
    a = ap.parse_args()

    if a.list_tags:
        for t in sorted({t for fam in TAGS for t in TAGS[fam]}):
            print(t)
        sys.exit(0)

    rows = search(tags=_tags_for(a.adjectives), anti=_tags_for(a.anti),
                  category=tuple(a.category) if a.category else None,
                  min_pop=a.min_pop, min_quality=a.min_quality,
                  top=a.top, seed=a.seed)
    if not rows:
        sys.exit("no families passed. Loosen --min-quality, lower --min-pop, "
                 "or drop an adjective - do NOT fall back to a default face.")
    show(f"{' + '.join(a.adjectives) or 'any'}  (seed {a.seed}, pop>={a.min_pop})", rows)
