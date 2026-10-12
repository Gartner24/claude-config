# Runner architecture

One page view of the workflow runner: what the parts are, how data moves between them, and the rules that hold everywhere. `/architect` reads this first (rule `spec-gate.md`) and updates it in the same commit when a decision changes an invariant. Specs: [0001](specs/0001-runner-stack-and-layout.md) stack, [0002](specs/0002-next-repo-command/index.md) `next`, [0003](specs/0003-scope-contract/index.md) scope contract, [0004](specs/0004-headless-step-loop/index.md) `wf run`, [0005](specs/0005-decision-parking-phone-pings/index.md) pings, [0006](specs/0006-standing-answers/index.md) standing answers, [0007](specs/0007-push-guard/index.md) push guard.

The goal: `wf` builds your scoped features overnight, pings you only for real decisions, and never pushes or designs on its own.

## Components

| Part | What it is | Writes | Reads |
|---|---|---|---|
| Scope files | `docs/scope/` (or `.workflow/scope/` in team repos). The plan and the queue: boxes, tags, header (`**Autopilot:**`, `**Source of truth:**`) | skills (`/scope`, `/architect`, `/develop`, `/check`, `/test`, `/sync`) | `next`, `wf run` |
| Specs | `docs/specs/`. The decisions a build follows | `/architect` only (`/sync` and `/develop` touch status lines) | the skills inside each call |
| `AGENTS.md` standing answers | an optional `## Standing answers` section per repo (spec 0006, being built) | you, by hand | `wf run`, once at start |
| `next` (`wf next`) | interactive launcher: finds the repo, reads the first open box, opens `claude <command>` in that repo after your Enter | nothing | scope files, `.git` files |
| `wf run` | unattended loop, one fresh `claude -p` call per box, then one `/sync` call (`runner/run.py`) | run records, the lock | scope files, standing answers, ntfy config |
| `claude -p` calls | the actual work. Each gets the unattended prompt, a deny list, a budget, a timeout | repo files (code, scope, specs) | everything a skill reads |
| ntfy (`runner/ntfy.py`) | pings your phone with a scrubbed question and buttons, polls the topic for your reply, burns one time codes | `~/.config/wf/ntfy.json` (codes burned) | the same file, the topic |
| State folder | `$XDG_STATE_HOME/wf` else `~/.local/state/wf`: `locks/<sha1>.lock`, `runs/<name>-<time>-<pid>/run.json`, `call-NN.json`, `call-NN.stderr` | `wf run` | you, later the morning report |
| Hooks | your `~/.claude` guard hooks (destructive command block, permission floor, Bash shape check), the design Stop hook, the review stack pre push receipt hook. They run inside every `claude -p` call too | deny or block a tool call | tool calls |
| Rules | always loaded `~/.claude/rules/`: `scope-contract.md` (how skills write scopes), `spec-gate.md` (how specs are accepted), `handoff.md` (who runs the next chain step), `lessons.md` | nothing | every session, headless included |
| Inhibitor | a `systemd-inhibit` child that keeps the machine awake, lid closed included, for the whole run | nothing | `wf`'s pid |

## Data flow

```
you: /architect (spec), /scope (boxes), Autopilot allowed, standing answers
        |
        v
  scope files + specs + AGENTS.md  <--------------------------------+
        |                                                           |
        v                                                           |
  wf run: start checks -> confirm (Enter or -y) -> lock, inhibitor  |
        |                                                           |
        v                                                           |
  claude -p <box command>  --(edits code, ticks boxes)--------------+
        |
        v
  wf rereads the scope: next box, Autopilot, branch
        |-- error, cap, no progress, guard ---------> stop, run.json
        |-- DECISION NEEDED + OPTION lines ---------> ntfy ping -> your reply -> claude -p --resume
        |-- next box in the same feature -----------> next call
        '-- feature finished -----------------------> claude -p /sync -> feature_done
```

A call never tells `wf` that it finished a box: `wf` only believes the files. Everything a call prints stays in the run folder; only the scrubbed ping text leaves the machine.

