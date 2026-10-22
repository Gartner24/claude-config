// The dashboard: one pane, three sections you move between with a key (p Plan, n Now, a Agents). The runner's Builds
// and Alerts views went with the runner.
// Same look as the band: k9s rows, state words that carry their meaning without color, dim chrome, color spent on
// state. Pure drawing from data; tokens.ts holds every value.
import type { WfDashAsk, WfDashFeature, WfDashHandoff, WfDashLoaded, WfDashOwed, WfDashPlan, WfDashPr, WfDashPrs } from './types/index.d.ts'
import { tokens } from './band.tsx'
import { handoverLink } from './handoff.ts'
import { agentStatus, color, glyph, pane, shortTab, space, specStatus, state, stateHelp, stateOrder, tinyTab } from './tokens.ts'

type El = { Box: any; Text: any; Button: any }
export type View = { section: string; tab: string; page: number; sel: number; gsel?: number; nsel?: number; ask?: WfDashAsk | null; notice?: { text: string; ok: boolean } | null }
// run: the confirmed action (spec 0060 AC-5); only the confirm row's `y` reaches it
export type Act = { go: (v: Partial<View>) => void; retry: () => void; run: (ask: WfDashAsk) => void }
type Plan = WfDashLoaded<WfDashPlan> | undefined

export const SECTIONS = [
  { id: 'plan', key: 'p', label: 'Plan' },
  { id: 'now', key: 'n', label: 'Now' },
  { id: 'agents', key: 'a', label: 'Agents' },
]

// Plan filters, in the order of their digit keys; `states` null means every open feature.
export const PLAN_TABS: { id: string; label: string; states: string[] | null; done?: boolean; empty: string }[] = [
  { id: 'needs-you', label: 'Needs you', states: ['waits on you'], empty: 'Nothing waits on you. A step only you can do (a login, a check on your phone) lands here.' },
  { id: 'ready', label: 'Ready', states: ['ready to build'], empty: 'Nothing is ready to build. A feature lands here once its design is accepted.' },
  { id: 'design', label: 'Needs design', states: ['needs a design'], empty: 'Nothing needs a design. A feature lands here while a decision is owed (/architect).' },
  { id: 'progress', label: 'In progress', states: ['in progress'], empty: 'Nothing is in progress. A feature lands here when it is partly done.' },
  { id: 'built', label: 'Built', states: ['done', 'done (untagged)'], done: true, empty: 'Nothing built yet. A feature lands here once it is built and merged.' },
  { id: 'open', label: 'All open', states: null, empty: 'Nothing open.' },
]

export const DEFAULT_VIEW: View = { section: 'plan', tab: 'needs-you', page: 0, sel: 0 }

// -- Actions (spec 0060 AC-5): the only next steps the dashboard may start; anything else is typed by you ------------
export const SAFE_STEPS = ['/architect', '/develop', '/check verify', '/test', '/sync', '/debug', '/scope']
// no line breaks or invisible format characters (bidi, zero width): the confirm must show exactly what runs
export const safeStep = (cmd: string | null) => !!cmd && !/[\r\n\p{Cc}\p{Cf}]/u.test(cmd) && SAFE_STEPS.some(s => cmd === s || cmd.startsWith(`${s} `))
// a step started in a chat of another repo would build there
const inRepo = (path: string, cwd: string | null) => !!cwd && (cwd === path || cwd.startsWith(`${path}/`))

// The start offer for a feature: the exact text to submit, or why it is yours to type; null when it has no next step.
export function startOffer(f: WfDashFeature, path: string, cwd: string | null): { ok: boolean; text: string } | null {
  if (isDone(f.state) || !f.command || f.state === 'waits on you') return null
  if (!safeStep(f.command)) return { ok: false, text: `type it yourself: ${f.command}` }
  if (!inRepo(path, cwd)) return { ok: false, text: `type it yourself in ${path}: ${f.command}` }
  return { ok: true, text: f.command }
}

export function confirmText(a: WfDashAsk): string {
  return a.kind === 'start' ? `Start "${a.text}" in this chat?` : `Stop ${a.label}?`
}

type Offer = { key: string; label: string; ask: WfDashAsk } | { note: string } | null
type ActLine = { t: string; tone: string; bold?: boolean }
type Key = { key: string; label: string; on: boolean; press: () => void }

// The rows a hotkey row wraps to at `cells` wide, so a view can budget for it.
const keyRows = (keys: Key[], cells: number) =>
  keys.length ? Math.max(1, Math.ceil((keys.reduce((n, k) => n + k.label.length + space.hotkeyCells, 0) + (keys.length - 1) * space.gap) / Math.max(1, cells))) : 0

