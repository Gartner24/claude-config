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
  staleSince: string | null
  // the auto handoff segment on the right: undefined before the first read; null when no chain file names this chat
  // ("handoff ?", never a guessed on or off)
  handoff?: WfDashAuto | null
}

export type WfDashFeature = {
  heading: string
  state: string
  next: string | null
  command: string | null
  spec: string | null
  specStatus: string | null
  deferred: boolean
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

// plan.py's answer (spec 0060 AC-1, the runner's parts gone)
export type WfDashPlan = { repos: WfDashRepo[]; warnings: string[] }

// an action waiting for its confirm (AC-5)
export type WfDashAsk =
  | { kind: 'start'; text: string }
  | { kind: 'stop'; id: string; label: string }

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
// this chat's auto handoff from its chain file in ~/.claude/state/auto-handoff/ (wf-handoff writes it): off, and the
// line in tokens; null until the file names this chat
export type WfDashAuto = { off: boolean; line: number | null }
// the last panel that was this chat's, this chat's id and the one it replaced, when the owner last dismissed
export type WfDashHandoff = { panel: WfDashPanel | null; me: string; prev: string | null; dismissed: number; frame: number; auto?: WfDashAuto | null }

export type WfDashLoaded<T> = { data: T | null; at: number | null; error: string | null }

declare module 'claude-code' {
  interface PluginState {
    'wf-dash': {
      facts: WfDashFacts
      effort: string | null
      plan: WfDashLoaded<WfDashPlan>
      view: {
        section: string; tab: string; page: number; sel: number; gsel?: number
        ask?: WfDashAsk | null; notice?: { text: string; ok: boolean } | null
      }
      handoff: WfDashHandoff
    }
  }
}
