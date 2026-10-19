import { expect, mock, test } from 'claude-code/testing'

const SID = '0a73f089-5127-4347-998d-3a7c8adf3ac9'
const STATUS = { running: [{ id: 'r1', repo: 'work', feature: '1. A' }], parked: [], questions: [] }
const FACTS = { plugin: 'wf-dash', key: 'facts' } as const

// the host beneath register.tsx: facts.py and `wf status --json` answer as told, files live in memory
function host(on: any, facts: () => { exitCode: number; stdout: string }, wf: () => { exitCode: number; stdout: string } = () => ({ exitCode: 0, stdout: JSON.stringify(STATUS) })) {
  const files: Record<string, string> = {}
  const state: Record<string, any> = {}
  const clock = mock.clock(on)
  on('state.get', (_$: any, e: any) => ({ value: { value: state[e.key], version: 0 } }))
  on('state.set', (_$: any, e: any) => { state[e.key] = e.value; return { value: { isSet: true, version: 1 } } })
  mock.env(on, { HOME: '/h', XDG_STATE_HOME: '' })
  on('session.start', () => ({ cwd: '/w' }))
  on('session.id', () => ({ value: SID }))
  on('session.cwd', () => ({ value: '/w' }))
  on('session.usage', () => ({ value: { context: { percent: 6 }, rateLimits: [] } }))
  on('session.model', () => ({ value: 'claude-opus-5-5' }))
  on('fs.write', (_$: any, e: any) => { files[e.path] = e.content ?? e.data ?? ''; return { value: undefined } })
  on('fs.read', (_$: any, e: any) => (e.path in files ? { value: files[e.path] } : { deny: 'ENOENT' }))
  on('command.register', (_$: any, e: any) => ({ value: { command: e.name } }))
  on('process.run', (_$: any, e: any) => {
    const r = e.argv[0] === 'wf' ? wf() : facts()
    return { value: { ...r, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  return { files, state, clock }
}

// covers: spec 0059 AC-2 (facts.py failing from the start still shows live runner counts, its own fields `?`; a later
// failure keeps the last good facts marked stale), AC-4 (the marker is touched under the mod's own folder)
test('a facts.py that fails from the start leaves the runner counts live, and a later failure marks the band stale', async ($, on) => {
  let factsOk = false
  const { files, state, clock } = host(on, () => factsOk
    ? { exitCode: 0, stdout: JSON.stringify({ folder: 'w', git: null, via: null, auto: null }) }
    : { exitCode: 1, stdout: '' })
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await clock.advance(10)
  expect(state[FACTS.key]?.wf).toEqual({ running: 1, parked: 0, questions: 0 })
  expect(state[FACTS.key]?.folder).toBe(null)
  expect(state[FACTS.key]?.staleSince).toBe(null)
  expect(Object.keys(files)).toContain(`/h/.local/state/wf-dash/${SID}`)

  factsOk = true
  await clock.advance(5000)
  expect(state[FACTS.key]?.folder).toBe('w')
  expect(state[FACTS.key]?.staleSince).toBe(null)

  factsOk = false
  await clock.advance(5000)
  expect(state[FACTS.key]?.folder).toBe('w')
  expect(state[FACTS.key]?.staleSince).not.toBe(null)
})

// covers: spec 0065 AC-1 (a stale tick keeps the runner counts it read, a failed field its last good count, and stores
// statusOk), plus the stale mark keeping its first time
test('a stale tick shows the runner counts it just read, and statusOk says whether wf status was read', async ($, on) => {
  let factsOk = true
  let wf: any = STATUS
  const { state, clock } = host(on,
    () => factsOk ? { exitCode: 0, stdout: JSON.stringify({ folder: 'w', git: null, via: null, auto: null }) } : { exitCode: 1, stdout: '' },
    () => wf ? { exitCode: 0, stdout: JSON.stringify(wf) } : { exitCode: 1, stdout: '' })
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await clock.advance(10)
  expect(state[FACTS.key]?.statusOk).toBe(true)

  factsOk = false
  wf = { running: [STATUS.running[0], { id: 'r2', repo: 'work', feature: '2. B' }], parked: null, questions: [] }
  await clock.advance(5000)
  const since = state[FACTS.key]?.staleSince
  expect(since).not.toBe(null)
  expect(state[FACTS.key]?.wf).toEqual({ running: 2, parked: 0, questions: 0 })
  expect(state[FACTS.key]?.statusOk).toBe(true)

  wf = null
  // past a minute, since the mark is a clock time: a mark that moved on each failed tick would show here
  await clock.advance(65000)
  expect(state[FACTS.key]?.wf).toEqual({ running: 2, parked: 0, questions: 0 })
  expect(state[FACTS.key]?.statusOk).toBe(false)
  expect(state[FACTS.key]?.staleSince).toBe(since)

  wf = { running: null, parked: null, questions: null }
  factsOk = true
  await clock.advance(5000)
  expect(state[FACTS.key]?.statusOk).toBe(false)
})
