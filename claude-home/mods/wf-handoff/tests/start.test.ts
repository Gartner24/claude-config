import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'
import { FIXTURE } from './start-cases.ts'
// Spec 0070 AC-1 to AC-3: a chat in a git repo starts /audit then /scope, or /scope, by itself.
const STATE = '/h/.claude/state/auto-handoff'
const SLOT = '/h/.claude/projects/-w/rollover/session.md'

function world(on: On, env: Record<string, string> = {}) {
  const clock = mock.clock(on, { now: 1_000_000 })
  mock.env(on, { HOME: '/h', ...env })
  const w = {
    clock,
    files: new Map<string, string>(),
    id: 'S1',
    top: '/w' as string | null, // `git rev-parse --show-toplevel`, null for no repo
    origin: 'git@github.com:me/own.git',
    commands: [] as string[],
  }
  on('session.cwd', () => ({ value: '/w' }))
  on('session.id', () => ({ value: w.id }))
  on('session.usage', () => ({ value: { startedAt: 0, context: { tokens: 1000, window: 1_000_000 }, rateLimits: [] } as any }))
  on('session.messages', () => ({ value: [] as any }))
  on('command.register', (_$, e: any) => ({ value: { command: e.name } }))
  on('ui.toast', () => ({ value: undefined }))
  on('ui.status', () => ({ value: undefined }))
  on('fs.read', (_$, e: any) => {
    const f = w.files.get(e.path) ?? (e.path.includes('/templates/') ? 'T' : undefined)
    if (f === undefined) throw new Error(`ENOENT ${e.path}`)
    return { value: f }
  })
  on('fs.write', (_$, e: any) => { w.files.set(e.path, e.text); return { value: undefined } })
  on('fs.stat', (_$, e: any) => {
    const hit = [...w.files.keys()].some(k => k === e.path || k.startsWith(e.path + '/'))
    if (!hit) throw new Error(`ENOENT ${e.path}`)
    return { value: { kind: 'file', size: 1, mtimeMs: 0, isLink: false } }
  })
  on('fs.list', () => ({ value: [] }))
  const out = (exitCode: number, stdout = '') => ({ value: { exitCode, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } })
  on('process.run', (_$, e: any) => {
    const a = e.argv as string[]
    if (a[0] === 'git' && a[4] === '--show-toplevel') return w.top ? out(0, `${w.top}\n`) : out(128)
    if (a[0] === 'git' && a[3] === 'remote') return w.origin ? out(0, `${w.origin}\n`) : out(2)
    if (a[0] === 'realpath') return out(0, `${a.at(-1)}\n`)
    if (a[0].endsWith('jjstack-rollover-slot')) return w.files.has(SLOT) ? out(0, `${SLOT}\n`) : out(1)
    return out(1)
  })
  on('process.spawn', async function* () { return { value: { code: 0, signal: null } } as any })
  on('command.run', (_$, e: any) => { w.commands.push(e.command); return { text: '' } })
  on('prompt.submit', (_$, e: any) => ({ text: e.text }))
  on('turn.complete', () => ({ text: '' }))
  on('session.start', (_$, e: any) => ({ cwd: e.cwd }))
  on('session.end', (_$, e: any) => ({ sessionId: e.sessionId }))
  return w
}

const start = async ($: any, w: ReturnType<typeof world>, interactive = true) => {
  await $.session.start({ cwd: '/w', surface: interactive ? 'terminal' : null, isInteractive: interactive })
  await w.clock.settle()
}
const complete = ($: any, turnId: string) => $.turn.complete({ turnId, answer: '', durationMs: 1, reason: 'answer' })
const typed = ($: any, text: string) => $.prompt.submit({ text, wait: false, origin: { kind: 'composer' } })
const chain = (w: ReturnType<typeof world>, root: string) => JSON.parse(w.files.get(`${STATE}/${root}.json`)!)

test('AC-1 no AGENTS.md: /audit at chat start, then /scope when that turn completes', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  await start($, w)
  expect(w.commands).toEqual(['audit'])
  await complete($, 'T1')
  await w.clock.settle()
  expect(w.commands).toEqual(['audit', 'scope'])
  await complete($, 'T2')
  expect(w.commands).toEqual(['audit', 'scope'])
  expect(chain(w, 'S1').startedFor).toBe('S1')
})

test('AC-1 the owner typing before the queued /scope drops it', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  await start($, w)
  await typed($, 'actually, fix the login first')
  await complete($, 'T1')
  await w.clock.settle()
  expect(w.commands).toEqual(['audit'])
})

