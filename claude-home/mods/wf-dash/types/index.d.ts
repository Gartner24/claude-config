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
  // "unknown" past the build where no PR record can say whether it is in review
  review: string | null
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
  id: string | null
  repo: string
  feature: string
  step: string | null
  cost: number | null
  calls: number | null
  startedAt: string | null
  steps: { command: string; started: string | null; minutes: number; cost: number | null; ok: boolean }[]
}

export type WfDashQuestion = { id: string; repo: string; feature: string; question: string; options: string[]; parked: boolean }

// `wf plan --json` (spec 0060 AC-1, AC-4); runs and questions are null when the runner could not read them
export type WfDashPlan = { repos: WfDashRepo[]; warnings: string[]; runs: WfDashRun[] | null; questions: WfDashQuestion[] | null }

// an action waiting for its confirm (AC-5)
export type WfDashAsk =
  | { kind: 'start'; text: string }
  | { kind: 'stop'; id: string; label: string }
  | { kind: 'answer'; id: string; options: string[]; n?: number }

export type WfDashLoaded<T> = { data: T | null; at: number | null; error: string | null }

declare module 'claude-code' {
  interface PluginState {
    'wf-dash': {
      facts: WfDashFacts
      effort: string | null
      alerts: WfDashAlert[]
      seen: WfDashSeen
      plan: WfDashLoaded<WfDashPlan>
      view: {
        section: string; tab: string; page: number; sel: number; bpos: number; apos?: number; gsel?: number
        ask?: WfDashAsk | null; notice?: { text: string; ok: boolean } | null
      }
    }
  }
}
