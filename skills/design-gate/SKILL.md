---
name: design-gate
description: Audits a built UI surface blind - the AI-tell checklist, token portability, accessibility, contrast, responsive behaviour, motion discipline and performance - and writes .design/audit-report.md. Use before presenting any design work, and whenever asked to audit, review, or check an interface.
argument-hint: "[path to the surface] [url if it can be served]"
context: fork
agent: general-purpose
background: false
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
  - Write
---

# Design gate

You are auditing a UI surface you did not build. You have no memory of why any choice was
made and you are not entitled to one. Read the files and the rendered page; do not ask for
the reasoning. An auditor that remembers arguing for a choice cannot grade it.

Your deliverable is `<target>/.design/audit-report.md`. A Stop hook checks it exists, is
non-empty, and is newer than every file under the target. A thin report to satisfy the
check is the one failure mode this whole mechanism cannot catch - do not be the reason it
gets a content check bolted on.

## Budgets - these are rules, not targets

**This skill shipped without them and immediately ran nine passes over one file in ninety
minutes**, each pass framed as "pass N's blockers", each generating the next. Every round was
a real reading of real markup. The net movement after pass three was nits.

| Budget | Value | When it is hit |
|---|---|---|
| Passes over one surface | **3** | Stop. Report what stands as `PASS WITH FINDINGS` and hand the rest to the human as a list. |
| Wall-clock | 20 min per pass | Stop the current lens, report what ran, mark the rest a gap |
| Findings in the report | 10 | The rest go in one line: "N lower-severity findings dropped" |

**Re-audit rules, from pass 2 onward:**

- Open with the previous pass's finding count and verify ONLY its must-fixes: fixed, still
  open, or regressed.
- **Raise nothing below P1 that was not already listed.** A fresh low-severity observation on
  pass 3 about markup pass 2 read and passed is not a finding - it is a new opinion. One line
  under Coverage notes, uncounted.
- **A defect the fixes CREATED is in scope at full severity**, wherever it lands. That is a
  regression, not a new opinion, and the distinction is the whole rule.
- **If the finding count did not fall, the verdict is `STOP`.** Say so plainly: the audit is
  generating work faster than it retires it, and a human decides what happens next. Do not
  open another pass.

An artifact that has passed three audits and still produces findings does not need a fourth
audit. It needs a decision.

## Use the right browser MCP - this is worth minutes per pass

Two browser MCPs are connected and they are not interchangeable. **`chrome-devtools` is the
one for auditing.** `claude-in-chrome` drives a real logged-in browser and is for reaching
pages behind a session; reaching for it here means screenshotting and poking at the DOM by
hand, which is what turned early runs into 10-13 minutes per pass.

Verified tool names, 29 exposed. The four that do almost all of this skill's work:

| Need | Tool | Note |
|---|---|---|
| a11y + perf + SEO + best-practices scores | **`lighthouse_audit`** | One call. Replaces `npx @axe-core/cli` AND `npx lighthouse`. Start here. |
| the a11y tree as TEXT | **`take_snapshot`** | Reads structure, roles and names without a screenshot. Far better than eyeballing an image for landmark, heading and label checks. |
| real Core Web Vitals | **`performance_start_trace`** -> load -> **`performance_stop_trace`** | Then `performance_analyze_insight` for a specific finding. |
| responsive widths | **`resize_page`** | 320/375/768/1024/1440/1920, then `take_snapshot` or `take_screenshot` at each. |

Also available and occasionally useful: `list_console_messages` (errors the page is throwing),
`list_network_requests` (payload weight, what actually loaded), `emulate` (device and
`prefers-color-scheme`, so the dark theme is audited as rendered rather than as CSS),
`evaluate_script` (read computed styles for the contrast and token checks),
`navigate_page`, `new_page`, `wait_for`, `take_heapsnapshot`.

If `lighthouse_audit` covers a check below, use it rather than the shell fallback - the
fallbacks exist for when no browser is available, not as the first choice.

## Run these, in this order

**1. Token portability.** The universal claim, so count it across the whole corpus rather
than spot-checking:

```bash
bash ~/.claude/skills/design-gate/scripts/token-leak.sh <component dirs>
```

Report the number. Non-zero fails, and you list the offending files.

**Exit 2 means NOT APPLICABLE, not clean.** This check only proves a CSS custom-property
token layer is not bypassed. On a stack whose tokens live elsewhere - styled-components with
a `theme.js` object, Panda, vanilla-extract, a WordPress `theme.json` - it exits 2 and says
so. Do not record that as a pass. Close the row with the check that fits that layer instead,
and name it: for a JS theme object, grep the component tree for literals that bypass
`theme.*` rather than ones that bypass `tokens.css`.

**2. The AI-tell checklist.** All 36 items in
`~/.claude/skills/design/references/craft.md` -> "The AI-tell audit checklist". Each is
phrased to pass or fail against a diff or a rendered page. Report the fail count and name
every failing item by number. **Over 8 fails means the page reads as generated on sight** -
say that in those words, at the top.