test('AC-2 AGENTS.md: /scope at chat start', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  w.files.set('/w/AGENTS.md', '# w')
  await start($, w)
  expect(w.commands).toEqual(['scope'])
})

test('AC-2 a folder that is not a git repo gets nothing', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  w.top = null
  await start($, w)
  expect(w.commands).toEqual([])
})

test('AC-2 a bot reviewed origin never gets /audit; /scope only with a scope folder', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  w.files.set('/h/.claude/private/work.md', '- origin under `github.com:team-org/` or `github.com:other-org/`: no local review')
  w.origin = 'https://github.com/Team-Org/site.git'
  await start($, w)
  expect(w.commands).toEqual([])
  w.id = 'S2'
  w.files.set('/w/.workflow/scope/scope.md', '# s')
  await start($, w)
  expect(w.commands).toEqual(['scope'])
  await complete($, 'T1')
  expect(w.commands).toEqual(['scope'])
})

test('AC-3 a live handover slot: no /audit or /scope', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  w.files.set(SLOT, 'handover')
  await start($, w)
  expect(w.commands).toEqual([])
})

// The same cases drive workflow-start.sh --test: the hook stays quiet exactly where these start a skill.
for (const c of FIXTURE.cases) {
  test(`AC-2 AC-3 shared case: ${c.name}`, { options: { viewer: '' } }, async ($, on) => {
    const w = world(on)
    w.files.set('/h/.claude/private/work.md', FIXTURE.work)
    w.origin = c.origin
    if (!c.repo) w.top = null
    if (c.agents) w.files.set('/w/AGENTS.md', '# w')
    // both scope folders are read: docs/ when the repo has AGENTS.md, .workflow/ when it has not
    if (c.scope) w.files.set(c.agents ? '/w/docs/scope/scope.md' : '/w/.workflow/scope/scope.md', '# s')
    if (c.slot) w.files.set(SLOT, 'handover')
    await start($, w)
    expect(w.commands).toEqual(c.start ? [c.start] : [])
  })
}

test('AC-1 once per chat id: a reload of the mod starts nothing again', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  w.files.set('/w/AGENTS.md', '# w')
  await start($, w)
  await start($, w)
  expect(w.commands).toEqual(['scope'])
})

test('AC-1 a chat already open when this mod version loads (its chain has no start record) starts nothing', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  w.files.set('/w/AGENTS.md', '# w')
  w.files.set(`${STATE}/S1.json`, JSON.stringify({ root: 'S1', session: 'S1', previous: null, startTokens: null, unattended: 0, triggeredAt: null, phase: 'idle', lastRequest: null }))
  await start($, w)
  expect(w.commands).toEqual([])
})

test('AC-1 an owner /clear starts the new chat from a timer, keyed by its new id, once', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  w.files.set('/w/AGENTS.md', '# w')
  await start($, w)
  await complete($, 'T1')
  // probe (d): inside session.end the host still answers the old id
  await $.session.end({ sessionId: 'S1', reason: 'clear' } as any)
  w.id = 'S2'
  expect(w.commands).toEqual(['scope'])
  await w.clock.advance(600)
  expect(w.commands).toEqual(['scope', 'scope'])
  expect(chain(w, 'S2')).toMatchObject({ root: 'S2', session: 'S2', startedFor: 'S2' })
  await start($, w) // a reload in the cleared chat
  expect(w.commands).toEqual(['scope', 'scope'])
})

test('AC-3 an owner /clear with a handover waiting starts nothing', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  w.files.set('/w/AGENTS.md', '# w')
  await start($, w)
  w.files.set(SLOT, 'handover')
  await $.session.end({ sessionId: 'S1', reason: 'clear' } as any)
  w.id = 'S2'
  await w.clock.advance(600)
  expect(w.commands).toEqual(['scope'])
})

for (const env of [{ WF_RUN: '1' }, { TM_WORKER_NAME: 'w1' }] as Record<string, string>[]) {
  test(`AC-1 nothing starts with ${Object.keys(env)[0]}`, { options: { viewer: '' } }, async ($, on) => {
    const w = world(on, env)
    await start($, w)
    expect(w.commands).toEqual([])
  })
}

test('AC-1 nothing starts headless', { options: { viewer: '' } }, async ($, on) => {
  const w = world(on)
  await start($, w, false)
  expect(w.commands).toEqual([])
})
