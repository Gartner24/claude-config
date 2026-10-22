// The band above the prompt: this session on the left, its auto handoff on the right, always one line.
// Pure drawing from facts; every color, width and word comes from tokens.ts.
import type { WfDashFacts } from './types/index.d.ts'
import type { HandoffLine } from './handoff.ts'
import { color, effort, glyph, meter, space, width } from './tokens.ts'

export type Facts = WfDashFacts

// One run of text in one color; a segment is a list of runs plus its width in cells.
type Run = { text: string; color?: string; bg?: string; dim?: boolean; bold?: boolean }
type Seg = { id: string; runs: Run[]; cells: number }

const seg = (id: string, runs: Run[]): Seg => ({ id, runs, cells: runs.reduce((n, r) => n + r.text.length, 0) })
const pad = (s: string, n: number) => (s.length >= n ? s : ' '.repeat(n - s.length) + s)
const pct = (v: number | null) => (v === null ? glyph.unknown : `${Math.round(v)}%`)

// "claude-opus-5-5[1m]" -> "Opus 5.5"; anything else is shown as given.
export function prettyModel(id: string | null) {
  if (!id) return glyph.unknown
  const m = /^claude-([a-z]+)-(\d+)(?:-(\d+))?/.exec(id.replace(/\[.*\]$/, ''))
  if (!m) return id.replace(/\[.*\]$/, '')
  return `${m[1][0].toUpperCase()}${m[1].slice(1)} ${m[2]}${m[3] ? '.' + m[3] : ''}`
}

function fillColor(v: number) {
  return v >= meter.badAt ? meter.fill.bad : v >= meter.warnAt ? meter.fill.warn : meter.fill.ok
}

// "in 2h10m", "in 3d4h": how long until a usage window resets; '' when unknown or past.
export function resetIn(iso: string | null, now: number) {
  const ms = iso ? Date.parse(iso) - now : NaN
  if (!(ms > 0)) return ''
  const m = Math.floor(ms / 60000), d = Math.floor(m / 1440), h = Math.floor((m % 1440) / 60)
  return d ? `in ${d}d${h}h` : h ? `in ${h}h${String(m % 60).padStart(2, '0')}m` : `in ${m % 60}m`
}

// "160k/1M": the context window's fill in tokens, as the host's own header writes sizes.
export function tokens(n: number) {
  return n >= 1e6 ? `${+(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${Math.round(n / 1e3)}k` : String(n)
}

// Today's status bar meter: the label centred, the used share on a background, the rest dim, then the number.
function meterSeg(id: string, label: string, value: number | null, reset = ''): Seg {
  const left = Math.floor((meter.width - label.length) / 2)
  const cells = (' '.repeat(left) + label).padEnd(meter.width)
  const filled = value === null ? 0 : Math.min(meter.width, Math.round((value / 100) * meter.width))
  const runs: Run[] = []
  if (filled) runs.push({ text: cells.slice(0, filled), bg: fillColor(value as number), color: meter.onFill })
  runs.push({ text: cells.slice(filled), dim: true })
  runs.push({ text: ' ' + pad(pct(value), width.pct - 1), color: value === null ? color.dim : value >= meter.warnAt ? fillColor(value) : color.text })
  if (reset) runs.push({ text: ' ' + reset, color: color.dim })
  return seg(id, runs)
}

// `rich` adds the reset times and the context tokens; the band drops them before it drops a segment.
// `compact` is for a column too narrow for the chip and the full handoff segment (the ~31 cells beside the docked
// dashboard).
export function segments(f: Facts, now = Date.now(), rich = true, compact = false, maxCells = Infinity) {
  const left: Seg[] = [seg('chip', [{ text: ' wf-dash ', bg: color.accent, color: 'inverseText', bold: true }])]
  const model: Run[] = [{ text: prettyModel(f.model), color: color.text }]
  if (f.effort) model.push({ text: ' ' + f.effort, color: (effort as Record<string, string>)[f.effort] ?? color.dim })
  left.push(seg('model', model))
  left.push(seg('folder', [{ text: f.folder ?? glyph.unknown, color: color.text }]))
  if (f.git) {
    const g = f.git
    const runs: Run[] = [{ text: g.branch, color: color.text }]
    if (g.changes === 0) runs.push({ text: ' clean', color: color.dim })
    if (g.staged) runs.push({ text: ` +${g.staged}`, color: color.ok })
    if (g.modified) runs.push({ text: ` ~${g.modified}`, color: color.warn })
    if (g.untracked) runs.push({ text: ` ?${g.untracked}`, color: color.dim })
    left.push(seg('git', runs))
  }
  // context is null until the first reply: left out until known, never shown as a guess, like effort
  if (f.context !== null) {
    const ctx: Run[] = [{ text: 'ctx ', color: color.dim }, { text: pct(f.context), color: f.context >= meter.warnAt ? fillColor(f.context) : color.text }]
    if (rich && f.contextTokens !== null && f.contextWindow) ctx.push({ text: ` ${tokens(f.contextTokens)}/${tokens(f.contextWindow)}`, color: color.dim })
    left.push(seg('ctx', ctx))
  }
  if (f.via) left.push(seg('via', [{ text: `via ${f.via}`, color: color.dim }]))
  else left.push(
    meterSeg('5h', '5h', f.fiveHour, rich ? resetIn(f.fiveHourReset, now) : ''),
    meterSeg('week', 'week', f.week, rich ? resetIn(f.weekReset, now) : ''),
  )

  // The right end, where the retired runner's counts were: the auto handoff, which the owner turns off in chats that
  // are not for coding (/auto-handoff). Compact (the ~31 cells beside the docked dashboard) drops the word.
  const h = f.handoff
  const right: Run[] = compact ? [] : [{ text: 'handoff ', color: color.dim }]
  if (h === undefined || h === null) right.push({ text: glyph.unknown, color: color.dim })
  else if (h.off) right.push({ text: 'off', color: color.warn })
  else right.push({ text: h.line ? `on ${tokens(h.line)}` : 'on', color: color.text })
  // the stale mark goes when it does not fit `maxCells` beside the state, never the state itself
  if (f.staleSince) {
    const mark = compact ? ' stale' : `${glyph.sep}stale since ${f.staleSince}`
    if (right.reduce((n, r) => n + r.text.length, 0) + mark.length <= maxCells) right.push({ text: mark, color: color.dim })
  }
  return { left, right: seg('handoff', right) }
}

