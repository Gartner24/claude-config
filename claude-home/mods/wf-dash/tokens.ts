// wf-dash design tokens. Every color, glyph, width and timing in the mod comes from here.
// Colors are Claude Code ThemeKeys, never hex, so the mod follows the user's terminal theme.

export const color = {
  text: "text",
  dim: "inactive",
  accent: "claude",
  border: "inactive",
  ok: "success",
  warn: "warning",
  bad: "error",
  review: "suggestion",
  design: "permission",
} as const;

// One word per state: color is never the only signal.
export const state = {
  // full-strength text, not the accent: the accent is identity and cursor, and its hue sits beside warning and error
  "building": { color: color.text, word: "building" },
  "waits on you": { color: color.warn, word: "waits on you" },
  "in review": { color: color.review, word: "in review" },
  "to publish": { color: color.review, word: "to publish" },
  "ready to build": { color: color.ok, word: "ready" },
  "needs a design": { color: color.design, word: "needs design" },
  "in progress": { color: color.text, word: "in progress" },
  // "built", the filter's word, so one state has one name
  "done": { color: color.dim, word: "built" },
  "dropped": { color: color.dim, word: "dropped" },
  "existing": { color: color.dim, word: "existing" },
} as const;

// Effort levels in jjstack's colors, as theme keys: low green, medium yellow, high magenta, xhigh cyan.
export const effort = {
  low: color.ok,
  medium: color.warn,
  high: color.design,
  xhigh: color.review,
  max: color.accent,
  auto: color.dim,
} as const;

// Alerts: a toast at the top right (the host draws it, no color) and, in the dashboard's Alerts view, a colored row.
export const alert = {
  "finished": color.ok,
  "stopped": color.warn,
  "stuck": color.bad,
  "question": color.warn,
} as const;

// Each plan state in plain words, for the detail line under the list.
export const stateHelp: Record<string, string> = {
  "building": "wf is building it now",
  "waits on you": "a step only you can do",
  "to publish": "built on its branch, PR not opened yet",
  "in review": "PR open, waiting for review and merge",
  "ready to build": "designed, ready to build",
  "needs a design": "a decision is owed first (/architect)",
  "in progress": "partly done, more steps to go",
  "done": "built and merged",
  "dropped": "dropped from the plan",
  "existing": "was already there before the plan",
};

// Short filter labels for a narrow pane, where only the selected filter shows its count.
export const shortTab: Record<string, string> = {
  "needs-you": "Needs you", "building": "Building", "publish": "Publish", "ready": "Ready",
  "design": "Design", "progress": "Progress", "built": "Built", "open": "All",
};

// The act-now row's labels when its counts would not fit one line at the pane's width (big counts, a 56-cell pane).
export const tinyTab: Record<string, string> = {
  "needs-you": "You", "building": "Build", "publish": "Publish", "ready": "Ready",
};

// A spec's status in plain words, for the plan's detail line.
export const specStatus: Record<string, string> = {
  "Proposed": "written, not accepted yet",
  "Accepted": "accepted, ready to build",
  "In Progress": "being built",
  "Superseded": "replaced by a newer spec",
  "unknown": "no spec file found",
};

// Agent status words and their colors.
export const agentStatus = {
  pending: color.dim,
  running: color.text,
  waiting: color.warn,
  idle: color.dim,
  completed: color.ok,
  failed: color.bad,
  killed: color.bad,
} as const;

// Panes: rows per page and the column widths, in cells.
export const pane = {
  page: 5,
  // rows the selected feature's detail block always takes
  detail: 3,
  // rows asked for when the pane opens above the prompt: a page plus header, tabs and pager
  rows: 21,
  steps: 3,
  // with more runs than this, each run shows two lines and no step history, so questions stay in view
  fullRuns: 2,
  // rows the Builds list may use in a 14-row pane: the top row, the intro, the "+N more" line and the footer take 4
  buildRows: 10,
  history: 20,
  // cells the host's pane border takes from the viewport width (one each side)
  frame: 2,
  // body rows the layout above is budgeted for (the ~14-row inline pane); a docked pane's rows past this go to the lists
  baseRows: 14,
  // the narrowest text column the detail block wraps into, so a tiny pane still shows words, not single letters
  minWrap: 10,
  // word: the Builds state word ("question", "building"); repo: the Builds repo name, truncated past this
  // cursor: the ">" mark (its cell plus the cell's gap make the 2-cell indent); clock: "HH:MM" right-aligned, no gap
  col: { state: 13, next: 24, spec: 15, time: 6, kind: 10, word: 8, repo: 14, result: 7, cursor: 1, clock: 5 },
  // under this many body columns (the host's bodyColumns, inside the frame) the plan drops its spec and next columns
  // and the views their intro line; the panel docked beside a 118-column session is about 84 inside (critique round 7)
  specMin: 80,
} as const;

export const stateOrder = ["building", "waits on you", "to publish", "in review", "ready to build", "needs a design", "in progress", "done", "dropped", "existing"] as const;

// Usage meters as today's status bar draws them (spec 0058): the label centred in `width`
// cells, the filled share on a background color, the rest dim, then the number.
// Green under 70, yellow 70-89, red 90 and up.
export const meter = {
  width: 5,
  warnAt: 70,
  badAt: 90,
  fill: { ok: color.ok, warn: color.warn, bad: color.bad },
  onFill: "inverseText",
} as const;

// ASCII only, so the band is copy-paste safe and needs no patched font.
export const glyph = {
  sep: "  ",
  unknown: "?",
  dirty: "*",
  // ends a line wrapWords had to cut
  cut: "...",
} as const;

// Spacing in terminal cells.
export const space = {
  gap: 2,
  // the plan's 8 filters in a narrow pane: one cell between keys so the row fits one line
  tight: 1,
  // one blank row above an error or a view's closing note
  line: 1,
  padX: 1,
  padY: 0,
  indent: 2,
  // cells the host keeps at the band's right end for its own `[-]` toggle (its bodyColumns already leaves them out)
  hostReserve: 5,
  // a plain hotkey button draws "w: " before its label
  hotkeyCells: 3,
} as const;

// Fixed column widths so a tick never shifts the line.
export const width = {
  pct: 4,
  count: 3,
  state: 12,
  spec: 8,
  elapsed: 6,
  // the terminal width assumed when the host sends neither bodyColumns nor a viewport
  viewport: 80,
} as const;

export const border = {
  style: "single",
  dim: true,
} as const;

// Timings in ms. Ticks come from the specs (band 5 s, plan pane 10 s).
export const time = {
  bandTick: 5000,
  planTick: 10000,
  barMarkerFresh: 15000,
  toast: 15000,
} as const;
