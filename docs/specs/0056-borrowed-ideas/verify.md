# Verify: ideas borrowed from tools we skip · spec 0056

First `/check verify` run, 2026-10-17, on branch `feat/0056-ideas-borrowed-from-tools-we-skip` (commit aba3dc2). Verdict: FAIL (one bug, AC-1).

## Commands
- [x] `python3 -B -m unittest discover -s runner/tests -p test_borrowed_ideas.py -v` -> 6 tests OK, including `claude-config update --plan` on a fixture with all three own names present in both skill trees: the plan names only `s (edited)`, none of the three -> AC-8. can fail: `update --plan` walks `claude-home/skills/` instead of the manifest, or a manifest entry is added for one of them.
- [x] Repo refusal check of lead-finder step 1: `git -C <repo>/docs rev-parse --is-inside-work-tree` printed `true` (refuse), `git -C ~/Documents rev-parse --is-inside-work-tree` exited 128 "not a git repository" (go on) -> AC-2. can fail: the command answers `true` outside a repo, or errors inside one, so the refusal flips.
- [x] The skill's Overpass query, city Medellin with the accent on the i (as OSM writes it), `shop=hairdresser`: HTTP 200, 123 elements (111 nodes, 11 ways, 1 relation), way centers at lat 6.2, lon -75.6 (Colombia), 3 with a website tag -> AC-1 query syntax and User-Agent. can fail: a bad Overpass QL line returns 400 and no elements.
- [x] (fixed, see run 2) The same query with the skill's own example spelling `Medellin` (no accent): HTTP 200, **0 elements** -> AC-1 FAIL. OSM names the area with the accent on the i, and `area["name"="<city>"]` matches exactly. A user who types the city without accents (the skill's example `Medellin peluqueria`, and Bogota, Cucuta, Ibague the same way) gets an empty list, and the one query per run rule leaves no retry. Fix in `/debug`: match the name accent and case tolerant (for example a regex with both letters, `[ii]` written as the plain and the accented i), or tell the skill to write the city's official OSM name with accents before the query.
- [x] robots.txt command `curl -sS -m 15 -A "lead-finder skill" -o - -w '\n%{http_code}' https://example.com/robots.txt` -> body then `404` on the last line, so the 404 rule can be read from the output -> AC-1. can fail: the `-w` status line missing, so a 404 and a 5xx look the same.
- [x] Paced home and sitemap fetch `curl ... --rate 1/s https://example.com/ -o home.html https://example.com/sitemap.xml -o sitemap.xml`: curl 8.23 accepts `--rate`, both files written (200, 404), wall time 1.08 s for two requests of about 0.08 s each, so they were spaced 1 second apart -> AC-1. can fail: curl without `--rate` (before 7.84) errors, or the two requests run back to back in about 0.2 s.
- [x] `grep` of `business-analyzer/SKILL.md:12`, `b2b.md:81`, `b2c.md:69`: still "go / no-go / pivot" and "go/no-go/fix-this-first" -> AC-5 keeps B2B and B2C verdict words. can fail: the scorecard edit spread to those files.
- [x] `python3 -B -m unittest discover -s runner/tests -p test_layout.py` -> OK, so `docs/guides/SKILLS.md` lists both new skills and is fresh. can fail: SKILLS.md not regenerated after the new front matter.
- [x] `python3 runner/tests/fast.py` -> 978 tests, 0 failed.

## /debug 2026-10-17: AC-1 accent fix
- Root cause: `area["name"="<city>"]` is an exact match and OSM writes the accented name. Fix: `area["name"~"^<city pattern>$",i]`, every vowel and n replaced by `.` (Overpass regex matches one UTF-8 letter per `.`).
- Probe: `area["name"~"^M.d.ll.n$",i]["boundary"="administrative"];out tags;` -> 3 areas named with the accent (Colombia, Spain, Mexico). Full skill query with `^M.d.ll..$` and `shop=hairdresser`, `out count` -> 123 total (111 nodes, 11 ways, 1 relation), the same as the accented exact query above. can fail: Overpass treats `.` as one byte, so the accented letter (two bytes) does not match and the count is 0.
- Test `test_lead_finder_city_accents` in `runner/tests/test_borrowed_ideas.py`; mutant (query back to `area["name"="<city>"]`) went red, restored green. Fast suite 979 tests, 0 failed.
- Not fixed, same query: the name match is not limited to Colombia, so Medellin also matches the Spanish and Mexican areas (they added no hairdressers here, but another city or trade could mix countries). That was true of the exact match too.

