# 0009 rationale: headless verify and test

## Context

`/check verify` proves a feature by running the app and exercising each acceptance criterion. Its own rules say that a behaviour it could not exercise is BLOCKED, never a pass, and that a missing browser tool is a block (`skills/check/modes/verify.md`, rules 1 to 3). In a `wf run` call there is no browser MCP: spec 0007 AC-4 gives every call an empty MCP list. So every web feature reports BLOCKED, which spec 0008 AC-4 parks. Your settled requirement (research doc section 6): headless verify should normally work through the chrome-devtools MCP with an isolated Brave, and BLOCKED only for real walls (login, captcha, 2FA, hardware).

The browser MCP cannot simply be switched on. Probe P1 (`verify.md`, 2026-10-12) showed that a call's sandboxed Bash runs in its own network namespace (its own private network, with its own localhost). A dev server that verify starts from Bash is reachable only from inside that call, and an MCP server (which Claude Code starts outside the sandbox) cannot reach it. Something outside the sandbox has to run the app, and that thing runs code the unattended calls may have written. Spec 0007's main guard (no credential in reach) has to hold for it too. The browser also runs outside the sandbox, with your user's file and network access.

`/test` decides what to test from `git diff HEAD` plus untracked files (`skills/test/SKILL.md`, step 1). Once a feature's work is committed, that list is empty, and `/test` asks "No changes found. What should I test?". In a run that question becomes a ping, or a guess. Checkpoint commits during a run (planned in feature 14, already done by `/develop` when a repo's `## Git` says `integration: on`) make this the normal case, not an edge case.

Both skills are vendored and overwritten on pull, so the fix cannot live in their text. It has to come from `wf`: its argv, its prompt, and processes it owns.

## Options considered

### Option 1: `wf` starts the app in its own bwrap jail (chosen)

Before each verify or debug call, `wf` runs the `app start` standing answer under `bwrap` with the network shared (so it is on the same localhost as the browser), credential paths hidden, the filesystem read only except the repo and package caches, and the call's stripped env. It waits for `app url` to answer, then runs the call, and stops the app after it. The browser MCP is given only to those calls, pinned, isolated, headless, behind a dead proxy and a navigation hook.

**Pros**:
- The model never decides what runs outside the sandbox. `wf` runs one command you wrote, frozen at start.
- Keeps spec 0007's guard: no credential is reachable from the app, the same bar as a call.
- `bwrap` is already required by spec 0007 AC-8, so there is no new dependency.
- A fresh app per call means verify always sees the current code, with no reliance on hot reload.

**Cons**:
- More `wf` code: an argv builder, a readiness loop, and process group cleanup on every path.
- An app with outside dependencies (database, Docker) must have them running, or it parks.
- The app shares your network, so it can reach any host (it has no credentials to use there).

### Option 2: the call starts the app through `sandbox.excludedCommands`

`wf` adds the `app start` command to the sandbox exclusions in its `--settings`, so the verify call's Bash can start it outside the sandbox on the real localhost.

**Pros**:
- Almost no `wf` code. Verify starts and stops the app the way it does by hand.

**Cons**:
- An excluded command runs with no jail, so it can read `~/.ssh` and push with your keys. That breaks spec 0007's main guard.
- Matching is by command prefix, so the model controls what actually runs outside the sandbox (arguments, a changed script).
- Spec 0007 AC-8 refuses exclusions on purpose.

### Option 3: no browser, HTTP only inside the sandbox

Verify starts the app from Bash and checks routes with `curl` and HTML checks, inside the same sandbox.

**Pros**:
- No new process outside the sandbox and no MCP. Zero new attack surface.

**Cons**:
- No clicks, forms or screenshots, so UI behaviours stay BLOCKED and the feature cannot close unattended. It misses the stated requirement.

### Option 4: `wf` starts the app as a plain process

Like Option 1, with the stripped env but no jail.

**Pros**:
- The simplest version of Option 1.

**Cons**:
- The app can read your ssh keys and token files and write anywhere in your home. The env strip alone does not keep spec 0007's guard.

## Rationale

The force that decides it is spec 0007's main guard: nothing that unattended work produced may hold a credential. Options 2 and 4 put repo code outside every jail with your keys readable, so they undo feature 20 for any repo with a web app. Option 3 keeps the guard but fails the requirement this feature exists for. Option 1 is the only one that does both. Its cost (a jail argv and a readiness loop in `wf`) is small next to the alternative, and it follows the rule this repo already keeps: `wf` decides, not the model (the app command comes from your standing answers, not from a call).

The browser runs outside the sandbox no matter which option is picked, so it is locked separately. `--isolated` gives a throwaway profile (no cookies or logged in sessions), and a test refuses any entry that attaches to a running browser or names a profile. The dead proxy (`--proxyServer 127.0.0.1:9`) sends every non loopback request to a port where nothing listens. That covers links, scripts and IP literals, which a navigation hook alone would miss, and Chrome keeps loopback off the proxy by default, so the app still loads. The navigation hook stops `file://` and `chrome://` and other origins at the tool call, fails closed like spec 0007's agent guard, and compares origins rather than string prefixes. The tool denies remove the file read door (`upload_file`) and the file dumps verify never needs. Only verify and debug calls get any of it. The package is pinned so an upstream release cannot change a night run without the probes running again.

For `/test`, the merge base with `main` (else `master`) needs no stored state and works across runs and across your own commits made before the run. A per feature base kept in `wf`'s state folder would be narrower, but it misses work committed before `wf` first saw the feature, and it is one more piece of state to keep right. Forbidding commits would fight feature 14 and tangle features that share a night. The cost of the chosen way, several features on one branch all being tested, is visible (a scope question, a ping) rather than silent.

A cross check on another model (2026-10-12) found doors the first draft left open: browser tools that write files to any path, the repo's settings and git hooks and the `/run` agent sockets inside the app jail, WebRTC and QUIC past the proxy, leftover Brave processes, and the app running through decision waits. All 15 items were applied. You then fixed the threat model (accidental or prompt injected leaks, not a model working to escape) and closed hardening on this feature, so a later door is a new decision rather than another round.

## Amendment 2026-10-12: WebRTC flag and the MCP's own npm cache

P5 failed: WebRTC gathered a `srflx` candidate (your public IP) through the dead proxy. A direct probe (`probes/p5-webrtc.py`, no `claude -p`) showed `--force-webrtc-ip-handling-policy` does reach Brave's command line, and Brave 154 ignores it. The switch spelled `--webrtc-ip-handling-policy` works: no candidate at all, for a hostname and a raw IP STUN server, while the control without it leaks both times. AC-4 now uses that spelling. No other option (a seeded profile, a network namespace for Brave) was needed.

The same pass looked at the background security review of `p2-jail.sh`. The app jail writes `~/.npm`, `~/.cache` and `~/.local/share/pnpm`, so it could plant something a later unsandboxed session of yours runs. Calls already have that same write access (spec 0007 AC-2), so narrowing only the app would close nothing; you accepted it as a residual, named under Security model. One part was new, though: this spec has `npx` start the browser tool outside every sandbox, from `~/.npm`, which calls and the app can write. A planted package there would run with your keys readable on the next verify. So `wf` now gives the MCP and its start check their own npm cache under the state folder, which neither calls nor the app can write. The probe confirmed `npx` downloads into and runs from that folder.

## Probe evidence

P1 (localhost isolation) is the one fact the design rests on. It is in `verify.md` with command and result. P2 to P7 are the build's first step and gate the rest.
