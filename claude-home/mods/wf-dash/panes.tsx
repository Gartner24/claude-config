// The dashboard: one pane, four sections you move between with a key (p Plan, b Builds, a Agents, l Alerts).
// Same look as the band: k9s rows, state words that carry their meaning without color, dim chrome, color spent on
// state. Pure drawing from data; tokens.ts holds every value.
import type { WfDashAlert, WfDashFeature, WfDashLoaded, WfDashQuestion, WfDashRepo, WfDashRun } from './types/index.d.ts'
import { agentStatus, alert, color, glyph, pane, shortTab, space, specStatus, state, stateHelp, stateOrder, tinyTab } from './tokens.ts'

type El = { Box: any; Text: any; Button: any }
export type View = { section: string; tab: string; page: number; sel: number; bpos: number; apos?: number }
export type Act = { go: (v: Partial<View>) => void; retry: () => void }
type Plan = WfDashLoaded<{ repos: WfDashRepo[] }> | undefined
type Runner = WfDashLoaded<{ runs: WfDashRun[] | null; questions: WfDashQuestion[] | null }> | undefined

export const SECTIONS = [
  { id: 'plan', key: 'p', label: 'Plan' },
  { id: 'builds', key: 'b', label: 'Builds' },
  { id: 'agents', key: 'a', label: 'Agents' },
  { id: 'alerts', key: 'l', label: 'Alerts' },
]

// Plan filters, in the order of their digit keys; `states` null means every open feature.
export const PLAN_TABS: { id: string; label: string; states: string[] | null; done?: boolean; empty: string }[] = [
  { id: 'needs-you', label: 'Needs you', states: ['waits on you'], empty: 'Nothing waits on you. A step only you can do (a login, a check on your phone) lands here.' },
  { id: 'building', label: 'Building', states: ['building'], empty: 'Nothing is building. A feature lands here while wf builds it.' },
  { id: 'publish', label: 'To publish', states: ['to publish', 'in review'], empty: 'Nothing to publish. A feature lands here once it is built on its branch, until its PR is merged.' },
  { id: 'ready', label: 'Ready', states: ['ready to build'], empty: 'Nothing is ready to build. A feature lands here once its design is accepted.' },
  { id: 'design', label: 'Needs design', states: ['needs a design'], empty: 'Nothing needs a design. A feature lands here while a decision is owed (/architect).' },
  { id: 'progress', label: 'In progress', states: ['in progress'], empty: 'Nothing is in progress. A feature lands here when it is partly done.' },
  { id: 'built', label: 'Built', states: ['done', 'done (untagged)'], done: true, empty: 'Nothing built yet. A feature lands here once it is built and merged.' },
  { id: 'open', label: 'All open', states: null, empty: 'Nothing open.' },
]

export const DEFAULT_VIEW: View = { section: 'plan', tab: 'needs-you', page: 0, sel: 0, bpos: 0 }

const hhmm = (ms: number) => {
  const d = new Date(ms)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
const isoTime = (iso: string | null) => (iso && /T(\d\d:\d\d)/.exec(iso)?.[1]) || glyph.unknown
const stateOf = (s: string) => (state as Record<string, { color: string; word: string }>)[s.replace(' (untagged)', '')] ?? { color: color.text, word: s }
const rank = (s: string) => {
  const i = (stateOrder as readonly string[]).indexOf(s.replace(' (untagged)', ''))
  return i < 0 ? stateOrder.length : i
}
// "done (untagged)" is the done group: one state, one group
const norm = (s: string) => s.replace(' (untagged)', '')
const isDone = (s: string) => ['done', 'dropped', 'existing'].includes(s.replace(' (untagged)', ''))
// the box's command is what the next step runs; a PR number says where a finished feature waits
// a box's text without backticks and without the scope's trailing tags (" . waits on you", " . live"): plan markup, not words
export const untag = (s: string) => s.replace(/`/g, '').replace(/\s+[.·]\s+(waits on you|later boxes go on|live|skipped)\b.*$/, '')
const step = (f: WfDashFeature) => (f.pr ? `PR #${f.pr} ${f.prState}` : f.command ?? untag(f.next ?? ''))
// "/check verify x" -> "verify": the step's kind in one word
const kind = (cmd: string) => {
  const m = /^\/(\w+)(?:\s+(\w+))?/.exec(cmd)
  if (!m) return cmd
  const verbs: Record<string, string> = { develop: 'build', architect: 'design', test: 'test', debug: 'debug', sync: 'sync', scope: 'plan' }
  return m[1] === 'check' ? (m[2] ?? 'check') : verbs[m[1]] ?? m[1]
}

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
        <Text color={color.dim}>r tries again. If it keeps failing, wf itself may be down: run wf queue in a terminal to see.</Text>
      </Box>
    )
  }
  return <Box marginTop={space.line}><Text color={color.dim}>{`Reading ${what}...`}</Text></Box>
}