## Second `/check verify` run, 2026-10-17, commit 8749283: PASS
- [x] `python3 -B -m unittest discover -s runner/tests -p test_borrowed_ideas.py -v` -> 7 tests OK (adds `test_lead_finder_city_accents`) -> AC-1, AC-8. can fail: the skill query goes back to the exact `area["name"="<city>"]`, or a manifest entry names one of the three.
- [x] The skill's query as written now, city typed without accents (`^M.d.ll..$`), `shop=hairdresser`, `out count` against `https://overpass-api.de/api/interpreter` -> HTTP 200, total 123 (111 nodes, 11 ways, 1 relation), the same as the accented exact query in run 1, where the unaccented exact query gave 0 -> AC-1 met. The public server was busy (502, 504, two proxy 502s) and answered on the fifth try after 120 s of backoff. can fail: the pattern does not cover the accented i, so the count is 0.
- [x] `python3 runner/tests/fast.py` -> 979 tests, 0 failed.
- The other run 1 steps cover files the fix did not touch (the fix commit changed only the query lines of `lead-finder/SKILL.md`, this file and the test), so their results stand.

## Static checks the spec names (not counted as can fail steps)
- AC-3: `allowed-tools` is exactly `Read, Write, WebFetch, Bash(curl:*), Bash(git rev-parse:*)`; "never contacts anyone", "personal name, contact by hand only", page text as data, Ley 1581 and other countries' laws are in `lead-finder/SKILL.md`.
- AC-2: table columns, the four signals, the seven booking words, "only n found", "a lead list, not a contact list" are in the skill text.
- AC-4: baseline first, confirm before spending, up to 12 personas, "invented", `model: sonnet`, ranked objections with first raised ties, "n of 12 answered", the label word for word, in `reaction-tester/SKILL.md`.
- AC-5: seven dimension names, "/35", "build / change course / drop", up to 3 cheap tests, 5 fatal flaw questions kept, in `new-business.md`.
- AC-6: rule file is 5 lines, names customer-research and offers, says "replaced X (date) with Y" and the bracket placeholder.
- AC-9: both skills set `disable-model-invocation: true`, say "Runs only when you type", and `skill-map.md` has no row for them.

These are text checks; how a model follows the text is proved only by real use, which is the AC-7 box.

## Left to later boxes
- AC-7 real use of each part: left to the box: Use each of the four once on a real case, write it in verify notes (AC-7)
- Skills linked and rule copied live: left to the box: Link the two skills and copy the rule live after the merge: `bin/install.sh`

