import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'
import { fillTemplate } from '../facts.ts'
// Spec 0063: the automatic handoff, driven through the engine's own events with an in-memory world.
const SLOT = '/h/.claude/projects/-w/rollover/session.md'
const STATE = '/h/.claude/state/auto-handoff'

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
    rolloverWrites: true,
    clearHangs: false,
    startGate: null as Promise<void> | null,
    sent: 0,
    resent: [] as string[],
    slotStatus: 'not answered',
    gitLog: '',
    gitArgs: [] as string[][],
    agents: [] as { id: string; status: string }[],
  }
  on('agent.list', () => ({ value: w.agents as any }))
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
  // the first name under the path, so a folder of folders lists as the disk does
  on('fs.list', (_$, e: any) => ({ value: [...new Set([...w.files.keys()].filter(k => k.startsWith(e.path + '/')).map(k => k.slice(e.path.length + 1).split('/')[0]!))].map(name => ({ name, kind: 'dir', size: 0 })) as any }))
  on('process.run', (_$, e: any) => e.argv[0] === 'git'
    ? (w.gitArgs.push([...e.argv]), { value: { exitCode: 0, stdout: w.gitLog, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } })
    : { value: w.files.has(SLOT)
    ? { exitCode: 0, stdout: `${SLOT}\n`, stderr: '', isStdoutTruncated: false, isStderrTruncated: false }
    : { exitCode: 1, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } })
  on('command.run', (_$, e: any) => {
    w.commands.push({ command: e.command, args: e.args })
    if (e.command === 'rollover' && w.rolloverWrites) {
      clock.advance(5) // the slot is written after the trigger
      w.files.set(SLOT, { text: `# Rollover handover\nNext: finish the gate. Context was 210k tokens.\n## Last request from the owner\n> fix it\nStatus: ${w.slotStatus}\n`, mtimeMs: clock.now() + 10 })
    }
    if (e.command === 'clear') {
      if (w.clearHangs) return new Promise(() => {})
      w.id = 'S2'
    }
    return { text: '' }
  })
  on('prompt.submit', (_$, e: any) => { if (e.origin.kind === 'plugin') w.resent.push(e.text); return { text: e.text } })
  on('tool.call', () => ({ result: 'ok', text: 'x'.repeat(400) } as any))
  on('turn.step', async function* (_$, e: any) {
    w.sent++
    return { turnId: e.turnId, index: e.index, answer: 'a', toolUses: [], stopReason: 'end_turn', usage: null } as any
  })
  on('turn.complete', () => ({ text: '' }))
  on('session.start', async (_$, e: any) => { await w.startGate; return { cwd: e.cwd } })
  on('session.end', (_$, e: any) => ({ sessionId: e.sessionId }))
  return w
}

const start = ($: any) => $.session.start({ cwd: '/w', surface: 'terminal', isInteractive: true })
const typed = ($: any, text: string, turnId?: string) => $.prompt.submit({ text, wait: false, origin: { kind: 'composer' }, ...(turnId ? { turnId } : {}) })
async function step($: any, turnId: string, index: number) {
  const s = $.turn.step({ turnId, index, model: 'm', messageCount: 1 })
  let x = await s.next()
  while (!x.done) x = await s.next()
  return x.value
}
const complete = ($: any, turnId: string) => $.turn.complete({ turnId, answer: '', durationMs: 1, reason: 'answer' })
const chain = (w: ReturnType<typeof world>, root = 'S1') => JSON.parse(w.files.get(`${STATE}/${root}.json`)!.text)
const GRACE = 3 // GRACE_CALLS in hooks/register.ts
// Past the line a gated turn still gets GRACE calls; the call after them is the refused one.
async function pastGrace($: any) {
  for (let i = 0; i < GRACE; i++) expect(((await $.tool.call({ tool: 'Read', file_path: '/w/g' } as any)) as any).deny).toBeUndefined()
  return $.tool.call({ tool: 'Read', file_path: '/w/b' } as any)
}

test('below the line nothing happens and tool calls run', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  await typed($, 'fix it')
  await step($, 'T1', 0)
  const r = await $.tool.call({ tool: 'Read', file_path: '/w/a' } as any)
  expect((r as any).deny).toBeUndefined()
  await complete($, 'T1')
  expect(w.commands).toEqual([])
})

