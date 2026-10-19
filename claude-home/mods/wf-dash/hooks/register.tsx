import type { Register } from 'claude-code'
import { alertTick, counts, parseStatus } from '../alerts.ts'
import { Band, HandoffRow, type Facts } from '../band.tsx'
import { handoffLine } from '../handoff.ts'
import { DEFAULT_VIEW, Dashboard, safeStep } from '../panes.tsx'
import type { WfDashAsk } from '../types/index.d.ts'
import { color, pane, space, time, width } from '../tokens.ts'

// wf-dash: the band and alerts (spec 0059) read `wf status --json`; the dashboard (spec 0060) reads `wf plan --json`
// and offers three actions, each behind a confirm. The drawing in band.tsx and panes.tsx is the locked look.

const FACTS = { plugin: 'wf-dash', key: 'facts' } as const
const EFFORT = { plugin: 'wf-dash', key: 'effort' } as const
const ALERTS = { plugin: 'wf-dash', key: 'alerts' } as const
const PLAN = { plugin: 'wf-dash', key: 'plan' } as const
const VIEW = { plugin: 'wf-dash', key: 'view' } as const
const HANDOFF = { plugin: 'wf-dash', key: 'handoff' } as const
const PANE = 'wf-dash'
// P9: a prompt submitted from inside the confirming hook does not start a turn; from the clock after it returns, it does.
// The host refuses $.prompt.submit of a text starting with "/" (it would run a command as the user), so the step goes
// through $.command.run, which runs it as if typed, once the session is idle.
const SUBMIT_AFTER = 1500
// what `wf auto bar` takes as a session id and an effort level (runner/auto.py); anything else names no file
const SESSION_ID = /^[A-Za-z0-9-]{1,100}$/
const LEVEL = /^[a-z]{1,20}$/

// `<state>/wf-dash` is the mod's own folder, as runner/auto.py dash_dir() names it, never under the runner's (AC-5);
// `<state>/wf/runs` holds the runner's run records, read only (runner/run.py state_dir)
async function stateDir($: any) {
  return (await $.env.get('XDG_STATE_HOME')) || `${await $.env.get('HOME')}/.local/state`
}

// shortcut: module values, so a hot reload forgets the dashboard is open until it is opened again; fine for a preview
let isOpen = false
let loadPanes = async (_force = false) => {}

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
async function shells($: any) {
  const msgs = await $.session.messages().catch(() => null)
  const found = new Map<string, any>()
  for (const m of Array.isArray(msgs) ? msgs : []) {
    for (const u of m.toolUses ?? []) {
      const id = u.tool === 'Bash' && u.input?.run_in_background === true ? SHELL_ID.exec(u.text ?? '')?.[1] : null
      if (id) found.set(id, { id, description: String(u.input?.description || u.input?.command || id), type: 'shell', status: 'started' })
      if (u.tool === 'TaskStop' && !u.isError) found.delete(String(u.input?.task_id))
    }
    if (m.role === 'user') for (const id of [...found.keys()]) if ((m.text ?? '').includes(`<task-id>${id}</task-id>`)) found.delete(id)
  }
  return [...found.values()].filter(s => !stoppedShells.has(s.id))
}

// AC-5: the three confirmed actions. Nothing else is reachable: no push, merge, delete, settings or spec edit.
async function perform($: any, a: WfDashAsk): Promise<{ text: string; ok: boolean }> {
  if (a.kind === 'start') {
    if (!safeStep(a.text)) return { text: `not started, not on the safe list: ${a.text}`, ok: false }
    const [, command, args = ''] = /^\/(\S+)\s*(.*)$/.exec(a.text)!
    $.clock.after(SUBMIT_AFTER, () => void $.command.run({ command, args }).catch(() => {}))
    return { text: `starting ${a.text}`, ok: true }
  }
  if (a.kind === 'stop') {
    const r = await $.tool.call({ tool: 'TaskStop', task_id: a.id }).catch((err: any) => ({ deny: String(err?.message ?? err) }))
    const ok = r && !('deny' in r) && !r.isError
    if (ok) stoppedShells.add(a.id)
    return ok ? { text: `stopped ${a.label}`, ok: true } : { text: `could not stop ${a.label}: ${r?.deny ?? r?.text ?? 'no answer'}`, ok: false }
  }
  const r = await $.process.run(['wf', 'answer', a.id, String(a.n)]).catch(() => null)
  void loadPanes(true)
  return r ? { text: (r.stdout || r.stderr).trim() || `exit ${r.exitCode}`, ok: r.exitCode === 0 } : { text: 'wf answer did not run', ok: false }
}

