import { expect, mock, test } from 'claude-code/testing'

// Spec 0057 AC-10: /handoff clears only with a live slot, and only from a timer after its hook returned.
for (const live of [true, false]) {
  test(`handoff ${live ? 'clears with a live slot' : 'does nothing without one'}`, async ($, on) => {
    const clock = mock.clock(on)
    mock.env(on, { HOME: '/h' })
    on('session.cwd', () => ({ value: '/w' }))
    let argv: readonly string[] = []
    on('process.run', (_$, e) => {
      argv = e.argv
      return { value: live ? { exitCode: 0, stdout: '/h/.claude/projects/-w/rollover/session.md\n', stderr: '' }
                  : { exitCode: 1, stdout: '', stderr: '' } }
    })
    let clears = 0
    on('command.run', { command: 'clear' }, () => { clears++; return { text: '' } })

    const r = await $.command.run({ command: 'handoff', args: '' })
    expect(argv).toEqual(['/h/.claude/skills/jjstack/bin/jjstack-rollover-slot', '--cwd', '/w', 'status', '--max-age-days', '1'])
    expect(r.text).toContain(live ? 'clearing' : 'no handover, run /rollover first')
    expect(clears).toBe(0)
    await clock.advance(2000)
    expect(clears).toBe(live ? 1 : 0)
  })
}

// Scope row 103: a manual /rollover then /handoff got no facts block, so no "not live" list; only the
// auto path stamped it (PR #152 added the list there and no test ever ran the manual path).
test('handoff stamps the not live facts into a handover a manual rollover wrote, once', async ($, on) => {
  const clock = mock.clock(on)
  mock.env(on, { HOME: '/h' })
  const SLOT = '/h/.claude/projects/-w/rollover/session.md'
  let slot = '# Rollover handover\nNext: go on.\n'
  const ok = (stdout: string, exitCode = 0) => ({ value: { exitCode, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } })
  on('session.cwd', () => ({ value: '/w' }))
  on('session.id', () => ({ value: 'S1' }))
  on('session.usage', () => ({ value: { startedAt: 0, context: { tokens: 90_000, window: 1_000_000 }, rateLimits: [] } as any }))
  on('session.messages', () => ({ value: [{ toolUses: [{ tool: 'Edit', input: { file_path: '/w/src/x.ts' } }] }] as any }))
  on('command.register', (_$, e: any) => ({ value: { command: e.name } }))
  on('fs.read', (_$, e: any) => { if (e.path === SLOT) return { value: slot }; if (e.path.includes('/templates/')) return { value: 'T' }; throw new Error(`ENOENT ${e.path}`) })
  on('fs.write', (_$, e: any) => { if (e.path === SLOT) slot = e.text; return { value: undefined } })
  on('fs.stat', (_$, e: any) => { throw new Error(`ENOENT ${e.path}`) })
  on('fs.list', () => ({ value: [] as any }))
  on('process.run', (_$, e: any) =>
    e.argv[0] === 'env' && e.argv[3] === 'gh' ? ok(JSON.stringify([{ number: 152, title: 'fix: manual handoff', url: 'https://github.com/o/r/pull/152', isDraft: false }]))
    : e.argv[0] === 'git' && e.argv[3] === 'rev-parse' ? ok('/w/.git\n')
    : e.argv[0] === 'git' && e.argv[3] === 'branch' ? ok('feat/y [ahead 2]\n')
    : e.argv[0] === 'git' ? ok('')
    : e.argv[0] === 'realpath' ? ok('/w\n')
    : ok(`${SLOT}\n`))
  on('command.run', { command: 'clear' }, () => ({ text: '' }))
  on('session.start', (_$, e: any) => ({ cwd: e.cwd }))
  await $.session.start({ cwd: '/w', surface: 'terminal', isInteractive: true })

  const r = await $.command.run({ command: 'handoff', args: '' })
  expect(r.text).toContain('clearing')
  expect(slot).toContain('## Handoff facts')
  expect(slot).toContain('Open PRs, not merged, so not live yet:\n- #152 fix: manual handoff https://github.com/o/r/pull/152\n- branch feat/y in /w: commits not on main')
  expect(slot).toContain('Files edited or written:\n- /w/src/x.ts')
  // a second /handoff on the same handover adds nothing
  await $.command.run({ command: 'handoff', args: '' })
  expect(slot.split('## Handoff facts').length).toBe(2)
  await clock.advance(2000)
})

