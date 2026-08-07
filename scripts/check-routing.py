#!/usr/bin/env python3
"""Regression check for USAGE.md skill routing.

Simulates the intent-router's documented algorithm (skills/intent-router/SKILL.md step 3):
    score = (count of TRIGGERS substrings present in prompt, case-insensitive) x PRIORITY
    discard score < 3

Three checks:
  1. overlap   - a trigger that contains another trigger in the same block double-counts,
                 inflating that block's score. The longer one is always redundant.
  2. self-route- every block's own EXAMPLE should route back to that block.
  3. canonical - hand-picked prompts must reach a specific skill.

Run after editing USAGE.md:  python3 scripts/check-routing.py
Exit 0 = no regressions. SELF_ROUTE_BASELINE is the known pre-existing failure count;
lower it as those get fixed, never raise it.
"""
import re
import sys
import pathlib

USAGE = pathlib.Path(__file__).resolve().parent.parent / "USAGE.md"
SELF_ROUTE_BASELINE = 0

# (prompt, substring that must appear in the winning block's name)
CANONICAL = [
    ("animate this SVG logo so the paths draw in on load", "animate"),
    ("pin the hero and scrub this timeline as the user scrolls", "gsap"),
    ("make the modal open smoothly and the accordion expand", "transitions-dev"),
    ("the bottom sheet should be draggable and feel like iOS", "apple-design"),
    ("make our pricing page look like this screenshot", "design-dna"),
    ("load this GLTF model and add bloom postprocessing", "threejs"),
    ("write the commit message for these changes", "/write"),
    ("this reads like chatgpt, polish it", "/polish"),
    ("write the methodology section for my thesis in APA", "/academic"),
    ("I need a thesis topic, the field is open", "project-finder"),
    ("audit the motion across this app", "review-animations"),
    # Substring-collision guards. A trigger is matched as a plain substring, so a short
    # trigger can hide inside an unrelated word. Each of these was a real bug:
    #   'cro'      inside 'across' / 'microservices'
    #   'go build' inside 'cargo build'
    # If you add a short trigger, add a case here proving it does not misfire.
    ("coordinate a change across the api, worker, and frontend services", "multi-workflow"),
    ("should I use microservices or a monolith", "council"),
    ("cargo build fails with a borrow checker error", "rust-build"),
    ("make this landing page feel high-end and expensive, like Linear", "high-end-visual-design"),
]


def parse(text):
    blocks = []
    for blk in re.split(r"\n### ", text)[1:]:
        name = blk.split("\n")[0].strip()
        tr = re.search(r"^TRIGGERS: (.+)$", blk, re.M)
        pr = re.search(r"^PRIORITY: (\d+)", blk, re.M)
        ex = re.search(r'^EXAMPLE: "(.+)"$', blk, re.M)
        if tr and pr:
            trigs = [x.strip().lower() for x in tr.group(1).split(",") if x.strip()]
            blocks.append((name, trigs, int(pr.group(1)), ex.group(1) if ex else None))
    return blocks


def rank(prompt, blocks):
    p = prompt.lower()
    scored = ((sum(1 for t in trigs if t in p) * prio, name) for name, trigs, prio, _ in blocks)
    return sorted([s for s in scored if s[0] >= 3], reverse=True)


def main():
    blocks = parse(USAGE.read_text())
    fails = []

    overlaps = [
        (name, a, b)
        for name, trigs, _, _ in blocks
        for a in trigs
        for b in trigs
        if a != b and a in b
    ]
    for name, short, long in overlaps:
        fails.append(f"overlap    {name}: '{long}' is redundant ('{short}' already matches it)")

    misrouted = 0
    for name, _, _, ex in blocks:
        if not ex:
            continue
        r = rank(ex, blocks)
        if not r or r[0][1] != name:
            misrouted += 1
    if misrouted > SELF_ROUTE_BASELINE:
        fails.append(
            f"self-route {misrouted} blocks do not route to their own EXAMPLE "
            f"(baseline {SELF_ROUTE_BASELINE}) - you made routing worse"
        )

    for prompt, expect in CANONICAL:
        r = rank(prompt, blocks)
        if expect is None:
            if r:
                fails.append(f"canonical  expected NOTHING to route, got {r[0]} for {prompt!r}")
        elif not r:
            fails.append(f"canonical  nothing routed for {prompt!r} (wanted {expect})")
        elif expect.lower() not in r[0][1].lower():
            fails.append(f"canonical  got {r[0][1]!r}, wanted {expect!r} for {prompt!r}")

    print(f"{len(blocks)} routable blocks | self-route failures: {misrouted} (baseline {SELF_ROUTE_BASELINE})")
    if fails:
        print(f"\n{len(fails)} problem(s):")
        for f in fails:
            print("  " + f)
        return 1
    print("routing OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
