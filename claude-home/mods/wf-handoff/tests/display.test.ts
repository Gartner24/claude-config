import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'
import { addNext, renderPage } from '../pages.ts'

// Spec 0064: what the handoff shows: panel.json for the band, toasts where no band draws,
// a page per handover, the page server's bind rule and the link back.
const SLOT = '/h/.claude/projects/-w/rollover/session.md'
const STATE = '/h/.claude/state/auto-handoff'
const SLOT_TEXT = '# Rollover handover\nNext: <b>finish</b> & ship.\n## Last request from the owner\n> fix it\nStatus: answered\n'

function world(on: On, o: { tailscale?: string; answers?: Record<string, string>; cmdline?: string; band?: boolean; surfaces?: string[]; noSlot?: boolean; token?: string; spawnSays?: string } = {}) {
  const clock = mock.clock(on, { now: 1_000_000 })
  mock.env(on, { HOME: '/h' })
  const w = {
    clock,
    files: new Map<string, { text: string; mtimeMs: number }>(),
    tokens: 10_000 as number | undefined,
    id: 'S1aaaaaa-1111',
    commands: [] as string[],
    toasts: [] as { text: string; timeoutMs?: number }[],
    spawned: [] as string[][],
    killed: [] as string[],
    fetched: [] as string[],
    panels: [] as any[],
  }
  // the token our server wrote at its start
  if (o.token) w.files.set(`${STATE}/server.token`, { text: `${o.token}\n`, mtimeMs: 0 })
  on('session.cwd', () => ({ value: '/w' }))
  on('session.id', () => ({ value: w.id }))
  on('session.surfaces', () => ({ value: (o.surfaces ?? ['terminal']) as any }))
  on('session.usage', () => ({ value: { startedAt: 0, context: { tokens: w.tokens, window: 1_000_000 }, rateLimits: [] } as any }))
  on('session.messages', () => ({ value: [] as any }))
  on('state.get', (_$, e: any) => e.plugin === 'chip-dash'
    ? { value: { value: o.band ? {} : undefined, version: o.band ? 3 : 0 } as any }
    : undefined as any)
  on('command.register', (_$, e: any) => ({ value: { command: e.name } }))
  on('ui.toast', (_$, e: any) => { w.toasts.push({ text: e.text, timeoutMs: e.timeoutMs }); return { value: undefined } })
  on('ui.status', () => ({ value: undefined }))
  on('fs.read', (_$, e: any) => {
    if (e.path.startsWith('/proc/')) return { value: o.cmdline ?? '' }
    const f = w.files.get(e.path) ?? (e.path.includes('/templates/') ? { text: 'TEMPLATE {{lastRequest}}', mtimeMs: 0 } : undefined)
    if (!f) throw new Error(`ENOENT ${e.path}`)
    return { value: f.text }
  })
  on('fs.write', (_$, e: any) => {
    w.files.set(e.path, { text: e.text, mtimeMs: clock.now() })
    if (e.path.endsWith('/panel.json')) w.panels.push(JSON.parse(e.text))
    return { value: undefined }
  })
  on('fs.stat', (_$, e: any) => {
    const f = w.files.get(e.path)
    if (!f) throw new Error(`ENOENT ${e.path}`)
    return { value: { kind: 'file', size: f.text.length, mtimeMs: f.mtimeMs, isLink: false } }
  })
  on('fs.list', () => ({ value: [] }))
  const ran = (exitCode: number, stdout = '') => ({ value: { exitCode, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } })
  on('process.run', (_$, e: any) => {
    if (e.argv[0] === 'tailscale') return o.tailscale ? ran(0, `${o.tailscale}\n`) : ran(1)
    if (e.argv[0] === 'kill') { w.killed.push(e.argv[1]); return ran(0) }
    // stands for server.py --probe HOST PORT TOKEN_FILE NONCE, whose HMAC check has its own self test
    // (server.py --test): ours only when the listener signs with the token in the token file
    if (e.argv[2] === '--probe') {
      w.fetched.push(`http://${e.argv[3]}:${e.argv[4]}/__wf-handoff?n=${e.argv[6]}`)
      expect(e.argv[5]).toBe(`${STATE}/server.token`)
      const a = o.answers?.[e.argv[3]]
      if (a === undefined) return ran(0, '{"state":"none"}')
      const j = (() => { try { return JSON.parse(a) } catch { return null } })()
      const tok = w.files.get(`${STATE}/server.token`)?.text.trim()
      const ours = j?.server === 'wf-handoff' && tok && j.signWith === tok
      return ran(0, JSON.stringify(ours ? { state: 'ours', bind: j.bind, pid: j.pid } : { state: 'foreign' }))
    }
    return w.files.has(SLOT) ? ran(0, `${SLOT}\n`) : ran(1)
  })
  on('process.spawn', async function* (_$, e: any) {
    w.spawned.push([...e.argv])
    if (o.spawnSays) yield { stream: 'stdout', text: o.spawnSays } as any
    return { value: { code: 0, signal: null } } as any
  })
  on('command.run', (_$, e: any) => {
    w.commands.push(e.command)
    if (e.command === 'rollover' && !o.noSlot) {
      clock.advance(5)
      w.files.set(SLOT, { text: SLOT_TEXT, mtimeMs: clock.now() + 10 })
    }
    if (e.command === 'clear') w.id = w.id === 'S1aaaaaa-1111' ? 'S2bbbbbb-2222' : 'S3cccccc-3333'
    return { text: '' }
  })
  on('prompt.submit', (_$, e: any) => ({ text: e.text }))
  on('tool.call', () => ({ result: 'ok', text: '' } as any))
  on('turn.step', async function* (_$, e: any) {
    return { turnId: e.turnId, index: e.index, answer: 'a', toolUses: [], stopReason: 'end_turn', usage: null } as any
  })
  on('turn.complete', () => ({ text: '' }))
  on('session.start', (_$, e: any) => ({ cwd: e.cwd }))
  on('session.end', (_$, e: any) => ({ sessionId: e.sessionId }))
  return w
}

