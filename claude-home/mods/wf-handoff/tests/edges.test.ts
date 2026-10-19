import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'

// Spec 0063: edge cases beyond auto.test.ts, first written as /check verify checks, same in-memory world.
const SLOT = '/h/.claude/projects/-w/rollover/session.md'
const STATE = '/h/.claude/state/auto-handoff'
const BASE_SLOT = '# Rollover handover\nNext: finish the gate. Context was 210k tokens.\n## Last request from the owner\n> fix it\nStatus: not answered\n'

function world(on: On, env: Record<string, string> = {}) {
  const clock = mock.clock(on, { now: 1_000_000 })
  mock.env(on, { HOME: '/h', ...env })
  const w = {
    clock,
    files: new Map<string, { text: string; mtimeMs: number }>(),
    tokens: 10_000 as number | undefined,
    id: 'S1',
    commands: [] as { command: string; args: string }[],
    toasts: [] as string[],
    status: undefined as string | undefined,
    messages: [] as unknown[],
    slotText: BASE_SLOT,
    clearMode: 'ok' as 'ok' | 'reject',
    resumeRejects: false,
    noSlotWrite: false,
    sent: 0,
    resent: [] as string[],
  }
  on('session.cwd', () => ({ value: '/w' }))
  on('session.id', () => ({ value: w.id }))
  on('session.usage', () => ({ value: { startedAt: 0, context: { tokens: w.tokens, window: 1_000_000 }, rateLimits: [] } as any }))
  on('session.messages', () => ({ value: w.messages as any }))
  on('command.register', (_$, e: any) => ({ value: { command: e.name } }))
  on('ui.toast', (_$, e: any) => { w.toasts.push(e.text); return { value: undefined } })
  on('ui.status', (_$, e: any) => { w.status = e.text; return { value: undefined } })
  on('fs.read', (_$, e: any) => {
    const f = w.files.get(e.path) ?? (e.path.includes('/templates/') ? { text: `TEMPLATE ${e.path.split('/').pop()} {{lastRequest}} {{#priority}}FIRST{{/priority}}{{^priority}}GO-ON{{/priority}}`, mtimeMs: 0 } : undefined)
    if (!f) throw new Error(`ENOENT ${e.path}`)
    return { value: f.text }
  })
  on('fs.write', (_$, e: any) => { w.files.set(e.path, { text: e.text, mtimeMs: clock.now() }); return { value: undefined } })
  on('fs.stat', (_$, e: any) => {
    const f = w.files.get(e.path)
    if (!f) throw new Error(`ENOENT ${e.path}`)
    return { value: { kind: 'file', size: f.text.length, mtimeMs: f.mtimeMs, isLink: false } }
  })
  on('fs.list', (_$, e: any) => ({ value: [...w.files.keys()].filter(k => k.startsWith(e.path + '/')).map(k => ({ name: k.slice(e.path.length + 1), kind: 'file' })) as any }))
  on('process.run', () => ({ value: w.files.has(SLOT)
    ? { exitCode: 0, stdout: `${SLOT}\n`, stderr: '', isStdoutTruncated: false, isStderrTruncated: false }
    : { exitCode: 1, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('command.run', (_$, e: any) => {
    w.commands.push({ command: e.command, args: e.args })
    if (e.command === 'rollover' && !w.noSlotWrite) {
      clock.advance(5)
      w.files.set(SLOT, { text: w.slotText, mtimeMs: clock.now() + 10 })
    }
    if (e.command === 'clear') {
      if (w.clearMode === 'reject') throw new Error('clear broke')
      w.id = w.id === 'S1' ? 'S2' : w.id === 'S2' ? 'S3' : 'S4'
    }
    if (e.command === 'resume-from-clear' && w.resumeRejects) throw new Error('seed broke')
    return { text: '' }
  })
  on('prompt.submit', (_$, e: any) => { if (e.origin.kind === 'plugin') w.resent.push(e.text); return { text: e.text } })
  on('tool.call', () => ({ result: 'ok', text: 'x'.repeat(400) } as any))
  on('turn.step', async function* (_$, e: any) {
    w.sent++
    return { turnId: e.turnId, index: e.index, answer: 'a', toolUses: [], stopReason: 'end_turn', usage: null } as any
  })
  on('turn.complete', () => ({ text: '' }))
  on('session.start', (_$, e: any) => ({ cwd: e.cwd }))
  on('session.end', (_$, e: any) => ({ sessionId: e.sessionId }))
  return w
}

const start = ($: any) => $.session.start({ cwd: '/w', surface: 'terminal', isInteractive: true })
const typed = ($: any, text: string, turnId?: string) => $.prompt.submit({ text, wait: false, origin: { kind: 'composer' }, ...(turnId ? { turnId } : {}) })
async function step($: any, turnId: string, index: number, agentId?: string) {
  const s = $.turn.step({ turnId, index, model: 'm', messageCount: 1, ...(agentId ? { agentId } : {}) })
  let x = await s.next()
  while (!x.done) x = await s.next()
  return x.value
}
const complete = ($: any, turnId: string, agentId?: string) => $.turn.complete({ turnId, answer: '', durationMs: 1, reason: 'answer', ...(agentId ? { agentId } : {}) })
const chain = (w: ReturnType<typeof world>, root = 'S1') => JSON.parse(w.files.get(`${STATE}/${root}.json`)!.text)
const read = ($: any, agentId?: string) => $.tool.call({ tool: 'Read', file_path: '/w/a', ...(agentId ? { agentId } : {}) } as any)
const names = (w: ReturnType<typeof world>) => w.commands.map(c => c.command)
const blockBytes = (slot: string) => new TextEncoder().encode(slot.slice(slot.indexOf('## Handoff facts'), slot.indexOf('Next: finish the gate'))).length
async function handoff($: any, w: ReturnType<typeof world>, turn: string) {
  await complete($, turn)
  await w.clock.settle()
  await complete($, `${turn}r`)
  await w.clock.advance(1500)
}

test('AC-1 AC-11 subagent events never gate, end a turn or hand off', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  w.tokens = 60_000
  expect(((await read($, 'A1')) as any).deny).toBeUndefined()
  await step($, 'T1', 1, 'A1')
  expect(w.sent).toBe(1)
  await complete($, 'T1', 'A1')
  expect(w.commands).toEqual([])
})

test('AC-4 ignoreFiles leaves matching paths out of the facts', { options: { threshold: 50000, ignoreFiles: 'dist/**,*.lock' } }, async ($, on) => {
  const w = world(on)
  await start($)
  w.messages = [{ role: 'assistant', text: '', toolUses: [
    { tool_use_id: '1', tool: 'Edit', input: { file_path: '/w/src/x.ts' } },
    { tool_use_id: '2', tool: 'Write', input: { file_path: 'dist/out.js' } },
    { tool_use_id: '3', tool: 'Write', input: { file_path: '/w/bun.lock' } },
    { tool_use_id: '4', tool: 'NotebookEdit', input: { notebook_path: '/w/n.ipynb' } },
  ] }]
  w.tokens = 60_000
  await handoff($, w, 'T1')
  const slot = w.files.get(SLOT)!.text
  expect(slot).toContain('- /w/src/x.ts')
  expect(slot).toContain('- /w/n.ipynb')
  expect(slot).not.toContain('out.js')
  expect(slot).not.toContain('bun.lock')
})

test('AC-4 long lists stay under 2000 bytes with +N more, next actions kept', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  w.messages = [{ role: 'assistant', text: '', toolUses: Array.from({ length: 200 }, (_, i) =>
    ({ tool_use_id: String(i), tool: 'Edit', input: { file_path: `/w/src/some/long/folder/file-${i}.ts` } })) }]
  w.tokens = 60_000
  await handoff($, w, 'T1')
  const slot = w.files.get(SLOT)!.text
  expect(blockBytes(slot)).toBeLessThan(2000)
  expect(slot).toMatch(/- \+\d+ more/)
  expect(slot).toContain('## Handoff numbers')
  expect(slot).toContain('Next: finish the gate')
})

test('AC-4 all three lists long stay under 2000 bytes', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  w.messages = [{ role: 'assistant', text: '', toolUses: Array.from({ length: 200 }, (_, i) => [
    { tool_use_id: `e${i}`, tool: 'Edit', input: { file_path: `/w/src/some/long/folder/file-${i}.ts` } },
    { tool_use_id: `b${i}`, tool: 'Bash', input: { command: 'git commit -m x' }, text: `[main ${(0xabc0000 + i).toString(16)}] feat: a fairly long commit subject number ${i}\nsee https://github.com/owner/repo/issues/${1000 + i}` },
  ]).flat() }]
  w.tokens = 60_000
  await handoff($, w, 'T1')
  expect(blockBytes(w.files.get(SLOT)!.text)).toBeLessThan(2000)
})

test('AC-4 multibyte paths with a viewer line stay under 2000 UTF-8 bytes', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.files.set(`${STATE}/S1.json`, { text: JSON.stringify({ root: 'S1', session: 'S1', previous: null, startTokens: null, unattended: 0, triggeredAt: null, phase: 'idle', lastRequest: null, link: 'http://100.1.2.3:3846/S1-abc' }), mtimeMs: 0 })
  await start($)
  w.messages = [{ role: 'assistant', text: '', toolUses: Array.from({ length: 200 }, (_, i) =>
    ({ tool_use_id: String(i), tool: 'Edit', input: { file_path: `/w/src/éèêëéèêë/日本語-${i}.ts` } })) }]
  w.tokens = 60_000
  await handoff($, w, 'T1')
  const slot = w.files.get(SLOT)!.text
  expect(blockBytes(slot)).toBeLessThan(2000)
  expect(slot).toMatch(/- \+\d+ more/)
  expect(slot).toContain('viewer: http://100.1.2.3:3846/S1-abc')
})