async function openDashboard($: any) {
  isOpen = true
  void loadPanes(true)
  await $.ui.open({ id: PANE, title: 'wf-dash', focus: true, closeOnEscape: true, rows: pane.rows })
  return { text: 'wf-dash open: p b a l switch views, esc closes' }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    let lastGood: Facts | null = null
    let factsRead = false
    let busy = false
    const id = await $.session.id().catch(() => '')
    const sid = SESSION_ID.test(id) ? id : null
    const state = await stateDir($)
    const dir = `${state}/wf-dash`
    const panelPath = `${await $.env.get('HOME')}/.claude/state/auto-handoff/panel.json`
    let me = id
    let prev: string | null = null

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
      await $.state.set(HANDOFF, { panel: mine ? p : old?.panel ?? null, me, prev, dismissed: old?.dismissed ?? 0, frame: old?.frame ?? 0 })
    }

    const refresh = async () => {
      if (busy) return
      busy = true
      try {
        // AC-4: the marker tells this session's `wf auto bar` to go short; its mtime is all it says
        if (sid) await $.fs.write(`${dir}/${sid}`, '').catch(() => {})
        await readPanel()
        const cwd = await $.session.cwd()
        const [r, st, usage, model, handed] = await Promise.all([
          $.process.run(['python3', `${$.plugin.root}/facts.py`, cwd]).catch(() => null),
          $.process.run(['wf', 'status', '--json']).catch(() => null),
          $.session.usage().catch(() => null),
          $.session.model().catch(() => null),
          sid ? $.fs.read(`${dir}/${sid}.effort`).catch(() => null) : null,
        ])
        const status = st && st.exitCode === 0 ? parseStatus(st.stdout) : null
        const wf = counts(status)
        const statusOk = !!wf && Object.values(wf).some(v => v !== null)
        await alertTick($, status, sid && `${dir}/${sid}.toasts`, { keep: pane.history, timeoutMs: time.toast, runs: `${state}/wf/runs` })
        const parsed = r && r.exitCode === 0 ? JSON.parse(r.stdout || 'null') : null
        // facts.py failing from the start must not hide or freeze the runner counts all session: its fields show `?`
        // until it first answers; only a failure after that keeps the last good facts, marked stale
        if (parsed) factsRead = true
        const raw = parsed ?? (factsRead ? null : {})
        const limit = (kind: string) => usage?.rateLimits?.find((x: any) => x.kind === kind) ?? null
        if (raw) {
          lastGood = {
            model,
            // the level `wf auto bar` handed over from the status line's own `.effort.level`; else the render falls back
            // to turn.step. Env vars are the parent shell's and showed `high` in a `medium` session: never read.
            effort: typeof handed === 'string' && LEVEL.test(handed) ? handed : null,
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
            wf,
            auto: raw.auto ?? null,
            staleSince: null,
            statusOk,
          }
          await $.state.set(FACTS, lastGood)
        } else if (lastGood) {
          // a failed tick keeps the last good facts, marked stale, never an empty band; the runner counts read on this
          // tick still show (spec 0065 AC-1), only a field that failed keeps its last good count. lastGood takes the
          // mark too, or each failed tick moved `stale since` to its own time.
          const old = lastGood.wf
          const fresh = wf && old ? { running: wf.running ?? old.running, parked: wf.parked ?? old.parked, questions: wf.questions ?? old.questions } : wf ?? old
          lastGood = { ...lastGood, wf: fresh, statusOk, staleSince: lastGood.staleSince ?? clock(await $.clock.now()) }
          await $.state.set(FACTS, lastGood)
        }
      } finally {
        busy = false
      }
    }

    // AC-2: never two `wf plan` calls at once (a tick is skipped while one runs); a failed or timed out call keeps the
    // last good plan, marked with the error, never an empty one
    let planBusy = false
    loadPanes = async (force = false) => {
      if (planBusy || !(force || isOpen)) return
      planBusy = true
      try {
        const r = await $.process.run(['wf', 'plan', '--json']).catch(() => null)
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

    void refresh()
    $.clock.every(time.bandTick, () => void refresh())
    $.clock.every(time.planTick, () => void loadPanes())
    // the spinner turns only while a handoff step runs, and stays on its first frame under reduced motion, as the host's does
    $.clock.every(time.spin, async () => {
      const { value: h } = await $.state.get(HANDOFF)
      if (!(h?.panel && !h.panel.sticky && h.panel.steps.some(s => s.state === 'running'))) return
      if ((await $.settings.read().catch(() => null) as any)?.prefersReducedMotion) return
      await $.state.set(HANDOFF, { ...h, frame: h.frame + 1 })
    })

    await $.command.register({ name: 'wf-dash', description: 'wf-dash: the plan, the builds, the agents and the alerts in one dashboard' })
    return started
  })

  on('command.run', { command: 'wf-dash' }, async $ => openDashboard($))

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

  // The real effort rides on every main-loop model request; the band shows it from the first reply on.
  on('turn.step', async function* ($, e, next) {
    if (!e.agentId && e.effort !== undefined) {
      const level = String(e.effort)
      const { value } = await $.state.get(EFFORT)
      if (value !== level) await $.state.set(EFFORT, level)
    }
    return yield* next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.surface !== 'terminal') return next(e)
    const { Box, Text, Button } = $.ui.resolve(e)
    const { value: facts } = await $.state.get(FACTS)
    const { value: level } = await $.state.get(EFFORT)
    const { value: handoff } = await $.state.get(HANDOFF)
    const line = handoff ? handoffLine(handoff, Date.now()) : null
    // the handed over level first, then the latest main loop request's; unknown stays out
    const value = facts && !facts.effort && level ? { ...facts, effort: level } : facts
    const band = value
      ? <Band Box={Box} Text={Text} Button={Button} facts={value} columns={e.props.bodyColumns ?? (e.viewport?.columns ?? width.viewport) - space.hostReserve} onOpen={() => void openDashboard($)} />
      : (
        <Box paddingX={space.padX}>
          <Text color={color.dim}>wf-dash: reading status</Text>
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
    const { value: alerts = [] } = await $.state.get(ALERTS)
    const { value: facts } = await $.state.get(FACTS)
    const listed = view.section === 'agents' ? await $.agent.list().catch(() => null) : []
    // a shell row never shares an id with an agent, so its stop can never reach one
    const agents = listed && view.section === 'agents'
      ? [...listed, ...(await shells($)).filter(s => !listed.some((a: any) => a.id === s.id))] : listed
    const cwd = await $.session.cwd().catch(() => null)
    const go = async (v: Partial<typeof view>) => {
      const { value: now = DEFAULT_VIEW } = await $.state.get(VIEW)
      await $.state.set(VIEW, { ...now, ...v })
    }
    const act = {
      go: (v: Partial<typeof view>) => void go(v),
      retry: () => void loadPanes(true),
      run: (a: WfDashAsk) => void perform($, a).then(notice => go({ notice })),
    }
    return <Dashboard el={el} view={view} act={act} plan={plan} cwd={cwd} agents={agents as any[] | null} alerts={alerts} focused={e.props.isFocused !== false} rows={e.props.placement === 'dock' ? e.props.scroll?.bodyRows : undefined} facts={facts?.wf ?? null} statusOk={facts ? facts.statusOk : null} columns={e.props.bodyColumns ?? (e.viewport?.columns ?? width.viewport) - pane.frame} />
  })
}
