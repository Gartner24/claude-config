import { expect, test } from 'claude-code/testing'
import { BUILD_STALE_MS, fit, liveBuilds, segments } from './band.tsx'
import { space } from './tokens.ts'

const facts = {
  model: 'claude-opus-5-5[1m]', effort: 'medium', folder: 'claude-config',
  git: { branch: 'docs/wf-dash-design', changes: 3, staged: 1, modified: 1, untracked: 1 },
  context: 16, contextTokens: 160000, contextWindow: 1000000,
  fiveHour: 21, fiveHourReset: null, week: 45, weekReset: null, via: null,
  staleSince: null, handoff: { off: false, line: 200000 },
}

// the cells the band takes for the segments it keeps, the way fit() counts them
const width = (kept: { cells: number }[], right: { cells: number }) =>
  kept.reduce((n, s) => n + s.cells, 0) + space.gap * Math.max(0, kept.length - 1) + space.gap + right.cells + 2 * space.padX
const words = (s: { runs: { text: string }[] }) => s.runs.map(r => r.text).join('')

for (const columns of [94, 120, 160]) {
  test(`the band fits one line at ${columns} columns and keeps the chip and the handoff state`, () => {
    const { left, right } = segments(facts, 0, false)
    const kept = fit(left, right, columns - space.hostReserve)
    expect(width(kept, right)).toBeLessThanOrEqual(columns - space.hostReserve)
    expect(kept.map(s => s.id)).toContain('chip')
    expect(words(right)).toBe('handoff on 200k')
  })
}

test('the right end says on with the line, off, or ? when unknown, and never names the runner', () => {
  expect(words(segments({ ...facts, handoff: { off: true, line: 200000 } }, 0, false).right)).toBe('handoff off')
  expect(words(segments({ ...facts, handoff: null }, 0, false).right)).toBe('handoff ?')
  expect(words(segments({ ...facts, handoff: undefined }, 0, false).right)).toBe('handoff ?')
  const all = segments(facts, 0, false)
  // the chip's own name says chip-dash; the runner's segment began "wf " and named builds, stuck runs and questions
  expect([...all.left, all.right].map(words).join(' ')).not.toMatch(/(^|\s)wf\s|building|stuck|question/)
})

test('the 31-cell column beside the docked dashboard keeps the chip and the bare handoff state', () => {
  const room = 31 - space.hostReserve - space.hotkeyCells
  const chip = segments(facts, 0, false).left[0]
  const { left, right } = segments(facts, 0, false, true, room - 2 * space.padX - chip.cells - space.gap)
  const kept = fit(left, right, room)
  expect(kept.map(s => s.id)).toEqual(['chip'])
  expect(width(kept, right)).toBeLessThanOrEqual(room)
  expect(words(right)).toBe('on 200k')
})

test('the stale mark shows when it fits and leaves before the handoff state does', () => {
  const f = { ...facts, staleSince: '10:42' }
  expect(words(segments(f, 0, false).right)).toBe('handoff on 200k  stale since 10:42')
  expect(words(segments(f, 0, false, true, 20).right)).toBe('on 200k stale')
  expect(words(segments(f, 0, false, true, 8).right)).toBe('on 200k')
})

test('a wide line keeps every segment', () => {
  const { left, right } = segments(facts, 0, false)
  expect(fit(left, right, 400).length).toBe(left.length)
})

test('segments leave in the drop order: folder first, model last', () => {
  const { left, right } = segments(facts, 0, false)
  const all = width(left, right)
  const folderGone = fit(left, right, all - 1).map(s => s.id)
  expect(folderGone).not.toContain('folder')
  expect(folderGone).toContain('model')
})

test('unknown context is left out, never shown as 0', () => {
  const { left } = segments({ ...facts, context: null }, 0, false)
  expect(left.map(s => s.id)).not.toContain('ctx')
})

test('a repo whose counts were skipped shows its branch only, never clean', () => {
  const git = { branch: 'main', changes: null, staged: null, modified: null, untracked: null }
  const { left } = segments({ ...facts, git }, 0, false)
  expect(words(left.find(s => s.id === 'git')!)).toBe('main')
})

test('unknown effort is left out of the band, never guessed', () => {
  const { left } = segments({ ...facts, effort: null }, 0, false)
  expect(words(left.find(s => s.id === 'model')!)).toBe('Opus 5.5')
})

// covers: spec 0074 AC-12 (build <n> when n is above 0, nothing at 0 or unknown)
test('the band shows build <n> only while workflow agents run', () => {
  const ids = (f: any) => segments(f, 0, false).left.map(s => s.id)
  expect(words(segments({ ...facts, build: 2 }, 0, false).left.find(s => s.id === 'build')!)).toBe('build 2')
  expect(ids({ ...facts, build: 0 })).not.toContain('build')
  expect(ids(facts)).not.toContain('build')
})

// covers: spec 0074 AC-12 (an entry with no turn.complete for 2 hours is dropped)
test('a workflow agent with no end for 2 hours is no longer counted', () => {
  const running = new Map([['old', 0], ['new', BUILD_STALE_MS]])
  expect(liveBuilds(running, BUILD_STALE_MS)).toBe(2)
  expect(liveBuilds(running, BUILD_STALE_MS + 1)).toBe(1)
  expect([...running.keys()]).toEqual(['new'])
})