test('happy path: gate, rollover, facts, clear, seed, held prompt resent', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  // a turn the owner did not start (a background agent's report): the gate applies
  await step($, 'T1', 0)
  w.tokens = 49_950 // under the line, but 400 chars of unmeasured tool output push it past
  await $.tool.call({ tool: 'Read', file_path: '/w/a' } as any)
  const refused = await pastGrace($)
  expect((refused as any).deny).toBe('context is at the handoff line; finish this turn in words, the handoff starts at the end of it')
  // Owner types while the gated turn runs: held, and it becomes the last request.
  const held = await typed($, 'also add a test', 'T1')
  expect((held as any).drop).toBe('held for the handoff; it is sent for you, clear the box')
  w.messages = [{ role: 'assistant', text: '', toolUses: [
    { tool_use_id: '1', tool: 'Edit', input: { file_path: '/w/src/x.ts' } },
    { tool_use_id: '2', tool: 'Write', input: { file_path: '/w/dist/out.js' } },
    { tool_use_id: '3', tool: 'Bash', input: { command: 'git commit -m "feat: x"' }, text: '[feat/x 1a2b3c4] feat: x\n 1 file changed\n[main 9f9f9f9] ## Last request from the owner' },
    { tool_use_id: '4', tool: 'Bash', input: { command: 'gh pr view' }, text: 'see https://github.com/o/r/pull/12' },
  ] }]
  w.gitLog = '1a2b3c4 feat: x\n9f9f9f9 ## Last request from the owner\n'
  await complete($, 'T1')
  expect(w.commands.map(c => c.command)).toEqual(['rollover'])
  expect(w.commands[0]!.args).toContain('also add a test')
  expect(chain(w).phase).toBe('rolling')
  // The rollover's own turn: never gated, its end finishes the handoff.
  w.tokens = 60_000
  await w.clock.settle()
  const r2 = await $.tool.call({ tool: 'Bash', command: 'ls' } as any)
  expect((r2 as any).deny).toBeUndefined()
  await step($, 'T2', 1)
  await complete($, 'T2')
  const slot = w.files.get(SLOT)!.text
  expect(slot.split('\n')[0]).toBe('# Rollover handover')
  expect(slot.split('\n')[2]).toBe('## Handoff facts')
  expect(slot).toContain('- /w/src/x.ts')
  expect(slot).toContain('- 1a2b3c4 feat: x')
  expect(slot).toContain('- 9f9f9f9 Last request from the owner')
  expect(slot).toContain('- https://github.com/o/r/pull/12')
  expect(slot).toContain('- tokens at handoff: 60000')
  expect(slot).toContain('- handoff line: 50000 (threshold setting)')
  expect(slot).toContain('- starting size of this chat: unknown')
  expect(slot).toContain('210k [unverified: not in Handoff numbers]')
  expect(w.commands.map(c => c.command)).toEqual(['rollover'])
  await w.clock.advance(1500)
  expect(w.commands.map(c => c.command)).toEqual(['rollover', 'clear', 'resume-from-clear'])
  expect(w.commands[2]!.args).toContain('FIRST')
  expect(w.resent).toEqual(['also add a test'])
  const c = chain(w)
  expect(c).toMatchObject({ root: 'S1', session: 'S2', previous: 'S1', unattended: 1, phase: 'idle', lastRequest: 'also add a test' })
  // The fresh chat's size is read after its first response.
  w.tokens = 30_000
  await step($, 'T3', 0)
  expect(chain(w).startTokens).toBe(30_000)
  const log = w.files.get(`${STATE}/auto-handoff.log`)!.text
  expect(w.gitArgs[0]).toEqual(['git', '-C', '/w', 'log', '--since=1970-01-01T00:16:40.000Z', '-n', '30', '--format=%h %s'])
  for (const s of ['trigger:', 'allowed Read at the gate (2 more)', 'refused Read', 'rollover started', 'slot found', 'cleared; seed run', 'fresh chat starts at 30000']) expect(log).toContain(s)
})

test('a model request past the line ends the turn and hands off', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  w.tokens = 60_000
  const r = await step($, 'T1', 1)
  expect(r.stopReason).toBe('end_turn')
  expect(w.sent).toBe(0)
  await complete($, 'T1')
  expect(w.commands.map(c => c.command)).toEqual(['rollover'])
})

test('a question cut off at line + 20k gets priority even when the handover says answered', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.slotStatus = 'answered'
  await start($)
  await typed($, 'why does it refuse?')
  await step($, 'T1', 0)
  w.tokens = 70_000 // an owner's turn is refused only at the hard margin, with no grace
  expect(((await $.tool.call({ tool: 'Bash', command: 'gh' } as any)) as any).deny).toBeDefined()
  await complete($, 'T1')
  await w.clock.settle()
  await step($, 'T2', 1)
  await complete($, 'T2')
  await w.clock.advance(1500)
  const seed = w.commands.find(c => c.command === 'resume-from-clear')!
  expect(seed.args).toContain('FIRST')
  expect(seed.args).toContain('why does it refuse?')
})