## Invariants (hold everywhere)

1. **Never pushes, merges or marks a PR ready.** `wf` itself runs no git write command. Every call gets the prompt line and a deny list for the common spellings. Today that is a backstop only: `env git push` and `gh api` get past it (review 2026-10-12). Feature 20 ([spec 0007](specs/0007-push-guard/index.md)) makes it hold outside the model: no credential in a call as the main guard, then the Bash sandbox, tool denies and hashed hook and config files. Threat model: an accidental or prompt injected push, not a model actively working to escape; the residual risks are listed once in spec 0007.
2. **Never decides design or accepts a spec unattended.** `wf run` refuses any box whose command is not on the allow list, so `/architect`, `/scope`, `/audit` and `design` boxes stay with you. Accepting a spec has no standing answer and never will (spec 0006). Inside an allowed step, any panel other than the three fixed ones and your standing answers becomes a ping. Open gap: a `/develop` step can still change UI without a locked design (feature 9).
3. **Paid steps never run unattended.** Billed commands (`/code-review ultra`, `/review-stack sealed`, `/ship`, deploys) are never on the allow list. Open gap: a tool inside an allowed step that bills is not stopped (feature 8).
4. **What pings you:** a `DECISION NEEDED:` line at the end of a call, and nothing else, plus the short `accepted, resuming` ack after your reply and the `wf ntfy test` you start yourself. No ping for start, finish or failure.
5. **Never automatic:** setting `**Autopilot:** allowed`, adding `· auto`, accepting a spec, choosing a tier, starting a run (Enter or `-y`), pushing or opening a PR, design direction, and marking a feature `done` except through `done: yes` on the box `wf` itself computed as the last one (spec 0006).
6. **Opt in, one at a time:** a run needs `**Autopilot:** allowed`, a named work branch (not `main`, `master` or detached), and the repo lock. Autopilot, branch and scope are checked again after every call and every wait.
7. **The files are the truth:** a box is done only when the scope says so. `wf` writes nothing in a repo; only the calls do.
8. **Bounded:** budget and timeout per call, call and hour caps per run, a wait cap per decision, a clean stop on Ctrl C, SIGHUP or SIGTERM, and a `run.json` with a stop reason on every path.

## Skills and commands under `wf run`

`wf run` decides by the first word of the box command, or the first two for `/check verify` (allow list in `runner/run.py`). Anything not listed as `runs` is refused `manual_box` before any call, or stops the run as `manual_box` when it is the next box.

| Command | `wf run` | Pings you for |
|---|---|---|
| `/develop` | runs | an owed decision (route to `/architect`, or build on an `Assumed` spec); any panel not fixed |
| `/check verify` | runs | the done offer, unless `done: yes` applies |
| `/test` | runs | `Run tests?` unless `run suite: yes`; the done offer unless `done: yes` applies |
| `/debug` | runs | a fix choice it cannot make |
| `/document` | runs | nothing for `Doc type` (fixed answer); other panels |
| `/sync` | runs, only as the final call, never as a box | any panel it shows |
| `/architect`, `/scope`, `/audit` | refuses | |
| `design`, `design-gate`, `brand-system`, `assets` as a box | refuses | |
| `/check review`, `/check` with any other second word, `/review`, `/code-review`, `/review-stack`, `/jj-security-review` | refuses | |
| `/ship`, `/pr`, `/land-and-deploy`, `/document-release`, deploys | refuses | |
| `/rollover`, `/save-and-clear`, `/resume-from-clear`, `/clear` | refuses (each call is already a fresh session) | |
| any other command | refuses | |
| a box with no command | stops (exit 3 at start, `no_command` mid run) | |

Fixed answers in every call: `Doc type` the recommended option, `Save verify steps?` Save to verify.md, `Agent skills` Not now, later (spec 0005). Standing answers per repo: `run suite` and `done` (spec 0006). No standing answer touches a design or spec panel.

`next` is not bound by this table: you are at the keyboard, so it opens any command after your Enter.
