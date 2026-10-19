export type WfDashFacts = {
  model: string | null
  effort: string | null
  folder: string | null
  // counts are null when the repo defines its own git filter: facts.py then skips `git status`
  git: { branch: string; changes: number | null; staged: number | null; modified: number | null; untracked: number | null } | null
  context: number | null
  contextTokens: number | null
  contextWindow: number | null
  fiveHour: number | null
  fiveHourReset: string | null
  week: number | null
  weekReset: string | null
  via: string | null
  wf: { running: number | null; parked: number | null; questions: number | null } | null
  auto: { here: boolean; chats: number } | null
  staleSince: string | null
}

export type WfDashAlert = { id: string; at: number; kind: 'finished' | 'stuck' | 'question'; feature: string; detail: string }

// `wf status --json` (spec 0059 AC-1); a field is null when the runner could not read it
export type WfStatusEntry = { id: string | null; repo: string; feature: string; title?: string }
export type WfStatus = { running: WfStatusEntry[] | null; parked: WfStatusEntry[] | null; questions: WfStatusEntry[] | null }
// the last good entries per field (null before the first good read) and every id already toasted
export type WfDashSeen = { prev: WfStatus; toasted: string[] }

export type WfDashFeature = {
  heading: string
  state: string
  next: string | null
  command: string | null
  spec: string | null
  specStatus: string | null
  deferred: boolean
  pr: number | null
  prState: string | null
}

export type WfDashRepo = {
  name: string
  path: string
  hub?: boolean
  error?: string
  warnings?: string[]
  rows?: string[]
  features?: WfDashFeature[]
}

export type WfDashRun = {
  repo: string
  feature: string
  step: string | null
  cost: number | null
  calls: number | null
  log: string[]
  startedAt: string | null
  steps: { command: string; started: string | null; minutes: number; cost: number | null; ok: boolean }[]
}

export type WfDashQuestion = { id: string; repo: string; feature: string; question: string; options: string[]; parked: boolean }

// spec 0064 AC-1: ~/.claude/state/auto-handoff/panel.json as the wf-handoff mod writes it
export type WfDashPanel = {
  session: string
  previous: string | null
  phase: string
  steps: { label: string; state: 'pending' | 'running' | 'done' | 'failed' }[]
  result: string | null
  sticky: boolean
  link: string | null
  at: number
}
// the last panel that was this chat's, this chat's id and the one it replaced, when the owner last dismissed
export type WfDashHandoff = { panel: WfDashPanel | null; me: string; prev: string | null; dismissed: number; frame: number }

export type WfDashLoaded<T> = { data: T | null; at: number | null; error: string | null }

declare module 'claude-code' {
  interface PluginState {
    'wf-dash': {
      facts: WfDashFacts
      effort: string | null
      alerts: WfDashAlert[]
      seen: WfDashSeen
      plan: WfDashLoaded<{ repos: WfDashRepo[] }>
      runner: WfDashLoaded<{ runs: WfDashRun[] | null; questions: WfDashQuestion[] | null }>
      view: { section: string; tab: string; page: number; sel: number; bpos: number }
      handoff: WfDashHandoff
    }
  }
}
