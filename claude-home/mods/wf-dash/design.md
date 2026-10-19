# wf-dash design (locked 2026-10-17)

The look rows 72 (band and alerts, spec 0059) and 73 (panes and actions, spec 0060) build. The drawing code in this
folder (`band.tsx`, `panes.tsx`, `tokens.ts`) is the reference: the build keeps it and swaps the preview fact
scripts (`facts.py`, `plan.py`, `runner.py`) for `wf status --json` and `wf plan --json`.

## Owner's words (2026-10-17)
- Look accepted as is at critique 29/40 ("accept as is"); keys that fall through to the prompt are plan row 75.
- Band: "it look really really good, better than jjstack". Missing effort and other things: added below.
- "dont import things from jjstack, we are creating something unattatched from it ... a new improved better new
  status bar with new cool features".
- Alerts: colored by type was asked; then "show at the top right as the others ... they can stay for longer, and how
  can I open them to see them complete". Built: top right toasts, 15 s, plus the dashboard's Alerts view (`l`) in color.
- Panes: "Build panes in this style".

## Direction
- Primary reference: k9s (label and value header, one framed view, row color is state, key hints). Borrowed: Soft
  Serve's name chip; btop's lit hotkey and small meters; Blast Radius and hamzafer's stacked rows for alert wording;
  Epic Status Line and burn-meter for reset times next to usage; pottekkat for tokens next to context.
- Rejected: powerline chevrons, hex palettes, emoji and Unicode status symbols.
- Colors are Claude Code theme keys only (`tokens.ts`), so the owner's terminal theme decides the hues. One accent,
  `claude`, for identity (the chip, the `wf` label) and the plan cursor; hotkey letters are the host's own button
  color. `building` and running agents are full-strength bold text, not the accent, because the accent's hue sits
  beside `warning` and `error` in common themes. Color is never the only signal: every state prints its word, every
  meter its number. ASCII only.

## Band (one line above the prompt)
`[ wf-dash ]  Opus 5.5 medium  <folder>  <branch> +s ~m ?u  ctx 16% 160k/1M  [5h meter] 20% in 2h10m  [week meter] 45% in 3d22h  auto: 2 chats on     wf 1 building  0 stuck  1 question`
- Effort in color per level (low ok, medium warn, high design, xhigh review, max accent). Shown from the first
  second: the status line receives `.effort.level` from Claude Code on every redraw, and the build makes our own bar
  (spec 0058, not jjstack) hand it to the band. Until then the band reads it only from each model
  request (`turn.step`), never from env vars or the settings files: env vars are the parent shell's, settings name a default, and both
  showed `high` in a `medium` session. Unknown effort is left out, never guessed.
- Git: `<branch>` then `clean` or `+staged ~modified ?untracked`. A repo whose own config defines a git filter shows
  the branch only (read from its HEAD file): `git status` would run that filter's command.
- Meters (5 cells): label centred, used share on a background (ok under 70, warn 70-89, bad 90+), then the number; the number
  turns warn or bad too. Reset times and context tokens are extras that leave first on a narrow line.
- Narrow line: segments leave in this order: folder, auto, git, week, 5h, via, ctx, model. The chip and the runner
  counts stay. The host keeps 4 cells at the right end for its `[-]`. When only the chip would be left (the ~31
  cells beside the docked dashboard), the runner counts go compact: zeros leave, short words, most urgent first, no
  `wf ` label (the chip beside it names wf): `2 ask 2 stuck 1 run`, or `idle`. A count that does not fit leaves
  whole, least urgent first, so the question count is the last to go. The chip is pinned.
- Unknown values print `?`, never 0; context and effort are left out until known. A failed tick keeps the last
  good band and adds `stale since HH:MM`; the runner counts that tick did read still show, only a count that failed
  keeps its last good number. In the full band each count's number is right aligned in 3 cells, so the line does not
  shift. The compact band adds a short ` stale` instead: it is the last part to go, its cells come out of the counts'
  budget, and when even the first count and the mark do not fit the band reads `stale` alone. The chip is a button (`w`), and its hotkey label takes 3 cells the fit counts.

## Alerts
- Toast at the top right (Claude Code draws it; a mod cannot color it): `<kind>: <feature> - <detail>`, 15 s.
  Kinds: `finished` (the run record says the queue or the feature is done), `stopped` (any other end, with its
  reason, or `ended with no record` when the record never came), `stuck`, `question`. The toast wraps, so the full text shows.
- The dashboard's Alerts view (`l`), an inbox like Linear's: every alert of the session, newest first; the title
  line is the kind word bold in its color (finished ok, stopped warn, stuck bad, question warn), the feature in bold, the time at
  the right; the detail in full, dim, under the feature. Empty, it says what will land there; `could not read wf` when the
  last tick could not read the runner, and `reading wf` before the first tick. When the alerts
  outgrow the pane, `j` / `k` scroll them and a dim line says `N newer above, +M older`.

