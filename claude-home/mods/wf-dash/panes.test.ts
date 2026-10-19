import { expect, test } from 'claude-code/testing'
import { DEFAULT_VIEW, Dashboard, PLAN_TABS, askText, paginate, planLines, untag, wrapWords } from './panes.tsx'
import { color } from './tokens.ts'

// every string a drawn tree prints, components called the way the host would
function texts(node: any): string[] {
  if (node == null || typeof node === 'boolean') return []
  if (typeof node === 'string' || typeof node === 'number') return [String(node)]
  if (Array.isArray(node)) return node.flatMap(texts)
  if (typeof node.type === 'function') return texts(node.type(node.props))
  return texts(node.props?.children)
}
const passThrough = (p: any) => p.children ?? null
const el = { Box: passThrough, Text: passThrough, Button: passThrough } as any

// covers: spec 0065 AC-3 (an empty alerts list says when wf could not be read, and before the first tick)
test('an empty alerts view says could not read wf, reading wf, or the empty text, from statusOk', () => {
  const view = { ...DEFAULT_VIEW, section: 'alerts' }
  const act = { go: () => {}, retry: () => {} }
  const draw = (statusOk: boolean | null) =>
    texts(Dashboard({ el, view, act, plan: null, runner: null, agents: [], alerts: [], facts: null, statusOk, columns: 100 } as any)).join('')
  expect(draw(false)).toContain('could not read wf')
  expect(draw(false)).not.toContain('No alerts yet')
  expect(draw(null)).toContain('reading wf')
  expect(draw(true)).toContain('No alerts yet.')
  expect(draw(true)).not.toContain('could not read wf')
})

// covers: spec 0065 AC-2 (a stopped alert shows in the Alerts view in alert.stopped, color.warn)
test('a stopped alert row prints its kind in the warn color, next to a finished one in ok', () => {
  // the host's jsx calls each component as it builds, so Text leaves a tagged pair in the tree
  const Text = (p: any) => ({ printed: [String(p.children), p.color] })
  const colored = (node: any): [string, string][] => {
    if (node == null || typeof node !== 'object') return []
    if (Array.isArray(node)) return node.flatMap(colored)
    if (node.printed) return [node.printed]
    if (typeof node.type === 'function') return colored(node.type(node.props))
    return colored(node.props?.children)
  }
  const view = { ...DEFAULT_VIEW, section: 'alerts' }
  const alerts = [
    { id: 'finished:r1', at: 0, kind: 'finished', feature: '1. A', detail: 'in work' },
    { id: 'stopped:r2', at: 0, kind: 'stopped', feature: '2. B', detail: 'in work, usage limit' },
  ]
  const got = colored(Dashboard({ el: { Box: passThrough, Text, Button: passThrough }, view, act: { go: () => {}, retry: () => {} },
    plan: null, runner: null, agents: [], alerts, facts: null, statusOk: true, columns: 100 } as any))
  expect(got).toContainEqual(['stopped', color.warn])
  expect(got).toContainEqual(['finished', color.ok])
  expect(got).toContainEqual(['in work, usage limit', color.dim])
})

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

test('a question drops the "in <feature>" its row already names, and keeps the ask', () => {
  const f = "74. Fix the runner's plan landing crash"
  expect(askText(`the step needs something only you can do in ${f}. the 0054 and 0061 pull requests need to be merged`, f))
    .toBe('the step needs something only you can do. the 0054 and 0061 pull requests need to be merged')
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