// Row 103, the common path: the owner types /clear (session.end, reason clear) after a manual /rollover.
// The chat starts at clock 1_000_000; a slot newer than that is this chat's, an older one is not.
async function ownerClear($: any, on: any, slotMtimeMs: number) {
  mock.clock(on, { now: 1_000_000 })
  mock.env(on, { HOME: '/h' })
  const SLOT = '/h/.claude/projects/-w/rollover/session.md'
  const w = { slot: '# Rollover handover\nNext: go on.\n' }
  const ok = (stdout: string) => ({ value: { exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } })
  on('session.cwd', () => ({ value: '/w' }))
  on('session.id', () => ({ value: 'S1' }))
  on('session.usage', () => ({ value: { startedAt: 0, context: { tokens: 90_000, window: 1_000_000 }, rateLimits: [] } as any }))
  on('session.messages', () => ({ value: [{ toolUses: [{ tool: 'Edit', input: { file_path: '/w/src/x.ts' } }] }] as any }))
  on('command.register', (_$, e: any) => ({ value: { command: e.name } }))
  on('fs.read', (_$, e: any) => { if (e.path === SLOT) return { value: w.slot }; if (e.path.includes('/templates/')) return { value: 'T' }; throw new Error(`ENOENT ${e.path}`) })
  on('fs.write', (_$, e: any) => { if (e.path === SLOT) w.slot = e.text; return { value: undefined } })
  on('fs.stat', (_$, e: any) => {
    if (e.path !== SLOT) throw new Error(`ENOENT ${e.path}`)
    return { value: { kind: 'file', size: w.slot.length, mtimeMs: slotMtimeMs, isLink: false } }
  })
  on('fs.list', () => ({ value: [] as any }))
  on('process.run', (_$, e: any) =>
    e.argv[0] === 'env' && e.argv[3] === 'gh' ? ok(JSON.stringify([{ number: 152, title: 'fix: manual handoff', url: 'https://github.com/o/r/pull/152', isDraft: false }]))
    : e.argv[0] === 'git' && e.argv[3] === 'rev-parse' ? ok('/w/.git\n')
    : e.argv[0] === 'git' && e.argv[3] === 'branch' ? ok('feat/y [ahead 2]\n')
    : e.argv[0] === 'git' ? ok('')
    : e.argv[0] === 'realpath' ? ok('/w\n')
    : ok(`${SLOT}\n`))
  on('session.start', (_$, e: any) => ({ cwd: e.cwd }))
  on('session.end', (_$, e: any) => ({ sessionId: e.sessionId }))
  await $.session.start({ cwd: '/w', surface: 'terminal', isInteractive: true })
  await $.session.end({ sessionId: 'S1', reason: 'clear' } as any)
  return w
}

test("the owner's /clear after a manual rollover stamps the not live facts into its slot, once", async ($, on) => {
  const w = await ownerClear($, on, 1_000_500)
  expect(w.slot).toContain('Open PRs, not merged, so not live yet:\n- #152 fix: manual handoff https://github.com/o/r/pull/152\n- branch feat/y in /w: commits not on main')
  expect(w.slot.split('## Handoff facts').length).toBe(2)
})

test("the owner's /clear leaves a slot an older chat wrote alone", async ($, on) => {
  const w = await ownerClear($, on, 500_000)
  expect(w.slot).toBe('# Rollover handover\nNext: go on.\n')
})
