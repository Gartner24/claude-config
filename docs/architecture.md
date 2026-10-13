# Runner architecture

One page view of the workflow runner: what the parts are, how data moves between them, and the rules that hold everywhere. `/architect` reads this first (rule `spec-gate.md`) and updates it in the same commit when a decision changes an invariant. Specs: [0001](specs/0001-runner-stack-and-layout.md) stack, [0002](specs/0002-next-repo-command/index.md) `next`, [0003](specs/0003-scope-contract/index.md) scope contract, [0004](specs/0004-headless-step-loop/index.md) `wf run`, [0005](specs/0005-decision-parking-phone-pings/index.md) pings, [0006](specs/0006-standing-answers/index.md) standing answers, [0007](specs/0007-push-guard/index.md) push guard, [0008](specs/0008-failure-park-policy/index.md) failure and park policy, [0009](specs/0009-headless-verify-test/index.md) headless verify and test, [0010](specs/0010-design-enforcement-unattended/index.md) design enforcement, [0011](specs/0011-build-decision-queue/index.md) build and decision queue, [0014](specs/0014-runner-resilience/index.md) runner resilience, [0015](specs/0015-checks-that-cannot-lie/index.md) checks that cannot lie, [0016](specs/0016-guard-hook-false-alarms/index.md) guard hook false alarms, [0017](specs/0017-several-repos-at-once.md) several repos at once.

The goal: `wf` builds your scoped features overnight, pings you only for real decisions, and never pushes or designs on its own.

## Components

