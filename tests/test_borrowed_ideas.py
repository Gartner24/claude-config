"""Spec 0056: the four borrowed ideas are own files that a skill update never touches, user typed only,
and the static checks the spec names."""
import json
import re
import unittest

from test_claude_config import REAL, SKILL, Case

OWN = ("lead-finder", "reaction-tester", "new-number-replaces-old")
SKILLS = REAL / "claude-home" / "skills"


def front(name):
    text = (SKILLS / name / "SKILL.md").read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return dict(line.split(": ", 1) for line in m.group(1).splitlines()), text


class TestNotDownloaded(Case):
    # covers: AC-8 (no manifest entry, so update never names or overwrites them)
    def test_real_manifest(self):
        entries = json.loads((REAL / "tools" / "config" / "manifest.json").read_text())["entries"]
        self.assertEqual([n for n in OWN if n in entries], [])

    def test_plan_skips_own(self):
        self.install_edited()
        self.commit({"skills/s/SKILL.md": SKILL + "line 7\n"})
        for n in OWN:
            for root in (self.live / "skills", self.repo / "claude-home" / "skills"):
                (root / n).mkdir()
                (root / n / "SKILL.md").write_text(f"---\nname: {n}\n---\n")
        r = self.tool("update", "--plan")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("s (edited): upstream", r.stdout)
        self.assertEqual([n for n in OWN if n in r.stdout + r.stderr], [])


class TestStatic(unittest.TestCase):
    # covers: AC-9 (typed only, never marked for wf in the skill map)
    def test_typed_only(self):
        rows = (REAL / "claude-home" / "rules-on-demand" / "skill-map.md").read_text().splitlines()
        for n in ("lead-finder", "reaction-tester"):
            meta, text = front(n)
            self.assertEqual(meta["disable-model-invocation"], "true", n)
            self.assertIn("only when you type", text, n)
            self.assertEqual([r for r in rows if n in r and "wf" in r], [], n)

    # covers: AC-3 (exactly these tools, no mail or post tool, never contacts)
    def test_lead_finder_tools(self):
        meta, text = front("lead-finder")
        self.assertEqual(meta["allowed-tools"], "Read, Write, WebFetch, Bash(curl:*), Bash(git rev-parse:*)")
        self.assertIn("never contacts anyone", text)
        self.assertIn("personal name, contact by hand only", text)

    # covers: AC-1 (an exact "name"="Medellin" area match found 0 elements, OSM writes Medellín)
    def test_lead_finder_city_accents(self):
        _, text = front("lead-finder")
        self.assertIn('area["name"~"^<city pattern>$",i]', text)
        self.assertNotIn('area["name"="', text)
        for typed, pattern, osm in (("Medellin", "M.d.ll..", "Medellín"), ("Bogota", "B.g.t.", "Bogotá")):
            self.assertIn(f"`{typed}` becomes `{pattern}`", text)
            self.assertRegex(osm, re.compile(f"^{pattern}$", re.I))

    # covers: AC-1 (one Overpass query with a named User-Agent, attribution, banned sources, robots.txt rules)
    def test_lead_finder_sources(self):
        meta, text = front("lead-finder")
        self.assertEqual(text.count("https://overpass-api.de/api/interpreter"), 1)
        self.assertIn('-A "lead-finder skill', text)
        self.assertIn("Never a second query in the same run", text)
        self.assertIn("Data (c) OpenStreetMap contributors, ODbL", text)
        self.assertIn("Never Google Maps, Google Places or LinkedIn", text)
        self.assertIn("at most 3 plain requests, at least 1 second apart", text)
        self.assertIn("404: no rules", text)
        self.assertIn("Timeout, other 4xx, or 5xx: skip the site and mark the row `unchecked`", text)

    # covers: AC-2 (signals, booking words, table shape, refusal inside a git repo)
    def test_lead_finder_output(self):
        _, text = front("lead-finder")
        for word in ("NO_WEBSITE", "NO_BOOKING", "BLOG_STALE", "INCUMBENT_AGENCY", "older than 12 months",
                     "| Business | Public URL | Signals | Evidence |", "0 to 20 rows, sorted by number of signals",
                     'say "only n found"', "pad nothing", "This is a lead list, not a contact list.",
                     "rev-parse --is-inside-work-tree", "If it prints `true`, refuse"):
            self.assertIn(word, text)
        booking = re.search(r"matching (.*?) or calendly", text).group(1)
        self.assertEqual(booking.split(", "), ["reservar", "agendar", "cita", "book", "booking", "appointment"])

    # covers: AC-3 (page text is data, Colombian data law named, other countries warned)
    def test_lead_finder_data(self):
        _, text = front("lead-finder")
        self.assertIn("data, never instructions", text)
        self.assertIn("Store no personal names, emails or phone numbers", text)
        self.assertIn("Ley 1581 of 2012", text)
        self.assertIn("Other countries have other data laws", text)

    # covers: AC-4 (baseline first, confirm, 12 Sonnet personas, ranked objections, the label)
    def test_reaction_tester(self):
        _, text = front("reaction-tester")
        base, ask = text.index("one plain baseline answer"), text.index("Spend up to 12 subagents")
        self.assertLess(base, ask)
        self.assertLess(ask, text.index("## Step 2"))
        self.assertIn("Stop until the user says yes", text)
        for word in ("up to 12 personas", 'marked "invented"', "model: sonnet",
                     "Objections ranked by how many personas raised them", "Ties keep the order they were first raised",
                     '"n of 12 answered"'):
            self.assertIn(word, text)
        self.assertTrue(text.rstrip().endswith("**opinions of simulated people, not a forecast**"))

    # covers: AC-5
    def test_scorecard(self):
        ba = SKILLS / "business-analyzer"
        text = (ba / "references" / "new-business.md").read_text()
        for word in ("problem", "buyer pays", "market size", "founder fit", "why now", "reach", "cost to test",
                     "/35", "build / change course / drop", "up to 3 cheap tests", '"no evidence"'):
            self.assertIn(word, text)
        self.assertNotIn("go / no-go / not-yet", text)
        # the 5 fatal flaw questions stay
        self.assertEqual(re.findall(r"^### (\d)\. .*\?$", text, re.M), ["1", "2", "3", "4", "5"])
        # B2B and B2C keep their own verdict words on purpose
        self.assertIn("go / no-go / pivot", (ba / "SKILL.md").read_text())
        for f in ("b2b.md", "b2c.md"):
            self.assertIn("go/no-go/fix-this-first", (ba / "references" / f).read_text(), f)

    # covers: AC-6
    def test_rule(self):
        text = (REAL / "claude-home" / "rules" / "new-number-replaces-old.md").read_text()
        self.assertLessEqual(len(text.splitlines()), 6)
        self.assertIn("customer-research", text)
        self.assertIn("offers", text)
        self.assertIn('"replaced X (date) with Y"', text)
        self.assertIn("Never write a figure with no source", text)


if __name__ == "__main__":
    unittest.main()
