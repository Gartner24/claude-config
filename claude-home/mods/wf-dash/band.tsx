// The band above the prompt: this session on the left, the runner on the right, always one line.
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

// `cells`: the number (or its `?`) is left padded to it, so the full band's line does not shift as a count grows;
// the compact band passes none, its zero test and budget read the bare text
function countRun(n: number | null, one: string, many: string, tone: string, cells = 0): Run {
  if (n === null) return { text: `${pad(glyph.unknown, cells)} ${many}`, color: color.dim }
  const word = n === 1 ? one : many
  return n === 0 ? { text: `${pad('0', cells)} ${word}`, color: color.dim } : { text: `${pad(String(n), cells)} ${word}`, color: tone, bold: true }
}

// `rich` adds the reset times and the context tokens; the band drops them before it drops a segment.
// `compact` is for a column too narrow for the chip and the full runner counts (the ~31 cells beside the docked
// dashboard): zero counts leave, the words shorten, one space between them.
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
  // the owner turns the auto handoff off in chats that are not for coding (/auto-handoff); the band says which this is
  if (f.handoff !== undefined) {
    const h = f.handoff
    left.push(seg('handoff', h === null
      ? [{ text: `handoff ${glyph.unknown}`, color: color.dim }]
      : h.off
        ? [{ text: 'handoff ', color: color.dim }, { text: 'off', color: color.warn }]
        : [{ text: 'handoff ', color: color.dim }, { text: h.line ? `on ${tokens(h.line)}` : 'on', color: color.text }]))
  }
  if (f.via) left.push(seg('via', [{ text: `via ${f.via}`, color: color.dim }]))
  else left.push(
    meterSeg('5h', '5h', f.fiveHour, rich ? resetIn(f.fiveHourReset, now) : ''),
    meterSeg('week', 'week', f.week, rich ? resetIn(f.weekReset, now) : ''),
  )

  // the bar's AUTO segment: lit when this chat drives the runner, dim when only other chats do; it sits next to the
  // runner counts and is among the first to leave a narrow line
  if (f.auto?.here) left.push(seg('auto', [{ text: 'auto on', color: color.ok, bold: true }]))
  else if (f.auto?.chats) left.push(seg('auto', [{ text: `auto: ${f.auto.chats} ${f.auto.chats === 1 ? 'chat' : 'chats'} on`, color: color.dim }]))

  const w = f.wf
  // compact: the chip right beside it already names wf
  const right: Run[] = compact ? [] : [{ text: 'wf ', color: color.accent, bold: true }]
  if (w === null) right.push({ text: `${glyph.unknown} status`, color: color.dim })
  else if (compact) {
    // most urgent first (what needs you, then what is stuck), and a count that does not fit `maxCells` leaves whole
    const counts = [countRun(w.questions, 'ask', 'ask', color.warn), countRun(w.parked, 'stuck', 'stuck', color.bad), countRun(w.running, 'run', 'run', color.text)]
    const live = counts.filter(r => !r.text.startsWith('0 '))
    // all zero: one dim word, so the runner segment never vanishes
    if (!live.length) right.push({ text: 'idle', color: color.dim })
    // the stale mark is added after the counts, so its cells come out of their budget, or the host cuts it off
    let cells = f.staleSince ? ' stale'.length : 0
    for (const [i, r] of live.entries()) {
      const need = r.text.length + (i ? 1 : 0)
      // stale: even the first count leaves whole when it and the mark do not fit; old counts never pass as current
      if ((i || f.staleSince) && cells + need > maxCells) break
      right.push(...(i ? [{ text: ' ' }] : []), r)
      cells += need
    }
  } else {
    right.push(countRun(w.running, 'building', 'building', color.text, width.count), { text: glyph.sep })
    right.push(countRun(w.parked, 'stuck', 'stuck', color.bad, width.count), { text: glyph.sep })
    right.push(countRun(w.questions, 'question', 'questions', color.warn, width.count))
  }
  if (f.staleSince) right.push({ text: compact ? (right.length ? ' stale' : 'stale') : `${glyph.sep}stale since ${f.staleSince}`, color: color.dim })
  return { left, right: seg('wf', right) }
}

// Left segments leave in this order when the line is too narrow; the runner segment and the chip stay. The handoff
// state is the last to go: it is the one fact here no other part of the screen shows.
const DROP = ['folder', 'auto', 'git', 'week', '5h', 'via', 'ctx', 'model', 'handoff']

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
  // the chip is pinned; when even the compact counts do not fit, the runner segment truncates at its end instead
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
