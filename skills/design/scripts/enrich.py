import io, json, subprocess, sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

def gf_dir(family):
    return family.lower().replace(' ', '').replace('-', '')

def fetch(family):
    """Grab the family's default TTF straight out of google/fonts. No API key."""
    slug = gf_dir(family)
    for lic in ('ofl', 'apache', 'ufl'):
        url = f'https://api.github.com/repos/google/fonts/contents/{lic}/{slug}'
        r = subprocess.run(['curl','-s','-m','20',url], capture_output=True, text=True)
        try: files = json.loads(r.stdout)
        except Exception: continue
        if not isinstance(files, list): continue
        ttfs = [f for f in files if f['name'].endswith('.ttf')]
        if not ttfs: continue
        vf = [f for f in ttfs if '[' in f['name']]
        pick = (vf or sorted(ttfs, key=lambda f: len(f['name'])))[0]
        b = subprocess.run(['curl','-sL','-m','30',pick['download_url']], capture_output=True)
        return TTFont(io.BytesIO(b.stdout)), pick['name'], lic
    return None, None, None

def metrics(family):
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
      'axes': [(a.axisTag, a.minValue, a.maxValue) for a in f['fvar'].axes] if 'fvar' in f else [],
      'tnum': 'tnum' in feats, 'onum': 'onum' in feats, 'smcp': 'smcp' in feats,
      'kern': 'kern' in feats or 'kern' in f,
      'features': feats,
    }

if __name__ == '__main__':
    for fam in sys.argv[1:]:
        m = metrics(fam)
        print(json.dumps(m) if m else f'{fam}: NOT FOUND')
