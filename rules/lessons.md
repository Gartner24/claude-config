# Hard-won lessons (always loaded)

Kept from rules/ecc when the rest of ECC was excluded from loading (2026-09-24).
Only project-specific lessons live here; generic practice is left to the model.

## Subagent models

When starting a subagent without a pinned model, pass `model`: sonnet for search, review and
simple edits; opus only for architecture and hard debugging. Custom agents already pin theirs.

## Review: an absent answer rendered as a definite one


The highest-yield class to look for in any code that renders fetched data, and the easiest to miss because it looks like defensive coding. Found more than a dozen times in a single console redesign.

For every count, list, status or total on screen, ask what it shows while the request is in flight, and what it shows after the request failed:

- `total ?? 0` reports a site with no visitors and an account owning no websites, when the truth is that nothing arrived.
- An empty array from a failed fetch renders identically to a genuinely empty collection, producing "no results", "no builds", "nobody else has access".
- A response missing a field is not a response saying the field is absent.
- A count that has not loaded is not zero, and a fetch that failed is not an empty list.

Falling back to different behaviour is fine. Falling back to a different fact is not. When the answer is unknown, say so or say nothing, and never print the zero.

Watch for it especially where a value gates a destructive control: a count defaulting to zero can switch off the guard on an irreversible action.

The same trap runs the other way for a lookup into a table you own - design tokens, an enum map, a constant registry. There a miss is a typo, not an absence, so a default beside the lookup buries it permanently: `colors.gray[950] || '#0f172a'` returned the fallback on every read because the path did not exist, and the result looked correct. Validate the key or let it throw. Genuinely optional external values - an env var, a user setting, an absent config field - keep their defaults; the difference is whether you wrote the table.


## Testing

## Get the RED back when the test came second

The workflow above depends on step 2: you watched the test fail, so you know it is wired to the thing it claims to cover. Most bug fixes skip that, because the fix is written before the test.

Mutation-check instead. Break the source deliberately, confirm that specific test goes red, restore it:

1. Back up the file with `cp` to a scratch path. Never `git checkout`, which discards unrelated edits.
2. Invert or remove the guard the fix added. A fix that touched several call sites has
   several guards: revert each one alone and watch that site's test go red. Two handlers
   dereferencing the same undefined argument were both fixed and only one was tested;
   the second path shipped uncovered and had to be pinned in a follow-up PR.
3. Run the test. It must fail, and it must be the test you wrote.
4. Restore from the backup and confirm the suite is green again.

State in the summary that the check was run. A test that passes against the broken code is not coverage, and this catches the case below.

### A test that reimplements the logic passes forever

The most common way a test covers nothing is defining a local copy of the behaviour and asserting against that, never importing the module under test. Caught twice in one codebase, both times a local helper standing in for the real module. Reverting the real fix then leaves the whole suite green.

Import the module under test. If it is awkward to render or construct, that is an argument for a shared fixture, not for a stand-in copy of its logic in the test file.

## A universal claim needs a corpus-wide assertion on the real artifact

When the requirement says **all**, **none**, **every**, or **zero** - "no inline styles
in the production build", "every route requires auth", "no secrets in the bundle",
"all prices are in cents" - a fixture cannot verify it and neither can asserting that
the transform ran.

A mutation check does not save you here. Break the source and a wrongly-scoped test
still goes red, which proves it is wired, not that it measures the right thing.

Three requirements, all of them:

1. **Assert on the artifact the user receives**, not on the machinery that produces it.
   The built file, the rendered HTML, the API response. Not "the extractor was called",
   not "the flag is true", not "the function returns the right shape".
2. **Quantify over the whole corpus.** Walk every file, route, or record the claim
   covers and count violations. One fixture proves one fixture.
3. **Assert the count is zero, and print the count on failure.** `expect(violations)
   .toHaveLength(0)` with the offenders listed. A boolean tells you something broke; a
   number tells you how far off you are, and a number that reads 600 is unmissable.

If the claim is conditional - gated on an env var, a build mode, a feature flag - the
test sets that condition and inspects the output produced under it. A test that runs in
development cannot verify a claim about production.

### Why this is its own rule

A test asserting that the machinery ran passed while 600+ violations shipped to
production. The suite was green, the mutation check would have passed, and the feature
was entirely non-functional. Coverage percentage says nothing about this: the line was
covered, by an assertion that could not fail for the reason that mattered.

### A mock weaker than the real module passes anything

A hook or module mocked with fewer fields than it really returns lets broken code through. A module mocked without one field the consumer reads meant a retry control that could never render, and every test passed. Mock the shape the consumer actually reads, not the minimum that makes the test run.

