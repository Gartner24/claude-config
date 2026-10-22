# Reference lock - wf-dash (terminal mod: band, toasts, panes, short bar)

Galleries (Mobbin, Refero, Curated) hold web and app screens, not terminal UIs, so the
references are shipped terminal tools, read from their own README screenshots (looked at
2026-10-17, not cached in the repo).

## Sources
1. k9s pods view - https://github.com/derailed/k9s/raw/master/assets/screen_po.png
2. k9s logs view - https://github.com/derailed/k9s/raw/master/assets/screen_logs.png
3. btop main screen - https://github.com/aristocratos/btop/raw/main/Img/normal.png
4. Soft Serve commit view - https://stuff.charm.sh/soft-serve/soft-serve-demo-commit.png
5. gh-dash overview - https://github.com/dlvhdr/gh-dash/raw/main/docs/src/assets/overview.gif
6. ccstatusline powerline - https://raw.githubusercontent.com/sirmalloc/ccstatusline/main/screenshots/powerline-flex.png
7. ccstatusline aligned - https://raw.githubusercontent.com/sirmalloc/ccstatusline/main/screenshots/autoAlign.png
(Dropped: lazygit README image, a video thumbnail, not UI.)

## Primary: k9s
Signature traits kept sharp:
- Header as `label: value` pairs, labels plain, values in one accent; facts, no decoration.
- One single-line bordered pane per view, its title set into the top border and centred:
  `Pods(all)[12]` - name, filter in a second color, count in brackets.
- Row color carries state (white normal, green healthy, red failing); no icons needed.
- Key hints as `<key>  Action`, key in accent, action dim, laid out in columns.
- Dim borders; color is spent on data, never on chrome.

## Borrowed (max 2 each)
- Soft Serve: the bottom bar - one solid accent chip for the name, then dim plain text,
  short chips at the right end. Used for the short bottom bar and the band's wf segment.
- btop: the hotkey letter inside a title drawn in the accent (the `1` of `1cpu`, the `m`
  of `menu` lit), and dotted mini bars for percentages. Used for pane titles and the 5h/week bars.

## Decision ledger
| decision | from |
|---|---|
| band = one `label value` line, values accented by threshold | k9s header |
| pane = one dim single-line border, title in the border with `[count]` | k9s |
| state = row color from theme keys (success/warning/error/inactive) | k9s |
| actions shown as `<key> Action` hint row at the pane foot | k9s |
| short bar = name chip + dim text | Soft Serve |
| usage bars as small block meters, not powerline | btop |

## Rejected
ccstatusline's powerline chevrons on colored backgrounds: they need a patched font, fight
the user's terminal theme, and spend color on chrome instead of on state.

## Round 7 references (Mobbin MCP, 2026-10-17, owner asked for the full pipeline)
The terminal grammar above (k9s) stays; these lock the information architecture, which the
critiques kept scoring low.
8. Linear issues view, grouped by status, count in each group header - https://mobbin.com/screens/d1d26f7d-e1e5-490f-ab4f-c96dd12854c1
9. Linear inbox, one line title + one dim line reason + time right - https://mobbin.com/screens/18c6955a-c42f-4cc1-9aa2-0276456720fb
10. Cursor automation run history: 3 stat tiles above a runs table (trigger, status word, duration) - https://mobbin.com/screens/8c9f4c28-46ed-4b65-acd9-e0a3762d33e4
11. 7shifts Pending Requests card: what waits on you sits in its own block, above everything, with the actions on the row - https://mobbin.com/screens/cc7d3fa8-66ee-45cb-9332-e7e557975c70
12. Modal function calls: status filter as ONE control with a dropdown, "1 error" badge on the tab - https://mobbin.com/screens/8d4aae1f-56e1-474d-9151-2e2a59b6c262
13. GitLab pipelines: status word + time under it in one fixed column - https://mobbin.com/screens/957013f7-8afb-4932-a788-4a08c14bb6d5

Primary for the Plan view: Linear issues (8). Signature traits: group headers carry the count
(`In Progress 2`), rows are one line (id, title, one meta), no repeated state word per row
inside a state group, the selected row gets the detail in a side or foot panel without
repeating what the row already says.
Borrowed: Modal (12) - the filter is one control showing only the active value and its count,
the others one key away, so filters never take more than one line at any width.
Borrowed: 7shifts (11) - Builds opens with a "Waits on you" block (questions, stuck) above runs.

## Round 7 live findings at 56 cols (before redesign)
- The act-now filter row wraps (`4: Ready 55` falls to its own line): 3 filter rows + intro + tabs + footer leave 5 list rows, of which 2 are repo headings.
- The detail block repeats the selected row's state word (`waits on you`) on its first line.
- The dim intro line costs a row on every view.
