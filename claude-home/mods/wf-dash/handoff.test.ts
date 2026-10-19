import { expect, mock, test } from 'claude-code/testing'
import { HandoffRow } from './band.tsx'
import { handoffLine } from './handoff.ts'
import { glyph, time } from './tokens.ts'

// Spec 0064 AC-2, AC-6: the handoff line under the band, from the wf-handoff mod's panel.json.
const LINK = 'http://100.88.1.2:3846/S1aaaaaa-0123456789abcdef'
const steps = (...s: string[]) => ['writing the handover', 'clearing', 'starting the fresh chat'].map((label, i) => ({ label, state: (s[i] ?? 'pending') as any }))
const panel = (o: any = {}) => ({ session: 'S1', previous: null, phase: 'rolling', steps: steps('running'), result: null, sticky: false, link: null, at: 1000, ...o })
const view = (p: any, o: any = {}) => ({ panel: p, me: 'S1', prev: null, dismissed: 0, frame: 0, ...o })

test('a running step shows with the braille spinner, one frame per turn', () => {
  expect(handoffLine(view(panel()), 1000)).toMatchObject({ kind: 'running', text: `${glyph.spinner[0]} writing the handover` })
  expect(handoffLine(view(panel(), { frame: 3 }), 1000)!.text).toBe(`${glyph.spinner[3]} writing the handover`)
  const clearing = panel({ phase: 'clearing', steps: steps('done', 'running') })
  expect(handoffLine(view(clearing), 1000)!.text).toBe(`${glyph.spinner[0]} clearing`)
})

test('the steps written under the old id show in the chat that replaced it', () => {
  const p = panel({ phase: 'clearing', steps: steps('done', 'running') })
  expect(handoffLine(view(p, { me: 'S2', prev: 'S1' }), 1000)!.kind).toBe('running')
  expect(handoffLine(view(p, { me: 'S9', prev: 'S8' }), 1000)).toBeNull()
})

test('the result shows with its link for 10 s, then the chat keeps a handover link', () => {
  const p = panel({ session: 'S2', previous: 'S1', phase: 'idle', steps: steps('done', 'done', 'done'), result: 'handed off · 210k -> 95k', link: LINK, at: 5000 })
  const v = view(p, { me: 'S2', prev: 'S1' })
  expect(handoffLine(v, 5000 + time.handoffResult - 1)).toMatchObject({ kind: 'result', text: `handed off · 210k -> 95k · ${LINK}` })
  expect(handoffLine(v, 5000 + time.handoffResult)).toMatchObject({ kind: 'link', text: `handover: ${LINK}` })
})

test('a chat that never came from a handoff shows no link line', () => {
  const p = panel({ session: 'S1', previous: null, phase: 'idle', steps: steps(), link: LINK })
  expect(handoffLine(view(p), 1000)).toBeNull()
})

test('a sticky failure stays past any time until dismissed, then it is gone', () => {
  const p = panel({ phase: 'failed', steps: steps('failed'), result: 'auto handoff failed: the rollover wrote no new handover; nothing was cleared', sticky: true, at: 1000 })
  expect(handoffLine(view(p), 1000 + 10 * 60_000)).toMatchObject({ kind: 'sticky', text: p.result })
  expect(handoffLine(view(p, { dismissed: 1001 }), 2000)).toBeNull()
  const paused = panel({ phase: 'paused', steps: steps(), result: 'auto handoff paused: type anything to resume', sticky: true })
  expect(handoffLine(view(paused), 1e9)!.kind).toBe('sticky')
})

test('AC-2 a dismissal hides only the sticky line it saw; a later failure shows again', () => {
  const p = panel({ phase: 'failed', steps: steps('failed'), result: 'auto handoff failed: again', sticky: true, at: 9000 })
  expect(handoffLine(view(p, { dismissed: 5000 }), 9000)).toMatchObject({ kind: 'sticky', text: 'auto handoff failed: again' })
})

// stand in host components: the mod's jsx calls them, so each node is { name, props }
const comp = (name: string) => (props: any) => ({ name, props })
const find = (node: any, name: string): any[] => {
  if (!node || typeof node !== 'object') return []
  const here = node.name === name ? [node] : []
  return [...here, ...[node.props?.children].flat().flatMap(k => find(k, name))]
}