test('AC-3 the last request is quoted as typed, even with $ patterns', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  await typed($, "use $& and $' in the regex")
  w.tokens = 60_000
  await complete($, 'T1')
  expect(w.commands[0]!.args).toContain("use $& and $' in the regex")
})

test('AC-5 unverified figures: only context lines, never code spans, file names or known numbers', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.slotText = '# H\nContext was 12% full, 1,234,567 tokens, see `150k` in run-200k.txt\nBuilt 5000 widgets today\nContext at 60k tokens\n'
  await start($)
  w.tokens = 60_000
  await handoff($, w, 'T1')
  const slot = w.files.get(SLOT)!.text
  expect(slot).toContain('12% [unverified: not in Handoff numbers]')
  expect(slot).toContain('1,234,567 tokens [unverified: not in Handoff numbers]')
  expect(slot).toContain('`150k` in run-200k.txt\n')
  expect(slot).toContain('Built 5000 widgets today\n')
  expect(slot).toContain('Context at 60k tokens\n')
  expect(w.files.get(`${STATE}/auto-handoff.log`)!.text).toContain('unverified figure: 12%')
})

test('AC-6 AC-7 an owner /clear starts a fresh chain: no seed, guard count reset', { options: { threshold: 50000, maxConsecutiveHandoffs: 1 } }, async ($, on) => {
  const w = world(on)
  await start($)
  w.tokens = 60_000
  await handoff($, w, 'T1')
  expect(names(w)).toEqual(['rollover', 'clear', 'resume-from-clear'])
  // Owner types /clear by hand in S2: a new chain, so the next crossing hands off instead of pausing.
  w.id = 'S9'
  await $.session.end({ sessionId: 'S2', reason: 'clear' } as any)
  expect(names(w)).toEqual(['rollover', 'clear', 'resume-from-clear'])
  w.tokens = 60_000
  expect(((await read($)) as any).deny).toBeDefined()
})

