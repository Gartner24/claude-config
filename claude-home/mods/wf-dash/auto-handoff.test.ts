import { expect, mock, test } from 'claude-code/testing'
import { fit, segments } from './band.tsx'
import { space } from './tokens.ts'

// The band's auto handoff segment (on with its line, off, unknown) and the tick that reads it from wf-handoff's
// chain file. A non-coding chat turns the handoff off with /auto-handoff off; the band must say which this chat is.
const facts = {
  model: 'claude-opus-5-5[1m]', effort: 'medium', folder: 'claude-config',
  git: { branch: 'main', changes: 0, staged: 0, modified: 0, untracked: 0 },
  context: 16, contextTokens: 160000, contextWindow: 1000000,
  fiveHour: 21, fiveHourReset: null, week: 45, weekReset: null, via: null,
  wf: { running: 0, parked: 0, questions: 0 }, auto: null, staleSince: null, statusOk: true,
}
const text = (f: any) => segments(f, 0, false).left.find(s => s.id === 'handoff')?.runs.map(r => r.text).join('')

test('the handoff segment says on with its line, off, or ? when no chain file names this chat', () => {
  expect(text({ ...facts, handoff: { off: false, line: 200000 } })).toBe('handoff on 200k')
  expect(text({ ...facts, handoff: { off: true, line: 200000 } })).toBe('handoff off')
  expect(text({ ...facts, handoff: { off: false, line: null } })).toBe('handoff on')
  expect(text({ ...facts, handoff: null })).toBe('handoff ?')
  expect(text(facts)).toBeUndefined()
})

test('a narrow band drops the model before the handoff state', () => {
  const f = { ...facts, handoff: { off: true, line: 200000 } }
  const { left, right } = segments(f, 0, false)
  const chip = left.find(s => s.id === 'chip')!.cells
  const hand = left.find(s => s.id === 'handoff')!.cells
  // room for the chip, the handoff segment and the runner counts, not the model too
  const room = chip + hand + right.cells + 2 * space.gap + 2 * space.padX
  expect(fit(left, right, room).map(s => s.id)).toEqual(['chip', 'handoff'])
})

const SID = '0a73f089-5127-4347-998d-3a7c8adf3ac9'
const DIR = '/h/.claude/state/auto-handoff'
function host(on: any, files: Record<string, string>) {
  const clock = mock.clock(on)
  mock.env(on, { HOME: '/h', XDG_STATE_HOME: '' })
  on('session.start', () => ({ cwd: '/w' }))
  on('session.id', () => ({ value: SID }))
  on('session.cwd', () => ({ value: '/w' }))
  on('session.usage', () => ({ value: { context: { percent: 6 }, rateLimits: [] } }))
  on('session.model', () => ({ value: 'claude-opus-5-5' }))
  on('settings.read', () => ({ value: { effortLevel: 'high' } }))
  on('fs.write', (_$: any, e: any) => { files[e.path] = e.text ?? ''; return { value: undefined } })
  on('fs.read', (_$: any, e: any) => (e.path in files ? { value: files[e.path] } : { deny: 'ENOENT' }))
  on('command.register', (_$: any, e: any) => ({ value: { command: e.name } }))
  on('process.run', (_$: any, e: any) => ({ value: { exitCode: 0, stdout: e.argv[0] === 'wf' ? '{}' : JSON.stringify({ folder: 'w', git: null, via: null }), stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  return clock
}
const props = { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 160 }

for (const surface of ['terminal', 'desktop'] as const) {
  test(`the band on the ${surface} reads off and the line from the chain file a handed off chat points at`, async ($, on) => {
    const files: Record<string, string> = {
      [`${DIR}/${SID}.root`]: 'ROOT\n',
      [`${DIR}/ROOT.json`]: JSON.stringify({ root: 'ROOT', session: SID, off: true, line: 250000 }),
    }
    const clock = host(on, files)
    await $.session.start({ surface, isInteractive: true, cwd: '/w' } as any)
    await clock.advance(10)
    const ui = await $.ui.mount({ plugin: 'wf-dash', surface, component: 'AbovePrompt', props } as never)
    expect(await ui.find({ type: 'Text', text: /^off$/ })).toBeDefined()
    // the settings' effort stands in before the first reply
    expect(await ui.find({ type: 'Text', text: /^ high$/ })).toBeDefined()
    await ui.unmount()
    files[`${DIR}/ROOT.json`] = JSON.stringify({ root: 'ROOT', session: SID, line: 250000 })
    await clock.advance(5000)
    const again = await $.ui.mount({ plugin: 'wf-dash', surface, component: 'AbovePrompt', props } as never)
    expect(await again.find({ type: 'Text', text: /^on 250k$/ })).toBeDefined()
    await again.unmount()
  })
}

test('a chain file that names another chat is not this chat\'s: the band says ?', async ($, on) => {
  const clock = host(on, { [`${DIR}/${SID}.json`]: JSON.stringify({ root: SID, session: 'someone-else', off: true }) })
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await clock.advance(10)
  const ui = await $.ui.mount({ plugin: 'wf-dash', surface: 'terminal', component: 'AbovePrompt', props } as never)
  expect(await ui.find({ type: 'Text', text: /^handoff \?$/ })).toBeDefined()
  await ui.unmount()
})

test('a survey holds the band: the band steps aside', async ($, on) => {
  const clock = host(on, {})
  // the engine's own drawing beneath the plugin: the survey
  on('ui.render', ($: any, e: any) => h($.ui.resolve(e).Text, {}, 'the survey'))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await clock.advance(10)
  const ui = await $.ui.mount({ plugin: 'wf-dash', surface: 'terminal', component: 'AbovePrompt', props: { ...props, hasSurvey: true } } as never)
  expect(await ui.find({ type: 'Text', text: /wf-dash/ })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: /^the survey$/ })).toBeDefined()
  await ui.unmount()
})
