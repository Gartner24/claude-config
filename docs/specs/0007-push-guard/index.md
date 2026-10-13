# 0007. Push guard outside the model

**Date**: 2026-10-12
**Status**: Accepted
**Amended by**: [0011](../0011-build-decision-queue/index.md) - AC-9's `guard:` part moved from the confirm line to its own line in each repo's plan block (0011 AC-6), same text after `guard: `; AC-8's missing `claude` exits 1 (0011 AC-4).
**Amended**: 2026-10-12, review stack findings M7, M8, M9 (`docs/briefs/runner-review-stack-2026-10-12.md`): AC-1 credential paths widened by spec 0008 AC-7; AC-2 and AC-7 submodule `config` and `hooks`; the spec 0004 `DENIED` push rule narrowed (spec 0004 AC-4).
**Amended**: 2026-10-12, second review stack (`c95f181..d20a328`, same brief): AC-2 and AC-7 cover submodules cloned in place and each submodule's `.git` pointer, `config.worktree` and include targets; AC-8 lists the refusals the first review added; AC-9 gains `submodules`; spec 0011 AC-9 counts a file at or under a submodule's `.git` as its repo's own.
**Amended by**: [0008](../0008-failure-park-policy/index.md) - AC-1 env strip widened to paid API keys, tokens and secrets (one `call_env()`); `~/.aws`, `~/.config/gcloud`, `~/.azure` join AC-2 `denyRead` and AC-5 `Read` denies. [0009](../0009-headless-verify-test/index.md) - AC-4: `/check verify` and debug calls in a repo naming an app get `MCP_BROWSER` instead of the empty list; AC-2 settings on those calls gain the browser hook. [0010](../0010-design-enforcement-unattended/index.md) - AC-5 deny list gains `Skill(design)` and `Skill(brand-system)`.

## Summary

Today a `wf run` call is kept from pushing by a prompt line and a list of denied command prefixes, and `env git push` or `gh api` walk past both. This spec moves the guard below the model. The main guard: a call never holds a credential that can push (tokens and the ssh agent are stripped, key and token files are unreadable). Behind it, shell commands run in Claude Code's Bash sandbox (an OS level jail) that cannot reach GitHub or the repo's remotes, MCP servers are limited to a fixed empty list, and the files that run outside the sandbox (settings, hooks, git config, programs on your PATH) cannot be edited and are checked between calls. Nothing changes outside a run.

## What you're agreeing to

