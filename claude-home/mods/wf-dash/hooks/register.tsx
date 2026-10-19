import type { Register } from 'claude-code'
import { alertTick, counts, parseStatus } from '../alerts.ts'
import { Band, type Facts } from '../band.tsx'
import { DEFAULT_VIEW, Dashboard } from '../panes.tsx'
import { pane, space, time } from '../tokens.ts'

// wf-dash: the band and alerts (spec 0059) read `wf status --json`; the dashboard (spec 0060, row 73) still reads the
// preview scripts plan.py and runner.py. The drawing in band.tsx and panes.tsx is the locked look.

const FACTS = { plugin: 'wf-dash', key: 'facts' } as const
const EFFORT = { plugin: 'wf-dash', key: 'effort' } as const
const ALERTS = { plugin: 'wf-dash', key: 'alerts' } as const
const PLAN = { plugin: 'wf-dash', key: 'plan' } as const
const RUNNER = { plugin: 'wf-dash', key: 'runner' } as const
const VIEW = { plugin: 'wf-dash', key: 'view' } as const
const PANE = 'wf-dash'
// what `wf auto bar` takes as a session id and an effort level (runner/auto.py); anything else names no file
const SESSION_ID = /^[A-Za-z0-9-]{1,100}$/
const LEVEL = /^[a-z]{1,20}$/

// the mod's own state folder, as runner/auto.py dash_dir() names it; never under the runner's (AC-5)
async function dashDir($: any) {
  return `${(await $.env.get('XDG_STATE_HOME')) || `${await $.env.get('HOME')}/.local/state`}/wf-dash`
}

// shortcut: module values, so a hot reload forgets the dashboard is open until it is opened again; fine for a preview
let isOpen = false
let loadPanes = async (_force = false) => {}

function clock(ms: number) {
  const d = new Date(ms)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
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
    const dir = await dashDir($)

    const refresh = async () => {
      if (busy) return
      busy = true
      try {
        // AC-4: the marker tells this session's `wf auto bar` to go short; its mtime is all it says
        if (sid) await $.fs.write(`${dir}/${sid}`, '').catch(() => {})
        const cwd = await $.session.cwd()
        const [r, st, usage, model, handed] = await Promise.all([
          $.process.run(['python3', `${$.plugin.root}/facts.py`, cwd]).catch(() => null),
          $.process.run(['wf', 'status', '--json']).catch(() => null),
          $.session.usage().catch(() => null),
          $.session.model().catch(() => null),
          sid ? $.fs.read(`${dir}/${sid}.effort`).catch(() => null) : null,
        ])
        const status = st && st.exitCode === 0 ? parseStatus(st.stdout) : null
        await alertTick($, status, sid && `${dir}/${sid}.toasts`, { keep: pane.history, timeoutMs: time.toast })
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
            wf: counts(status),
            auto: raw.auto ?? null,
            staleSince: null,
          }
          await $.state.set(FACTS, lastGood)
        } else if (lastGood) {
          // a failed tick keeps the last good facts, marked stale, never an empty band
          await $.state.set(FACTS, { ...lastGood, staleSince: lastGood.staleSince ?? clock(await $.clock.now()) })
        }
      } finally {
        busy = false
      }
    }

    // Dashboard data: one script call at a time; a failed call keeps the last good data, marked with the error.
    const fetch = async (script: string) => {
      const r = await $.process.run(['python3', `${$.plugin.root}/${script}`]).catch(() => null)
      const data = r && r.exitCode === 0 ? JSON.parse(r.stdout || 'null') : null
      return { data, error: data ? null : r ? `exit ${r.exitCode}` : 'did not run', at: await $.clock.now() }
    }
    let planBusy = false
    const loadPlan = async () => {
      if (planBusy) return
      planBusy = true
      try {
        const got = await fetch('plan.py')
        const { value: old } = await $.state.get(PLAN)
        await $.state.set(PLAN, got.data ? got : { data: old?.data ?? null, at: old?.at ?? null, error: got.error })
      } finally {
        planBusy = false
      }
    }
    let runnerBusy = false
    const loadRunner = async () => {
      if (runnerBusy) return
      runnerBusy = true
      try {
        const got = await fetch('runner.py')
        const { value: old } = await $.state.get(RUNNER)
        await $.state.set(RUNNER, got.data ? got : { data: old?.data ?? null, at: old?.at ?? null, error: got.error })
      } finally {
        runnerBusy = false
      }
    }
    loadPanes = async (force = false) => {
      if (force || isOpen) await Promise.all([loadPlan(), loadRunner()])
    }

    void refresh()
    $.clock.every(time.bandTick, () => void refresh())
    $.clock.every(time.planTick, () => void loadPanes())

    await $.command.register({ name: 'wf-dash', description: 'wf-dash: the plan, the builds, the agents and the alerts in one dashboard' })
    return started
  })

  on('command.run', { command: 'wf-dash' }, async $ => openDashboard($))

  on('ui.close', async ($, e, next) => {
    if (e.id === PANE) isOpen = false
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
    if (!facts) {
      return (
        <Box paddingX={space.padX}>
          <Text color="inactive">wf-dash: reading status</Text>
        </Box>
      )
    }
    // the handed over level first, then the latest main loop request's; unknown stays out
    const value = !facts.effort && level ? { ...facts, effort: level } : facts
    return <Band Box={Box} Text={Text} Button={Button} facts={value} columns={e.props.bodyColumns ?? (e.viewport?.columns ?? 80) - space.hostReserve} onOpen={() => void openDashboard($)} />
  })

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if ((e as any).requestId !== PANE || e.surface !== 'terminal') return next(e)
    const el = $.ui.resolve(e)
    const { value: view = DEFAULT_VIEW } = await $.state.get(VIEW)
    const { value: plan } = await $.state.get(PLAN)
    const { value: runner } = await $.state.get(RUNNER)
    const { value: alerts = [] } = await $.state.get(ALERTS)
    const { value: facts } = await $.state.get(FACTS)
    const agents = view.section === 'agents' ? await $.agent.list().catch(() => null) : []
    const act = {
      go: (v: Partial<typeof view>) => void $.state.set(VIEW, { ...view, ...v }),
      retry: () => void loadPanes(true),
    }
    return <Dashboard el={el} view={view} act={act} plan={plan} runner={runner} agents={agents as any[] | null} alerts={alerts} focused={e.props.isFocused !== false} rows={e.props.placement === 'dock' ? e.props.scroll?.bodyRows : undefined} facts={facts?.wf ?? null} columns={e.props.bodyColumns ?? (e.viewport?.columns ?? 80) - pane.frame} />
  })
}
