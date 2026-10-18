import { expect, mock, test } from 'claude-code/testing'

const SID = '0a73f089-5127-4347-998d-3a7c8adf3ac9'
const STATUS = { running: [{ id: 'r1', repo: 'work', feature: '1. A' }], parked: [], questions: [] }
const FACTS = { plugin: 'wf-dash', key: 'facts' } as const

// the host beneath register.tsx: facts.py and `wf status --json` answer as told, files live in memory
function host(on: any, facts: () => { exitCode: number; stdout: string }) {
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
    const r = e.argv[0] === 'wf' ? { exitCode: 0, stdout: JSON.stringify(STATUS) } : facts()
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