// Left segments leave in this order when the line is too narrow; the handoff segment and the chip stay.
const DROP = ['folder', 'git', 'week', '5h', 'via', 'ctx', 'model']

export function fit(left: Seg[], right: Seg, columns: number) {
  const used = (l: Seg[]) => l.reduce((n, s) => n + s.cells, 0) + space.gap * Math.max(0, l.length - 1) + space.gap + right.cells + 2 * space.padX
  let kept = left
  for (const id of DROP) {
    if (used(kept) <= columns) break
    kept = kept.filter(s => s.id !== id)
  }
  return kept
}

function draw(Box: any, Text: any, s: Seg, shrink = 0) {
  return (
    <Box flexShrink={shrink}>
      <Text wrap="truncate-end">
      {s.runs.map(r => (
        <Text color={r.color} backgroundColor={r.bg} dimColor={r.dim} bold={r.bold}>{r.text}</Text>
      ))}
      </Text>
    </Box>
  )
}

// `columns`: the host's bodyColumns, the band's own column (beside a docked pane too) less the host's `[-]` cells
export function Band({ Box, Text, Button, facts, columns, onOpen }: { Box: any; Text: any; Button?: any; facts: Facts; columns: number; onOpen?: () => void }) {
  // the chip as a button draws its hotkey first ("w: "), cells the segment width does not count
  const room = columns - (Button && onOpen ? space.hotkeyCells : 0)
  let { left, right } = segments(facts)
  let kept = fit(left, right, room)
  if (kept.length < left.length) {
    ;({ left, right } = segments(facts, Date.now(), false))
    kept = fit(left, right, room)
  }
  if (kept.length === 1) {
    ;({ left, right } = segments(facts, Date.now(), false, true, room - 2 * space.padX - left[0].cells - space.gap))
    kept = fit(left, right, room)
  }
  // the chip is pinned; when even the compact state does not fit, the handoff segment truncates at its end instead
  return (
    <Box flexDirection="row" paddingX={space.padX} width="100%">
      <Box flexDirection="row" gap={space.gap} flexGrow={1} flexShrink={kept.length === 1 ? 0 : 1}>
        {kept.map(s =>
          // the chip opens the dashboard: a click, or w once the band holds the keys
          s.id === 'chip' && Button && onOpen
            ? <Button key="wf-dash-open" plain hotkey="w" onPress={onOpen}><Text backgroundColor={color.accent} color="inverseText" bold>{' wf-dash '}</Text></Button>
            : draw(Box, Text, s),
        )}
      </Box>
      <Box flexShrink={1} marginLeft={space.gap}>
        {draw(Box, Text, right, 1)}
      </Box>
    </Box>
  )
}

// Spec 0064 AC-2: the handoff's own line under the band; a sticky one carries its dismiss key.
export function HandoffRow({ Box, Text, Button, line, onDismiss }: { Box: any; Text: any; Button?: any; line: HandoffLine; onDismiss?: () => void }) {
  return (
    <Box flexDirection="row" paddingX={space.padX} gap={space.gap} width="100%">
      <Box flexShrink={1}>
        <Text color={line.color} bold={line.kind === 'sticky'} wrap="truncate-end">{line.text}</Text>
      </Box>
      {line.kind === 'sticky' && Button && onDismiss
        ? <Button key="wf-dash-handoff-dismiss" plain hotkey="x" onPress={onDismiss}><Text color={color.dim}>dismiss</Text></Button>
        : null}
    </Box>
  )
}
