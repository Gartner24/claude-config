#!/usr/bin/env python3
"""flash-check.py LUMA.txt: counts big frame-to-frame luma jumps from an ffmpeg signalstats dump (see qa-checklist.md step 6).
Flags 1-s windows with more than 6 jumps (> 3 flashes per second). Written for the instagram-reels-design skill."""
import re, sys
t, y = [], []
for line in open(sys.argv[1]):
    m = re.search(r"pts_time:([\d.]+)", line)
    if m: t.append(float(m.group(1)))
    m = re.search(r"YAVG=([\d.]+)", line)
    if m: y.append(float(m.group(1)))
jumps = [t[i] for i in range(1, len(y)) if abs(y[i] - y[i-1]) >= 25]
bad = sorted({round(a, 2) for a in jumps if sum(1 for b in jumps if a <= b < a + 1.0) > 6})
print("luma jumps >= 25/255:", len(jumps), "| 1-s windows with > 6 jumps (> 3 flashes):", bad[:20] or "none")
