#!/usr/bin/env bash
# Fetch and cache the three Google Fonts data files the font search needs.
# Cache: $GFONTS_CACHE, default ~/.cache/gfonts. Re-run to refresh (corpus grows monthly).
#
#   fontdata.sh          fetch if missing
#   fontdata.sh --force  refetch
#
# What each file is, and why it is not the documented API:
#   gfmeta.txt  fonts.google.com/metadata/fonts - KEYLESS, 1946 families, 24 fields
#               including the `popularity` integer rank. The documented
#               googleapis.com/webfonts/v1 endpoint needs a key and carries no
#               popularity, which is the field the whole anti-repetition rule turns on.
#   gftags.csv  google/fonts tags/all/families.csv - 33,755 rows, 1941 families x 74
#               human-scored 0-100 tags, including /Quality/{Concept,Drawing,Spacing,
#               Wordspace}. That is Google's own well-built-vs-filler signal.
#   quant.csv   google/fonts tags/all/quant.csv - measured stroke min/max per family;
#               max/min is stroke contrast.
set -euo pipefail
CACHE="${GFONTS_CACHE:-$HOME/.cache/gfonts}"
mkdir -p "$CACHE"
UA="claude-code-design-skill/1.0"

get() { # url dest
  if [ -s "$2" ] && [ "${1:-}" != "--force" ] && [ -z "${FORCE:-}" ]; then
    echo "  cached  $(basename "$2") ($(du -h "$2" | cut -f1))"; return
  fi
  curl -sfL --max-time 90 -A "$UA" "$1" -o "$2"
  echo "  fetched $(basename "$2") ($(du -h "$2" | cut -f1))"
}

[ "${1:-}" = "--force" ] && export FORCE=1

echo "caching Google Fonts data -> $CACHE"
get "https://fonts.google.com/metadata/fonts" "$CACHE/gfmeta.txt"
get "https://raw.githubusercontent.com/google/fonts/main/tags/all/families.csv" "$CACHE/gftags.csv"
get "https://raw.githubusercontent.com/google/fonts/main/tags/all/quant.csv" "$CACHE/quant.csv"

python3 - "$CACHE" <<'PY'
import json, sys, csv, collections, pathlib
c = pathlib.Path(sys.argv[1])
raw = (c / "gfmeta.txt").read_text()
d = json.loads(raw[raw.index("{"):])
fams = d["familyMetadataList"]
cats = collections.Counter(f.get("category") for f in fams)
rows = sum(1 for _ in csv.reader(open(c / "gftags.csv")))
print(f"  {len(fams)} families  {sum(1 for f in fams if f.get('axes'))} variable  {rows} tag rows")
print(f"  {dict(cats)}")
PY
