// Spec 0064 AC-2, AC-6: the handoff line under the band, drawn from the wf-handoff mod's panel.json.
// A file contract, no shared code: wf-handoff writes the file, this only reads it.
import type { WfDashHandoff, WfDashPanel } from './types/index.d.ts'
import { color, glyph, time } from './tokens.ts'

export type HandoffLine = { kind: 'running' | 'result' | 'sticky' | 'link'; text: string; color: string; link: string | null }

// The panel is for this chat when it names this chat, or the chat this one replaced in the same
// terminal: the steps before the clear are written under the old id.
const ours = (p: WfDashPanel, h: WfDashHandoff) => p.session === h.me || (h.prev !== null && p.session === h.prev)

export function handoffLine(h: WfDashHandoff, now: number): HandoffLine | null {
  const p = h.panel
  if (!p || !ours(p, h)) return null
  // sticky: until the owner types or presses the dismiss key, never on a timer
  if (p.sticky && p.result && p.at > h.dismissed) {
    return { kind: 'sticky', text: p.result, color: p.phase === 'paused' ? color.warn : color.bad, link: null }
  }
  const running = p.steps.find(s => s.state === 'running')
  if (running && !p.sticky) {
    const spin = glyph.spinner[h.frame % glyph.spinner.length]
    return { kind: 'running', text: `${spin} ${running.label}`, color: color.text, link: null }
  }
  const done = p.steps.length > 0 && p.steps.every(s => s.state === 'done')
  if (done && p.result && now - p.at < time.handoffResult) {
    return { kind: 'result', text: p.link ? `${p.result} · ${p.link}` : p.result, color: color.ok, link: p.link }
  }
  // a chat that came from a handoff keeps its way back to the handover
  if (p.session === h.me && p.previous && p.link) return { kind: 'link', text: `handover: ${p.link}`, color: color.dim, link: p.link }
  return null
}