// -- Plan ----------------------------------------------------------------------------------------------------------

type Line = { kind: 'group'; name: string; note: string; tone?: string } | { kind: 'feature'; f: WfDashFeature; repo: string } | { kind: 'note'; text: string; tone: string }

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
export function planLines(repos: WfDashRepo[], tab: (typeof PLAN_TABS)[number]): Line[] {
  const picked = repos.flatMap(r =>
    r.error || r.hub ? [] : (r.features ?? []).filter(f => !f.deferred && (tab.states ? tab.states.includes(f.state) : !isDone(f.state))).map(f => ({ f, repo: r.name })))
  const lines: Line[] = []
  const groups = [...new Set(picked.map(p => p.f.state.replace(' (untagged)', '')))].sort((a, b) => rank(a) - rank(b))
  for (const g of groups) {
    const members = picked.filter(p => p.f.state.replace(' (untagged)', '') === g)
    // one group on a single-state filter: the filter tab already says the state and the count, so the row goes to a feature
    if (groups.length > 1 || tab.id === 'open') lines.push({ kind: 'group', name: stateOf(g).word, note: `${members.length}`, tone: stateOf(g).color })
    members.forEach(p => lines.push({ kind: 'feature', f: p.f, repo: p.repo }))
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

// The runner writes "<what it needs> in <feature>. <detail>"; the row above already names the feature, so drop it.
export function askText(question: string, feature: string): string {
  return question.split(` in ${feature}`).join('').replace(/\s{2,}/g, ' ').trim()
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

function PlanSection({ el, plan, view, act, columns, extra = 0 }: { el: El; plan: Plan; view: View; act: Act; columns: number; extra?: number }) {
  const { Box, Text } = el
  if (!plan?.data) return loading(el, 'the plan', plan, act)
  const repos = plan.data.repos
  const all = repos.flatMap(r => r.features ?? []).filter(f => !f.deferred)
  const count = (t: (typeof PLAN_TABS)[number]) => all.filter(f => (t.states ? t.states.includes(f.state) : !isDone(f.state))).length
  const tab = PLAN_TABS.find(t => t.id === view.tab) ?? PLAN_TABS[0]
  const pageList = paginate(planLines(repos, tab), pane.page + extra)
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
  // n: the first feature of the next state group, wrapping to the top
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
  // the detail block: next step first, wrapped to two lines when it runs long, then what the state means, then the ids;
  // never the state word again (the group heading says it)
  const detail = (() => {
    if (!chosen) return []
    const cells = Math.max(pane.minWrap, inner - space.indent)
    const help = stateHelp[chosen.state.replace(' (untagged)', '')]
    // position first, so a narrow pane never cuts it; the repo only when the rows on screen do not already show it
    const meta = [
      `${sel + 1} of ${feats.length}`,
      chosen.pr ? `PR #${chosen.pr} ${chosen.prState}` : '',
      chosen.spec ? (isDone(chosen.state) ? `spec ${chosen.spec}` : `spec ${chosen.spec}: ${specStatus[chosen.specStatus ?? 'unknown'] ?? chosen.specStatus}`) : 'no spec',
      !repoCol && new Set(feats.map(x => x.line.repo)).size > 1 ? feats[sel].line.repo : '',
    ].filter(Boolean).join('  ')
    // the name cell's width in the list row; when the row cut the name (or its repo), the detail shows them in full first
    const nameCells = inner - pane.col.cursor - 2 * space.tight - (repoCol ? pane.col.repo + space.tight : 0)
      - (wide && !isDone(chosen.state) ? pane.col.next + space.tight : 0) - (wide ? pane.col.spec + space.tight : 0)
    const heading = chosen.heading.replace(/`/g, '')
    const repo = feats[sel].line.repo
    const cut = heading.length > nameCells || (repoCol && repo.length > pane.col.repo - space.tight)
    const out = cut ? [{ t: repoCol ? `${heading}  ${repo}` : heading, tone: color.text }] : []
    const room = pane.detail - 1 - out.length
    const next = isDone(chosen.state) ? [] : wrapWords(`next: ${untag(chosen.next ?? chosen.command ?? glyph.unknown)}`, cells, room)
    out.push(...next.map(t => ({ t, tone: color.text })))
    if (out.length < pane.detail - 1 && help) out.push({ t: help, tone: color.dim })
    out.push({ t: meta, tone: color.dim })
    return out
  })()
  return (
    <Box flexDirection="column">
      {wide && (
        <Text color={color.dim} wrap="truncate-end">
          {tab.id === 'needs-you' ? "Steps only you can do. wf's own questions are in Builds." : 'Every plan, grouped by what each feature needs next.'}
        </Text>
      )}
      {tabRows.map(row =>
        keyRow(el, row.map(({ t, text }) => ({ key: String(PLAN_TABS.indexOf(t) + 1), label: text, on: t.id === tab.id, mark: true, press: () => act.go({ tab: t.id, sel: 0 }) })), wide ? space.gap : space.tight))}
      {/* a fixed height, padded with blank rows, so switching filters never moves the layout under the fingers */}
      <Box flexDirection="column" height={extra ? Math.max(pane.page, Math.min(pane.page + extra, pageList[page].length)) : pane.page}>
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
      </Box>
      {/* every key always bound, dim when it would do nothing: an unbound key falls through to the prompt and takes focus */}
      {keyRow(el, [
        { key: 'j', label: 'down', on: feats.length > 1, press: () => act.go({ sel: Math.max(0, Math.min(feats.length - 1, sel + 1)) }) },
        { key: 'k', label: 'up', on: feats.length > 1, press: () => act.go({ sel: Math.max(0, sel - 1) }) },
        { key: 'd', label: `${wide ? 'page down' : 'pg'} ${page + 1}/${pages}`, on: page < pages - 1, press: () => act.go({ sel: page < pages - 1 ? pageFirst(page + 1) : sel }) },
        { key: 'u', label: wide ? 'page up' : 'back', on: page > 0, press: () => act.go({ sel: page > 0 ? pageFirst(page - 1) : sel }) },
        { key: 'n', label: wide ? 'next group' : 'group', on: new Set(feats.map(x => norm(x.line.f.state))).size > 1, press: () => act.go({ sel: nextGroup() }) },
        { key: 'g', label: 'top', on: sel > 0, press: () => act.go({ sel: 0 }) },
      ], wide ? space.gap : space.tight)}
      {plan.error && <Text color={color.warn}>{`stale since ${hhmm(plan.at ?? Date.now())}: the last refresh failed (${plan.error}); r tries again`}</Text>}
    </Box>
  )
}

// -- Builds (the runner) -------------------------------------------------------------------------------------------

type Item = { rows: number; draw: () => any; heading?: boolean; run?: string }

function BuildsSection({ el, runner, view, act, columns, extra = 0 }: { el: El; runner: Runner; view: View; act: Act; columns: number; extra?: number }) {
  const { Box, Text } = el
  if (!runner?.data) return loading(el, 'the builds', runner, act)
  const { runs, questions } = runner.data
  const full = (runs ?? []).length <= pane.fullRuns
  const heading = (word: string, n: number, tone: string): Item => ({
    rows: 1,
    heading: true,
    draw: () => <Box flexDirection="row" gap={space.tight}><Text color={tone} bold>{word}</Text><Text color={color.dim}>{`${n}`}</Text></Box>,
  })
  // what waits on you sits in its own block above the runs, so it never falls below the fold
  const items: Item[] = [
    ...((questions ?? []).length ? [heading(state['waits on you'].word, questions!.length, state['waits on you'].color)] : []),
    ...(questions ?? []).map(q => {
      // every reply option shown, wrapped to two lines if need be (they are the point of the row); the ask, without the
      // "in <feature>" the row above names, keeps its two lines: it says what to decide
      const w = Math.max(pane.minWrap, columns - 2 * space.padX - space.indent)
      const prefix = columns >= pane.specMin ? `reply on your phone to question ${q.id}:` : `on phone, ${q.id}:`
      const reply = wrapWords(`${prefix}  ${q.options.map((o, i) => `${i + 1} ${o}`).join('  ')}`, w, 2)
      const ask = wrapWords(askText(q.question, q.feature), w, 2)
      return {
      rows: 1 + ask.length + reply.length,
      draw: () => (
        <Box flexDirection="column">
          {/* fixed cells: a bare Text in a row wraps mid-word in a narrow pane and breaks the row budget */}
          <Box flexDirection="row">
            {cell(Box, Text, q.parked ? 'stuck' : 'question', pane.col.word, { color: q.parked ? color.bad : color.warn, bold: true })}
            {cell(Box, Text, q.feature, null, { color: color.text })}
            {cell(Box, Text, q.repo, pane.col.repo, { color: color.dim })}
          </Box>
          {ask.map(t => <Box paddingLeft={space.indent}><Text color={color.text} wrap="truncate-end">{t}</Text></Box>)}
          {/* dim, not the accent: the numbers are the phone's buttons, not keys here */}
          {reply.map(t => <Box paddingLeft={space.indent}><Text color={color.dim} wrap="truncate-end">{t}</Text></Box>)}
        </Box>
      ),
      }
    }),
    ...((runs ?? []).length ? [heading(state.building.word, runs!.length, state.building.color)] : []),
    ...(runs ?? []).map(r => {
      const steps = full ? r.steps.slice(-pane.steps) : []
      return {
        rows: 2 + steps.length,
        // the summary line names the run in a fixed width, so "now <step>" always fits beside it
        run: `${r.feature.length > pane.col.next ? r.feature.slice(0, pane.col.next - glyph.cut.length) + glyph.cut : r.feature}  now ${r.step ? kind(r.step) : glyph.unknown}`,
        draw: () => (
          <Box flexDirection="column">
            <Box flexDirection="row">
              {cell(Box, Text, r.feature, null, { color: color.text, bold: true })}
              {cell(Box, Text, r.repo, pane.col.repo, { color: color.dim })}
            </Box>
            <Box paddingLeft={space.indent}>
              <Text wrap="truncate-end">
                <Text color={color.dim}>now </Text>
                <Text color={color.text} bold>{r.step ? kind(r.step) : r.calls === 0 ? 'starting' : glyph.unknown}</Text>
                <Text color={color.dim}>
                  {'  ' + (r.calls ? `${r.calls} ${r.calls === 1 ? 'step' : 'steps'} so far, ${r.cost === null ? glyph.unknown : `$${r.cost.toFixed(2)}`}, started ${isoTime(r.startedAt)}` : `started ${isoTime(r.startedAt)}`)}
                </Text>
              </Text>
            </Box>
            {steps.map(st => (
              <Box flexDirection="row" paddingLeft={space.indent}>
                {cell(Box, Text, isoTime(st.started), pane.col.time, { color: color.dim })}
                {cell(Box, Text, kind(st.command), pane.col.word, { color: color.text })}
                {cell(Box, Text, st.ok ? 'ok' : 'failed', pane.col.result, { color: st.ok ? color.ok : color.bad, bold: !st.ok })}
                {cell(Box, Text, `${st.minutes}m  ${st.cost === null ? glyph.unknown : `$${st.cost.toFixed(2)}`}`, null, { color: color.dim })}
              </Box>
            ))}
          </Box>
        ),
      }
    }),
  ]
  // show what fits from the scroll position; the rest is counted, never silently cut
  const start = Math.min(view.bpos ?? 0, Math.max(0, items.length - 1))
  const shown: Item[] = []
  let used = 0
  const rest = items.slice(start)
  for (const [i, it] of rest.entries()) {
    // a heading only comes with its first item, never alone at the foot
    const need = it.heading && rest[i + 1] ? it.rows + rest[i + 1].rows : it.rows
    if (shown.length && used + need > pane.buildRows + extra) break
    shown.push(it)
    used += it.rows
  }
  // headings are not items the reader is missing; count only questions and runs below the fold
  const below = items.slice(start + shown.length).filter(it => !it.heading).length
  // runs scrolled out of view are still named, so the band's run count always has a match here
  const hiddenRuns = items.slice(start + shown.length).flatMap(it => (it.run ? [it.run] : []))
  return (
    <Box flexDirection="column">
      {columns >= pane.specMin && <Text color={color.dim}>What wf builds on its own right now, and what it asks you.</Text>}
      {runs === null && <Text color={color.bad}>Could not read what wf is building.</Text>}
      {runs !== null && runs.length === 0 && !(questions ?? []).length && <Text color={color.dim}>wf is not building anything right now, and asks you nothing.</Text>}
      {shown.map(it => it.draw())}
      {/* a run below the fold still gets its own line, so "is it running?" is answered without scrolling */}
      {hiddenRuns.length > 0 && (
        <Text wrap="truncate-end">
          <Text color={state.building.color} bold>{`${state.building.word} `}</Text>
          <Text color={color.text}>{hiddenRuns[0]}</Text>
          <Text color={color.dim}>{hiddenRuns.length > 1 ? `  +${hiddenRuns.length - 1}` : ''}</Text>
        </Text>
      )}
      {/* the runs below are named by the summary line, so "more" counts only the questions still below */}
      {(start > 0 || below - hiddenRuns.length > 0) && (
        <Text color={color.dim}>{[start > 0 ? `${start} above` : '', below - hiddenRuns.length > 0 ? `+${below - hiddenRuns.length} more` : ''].filter(Boolean).join(', ')}</Text>
      )}
      {keyRow(el, [
        { key: 'j', label: 'down', on: below > 0, press: () => act.go({ bpos: below > 0 ? start + 1 : start }) },
        { key: 'k', label: 'up', on: start > 0, press: () => act.go({ bpos: Math.max(0, start - 1) }) },
      ])}
    </Box>
  )
}

// -- Agents --------------------------------------------------------------------------------------------------------

function AgentsSection({ el, agents, columns }: { el: El; agents: any[] | null; columns: number }) {
  const { Box, Text } = el
  if (agents === null) return <Box marginTop={space.line}><Text color={color.bad}>Could not list this session's agents.</Text></Box>
  return (
    <Box flexDirection="column">
      {columns >= pane.specMin && <Text color={color.dim}>The agents this chat started, and what each is doing.</Text>}
      <Box flexDirection="column">
        {/* an empty list from the mod API is not proof of no agents: the host's own count may still show some */}
        {agents.length === 0 && <Text color={color.dim}>No agents listed. The host's own agent count below the prompt may still show some.</Text>}
        {agents.map(a => (
          <Box flexDirection="row">
            {cell(Box, Text, a.status, pane.col.state, { color: (agentStatus as Record<string, string>)[a.status] ?? color.text, bold: a.status === 'running' })}
            {cell(Box, Text, a.description || a.name || a.id, null, { color: color.text })}
            {cell(Box, Text, a.type, pane.col.next, { color: color.dim })}
          </Box>
        ))}
      </Box>
      <Text color={color.dim}>Background shells are not listed: the mod API has no call for them yet.</Text>
    </Box>
  )
}

// -- Alerts --------------------------------------------------------------------------------------------------------

function AlertsSection({ el, alerts, view, act, columns, extra = 0 }: { el: El; alerts: WfDashAlert[]; view: View; act: Act; columns: number; extra?: number }) {
  const { Box, Text } = el
  const list = [...alerts].reverse()
  // details print in full, so an alert takes its title row plus the rows its detail wraps to
  const textCells = Math.max(1, columns - 2 * space.padX - pane.col.kind - space.tight)
  const rows = (a: WfDashAlert) => 1 + Math.max(1, Math.ceil(a.detail.length / textCells))
  const start = Math.min(view.apos ?? 0, Math.max(0, list.length - 1))
  let used = 0
  let end = start
  while (end < list.length && (end === start || used + rows(list[end]) <= pane.buildRows + extra)) used += rows(list[end++])
  const below = list.length - end
  return (
    <Box flexDirection="column">
      {columns >= pane.specMin && <Text color={color.dim}>Every alert this session, newest first. Each also shows at the top right for 15 s.</Text>}
      {list.length === 0 && <Text color={color.dim}>No alerts yet. When wf finishes a feature, gets stuck or asks you something, it lands here.</Text>}
      {/* inbox rows, Linear style: kind and feature on the title line with the time at the right, the detail in full below */}
      {list.slice(start, end).map(a => (
        <Box flexDirection="column">
          <Box flexDirection="row">
            {cell(Box, Text, a.kind, pane.col.kind, { color: alert[a.kind], bold: true })}
            {cell(Box, Text, a.feature, null, { color: color.text, bold: true })}
            <Box width={pane.col.clock} flexShrink={0} justifyContent="flex-end"><Text color={color.dim}>{hhmm(a.at)}</Text></Box>
          </Box>
          <Box paddingLeft={pane.col.kind + space.tight}><Text color={color.dim}>{a.detail}</Text></Box>
        </Box>
      ))}
      {(start > 0 || below > 0) && (
        <Text color={color.dim}>{[start > 0 ? `${start} newer above` : '', below > 0 ? `+${below} older` : ''].filter(Boolean).join(', ')}</Text>
      )}
      {keyRow(el, [
        { key: 'j', label: 'down', on: below > 0, press: () => act.go({ apos: below > 0 ? start + 1 : start }) },
        { key: 'k', label: 'up', on: start > 0, press: () => act.go({ apos: Math.max(0, start - 1) }) },
      ])}
    </Box>
  )
}

// -- The dashboard -------------------------------------------------------------------------------------------------

export function Dashboard({ el, view, act, plan, runner, agents, alerts, facts, columns, focused = true, rows }: {
  el: El; view: View; act: Act; plan: Plan; runner: Runner; agents: any[] | null; alerts: WfDashAlert[]; columns: number; focused?: boolean; rows?: number
  facts: { running: number | null; parked: number | null; questions: number | null } | null
}) {
  const { Box, Text } = el
  const section = SECTIONS.find(s => s.id === view.section) ?? SECTIONS[0]
  // a docked pane's rows past the inline budget go to the lists, so the room is used, not left blank
  const extra = rows ? Math.max(0, rows - pane.baseRows) : 0
  return (
    <Box flexDirection="column" paddingX={space.padX}>
      <Box flexDirection="row" columnGap={space.gap}>
        <Text backgroundColor={color.accent} color="inverseText" bold>{' wf-dash '}</Text>
        {keyRow(el, SECTIONS.map(s => ({ key: s.key, label: s.label, on: s.id === section.id, mark: true, press: () => act.go({ section: s.id }) })), columns >= pane.specMin ? space.gap : space.tight)}
      </Box>
      {/* a stray key hands the keyboard to the prompt; say so, and how to come back, instead of failing silently.
          This used to name the host's focus key, which did not give the keys back in a real terminal; a click did (spec 0062 P11) */}
      {!focused && <Text color={color.warn} wrap="truncate-end">Keys go to the prompt now: click the dashboard to return</Text>}
      <Box flexDirection="column">
        {section.id === 'plan' && <PlanSection el={el} plan={plan} view={view} act={act} columns={columns} extra={extra} />}
        {section.id === 'builds' && <BuildsSection el={el} runner={runner} view={view} act={act} columns={columns} extra={extra} />}
        {section.id === 'agents' && <AgentsSection el={el} agents={agents} columns={columns} />}
        {section.id === 'alerts' && <AlertsSection el={el} alerts={alerts} view={view} act={act} columns={columns} extra={extra} />}
      </Box>
      <Box flexDirection="row" columnGap={space.gap} flexWrap="wrap">
        {keyRow(el, [{ key: 'r', label: 'refresh', on: true, press: act.retry }])}
        <Text color={color.dim}>esc closes</Text>
      </Box>
    </Box>
  )
}