test('AC-6 AC-8 a clear that rejects fails, sends no seed, says it may have cleared', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.clearMode = 'reject'
  await start($)
  w.tokens = 60_000
  await handoff($, w, 'T1')
  await w.clock.advance(20_000)
  expect(names(w)).toEqual(['rollover', 'clear'])
  expect(chain(w).phase).toBe('failed')
  expect(w.status).toContain('the clear failed; the chat may still have cleared')
})

test('AC-8 a seed that rejects fails and leaves the handover for a typed /resume-from-clear', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.resumeRejects = true
  await start($)
  w.tokens = 60_000
  await handoff($, w, 'T1')
  await w.clock.settle()
  expect(names(w)).toEqual(['rollover', 'clear', 'resume-from-clear'])
  expect(chain(w).phase).toBe('failed')
  expect(w.status).toContain('type /resume-from-clear')
  expect(chain(w).unattended).toBe(1)
  expect(((await read($)) as any).deny).toBeUndefined()
})

test('AC-6 held slash text goes through command.run, plain text through prompt.submit', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  w.tokens = 60_000
  expect(((await read($)) as any).deny).toBeDefined()
  await typed($, 'plain words', 'T1')
  await typed($, '/scope add a thing', 'T1')
  await handoff($, w, 'T1')
  expect(w.resent).toEqual(['plain words'])
  expect(w.commands.slice(3)).toEqual([{ command: 'scope', args: 'add a thing' }])
})

test('AC-6 an answered last request seeds without the priority part', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.slotText = '# H\n## Last request from the owner\n> fix it\nStatus: answered\n## Other\nStatus: not answered\n'
  await start($)
  w.tokens = 60_000
  await handoff($, w, 'T1')
  expect(w.commands[2]!.args).toContain('GO-ON')
  expect(w.commands[2]!.args).not.toContain('FIRST')
})

test('AC-9 AC-10 the sectionsTemplate setting points at the owner file', { options: { threshold: 50000, sectionsTemplate: '~/my/sections.md' } }, async ($, on) => {
  const w = world(on)
  w.files.set('/h/my/sections.md', { text: 'MY SECTIONS {{lastRequest}}', mtimeMs: 0 })
  await start($)
  await typed($, 'do x')
  w.tokens = 60_000
  await complete($, 'T1')
  expect(w.commands[0]).toEqual({ command: 'rollover', args: 'MY SECTIONS do x' })
})