| Part | What it is | Writes | Reads |
|---|---|---|---|
| Scope files | `docs/scope/` (or `.workflow/scope/` in team repos). The plan and the queue: boxes, tags, header (`**Autopilot:**`, `**Source of truth:**`) | skills (`/scope`, `/architect`, `/develop`, `/check`, `/test`, `/sync`) | `next`, `wf run` |
| Specs | `docs/specs/`. The decisions a build follows | `/architect` only (`/sync` and `/develop` touch status lines) | the skills inside each call |
| `AGENTS.md` standing answers | an optional `## Standing answers` section per repo (spec 0006) | you, by hand | `wf run`, once at start and shown in the plan; reread before each call only to stop the repo if a call changed them (spec 0011 AC-6) |
| `next` (`wf next`) | interactive launcher: finds the repo, reads the first open box, opens `claude <command>` in that repo after your Enter | nothing | scope files, `.git` files |
| `wf run` | unattended loop, one fresh `claude -p` call per box, then one `/sync` call per feature (`runner/run.py`). With spec 0011 it works through a queue: every `· auto` feature with a ticked `(spec)` box, in every repo on your `wf allow` list (or one named repo), one feature at a time per repo, moving on after a park or a question | run records, the locks, `queue.json` | scope files, standing answers, ntfy config, trust list, `queue.json` |
| `wf queue`, `wf unpark` | read only plan of what `wf run` would do; clear a repo's or feature's parks and open questions (spec 0011) | `queue.json` (`wf unpark` only) | scope files, `queue.json`, locks |
| `claude -p` calls | the actual work. Each gets the unattended prompt, a deny list, a budget, a timeout | repo files (code, scope, specs) | everything a skill reads |
| ntfy (`runner/ntfy.py`) | pings your phone with a scrubbed question and buttons, polls the topic for your reply, burns one time codes | `~/.config/wf/ntfy.json` (codes burned) | the same file, the topic |
| State folder | `$XDG_STATE_HOME/wf` else `~/.local/state/wf`: `locks/<sha1>.lock`, `runs/<name>-<time>-<pid>/run.json`, `call-NN.json`, `call-NN.stderr`, `log.txt` (live event log with each call's transcript path, spec 0014), `queue.json` (parks and open questions kept between runs, spec 0011) | `wf run` | you, later the morning report |
| Hooks | your `~/.claude` guard hooks (destructive command block, permission floor, Bash shape check), the design Stop hook, the review stack pre push receipt hook. They run inside every `claude -p` call too | deny or block a tool call | tool calls |
| Rules | always loaded `~/.claude/rules/`: `scope-contract.md` (how skills write scopes), `spec-gate.md` (how specs are accepted), `handoff.md` (who runs the next chain step), `check-gates.md` (checks that can fail, spec `**Paths:**`, brief cross checks, spec 0015), `lessons.md` | nothing | every session, headless included |
| App jail and browser | only for `/check verify` and debug calls in a repo whose standing answers name `app start` and `app url` (spec 0009): `wf` runs the app under `bwrap` on the shared localhost, and the call gets a pinned, isolated, headless chrome-devtools MCP that reaches only loopback | `app-NN.log`, `shots/` in the run folder | the standing answers |
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
        |-- run stop (Ctrl C, caps, limit, global guard) --> stop, run.json
        |-- repo stop (branch, Autopilot, repo guard) -----> next repo
        |-- park (failure, BLOCKED, cap) ------------------> queue.json park, next feature
        |-- DECISION NEEDED + OPTION lines ----------------> queue.json, ntfy ping, next feature;
        |                                                     your reply -> claude -p --resume later
        |-- next box in the same feature ------------------> next call
        '-- feature finished ------------------------------> claude -p /sync -> feature_done, next feature
```

With spec 0011 the run picks answered questions first, then the next queued feature in trust list and file order, and waits up to `--max-wait` at the end for open questions. Spec 0011 is not built yet; until then a park or question ends the run or waits in place.

A call never tells `wf` that it finished a box: `wf` only believes the files. Everything a call prints stays in the run folder; only the scrubbed ping text leaves the machine.

## Invariants (hold everywhere)

1. **Never pushes, merges or marks a PR ready.** `wf` itself runs no git write command. Every call gets the prompt line and a deny list for the common spellings. Today that is a backstop only: `env git push` and `gh api` get past it (review 2026-10-12). Feature 20 ([spec 0007](specs/0007-push-guard/index.md)) makes it hold outside the model: no credential in a call as the main guard, then the Bash sandbox, tool denies and hashed hook and config files. Threat model: an accidental or prompt injected push, not a model actively working to escape; the residual risks are listed once in spec 0007. The same threat model covers the app and browser a run starts (spec 0009): an accidental or prompt injected leak, not a model working to escape, and no further hardening rounds on either feature.
2. **Never decides design or accepts a spec unattended.** `wf run` refuses any box whose command is not on the allow list, so `/architect`, `/scope`, `/audit` and `design` boxes stay with you. Accepting a spec has no standing answer and never will (spec 0006). Inside an allowed step, any panel other than the three fixed ones and your standing answers becomes a ping. UI with no locked design parks `blocked`, calls can never invoke `design` or `brand-system`, and a feature whose branch changed frontend files closes only with a passing `design-gate` report newer than each of them, else it parks `design_gate` before `/sync` ([spec 0010](specs/0010-design-enforcement-unattended/index.md)).
3. **Paid steps never run unattended.** Billed commands (`/code-review ultra`, `/review-stack sealed`, `/ship`, deploys) are never on the allow list. Feature 8 ([spec 0008](specs/0008-failure-park-policy/index.md)) closes the gap inside allowed steps: no API key, token, secret or cloud credential reaches a call.
4. **What pings you:** a `DECISION NEEDED:` line at the end of a call, and nothing else, plus the short `accepted, resuming` ack after your reply (`<id> accepted` with spec 0011), one re-ping per run of a question still open from an earlier run (spec 0011), and the `wf ntfy test` you start yourself. No ping for start, finish or failure.
5. **Never automatic:** setting `**Autopilot:** allowed`, adding `· auto`, accepting a spec, choosing a tier, starting a run (Enter or `-y`), pushing or opening a PR, design direction, and marking a feature `done` except through `done: yes` on the box `wf` itself computed as the last one (spec 0006).
6. **Opt in, one at a time:** a run needs `**Autopilot:** allowed` on a repo you listed with `wf allow` (spec 0008; a cloned scope cannot list itself), a named work branch (not `main`, `master` or detached), and the repo lock; a feature also needs `· auto` and a ticked `(spec)` box (spec 0011). One call at a time per repo (bare `wf run` runs one child per repo side by side, never two repos sharing a port, git common dir or folder, spec 0017), one feature at a time per repo, and every repo a run touches stays locked until it exits. While a repo is dirty and holds a park or open question, no other feature starts there. Autopilot, branch and scope are checked again after every call and every wait.
7. **The files are the truth:** a box is done only when the scope says so. `wf` writes nothing in a repo; only the calls do.
8. **Bounded:** budget and timeout per call, call and hour caps per run, a wait cap per decision, a clean stop on Ctrl C, SIGHUP or SIGTERM, at most 2 `/debug` calls, one usage limit wait (6 hours at most) and 91 minutes of API outage waits (spec 0014) per run, the run stopped `crash_loop` when two features in a row park with the same call error, denial or app failure (spec 0014), 120 s for the app to get ready and a sweep of every process left with the run's `WF_RUN` (spec 0009), and a `run.json` with a stop reason on every path. Every reason is a park (this feature is stuck, the run moves on), a repo stop (that repo is done for this run) or a run stop (the run ends), spec 0008 as amended by spec 0011. With the queue, `--max-calls` and the 2 debug attempts count per feature, `--max-hours`, the usage limit wait and the end of queue wait (`--max-wait`) per run.

## Skills and commands under `wf run`

`wf run` decides by the first word of the box command, or the first two for `/check verify` (allow list in `runner/run.py`). Anything not listed as `runs` is refused `manual_box` before any call, or stops the run as `manual_box` when it is the next box. A box ending ` · waits on you` (or whose first open milestone does) is refused `waiting` before the command check, whatever its command ([spec 0012](specs/0012-waiting-boxes-owed-to-you/index.md)), unless it also carries ` · later boxes go on`: then the build goes on past it and only the final `/sync` waits for it (spec 0014).

| Command | `wf run` | Pings you for |
|---|---|---|
| `/develop` | runs | an owed decision (route to `/architect`, or build on an `Assumed` spec); any panel not fixed |
| `/check verify` | runs; drives the app in the browser when the repo names one (spec 0009); runs `design-gate` when the branch changed frontend files (spec 0010); a pass without its `CAN FAIL CHECKED:` line parks `unchecked` (spec 0015) | the done offer, unless `done: yes` applies |
| `/test` | runs; a pass without its `MUTATION CHECKED:` line parks `unchecked` (spec 0015) | `Run tests?` unless `run suite: yes`; the done offer unless `done: yes` applies |
| `/debug` | runs | a fix choice it cannot make |
| `/document` | runs | nothing for `Doc type` (fixed answer); other panels |
| `/sync` | runs only as the feature's final call: automatically once every box is ticked, or as its `/sync` box once every other box is ticked (spec 0014) | any panel it shows |
| `/architect`, `/scope`, `/audit` | refuses | |
| `design`, `design-gate`, `brand-system`, `assets` as a box | refuses (inside a call, `design` and `brand-system` are denied, `design-gate` runs, spec 0010) | |
| `/check review`, `/check` with any other second word, `/review`, `/code-review`, `/review-stack`, `/jj-security-review` | refuses | |
| `/ship`, `/pr`, `/land-and-deploy`, `/document-release`, deploys | refuses | |
| `/rollover`, `/save-and-clear`, `/resume-from-clear`, `/clear` | refuses (each call is already a fresh session) | |
| any other command | refuses | |
| a box with no command | stops (exit 3 at start, `no_command` mid run) | |

Fixed answers in every call: `Doc type` the recommended option, `Save verify steps?` Save to verify.md, `Agent skills` Not now, later (spec 0005). Standing answers per repo: `run suite` and `done` (spec 0006). No standing answer touches a design or spec panel.

`next` is not bound by this table: you are at the keyboard, so it opens any command after your Enter.
