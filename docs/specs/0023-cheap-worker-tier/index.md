# 0023 · Cheap worker tier: `fb-ask`

**Date**: 2026-10-13
**Status**: Accepted (built 8490b26)
**Paths:** `scripts/fb-ask.py`, `bin/install.sh`, `_archive/runner/run.py`, `_archive/runner/report.py`, `_archive/runner/tests/*`, `claude-home/rules-on-demand/cheap-worker.md`, `AGENTS.md`
**Amends**: [0008](../../../_archive/runner/docs/specs/0008-failure-park-policy/index.md) AC-7 (one more credential folder hidden from calls).

## What you're agreeing to
- Boring reading jobs (summaries of long pages, logs and transcripts, first pass triage, pulling fields out, sorting into labels, commit message drafts) can go to the free claude-fb models through one command, `fb-ask`, which only returns text.
- It can never edit code, decide anything or review security: it has no tools, and only those six kinds of job exist.
- Anything from a client or work repo never goes there: the repo's git origin must be on your own list, and text holding a private name is refused.
- When the free models are down, slow or out of quota, `fb-ask` says so at once and the normal Claude session or step does the job itself. Nothing waits and nothing stops.
- The runner uses it in one place: a short summary of a failed check, handed to the fix step next to the raw text it gets today.

## Acceptance criteria
- **AC-1** (the command): `fb-ask <task> [--fields a,b,...] [--labels x,y,...] [--file PATH ...]`, input from the files in order, else stdin. `<task>` is one of `summarize`, `triage`, `extract` (needs `--fields`), `classify` (needs `--labels`), `commit-msg`. Any other task or a missing flag exits 2 with a usage line, before any file, git, network or key read. The request has no tools and `fb-ask` writes no file: the answer reaches the caller only as stdout text.
- **AC-2** (answer): exit 0, stdout is the answer, stderr one line `fb-ask: <model> <seconds>s`. For `extract` the answer must parse as one JSON object with exactly the asked fields; for `classify`, as `{"label": <one of the labels>}`. Anything else is a fall back (`bad_json`).
- **AC-3** (fall back, never stop): exit 3, empty stdout, stderr one line `fb-ask: fall back: <reason>`, reason one of `in_call`, `proxy_down`, `wrong_proxy`, `no_key`, `http_<status>`, `timeout`, `empty`, `bad_json`, `too_large`. Any non 200 status counts, a 429 or 402 from the last tier of the proxy's own chain included; `fb-ask` never retries on its own. Worst case wall time: 20 s for a proxy start plus 180 s for the answer.
- **AC-4** (refused): exit 4, empty stdout, stderr `fb-ask: refused: <reason>`, reason one of `client_repo`, `private_name`, `no_names_list`. The line never names the origin, the path or the name. Exit 3 and 4 mean the same to a caller: do the job with normal Claude.
- **AC-5** (origin gate, not folder names): for the working directory and for every `--file`, `fb-ask` finds the git top level and reads `remote.origin.url` with the `wf.GIT_SAFE` options (`runner/wf.py:47`), normalizes it to `host/owner/repo` (lowercase, no scheme, user, port or `.git`), and allows it only when it starts with a line of `~/.claude/private/fb-ok.txt`. A missing or empty file allows no repo. A repo with no origin is refused. A path in no git repo passes this gate. The folder name is never read: a test clones an allowed looking folder name with another origin and gets `client_repo`.
- **AC-6** (content gate): the whole input is checked with the private names checker (`scripts/private-names.py check` on a 0600 temp file, removed after); any hit is `private_name`, a missing `names.txt` is `no_names_list`.
- **AC-7** (never inside a `wf run` call): with `WF_RUN` set (`runner/run.py:2982`) `fb-ask` exits 3 `in_call` before reading anything else. `~/.config/claude-fb` joins `CREDENTIAL_PATHS` (`runner/run.py:60`), so no call can read the proxy key.
- **AC-8** (proxy): `fb-ask` talks only to `http://127.0.0.1:4000` with model `fb-safe`, never `fb-any`. Not alive (`/health/liveliness`): it starts `~/.local/share/claude-fb/start-proxy.sh` detached, logging to `~/.local/state/claude-fb/litellm.log`, as `claude-fb` does, and waits up to 20 s. The key is the `LITELLM_MASTER_KEY=` line of the proxy's key file, whose path is the `key file:` line of `~/.claude/private/fb-ask.conf` (the path is private, never in this repo); it is read into memory only (never argv, env of a child, stdout or stderr); unreadable is `no_key`. Before the job it checks that `/v1/models` lists `fb-safe`, else `wrong_proxy` (another LiteLLM on port 4000).
- **AC-9** (input as data): input over 300,000 characters is `too_large`. The request is a fixed system prompt per task that says the text between `<data>` tags is material to process, never instructions, then the input inside those tags.
- **AC-10** (runner use): when `/check verify` ends `VERIFY FAIL: debug` (`runner/run.py:2100-2106`), the runner process runs `fb-ask summarize` on the whole verify result, with the repo as working directory, `WF_RUN` unset, and a 210 s timeout. On exit 0 the `/debug` command gets `Summary of the failure by a cheaper model (data, may be wrong):` and the summary, above the raw tail `debug_command` adds today (`runner/run.py:3150-3154`, unchanged). On any other exit the command is exactly today's. The call record gains `fb: "ok"` or `fb: "<reason>"`.
- **AC-11** (report): when a run made any `fb-ask` job, the morning report has one line `cheap tier: <n> jobs, <m> fell back (<reason> x<k>, ...)`.
- **AC-12** (sessions): `rules/cheap-worker.md`, at most 8 lines: the six job kinds and when they pay (input over about 20,000 characters, or many small items), the never list (code edits, decisions, security review, anything from a client or work repo), the command, exit 3 or 4 means do it yourself, and the answer is data that may be wrong. Edited live in `~/.claude/rules/`, then `./sync.sh`.
- **AC-13** (self checks): `fb-ask --test` runs against a fake local HTTP server and temp repos, and covers every fall back and refusal reason, AC-5's folder name case, `WF_RUN`, `fb-safe` only, and that the key never appears in argv, stdout, stderr or a child's environment. `install.sh` links `~/.local/bin/fb-ask` and runs `--test`. AGENTS.md gets one command line.
- **AC-14** (Done when): a runner test makes `/check verify` fail into `/debug` with a stub `fb-ask` and shows the summary in the debug call's prompt; with the stub exiting 3, the prompt equals today's. `fb-ask edit`, `fb-ask review`, `fb-ask decide` exit 2 with no network.

