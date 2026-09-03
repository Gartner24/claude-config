# Testing Requirements

## Minimum Test Coverage: 80%

Test Types (ALL required):
1. **Unit Tests** - Individual functions, utilities, components
2. **Integration Tests** - API endpoints, database operations
3. **E2E Tests** - Critical user flows (framework chosen per language)

## Test-Driven Development

MANDATORY workflow:
1. Write test first (RED)
2. Run test - it should FAIL
3. Write minimal implementation (GREEN)
4. Run test - it should PASS
5. Refactor (IMPROVE)
6. Verify coverage (80%+)

## Get the RED back when the test came second

The workflow above depends on step 2: you watched the test fail, so you know it is wired to the thing it claims to cover. Most bug fixes skip that, because the fix is written before the test.

Mutation-check instead. Break the source deliberately, confirm that specific test goes red, restore it:

1. Back up the file with `cp` to a scratch path. Never `git checkout`, which discards unrelated edits.
2. Invert or remove the guard the fix added.
3. Run the test. It must fail, and it must be the test you wrote.
4. Restore from the backup and confirm the suite is green again.

State in the summary that the check was run. A test that passes against the broken code is not coverage, and this catches the case below.

### A test that reimplements the logic passes forever

The most common way a test covers nothing is defining a local copy of the behaviour and asserting against that, never importing the module under test. Reverting the real fix then leaves the whole suite green.

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

## Troubleshooting Test Failures

1. Use **tdd-guide** agent
2. Check test isolation
3. Verify mocks are correct
4. Fix implementation, not tests (unless tests are wrong)

### A mock weaker than the real module passes anything

A hook or module mocked with fewer fields than it really returns lets broken code through. Mock the shape the consumer actually reads, not the minimum that makes the test run.

## Agent Support

- **tdd-guide** - Use PROACTIVELY for new features, enforces write-tests-first

## Test Structure (AAA Pattern)

Prefer Arrange-Act-Assert structure for tests:

```typescript
test('calculates similarity correctly', () => {
  // Arrange
  const vector1 = [1, 0, 0]
  const vector2 = [0, 1, 0]

  // Act
  const similarity = calculateCosineSimilarity(vector1, vector2)

  // Assert
  expect(similarity).toBe(0)
})
```

### Test Naming

Use descriptive names that explain the behavior under test:

```typescript
test('returns empty array when no markets match query', () => {})
test('throws error when API key is missing', () => {})
test('falls back to substring search when Redis is unavailable', () => {})
```
