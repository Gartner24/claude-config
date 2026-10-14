# 0023. Cheap worker tier (rationale)

## Context

Scope feature 15: low value work goes to the free claude-fb models and comes back as data; never code edits, decisions, security review or client code. Brief: [docs/briefs/finish-runner-today.md](../../briefs/finish-runner-today.md) item 12.

What exists today:
- `claude-fb` (a shell function in the dotfiles repo) runs Claude Code through a local LiteLLM proxy on `127.0.0.1:4000`. It starts the proxy with `~/.local/share/claude-fb/start-proxy.sh` when `/health/liveliness` does not answer, and authenticates with `LITELLM_MASTER_KEY` from its key file (a private path, so `fb-ask` reads it from `~/.claude/private/fb-ask.conf`). The proxy speaks the Anthropic `/v1/messages` API.
- Model groups: `fb-safe` (Ollama Cloud, then Groq; neither trains on prompts) and `fb-any` (adds Gemini free and Mistral free, which may train on or review prompts).
- Another project's Docker stack can run its own LiteLLM on the same port, so "something answers on 4000" does not mean it is claude-fb's proxy.
- A `wf run` call's environment loses every `*_KEY`, `*_TOKEN` and similar (`runner/run.py:57-68`, `2976-2983`), its sandbox denies forge hosts (`runner/run.py:69`, `1044`) and reads of `CREDENTIAL_PATHS` (`runner/run.py:60-63`, `1049`). `~/.config/claude-fb` is not in that list; only the user's permission rules deny the Read tool on the key file, and `user_read_denies()` feeds those only to the app jail (`runner/run.py:1081`), not to the calls' sandbox.
- The runner hands a failed verify to `/debug` as the last 1,500 characters of the verify result (`runner/run.py:3150-3154`, called at `2106`).
- The private names checker (`scripts/private-names.py check <paths>`, spec 0013) exits 1 on a hit and never prints the name.

## Options considered

### Where the runner uses it
1. **The runner process itself, for its own text jobs (chosen).** No key or proxy port inside a call, and the sandbox needs no change. One concrete use: the failure summary for `/debug`.
2. Inside `wf run` calls through Bash. Needs the sandbox to reach loopback port 4000 and the key readable inside the call, which undoes spec 0008 AC-7's "no secret reaches a call". Rejected.
3. Both. Rejected for the reason in 2.

### How it fails over to normal Claude
1. **`fb-ask` exits 3 at once and the caller does the job itself (chosen).** The caller is already Claude (a session, or a step's call), so "normal Claude" is free and needs no second path. In the runner, the fall back is today's behavior exactly.
2. `fb-ask` calls `claude -p --model haiku` itself. A second model call path with its own limits, env and guard; it spends subscription usage the caller would spend anyway.
3. Retry with backoff inside `fb-ask`. LiteLLM already falls through its tiers; extra waiting is what "never stop" forbids.

### How "never for client or work code" is enforced
1. **An allow list of origin prefixes in `~/.claude/private/fb-ok.txt`, fail closed, plus the private names check on the content (chosen).** A freelance client repo can live under your own account, so a block list by org misses it; an allow list only lets through what you named. The content check catches client text that arrives from outside any repo (a log pasted in a non repo folder).
2. A block list of orgs (the bot reviewed orgs in `~/.claude/private/work.md`). Fails open for every client repo not listed.
3. Folder names (`~/projects/work/...`). Ruled out by the feature: a clone can live anywhere.

## Decided without asking (2026-10-13)
Per the brief, the recommended option was taken for every question.

| Question | Options | Pick |
|---|---|---|
| Where does a runner step call it? | runner process only; inside calls; both | Runner process only. Calls get `WF_RUN` and fall back `in_call`; the key folder is hidden from calls. |
| Which runner job? | debug hand-off summary; phone question detail; morning report digest | Debug hand-off only: it is the one place where a long text is cut to 1,500 characters today, and it meets the Done when. Others later if it proves useful. |
| Fail over how? | caller does it itself (exit 3); `fb-ask` calls Claude Haiku; retry | Caller does it itself. |
| Which model group? | `fb-safe` only; `fb-any` allowed for non repo text | `fb-safe` only. `fb-any` providers may train on prompts. |
| Client rule by what? | origin allow list plus content names check; org block list; folder names | Origin allow list (fail closed) plus content check. |
| A repo with no origin? | refuse; allow | Refuse (a local client clone has none). |
| Text outside any repo? | allow (content check still runs); refuse | Allow, so page and transcript summaries work from any folder. |
| Who starts the proxy? | `fb-ask` with the existing start script; never, fall back; a user service | `fb-ask`, outside calls, with `start-proxy.sh`, as `claude-fb` does. A service only if the report shows it is needed. |
| Where does `fb-ask` learn the key file's path? | a `key file:` line in `~/.claude/private/fb-ask.conf`; hardcoded; an env var | The private conf: the path is on the private names list, so it cannot be in this public repo, and an env var would reach child processes. Missing conf is `no_key`. |
| Output shape? | plain text, JSON only for extract and classify; JSON always | Plain text, so a session reads it directly; JSON where the job is structured. |
| Input size cap? | 300,000 characters; chunking | Cap, fall back `too_large`; the caller can split. Chunking is speculative. |
| Fall back and refusal exit codes? | one code; two codes | Two (3 fall back, 4 refused), so the report can tell an outage from a gate. |
| How do sessions learn it? | an always loaded rule of at most 8 lines; a skill; nothing | Rule. A skill is not loaded when the job comes up mid task. |

## Risks
- A cheaper model's summary can be wrong. The debug call always gets the raw tail too, and the summary is labeled.
- The free Ollama pool is one monthly pool; when it runs out, Groq takes over through the proxy, and after that every job falls back. That costs subscription usage, not a stop.
- The allow list is only as good as what you put in it. It starts empty, which sends nothing from any repo.
