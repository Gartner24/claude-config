import io, json, os, re, subprocess, sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

CACHE = os.environ.get('GFONTS_CACHE') or os.path.expanduser('~/.cache/gfonts')
MCACHE = os.path.join(CACHE, 'metrics')
# Bump when the shape or provenance of a cached record changes. Entries written by an
# older version are ignored rather than served - a cache that outlives its schema hands
# back confidently wrong data, which is worse than a slow re-measure.
MCACHE_V = 2

def gf_dir(family):
    return family.lower().replace(' ', '').replace('-', '')

_META = None

def _axes_from_metadata(family):
    """Variable-font axes for a family, from the cached corpus metadata."""
    global _META
    if _META is None:
        try:
            raw = open(os.path.join(CACHE, 'gfmeta.txt')).read()
            _META = {f['family']: f for f in json.loads(raw[raw.index('{'):])['familyMetadataList']}
        except Exception:
            _META = {}
    f = _META.get(family) or {}
    return [(a['tag'], a['min'], a['max']) for a in f.get('axes', [])]


def fetch(family):
    """Get the family's default TTF.

    Primary source is the Google Fonts CSS API, which hands back a direct
    fonts.gstatic.com URL and is NOT on GitHub's 60-per-hour unauthenticated API
    budget. The previous version listed the google/fonts repo through
    api.github.com, three licence directories per family - so a single pair.py run
    over 40 candidates could issue ~120 calls against that 60/hr limit, and the
    failure was silent: metrics() returned None and the family was dropped from the
    shortlist without a word.
    """
    fam = family.replace(' ', '+')
    # An old UA makes the CSS API serve TTF rather than woff2, which fontTools reads
    # without brotli.
    r = subprocess.run(['curl', '-s', '-m', '20', '-A', 'Mozilla/4.0',
                        f'https://fonts.googleapis.com/css2?family={fam}'],
                       capture_output=True, text=True)
    m = re.search(r'url\((https://fonts\.gstatic\.com/[^)]+\.ttf)\)', r.stdout or '')
    if m:
        b = subprocess.run(['curl', '-sL', '-m', '30', m.group(1)], capture_output=True)
        if b.stdout[:4] in (b'\x00\x01\x00\x00', b'true', b'ttcf', b'OTTO'):
            return TTFont(io.BytesIO(b.stdout)), m.group(1).rsplit('/', 1)[-1], 'gstatic'

    # Fallback: the repo listing. Authenticated when `gh` is logged in (5000/hr),
    # otherwise the old 60/hr path - reached only for families the CSS API does not serve.
    tok = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
    hdr = ['-H', f'Authorization: Bearer {tok.stdout.strip()}'] if tok.returncode == 0 and tok.stdout.strip() else []
    slug = gf_dir(family)
    for lic in ('ofl', 'apache', 'ufl'):
        url = f'https://api.github.com/repos/google/fonts/contents/{lic}/{slug}'
        r = subprocess.run(['curl', '-s', '-m', '20', *hdr, url], capture_output=True, text=True)
        try: files = json.loads(r.stdout)
        except Exception: continue
        if not isinstance(files, list): continue
        ttfs = [f for f in files if f['name'].endswith('.ttf')]
        if not ttfs: continue
        vf = [f for f in ttfs if '[' in f['name']]
        pick = (vf or sorted(ttfs, key=lambda f: len(f['name'])))[0]
        b = subprocess.run(['curl', '-sL', '-m', '30', pick['download_url']], capture_output=True)
        return TTFont(io.BytesIO(b.stdout)), pick['name'], lic
    return None, None, None

def metrics(family, use_cache=True):
    """Measured metrics for one family. Cached on disk: pair.py asks for up to 40
    families per run, and the numbers do not change between runs."""
    cpath = os.path.join(MCACHE, gf_dir(family) + '.json')
    if use_cache and os.path.exists(cpath):
        try:
            with open(cpath) as fh: c = json.load(fh)
            if c.get('_v') == MCACHE_V:
                return c
        except Exception:
            pass
    m = _measure(family)
    if m is not None:
        m['_v'] = MCACHE_V
    if m is not None and use_cache:
        os.makedirs(MCACHE, exist_ok=True)
        try:
            with open(cpath, 'w') as fh: json.dump(m, fh)
        except OSError:
            pass
    return m

def _measure(family):
    f, name, lic = fetch(family)
    if f is None: return None
    os2, head = f['OS/2'], f['head']
    upm = head.unitsPerEm
    gs = f.getGlyphSet()
    def adv(g):
        try: return gs[g].width / upm
        except KeyError: return None
    feats = sorted({r.FeatureTag for r in f['GSUB'].table.FeatureList.FeatureRecord}) if 'GSUB' in f else []
    xh = os2.sxHeight / upm if getattr(os2, 'sxHeight', None) else None
    cap = os2.sCapHeight / upm if getattr(os2, 'sCapHeight', None) else None
    return {
      'family': family, 'file': name, 'license_dir': lic,
      'x_height_em': round(xh, 4) if xh else None,
      'cap_height_em': round(cap, 4) if cap else None,
      'x_over_cap': round(xh / cap, 3) if xh and cap else None,
      'width_class': os2.usWidthClass,
      'n_advance_em': round(adv('n'), 4) if adv('n') else None,
      'glyphs': len(f.getGlyphOrder()),
      # The CSS API serves the STATIC Regular, which carries no fvar - so axes come from
      # the cached family metadata, which is authoritative for the family and was already
      # being fetched. Reading them off whichever binary happened to be in the repo (the
      # old path) was never better, and this way a static-only fetch still reports them.
      'axes': _axes_from_metadata(family),
      'tnum': 'tnum' in feats, 'onum': 'onum' in feats, 'smcp': 'smcp' in feats,
      'kern': 'kern' in feats or 'kern' in f,
      'features': feats,
    }

if __name__ == '__main__':
    for fam in sys.argv[1:]:
        m = metrics(fam)
        print(json.dumps(m) if m else f'{fam}: NOT FOUND')