test('a question answered in a full turn does not get priority later', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.slotStatus = 'answered'
  await start($)
  await typed($, 'why does it refuse?')
  await step($, 'T1', 0)
  await complete($, 'T1')
  await step($, 'T2', 0)
  w.tokens = 60_000
  expect(((await pastGrace($)) as any).deny).toBeDefined()
  await complete($, 'T2')
  await w.clock.settle()
  await step($, 'T3', 1)
  await complete($, 'T3')
  await w.clock.advance(1500)
  expect(w.commands.find(c => c.command === 'resume-from-clear')!.args).toContain('GO-ON')
})

test('no new slot: nothing is cleared, the failure stays and the gate opens', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.rolloverWrites = false
  await start($)
  w.tokens = 60_000
  await complete($, 'T1')
  await w.clock.settle()
  await complete($, 'T2')
  await w.clock.advance(20_000)
  expect(w.commands.map(c => c.command)).toEqual(['rollover'])
  expect(chain(w).phase).toBe('failed')
  expect(w.status).toContain('auto handoff failed')
  const r = await $.tool.call({ tool: 'Read', file_path: '/w/a' } as any)
  expect((r as any).deny).toBeUndefined()
  await typed($, 'ok go on')
  expect(chain(w).phase).toBe('idle')
  expect(w.status).toBeUndefined()
})

test('a clear that never finishes fails after 15 s and sends no seed', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.clearHangs = true
  await start($)
  w.tokens = 60_000
  await complete($, 'T1')
  await w.clock.settle()
  await complete($, 'T2')
  await w.clock.advance(20_000)
  expect(w.commands.map(c => c.command)).toEqual(['rollover', 'clear'])
  expect(chain(w).phase).toBe('failed')
  expect(w.status).toContain('may still have cleared')
})

test('the fresh chat waits for start plus headroom, and past the guard it pauses', { options: { threshold: 50000, maxConsecutiveHandoffs: 1 } }, async ($, on) => {
  const w = world(on)
  await start($)
  w.tokens = 60_000
  await complete($, 'T1')
  await w.clock.settle()
  await complete($, 'T2')
  await w.clock.advance(1500)
  w.tokens = 45_000
  await step($, 'T3', 0)
  expect(chain(w, 'S1').startTokens).toBe(45_000)
  w.tokens = 80_000 // past 50k but under 45k + 40k
  await complete($, 'T3')
  expect(w.commands.filter(c => c.command === 'rollover').length).toBe(1)
  w.tokens = 90_000
  const r = await $.tool.call({ tool: 'Read', file_path: '/w/a' } as any)
  expect((r as any).deny).toBeUndefined() // guard reached: paused, not gated
  expect(chain(w).phase).toBe('paused')
  expect(w.toasts).toContain('auto handoff paused: type anything to resume')
  await typed($, 'carry on')
  expect(chain(w)).toMatchObject({ phase: 'idle', unattended: 0 })
})

test('AUTO_HANDOFF_TOKENS sets the line; hand typed /rollover is never gated', async ($, on) => {
  const w = world(on, { AUTO_HANDOFF_TOKENS: '20000' })
  await start($)
  await typed($, '/rollover')
  w.tokens = 25_000
  const r = await $.tool.call({ tool: 'Read', file_path: '/w/a' } as any)
  expect((r as any).deny).toBeUndefined()
  await complete($, 'T1')
  expect(w.commands).toEqual([])
  await typed($, 'next thing')
  expect(((await pastGrace($)) as any).deny).toBeDefined()
})

for (const env of [{ WF_RUN: '1' }, { TM_WORKER_NAME: 'w1' }, { AUTO_HANDOFF_DISABLE: '1' }] as Record<string, string>[]) {
  test(`does nothing with ${Object.keys(env)[0]}`, { options: { threshold: 50000 } }, async ($, on) => {
    const w = world(on, env)
    await start($)
    w.tokens = 60_000
    const r = await $.tool.call({ tool: 'Read', file_path: '/w/a' } as any)
    expect((r as any).deny).toBeUndefined()
    await complete($, 'T1')
    expect(w.commands).toEqual([])
  })
}

test('does nothing headless', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await $.session.start({ cwd: '/w', surface: null, isInteractive: false } as any)
  w.tokens = 60_000
  await complete($, 'T1')
  expect(w.commands).toEqual([])
})

