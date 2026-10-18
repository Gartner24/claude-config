import type { Register } from 'claude-code'

// Spec 0057 AC-10: /handoff replaces typing /clear after a /rollover. The clear empties the
// context and handover-start.sh (SessionStart, clear) then loads the handover; that hook is
// the fallback when this mod is gone or breaks on an update.
export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    await $.command.register({ name: 'handoff', description: 'After /rollover: clear and load the waiting handover' })
    return started
  })

  on('command.run', { command: 'handoff' }, async $ => {
    const home = await $.env.get('HOME')
    const cwd = await $.session.cwd()
    // Same status call and flags as handover-start.sh, so the mod never clears when the hook would load nothing.
    const r = await $.process.run(
      [`${home}/.claude/skills/jjstack/bin/jjstack-rollover-slot`, '--cwd', cwd, 'status', '--max-age-days', '1'],
      { timeoutMs: 2000 },
    ).catch(() => ({ exitCode: 1, stdout: '' }))
    if (r.exitCode !== 0 || !r.stdout.trim()) return { text: 'no handover, run /rollover first' }
    // Probe P2: awaiting $.command.run inside a command.run hook is refused (it waits on the turn
    // this hook holds), so the clear runs from a timer after the hook has returned.
    $.clock.after(1500, () => {
      void $.command.run({ command: 'clear', args: '' })
    })
    return { text: `Handover found at ${r.stdout.trim()}; clearing in 1.5 s, then it loads.` }
  })
}