const start = async ($: any, w: ReturnType<typeof world>) => {
  await $.session.start({ cwd: '/w', surface: 'terminal', isInteractive: true })
  await w.clock.settle()
}
async function step($: any, turnId: string) {
  const s = $.turn.step({ turnId, index: 0, model: 'm', messageCount: 1 })
  let x = await s.next()
  while (!x.done) x = await s.next()
}
const complete = ($: any, turnId: string) => $.turn.complete({ turnId, answer: '', durationMs: 1, reason: 'answer' })
// One whole handoff: the trigger turn, the rollover turn, the clear, then the fresh chat's first reply.
async function handoff($: any, w: ReturnType<typeof world>, n: number, fresh = 95_000) {
  w.tokens = 210_000
  await complete($, `T${n}`)
  await w.clock.settle()
  await complete($, `T${n}r`)
  await w.clock.advance(1500)
  w.tokens = fresh
  await step($, `T${n}f`)
}
const states = (p: any) => p.steps.map((s: any) => s.state).join(' ')
const chainOf = (w: ReturnType<typeof world>) => JSON.parse(w.files.get(`${STATE}/S1aaaaaa-1111.json`)!.text)

test('AC-1 AC-6 panel.json walks the three steps, then the result and the link', { options: { threshold: 200000 } }, async ($, on) => {
  const w = world(on)
  await start($, w)
  await handoff($, w, 1)
  const ps = w.panels
  expect(ps[0].steps.map((s: any) => s.label)).toEqual(['writing the handover', 'clearing', 'starting the fresh chat'])
  expect(ps.map(p => `${p.phase}: ${states(p)}`)).toEqual([
    'gated: pending pending pending',
    'rolling: running pending pending',
    'clearing: done running pending',
    'seeding: done done running',
    'idle: done done running',
    'idle: done done done',
  ])
  const last = ps.at(-1)
  expect(last).toMatchObject({ session: 'S2bbbbbb-2222', previous: 'S1aaaaaa-1111', result: 'handed off · 210k -> 95k', sticky: false })
  expect(last.link).toMatch(/^http:\/\/127\.0\.0\.1:3846\/S1aaaaaa-[0-9a-f]{16}$/)
  expect(ps[2].session).toBe('S1aaaaaa-1111') // written before the clear, under the old id
  expect(chainOf(w).link).toBe(last.link)
  expect(chainOf(w).pageKey).toBe(last.link.slice(-16))
  expect(w.files.get(SLOT)!.text).toContain(`viewer: ${last.link}`)
})

test('AC-1 AC-2 a missing slot leaves a sticky failed step until the owner types', { options: { threshold: 200000 } }, async ($, on) => {
  const w = world(on, { noSlot: true })
  await start($, w)
  w.tokens = 210_000
  await complete($, 'T1')
  await w.clock.settle()
  await complete($, 'T1r')
  const failed = w.panels.at(-1)
  expect(failed).toMatchObject({ phase: 'failed', sticky: true })
  expect(states(failed)).toBe('failed pending pending')
  expect(failed.result).toContain('auto handoff failed: the rollover wrote no new handover')
  await $.prompt.submit({ text: 'ok', wait: false, origin: { kind: 'composer' } })
  expect(w.panels.at(-1)).toMatchObject({ phase: 'idle', sticky: false, result: null })
})

