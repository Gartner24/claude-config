import { expect, test } from 'claude-code/testing'
import { Dashboard } from './panes.tsx'

const HINT = 'Keys go to the prompt now: click the dashboard to return'
const el = { Box: 'Box', Text: 'Text', Button: 'Button' }

// every string the dashboard draws, button labels included; the host's tree keeps children on the node
function texts(node: any): string[] {
  if (node == null || typeof node === 'boolean') return []
  if (typeof node === 'string' || typeof node === 'number') return [String(node)]
  if (Array.isArray(node)) return node.flatMap(texts)
  return [...(node.props?.label ? [String(node.props.label)] : []), ...texts(node.children)]
}

function draw(focused: boolean, section = 'agents') {
  const view = { section, tab: 'open', page: 0, sel: 0 }
  return texts(Dashboard({
    el, view, act: { go: () => {}, retry: () => {}, run: () => {} }, plan: null as any, agents: [], columns: 100, focused,
  }))
}

// covers: spec 0062 AC-2 and AC-5 (unfocused, the warn line names the click exactly; focused, no warn line;
// the old focus key hint is gone)
test('unfocused, the dashboard says a click brings the keys back', () => {
  expect(draw(false)).toContain(HINT)
  expect(draw(false).join('\n')).not.toContain('ctrl+x tab')
})

test('focused, the dashboard shows no warn line', () => {
  expect(draw(true).some(t => t.startsWith('Keys go to the prompt'))).toBe(false)
})

// the old hint did not work (spec 0062 P11), so nothing the dashboard draws may still teach it. A hooks module
// cannot read its own files as text, so the scan covers what it draws; design.md is grepped in verify
test('no view of the dashboard still names ctrl+x tab', () => {
  const drawn: Record<string, string> = {}
  for (const section of ['agents', 'plan']) for (const focused of [false, true]) drawn[`${section} ${focused}`] = draw(focused, section).join('\n')
  expect(Object.values(drawn).join('\n').split('\n').length).toBeGreaterThan(5)
  expect(Object.keys(drawn).filter(k => drawn[k].includes('ctrl+x tab'))).toEqual([])
})