## Not this feature
- `python3 scripts/asciify.py --check` exits 1 on `docs/research/tool-review-2026-10/63a-harvey.md` (U+00F3), from commit 4446741 (PR #19), already on main.
- `python3 scripts/private-names.py check` lists only sandbox unreadable dotfiles (known sandbox mount), no hits.

## Acceptance criteria coverage
- AC-1 met (run 2, after the accent fix) · AC-2 met · AC-3 met (static) · AC-4 met (static) · AC-5 met · AC-6 met (static) · AC-7 left to its box · AC-8 met · AC-9 met (static)
# Spec 0056 AC-7 verify notes (run 2026-10-18)

Skills were read from the feature worktree /home/santiago/.local/share/wf-trees/claude-config-5f0728/feat-0056-ideas-borrowed-from-tools-we-skip/claude-home/ (not yet installed to ~/.claude; the install box waits on the owner). Nothing was written inside any repo. Scratch: /tmp/claude-1000/-home-santiago--claude/7692240f-4247-4b06-ac42-86d1193f0505/scratchpad/p0056/

- [x] **B10 lead finder** (steps followed by hand from SKILL.md; the slash command is not installed yet)
  - Case: `Medellin peluqueria`, output /tmp/.../p0056/lead-list.md.
  - Commands: `git -C <out dir> rev-parse --is-inside-work-tree` (not a git repository, so allowed); one Overpass `curl` with `[name]~"^M.d.ll..$"` and `shop=hairdresser`; robots.txt then home + sitemap via `curl --rate 1/s` for one site.
  - Result: first run got HTTP 502 "at capacity" from Overpass (failure path: skill says go on without OSM). A second, separate run returned 200 with 123 elements; 3 had a website tag. The accent-proof city pattern matched Medellin. The 20-row table was written: 20 x NO_WEBSITE, each citing an OSM object URL, 3 rows marked `personal name, contact by hand only`, no phone/email stored. Own-domain check: London City (barberlondoncity.com) robots.txt 200, allows `*`; home page has booking words, 2023 copyright, no agency credit, sitemap index has no lastmod, so 0 signals. Gente Actual: domain did not resolve, `unchecked`. Tribute Barberia: website tag is instagram.com (social network), not read.
  - Findings: (1) public Overpass can 502, and "one query per run" means a retry is a new run; (2) BLOG_STALE cannot be decided from a WordPress sitemap index (lastmod lives in the child sitemaps, which need extra requests beyond the 3-request cap); (3) rows in the table include the "(personal name...)" marker inside the name cell, fine.
  - can fail: if the city pattern missed accents, Overpass would return 0 elements; if the path check were skipped a repo path would be accepted. Both were exercised (123 elements; rev-parse returned an error only for a non-repo path).

- [x] **B11 reaction tester** (steps by hand; 3 personas, not 12, to spare the weekly limit)
  - Case: offer "one-page website with WhatsApp booking, 5 days, 450,000 COP one time" for Medellin barbershops (follows from the lead list).
  - Baseline given first: owners live on WhatsApp/Instagram, expect price and "will it bring clients" objections. Spend confirmation: the caller's instruction to use each once stood in for the "yes".
  - 3 Sonnet subagents (all marked "invented"; no reviews given): Carlos (barbershop), Dona Luz (peluqueria), Andres (El Poblado). 3 of 3 answered; all WOULD BUY: maybe.
  - Objections ranked (n of 3): who updates prices/hours/photos later and at what cost 3; wants examples from other local shops 3; "Google-visible" vague or unproven 3 (Carlos, Luz, Andres); hidden costs behind "no monthly fee" / domain and hosting 3; 450,000 COP vs unproven new clients 2 (Carlos, Luz); already has WhatsApp/Instagram/booking app 2 (Carlos, Andres); pay after seeing it, not upfront 2 (Carlos, Luz); English+Spanish for tourists 1; "barbershop" wording vs her peluqueria 1.
  - Differs from baseline: baseline did not predict the "who maintains it" and "show examples" objections, nor the wording mismatch barbershop vs peluqueria.
  - Label: **opinions of simulated people, not a forecast**.
  - can fail: if a subagent answered in the wrong shape it would be dropped and the report would show "n of 3 answered"; if the persona prompt ignored the offer text, objections would not reference 450,000 COP and the 5 days. They did.

- [x] **B12 idea scorecard** (new-business.md template, same idea)
  - Case: the idea above, scored with only the evidence at hand.
  - Fatal-flaw 5 questions: real problem? yes weak (120 of 123 OSM hairdressers have no website tag, but OSM tags are incomplete); buyer pays? unproven; market size? unknown; founder fit? plausible (the owner's studio); why now/defensibility? none.
  - Scorecard: problem 3 (OSM count; owners say Instagram suffices), buyer pays 2 (3 simulated maybes, no real buyer), market size 2 (no evidence), founder fit 4 (web studio, Spanish), why now 1 (no evidence), reach 3 (lead list exists, contact by hand), cost to test 5 (talk to 5-10 owners, near zero). Total 20/35.
  - Verdict: **change course**: sell "get found and booked" proof, not a bare site. Cheap tests: show a sample site to 5 Medellin owners; ask 3 whether they would pay 450,000 COP before building; check Google Maps listing completeness for 5 owners.
  - can fail: if the file lacked a dimension or the /35 total the table could not be filled; verified the 7 dimension names, "Total n/35" and "build / change course / drop" are present in new-business.md (lines ~40-100).

- [x] **B13 new number replaces old** (rule file read at claude-home/rules/new-number-replaces-old.md, 3 lines)
  - Case A (real): the 450,000 COP price used in the reaction test had no source. The rule says write a bracket placeholder: it should have been `[price: ask the client]`. Applied honestly: the figure is recorded here as an unsourced test input, not as a fact for any doc.
  - Case B (replace branch, simulated user figure): scratch copy of ~/.claude/skills/offers/SKILL.md line 114 ("plan on 10-40% relative lift"); with the rule the figure becomes `[lift: ask the client]` in /tmp/.../p0056/rule-case.txt. The skill file itself was not touched. Log line: "replaced 10-40% (2026-10-18) with [lift: ask the client]". No user actually gave a differing figure, so only the placeholder half was truly exercised; the "replaced X with Y" half is a dry run.
  - can fail: the grep of the output for "ask the client" and the absence of "10" would fail if the rule were ignored. Note the rule is not yet installed into ~/.claude/rules/, so it was not live in this session.