test('templates are copied on first start and the owner copy wins', async ($, on) => {
  const w = world(on)
  w.files.set('/h/.claude/auto-handoff/instructions.md', { text: 'MINE', mtimeMs: 0 })
  await start($)
  expect(w.files.get('/h/.claude/auto-handoff/sections.md')!.text).toContain('TEMPLATE sections.md')
  expect(w.files.get('/h/.claude/auto-handoff/instructions.md')!.text).toBe('MINE')
})

const cmd = async ($: any, args: string) => ((await $.command.run({ command: 'auto-handoff', args })) as any).text as string

test('a fresh chat writes its chain file at start, on, with the line the band shows', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  expect(chain(w)).toMatchObject({ phase: 'idle', line: 50000 })
  expect(chain(w).off).toBeUndefined()
  expect(await cmd($, '')).toBe('auto handoff is on: this chat hands off at 50k tokens (now 10k)')
})

test('/auto-handoff off: past the line no gate and no rollover; on again, the next call is gated', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  expect(await cmd($, 'off')).toMatch(/^auto handoff is off for this chat/)
  expect(chain(w).off).toBe(true)
  await typed($, 'fix it')
  w.tokens = 60_000
  expect((await step($, 'T1', 0)).answer).toBe('a')
  expect(((await $.tool.call({ tool: 'Read', file_path: '/w/a' } as any)) as any).deny).toBeUndefined()
  await complete($, 'T1')
  expect(w.commands).toEqual([])
  expect(await cmd($, 'on')).toBe('auto handoff is on: this chat hands off at 50k tokens (now 60k)')
  expect(chain(w).off).toBe(false)
  await typed($, 'go on')
  expect(((await pastGrace($)) as any).deny).toBeDefined()
})

test('/auto-handoff with another word changes nothing and says how to use it', async ($, on) => {
  const w = world(on)
  await start($)
  expect(await cmd($, 'maybe')).toMatch(/^use \/auto-handoff on, \/auto-handoff off/)
  expect(chain(w).off).toBeUndefined()
})

test('/auto-handoff typed while the chat start is still running waits for it, then applies', async ($, on) => {
  const w = world(on)
  let open!: () => void
  w.startGate = new Promise<void>(r => { open = r })
  const starting = start($)
  const reply = cmd($, 'off')
  await new Promise(r => setTimeout(r, 20))
  open()
  await starting
  expect(await reply).toMatch(/^auto handoff is off for this chat/)
  expect(chain(w).off).toBe(true)
})

test('a chat where the handoff does not run says so', async ($, on) => {
  world(on, { AUTO_HANDOFF_DISABLE: '1' })
  await start($)
  expect(await cmd($, 'off')).toMatch(/^auto handoff does not run in this chat/)
})

test('off rides into the chat /handoff starts; an owner clear starts on', async ($, on) => {
  const w = world(on)
  await start($)
  await cmd($, 'off')
  w.files.set(SLOT, { text: 'handover', mtimeMs: w.clock.now() })
  await $.command.run({ command: 'handoff', args: '' })
  await w.clock.advance(1500)
  await $.session.end({ sessionId: 'S1', reason: 'clear' } as any)
  expect(chain(w, 'S2').off).toBe(true)
  w.id = 'S3'
  await $.session.end({ sessionId: 'S2', reason: 'clear' } as any)
  expect(chain(w, 'S3').off).toBeUndefined()
})

test('the rollover and the fresh chat get this chat\'s transcript path, so neither searches for it', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  const log = '/h/.claude/projects/-w/S1.jsonl'
  w.files.set('/h/.claude/projects/-other/S9.jsonl', { text: '', mtimeMs: 0 })
  w.files.set(log, { text: '', mtimeMs: 0 })
  w.files.set('/h/.claude/auto-handoff/instructions.md', { text: 'read <previous transcript> now', mtimeMs: 0 })
  // the shipped template's two lines; the shipped file itself is checked in the test after next
  w.files.set('/h/.claude/auto-handoff/sections.md', { text: "{{#transcript}}This chat's transcript is {{transcript}}: name it as the previous transcript{{/transcript}}\nOnce the slot is written, end the turn with one short line.", mtimeMs: 0 })
  await start($)
  w.tokens = 60_000
  await step($, 'T1', 1)
  await complete($, 'T1')
  expect(w.commands[0]!.args).toContain(`This chat's transcript is ${log}: name it as the previous transcript`)
  expect(w.commands[0]!.args).toContain('end the turn with one short line')
  await w.clock.settle()
  await step($, 'T2', 1)
  await complete($, 'T2')
  await w.clock.advance(1500)
  expect(w.commands.find(c => c.command === 'resume-from-clear')!.args).toBe(`read ${log} now`)
})