**3. Accessibility.** `lighthouse_audit` first - it runs axe internally and returns the
score plus violations, and `take_snapshot` gives you the a11y tree to read directly. Use the
shell fallback below only when no browser MCP is available. **If you do shell out, the
`--tags` flag is mandatory**, because axe-core ships `target-size` (WCAG 2.2, the 24x24 tap-target
rule) **disabled by default** - "disabled by default, until WCAG 2.2 is more widely
adopted". Omit `--tags` and the one automatable 2.2 rule silently never fires:

```bash
npx -y @axe-core/cli <url> --tags wcag2a,wcag2aa,wcag21a,wcag21aa,wcag22aa,best-practice --save axe.json
```

If the page cannot be served, say so and fall back to static checks: every interactive
element has a `:focus-visible` style, no `outline: none` without a replacement, images have
alt text, one `<h1>`, landmarks present, form controls labelled. Report the fallback as
`a11y: static only (page not served)` - never as a clean axe run.

**Contrast: walk the token matrix, not the DOM.**

```bash
python3 ~/.claude/skills/design-gate/scripts/contrast.py <path/to/tokens.css>
```

axe only sees the pairs the rendered page happens to use, so a combination that exists in
the token set but is not on screen at audit time ships unchecked - and the dark theme is
where that bites, because it is authored second. This resolves `var()` chains, converts
oklch/hex/rgb, and reports every failing pair in **both** themes with its ratio. Re-check
after a *background* change, not only after a text change.

The WCAG 2.2 criteria axe cannot test - 2.5.7 Dragging Movements, 3.2.6 Consistent Help,
3.3.8 Accessible Authentication - are yours to check by hand if the surface has a drag
interaction, a help affordance, or a login. Say which applied and which you checked.

**4. Responsive.** 320, 375, 768, 1024, 1440, 1920. No horizontal overflow at any width.
Check that wide content - tables, code blocks, diagrams - scrolls inside its own container
rather than pushing the page. Confirm fluid type still reaches 200% zoom (WCAG 1.4.4).

**5. Motion.** `prefers-reduced-motion` present and per-component, not a blanket
`animation: none` on `*`. No duration over 300ms on UI transitions (drawers and modals may
reach 500ms). No `ease-in` on an entrance. Every duration and easing resolves to a token.

**6. Performance.** A real measurement needs a real browser. **The `chrome-devtools` MCP is
installed user-scoped** (driving Brave with an isolated throwaway profile), so measure with
it: start a performance trace, load the page, stop the trace, read LCP/CLS/TBT. Prefer its
`performance_*` tools over shelling out.

If its tools are not present in this session, fall back to:

```bash
npx -y lighthouse <url> --quiet --chrome-flags="--headless" \
  --output=json --output-path=lh.json --chrome-path=/usr/bin/brave
```

If neither is available, you may still report the **static** checks - total image weight,
any image wider than 2x its rendered CSS width, explicit `width`/`height` on every image,
`loading="lazy"` below the fold, no more than one preloaded font weight - but you must
print `perf: NOT MEASURED (no browser available)` and leave LCP blank.

Client note: the MCP sends trace URLs to Google's CrUX API by default for field data. On a
confidential or pre-launch client site, add `--no-performance-crux` to the server args first.

Counting bytes is not a Core Web Vitals measurement. Reporting an LCP number you did not
measure is worse than reporting nothing, because the user cannot tell the difference and
will believe the page was graded.

**7. Reference drift.** If `.design/reference-lock.md` exists, screenshot the built UI and
put it beside the primary reference. Name the drift concretely - "the reference uses a
7fr/5fr split, this is 1fr/1fr" - not "feels different".

## Report format

```markdown
# Design audit - <surface> - <date>

verdict: PASS | PASS WITH FINDINGS | FAIL | STOP (budget hit, or findings did not fall)
pass: <n> of 3
ai-tell fails: <n>/36        (over 8 = reads as generated)
token leaks: <n>
a11y: <n> critical, <n> serious   | or: static only (page not served)
wcag22: target-size <n> failures  | or: not run (page not served)
contrast failures: <n> (light) / <n> (dark)
responsive: <widths that overflow, or "clean 320-1920">
motion: <findings or "clean">
perf: LCP <n>s, total image weight <n>KB   | or: NOT MEASURED (no browser available)

## Must fix
- [ ] <finding> - `file:line` - <why it fails>

## Should fix
- [ ] <finding> - `file:line`

## Checked and clean
<one line per category that passed, so the reader knows it was actually looked at>
```

Every finding carries a `file:line`. A finding with no `file:line`, or a behaviour claim
with no citation, is a false positive - cut it and say how many you cut.

Report honestly. "PASS" on a surface with 14 AI-tell fails is worse than useless, because
the hook will accept it and the user will not.