test('AC-3 with no band the start, the result and a sticky line are toasts, sticky for 30 s', { options: { threshold: 200000, maxConsecutiveHandoffs: 1 } }, async ($, on) => {
  const w = world(on)
  await start($, w)
  await handoff($, w, 1, 45_000)
  expect(w.toasts[0]!.text).toBe('auto handoff started: writing the handover')
  expect(w.toasts[1]!.text).toMatch(/^handed off · 210k -> 45k · http:\/\/127\.0\.0\.1:3846\/S1aaaaaa-[0-9a-f]{16}$/)
  w.tokens = 300_000
  await $.tool.call({ tool: 'Read', file_path: '/w/a' } as any)
  expect(w.toasts.at(-1)).toEqual({ text: 'auto handoff paused: type anything to resume', timeoutMs: 30000 })
})

test('AC-3 the chip-dash band in the terminal takes the place of the toasts', { options: { threshold: 200000 } }, async ($, on) => {
  const w = world(on, { band: true })
  await start($, w)
  await handoff($, w, 1)
  expect(w.toasts).toEqual([])
})

test('AC-3 a surface that draws no band gets the toasts even with chip-dash loaded', { options: { threshold: 200000 } }, async ($, on) => {
  const w = world(on, { band: true, surfaces: ['terminal', 'mobile'] })
  await start($, w)
  await handoff($, w, 1)
  expect(w.toasts.map(t => t.text)[0]).toBe('auto handoff started: writing the handover')
})

test('AC-4 each handover gets an escaped page, linked to the one before and after', { options: { threshold: 200000, minHeadroom: 1000, maxConsecutiveHandoffs: 5 } }, async ($, on) => {
  const w = world(on)
  await start($, w)
  await handoff($, w, 1)
  const first = w.files.get(`${STATE}/pages/S1aaaaaa-1111.html`)!.text
  const link1 = chainOf(w).link
  expect(first).toContain(`<meta name="wf-handoff-key" content="${link1.slice(-16)}">`)
  expect(first).toContain('&lt;b&gt;finish&lt;/b&gt; &amp; ship.')
  expect(first).not.toContain('<b>finish')
  expect(first).toContain('first handover of this chain')
  expect(first).not.toContain('next handover')
  await handoff($, w, 2)
  const link2 = chainOf(w).link
  expect(link2).toMatch(/\/S2bbbbbb-[0-9a-f]{16}$/)
  const second = w.files.get(`${STATE}/pages/S2bbbbbb-2222.html`)!.text
  expect(second).toContain(`<a href="${link1}">previous handover</a>`)
  expect(w.files.get(`${STATE}/pages/S1aaaaaa-1111.html`)!.text).toContain(`<a href="${link2}">next handover</a>`)
})

test('AC-4 renderPage escapes every slot line and addNext fills the next link once', () => {
  const html = renderPage('# A <x>\n"q" \'s\'', { key: 'k', title: 't<', prev: 'http://h/"x' })
  expect(html).toContain('<h1>A &lt;x&gt;</h1>')
  expect(html).toContain('<p>&quot;q&quot; &#39;s&#39;</p>')
  expect(html).toContain('<title>t&lt;</title>')
  expect(html).toContain('<a href="http://h/&quot;x">previous handover</a>')
  const once = addNext(html, 'http://n')
  expect(once).toContain('<a href="http://n">next handover</a>')
  expect(addNext(once, 'http://other')).not.toContain('http://other')
})

test('AC-5 with no Tailscale the server binds 127.0.0.1 only', async ($, on) => {
  const w = world(on)
  await start($, w)
  expect(w.spawned.length).toBe(1)
  expect(w.spawned[0]!.slice(1)).toEqual([expect.stringMatching(/server\.py$/), '--bind', '127.0.0.1', '--port', '3846', '--dir', `${STATE}/pages`, '--token-file', `${STATE}/server.token`] as any)
})

