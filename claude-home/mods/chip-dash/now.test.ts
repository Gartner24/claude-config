import { expect, mock, test } from 'claude-code/testing'
import { fit, segments } from './band.tsx'
import { checksWord, parsePrs } from './now.ts'
import { SECTIONS, owedLines } from './panes.tsx'
import { space, time } from './tokens.ts'

// Spec 0071: the Now view (owed, PRs, handoff, agents), its one gh search, and the band's `owed N`.
const CATCH = '/h/.claude/state/chain-catch'
const AUTO = '/h/.claude/state/auto-handoff'
const PANEL = `${AUTO}/panel.json`
const PANE_PROPS = { title: 'chip-dash', isFocused: true, bodyColumns: 100, placement: 'inline', scroll: { offset: 0, bodyRows: 14 }, view: {} } as any
const isGh = (argv: string[]) => argv[0] === 'gh'

const node = (repo: string, number: number, title: string, isDraft: boolean, state: string | null) =>
  ({ number, title, isDraft, url: `https://github.com/o/${repo}/pull/${number}`, repository: { name: repo }, commits: { nodes: [{ commit: { statusCheckRollup: state === null ? null : { state } } }] } })
const answer = (nodes: any[], total = nodes.length) => JSON.stringify({ data: { search: { issueCount: total, nodes } } })
const bash = (id: string) =>
  ({ role: 'assistant', text: '', toolUses: [{ tool_use_id: `t-${id}`, tool: 'Bash', input: { command: 'sleep 1', description: `shell ${id}`, run_in_background: true }, text: `Command running in background with ID: ${id}. Output is being written to: /tmp/${id}` }] })