test('AC-2 a sticky line carries the band\'s dismiss key x; other lines have none', () => {
  const [Box, Text, Button] = [comp('Box'), comp('Text'), comp('Button')]
  let dismissed = 0
  const sticky = HandoffRow({ Box, Text, Button, line: { kind: 'sticky', text: 'auto handoff failed: x', color: 'red', link: null }, onDismiss: () => { dismissed++ } })
  const buttons = find(sticky, 'Button')
  expect(buttons.length).toBe(1)
  expect(buttons[0].props.hotkey).toBe('x')
  buttons[0].props.onPress()
  expect(dismissed).toBe(1)
  const result = HandoffRow({ Box, Text, Button, line: { kind: 'result', text: `handed off · 210k -> 95k · ${LINK}`, color: 'green', link: LINK }, onDismiss: () => {} })
  expect(find(result, 'Button')).toEqual([])
  expect(find(result, 'Text')[0].props.children).toEqual([`handed off · 210k -> 95k · ${LINK}`])
})

// the host beneath register.tsx, as register.test.ts has it, plus the panel file
function host(on: any) {
  const files: Record<string, string> = {}
  const state: Record<string, any> = {}
  const clock = mock.clock(on, { now: 50_000 })
  const w = { files, state, clock, id: 'S1' }
  on('state.get', (_$: any, e: any) => ({ value: { value: state[e.key], version: 0 } }))
  on('state.set', (_$: any, e: any) => { state[e.key] = e.value; return { value: { isSet: true, version: 1 } } })
  mock.env(on, { HOME: '/h', XDG_STATE_HOME: '' })
  on('session.start', () => ({ cwd: '/w' }))
  on('session.id', () => ({ value: w.id }))
  on('session.cwd', () => ({ value: '/w' }))
  on('session.usage', () => ({ value: { context: { percent: 6 }, rateLimits: [] } }))
  on('session.model', () => ({ value: 'claude-opus-5-5' }))
  on('fs.write', (_$: any, e: any) => { files[e.path] = e.text ?? ''; return { value: undefined } })
  on('fs.read', (_$: any, e: any) => (e.path in files ? { value: files[e.path] } : { deny: 'ENOENT' }))
  on('command.register', (_$: any, e: any) => ({ value: { command: e.name } }))
  on('process.run', () => ({ value: { exitCode: 1, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('prompt.submit', (_$: any, e: any) => ({ text: e.text }))
  return w
}
const PANEL = '/h/.claude/state/auto-handoff/panel.json'

test('the band tick reads panel.json, follows the id across a clear, and keeps our panel over another chat\'s', async ($, on) => {
  const w = host(on)
  w.files[PANEL] = JSON.stringify(panel({ phase: 'clearing', steps: steps('done', 'running') }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await w.clock.advance(10)
  expect(w.state.handoff).toMatchObject({ me: 'S1', prev: null, panel: { phase: 'clearing' } })
  const spun = w.state.handoff.frame
  await w.clock.advance(time.spin)
  expect(w.state.handoff.frame).toBeGreaterThan(spun)
  w.id = 'S2'
  w.files[PANEL] = JSON.stringify(panel({ session: 'S2', previous: 'S1', phase: 'idle', steps: steps('done', 'done', 'done'), result: 'handed off · 210k -> 95k', link: LINK }))
  await w.clock.advance(time.bandTick)
  expect(w.state.handoff).toMatchObject({ me: 'S2', prev: 'S1', panel: { session: 'S2', link: LINK } })
  w.files[PANEL] = JSON.stringify(panel({ session: 'OTHER', phase: 'rolling' }))
  await w.clock.advance(time.bandTick)
  expect(w.state.handoff.panel.session).toBe('S2')
})

test('under reduced motion the spinner keeps its first frame', async ($, on) => {
  const w = host(on)
  let reduced = true
  on('settings.read', () => ({ value: { prefersReducedMotion: reduced } as any }))
  w.files[PANEL] = JSON.stringify(panel({ phase: 'clearing', steps: steps('done', 'running') }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await w.clock.advance(10)
  await w.clock.advance(time.spin * 3)
  expect(w.state.handoff.frame).toBe(0)
  expect(handoffLine(w.state.handoff, 50_000)!.text).toBe(`${glyph.spinner[0]} clearing`)
  reduced = false
  await w.clock.advance(time.spin)
  expect(w.state.handoff.frame).toBeGreaterThan(0)
})

test('typing dismisses a sticky line', async ($, on) => {
  const w = host(on)
  w.files[PANEL] = JSON.stringify(panel({ phase: 'failed', steps: steps('failed'), result: 'auto handoff failed: x', sticky: true, at: 40_000 }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/w' } as any)
  await w.clock.advance(10)
  expect(handoffLine(w.state.handoff, 60_000)!.kind).toBe('sticky')
  await $.prompt.submit({ text: 'ok', wait: false, origin: { kind: 'composer' } } as any)
  expect(handoffLine(w.state.handoff, 60_000)).toBeNull()
})
