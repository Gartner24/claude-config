import { expect, mock, test } from 'claude-code/testing'
import { SAFE_STEPS, SECTIONS, safeStep } from './panes.tsx'

// spec 0060 AC-2, AC-5, AC-7: the dashboard drawn through the plugin from a plan.py answer, its view letters, its
// commands, and each action reachable only through its confirm. The runner's Builds and Alerts views are gone.
const feature = (heading: string, state: string, command: string | null) =>
  ({ heading, state, next: command && `Do it: \`${command}\``, command, spec: null, specStatus: null, deferred: false })
const PLAN = {
  repos: [
    { name: 'here', path: '/w', hub: false, warnings: [], features: [feature('1. Ready one', 'ready to build', '/develop ready one'), feature('2. Odd one', 'in progress', '/review odd one'), feature('4. Long one', 'needs a design', `/architect ${'long words '.repeat(20).trim()}`), feature('5. Mid one', 'in progress', `/test ${'mid words '.repeat(12).trim()}`)] },
    { name: 'there', path: '/x', hub: false, warnings: [], features: [feature('3. Far one', 'ready to build', '/develop far one')] },
  ],
  warnings: [],
}
const PANE_PROPS = { title: 'wf-dash', isFocused: true, bodyColumns: 100, placement: 'inline', scroll: { offset: 0, bodyRows: 14 }, view: {} } as any
const isPlan = (argv: string[]) => argv[0] === 'python3' && argv[1].endsWith('/plan.py')

