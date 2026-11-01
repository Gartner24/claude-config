import type { Register } from 'claude-code'
import { Band, HandoffRow, liveBuilds, type Facts } from '../band.tsx'
import { handoffLine } from '../handoff.ts'
import { parseOwed, parsePrs, prArgv } from '../now.ts'
import { DEFAULT_VIEW, Dashboard, safeStep } from '../panes.tsx'
import type { WfDashAsk, WfDashOwed } from '../types/index.d.ts'
import { color, pane, space, time, width } from '../tokens.ts'

// chip-dash: the band (spec 0059) reads this session and wf-handoff's files; the dashboard (spec 0060) reads plan.py and
// offers two actions, each behind a confirm; its Now view (spec 0071) reads the catch state file and one gh search.
// The drawing in band.tsx and panes.tsx is the locked look. Nothing here runs or reads the retired wf runner.

const FACTS = { plugin: 'chip-dash', key: 'facts' } as const
const EFFORT = { plugin: 'chip-dash', key: 'effort' } as const
const PLAN = { plugin: 'chip-dash', key: 'plan' } as const
const VIEW = { plugin: 'chip-dash', key: 'view' } as const
const HANDOFF = { plugin: 'chip-dash', key: 'handoff' } as const
const PRS = { plugin: 'chip-dash', key: 'prs' } as const
const BUILD = { plugin: 'chip-dash', key: 'build' } as const
const PANE = 'chip-dash'
// P9: a prompt submitted from inside the confirming hook does not start a turn; from the clock after it returns, it does.
// The host refuses $.prompt.submit of a text starting with "/" (it would run a command as the user), so the step goes
// through $.command.run, which runs it as if typed, once the session is idle.
const SUBMIT_AFTER = 1500
// an effort level as the settings spell one
const LEVEL = /^[a-z]{1,20}$/

// shortcut: module values, so a hot reload forgets the dashboard is open until it is opened again; fine for a preview
let isOpen = false
let loadPanes = async (_force = false) => {}
let loadPrs = async (_force = false) => {}
// spec 0074 AC-12: running workflow agents, agentId -> spawn time, from agent.spawn and turn.complete. shortcut: a
// module value, so a mod reload starts the count at 0 ($.agent.list() leaves workflow agents out); accepted in the spec
const building = new Map<string, number>()

async function countBuilds($: any) {
  const n = liveBuilds(building, await $.clock.now())
  if ((await $.state.get(BUILD)).value !== n) await $.state.set(BUILD, n)
}

