import { expect, mock, test } from 'claude-code/testing'

const SID = '0a73f089-5127-4347-998d-3a7c8adf3ac9'
const FACTS = { plugin: 'wf-dash', key: 'facts' } as const

// the host beneath register.tsx: facts.py answers as told, files live in memory
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
  on('process.run', () => ({ value: { ...facts(), stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  return { files, state, clock }
}

// covers: spec 0059 AC-2 (facts.py failing from the start still draws the band, its own fields `?`; a later failure
// keeps the last good facts marked stale, the mark keeping its first time), and no file is written under the old
// runner marker folder
test('a facts.py that fails from the start still draws, and a later failure marks the band stale once', async ($, on) => {
  let factsOk = false
  const { files, state, clock } = host(on, () => factsOk
    ? { exitCode: 0, stdout: JSON.stringify({ folder: 'w', git: null, via: null }) }
    : { exitCode: 1, stdout: '' })
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await clock.advance(10)
  expect(state[FACTS.key]?.folder).toBe(null)
  expect(state[FACTS.key]?.staleSince).toBe(null)
  expect(Object.keys(files).filter(f => f.includes('/.local/state/'))).toEqual([])

  factsOk = true
  await clock.advance(5000)
  expect(state[FACTS.key]?.folder).toBe('w')
  expect(state[FACTS.key]?.staleSince).toBe(null)

  factsOk = false
  await clock.advance(5000)
  const since = state[FACTS.key]?.staleSince
  expect(state[FACTS.key]?.folder).toBe('w')
  expect(since).not.toBe(null)
  // past a minute, since the mark is a clock time: a mark that moved on each failed tick would show here
  await clock.advance(65000)
  expect(state[FACTS.key]?.staleSince).toBe(since)

  factsOk = true
  await clock.advance(5000)
  expect(state[FACTS.key]?.staleSince).toBe(null)
})

test('facts.py output that is not JSON counts as a failed tick, never a crash', async ($, on) => {
  let out = JSON.stringify({ folder: 'w', git: null, via: null })
  const { state, clock } = host(on, () => ({ exitCode: 0, stdout: out }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await clock.advance(10)
  out = 'Traceback (most recent call last)'
  await clock.advance(5000)
  expect(state[FACTS.key]?.folder).toBe('w')
  expect(state[FACTS.key]?.staleSince).not.toBe(null)
})

// a local named h hid the JSX factory, so every band draw threw and the host drew nothing in its place
test('the band above the prompt draws, with and without a handoff line', async ($, on) => {
  const { state } = host(on, () => ({ exitCode: 1, stdout: '' }))
  const props = { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 100 }
  let ui = await $.ui.mount({ plugin: 'wf-dash', surface: 'terminal', component: 'AbovePrompt', props } as never)
  expect(await ui.find({ type: 'Text', text: /wf-dash: reading status/ })).toBeDefined()
  await ui.unmount()
  state['handoff'] = { panel: { sticky: true, steps: [] }, frame: 0 }
  ui = await $.ui.mount({ plugin: 'wf-dash', surface: 'terminal', component: 'AbovePrompt', props } as never)
  expect(await ui.find({ type: 'Text', text: /wf-dash: reading status/ })).toBeDefined()
  await ui.unmount()
})
