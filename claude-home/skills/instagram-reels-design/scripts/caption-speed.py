#!/usr/bin/env python3
"""caption-speed.py CAPTIONS.srt: words per second for every caption cue (see qa-checklist.md step 4).
Flags cues over 3.0 w/s. Written for the instagram-reels-design skill."""
import re, sys
txt = open(sys.argv[1], encoding="utf-8-sig").read()
ts = lambda s: sum(float(x) * m for x, m in zip(s.replace(",", ".").split(":"), (3600, 60, 1)))
for blk in re.split(r"\n\s*\n", txt.strip()):
    lines = blk.strip().splitlines()
    m = next((re.match(r"(\S+) --> (\S+)", l) for l in lines if "-->" in l), None)
    if not m: continue
    words = " ".join(l for l in lines if "-->" not in l and not l.strip().isdigit()).split()
    d = ts(m.group(2)) - ts(m.group(1)); wps = len(words) / d if d else 99
    flag = "  <-- too fast" if wps > 3.0 else ""
    print("%s  %.2f s  %d words  %.1f w/s%s  %s" % (m.group(1), d, len(words), wps, flag, " ".join(words)[:60]))