function clock(ms: number) {
  const d = new Date(ms)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// AC-5: no API lists background shells; their ids are only in the Bash result text (probe P8). One stopped by a
// TaskStop (the model's, or this mod's, which the transcript does not hold) or named by a later task notice is left
// out; the rest are only "started": one may have ended without the transcript saying so.
// Security review: only a background Bash call's own result, at its start, so quoted output never adds a row.
const SHELL_ID = /^Command running in background with ID:\s*([A-Za-z0-9_-]+)\./
const stoppedShells = new Set<string>()
// null when the transcript could not be read: the Now view then counts `agents ?`, never 0 shells (spec 0071 AC-6)
async function shells($: any): Promise<any[] | null> {
  const msgs = await $.session.messages().catch(() => null)
  if (!Array.isArray(msgs)) return null
  const found = new Map<string, any>()
  for (const m of msgs) {
    for (const u of m.toolUses ?? []) {
      const id = u.tool === 'Bash' && u.input?.run_in_background === true ? SHELL_ID.exec(u.text ?? '')?.[1] : null
      if (id) found.set(id, { id, description: String(u.input?.description || u.input?.command || id), type: 'shell', status: 'started' })
      if (u.tool === 'TaskStop' && !u.isError) found.delete(String(u.input?.task_id))
    }
    if (m.role === 'user') for (const id of [...found.keys()]) if ((m.text ?? '').includes(`<task-id>${id}</task-id>`)) found.delete(id)
  }
  return [...found.values()].filter(s => !stoppedShells.has(s.id))
}

// AC-5: the two confirmed actions. Nothing else is reachable: no push, merge, delete, settings or spec edit.
async function perform($: any, a: WfDashAsk): Promise<{ text: string; ok: boolean }> {
  if (a.kind === 'start') {
    if (!safeStep(a.text)) return { text: `not started, not on the safe list: ${a.text}`, ok: false }
    const [, command, args = ''] = /^\/(\S+)\s*(.*)$/.exec(a.text)!
    $.clock.after(SUBMIT_AFTER, () => void $.command.run({ command, args }).catch(() => {}))
    return { text: `starting ${a.text}`, ok: true }
  }
  const r = await $.tool.call({ tool: 'TaskStop', task_id: a.id }).catch((err: any) => ({ deny: String(err?.message ?? err) }))
  const ok = r && !('deny' in r) && !r.isError
  if (ok) stoppedShells.add(a.id)
  return ok ? { text: `stopped ${a.label}`, ok: true } : { text: `could not stop ${a.label}: ${r?.deny ?? r?.text ?? 'no answer'}`, ok: false }
}

async function openDashboard($: any) {
  isOpen = true
  void loadPanes(true)
  await $.ui.open({ id: PANE, title: 'chip-dash', focus: true, closeOnEscape: true, rows: pane.rows })
  // reopened on Now: Now opens, so the PR search runs (spec 0071 AC-4); after the open, so the engine lists the pane.
  // On any other view it does nothing
  void loadPrs(true)
  return { text: 'chip-dash open: p n a switch views, esc closes' }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    let lastGood: Facts | null = null
    let factsRead = false
    let busy = false
    const id = await $.session.id().catch(() => '')
    const home = await $.env.get('HOME')
    const handoffDir = `${home}/.claude/state/auto-handoff`
    const catchDir = `${home}/.claude/state/chain-catch`
    const panelPath = `${handoffDir}/panel.json`
    let me = id
    let prev: string | null = null

    // /auto-handoff on or off, and the line: the chain file wf-handoff's save() writes, found the way its own
    // session.start finds it (a handed off chat points at its chain's root). No file names this chat: null, never on.
    const readAuto = async () => {
      const root = (await $.fs.read(`${handoffDir}/${me}.root`).catch(() => '')).trim() || me
      let c: any = null
      try { c = JSON.parse(await $.fs.read(`${handoffDir}/${root}.json`)) } catch {}
      return c && c.session === me ? { off: c.off === true, line: typeof c.line === 'number' ? c.line : null } : null
    }

    // Spec 0064 AC-2, AC-6: the wf-handoff mod's panel. A /clear keeps this module but changes the id, so the
    // id before it is the chat this one came from. A panel another chat wrote keeps the last one that was ours.
    const readPanel = async () => {
      const now = await $.session.id().catch(() => me)
      if (now && now !== me) { prev = me; me = now }
      const raw = await $.fs.read(panelPath).catch(() => null)
      let p: any = null
      try { p = raw ? JSON.parse(raw) : null } catch {}
      const { value: old } = await $.state.get(HANDOFF)
      const mine = p && typeof p.session === 'string' && Array.isArray(p.steps) && (p.session === me || p.session === prev)
      await $.state.set(HANDOFF, { panel: mine ? p : old?.panel ?? null, me, prev, dismissed: old?.dismissed ?? 0, frame: old?.frame ?? 0, auto: await readAuto() })
    }

    // Spec 0071 AC-2, AC-7: what this chat owes, from spec 0070's catch file under this chat's id, else the id it
    // replaced after a /clear (readPanel keeps both). A check or a read that fails is unknown (`owed ?` and the
    // error), never "not installed" or "nothing owed": it used to read a rejected exists as false (PR 164 review).
    const readOwed = async (): Promise<WfDashOwed> => {
      try {
        if (!(await $.fs.exists(catchDir))) return { installed: false, lines: null, error: null }
        for (const sid of [me, prev]) {
          const path = `${catchDir}/${sid}.json`
          if (!sid || !(await $.fs.exists(path))) continue
          return parseOwed(await $.fs.read(path))
        }
        return { installed: true, lines: [], error: null }
      } catch (err: any) {
        return { installed: true, lines: null, error: String(err?.message ?? err) }
      }
    }

    const refresh = async () => {
      if (busy) return
      busy = true
      try {
        await readPanel()
        const owed = await readOwed()
        const cwd = await $.session.cwd()
        const [r, usage, model, setLevel] = await Promise.all([
          $.process.run(['python3', `${$.plugin.root}/facts.py`, cwd]).catch(() => null),
          $.session.usage().catch(() => null),
          $.session.model().catch(() => null),
          // the settings' effortLevel stands in until the first reply brings the real one (turn.step). Env vars are the
          // parent shell's and showed `high` in a `medium` session: never read.
          $.settings.read({ key: 'effortLevel' }).catch(() => null),
        ])
        let parsed: any = null
        try { parsed = r && r.exitCode === 0 ? JSON.parse(r.stdout || 'null') : null } catch {}
        // facts.py failing from the start must not hide the band: its fields show `?` until it first answers; only a
        // failure after that keeps the last good facts, marked stale
        if (parsed) factsRead = true
        const raw = parsed ?? (factsRead ? null : {})
        const limit = (kind: string) => usage?.rateLimits?.find((x: any) => x.kind === kind) ?? null
        if (raw) {
          lastGood = {
            model,
            effort: typeof setLevel === 'string' && LEVEL.test(setLevel) ? setLevel : null,
            folder: raw.folder ?? null,
            git: raw.git ?? null,
            context: usage?.context?.percent ?? null,
            contextTokens: usage?.context?.tokens ?? null,
            contextWindow: usage?.context?.window ?? null,
            fiveHour: limit('five_hour')?.percentUsed ?? null,
            fiveHourReset: limit('five_hour')?.resetsAt ?? null,
            week: limit('seven_day')?.percentUsed ?? null,
            weekReset: limit('seven_day')?.resetsAt ?? null,
            via: raw.via ?? null,
            profile: raw.profile ?? null,
            staleSince: null,
            owed,
          }
          await $.state.set(FACTS, lastGood)
        } else if (lastGood) {
          // a failed tick keeps the last good facts, marked stale, never an empty band; the mark keeps its first time.
          // The owed count is its own read, so it stays current while facts.py fails.
          lastGood = { ...lastGood, owed, staleSince: lastGood.staleSince ?? clock(await $.clock.now()) }
          await $.state.set(FACTS, lastGood)
        }
      } finally {
        busy = false
      }
    }

    // AC-2: never two plan.py calls at once (a tick is skipped while one runs); a failed or timed out call keeps the
    // last good plan, marked with the error, never an empty one
    let planBusy = false
    loadPanes = async (force = false) => {
      if (planBusy || !(force || isOpen)) return
      planBusy = true
      try {
        const r = await $.process.run(['python3', `${$.plugin.root}/plan.py`]).catch(() => null)
        let data = null
        try {
          data = r && r.exitCode === 0 ? JSON.parse(r.stdout) : null
        } catch {}
        const ok = !!data && Array.isArray(data.repos)
        const { value: old } = await $.state.get(PLAN)
        const error = ok ? null : r ? (r.exitCode === 0 ? 'not the expected JSON' : `exit ${r.exitCode}`) : 'did not run or timed out'
        await $.state.set(PLAN, ok ? { data, at: await $.clock.now(), error } : { data: old?.data ?? null, at: old?.at ?? null, error })
      } finally {
        planBusy = false
      }
    }

    // Spec 0071 AC-3, AC-4: the one PR search, only while the dashboard is open on Now: when Now opens and on r
    // (force), and every 2 minutes on the panes' tick. Never two at once; a failed call keeps the last list, marked.
    let prBusy = false
    let prStarted = -Infinity
    loadPrs = async (force = false) => {
      const { value: view } = await $.state.get(VIEW)
      // the engine's record of open panes first: the module's isOpen forgets an open pane on a hot reload; isOpen
      // only when the record cannot be read
      const open = (await $.ui.panes().catch(() => null))?.some((p: any) => p.id === PANE) ?? isOpen
      if (prBusy || !open || view?.section !== 'now') return
      const now = await $.clock.now()
      if (!force && now - prStarted < time.prTick) return
      prBusy = true
      prStarted = now
      try {
        const r = await $.process.run(prArgv(), { timeoutMs: time.prTimeout }).catch(() => null)
        const data = r && r.exitCode === 0 ? parsePrs(r.stdout) : null
        const said = r ? String(r.stderr ?? '').split('\n').map(l => l.trim()).find(Boolean) : ''
        const error = data ? null : !r ? 'did not run or timed out' : r.exitCode !== 0 ? said || `exit ${r.exitCode}` : 'not the expected answer'
        const { value: old } = await $.state.get(PRS)
        await $.state.set(PRS, data ? { data, at: await $.clock.now(), error } : { data: old?.data ?? null, at: old?.at ?? null, error })
      } finally {
        prBusy = false
      }
    }

    void refresh()
    $.clock.every(time.bandTick, () => { void refresh(); void countBuilds($).catch(() => {}) })
    $.clock.every(time.planTick, () => { void loadPanes(); void loadPrs() })
    // the spinner turns only while a handoff step runs, and stays on its first frame under reduced motion, as the host's does
    $.clock.every(time.spin, async () => {
      const { value: h } = await $.state.get(HANDOFF)
      if (!(h?.panel && !h.panel.sticky && h.panel.steps.some(s => s.state === 'running'))) return
      if ((await $.settings.read().catch(() => null) as any)?.prefersReducedMotion) return
      await $.state.set(HANDOFF, { ...h, frame: h.frame + 1 })
    })

    for (const name of ['chip', 'wf-dash']) await $.command.register({ name, description: 'chip-dash: the plan, what this chat owes and your PRs, and its agents in one dashboard' })
    return started
  })

  for (const command of ['chip', 'wf-dash']) on('command.run', { command }, async $ => openDashboard($))

  on('ui.close', async ($, e, next) => {
    if (e.id === PANE) isOpen = false
    return next(e)
  })

  // Spec 0064 AC-2: a sticky handoff line goes once the owner types.
  on('prompt.submit', async ($, e, next) => {
    if (e.origin.kind === 'composer' || e.origin.kind === 'bridge') {
      // never in the way of the prompt: a failed read or write only keeps the line
      const h = (await $.state.get(HANDOFF).catch(() => null))?.value
      if (h?.panel?.sticky) await $.state.set(HANDOFF, { ...h, dismissed: await $.clock.now() }).catch(() => {})
    }
    return next(e)
  })

  // spec 0074 AC-12: probe P1 saw agent.spawn carry e.workflow for each workflow agent and turn.complete its agentId
  on('agent.spawn', async ($, e, next) => {
    const r = await next(e)
    // never in the way of a spawn: a failed count only leaves the band behind
    try {
      const id = e.workflow && r && !('deny' in r) ? (r as any).agentId : null
      if (id) {
        building.set(id, await $.clock.now())
        await countBuilds($)
      }
    } catch {}
    return r
  })

  on('turn.complete', async ($, e, next) => {
    if (e.agentId && building.delete(e.agentId)) await countBuilds($).catch(() => {})
    return next(e)
  })

  // The real effort rides on every main-loop model request; the band shows it from the first reply on.
  on('turn.step', async function* ($, e, next) {
    if (!e.agentId && e.effort !== undefined) {
      const level = String(e.effort)
      const { value } = await $.state.get(EFFORT)
      if (value !== level) await $.state.set(EFFORT, level)
    }
    return yield* next(e)
  })

  // The host raises the band on the terminal and the desktop; it used to draw on the terminal only, so a desktop
  // chat had no band at all. A survey holds the band while it asks.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if ((e.surface !== 'terminal' && e.surface !== 'desktop') || e.props.hasSurvey) return next(e)
    const { Box, Text, Button } = $.ui.resolve(e)
    const { value: facts } = await $.state.get(FACTS)
    const { value: level } = await $.state.get(EFFORT)
    const { value: handoff } = await $.state.get(HANDOFF)
    const { value: build } = await $.state.get(BUILD)
    const line = handoff ? handoffLine(handoff, Date.now()) : null
    // the latest main loop request's level first, then the settings' one; unknown stays out
    const value = facts && { ...facts, build: build ?? 0, effort: level || facts.effort, ...(handoff && 'auto' in handoff ? { handoff: handoff.auto ?? null } : {}) }
    const band = value
      ? <Band Box={Box} Text={Text} Button={Button} facts={value} columns={e.props.bodyColumns ?? (e.viewport?.columns ?? width.viewport) - space.hostReserve} onOpen={() => void openDashboard($)} />
      : (
        <Box paddingX={space.padX}>
          <Text color={color.dim}>chip-dash: reading status</Text>
        </Box>
      )
    if (!line) return band
    const dismiss = async () => {
      const { value: cur } = await $.state.get(HANDOFF)
      if (cur) await $.state.set(HANDOFF, { ...cur, dismissed: await $.clock.now() })
    }
    return (
      <Box flexDirection="column" width="100%">
        {band}
        <HandoffRow Box={Box} Text={Text} Button={Button} line={line} onDismiss={() => void dismiss()} />
      </Box>
    )
  })

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if ((e as any).requestId !== PANE || e.surface !== 'terminal') return next(e)
    const el = $.ui.resolve(e)
    const { value: view = DEFAULT_VIEW } = await $.state.get(VIEW)
    const { value: plan } = await $.state.get(PLAN)
    const live = view.section === 'agents' || view.section === 'now'
    const listed = live ? await $.agent.list().catch(() => null) : []
    // a shell row never shares an id with an agent, so its stop can never reach one
    const sh = listed && live ? (await shells($))?.filter(s => !listed.some((a: any) => a.id === s.id)) ?? null : []
    const agents = listed && view.section === 'agents' ? [...listed, ...(sh ?? [])] : listed
    // spec 0071 AC-6: the Now view's one line, from the Agents view's own lists
    const count = listed && sh ? { running: listed.filter((a: any) => a.status === 'running').length, shells: sh.length } : null
    const cwd = await $.session.cwd().catch(() => null)
    const go = async (v: Partial<typeof view>) => {
      const { value: now = DEFAULT_VIEW } = await $.state.get(VIEW)
      await $.state.set(VIEW, { ...now, ...v })
      if (v.section === 'now' && now.section !== 'now') void loadPrs(true)
    }
    const act = {
      go: (v: Partial<typeof view>) => void go(v),
      retry: () => { void loadPanes(true); void loadPrs(true) },
      run: (a: WfDashAsk) => void perform($, a).then(notice => go({ notice })),
    }
    const extras = view.section === 'now'
      ? { prs: (await $.state.get(PRS)).value, owed: (await $.state.get(FACTS)).value?.owed, handoff: (await $.state.get(HANDOFF)).value, count }
      : {}
    return <Dashboard el={el} view={view} act={act} plan={plan} cwd={cwd} agents={agents as any[] | null} focused={e.props.isFocused !== false} rows={e.props.placement === 'dock' ? e.props.scroll?.bodyRows : undefined} columns={e.props.bodyColumns ?? (e.viewport?.columns ?? width.viewport) - pane.frame} {...extras} />
  })
}