test('with no transcript found the block drops and the placeholder stays for the skill', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.files.set('/h/.claude/auto-handoff/sections.md', { text: 'S{{#transcript}} log {{transcript}}{{/transcript}}{{^transcript}} none{{/transcript}}', mtimeMs: 0 })
  await start($)
  w.tokens = 60_000
  await step($, 'T1', 1)
  await complete($, 'T1')
  expect(w.commands[0]!.args).toBe('S none')
})

// The shipped template's own lines (a test cannot read a .md file; verify greps templates/sections.md for them).
const shippedSections = "{{#transcript}}\nThis chat's transcript is {{transcript}}: name it as the previous transcript, do not search for the newest log.\n{{/transcript}}\nOnce the slot is written, end the turn with one short line: the chat is cleared a second later, and the fresh chat reads the handover, not a summary."
test('the transcript block keeps its line with a path and drops without one, the one line close stays', () => {
  const text = shippedSections
  const filled = fillTemplate(text, { priority: false, lastRequest: 'x', transcript: '/p/S1.jsonl' })
  expect(filled).toContain("This chat's transcript is /p/S1.jsonl: name it as the previous transcript")
  expect(fillTemplate(text, { priority: false, lastRequest: 'x', transcript: null })).not.toContain("This chat's transcript")
  expect(filled).toContain('end the turn with one short line')
})

// Handoff loss audit fix 4: the gate stopped promised work halfway and left the owner's newest message unanswered.
test('fix 4: a turn started by a fresh owner message is never gated; it hands off at its end', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.slotStatus = 'answered'
  await start($)
  await typed($, 'zip it and send it to my phone')
  await step($, 'T1', 0)
  w.tokens = 60_000
  expect((await step($, 'T1', 1)).answer).toBe('a') // the model request goes on
  for (let i = 0; i < GRACE + 2; i++) expect(((await $.tool.call({ tool: 'Bash', command: 'zip' } as any)) as any).deny).toBeUndefined()
  expect(chain(w).phase).toBe('idle')
  expect(w.commands).toEqual([])
  await complete($, 'T1')
  expect(w.commands.map(c => c.command)).toEqual(['rollover'])
  await w.clock.settle()
  await step($, 'T2', 1)
  await complete($, 'T2')
  await w.clock.advance(1500)
  // the owner's turn ran to its end, so its request is not marked unanswered
  expect(w.commands.find(c => c.command === 'resume-from-clear')!.args).toContain('GO-ON')
})

test('fix 4: at line + 20k every tool call is refused, with no grace', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  await start($)
  await step($, 'T1', 0)
  w.tokens = 70_000
  expect(((await $.tool.call({ tool: 'Read', file_path: '/w/a' } as any)) as any).deny).toBeDefined()
  expect(chain(w).phase).toBe('gated')
})

// Handoff loss audit fix 5: a handoff stopped a running helper agent, which was relaunched from zero.
test('fix 5: the handoff waits while a background agent runs, then starts once', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.agents = [{ id: 'a1', status: 'running' }, { id: 'a0', status: 'completed' }]
  await start($)
  w.tokens = 60_000
  await complete($, 'T1')
  expect(w.commands).toEqual([])
  expect(chain(w).phase).toBe('gated')
  await w.clock.advance(5000)
  // the agent's report starts a turn meanwhile: it ends at once and starts no second handoff
  expect((await step($, 'N1', 0)).stopReason).toBe('end_turn')
  await complete($, 'N1')
  expect(w.commands).toEqual([])
  w.agents[0]!.status = 'completed'
  await w.clock.advance(5000)
  expect(w.commands.map(c => c.command)).toEqual(['rollover'])
  expect(w.files.get(`${STATE}/auto-handoff.log`)!.text).toContain('waiting for 1 background agent(s) before the handoff')
  expect(w.files.get(`${STATE}/auto-handoff.log`)!.text.split('waiting for').length).toBe(2) // one wait, not one per turn
})

test('fix 5: the wait is capped at 15 minutes', { options: { threshold: 50000 } }, async ($, on) => {
  const w = world(on)
  w.agents = [{ id: 'a1', status: 'waiting' }]
  await start($)
  w.tokens = 60_000
  await complete($, 'T1')
  await w.clock.advance(14 * 60_000)
  expect(w.commands).toEqual([])
  await w.clock.advance(60_000 + 5000)
  expect(w.commands.map(c => c.command)).toEqual(['rollover'])
  expect(w.files.get(`${STATE}/auto-handoff.log`)!.text).toContain('agents still running after 15 min; handoff starts')
})