// An action's lines and keys: a pending confirm (y runs it, c cancels), else the last result and the view's offer.
// Each view draws them inside its own row budget: the dashboard never grows past its rows, so the confirm's keys
// can never fall off the bottom of the pane (design-gate 2026-10-18).
function actionParts(view: View, act: Act, offer: Offer, cells: number): { lines: ActLine[]; keys: Key[]; rows: number } {
  const a = view.ask
  let lines: ActLine[]
  let keys: Key[]
  if (a) {
    keys = [
      { key: 'y', label: 'yes', on: true, press: () => { act.go({ ask: null }); act.run(a) } },
      { key: 'c', label: 'cancel', on: true, press: () => act.go({ ask: null }) },
    ]
    // wrapped, never cut: the whole text that runs is on screen before yes
    lines = wrapWords(confirmText(a), cells, Infinity).map(t => ({ t, tone: color.warn, bold: true }))
  } else {
    lines = [
      ...(view.notice ? [{ t: view.notice.text, tone: view.notice.ok ? color.ok : color.bad }] : []),
      ...(offer && 'note' in offer ? [{ t: offer.note, tone: color.dim }] : []),
    ]
    keys = offer && 'ask' in offer ? [{ key: offer.key, label: offer.label, on: true, press: () => act.go({ ask: offer.ask, notice: null }) }] : []
  }
  return { lines, keys, rows: lines.length + keyRows(keys, cells) }
}

function actionRow(el: El, parts: { lines: ActLine[]; keys: Key[] }) {
  const { Box, Text } = el
  return (
    <Box flexDirection="column">
      {parts.lines.map(l => <Text color={l.tone} bold={l.bold} wrap="truncate-end">{l.t}</Text>)}
      {parts.keys.length > 0 && keyRow(el, parts.keys)}
    </Box>
  )
}

