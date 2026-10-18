import type { Register } from 'claude-code'
import type { WfDashAlert } from '../types/index.d.ts'
import { Band, type Facts } from '../band.tsx'
import { DEFAULT_VIEW, Dashboard } from '../panes.tsx'
import { pane, space, time } from '../tokens.ts'

// Design preview of wf-dash (specs 0059, 0060). Rows 72 and 73 replace facts.py, plan.py and runner.py with
// `wf status --json` and `wf plan --json`, turn the sample alerts into real ones from the id diff, and add the
// confirmed actions; the drawing in band.tsx and panes.tsx is the locked look.

const FACTS = { plugin: 'wf-dash', key: 'facts' } as const
const EFFORT = { plugin: 'wf-dash', key: 'effort' } as const
const ALERTS = { plugin: 'wf-dash', key: 'alerts' } as const
const PLAN = { plugin: 'wf-dash', key: 'plan' } as const
const RUNNER = { plugin: 'wf-dash', key: 'runner' } as const
const VIEW = { plugin: 'wf-dash', key: 'view' } as const
const PANE = 'wf-dash'

const SAMPLE_ALERTS: Omit<WfDashAlert, 'id' | 'at'>[] = [
  { kind: 'finished', feature: '58. Own status bar', detail: 'PR ready to review' },
  { kind: 'stuck', feature: '65. Scan skills with skillspector', detail: 'the baseline needs a write it cannot make' },
  { kind: 'question', feature: '61. Cheap model gatekeeper', detail: 'answer on your phone' },
]

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
    let busy = false

    const refresh = async () => {
      if (busy) return
      busy = true
      try {
        const cwd = await $.session.cwd()
        const [r, usage, model] = await Promise.all([
          $.process.run(['python3', `${$.plugin.root}/facts.py`, cwd]).catch(() => null),
          $.session.usage().catch(() => null),
          $.session.model().catch(() => null),
        ])
        const raw = r && r.exitCode === 0 ? JSON.parse(r.stdout || 'null') : null
        const limit = (kind: string) => usage?.rateLimits?.find((x: any) => x.kind === kind) ?? null
        if (raw) {
          lastGood = {
            model,
            // only turn.step knows this session's effort: env vars are the parent shell's and showed `high` in a `medium`
            // session. Unknown is left out, never guessed.
            effort: null,
            folder: raw.folder ?? null,
            git: raw.git ?? null,
            context: usage?.context?.percent ?? null,
            contextTokens: usage?.context?.tokens ?? null,
            contextWindow: usage?.context?.window ?? null,
            fiveHour: limit('five_hour')?.percentUsed ?? null,
            fiveHourReset: limit('five_hour')?.resetsAt ?? null,
            week: limit('seven_day')?.percentUsed ?? null,
            weekReset: limit('seven_day')?.resetsAt ?? null,
            via: null,
            wf: raw.wf ?? null,
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
    await $.command.register({ name: 'wf-dash-alerts', description: 'wf-dash preview: send the three sample alerts' })
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
    const value = level ? { ...facts, effort: level } : facts
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

  on('command.run', { command: 'wf-dash-alerts' }, async $ => {
    const send = async (a: Omit<WfDashAlert, 'id' | 'at'>, i: number) => {
      const at = await $.clock.now()
      const { value = [] } = await $.state.get(ALERTS)
      await $.state.set(ALERTS, [...value, { ...a, id: `sample-${at}-${i}`, at }].slice(-pane.history))
      // the toast keeps the type word first; the full text and its color live in the dashboard's Alerts view
      $.ui.toast(`${a.kind}: ${a.feature} - ${a.detail}`, { timeoutMs: time.toast })
    }
    SAMPLE_ALERTS.forEach((a, i) => $.clock.after(i * time.sampleGap, () => void send(a, i)))
    return { text: `Three sample alerts follow at the top right, ${time.sampleGap / 1000} s apart; each stays ${time.toast / 1000} s. /wf-dash, then l, shows them in full.` }
  })
}
