# 0007. Push guard outside the model: rationale

## Context

> Premise note: the scope row asked for "a git pre-push guard ... while `wf run` holds that repo's lock". A pre-push hook cannot meet the row's own Done when ("refused whatever its spelling"): `git push --no-verify` skips it, `git -c core.hooksPath=/dev/null push` replaces it, and `gh api`, `gh pr create` or an MCP tool never run git at all. You chose to guard the call itself instead (the design conversation of 2026-10-12), so the lock plays no part and the Done when is reworded to match.

`wf run` (spec 0004) starts one `claude -p` call per box, in auto permission mode, unattended, often overnight. Invariant 1 of [docs/architecture.md](../../architecture.md) says a run never pushes, merges or marks a PR ready. Today that rests on two things the model controls or can talk around: a prompt line, and a `--disallowedTools` deny list that matches command prefixes only. The `/review` of 2026-10-12 found `env git push` and `gh api` both get past it.

A push is a network write to a remote host. It can leave a call through four doors: Bash (any spelling of git, gh, curl, ssh, a script), an MCP tool that talks to GitHub, a hook (hooks run outside any model control, with your full rights), and the settings that decide the other three, which a call can edit because it can write the repo. A guard that closes one door and leaves another is the same backstop as today.

The cost of getting it wrong is public and hard to undo: a half built branch pushed, a PR opened from a client repo, or a merge, all while you are asleep.

## Options considered

### Option 1: Claude Code Bash sandbox per call, plus closing the non Bash doors

`wf` passes `--settings` to every call with the Bash sandbox on (bubblewrap, a Linux tool that runs each command in a locked down namespace), the unsandboxed fallback off, GitHub and every remote's host unreachable, and writes limited to the repo, the git dir, temp and package caches. It adds `--strict-mcp-config` with a shipped MCP allowlist, denies edits to settings and hook files, and stops the run if any of them change between calls.

**Pros**:
- Holds at the OS level: no spelling, flag or script reaches the host.
- Per call, so nothing changes outside a run and nothing needs releasing.
- Covers `gh api` and every other tool that needs the network, not just git.

**Cons**:
- Depends on Claude Code sandbox behaviour (keys, merge rules, subagents), which needs a probe now and again after each upgrade.
- Calls lose all GitHub reads (`gh issue view`, `git fetch`).
- The filesystem limits can break a build that writes somewhere unexpected.

### Option 2: pre-push hook keyed on the lock (the scope row's wording)

A global `core.hooksPath` pre-push hook refuses while the repo's `wf` lock is held.

**Pros**:
- Small, readable refusal message, also catches a push from another terminal during a run.

**Cons**:
- `--no-verify`, `-c core.hooksPath` and `gh api` get through, so the Done when fails.
- A global `core.hooksPath` replaces every repo's own `.git/hooks`, including the review stack receipt hook.

### Option 3: strip push credentials per call

Unset `SSH_AUTH_SOCK` and set `GH_TOKEN`, `GIT_ASKPASS`, `GIT_SSH_COMMAND` to failing values in each call's environment.

**Pros**:
- No new tool, no sandbox dependency.

**Cons**:
- The model can reset any env var inline, and can read key files in `~/.ssh` and the `gh` token on disk.

### Option 4: sandbox plus pre-push hook

Option 1 plus Option 2's hook for a readable message.

**Pros**:
- Clear refusal text, and covers other terminals during a run.

**Cons**:
- Same `core.hooksPath` conflict as Option 2, more to install and test, and the sandbox already refuses.

## Rationale

Option 1, with one ordering you set after the cross check: a call holding no credential that can push is the main guard, and the sandbox and tool denies are layers behind it. A push needs a credential and a route; removing the credential holds without any reasoning about network spellings, and the route block covers the case where a credential is found anyway. The threat model is an accidental or prompt injected push, not a model working to escape; anything beyond that is accepted residual risk, listed once in `index.md`, with no further hardening rounds on this feature.

The forces are an unattended model with auto permissions and write access to the repo, and a requirement that holds whatever the spelling. Only a guard below the model's tools holds against every spelling, so the network door is closed by the OS, not by matching strings. The other doors are closed where they open: MCP servers by passing only an inline empty list (a list file in the repo would be writable when `wf` runs on this repo), and everything that runs outside the sandbox with your rights (hooks, plugin hooks, git config, programs on a writable `PATH` dir, the `git` and `claude` that `wf` itself runs) by denying the Edit and Write tools on it, resolving binaries at start, and checking hashes between calls, so a change stops the run instead of being trusted. The cross check of 2026-10-12 found those outside the sandbox doors; directory denies cover them with less code than a per file list.

The lock based hook was rejected because it is the same class of guard as the deny list (it trusts the process not to skip it). Blocking only GitHub plus each remote's host, rather than all network, keeps package installs working; a build that needs GitHub mid run (an issue read, a `git fetch`) is the accepted cost, and an issue sourced feature copies its intent into the scope row first. The prefix deny list stays as a first line: it is free and gives the model a clear denial instead of a network error it might try to route around.