function host(on: any) {
  const w = {
    id: 'S1',
    files: {} as Record<string, string>,
    dirs: new Set<string>(),
    gh: { exitCode: 0, stdout: answer([node('here', 4, 'Fix it', false, 'FAILURE'), node('there', 9, 'Draft one', true, null)]), stderr: '' },
    ghHold: null as null | Promise<void>,
    argv: [] as string[][],
    agents: [] as any[] | null,
    messages: [] as any[] | null,
    // closes the pane as the person's close mark does: the engine raises ui.close, the mod's hook hears it
    close: async () => {},
  }
  const clock = mock.clock(on)
  mock.env(on, { HOME: '/h', XDG_STATE_HOME: '' })
  on('session.start', () => ({ cwd: '/w' }))
  on('session.id', () => ({ value: w.id }))
  on('session.cwd', () => ({ value: '/w' }))
  on('session.usage', () => ({ value: { context: { percent: 6 }, rateLimits: [] } }))
  on('session.model', () => ({ value: 'claude-opus-5-5' }))
  on('fs.write', () => ({ value: undefined }))
  on('fs.read', (_$: any, e: any) => (e.path in w.files ? { value: w.files[e.path] } : { deny: 'ENOENT' }))
  on('fs.exists', (_$: any, e: any) => ({ value: e.path in w.files || w.dirs.has(e.path) }))
  on('command.register', (_$: any, e: any) => ({ value: { command: e.name } }))
  // the engine's record of open panes: the person's close mark takes the pane out of it (a test cannot raise ui.close)
  let open = false
  on('ui.open', (_$: any, e: any) => { open = true; w.close = async () => { open = false }; return { value: { isPlaced: true } } })
  on('ui.panes', () => ({ value: open ? [{ id: 'chip-dash', title: 'chip-dash', isShown: true, isFocused: true, isPlaced: true }] : [] }))
  on('agent.list', () => (w.agents ? { value: w.agents } : { deny: 'no agents api' }))
  on('session.messages', () => (w.messages ? { value: w.messages } : { deny: 'no transcript' }))
  on('process.run', async (_$: any, e: any) => {
    w.argv.push([...e.argv])
    if (isGh(e.argv)) {
      if (w.ghHold) await w.ghHold
      return { value: { ...w.gh, isStdoutTruncated: false, isStderrTruncated: false } }
    }
    const out = e.argv[1]?.endsWith('/plan.py') ? JSON.stringify({ repos: [], warnings: [] }) : '{}'
    return { value: { exitCode: 0, stdout: out, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  return { w, clock }
}

async function start($: any, on: any, setup: (w: any) => void = () => {}) {
  const h = host(on)
  setup(h.w)
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await h.clock.advance(10)
  return h
}
async function openDash($: any, h: any) {
  await $.command.run({ command: 'chip', args: '' } as any)
  await h.clock.advance(10)
  return $.ui.mount({ plugin: 'chip-dash', surface: 'terminal', component: 'Pane', requestId: 'chip-dash', props: PANE_PROPS })
}
async function openNow($: any, on: any, setup?: (w: any) => void) {
  const h = await start($, on, setup)
  const ui = await openDash($, h)
  await ui.press({ key: 'k-n' })
  await h.clock.advance(10)
  return { ...h, ui }
}
const text = async (ui: any, re: RegExp) => (await ui.find({ type: 'Text', text: re }))?.text
const ghCalls = (w: any) => w.argv.filter(isGh).length

// -- AC-1 -------------------------------------------------------------------------------------------------------------

test('AC-1 the top line reads p Plan, n Now, a Agents; it opens on Plan, n opens Now, and Plan keeps n free', async ($, on) => {
  expect(SECTIONS.map(s => `${s.key}: ${s.label}`)).toEqual(['p: Plan', 'n: Now', 'a: Agents'])
  const h = await start($, on)
  const ui = await openDash($, h)
  expect(await text(ui, /^Steps only you can do/)).toBeDefined()
  // two buttons on one hotkey, the later wins: Plan's next group must not sit on n
  expect((await ui.find({ key: 'k-t' }))?.text).toMatch(/next group/)
  await ui.press({ key: 'k-n' })
  expect(await text(ui, /^your PRs /)).toBeDefined()
})

// -- AC-2 -------------------------------------------------------------------------------------------------------------

test('AC-2 no catch folder: catch not installed', async ($, on) => {
  const { ui } = await openNow($, on)
  expect(await text(ui, /^catch not installed \(row 92\)$/)).toBeDefined()
})

test('AC-2 the folder but no file for this chat, or an empty owed list: nothing owed', async ($, on) => {
  const { w, clock, ui } = await openNow($, on, w => { w.dirs.add(CATCH); w.files[`${CATCH}/OTHER.json`] = JSON.stringify({ owed: ['not ours'] }) })
  expect(await text(ui, /^nothing owed$/)).toBeDefined()
  expect(await text(ui, /not ours/)).toBeUndefined()
  w.files[`${CATCH}/S1.json`] = JSON.stringify({ owed: [], blocks: 0 })
  await clock.advance(time.bandTick)
  expect(await text(ui, /^nothing owed$/)).toBeDefined()
})

test('AC-2 a file that does not parse: owed ? and the parse error, never nothing owed', async ($, on) => {
  const { ui } = await openNow($, on, w => { w.dirs.add(CATCH); w.files[`${CATCH}/S1.json`] = '{"owed": [' })
  expect(await text(ui, /^owed \?$/)).toBeDefined()
  expect(await text(ui, /JSON|Unexpected|parse/i)).toBeDefined()
  expect(await text(ui, /^nothing owed$/)).toBeUndefined()
})

test('AC-2 each owed line on its own row under owed N', async ($, on) => {
  const { ui } = await openNow($, on, w => { w.dirs.add(CATCH); w.files[`${CATCH}/S1.json`] = JSON.stringify({ owed: ['owed: /check verify x (row 9 X)', 'owed: /test y (row 10 Y)'], blocks: 1 }) })
  expect(await text(ui, /^owed 2$/)).toBeDefined()
  expect(await text(ui, /^owed: \/check verify x \(row 9 X\)$/)).toBeDefined()
  expect(await text(ui, /^owed: \/test y \(row 10 Y\)$/)).toBeDefined()
})

test('AC-2 after a /clear the chat reads the file of the id it replaced', async ($, on) => {
  const { w, clock, ui } = await openNow($, on, w => { w.dirs.add(CATCH); w.files[`${CATCH}/S1.json`] = JSON.stringify({ owed: ['owed: /sync z (row 3 Z)'] }) })
  w.id = 'S2'
  await clock.advance(time.bandTick)
  expect(await text(ui, /^owed: \/sync z \(row 3 Z\)$/)).toBeDefined()
  w.files[`${CATCH}/S2.json`] = JSON.stringify({ owed: [] })
  await clock.advance(time.bandTick)
  expect(await text(ui, /^nothing owed$/)).toBeDefined()
})

// -- AC-3 -------------------------------------------------------------------------------------------------------------

test('AC-3 one gh api graphql search; each PR as repo#number, draft or ready, checks, title', async ($, on) => {
  const { w, ui } = await openNow($, on)
  const calls = w.argv.filter(isGh)
  expect(calls.length).toBe(1)
  expect(calls[0].slice(0, 4)).toEqual(['gh', 'api', 'graphql', '-f'])
  expect(calls[0][4]).toContain('search(query: "is:pr is:open author:@me sort:updated-desc", type: ISSUE, first: 20)')
  expect(calls[0][4]).toContain('statusCheckRollup { state }')
  expect(await text(ui, /^your PRs 2$/)).toBeDefined()
  expect(await text(ui, /^here#4   ready  checks failing  Fix it$/)).toBeDefined()
  expect(await text(ui, /^there#9  draft  checks none     Draft one$/)).toBeDefined()
})

test('AC-3 the checks mapping', () => {
  expect(checksWord({ state: 'SUCCESS' })).toBe('ok')
  expect(checksWord({ state: 'FAILURE' })).toBe('failing')
  expect(checksWord({ state: 'ERROR' })).toBe('failing')
  expect(checksWord({ state: 'PENDING' })).toBe('pending')
  expect(checksWord({ state: 'EXPECTED' })).toBe('pending')
  expect(checksWord(null)).toBe('none')
  expect(checksWord(undefined)).toBe('none')
  expect(checksWord({ state: 'SOMETHING_NEW' })).toBe('?')
  expect(parsePrs('{"data": {}}')).toBeNull()
  expect(parsePrs('not json')).toBeNull()
})

test('AC-3 more than 20 open: a +k more on GitHub line from issueCount', async ($, on) => {
  const nodes = Array.from({ length: 20 }, (_, i) => node('r', i + 1, `pr ${i + 1}`, false, 'SUCCESS'))
  const { ui } = await openNow($, on, w => { w.gh.stdout = answer(nodes, 27) })
  expect(await text(ui, /^your PRs 27$/)).toBeDefined()
  expect(await text(ui, /\+7 more on GitHub$/)).toBeDefined()
})

test('AC-3 zero results: no open PRs', async ($, on) => {
  const { ui } = await openNow($, on, w => { w.gh.stdout = answer([]) })
  expect(await text(ui, /^your PRs 0$/)).toBeDefined()
  expect(await text(ui, /^no open PRs$/)).toBeDefined()
})

test('AC-3 a failed call after a good one keeps the list, marked stale since HH:MM with the error', async ($, on) => {
  const { w, ui } = await openNow($, on)
  w.gh = { exitCode: 1, stdout: '', stderr: 'gh: could not resolve host\n' }
  await ui.press({ key: 'k-r' })
  expect(await text(ui, /^stale since \d\d:\d\d: gh: could not resolve host$/)).toBeDefined()
  expect(await text(ui, /^here#4 /)).toBeDefined()
  expect(await text(ui, /^your PRs 2$/)).toBeDefined()
})

test('AC-3 before the first call ends: reading GitHub, and the count is ?', async ($, on) => {
  let release = () => {}
  const { ui } = await openNow($, on, w => { w.ghHold = new Promise<void>(r => { release = r }) })
  expect(await text(ui, /^reading GitHub$/)).toBeDefined()
  expect(await text(ui, /^your PRs \?$/)).toBeDefined()
  release()
  // the held call ends inside the test, so its write is not left running past it
  await ui.press({ key: 'k-p' })
})

test('AC-3 a first call that fails shows ? and the error, never no open PRs', async ($, on) => {
  const { ui } = await openNow($, on, w => { w.gh = { exitCode: 4, stdout: '', stderr: 'gh auth login required' } })
  expect(await text(ui, /^your PRs \?$/)).toBeDefined()
  expect(await text(ui, /^could not read GitHub \(gh auth login required\); r tries again$/)).toBeDefined()
  expect(await text(ui, /^no open PRs$/)).toBeUndefined()
})

// -- AC-4 -------------------------------------------------------------------------------------------------------------

test('AC-4 no GitHub call while closed or on Plan, then on open of Now, on r, and every 2 minutes on Now only', async ($, on) => {
  const h = await start($, on)
  await h.clock.advance(5 * 60_000)
  expect(ghCalls(h.w)).toBe(0)
  const ui = await openDash($, h)
  await h.clock.advance(5 * 60_000)
  expect(ghCalls(h.w)).toBe(0)
  await ui.press({ key: 'k-n' })
  await h.clock.advance(10)
  expect(ghCalls(h.w)).toBe(1)
  await h.clock.advance(time.prTick - 20_000)
  expect(ghCalls(h.w)).toBe(1)
  // the 2 minute check rides the 10 s panes tick, so it runs on the first tick past 2 minutes
  await h.clock.advance(20_000 + time.planTick)
  expect(ghCalls(h.w)).toBe(2)
  await ui.press({ key: 'k-r' })
  expect(ghCalls(h.w)).toBe(3)
  await ui.press({ key: 'k-p' })
  await ui.press({ key: 'k-r' })
  await h.clock.advance(5 * 60_000)
  expect(ghCalls(h.w)).toBe(3)
  await ui.press({ key: 'k-n' })
  expect(ghCalls(h.w)).toBe(4)
  await h.w.close()
  await h.clock.advance(5 * 60_000)
  expect(ghCalls(h.w)).toBe(4)
})

test('AC-4 closing the dashboard on Now stops the 2 minute search', async ($, on) => {
  const { w, clock } = await openNow($, on)
  expect(ghCalls(w)).toBe(1)
  await w.close()
  await clock.advance(5 * 60_000)
  expect(ghCalls(w)).toBe(1)
})

test('AC-4 reopening the dashboard left on Now runs the search at once', async ($, on) => {
  const { w, clock } = await openNow($, on)
  await w.close()
  await clock.advance(30_000)
  expect(ghCalls(w)).toBe(1)
  await $.command.run({ command: 'chip', args: '' } as any)
  // less than the panes' tick, so only the open's own search can have run
  await clock.advance(10)
  expect(ghCalls(w)).toBe(2)
})

// -- AC-5 -------------------------------------------------------------------------------------------------------------

test('AC-5 the handoff block says on with the line, off, or ? with the band\'s words, and the last handover link', async ($, on) => {
  const { w, clock, ui } = await openNow($, on, w => {
    w.files[`${AUTO}/S1.json`] = JSON.stringify({ root: 'S1', session: 'S1', line: 250000 })
    w.files[PANEL] = JSON.stringify({ session: 'S1', previous: 'S0', phase: 'idle', steps: [], result: null, sticky: false, link: 'http://x/handover', at: 1 })
  })
  expect(await text(ui, /^handoff on 250k$/)).toBeDefined()
  expect(await text(ui, /^last handover: http:\/\/x\/handover$/)).toBeDefined()
  w.files[`${AUTO}/S1.json`] = JSON.stringify({ root: 'S1', session: 'S1', off: true, line: 250000 })
  await clock.advance(time.bandTick)
  expect(await text(ui, /^handoff off$/)).toBeDefined()
  delete w.files[`${AUTO}/S1.json`]
  await clock.advance(time.bandTick)
  expect(await text(ui, /^handoff \?$/)).toBeDefined()
})

test('AC-5 a panel with no previous chat shows no handover link', async ($, on) => {
  const { ui } = await openNow($, on, w => {
    w.files[PANEL] = JSON.stringify({ session: 'S1', previous: null, phase: 'idle', steps: [], result: null, sticky: false, link: 'http://x/handover', at: 1 })
  })
  expect(await text(ui, /^last handover:/)).toBeUndefined()
})

// -- AC-6 -------------------------------------------------------------------------------------------------------------

test('AC-6 agents counts the running ones and the shells not stopped or finished; unknown is agents ?', async ($, on) => {
  const { w, ui } = await openNow($, on, w => {
    w.agents = [{ id: 'a1', status: 'running', type: 'x' }, { id: 'a2', status: 'completed', type: 'x' }, { id: 'a3', status: 'running', type: 'x' }]
    w.messages = [bash('s1'), bash('s2'), { role: 'assistant', text: '', toolUses: [{ tool_use_id: 't', tool: 'TaskStop', input: { task_id: 's2' }, text: 'stopped' }] }]
  })
  expect(await text(ui, /^agents 2 running, 1 shells$/)).toBeDefined()
  expect(await text(ui, /^a: details$/)).toBeDefined()
  w.agents = null
  await ui.press({ key: 'k-r' })
  expect(await text(ui, /^agents \?$/)).toBeDefined()
  w.agents = []
  w.messages = null
  await ui.press({ key: 'k-r' })
  expect(await text(ui, /^agents \?$/)).toBeDefined()
})

// -- AC-7 -------------------------------------------------------------------------------------------------------------

const facts = {
  model: 'claude-opus-5-5[1m]', effort: 'medium', folder: 'claude-config',
  git: { branch: 'main', changes: 0, staged: 0, modified: 0, untracked: 0 },
  context: 16, contextTokens: 160000, contextWindow: 1000000,
  fiveHour: 21, fiveHourReset: null, week: 45, weekReset: null, via: null, staleSince: null,
  handoff: { off: false, line: 200000 },
}
const owed = (lines: string[] | null) => ({ installed: true, lines, error: lines ? null : 'bad' })
const ids = (f: any, columns: number) => { const { left, right } = segments(f, 0, false); return fit(left, right, columns).map(s => s.id) }

test('AC-7 the band shows owed N in warn bold when this chat owes; nothing at 0, when missing or unreadable', () => {
  const seg = segments({ ...facts, owed: owed(['a', 'b']) }, 0, false).left.find(s => s.id === 'owed')!
  expect(seg.runs).toEqual([{ text: 'owed 2', color: 'warning', bold: true }])
  for (const o of [owed([]), owed(null), { installed: false, lines: null, error: null }, undefined]) {
    const all = segments({ ...facts, owed: o } as any, 0, false)
    expect([...all.left, all.right].flatMap(s => s.runs.map(r => r.text)).join(' ')).not.toMatch(/owed/)
  }
})

test('AC-7 owed is the last segment to drop and stays in the compact band beside the docked dashboard', () => {
  const f = { ...facts, owed: owed(['a']) }
  const { left, right } = segments(f, 0, false)
  const chip = left.find(s => s.id === 'chip')!.cells
  const o = left.find(s => s.id === 'owed')!.cells
  // room for the chip, owed and the handoff state, not the model too
  expect(ids(f, chip + o + right.cells + 2 * space.gap + 2 * space.padX)).toEqual(['chip', 'owed'])
  const room = 31 - space.hostReserve - space.hotkeyCells
  const compact = segments(f, 0, false, true, 0)
  expect(fit(compact.left, compact.right, room).map(s => s.id)).toEqual(['chip', 'owed'])
  expect(fit(compact.left, compact.right, 10).map(s => s.id)).toEqual(['chip', 'owed'])
})

test('AC-7 the band tick reads this chat\'s owed file into the facts the band draws', async ($, on) => {
  const h = await start($, on, w => { w.dirs.add(CATCH); w.files[`${CATCH}/S1.json`] = JSON.stringify({ owed: ['x', 'y', 'z'] }) })
  const props = { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 160 }
  let ui = await $.ui.mount({ plugin: 'chip-dash', surface: 'terminal', component: 'AbovePrompt', props } as never)
  expect(await text(ui, /^owed 3$/)).toBeDefined()
  await ui.unmount()
  h.w.files[`${CATCH}/S1.json`] = JSON.stringify({ owed: [] })
  await h.clock.advance(time.bandTick)
  ui = await $.ui.mount({ plugin: 'chip-dash', surface: 'terminal', component: 'AbovePrompt', props } as never)
  expect(await text(ui, /owed/)).toBeUndefined()
  await ui.unmount()
})

// -- AC-8, AC-9 -------------------------------------------------------------------------------------------------------

test('AC-9 more owed lines than the block holds end in and k more', () => {
  const lines = owedLines(owed(['a', 'b', 'c', 'd']))
  expect(lines.map(l => l.t)).toEqual(['owed 4', 'a', 'and 3 more'])
  expect(owedLines(owed(['a', 'b'])).map(l => l.t)).toEqual(['owed 2', 'a', 'b'])
})

test('AC-8 AC-9 more PRs than the block holds: +k more, and j moves the cursor and scrolls the list', async ($, on) => {
  const nodes = Array.from({ length: 8 }, (_, i) => node('r', i + 1, `pr ${i + 1}`, false, 'SUCCESS'))
  const { ui } = await openNow($, on, w => { w.gh.stdout = answer(nodes) })
  // 6 rows: the heading, 4 PRs, the more line
  expect(await text(ui, /^r#4 /)).toBeDefined()
  expect(await text(ui, /^r#5 /)).toBeUndefined()
  expect(await text(ui, /^\+4 more$/)).toBeDefined()
  expect((await ui.find({ key: 'k-k' }))?.props?.dimColor).toBe(true)
  for (let i = 0; i < 5; i++) await ui.press({ key: 'k-j' })
  expect(await text(ui, /^r#6 /)).toBeDefined()
  expect(await text(ui, /^r#1 /)).toBeUndefined()
  expect(await text(ui, /^2 above, \+2 more$/)).toBeDefined()
  expect((await ui.find({ key: 'k-k' }))?.props?.dimColor).toBe(false)
})
