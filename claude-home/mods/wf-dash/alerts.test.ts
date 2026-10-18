import { expect, test } from 'claude-code/testing'
import { alertTick, counts, diff, NEVER_SEEN, parseStatus } from './alerts.ts'
import { segments } from './band.tsx'
import { pane, time } from './tokens.ts'

const run = (id: string | null, feature = '1. A') => ({ id, repo: 'work', feature })
const ask = (id: string, title = 'Which storage engine?', feature = '2. B') => ({ id, repo: 'work', feature, title })
const status = (running: any[] | null, parked: any[] | null, questions: any[] | null) => ({ running, parked, questions })

// a $ with only what alertTick calls: state and files in memory, toasts recorded
function fake$(files: Record<string, string> = {}) {
  const state: Record<string, any> = {}
  const toasts: { text: string; opts: any }[] = []
  const $ = {
    state: {
      get: async (r: any) => ({ value: state[r.key] }),
      set: async (r: any, v: any) => { state[r.key] = v; return { isSet: true } },
    },
    fs: {
      read: async (p: string) => { if (!(p in files)) throw new Error('ENOENT'); return files[p] },
      write: async (p: string, t: string) => { files[p] = t },
    },
    clock: { now: async () => 1000 },
    ui: { toast: (text: string, opts: any) => { toasts.push({ text, opts }) } },
  }
  return { $, state, toasts, files }
}
const opts = { keep: pane.history, timeoutMs: time.toast }

test('no alert on the first tick, whatever is already there', () => {
  const { alerts } = diff(NEVER_SEEN, status([run('r1')], [ask('q1')], [ask('q1')]))
  expect(alerts).toEqual([])
})

test('a run leaving running is finished, a new parked id is stuck, a new question id is a question', () => {
  let { seen } = diff(NEVER_SEEN, status([run('r1'), run('r2', '3. C')], [], []))
  const got = diff(seen, status([run('r2', '3. C')], [ask('q1')], [ask('q1'), ask('q2', 'Pick one', '4. D')]))
  expect(got.alerts).toEqual([
    { id: 'finished:r1', kind: 'finished', feature: '1. A', detail: 'in work' },
    { id: 'stuck:q1', kind: 'stuck', feature: '2. B', detail: 'Which storage engine?' },
    { id: 'question:q2', kind: 'question', feature: '4. D', detail: 'Pick one' },
  ])
  seen = got.seen
  expect(diff(seen, status([run('r2', '3. C')], [ask('q1')], [ask('q1'), ask('q2')])).alerts).toEqual([])
})

test('each id toasts once, even when it leaves and comes back', () => {
  let { seen } = diff(NEVER_SEEN, status([], [], []))
  seen = diff(seen, status([], [], [ask('q1')])).seen
  seen = diff(seen, status([], [], [])).seen
  expect(diff(seen, status([], [], [ask('q1')])).alerts).toEqual([])
})

test('a failed tick, or a null field, is skipped and never read as empty', () => {
  let { seen } = diff(NEVER_SEEN, status([run('r1')], [], [ask('q1')]))
  // read as empty, r1 would have finished; it must not
  const failed = diff(seen, null)
  expect(failed.alerts).toEqual([])
  expect(failed.seen).toEqual(seen)
  const nullRunning = diff(seen, status(null, [], [ask('q1')]))
  expect(nullRunning.alerts).toEqual([])
  // the next good tick still compares with r1, so its end is caught
  expect(diff(nullRunning.seen, status([], [], [ask('q1')])).alerts.map(a => a.id)).toEqual(['finished:r1'])
})

test('a run with no id never alerts', () => {
  const { seen } = diff(NEVER_SEEN, status([run(null)], [], []))
  expect(diff(seen, status([], [], [])).alerts).toEqual([])
})

test('an alert toasts for 15 s, lands in the alert list, and the list keeps the last 20', async () => {
  const { $, state, toasts } = fake$()
  await alertTick($, status([], [], []), '/d/s.toasts', opts)
  expect(toasts).toEqual([])
  for (let i = 0; i < 25; i++) await alertTick($, status([], [], Array.from({ length: i + 1 }, (_, j) => ask(`q${j}`))), '/d/s.toasts', opts)
  expect(toasts[0]).toEqual({ text: 'question: 2. B - Which storage engine?', opts: { timeoutMs: 15000 } })
  expect(toasts.length).toBe(25)
  expect(state.alerts.length).toBe(20)
  expect(state.alerts.at(-1)).toEqual({ id: 'question:q24', kind: 'question', feature: '2. B', detail: 'Which storage engine?', at: 1000 })
})

test('what was seen survives a reload through its file, so nothing toasts twice', async () => {
  const first = fake$()
  await alertTick(first.$, status([run('r1')], [], []), '/d/s.toasts', opts)
  await alertTick(first.$, status([], [], []), '/d/s.toasts', opts)
  expect(first.toasts.length).toBe(1)
  // a reload: $.state is empty, the file is not
  const again = fake$(first.files)
  await alertTick(again.$, status([], [], []), '/d/s.toasts', opts)
  await alertTick(again.$, status([run('r1')], [], []), '/d/s.toasts', opts)
  await alertTick(again.$, status([], [], []), '/d/s.toasts', opts)
  expect(again.toasts).toEqual([])
})

test('the band shows ? for a count the runner could not read, never 0', () => {
  expect(counts(status(null, [], [ask('q1')]))).toEqual({ running: null, parked: 0, questions: 1 })
  expect(counts(null)).toBe(null)
  expect(parseStatus('not json')).toBe(null)
  expect(parseStatus('{"running": 3}')).toBe(null)
  const f = { model: 'claude-opus-5-5', effort: null, folder: 'w', git: null, context: null, contextTokens: null, contextWindow: null,
    fiveHour: null, fiveHourReset: null, week: null, weekReset: null, via: null, auto: null, staleSince: null }
  const text = (wf: any) => segments({ ...f, wf }, 0, false).right.runs.map(r => r.text).join('')
  expect(text(counts(status(null, [], [ask('q1')])))).toBe('wf ? building  0 stuck  1 question')
  expect(text(counts(null))).toBe('wf ? status')
  // no subscription rate limits: the meters print ?
  const left = segments({ ...f, wf: null }, 0, false).left
  expect(left.find(s => s.id === '5h')!.runs.map(r => r.text).join('')).toContain('?')
})

test('unknown effort is left out of the band, never guessed', () => {
  const f = { model: 'claude-opus-5', effort: null, folder: 'w', git: null, context: null, contextTokens: null, contextWindow: null,
    fiveHour: 1, fiveHourReset: null, week: 1, weekReset: null, via: null, wf: null, auto: null, staleSince: null }
  const model = (effort: string | null) => segments({ ...f, effort }, 0, false).left.find(s => s.id === 'model')!.runs.map(r => r.text).join('')
  expect(model(null)).toBe('Opus 5')
  expect(model('medium')).toBe('Opus 5 medium')
})