## Dashboard (`/wf-dash`, or click the band's chip, or `w` once the band has the keys)
One pane with four views, switched by a letter: `p: Plan  b: Builds  a: Agents  l: Alerts`. The owner asked for
one dashboard to move inside, not a command per view. It replaces the separate `/plan`, `/agents` and `/runner`
of spec 0060 (which also clash with Claude Code's own `/plan` and `/agents`); row 73 records the change.
- Opens with focus, Escape closes it, asks for 21 rows above the prompt (the host may give fewer).
- Top line: the chip, then the view keys; the selected view and filter are bracketed (`[Plan]`) and at full
  strength, the rest dim, so the cue does not rest on brightness alone. No counts line: the band right below
  already shows them. No blank lines: the pane is short (about 14 rows).
- Footer: Plan `j: down  k: up  d: page down N/M  u: page up  n: next group  g: top` (narrow: `d: pg N/M  u: back
  n: group`), Builds and Alerts `j: down  k: up` (lit only with more below or above), then on every view `r: refresh  esc closes`. Every key shown is
  always bound and dims when it would do nothing (one item, one page, one group), because a key with no button falls
  through to the prompt and takes the keyboard. When that happens anyway (any other letter), a warn line under the
  top line says `Keys go to the prompt now: click the dashboard to return`, the one way back that worked in a real
  terminal. A mod cannot catch a key it has no button for, and a hotkey button cannot be hidden (spec 0062, probes
  P10 and P11).
- Widths come from the host's `bodyColumns` (the pane's body inside its frame, docked or inline; the band's column
  less the host's `[-]`), never the terminal width: docked beside a 118-column session the panel is about 84 inside
  and gets the wide layout, while the band sizes to the 31 cells left of it. At 80 body columns or wider each view
  opens with one dim line saying what it shows; narrower views drop it to keep the row, and the view keys sit one
  cell apart so the top line stays one line.
- Plan: eight filters on digit keys, each with its count: `1: Needs you  2: Building  3: To publish  4: Ready
  5: Needs design  6: In progress  7: Built  8: All open`. When one row would not fit (narrow, or a docked panel near 88 cells) they sit in two deliberate rows of
  four (act now, then the rest; the owner kept this over a one-line filter) with short labels (`Publish`, `Design`,
  `Progress`, `All`), one cell apart; the act now row keeps its counts and switches to tiny labels (`You`, `Build`)
  only when the counts would wrap it; the second row shows a count only on the selected filter. "To publish" is built and not yet merged: the runner's
  PR record says `local` (not pushed: `to publish`) or `draft`, `ready`, `approved` (`in review`, with `PR #N`).
  Grouped by state across repos, like Linear's issues view: the group heading is the state word, bold in its color,
  with its count (`waits on you 10`; done features read `built`, the filter's word), so rows never repeat it; a single-state filter drops the one heading (its tab already says state and count) and gives the row to a feature. Rows: name, repo (14, dim, only when the page on
  screen mixes repos), next step (24, dim) and spec with its status (15, dim), both only at 80 body columns or wider;
  built rows drop the next step. A `>` cursor moves over features with `j` / `k`. The list is always 5 rows (plus every row a docked pane has past 14), padded blank, so switching filters never
  moves the layout; a page never ends on a lone group heading, and a page that starts inside a group repeats its
  heading as `<state>  N cont.`. The page follows the cursor. Broken scopes, hub rows (All open) and scope warnings
  (`<repo>: <warning>`) follow the state groups. The Needs you filter's intro line (wide only) says it lists steps
  only you can do and that the runner's own questions are in Builds. Under the list a 3-row detail
  block shows the selected feature without its state word (the heading says it): its full name (and repo) first when the row cut them, then `next: ...` (wrapped to two
  lines when long), what the state means when there is room (`a step only you can do`), then `N/M` first (so a
  narrow pane never cuts it), `spec NNNN: <status in plain words>`, PR, and the repo when the list spans repos but
  the rows on screen do not show it. Hub
  scopes show their open rows under All open. An empty filter says what lands in it (`Nothing to publish. A feature lands here once it is built on its branch, until its PR is merged.`). `d` and `u` stop at the last and first page. A broken scope shows its error in bad; a failed refresh keeps the
  last plan and says `stale since HH:MM: the last refresh failed (...); r tries again`.
- Builds (the runner, named for what it does): one plain line on what it shows (wide only), then a `waits on you N`
  block (warn, bold; 7shifts' pending block) with each question and each stuck feature, so the thing that needs
  you never falls below the fold, then a `building N` block with each run (lowercase state words, as Plan's group headings). A block heading never sits alone at the
  foot. A run: `<feature>  <repo>` in fixed cells (repo 14, the feature takes the rest; each truncates, never
  wraps, so an item keeps its row count), `now <verify|build|test|debug|sync|design>  N steps so far, $X, started HH:MM`,
  and, with 2 runs or fewer, its last 3 steps as `HH:MM  kind  ok|failed  Nm  $X`. The step running now comes from the run's log (the
  run record only gets a step once it ends). A question: `question` or `stuck`, feature, repo, the ask in up to two lines without the `in <feature>` the row already names, and
  `reply on your phone to question <id>: 1 option  2 option` (narrow: `on phone, <id>:`) wrapped to a second line rather than cut, dim (the numbers are the phone's buttons, not keys here). When the items
  outgrow the pane, `j` / `k` scroll them and a dim line says `N above, +M more`; a run scrolled out of view still gets one line, `building <feature cut to 24>  now <step>  +N`, and "more" then counts only the questions below.
- Agents: status word (running bold text, waiting warn, failed bad, others dim), description, type. An empty list
  says the mod API lists none and the host's own count may still show some (empty is not proof of none). Background
  shells follow the agents as `started  <description>  shell`, read from this chat's Bash results less the stopped or
  finished ones; one dim line says a started shell may have ended unseen.
- Actions (row 73, spec 0060 AC-5) go in the footer row as hotkey buttons, each behind a confirm that shows the
  exact text.

## Preview
`claude --plugin-dir claude-home/mods/wf-dash`, then `/wf-dash` for the dashboard; its Alerts view (`l`) lists the session's alerts.