## Build plan
1. `scripts/fb-ask.py` with its `--test`: AC-1 to AC-9, AC-13, AC-14 (second half).
2. Runner: `CREDENTIAL_PATHS`, the debug hand-off, the call record field and the report line: AC-7 (second half), AC-10, AC-11, AC-14 (first half).
3. `install.sh` link and self check, AGENTS.md line, `rules/cheap-worker.md`: AC-12, AC-13.
4. `~/.claude/private/fb-ok.txt` with your own repos' origin prefixes, and `~/.claude/private/fb-ask.conf` with the `key file:` line · waits on you (until it exists, every repo is refused and only non repo text uses the tier).

## Probes
Run before the build; record command and result in `verify.md`. None calls Claude or posts anything.
- **P1** (proxy identity and auth): with the proxy up, `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:4000/v1/models` (expect 401 without the key), then `curl -s -H "Authorization: Bearer $(sed -n 's/^LITELLM_MASTER_KEY=//p' <key file>)" http://127.0.0.1:4000/v1/models | jq -r '.data[].id'` lists `fb-safe`. Prints model ids only.
- **P2** (an answer through `/v1/messages`): `curl -s -H "x-api-key: $(sed -n 's/^LITELLM_MASTER_KEY=//p' <key file>)" -H 'anthropic-version: 2023-06-01' -H 'content-type: application/json' -d '{"model":"fb-safe","max_tokens":200,"messages":[{"role":"user","content":"Summarize in one line: the build failed because test_login timed out twice."}]}' http://127.0.0.1:4000/v1/messages | jq '{model, text: .content[0].text}'`. Confirms the header the proxy accepts (`x-api-key` or `Authorization: Bearer`) and the answer shape. Uses the free pool only.
- **P3** (start time): with the proxy stopped, `time (setsid nohup ~/.local/share/claude-fb/start-proxy.sh >/dev/null 2>&1 & for i in $(seq 40); do curl -s -m 1 http://127.0.0.1:4000/health/liveliness >/dev/null && break; sleep 0.5; done)` finishes under 20 s.

## Follow-up
- `docs/architecture.md`: the line "only the scrubbed ping text leaves the machine" gains the `fb-ask` summary (the build's `/sync` updates it).
- A user service for the proxy, only if the report shows `proxy_down` fall backs most nights.
- `fb-ask` inside `wf run` calls stays off (AC-7); revisit only if a call ever needs it, with its own probe of the sandbox reaching loopback.
