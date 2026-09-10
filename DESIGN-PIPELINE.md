# Design pipeline - setup and use

Rewritten 2026-09-09. The previous version taught a setup that no longer works: it told you
to run

```
claude mcp add magic --scope user --env API_KEY="YOUR_KEY" -- npx -y @21st-dev/magic@latest
```

which is the exact command that produced the broken server that failed on every session for
months. `@21st-dev/magic` is now a shim; the service moved to `https://21st.dev/api/mcp` and
switched from an `API_KEY` env var to an `x-api-key` header. It also documented `/ui` and
`/21` as if they were commands. They were never protocol features, only tool-description
conventions, and they are gone.

There is almost nothing to set up now. Read the "One-time" section, then use `/design`.

---

## What runs the pipeline

Three skills, not a prompt you retype:

| | Owns | Enforced by |
|---|---|---|
| **`/brand-system`** | Client identity: positioning, register, type, colour, logo, voice | Run ledger + Stop hook. `emit` closes only when the board passes the contract checker. |
| **`/design`** | Surfaces: a page, a section, a component, in any stack | Run ledger + Stop hook. `gate` can never be skipped. |
| **`/assets`** | Imagery, icons, shapes, background removal | Triage table - most assets are coded or fetched, not generated. |

`/design-gate` is the blind auditor `/design` calls. It runs forked, with no memory of the
build, because an auditor that argued for a choice cannot grade it.

**A signed `brand-system.html` outranks everything.** `/design` transcribes its `:root`
tokens; it does not re-derive them.

---

## One-time

**Already installed and connected** - nothing to do:

```
mobbin           real shipped app screens, returned inline as images   (paid Mobbin plan, OAuth)
shadcn           component sourcing, any registry                      (no key, user-scoped)
21st             inspiration, React+Tailwind only                      (x-api-key)
chrome-devtools  real perf measurement, drives Brave in a throwaway profile
```

If `/mcp` does not list one, restart the session - MCP servers load at start.

**The only thing you still have to do yourself:**

```bash
bash ~/.claude/skills/assets/scripts/gemini-key.sh set     # paste the key, hidden
bash ~/.claude/skills/assets/scripts/gemini-key.sh test    # proves billing is actually on
```

Image generation is **not** on the Gemini API free tier and a consumer Gemini subscription
grants no API quota, so the key must be attached to a billing-enabled project. Budget $2-4 per
site. Without a key `/assets` still works - it hands you paste-ready prompts to run in the
Gemini app instead of silently skipping imagery.

**Optional, per project:** `pnpm dlx shadcn@latest mcp init --client claude` pins the shadcn
server into the repo's `.mcp.json` so teammates get it too. Not needed for you - it is already
user-scoped.

---

## Using it

```
/design [what + where]
```

That is the whole prompt. Everything the old kickoff block spelled out is now in the skill,
and the skill is enforced rather than suggested. Add context only when it changes the answer:
a reference image or URL, brand colours, a Figma link, existing CSS to match. Whatever you
supply is locked as given; whatever you leave out gets decided and stated.

For a client build, run `/brand-system` first. `/design` will otherwise propose a direction
the client never signed off on.

### What actually happens

```
detect     which stack, from the repo, not from assumption
reference  look at real shipped UI first - Mobbin, then Refero, then public galleries
direction  brand-system > design-dna on a reference > saved direction > ui-ux-pro-max
tokens     the direction becomes tokens.css - this is what makes it stack-agnostic
source     shadcn MCP, then the per-stack matrix
assemble   frontend-design + impeccable
assets     /assets
motion     animate, only where it earns its place
gate       design-gate, blind. Cannot be skipped.
conversion cro/pricing/signup/paywalls, marketing surfaces only
```

Each step closes a row in `<project>/.design/run.json` with evidence, or a skip reason from a
closed vocabulary. A Stop hook refuses to end the turn while a row is open. The closing table
is generated from that file, so it cannot claim a step ran when it did not.

---

## The two rules that matter most

**1. Fonts and colours are searched, never picked from a list.** A lookup table cannot produce
variety - that is why every site used to come out with the same faces. The old brand guide had
25 families in a 6-row table and recommended Inter in half of them.

```bash
python3 ~/.claude/skills/design/scripts/fontsearch.py \
  --adjectives loud active --anti calm --category Display --seed <client-slug>
node ~/.claude/skills/design/scripts/build-ramp.mjs --hue <deg> --sat 0.9
```

`--seed <client-slug>` is mandatory: it samples the qualifying band instead of always taking
the top of the ranking. The `--min-pop 300` floor excludes Inter, Roboto, Poppins, Montserrat,
Open Sans, Lato and Playfair by construction - all of them are top-30 by popularity - and
still leaves 189 quality-72+ Display families.

**2. Most assets should never touch an image model.** Icons come from Iconify, backgrounds and
grain and blobs are code, OG cards are rendered text, UI mockups are screenshots of the real
thing, and portraits are a hard stop that asks you for a real photograph. Generation is for
conceptual and atmospheric imagery, and that is roughly one asset in five.

---

## Reference material

Long-form, in the skills rather than here so it loads on demand:

- `skills/design/references/craft.md` - the 36-item AI-tell checklist and 25 ranked craft moves
- `skills/design/references/stacks.md` - stack detection, component matrix, the token schema
- `skills/design/references/reference-lock.md` - Mobbin/Refero, gallery ladder, ToS boundaries
- `skills/assets/references/` - generation, sourcing, shapes, editing, prompting
- `~/projects/freelance/website-build-templates/guides/BRAND-SYSTEM-GUIDE.md` - the craft layer

Verify the tooling still works after touching it:
`bash ~/.claude/skills/design/scripts/test-ledger.sh` (37 assertions)
