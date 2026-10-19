// Spec 0059 AC-3: alerts from the change in `wf status --json` ids between two ticks. Pure, so the tests drive it.
import type { WfDashAlert, WfDashSeen, WfRunRecord, WfStatus, WfStatusEntry } from './types/index.d.ts'

export type NewAlert = Omit<WfDashAlert, 'at'>

// how many toasted ids are kept to toast each only once; far more than the runner ever has open at a time
const REMEMBER = 200

export const NEVER_SEEN: WfDashSeen = { prev: { running: null, parked: null, questions: null }, toasted: [] }

export const toastText = (a: Pick<WfDashAlert, 'kind' | 'feature' | 'detail'>) => `${a.kind}: ${a.feature} - ${a.detail}`

// spec 0065 AC-2: a run that left `running` is `finished` only when its own record says so. A record not written yet is
// read again on each of the next RETRIES ticks before the alert settles; this used to toast `finished` for every end.
const RETRIES = 3
const FINISHED = ['queue_done', 'feature_done']

const ids = (l: WfStatusEntry[]) => new Set(l.map(e => e.id).filter(Boolean))

// the ids whose run record this tick reads: runs that just left `running`, and those still waiting for theirs
export function departed(seen: WfDashSeen, now: WfStatus | null): string[] {
  const live = now?.running ? ids(now.running) : null
  const left = live ? (seen.prev.running ?? []).map(e => e.id).filter((id): id is string => !!id && !live.has(id) && !seen.toasted.includes(id)) : []
  return [...(seen.pending ?? []).map(p => p.id), ...left]
}

// `now` null: the tick's `wf status` failed, so every field is skipped, never read as empty.
// `records`: the run record of each `departed` id, null when missing or unreadable.
export function diff(seen: WfDashSeen, now: WfStatus | null, records: Record<string, WfRunRecord | null> = {}): { seen: WfDashSeen; alerts: NewAlert[] } {
  const toasted = new Set(seen.toasted)
  const alerts: NewAlert[] = []
  const prev = { ...seen.prev }
  const pending: NonNullable<WfDashSeen['pending']> = []
  const add = (id: string, kind: NewAlert['kind'], e: WfStatusEntry, detail: string) => {
    if (toasted.has(id)) return
    toasted.add(id)
    alerts.push({ id: `${kind}:${id}`, kind, feature: e.feature, detail })
  }
  const title = (id: string | null) => now?.questions?.find(q => q.id === id)?.title
  const ended = (id: string, e: WfStatusEntry, tries: number) => {
    const r = records[id]
    if (r?.ended && FINISHED.includes(r.stop_reason ?? '')) add(id, 'finished', e, `in ${e.repo}`)
    else if (r?.ended) add(id, 'stopped', e, `in ${e.repo}, ${String(r.stop_reason).replaceAll('_', ' ')}`)
    else if (tries >= RETRIES) add(id, 'stopped', e, `in ${e.repo}, ended with no record (lost its lock or crashed)`)
    else pending.push({ id, repo: e.repo, feature: e.feature, tries })
  }

  for (const p of seen.pending ?? []) ended(p.id, p, p.tries + 1)
  // a run without an id (its folder not found) cannot be followed, so it never alerts
  if (now?.running) {
    const live = ids(now.running)
    for (const e of prev.running ?? []) if (e.id && !live.has(e.id) && !toasted.has(e.id)) ended(e.id, e, 0)
    prev.running = now.running
  }
  // parked before questions: a parked decision is a question too, and one id toasts once, as stuck
  if (now?.parked) {
    const old = ids(prev.parked ?? [])
    if (prev.parked) for (const e of now.parked) if (e.id && !old.has(e.id)) add(e.id, 'stuck', e, title(e.id) ?? `in ${e.repo}`)
    prev.parked = now.parked
  }
  if (now?.questions) {
    const old = ids(prev.questions ?? [])
    if (prev.questions) for (const e of now.questions) if (e.id && !old.has(e.id)) add(e.id, 'question', e, e.title ?? `in ${e.repo}`)
    prev.questions = now.questions
  }
  return { seen: { prev, toasted: [...toasted].slice(-REMEMBER), pending }, alerts }
}

// `wf status --json` stdout, or null when it is not the expected shape
export function parseStatus(stdout: string): WfStatus | null {
  try {
    const s = JSON.parse(stdout)
    const ok = (v: unknown) => v === null || Array.isArray(v)
    return s && ok(s.running) && ok(s.parked) && ok(s.questions) ? s : null
  } catch {
    return null
  }
}

const SEEN = { plugin: 'wf-dash', key: 'seen' } as const
const ALERTS = { plugin: 'wf-dash', key: 'alerts' } as const
const isSeen = (v: any): v is WfDashSeen => !!v && !!v.prev && Array.isArray(v.toasted)
const RUN_ID = /^[\w-][\w.-]*$/

// One tick's alerts: toast each new one, keep the last `keep` for the dashboard's Alerts view. What was seen lives in
// $.state and, since probe P5 left its persistence unproven, in `file`, so a hot reload toasts nothing twice.
// `runs`: the runner's `<state>/wf/runs` folder, each run's record at `<runs>/<id>/run.json`.
export async function alertTick($: any, status: WfStatus | null, file: string | null, opts: { keep: number; timeoutMs: number; runs?: string | null }) {
  let { value: seen } = await $.state.get(SEEN)
  if (!isSeen(seen)) {
    const saved = file ? await $.fs.read(file).then((t: string) => JSON.parse(t)).catch(() => null) : null
    seen = isSeen(saved) ? saved : NEVER_SEEN
  }
  const records: Record<string, WfRunRecord | null> = {}
  // the id is a folder name from `wf status`; one that is not stays unread, so it can never reach outside `runs`
  for (const id of departed(seen, status)) {
    records[id] = opts.runs && RUN_ID.test(id)
      ? await $.fs.read(`${opts.runs}/${id}/run.json`).then((t: string) => JSON.parse(t)).catch(() => null)
      : null
  }
  const got = diff(seen, status, records)
  if (JSON.stringify(got.seen) === JSON.stringify(seen)) return
  await $.state.set(SEEN, got.seen)
  if (file) await $.fs.write(file, JSON.stringify(got.seen)).catch(() => {})
  if (!got.alerts.length) return
  const at = await $.clock.now()
  const { value = [] } = await $.state.get(ALERTS)
  await $.state.set(ALERTS, [...value, ...got.alerts.map(a => ({ ...a, at }))].slice(-opts.keep))
  for (const a of got.alerts) $.ui.toast(toastText(a), { timeoutMs: opts.timeoutMs })
}

// the band's counts: a field the runner could not read stays null, shown as `?`
export const counts = (s: WfStatus | null) =>
  s && { running: s.running?.length ?? null, parked: s.parked?.length ?? null, questions: s.questions?.length ?? null }