- A call has no way to log in to GitHub or your remotes, and cannot reach them, so pushes, PRs, merges, issue reads and `git fetch` all fail during a run.
- This guards against an accidental or prompt injected push, not against a model actively working to break out. The leftover risks are listed once, below, and accepted.
- Calls cannot start cloud agents, routines or messages to cloud sessions; local subagents keep working.
- Calls get no MCP servers, cannot edit settings, hooks, git config (a worktree's git pointers and any file a git config includes too) or anything on your PATH, and a change to any of those stops the run.
- `wf run` refuses to start when the sandbox cannot run.
- Nothing is accepted until the probes in `verify.md` pass on the real `claude`.

## Threat model

Guarded: a call that pushes, opens or merges a PR, or otherwise publishes to GitHub or the repo's remotes by accident, by a wrong reading of a skill, or because fetched content told it to (prompt injection), whatever spelling or tool it reaches for first.

Not guarded, accepted residual risk (listed here once, no further hardening rounds on this feature):
- A model deliberately working to escape: finding a sandbox or bubblewrap bug, chaining several unguarded steps on purpose, or using a door not named here.
- Publishing to a host that is neither GitHub, a listed forge, nor one of the repo's remotes (a paste site, an unlisted forge through `curl`). With no credentials it cannot push to your accounts, but it can send repo content out.
- A hook script that runs a file outside the denied and hashed set by a path it computes at run time.
- A raw IP address gets past `deniedDomains`, which matches hostnames only (probe 11, 2026-10-12). With no credential in the call this cannot push to your accounts.
- Changes in Claude Code's sandbox behaviour after an upgrade, until the `verify.md` probes run again.

## Requirements

**User stories**:
- As you, I want a push attempted from inside a `wf run` call to fail whatever its spelling or tool, so that an overnight run can never publish anything.
- As you, I want my own pushes outside a run to work exactly as before, so that the guard costs me nothing by day.
- As you, I want a run that cannot be guarded to never start, so that a missing tool never quietly drops me back to the prefix list.

**Acceptance criteria**:
- **AC-1** (main guard, no credentials): every call and resume runs with an env copied from `wf`'s, minus `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN`, `SSH_AUTH_SOCK`, `SSH_ASKPASS`, `GIT_ASKPASS`, `GIT_SSH`, `GIT_SSH_COMMAND`, plus `ENABLE_CLAUDEAI_MCP_SERVERS=false`. The credential paths `~/.config/gh`, `~/.ssh`, `~/.git-credentials`, `~/.netrc` are in the sandbox `denyRead` (AC-2) and get `Read(//<path>/**)` (or `Read(//<path>)` for a file) in `--disallowedTools` (AC-5).
- **AC-2**: every call and resume gets `--settings` as an inline JSON string (not a file), keys in this order: `{"sandbox": {"enabled": true, "failIfUnavailable": true, "autoAllowBashIfSandboxed": true, "allowUnsandboxedCommands": false, "network": {"allowedDomains": ["*"], "deniedDomains": <hosts>, "strictAllowlist": true}, "filesystem": {"allowWrite": <write paths>, "denyWrite": <write denies>, "denyRead": <credential paths>}}}`. Write paths: the repo path, `git rev-parse --path-format=absolute --git-common-dir`, `~/.npm`, `~/.cache`, `~/.local/share/pnpm` (the per user temp dir is writable by default). Write denies: the AC-5 deny list minus the git common dir, plus `<git common dir>/config` and `<git common dir>/hooks`, plus, for each submodule git dir (every folder under `<git common dir>/modules` that holds a `HEAD` file, nested ones included, in sorted walk order), its `config` and `hooks` (amendment 2026-10-12, review stack finding M8: a submodule's hooks used to stay writable and run at your next commit there). Second review amendment: the submodules are also read from the index (`git ls-files -z --stage`, every mode `160000` entry); a gitlink whose `<repo>/<path>/.git` is a real folder (a submodule cloned in place) is a submodule git dir too, after the ones under `modules`, and gets the same `config` and `hooks`; for every submodule git dir, its `config.worktree` and the include targets of its `config` and `config.worktree` (found as in AC-7) join the AC-5 list, and so does each gitlink's `.git` pointer file. A gitlink whose `.git` is absent (a submodule not checked out) has that path hashed as `absent` in AC-7 but is not denied, since the sandbox's empty placeholder would read to git as a broken `.git` file; creating it stops the repo. A gitlink whose `.git` is a symlink refuses `no_sandbox` (`<path> is a symlink, so its git dir cannot be guarded`). The whole in place `.git` folder is denied to Edit (AC-5 rules), but only its `config` and `hooks` to the sandbox, so a commit inside the submodule still works. Accepted limit: a submodule nested inside an in place clone is not walked. If probe 5 (AC-10) shows `"*"` is not accepted, this AC goes back to `/architect` before the build (the fallback, an allowlist of registries, is a different decision). IP literals getting past `deniedDomains` is accepted (Threat model).
- **AC-3**: `<hosts>` is `github.com`, `*.github.com`, `*.githubusercontent.com`, `gitlab.com`, `*.gitlab.com`, `bitbucket.org`, `*.bitbucket.org`, `codeberg.org`, `*.sr.ht`, plus the host of every URL of every remote (`git remote -v`, fetch and push lines), computed once at start. Host parsing: `scheme://[user@]host[:port]/...` gives `host`; scp form `[user@]host:path` gives `host`; a local path or `file://` gives none. Sorted, deduplicated.
- **AC-4**: every call and resume gets `--strict-mcp-config --mcp-config '{"mcpServers": {}}'`, the value a constant `MCP_ALLOW` in `runner/run.py` passed inline. Feature 7 adds chrome-devtools there with its own isolation check.
- **AC-5**: `--disallowedTools` is the existing `DENIED` list plus `Artifact`, `ArtifactData`, `ArtifactComments`, `RemoteTrigger`, `CronCreate`, `CronDelete`, `SendMessage`, `Skill(schedule)`, the AC-1 `Read` denies, and `Edit(//<p>)` (with `/**` for a directory) for every path in the deny list, computed once at start. `Edit` only: Claude Code 2.1.296 does not match `Write(path)` rules in file permission checks, and `Edit` rules cover every file editing tool (probe run of 2026-10-12). The deny list:
  - every top level entry of `~/.claude` except `projects` (so memory writes keep working), and `~/.claude.json`
  - the repo's `.claude` directory and the git common dir
  - `~/.gitconfig`, `~/.config/git`, `~/.config/gh`, `~/.bashrc`, `~/.bash_profile`, `~/.profile`, `~/.zshrc`, `~/.zshenv`, `~/.zprofile`
  - every `PATH` directory `wf`'s user can write (`os.access(W_OK)`), and `~/.local/share/claude`
  - for every hook token (AC-7) outside the dirs above, its parent directory, both through the link path and the real path.
  - the git pointer and config files of AC-7 (amendment of 2026-10-12): in a linked worktree the repo's `.git` file, `<git dir>/commondir` and `<git dir>/gitdir`; in any checkout `<git dir>/config.worktree`; and every include target. These stay in the write denies too (they are not the git common dir). The rest of a worktree's git dir (`HEAD`, `index`, `logs/`, `COMMIT_EDITMSG`) stays writable, because a commit writes there. A path already under a denied folder is deduplicated, no error. Untested: whether the sandbox stops a call creating one of these files that was absent at start; the AC-7 hash still catches it before the next call.
- **AC-5b** (no cloud agents): the AC-2 `--settings` JSON also carries `"hooks": {"PreToolUse": [{"matcher": "Agent", "hooks": [{"type": "command", "timeout": 10, "command": "<python3> -c '<AGENT_GUARD>' || exit 2"}]}]}`, where `<python3>` is the absolute path resolved at start (AC-6) and `AGENT_GUARD` is a constant in `runner/run.py`. It fails closed: it reads the hook JSON from stdin and exits 0 only when the input parses, `tool_name` is `Agent`, `tool_input` is an object, and `tool_input.isolation` is absent, `null` or `"worktree"`; every other case, any exception included, prints `wf run: remote agents are refused` to stderr and exits 2, and the shell `|| exit 2` turns any other non zero exit (a crash, a missing interpreter) into 2.
- **AC-6**: at start `wf` resolves `git`, `claude` and `python3` with `shutil.which` then `os.path.realpath`, and every later `git` and `claude` it runs (calls, resumes, `head_branch`, `changes`, rereads) uses those absolute paths.
- **AC-7**: guarded files, hashed at start with sha256 (`absent` for a missing one) and compared before every call and every resume: the repo's `.claude/settings.json` and `.claude/settings.local.json`, `~/.claude/settings.json` and `~/.claude/settings.local.json`, every `~/.claude/plugins/cache/**/hooks.json`, `<git common dir>/config`, the worktree files, the include targets, every file in `<git common dir>/hooks`, each submodule git dir's `config` and every file in its `hooks` (AC-2), each gitlink's `.git` pointer file and each submodule git dir's `config.worktree` and include targets (AC-2, second review), and every hook token. Worktree files (amendment of 2026-10-12): `<git dir>` is `git rev-parse --path-format=absolute --git-dir` at start; when it differs from the git common dir (a linked worktree), the repo's `.git` file, `<git dir>/commondir` and `<git dir>/gitdir`; in every checkout `<git dir>/config.worktree` (`absent` when missing, so a new one is caught). Include targets: for `<git common dir>/config`, `<git dir>/config.worktree` and, in turn, each target found, every value of `git config --file <file> --get-regexp '^include(if\..*)?\.path$'`, whatever its condition, with `~/` expanded to the home folder, a value starting with `%(prefix)/` skipped, and a relative value resolved against the including file's folder; targets join the list in discovery order (depth first, in the file's order), each file is read once, a missing one is `absent`, and a directory is not hashed (AC-5 still denies it as a folder). The `.git` file and each include target keep both their link path and real path, as hook tokens do; a path already in the list is not added again. Each file is read with `git -C /` (inside the repo, git first loads the repo's own config with its includes); when git cannot read one, `start_checks()` refuses with `no_sandbox` and `git cannot read <file>: <git's error>`, because the targets are then unknown (added at build, 2026-10-12). A hook token: in each existing settings file, each `hooks.<Event>[].hooks[].command` (only `type: command`; `statusLine` excluded) split with `shlex.split`, falling back to `str.split` on `ValueError`; a token counts when it contains `/` or starts with `~`, contains no `$`, and after expanding `~` is a regular file (`os.path.isfile`); both its link path and real path are kept. Empty placeholder (amendment of 2026-10-12, after the first real run stopped on `.git/config.worktree`): the sandbox's `denyWrite` creates an empty regular file for an absent denied path at run start, so a file `absent` at start that is now an empty regular file, not a symlink, counts as unchanged; any content still counts as a change. A difference stops the run with reason `guard_changed` and detail `<path> changed during the run; inspect or delete it before opening a session in this repo`, naming the first changed path in the order above.
- **AC-8**: `start_checks()` refuses with reason `no_sandbox` (exit 5, the `refuse()` path, no lock, no call) when `bwrap`, `socat`, `git`, `claude` or `python3` does not resolve on `PATH`, or when `~/.claude/settings.json` or `~/.claude/settings.local.json` has a non empty `sandbox.excludedCommands` (user level exclusions still apply under `--settings`). The check runs after the Autopilot check. A missing `claude` exits 1 instead (spec 0011 AC-4). Also `no_sandbox`, because a guard built on an unknown answer would leave something unhashed (review stack 2026-10-12, both rounds): a repo or user settings file that cannot be read or parsed (`<file> cannot be read as settings, so its hooks are unknown: ...`), `git remote -v` failing (`git remote -v failed: ...`), the hooks folder, a submodule hooks folder or a folder under `<git common dir>/modules` that cannot be listed (`cannot list <folder>: <error>`), and `git ls-files --stage` failing.
- **AC-9**: `run.json` gets `guard`: `{"hosts": [...], "write_paths": [...], "deny_paths": [...], "binaries": {"git": path, "claude": path, "python3": path}, "submodules": [<repo>/<gitlink path>/.git, ...], "guarded_files": {path: sha256 or "absent"}, "absent_denied": [...]}`, set before the first call (`submodules` added by the second review, `absent_denied` by spec 0009). The confirm line gets `guard: <n> hosts, <k> files` after the caps part.
- **AC-10**: probes on the real `claude` (2.1.296), each recorded in `verify.md` with command and result. All must pass before this spec is accepted, and the set runs again after every Claude Code upgrade. From a call built with the AC-1 to AC-5 argv and env in a scratch repo whose `origin` is a GitHub URL: (1) `git ls-remote origin` fails; (2) `env git ls-remote git@github.com:git/git.git` fails; (3) `gh api user` and `gh auth token` both fail, each run through a one command helper script that prints only a REACHABLE or BLOCKED marker, never a token; (4) the same with `dangerouslyDisableSandbox` fails; (5) `curl -s -o /dev/null -w '%{http_code}' https://pypi.org/simple/` prints `200`; (6) a subagent's `gh api user` fails; (7) writing `~/probe-wf` fails, writing `~/.cache/probe-wf` succeeds; (8) appending to an existing non settings file under the repo's `.claude/` from Bash fails and the Edit tool on it is denied (a settings file is stopped earlier by the auto mode classifier, which hides the sandbox result); (9) the call lists no `mcp__` tools, plugin and claude.ai ones included; (10) a project `.claude/settings.json` with `sandbox.excludedCommands: ["gh"]` does not make (3) succeed; (11) `curl -k -H 'Host: api.github.com' https://<a github.com IP>/` fails; (12) creating a file under the repo's `.claude/` that did not exist at start fails from Bash; (13) in a repo with at least one commit, an `Agent` call with `isolation: "remote"` is refused by the AC-5b hook, and the `schedule` skill, `RemoteTrigger` and `SendMessage` are all denied; (14) the AC-5b hook command, fed malformed JSON, an empty stdin, `isolation: "remote"`, and a valid local `Agent` input, exits 2, 2, 2 and 0. If 12, 13 or 14 fails, that goes back to `/architect`, not into the build.
- **AC-11**: outside a run nothing changes: no hook, git config or global setting is written by `wf` or `install.sh` for this feature.

## Decision

**Chosen option**: Option 1: no credentials in a call as the main guard, with the Claude Code Bash sandbox and tool denies as layers behind it.

`wf` builds the guard into each call's argv and env, and checks the guarded files between calls. Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch**:
- `guard` on the `Run`: `hosts`, `write_paths`, `deny_paths` (sorted lists), `binaries` (`git`, `claude`, `python3` absolute paths), `files` (ordered map path to sha256 or `absent`). Computed once in `start_checks()`, written to `run.json`. No other storage.

**API surface** (CLI only):
| Surface | Inputs | Output | Errors |
|---|---|---|---|
| `wf run <repo>` start | remotes, git common dir, settings files, plugin `hooks.json`, `PATH`, `~/.claude` entries | `guard:` part on the confirm line, `guard` in `run.json` | `refused: no_sandbox: <what>`, exit 5 |
| each call and resume | the frozen guard | stripped env, inline `--settings`, `--strict-mcp-config --mcp-config '<MCP_ALLOW>'`, extended `--disallowedTools`, absolute `claude` | stop `guard_changed: <detail>` |

**Value sourcing**:
| Action | Value | Source |
|---|---|---|
| each call | env | `wf`'s env minus the AC-1 names, plus `ENABLE_CLAUDEAI_MCP_SERVERS=false` |
| start | blocked hosts | the fixed AC-3 set plus `git remote -v` |
| start | write paths | repo path, `git rev-parse --path-format=absolute --git-common-dir`, fixed cache dirs, AC-2 |
| start | deny paths | the AC-5 list: `~/.claude` listing, fixed dotfiles, writable `PATH` dirs, hook token parents |
| start | guarded files and hashes | AC-7 list |
| start | git dir, worktree files | `git rev-parse --path-format=absolute --git-dir`, AC-7 |
| start | include targets | `git config --file <f> --get-regexp '^include(if\..*)?\.path$'` on each guarded git config, AC-7 |
| start | `git`, `claude` paths | `shutil.which` plus `realpath`, AC-6 |
| each call | MCP config | `MCP_ALLOW` constant in `runner/run.py` |
| each call | changed or not | sha256 of each guarded file now vs at start |

**Key invariants**:
- No call starts without the stripped env, the inline sandbox settings, the strict MCP flags and the extended deny list; there is no flag to turn the guard off.
- The guard is computed once at start and never relaxed by anything a call writes.
- A guarded file that changes stops the run before the next call or resume, never after it.
- `wf` writes nothing outside its state folder for this feature (AC-11).

**Security model**: see Threat model. Layers, strongest first: no credential reachable (env, `denyRead`, `Read` denies); Bash jailed by bubblewrap (network to forges and remotes, writes outside the write paths); tools that run outside the sandbox (Edit, Write, Read, Artifact) denied on the paths that matter; MCP limited to an empty inline list; hooks, git config and programs `wf` runs frozen by hash or resolved to absolute paths at start; the prefix deny list and prompt line as the first, cheapest layer.

**Configuration required**: none new.

**Critical test scenarios**:
- Env: a call's env lacks every AC-1 name even when `wf` has them set, and has `ENABLE_CLAUDEAI_MCP_SERVERS=false`, verifies **AC-1**
- Argv: a call and a resume both carry the AC-2 JSON (parsed and compared as a dict), the MCP flags with the inline constant, and the AC-5 deny list, verifies **AC-2**, **AC-4**, **AC-5**
- Hosts: remotes in https, ssh, scp, `file://` and local path forms give the expected sorted set with the fixed forges, verifies **AC-3**
- Deny paths: a fake home with `~/.claude/{projects,hooks,settings.json}`, a writable and a read only `PATH` dir, and a symlinked hook token give the expected list (no `projects`, both link and real parent), verifies **AC-5**
- Binaries: a fake `git` earlier on `PATH` after start is not the one `wf` runs, verifies **AC-6**
- Hook tokens: a command with nested quotes, `>/dev/null`, a bare `bash`, and a `$HOME` token yields only the real script files, verifies **AC-7**
- Guard changed: the fake claude edits `.claude/settings.json` during call 1; the run stops `guard_changed` before call 2; the same before a resume; the detail matches; an absent `.git/config.worktree` left as an empty file by call 1 does not stop the run, one with content does, verifies **AC-7**
- Worktree and includes: a run in a linked worktree hashes and denies its `.git` file, `commondir`, `gitdir` and `config.worktree`, still commits (its `HEAD`, `index`, `logs/` are not guarded); an `[include]` relative path, an `[includeIf]` `~` path and an include inside an included file are all hashed and denied; a call that rewrites the `.git` file or an include target stops `guard_changed`, verifies **AC-5**, **AC-7**
- Refusals: no `bwrap`, no `socat`, user `excludedCommands`, each exit 5 with no lock and no run folder, verifies **AC-8**
- Record: `run.json` `guard` and the confirm line part, verifies **AC-9**
- Agent guard: the AC-5b command run directly with the four probe 14 inputs, plus a missing interpreter path, exits 2, 2, 2, 0 and 2, verifies **AC-5b**
- Probes 1 to 14 on the real `claude`, verifies **AC-10**
- Outside a run: `install.sh --dry-run` output and `git config --global --list` unchanged by the feature, verifies **AC-11**

## Build plan

Skateboard: step 1 is the probe gate; step 2 alone already removes every credential from a call.

1. Run the AC-10 probes with a hand built argv and env and record them in `verify.md`; go back to `/architect` if 5, 12, 13 or 14 fails, satisfies **AC-10**
2. Stripped env and `ENABLE_CLAUDEAI_MCP_SERVERS` in `call()`; absolute `git` and `claude` resolved at start and used everywhere; tests, satisfies **AC-1**, **AC-6**
3. `remote_hosts()`, write paths, deny paths, the inline AC-2 JSON with the AC-5b hook and `MCP_ALLOW` flags in `call()` for calls and resumes; the extended deny list; tests, satisfies **AC-2**, **AC-3**, **AC-4**, **AC-5**, **AC-5b**
4. Guarded files: collect hook tokens, hash, compare before each call and resume, stop `guard_changed`; tests with a `write_file` step in the fake claude, satisfies **AC-7**
5. `no_sandbox` start checks, `run.json` `guard`, confirm line part; tests, satisfies **AC-8**, **AC-9**, **AC-11**
6. Run the AC-10 probes again through `wf run` itself on a scratch repo and add them to `verify.md`, satisfies **AC-10**
7. Amendment of 2026-10-12: worktree files and include targets in the AC-7 hashes and the AC-5 deny list; tests, satisfies **AC-5**, **AC-7**

## Consequences

**Positive**:
- Invariant 1 holds below the model: no credential in a call, and each other door has a named control.
- Per call, so your day to day pushes and terminals are untouched.

**Negative / tradeoffs**:
- No GitHub reads during a run: an issue sourced feature needs its intent in the scope row first, and nothing can `git fetch`.
- A call cannot edit `~/.claude` (outside memory), git config, dotfiles or anything on a writable `PATH` dir; a step that legitimately needs to fails inside the run.
- Bound to Claude Code sandbox behaviour; an upgrade can change it silently, so the probes rerun after each upgrade.
- A build that writes outside the write paths fails inside the run (a ping or a failed step, never a silent pass).
- The residual risks in Threat model stay open by choice.

**Neutral**:
- The scope row's wording (pre-push hook, lock) is replaced; its Done when is reworded to match.
- The prefix deny list stays as a cheap first line.

## Follow-up

- [ ] Root `AGENTS.md` Gotchas: rerun the 0007 `verify.md` probes after a Claude Code upgrade; `/sync` owns this.
- [ ] Feature 7: add chrome-devtools to `MCP_ALLOW` in `runner/run.py`, isolated profile only, never attached to your running browser, with a self check that refuses an entry that attaches.
- [ ] Not in the 2026-10-12 amendment (you asked for no other changes), same class, open: include targets of `~/.gitconfig` and `~/.config/git/config` (those two files are denied but not hashed), a `core.hooksPath` outside `<git common dir>/hooks`, `<git common dir>/info/attributes`.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).
