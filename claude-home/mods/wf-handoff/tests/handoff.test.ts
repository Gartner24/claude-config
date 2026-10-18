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
