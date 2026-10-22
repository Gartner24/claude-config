import { expect, test } from 'claude-code/testing'
import { PLAN_TABS, paginate, planLines, startOffer, untag, wrapWords } from './panes.tsx'

const group = (name: string) => ({ kind: 'group' as const, name, note: '' })
const feat = (n: number, r: string) => ({ kind: 'feature' as const, f: { heading: `f${n}` } as any, repo: r })

test('a page that starts inside a group repeats its heading, marked cont.', () => {
  const lines = [group('a'), feat(1, 'a'), feat(2, 'a'), feat(3, 'a'), feat(4, 'a'), feat(5, 'a'), feat(6, 'a')]
  const pages = paginate(lines, 5)
  expect(pages.length).toBe(2)
  expect(pages[1][0]).toEqual({ kind: 'group', name: 'a', note: ' cont.' })
  expect(pages.every(p => p.length <= 5)).toBe(true)
})

test('a group heading never sits alone at the foot of a page', () => {
  const lines = [group('a'), feat(1, 'a'), feat(2, 'a'), feat(3, 'a'), group('b'), feat(4, 'b')]
  const pages = paginate(lines, 5)
  expect(pages[0][pages[0].length - 1].kind).toBe('feature')
  expect(pages[1][0]).toEqual(group('b'))
})

test('no lines gives one empty page', () => {
  expect(paginate([], 5)).toEqual([[]])
})

test('plan rows group by state across repos, the heading carries the count, in state order', () => {
  const f = (heading: string, state: string) => ({ heading, state }) as any
  const repos = [
    { name: 'a', features: [f('x', 'ready to build'), f('y', 'waits on you')] },
    { name: 'b', features: [f('z', 'waits on you'), f('w', 'done')] },
  ] as any
  const lines = planLines(repos, PLAN_TABS.find(t => t.id === 'open')!)
  expect(lines.map(l => (l.kind === 'group' ? `${l.name} ${l.note}` : l.kind === 'feature' ? `${l.f.heading}@${l.repo}` : l.text)))
    .toEqual(['waits on you 2', 'y@a', 'z@b', 'ready 1', 'x@a'])
})

test('a long next step wraps at spaces to two lines and marks what it cut', () => {
  const out = wrapWords('next: /check verify sessions pass work to each other and more words here', 20, 2)
  expect(out.length).toBe(2)
  expect(out.every(l => l.length <= 20)).toBe(true)
  expect(out[1].endsWith('...')).toBe(true)
  expect(wrapWords('short', 20, 2)).toEqual(['short'])
})

test('a single-state filter gives its heading row to a feature; All open keeps the heading', () => {
  const repos = [{ name: 'a', features: [{ heading: 'x', state: 'waits on you' }, { heading: 'y', state: 'waits on you' }] }] as any
  expect(planLines(repos, PLAN_TABS.find(t => t.id === 'needs-you')!).map(l => l.kind)).toEqual(['feature', 'feature'])
  expect(planLines(repos, PLAN_TABS.find(t => t.id === 'open')!)[0].kind).toBe('group')
})

test('a next step drops the plan tags and backticks, and keeps its words', () => {
  expect(untag('Deploy to beta: `bin/deploy.sh` . waits on you . later boxes go on')).toBe('Deploy to beta: bin/deploy.sh')
  expect(untag('/check verify x')).toBe('/check verify x')
})

test('the filters are the six the scope alone can tell; none needs the runner', () => {
  expect(PLAN_TABS.map(t => t.id)).toEqual(['needs-you', 'ready', 'design', 'progress', 'built', 'open'])
  expect(PLAN_TABS.flatMap(t => t.states ?? [])).not.toContain('building')
  const f = { heading: 'x', state: 'ready to build', next: null, command: '/develop x', spec: null, specStatus: null, deferred: false }
  expect(startOffer(f, '/w', '/w')).toEqual({ ok: true, text: '/develop x' })
})