const hhmm = (ms: number) => {
  const d = new Date(ms)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
const stateOf = (s: string) => (state as Record<string, { color: string; word: string }>)[s.replace(' (untagged)', '')] ?? { color: color.text, word: s }
const rank = (s: string) => {
  const i = (stateOrder as readonly string[]).indexOf(s.replace(' (untagged)', ''))
  return i < 0 ? stateOrder.length : i
}
// "done (untagged)" is the done group: one state, one group
const norm = (s: string) => s.replace(' (untagged)', '')
const isDone = (s: string) => ['done', 'dropped', 'existing'].includes(s.replace(' (untagged)', ''))
// a box's text without backticks and without the scope's trailing tags (" . waits on you", " . live"): plan markup, not words
export const untag = (s: string) => s.replace(/`/g, '').replace(/\s+[.·]\s+(waits on you|later boxes go on|live|skipped)\b.*$/, '')
// the box's command is what the next step runs
const step = (f: WfDashFeature) => f.command ?? untag(f.next ?? '')

function cell(Box: any, Text: any, text: string, w: number | null, props: Record<string, unknown> = {}) {
  return (
    <Box width={w ?? undefined} flexGrow={w ? 0 : 1} flexShrink={w ? 0 : 1} marginRight={space.tight}>
      <Text wrap="truncate-end" {...props}>{text}</Text>
    </Box>
  )
}

function keyRow({ Box, Button }: El, items: { key: string; label: string; on: boolean; press: () => void; mark?: boolean }[], gap: number = space.gap) {
  return (
    <Box flexDirection="row" columnGap={gap} flexWrap="wrap">
      {items.map(i => <Button key={`k-${i.key}`} plain hotkey={i.key} label={i.on && i.mark ? `[${i.label}]` : i.label} dimColor={!i.on} onPress={i.press} />)}
    </Box>
  )
}

function loading({ Box, Text }: El, what: string, l: WfDashLoaded<unknown> | undefined, act?: Act) {
  if (l?.error && !l.data) {
    return (
      <Box flexDirection="column" marginTop={space.line}>
        <Text color={color.bad}>{`Could not read ${what} (${l.error}).`}</Text>
        <Text color={color.dim}>r tries again. If it keeps failing, run python3 plan.py from the chip-dash mod folder in a terminal to see why.</Text>
      </Box>
    )
  }
  return <Box marginTop={space.line}><Text color={color.dim}>{`Reading ${what}...`}</Text></Box>
}

// -- Plan ----------------------------------------------------------------------------------------------------------

type Line = { kind: 'group'; name: string; note: string; tone?: string } | { kind: 'feature'; f: WfDashFeature; repo: string; path?: string } | { kind: 'note'; text: string; tone: string }

// Pages of `rows` lines that never orphan a group heading at the foot, and repeat the heading (`cont.`) on top of a
// page that starts inside a group, so every row on screen sits under its group's name.
export function paginate(lines: Line[], rows: number): Line[][] {
  const pages: Line[][] = []
  let cur: Line[] = []
  let group: Extract<Line, { kind: 'group' }> | null = null
  for (const l of lines) {
    if (l.kind === 'group') group = l
    if (cur.length + (l.kind === 'group' ? 2 : 1) > rows) {
      pages.push(cur)
      cur = l.kind !== 'group' && group ? [{ ...group, note: `${group.note} cont.` }] : []
    }
    cur.push(l)
  }
  if (cur.length) pages.push(cur)
  return pages.length ? pages : [[]]
}

// Grouped by state, Linear style: the group heading carries the state word and its count, so rows never repeat it.
// Each row names its repo instead. Broken scopes, hub rows and scope warnings follow the state groups.
export function planLines(repos: WfDashPlan['repos'], tab: (typeof PLAN_TABS)[number]): Line[] {
  const picked = repos.flatMap(r =>
    r.error || r.hub ? [] : (r.features ?? []).filter(f => !f.deferred && (tab.states ? tab.states.includes(f.state) : !isDone(f.state))).map(f => ({ f, repo: r.name, path: r.path })))
  const lines: Line[] = []
  const groups = [...new Set(picked.map(p => p.f.state.replace(' (untagged)', '')))].sort((a, b) => rank(a) - rank(b))
  for (const g of groups) {
    const members = picked.filter(p => p.f.state.replace(' (untagged)', '') === g)
    // one group on a single-state filter: the filter tab already says the state and the count, so the row goes to a feature
    if (groups.length > 1 || tab.id === 'open') lines.push({ kind: 'group', name: stateOf(g).word, note: `${members.length}`, tone: stateOf(g).color })
    members.forEach(p => lines.push({ kind: 'feature', f: p.f, repo: p.repo, path: p.path }))
  }
  for (const r of repos) {
    if (r.error) lines.push({ kind: 'group', name: r.name, note: '' }, { kind: 'note', text: `could not read this scope: ${r.error}`, tone: color.bad })
    else if (r.hub && tab.id === 'open' && r.rows?.length) {
      lines.push({ kind: 'group', name: r.name, note: `${r.rows.length} open rows (hub)` })
      r.rows.forEach(t => lines.push({ kind: 'note', text: t, tone: color.text }))
    } else if (!tab.done && picked.some(p => p.repo === r.name)) r.warnings?.forEach(w => lines.push({ kind: 'note', text: `${r.name}: ${w}`, tone: color.warn }))
  }
  return lines
}

// Up to `max` lines of `cells` cells, broken at spaces; the last line ends in "..." when text is left over.
export function wrapWords(text: string, cells: number, max: number): string[] {
  const out: string[] = []
  let rest = text.trim()
  while (rest && out.length < max) {
    if (rest.length <= cells) { out.push(rest); rest = ''; break }
    if (out.length === max - 1) { out.push(rest.slice(0, Math.max(0, cells - glyph.cut.length)).trimEnd() + glyph.cut); rest = ''; break }
    const cut = rest.lastIndexOf(' ', cells)
    const at = cut > 0 ? cut : cells
    out.push(rest.slice(0, at).trimEnd())
    rest = rest.slice(at).trimStart()
  }
  return out
}

function PlanSection({ el, plan, view, act, columns, cwd, extra = 0 }: { el: El; plan: Plan; view: View; act: Act; columns: number; cwd: string | null; extra?: number }) {
  const { Box, Text } = el
  if (!plan?.data) return loading(el, 'the plan', plan, act)
  const repos = plan.data.repos
  const all = repos.flatMap(r => r.features ?? []).filter(f => !f.deferred)
  const count = (t: (typeof PLAN_TABS)[number]) => all.filter(f => (t.states ? t.states.includes(f.state) : !isDone(f.state))).length
  const tab = PLAN_TABS.find(t => t.id === view.tab) ?? PLAN_TABS[0]
  // plan warnings under All open take their rows out of the list's page, so the pane never grows past its rows; the
  // list keeps two (a heading and a feature), and warnings past that are counted on the last line, never cut silently
  const warnAll = tab.id === 'open' ? plan.data.warnings ?? [] : []
  const warnMax = pane.page + extra - 2
  const warns = warnAll.length > warnMax ? [...warnAll.slice(0, warnMax - 1), `+${warnAll.length - warnMax + 1} more plan warnings`] : warnAll
  const room = pane.page + extra - warns.length
  const pageList = paginate(planLines(repos, tab), room)
  // the cursor moves over features only; the page is the one that holds the selected feature
  const feats = pageList.flatMap((p, pi) => p.flatMap(l => (l.kind === 'feature' ? [{ line: l, page: pi }] : [])))
  const sel = feats.length ? Math.min(view.sel ?? 0, feats.length - 1) : -1
  const pages = pageList.length
  const page = sel >= 0 ? feats[sel].page : 0
  const chosen = sel >= 0 ? feats[sel].line.f : null
  const wide = columns >= pane.specMin
  const pageFirst = (p: number) => {
    const want = ((p % pages) + pages) % pages
    const i = feats.findIndex(x => x.page >= want)
    return i < 0 ? 0 : i
  }
  // t: the first feature of the next state group, wrapping to the top. It was n until Now took n (spec 0071 AC-1):
  // two buttons on one hotkey, the later wins, so n would never have opened Now from Plan
  const nextGroup = () => {
    if (sel < 0) return 0
    const i = feats.findIndex((x, k) => k > sel && norm(x.line.f.state) !== norm(feats[sel].line.f.state))
    return i < 0 ? 0 : i
  }
  // the repo column only when the page on screen mixes repos
  const repoCol = new Set(pageList[page].flatMap(l => (l.kind === 'feature' ? [l.repo] : []))).size > 1
  const inner = columns - 2 * space.padX
  // a narrow pane: two deliberate rows of 4 (act now / the rest) with short labels; the act-now row keeps its counts and
  // falls back to its tiny labels only when the counts would push it past one line
  const label = (t: (typeof PLAN_TABS)[number], names: Record<string, string>, counted: boolean) =>
    counted ? `${names[t.id]} ${count(t)}` : names[t.id]
  // a row's cells: each label with its "N: " hotkey, the gaps, and the selected filter's two brackets
  const brackets = 2
  const rowCells = (labels: string[], gap: number) => labels.reduce((n, l) => n + l.length + space.hotkeyCells, 0) + (labels.length - 1) * gap + brackets
  const actNow = PLAN_TABS.slice(0, 4)
  const rest = PLAN_TABS.slice(4)
  const full = Object.fromEntries(PLAN_TABS.map(x => [x.id, x.label]))
  const actNames = rowCells(actNow.map(t => label(t, shortTab, true)), space.tight) <= inner ? shortTab : { ...shortTab, ...tinyTab }
  // wide: one row when all eight fit, else the same deliberate 4 + 4 split as narrow, with full labels and counts
  const tabRows = wide
    ? rowCells(PLAN_TABS.map(t => label(t, full, true)), space.gap) <= inner
      ? [PLAN_TABS.map(t => ({ t, text: label(t, full, true) }))]
      : [actNow, rest].map(r => r.map(t => ({ t, text: label(t, full, true) })))
    : [actNow.map(t => ({ t, text: label(t, actNames, true) })), rest.map(t => ({ t, text: label(t, shortTab, t.id === tab.id) }))]
  const cells = Math.max(pane.minWrap, inner - space.indent)
  // the start action lives in the detail block's rows; a confirm too long to show whole beside its keys is not offered
  const o = chosen ? startOffer(chosen, feats[sel].line.path ?? '', cwd) : null
  const fits = (text: string) => wrapWords(confirmText({ kind: 'start', text }), cells, Infinity).length < pane.detail
  const parts = actionParts(view, act, !o ? null : !o.ok ? { note: o.text } : fits(o.text)
    ? { key: 's', label: 'start it', ask: { kind: 'start', text: o.text } }
    : { note: `type it yourself: ${o.text}` }, cells)
  // the detail block: next step first, wrapped to two lines when it runs long, then what the state means, then the ids;
  // never the state word again (the group heading says it)
  const detail = (() => {
    if (!chosen) return []
    const help = stateHelp[chosen.state.replace(' (untagged)', '')]
    // position first, so a narrow pane never cuts it; the repo only when the rows on screen do not already show it
    const meta = [
      `${sel + 1} of ${feats.length}`,
      chosen.spec ? (isDone(chosen.state) ? `spec ${chosen.spec}` : `spec ${chosen.spec}: ${specStatus[chosen.specStatus ?? 'unknown'] ?? chosen.specStatus}`) : 'no spec',
      !repoCol && new Set(feats.map(x => x.line.repo)).size > 1 ? feats[sel].line.repo : '',
    ].filter(Boolean).join('  ')
    // the name cell's width in the list row; when the row cut the name (or its repo), the detail shows them in full first
    const nameCells = inner - pane.col.cursor - 2 * space.tight - (repoCol ? pane.col.repo + space.tight : 0)
      - (wide && !isDone(chosen.state) ? pane.col.next + space.tight : 0) - (wide ? pane.col.spec + space.tight : 0)
    const heading = chosen.heading.replace(/`/g, '')
    const repo = feats[sel].line.repo
    const cut = heading.length > nameCells || (repoCol && repo.length > pane.col.repo - space.tight)
    // the action's rows come out of the block, never added below it
    const rows = pane.detail - parts.rows
    const out = cut && rows > 1 ? [{ t: repoCol ? `${heading}  ${repo}` : heading, tone: color.text }] : []
    const room = rows - 1 - out.length
    const next = isDone(chosen.state) || room < 1 ? [] : wrapWords(`next: ${untag(chosen.next ?? chosen.command ?? glyph.unknown)}`, cells, room)
    out.push(...next.map(t => ({ t, tone: color.text })))
    if (out.length < rows - 1 && help) out.push({ t: help, tone: color.dim })
    // a two-line confirm and its keys fill the block: no row is left for the ids
    if (out.length < rows) out.push({ t: meta, tone: color.dim })
    return out
  })()
  return (
    <Box flexDirection="column">
      {wide && (
        <Text color={color.dim} wrap="truncate-end">
          {tab.id === 'needs-you' ? 'Steps only you can do: a login, a check on your phone.' : 'Every plan, grouped by what each feature needs next.'}
        </Text>
      )}
      {tabRows.map(row =>
        keyRow(el, row.map(({ t, text }) => ({ key: String(PLAN_TABS.indexOf(t) + 1), label: text, on: t.id === tab.id, mark: true, press: () => act.go({ tab: t.id, sel: 0 }) })), wide ? space.gap : space.tight))}
      {/* a fixed height, padded with blank rows, so switching filters never moves the layout under the fingers */}
      <Box flexDirection="column" height={extra ? Math.max(pane.page - warns.length, Math.min(room, pageList[page].length)) : room}>
        {feats.length === 0 && pageList[0].length === 0 && <Text color={color.dim}>{tab.empty}</Text>}
        {pageList[page].map(l => {
          if (l.kind === 'group') {
            return (
              <Box flexDirection="row" gap={space.tight}>
                <Text color={l.tone ?? color.text} bold>{l.name}</Text>
                <Text color={color.dim}>{l.note}</Text>
              </Box>
            )
          }
          if (l.kind === 'note') return <Box paddingLeft={space.indent}><Text color={l.tone} wrap="truncate-end">{l.text}</Text></Box>
          const on = l.f === chosen
          return (
            <Box flexDirection="row">
              {cell(Box, Text, on ? '>' : ' ', pane.col.cursor, { color: color.accent, bold: true })}
              {cell(Box, Text, l.f.heading.replace(/`/g, ''), null, { color: isDone(l.f.state) ? color.dim : color.text, bold: on })}
              {repoCol && cell(Box, Text, l.repo, pane.col.repo, { color: color.dim })}
              {wide && !isDone(l.f.state) && cell(Box, Text, step(l.f), pane.col.next, { color: color.dim })}
              {wide && cell(Box, Text, l.f.spec ? `${l.f.spec} ${l.f.specStatus ?? 'unknown'}` : '', pane.col.spec, { color: color.dim })}
            </Box>
          )
        })}
      </Box>
      {/* the selected feature in full, three rows always (blank when nothing is selected) so the height holds;
          indented, not led by ">", so the cursor stays the only selection mark */}
      <Box flexDirection="column" height={pane.detail}>
        {detail.map(d => <Box paddingLeft={space.indent}><Text color={d.tone} wrap="truncate-end">{d.t}</Text></Box>)}
        {chosen && <Box paddingLeft={space.indent}>{actionRow(el, parts)}</Box>}
      </Box>
      {/* every key always bound, dim when it would do nothing: an unbound key falls through to the prompt and takes focus */}
      {keyRow(el, [
        { key: 'j', label: 'down', on: feats.length > 1, press: () => act.go({ sel: Math.max(0, Math.min(feats.length - 1, sel + 1)) }) },
        { key: 'k', label: 'up', on: feats.length > 1, press: () => act.go({ sel: Math.max(0, sel - 1) }) },
        { key: 'd', label: `${wide ? 'page down' : 'pg'} ${page + 1}/${pages}`, on: page < pages - 1, press: () => act.go({ sel: page < pages - 1 ? pageFirst(page + 1) : sel }) },
        { key: 'u', label: wide ? 'page up' : 'back', on: page > 0, press: () => act.go({ sel: page > 0 ? pageFirst(page - 1) : sel }) },
        { key: 't', label: wide ? 'next group' : 'group', on: new Set(feats.map(x => norm(x.line.f.state))).size > 1, press: () => act.go({ sel: nextGroup() }) },
        { key: 'g', label: 'top', on: sel > 0, press: () => act.go({ sel: 0 }) },
      ], wide ? space.gap : space.tight)}
      {warns.map(w => <Text color={color.warn} wrap="truncate-end">{w}</Text>)}
      {plan.error && <Text color={color.warn}>{`stale since ${hhmm(plan.at ?? Date.now())}: the last refresh failed (${plan.error}); r tries again`}</Text>}
    </Box>
  )
}

// -- Agents --------------------------------------------------------------------------------------------------------

const SHELL_NOTE = "Shells come from this chat's Bash results: a started one may have ended unseen."

function AgentsSection({ el, agents, view, act, columns, extra = 0 }: { el: El; agents: any[] | null; view: View; act: Act; columns: number; extra?: number }) {
  const { Box, Text } = el
  if (agents === null) return <Box marginTop={space.line}><Text color={color.bad}>Could not list this session's agents.</Text></Box>
  const sel = agents.length ? Math.min(view.gsel ?? 0, agents.length - 1) : -1
  const chosen = sel >= 0 ? agents[sel] : null
  const cells = columns - 2 * space.padX
  const parts = actionParts(view, act, chosen && (chosen.status === 'running' || chosen.type === 'shell')
    ? { key: 'x', label: 'stop it', ask: { kind: 'stop', id: chosen.id, label: `${chosen.type === 'shell' ? 'shell' : 'agent'} ${chosen.description || chosen.id}` } }
    : null, cells)
  // shells pile up over a long chat: show the rows that fit beside the note, the j/k row and the action, and follow
  // the cursor, so the confirm's keys never fall off the bottom (design-gate 2026-10-18 pass 4)
  const fit = Math.max(1, pane.listRows + extra - parts.rows - Math.ceil(SHELL_NOTE.length / Math.max(1, cells)) - 1)
  const start = Math.max(0, sel - fit + 1)
  const below = Math.max(0, agents.length - start - fit)
  return (
    <Box flexDirection="column">
      {columns >= pane.specMin && <Text color={color.dim}>The agents this chat started, and what each is doing.</Text>}
      <Box flexDirection="column">
        {/* an empty list from the mod API is not proof of no agents: the host's own count may still show some */}
        {agents.length === 0 && <Text color={color.dim}>No agents listed. The host's own agent count below the prompt may still show some.</Text>}
        {agents.slice(start, start + fit).map(a => (
          <Box flexDirection="row">
            {cell(Box, Text, a === chosen ? '>' : ' ', pane.col.cursor, { color: color.accent, bold: true })}
            {cell(Box, Text, a.status, pane.col.state, { color: (agentStatus as Record<string, string>)[a.status] ?? color.text, bold: a.status === 'running' })}
            {cell(Box, Text, a.description || a.name || a.id, null, { color: color.text })}
            {cell(Box, Text, a.type, pane.col.next, { color: color.dim })}
          </Box>
        ))}
      </Box>
      {(start > 0 || below > 0) && (
        <Text color={color.dim}>{[start > 0 ? `${start} above` : '', below > 0 ? `+${below} more` : ''].filter(Boolean).join(', ')}</Text>
      )}
      <Text color={color.dim}>{SHELL_NOTE}</Text>
      {keyRow(el, [
        { key: 'j', label: 'down', on: sel < agents.length - 1, press: () => act.go({ gsel: Math.min(agents.length - 1, sel + 1) }) },
        { key: 'k', label: 'up', on: sel > 0, press: () => act.go({ gsel: Math.max(0, sel - 1) }) },
      ])}
      {actionRow(el, parts)}
    </Box>
  )
}

// -- Now (spec 0071) -----------------------------------------------------------------------------------------------
// This chat right now: what it owes, your open PRs, its handoff, its agents. Four blocks of fixed height (AC-9), so a
// refresh never moves a row; each block draws `?` for what it could not read, never a 0.

type NowLine = { t: string; tone: string; bold?: boolean; indent?: boolean }
// agents with status running and shells not stopped or finished; null when either list could not be read
export type AgentCount = { running: number; shells: number } | null

// AC-2: up to `rows` rows, the heading counted; lines past them end in `and k more`
export function owedLines(o: WfDashOwed | undefined, rows: number = pane.now.owed): NowLine[] {
  if (!o) return [{ t: 'owed ?', tone: color.warn, bold: true }]
  if (!o.installed) return [{ t: 'catch not installed (row 92)', tone: color.dim }]
  if (o.lines === null) return [{ t: 'owed ?', tone: color.warn, bold: true }, { t: o.error ?? '', tone: color.dim, indent: true }]
  if (!o.lines.length) return [{ t: 'nothing owed', tone: color.dim }]
  const room = rows - 1
  const shown = o.lines.length > room ? o.lines.slice(0, room - 1) : o.lines
  return [
    { t: `owed ${o.lines.length}`, tone: color.warn, bold: true },
    ...shown.map(t => ({ t, tone: color.warn, indent: true })),
    ...(shown.length < o.lines.length ? [{ t: `and ${o.lines.length - shown.length} more`, tone: color.dim, indent: true }] : []),
  ]
}

const checksTone: Record<string, string> = { ok: color.ok, failing: color.bad, pending: color.warn, none: color.dim }

// AC-3, AC-9: the PR block in `rows` rows (heading counted): the rows that fit beside a stale line and a "more" line,
// following the cursor
export function prBlock(l: WfDashLoaded<WfDashPrs> | undefined, nsel: number, rows: number) {
  const data = l?.data ?? null
  const head: NowLine = { t: `your PRs ${data ? data.total : glyph.unknown}`, tone: color.text, bold: true }
  const none = { head, prs: [] as WfDashPr[], start: 0, sel: -1, notes: [] as NowLine[] }
  if (!data) {
    // before the first call ends, or a first call that failed: no list yet, so nothing to keep
    const t = l?.error ? `could not read GitHub (${l.error}); r tries again` : 'reading GitHub'
    return { ...none, notes: [{ t, tone: l?.error ? color.bad : color.dim, indent: true }] }
  }
  const stale: NowLine[] = l?.error ? [{ t: `stale since ${hhmm(l.at ?? Date.now())}: ${l.error}`, tone: color.warn, indent: true }] : []
  if (!data.prs.length) return { ...none, notes: [...stale, { t: 'no open PRs', tone: color.dim, indent: true }] }
  const onGitHub = Math.max(0, data.total - data.prs.length)
  let fit = rows - 1 - stale.length
  if (data.prs.length > fit || onGitHub > 0) fit -= 1
  fit = Math.max(1, fit)
  const sel = Math.max(0, Math.min(nsel, data.prs.length - 1))
  const start = Math.max(0, sel - fit + 1)
  const below = Math.max(0, data.prs.length - start - fit)
  const more = [start > 0 ? `${start} above` : '', below > 0 ? `+${below} more` : '', onGitHub > 0 ? `+${onGitHub} more on GitHub` : ''].filter(Boolean).join(', ')
  return { head, prs: data.prs.slice(start, start + fit), start, sel, notes: [...stale, ...(more ? [{ t: more, tone: color.dim, indent: true }] : [])] }
}

// AC-5: the band's own words for the handoff, then the handover this chat came from under the band's link rule
export function handoffLines(h: WfDashHandoff | undefined): { runs: NowLine[]; link: string | null } {
  const a = h?.auto
  const word = a == null ? { t: glyph.unknown, tone: color.dim } : a.off ? { t: 'off', tone: color.warn } : { t: a.line ? `on ${tokens(a.line)}` : 'on', tone: color.text }
  return { runs: [{ t: 'handoff ', tone: color.dim }, word], link: h ? handoverLink(h) : null }
}

export const agentsLine = (c: AgentCount) => (c ? `agents ${c.running} running, ${c.shells} shells` : `agents ${glyph.unknown}`)

function NowSection({ el, view, act, prs, owed, handoff, count, columns, extra = 0 }: {
  el: El; view: View; act: Act; prs: WfDashLoaded<WfDashPrs> | undefined; owed: WfDashOwed | undefined; handoff: WfDashHandoff | undefined; count: AgentCount; columns: number; extra?: number
}) {
  const { Box, Text } = el
  const line = (l: NowLine) => (
    <Box paddingLeft={l.indent ? space.indent : 0}><Text color={l.tone} bold={l.bold} wrap="truncate-end">{l.t}</Text></Box>
  )
  const block = prBlock(prs, view.nsel ?? 0, pane.now.prs + extra)
  const total = prs?.data?.prs.length ?? 0
  // the repo#number column takes the widest on screen, up to its cap, so the words line up; a narrow pane caps it at
  // the plan's repo cells, so the title keeps some room (the row's words stay as AC-3 spells them)
  const idW = Math.min(columns >= pane.specMin ? pane.col.prId : pane.col.repo, Math.max(0, ...block.prs.map(p => `${p.repo}#${p.number}`.length)))
  const ho = handoffLines(handoff)
  return (
    <Box flexDirection="column">
      <Box flexDirection="column" height={pane.now.owed}>{owedLines(owed).map(line)}</Box>
      <Box flexDirection="column" height={pane.now.prs + extra}>
        {line(block.head)}
        {block.prs.map((p, i) => {
          const on = block.start + i === block.sel
          const id = `${p.repo}#${p.number}`
          return (
            <Box flexDirection="row">
              {cell(Box, Text, on ? '>' : ' ', pane.col.cursor, { color: color.accent, bold: true })}
              <Text wrap="truncate-end">
                <Text color={color.text} bold={on}>{(id.length > idW ? id.slice(0, Math.max(0, idW - glyph.cut.length)) + glyph.cut : id).padEnd(idW)}</Text>
                <Text color={p.draft ? color.dim : color.text}>{`  ${p.draft ? 'draft' : 'ready'}`}</Text>
                <Text color={color.dim}>{'  checks '}</Text>
                <Text color={checksTone[p.checks] ?? color.dim}>{p.checks.padEnd('failing'.length)}</Text>
                <Text color={color.text}>{`  ${p.title}`}</Text>
              </Text>
            </Box>
          )
        })}
        {block.notes.map(line)}
      </Box>
      <Box flexDirection="column" height={pane.now.handoff}>
        <Text wrap="truncate-end">{ho.runs.map(r => <Text color={r.tone}>{r.t}</Text>)}</Text>
        {ho.link && line({ t: `last handover: ${ho.link}`, tone: color.dim, indent: true })}
      </Box>
      <Box flexDirection="row" height={pane.now.agents} columnGap={space.gap}>
        {/* the count takes the row, so `a: details` holds its cell when a count grows a digit */}
        <Box flexGrow={1} flexShrink={1}><Text color={count ? color.text : color.dim} wrap="truncate-end">{agentsLine(count)}</Text></Box>
        <Text color={color.dim}>a: details</Text>
      </Box>
      {/* AC-8: the view's whole footer on one row, so the four blocks keep the pane's 14 rows */}
      <Box flexDirection="row" columnGap={space.gap} flexWrap="wrap">
        {keyRow(el, [
          { key: 'j', label: 'down', on: block.sel >= 0 && block.sel < total - 1, press: () => act.go({ nsel: Math.min(total - 1, block.sel + 1) }) },
          { key: 'k', label: 'up', on: block.sel > 0, press: () => act.go({ nsel: Math.max(0, block.sel - 1) }) },
          { key: 'r', label: 'refresh', on: true, press: act.retry },
        ])}
        <Text color={color.dim}>esc closes</Text>
      </Box>
    </Box>
  )
}

// -- The dashboard -------------------------------------------------------------------------------------------------

export function Dashboard({ el, view, act, plan, agents, columns, cwd = null, focused = true, rows, prs, owed, handoff, count = null }: {
  el: El; view: View; act: Act; plan: Plan; agents: any[] | null; columns: number; cwd?: string | null; focused?: boolean; rows?: number
  prs?: WfDashLoaded<WfDashPrs>; owed?: WfDashOwed; handoff?: WfDashHandoff; count?: AgentCount
}) {
  const { Box, Text } = el
  const section = SECTIONS.find(s => s.id === view.section) ?? SECTIONS[0]
  // a docked pane's rows past the inline budget go to the lists, so the room is used, not left blank
  const extra = rows ? Math.max(0, rows - pane.baseRows) : 0
  return (
    <Box flexDirection="column" paddingX={space.padX}>
      <Box flexDirection="row" columnGap={space.gap}>
        <Text backgroundColor={color.accent} color="inverseText" bold>{' chip '}</Text>
        {keyRow(el, SECTIONS.map(s => ({ key: s.key, label: s.label, on: s.id === section.id, mark: true, press: () => act.go({ section: s.id, ask: null, notice: null }) })), columns >= pane.specMin ? space.gap : space.tight)}
      </Box>
      {/* a stray key hands the keyboard to the prompt; say so, and how to come back, instead of failing silently.
          This used to name the host's focus key, which did not give the keys back in a real terminal; a click did (spec 0062 P11) */}
      {!focused && <Text color={color.warn} wrap="truncate-end">Keys go to the prompt now: click the dashboard to return</Text>}
      <Box flexDirection="column">
        {section.id === 'plan' && <PlanSection el={el} plan={plan} view={view} act={act} columns={columns} cwd={cwd} extra={extra} />}
        {section.id === 'now' && <NowSection el={el} view={view} act={act} prs={prs} owed={owed} handoff={handoff} count={count} columns={columns} extra={extra} />}
        {section.id === 'agents' && <AgentsSection el={el} agents={agents} view={view} act={act} columns={columns} extra={extra} />}
      </Box>
      {section.id !== 'now' && (
        <Box flexDirection="row" columnGap={space.gap} flexWrap="wrap">
          {keyRow(el, [{ key: 'r', label: 'refresh', on: true, press: act.retry }])}
          <Text color={color.dim}>esc closes</Text>
        </Box>
      )}
    </Box>
  )
}