test('AC-5 with Tailscale up the server binds its IPv4 address and the link uses it', { options: { threshold: 200000 } }, async ($, on) => {
  const w = world(on, { tailscale: '100.88.1.2' })
  await start($, w)
  expect(w.spawned[0]).toContain('100.88.1.2')
  expect(w.spawned[0]).not.toContain('127.0.0.1')
  await handoff($, w, 1)
  expect(chainOf(w).link).toMatch(/^http:\/\/100\.88\.1\.2:3846\//)
})

test('AC-5 a Tailscale answer that is not a 100.x address falls back to loopback', async ($, on) => {
  const w = world(on, { tailscale: '0.0.0.0' })
  await start($, w)
  expect(w.spawned[0]).toContain('127.0.0.1')
  expect(w.spawned[0]).not.toContain('0.0.0.0')
})

const OURS = (bind: string, token = 'T0K') => JSON.stringify({ server: 'wf-handoff', bind, pid: 42, signWith: token })

test('AC-5 a server of ours on the same address is left alone and its address is the link', { options: { threshold: 200000 } }, async ($, on) => {
  const w = world(on, { token: 'T0K', answers: { '127.0.0.1': OURS('127.0.0.1') } })
  await start($, w)
  expect(w.spawned).toEqual([])
  expect(w.killed).toEqual([])
  await handoff($, w, 1)
  expect(chainOf(w).link).toMatch(/^http:\/\/127\.0\.0\.1:3846\/S1aaaaaa-/)
})

test('AC-5 when Tailscale came up, our loopback server is stopped and a new one starts', async ($, on) => {
  const w = world(on, { token: 'T0K', tailscale: '100.88.1.2', cmdline: 'python3\0/h/.claude/skills/wf-handoff/server.py\0--bind', answers: { '127.0.0.1': OURS('127.0.0.1') } })
  await start($, w)
  expect(w.fetched.map(u => new URL(u).host)).toEqual(['100.88.1.2:3846', '127.0.0.1:3846'])
  expect(w.killed).toEqual(['42'])
  expect(w.spawned[0]).toContain('100.88.1.2')
})

test('AC-5 a pid that is not our server is never killed', async ($, on) => {
  const w = world(on, { token: 'T0K', tailscale: '100.88.1.2', cmdline: 'nginx', answers: { '127.0.0.1': OURS('127.0.0.1') } })
  await start($, w)
  expect(w.killed).toEqual([])
  expect(w.spawned).toEqual([])
})

test('AC-5 a port taken by something else is left alone with one log line', async ($, on) => {
  const w = world(on, { answers: { '127.0.0.1': '<html>other app</html>' } })
  await start($, w)
  expect(w.spawned).toEqual([])
  expect(w.files.get(`${STATE}/auto-handoff.log`)!.text.match(/taken by something else/g)!.length).toBe(1)
})

test('AC-5 a listener that says it is ours without our token gets no kill, no traffic, and file links', { options: { threshold: 200000 } }, async ($, on) => {
  const w = world(on, { token: 'T0K', tailscale: '100.88.1.2', cmdline: 'python3\0/x/wf-handoff/server.py', answers: { '127.0.0.1': OURS('127.0.0.1', 'FAKE') } })
  await start($, w)
  expect(w.killed).toEqual([])
  expect(w.spawned).toEqual([])
  await handoff($, w, 1)
  expect(chainOf(w).link).toBe(`file://${STATE}/pages/S1aaaaaa-1111.html`)
})

test('AC-5 a replayed answer does not pass: each probe sends a fresh nonce', async ($, on) => {
  // a recorded answer: right server name, a mac of some earlier nonce, no signature with our token
  const w = world(on, { token: 'T0K', answers: { '127.0.0.1': JSON.stringify({ server: 'wf-handoff', bind: '127.0.0.1', pid: 42, mac: 'recorded-from-an-old-nonce' }) } })
  await start($, w)
  expect(w.fetched[0]).toMatch(/\/__wf-handoff\?n=[0-9a-f]{16}$/)
  expect(w.files.get(`${STATE}/auto-handoff.log`)!.text).toContain('taken by something else')
  await $.session.start({ cwd: '/w', surface: 'terminal', isInteractive: true })
  await w.clock.settle()
  expect(w.fetched.length).toBe(2)
  expect(w.fetched[1]).not.toBe(w.fetched[0]) // a fresh nonce on every probe
})

test('AC-5 a port taken between the probe and the bind gives file links, never links to that listener', { options: { threshold: 200000 } }, async ($, on) => {
  const w = world(on, { spawnSays: 'port 3846 on 127.0.0.1 not free (Address already in use)\n' })
  await start($, w)
  expect(w.spawned.length).toBe(1)
  await handoff($, w, 1)
  expect(chainOf(w).link).toBe(`file://${STATE}/pages/S1aaaaaa-1111.html`)
  expect(w.files.get(`${STATE}/auto-handoff.log`)!.text).toContain('server: port 3846 on 127.0.0.1 not free')
})

test('AC-5 a blank viewer means no server and a file link', { options: { threshold: 200000, viewer: '' } }, async ($, on) => {
  const w = world(on)
  await start($, w)
  expect(w.spawned).toEqual([])
  expect(w.fetched).toEqual([])
  await handoff($, w, 1)
  expect(chainOf(w).link).toBe(`file://${STATE}/pages/S1aaaaaa-1111.html`)
})

test('AC-5 viewer 127.0.0.1:4000 keeps loopback even with Tailscale up', { options: { viewer: '127.0.0.1:4000' } }, async ($, on) => {
  const w = world(on, { tailscale: '100.88.1.2' })
  await start($, w)
  expect(w.spawned[0]!.slice(2, 6)).toEqual(['--bind', '127.0.0.1', '--port', '4000'])
})