test('AC-2 Esc: a gated turn with no turn.complete hands off at the next step', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  await step($, 'T1', 0)
  w.tokens = 60_000
  expect(((await read($)) as any).deny).toBeDefined()
  w.tokens = 1_000
  const r = await step($, 'T2', 0)
  expect(r.stopReason).toBe('end_turn')
  await w.clock.settle()
  expect(names(w)).toEqual(['rollover'])
})

test('AC-2 Esc: the next owner prompt starts the handoff and is held', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  await step($, 'T1', 0)
  w.tokens = 60_000
  expect(((await read($)) as any).deny).toBeDefined()
  const h = await typed($, 'are you there')
  expect((h as any).drop).toBeDefined()
  await w.clock.settle()
  expect(names(w)).toEqual(['rollover'])
  expect(w.commands[0]!.args).toContain('are you there')
})

test('AC-1 default line is 200000', async ($, on) => {
  const w = world(on)
  await start($)
  w.tokens = 199_000
  expect(((await read($)) as any).deny).toBeUndefined()
  w.tokens = 201_000
  expect(((await read($)) as any).deny).toBeDefined()
})

test('AC-7 default guard: the third unattended crossing pauses', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  w.tokens = 60_000
  await handoff($, w, 'T1')
  await step($, 'T2s', 0) // fresh chat starts at 60000
  w.tokens = 120_000
  await handoff($, w, 'T2')
  expect(names(w).filter(c => c === 'resume-from-clear').length).toBe(2)
  await step($, 'T3s', 0)
  w.tokens = 200_000
  expect(((await read($)) as any).deny).toBeUndefined()
  expect(chain(w).phase).toBe('paused')
  const log = w.files.get(`${STATE}/auto-handoff.log`)!.text
  expect(log).toMatch(/ S3 paused after 2 handoffs in a row/)
})

test('AC-2 a refused call hands off even when the size later reads under the line', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  await step($, 'T1', 0)
  w.tokens = 60_000
  expect(((await read($)) as any).deny).toBeDefined()
  w.tokens = 1_000
  expect(((await read($)) as any).deny).toBeDefined() // still gated
  await complete($, 'T1')
  expect(names(w)).toEqual(['rollover'])
})

test('AC-1 a fresh chat hands off at start plus headroom, not at the threshold', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  w.tokens = 60_000
  await handoff($, w, 'T1')
  w.tokens = 45_000
  await step($, 'T2s', 0)
  w.tokens = 84_000 // past 50k, under 45k + 40k
  expect(((await read($)) as any).deny).toBeUndefined()
  w.tokens = 86_000
  expect(((await read($)) as any).deny).toBeDefined()
  await handoff($, w, 'T2')
  expect(w.files.get(SLOT)!.text).toContain('- handoff line: 85000 (start plus headroom)')
})

test('AC-4 AC-8 an older slot from before the trigger is not taken as the new handover', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.noSlotWrite = true
  w.files.set(SLOT, { text: BASE_SLOT, mtimeMs: 0 })
  await start($)
  w.tokens = 60_000
  await handoff($, w, 'T1')
  expect(names(w)).toEqual(['rollover'])
  expect(chain(w).phase).toBe('failed')
  expect(w.files.get(SLOT)!.text).toBe(BASE_SLOT)
})

test('AC-7 a failed handoff counts toward the guard', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.noSlotWrite = true
  await start($)
  w.tokens = 60_000
  await handoff($, w, 'T1')
  expect(chain(w)).toMatchObject({ phase: 'failed', unattended: 1 })
})

test('AC-4 a chain link adds one viewer line to the facts', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.files.set(`${STATE}/S1.json`, { text: JSON.stringify({ root: 'S1', session: 'S1', previous: null, startTokens: null, unattended: 0, triggeredAt: null, phase: 'idle', lastRequest: null, link: 'http://100.1.2.3:3846/S1-abc' }), mtimeMs: 0 })
  await start($)
  w.tokens = 60_000
  await handoff($, w, 'T1')
  const slot = w.files.get(SLOT)!.text
  expect(slot.match(/^viewer: http:\/\/100\.1\.2\.3:3846\/S1-abc$/gm)?.length).toBe(1)
})

test('AC-12 a log line carries the session id for each event', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.clearMode = 'reject'
  await start($)
  w.tokens = 60_000
  expect(((await read($)) as any).deny).toBeDefined()
  await handoff($, w, 'T1')
  const log = w.files.get(`${STATE}/auto-handoff.log`)!.text
  for (const s of ['trigger:', 'refused Read', 'rollover started', 'slot found', 'failed: the clear failed']) expect(log).toMatch(new RegExp(`^\\S+ S1 ${s}`, 'm'))
})