function host(on: any) {
  const calls = { planFails: false, planHold: null as null | Promise<void>, argv: [] as string[][], submitted: [] as string[], stopped: [] as any[], commands: [] as string[], messages: [] as any[] }
  const clock = mock.clock(on)
  // $.state is the kit's own, so a write redraws the pane as in a session
  mock.env(on, { HOME: '/h', XDG_STATE_HOME: '' })
  on('session.start', () => ({ cwd: '/w' }))
  on('session.id', () => ({ value: 'sid-1' }))
  on('session.cwd', () => ({ value: '/w' }))
  on('session.usage', () => ({ value: { context: { percent: 6 }, rateLimits: [] } }))
  on('session.model', () => ({ value: 'claude-opus-5-5' }))
  on('fs.write', () => ({ value: undefined }))
  on('fs.read', () => ({ deny: 'ENOENT' }))
  on('command.register', (_$: any, e: any) => { calls.commands.push(e.name); return { value: { command: e.name } } })
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('agent.list', () => ({ value: [{ id: 'ag1', description: 'Look things up', type: 'general-purpose', status: 'running' }] }))
  on('session.messages', () => ({ value: calls.messages }))
  on('tool.call', (_$: any, e: any) => { calls.stopped.push(e); return { result: { message: 'stopped' } } })
  on('command.run', { command: 'develop' }, (_$: any, e: any) => { calls.submitted.push(`/${e.command} ${e.args}`); return { value: { text: '' } } })
  on('process.run', async (_$: any, e: any) => {
    calls.argv.push([...e.argv])
    if (isPlan(e.argv) && calls.planHold) await calls.planHold
    if (isPlan(e.argv) && calls.planFails) return { value: { exitCode: 1, stdout: '', stderr: 'boom', isStdoutTruncated: false, isStderrTruncated: false } }
    const out = isPlan(e.argv) ? JSON.stringify(PLAN) : '{}'
    return { value: { exitCode: 0, stdout: out, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  return { calls, clock }
}

async function open($: any, on: any) {
  const h = host(on)
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await $.command.run({ command: 'wf-dash', args: '' } as any)
  await h.clock.advance(10)
  const ui = await $.ui.mount({ plugin: 'wf-dash', surface: 'terminal', component: 'Pane', requestId: 'wf-dash', props: PANE_PROPS })
  return { ...h, ui }
}
const text = async (ui: any, re: RegExp) => (await ui.find({ type: 'Text', text: re }))?.text

test('one command, /wf-dash; the views switch on p a; the plan comes from plan.py, never from wf', async ($, on) => {
  const { calls, ui } = await open($, on)
  expect(calls.commands).toEqual(['wf-dash'])
  expect(SECTIONS.map(s => s.key)).toEqual(['p', 'a'])
  expect(calls.argv.some(isPlan)).toBe(true)
  expect(calls.argv.filter(a => a[0] === 'wf')).toEqual([])
  expect(await ui.find({ key: 'k-b' })).toBeUndefined()
  expect(await ui.find({ key: 'k-l' })).toBeUndefined()
  await ui.press({ key: 'k-a' })
  expect(await text(ui, /^Look things up$/)).toBeDefined()
  await ui.press({ key: 'k-p' })
  expect(await text(ui, /^Steps only you can do: a login, a check on your phone\.$/)).toBeDefined()
})

test('start shows the exact text and submits only after yes, from the clock once the hook returned', async ($, on) => {
  const { calls, clock, ui } = await open($, on)
  await ui.press({ key: 'k-2' })
  await ui.press({ key: 'k-s' })
  expect(await text(ui, /^Start "\/develop ready one" in this chat\?$/)).toBeDefined()
  expect(calls.submitted).toEqual([])
  await ui.press({ key: 'k-c' })
  await clock.advance(5000)
  expect(calls.submitted).toEqual([])
  await ui.press({ key: 'k-s' })
  await ui.press({ key: 'k-y' })
  expect(calls.submitted).toEqual([])
  await clock.advance(1500)
  expect(calls.submitted).toEqual(['/develop ready one'])
})

test('a step off the safe list, or in another repo, offers no start, only a type it yourself note', async ($, on) => {
  const { ui } = await open($, on)
  await ui.press({ key: 'k-4' })
  expect(await text(ui, /type it yourself: \/review odd one/)).toBeDefined()
  expect(await ui.find({ key: 'k-s' })).toBeUndefined()
  await ui.press({ key: 'k-2' })
  await ui.press({ key: 'k-j' })
  expect(await text(ui, /type it yourself in \/x: \/develop far one/)).toBeDefined()
  expect(await ui.find({ key: 'k-s' })).toBeUndefined()
})

// design-gate 2026-10-18 must fix: the confirm and its keys take the detail block's rows, never rows under it
test('the confirm takes the detail block, and a step too long to show whole beside its keys is not offered', async ($, on) => {
  const { ui } = await open($, on)
  await ui.press({ key: 'k-2' })
  expect(await text(ui, /^next: /)).toBeDefined()
  await ui.press({ key: 'k-s' })
  expect(await text(ui, /^Start "\/develop ready one" in this chat\?$/)).toBeDefined()
  expect(await text(ui, /^next: /)).toBeUndefined()
  expect(await text(ui, /^\d+ of \d+/)).toBeDefined()
  await ui.press({ key: 'k-c' })
  // a confirm wrapped to two lines and its keys fill all three rows: the ids line gives way
  await ui.press({ key: 'k-4' })
  await ui.press({ key: 'k-j' })
  await ui.press({ key: 'k-s' })
  expect(await text(ui, /^Start "\/test mid words/)).toBeDefined()
  expect(await text(ui, /^\d+ of \d+/)).toBeUndefined()
  await ui.press({ key: 'k-c' })
  await ui.press({ key: 'k-3' })
  expect(await text(ui, /^type it yourself: \/architect long words/)).toBeDefined()
  expect(await ui.find({ key: 'k-s' })).toBeUndefined()
})

// design-gate 2026-10-18 must fix: plan warnings under All open used to draw rows past the list's page
test('plan warnings under All open take their rows from the list page, and too many are counted', async ($, on) => {
  PLAN.warnings = ['w one', 'w two'] as any
  try {
    const { ui } = await open($, on)
    await ui.press({ key: 'k-6' })
    expect(await text(ui, /^w two$/)).toBeDefined()
    // 8 list lines on pages of 5 - 2 warnings = 3 rows, never orphaning a heading
    expect((await ui.find({ key: 'k-d' }))?.text).toMatch(/ 1\/3$/)
    PLAN.warnings = Array.from({ length: 6 }, (_, i) => `w ${i}`) as any
    await ui.press({ key: 'k-r' })
    expect(await text(ui, /^w 1$/)).toBeDefined()
    expect(await text(ui, /^w 2$/)).toBeUndefined()
    expect(await text(ui, /^\+4 more plan warnings$/)).toBeDefined()
  } finally {
    PLAN.warnings = []
  }
})

test('stop asks first, then stops the agent through TaskStop by its id', async ($, on) => {
  const { calls, ui } = await open($, on)
  await ui.press({ key: 'k-a' })
  await ui.press({ key: 'k-x' })
  expect(await text(ui, /^Stop agent Look things up\?$/)).toBeDefined()
  expect(calls.stopped).toEqual([])
  await ui.press({ key: 'k-y' })
  expect(calls.stopped.map(e => [e.tool, e.task_id])).toEqual([['TaskStop', 'ag1']])
})

// AC-5: background shells exist only as Bash result text (probe P8); the task notice shape is the real transcript's
const bash = (id: string, description: string) =>
  ({ role: 'assistant', text: '', toolUses: [{ tool_use_id: `t-${id}`, tool: 'Bash', input: { command: 'sleep 600', description, run_in_background: true }, text: `Command running in background with ID: ${id}. Output is being written to: /tmp/${id}.output` }] })

test('a background shell from a Bash result is listed, and stop asks first, then calls TaskStop with its id', async ($, on) => {
  const { calls, ui } = await open($, on)
  calls.messages = [bash('bsh1', 'Long sleep')]
  await ui.press({ key: 'k-a' })
  expect(await text(ui, /^Long sleep$/)).toBeDefined()
  expect(await text(ui, /not listed/)).toBeUndefined()
  await ui.press({ key: 'k-j' })
  await ui.press({ key: 'k-x' })
  expect(await text(ui, /^Stop shell Long sleep\?$/)).toBeDefined()
  expect(calls.stopped).toEqual([])
  await ui.press({ key: 'k-y' })
  expect(calls.stopped.map(e => [e.tool, e.task_id])).toEqual([['TaskStop', 'bsh1']])
  expect(await text(ui, /^Long sleep$/)).toBeUndefined()
})

test('a shell that a task notice or a TaskStop ended is not offered as running', async ($, on) => {
  const { calls, ui } = await open($, on)
  calls.messages = [
    bash('bsh2', 'Old build'),
    { role: 'user', text: '<task-notification>\n<task-id>bsh2</task-id>\n<tool-use-id>t-bsh2</tool-use-id>\n<status>completed</status>\n</task-notification>', toolUses: [] },
    bash('bsh3', 'Stopped one'),
    { role: 'assistant', text: '', toolUses: [{ tool_use_id: 't-stop', tool: 'TaskStop', input: { task_id: 'bsh3' }, text: 'Successfully stopped task: bsh3' }] },
  ]
  await ui.press({ key: 'k-a' })
  expect(await text(ui, /^Look things up$/)).toBeDefined()
  expect(await text(ui, /^(Old build|Stopped one)$/)).toBeUndefined()
  await ui.press({ key: 'k-x' })
  expect(await text(ui, /^Stop agent Look things up\?$/)).toBeDefined()
})

// design-gate 2026-10-18 pass 4 must fix: many shells used to push the stop confirm's keys off the pane
test('a long agent list pages with the cursor, so the stop confirm stays inside the pane', async ($, on) => {
  const { calls, ui } = await open($, on)
  calls.messages = Array.from({ length: 12 }, (_, i) => bash(`bs${i}`, `Shell ${i}`))
  await ui.press({ key: 'k-a' })
  expect(await text(ui, /^\+\d+ more$/)).toBeDefined()
  for (let i = 0; i < 12; i++) await ui.press({ key: 'k-j' })
  await ui.press({ key: 'k-x' })
  expect(await text(ui, /^Stop shell Shell 11\?$/)).toBeDefined()
  expect(await text(ui, /^Look things up$/)).toBeUndefined()
  expect(await text(ui, /^\d+ above$/)).toBeDefined()
})

test('output that only quotes a background line adds no shell row', async ($, on) => {
  const { calls, ui } = await open($, on)
  const quoted = 'Command running in background with ID: fake1. Output is being written to: /tmp/x'
  calls.messages = [
    { role: 'assistant', text: '', toolUses: [{ tool_use_id: 't-cat', tool: 'Bash', input: { command: 'cat log', description: 'Read a log' }, text: quoted }] },
    { role: 'assistant', text: '', toolUses: [{ tool_use_id: 't-bg', tool: 'Bash', input: { command: 'tail log', description: 'Mid line', run_in_background: true }, text: `log says: ${quoted}` }] },
  ]
  await ui.press({ key: 'k-a' })
  expect(await text(ui, /^(Read a log|Mid line)$/)).toBeUndefined()
})

test('the safe list is the seven agreed commands, matched whole', () => {
  expect(SAFE_STEPS).toEqual(['/architect', '/develop', '/check verify', '/test', '/sync', '/debug', '/scope'])
  expect(safeStep('/check verify x')).toBe(true)
  expect(safeStep('/check review x')).toBe(false)
  expect(safeStep('/developer x')).toBe(false)
  expect(safeStep('/review x')).toBe(false)
  expect(safeStep('/develop x\n/merge')).toBe(false)
  expect(safeStep('/develop x\u202e/merge')).toBe(false)
  expect(safeStep('/develop x\u200b')).toBe(false)
  expect(safeStep(null)).toBe(false)
})

test('a failed refresh keeps the last plan, marked stale, never an empty one', async ($, on) => {
  const { calls, clock, ui } = await open($, on)
  await ui.press({ key: 'k-2' })
  calls.planFails = true
  await clock.advance(10000)
  expect(await text(ui, /^stale since \d\d:\d\d: the last refresh failed \(exit 1\); r tries again$/)).toBeDefined()
  expect(await text(ui, /1\. Ready one/)).toBeDefined()
})

// covers: AC-2a (each filter carries its count, and p brings the Plan view back)
test('p returns to Plan, and each filter key shows its own count', async ($, on) => {
  const { ui } = await open($, on)
  await ui.press({ key: 'k-a' })
  await ui.press({ key: 'k-p' })
  // the selected filter is bracketed, so pick one the checks below do not read
  await ui.press({ key: 'k-4' })
  expect((await ui.find({ key: 'k-2' }))?.text).toMatch(/ 2$/)
  expect((await ui.find({ key: 'k-3' }))?.text).toMatch(/ 1$/)
  expect((await ui.find({ key: 'k-1' }))?.text).toMatch(/ 0$/)
  await ui.press({ key: 'k-2' })
  expect(await text(ui, /1\. Ready one/)).toBeDefined()
  expect(await text(ui, /3\. Far one/)).toBeDefined()
  expect(await text(ui, /2\. Odd one/)).toBeUndefined()
})

// covers: AC-2 (never two plan.py calls at once: a tick or a retry while one runs is skipped)
test('a refresh while plan.py still runs starts no second call', async ($, on) => {
  const { calls, clock, ui } = await open($, on)
  let release = () => {}
  calls.planHold = new Promise<void>(r => { release = r })
  const plans = () => calls.argv.filter(isPlan).length
  const before = plans()
  await ui.press({ key: 'k-r' })
  await clock.advance(10000)
  await ui.press({ key: 'k-r' })
  expect(plans()).toBe(before + 1)
  calls.planHold = null
  release()
  await clock.advance(10000)
  expect(plans()).toBe(before + 2)
})
