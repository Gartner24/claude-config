import { expect, test } from 'claude-code/testing'
import { fit, segments } from './band.tsx'
import { space } from './tokens.ts'

const facts = {
  model: 'claude-opus-5-5[1m]', effort: 'medium', folder: 'claude-config',
  git: { branch: 'docs/wf-dash-design', changes: 3, staged: 1, modified: 1, untracked: 1 },
  context: 16, contextTokens: 160000, contextWindow: 1000000,
  fiveHour: 21, fiveHourReset: null, week: 45, weekReset: null, via: null,
  wf: { running: 4, parked: 1, questions: 2 }, auto: { here: false, chats: 2 }, staleSince: null,
}

// the cells the band takes for the segments it keeps, the way fit() counts them
const width = (kept: { cells: number }[], right: { cells: number }) =>
  kept.reduce((n, s) => n + s.cells, 0) + space.gap * Math.max(0, kept.length - 1) + space.gap + right.cells + 2 * space.padX

for (const columns of [94, 120, 160]) {
  test(`the band fits one line at ${columns} columns and keeps the chip and the runner`, () => {
    const { left, right } = segments(facts, 0, false)
    const kept = fit(left, right, columns - space.hostReserve)
    expect(width(kept, right)).toBeLessThanOrEqual(columns - space.hostReserve)
    expect(kept.map(s => s.id)).toContain('chip')
    expect(right.runs.map(r => r.text).join('')).toContain('4 building')
  })
}

test('compact runner counts leave zeros out and put what needs you first', () => {
  const { right } = segments({ ...facts, wf: { running: 4, parked: 0, questions: 2 } }, 0, false, true)
  expect(right.runs.map(r => r.text).join('')).toBe('2 ask 4 run')
})

test('the 31-cell column beside the docked dashboard keeps the chip and drops whole counts, least urgent first', () => {
  const room = 31 - space.hostReserve - space.hotkeyCells
  const wf = { running: 1, parked: 2, questions: 2 }
  const chip = segments({ ...facts, wf }, 0, false).left[0]
  const { left, right } = segments({ ...facts, wf }, 0, false, true, room - 2 * space.padX - chip.cells - space.gap)
  const kept = fit(left, right, room)
  expect(kept.map(s => s.id)).toEqual(['chip'])
  expect(width(kept, right)).toBeLessThanOrEqual(room)
  expect(right.runs.map(r => r.text).join('')).toBe('2 ask')
})

test('the stale mark fits the 31-cell column too, so old counts never read as current', () => {
  const room = 31 - space.hostReserve - space.hotkeyCells
  const f = { ...facts, wf: { running: 1, parked: 2, questions: 2 }, staleSince: '10:42' }
  const chip = segments(f, 0, false).left[0]
  const { left, right } = segments(f, 0, false, true, room - 2 * space.padX - chip.cells - space.gap)
  expect(width(fit(left, right, room), right)).toBeLessThanOrEqual(room)
  expect(right.runs.map(r => r.text).join('')).toBe('stale')
  const wide = segments(f, 0, false, true, 20).right
  expect(wide.runs.map(r => r.text).join('')).toBe('2 ask 2 stuck stale')
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
  expect(left.find(s => s.id === 'git')!.runs.map(r => r.text).join('')).toBe('main')
})
