# Verify: fb-ask can use the laptop model for private text · spec 0053

The spec is the flat file `../0053-fb-ask-local-model.md`; this folder only holds its verify steps.
First run: 2026-10-17, `/check verify` under `wf run`, result PASS for AC-1 to AC-8; AC-9 left to its box.

How it ran: `python3 -B docs/specs/0053-fb-ask-local-model/probes/verify0053.py` runs the real `fb-ask` CLI
(through the same constant patch wrapper the self checks use) against a fake proxy on a random port that
records every request. A scratch home holds `names.txt` and no `fb-ok.txt`, so both gates refuse without
`--local`; the cwd is a git repo whose origin is a client. Can fail was checked by breaking `scripts/fb-ask.py`
one way at a time (14 mutants, each restored): every step below went red on its mutant.

## Commands
- [x] V1 `fb-ask summarize --local` in the client repo, input holding a private name: exit 0, answer on stdout, request model `fb-local`, stderr `fb-ask: local fb-local 0.0s` -> AC-1, AC-2, AC-6
  can fail: model left at `fb-safe`, either gate kept with `--local`, or the stderr name taken from the reply (all seen red)
- [x] V2 that request carries `max_tokens` 1024 (summarize) -> AC-5
  can fail: a gate kept with `--local` stops the request (seen red)
- [x] V3 same call without `--local`: exit 4 `fb-ask: refused: client_repo`, zero requests -> AC-2
  can fail: origin gate off in cloud mode (seen red)
- [x] V4 private name, no repo, without `--local`: exit 4 `fb-ask: refused: private_name`, name not printed -> AC-2
  can fail: names gate off in cloud mode (seen red)
- [x] V5 `extract --fields job --local`: model `fb-local`, `max_tokens` 512 -> AC-1, AC-5
  can fail: model left at `fb-safe` (seen red)
- [x] V6 proxy listing only `fb-safe` and `fb-any`, `--local`: exit 3 `fall back: wrong_proxy`, zero POST requests (so never `fb-safe`) -> AC-4
  can fail: `fb-safe` accepted when `fb-local` is missing (seen red)
- [x] V7 `--local` with 30,000 characters answers; 30,001 gives `fall back: too_large` with no request -> AC-5
  can fail: the cloud 300,000 cap used locally (seen red)
- [x] V8 reply `usage.input_tokens` 15,500 and missing usage both give `fall back: truncated` and empty stdout; 15,499 answers -> AC-5b
  can fail: truncation check removed (seen red)
- [x] V9 reply slower than `LOCAL_WAIT=1` with `ANSWER_WAIT=30`: `fall back: timeout` -> AC-5
  can fail: `ANSWER_WAIT` used locally (seen red)
- [x] V10 `WF_RUN=r9` with `--local`: `fall back: in_call`, zero GET requests -> AC-3
  can fail: `WF_RUN` check removed (seen red)
- [x] V11 the runner's own `run.repo_lock` holds the lock of an `active.json` entry's tree: the runner's `auto.entry_running` says True and `fb-ask --local` gives `fall back: wf_building`, zero requests -> AC-3
  can fail: build check removed (seen red)
- [x] V12 same held lock, without `--local`: reaches the origin gate (`refused: client_repo`), so cloud mode does not check builds -> AC-3
  can fail: build check run in cloud mode too (seen red)
- [x] V13 lock released (crashed run left a free lock file): `--local` answers again -> AC-3
  can fail: a free lock counted as a build (seen red)
- [x] `python3 -B scripts/fb-ask.py --test`: `fb-ask: all self checks passed`, including the spec 0053 cases -> AC-7
  Not counted as can fail here; mutation checks of these self checks belong to `/test`.
- [x] `claude-home/rules/cheap-worker.md` is 8 lines and says: client or work text only with `--local`, about 2 minutes cold, about 6 words a second, under about 30,000 characters, 600000 ms tool timeout or background, never during a wf build; `AGENTS.md:29` shows `fb-ask <task> [--local]` -> AC-8
  Read check only, not counted as can fail.
- [ ] P1 and P2 live probes on the real `fb-local` model -> AC-9
  left to the box: Live probes P1 and P2, never while wf builds (AC-9). The sandbox cannot read `~/.config/claude-fb` (the key) and has its own localhost, so the real proxy on port 4000 is unreachable from here.

## Acceptance criteria coverage
- AC-1 met · AC-2 met · AC-3 met · AC-4 met · AC-5 met · AC-5b met · AC-6 met · AC-7 met (self checks green) · AC-8 met · AC-9 left to its box

# Spec 0053 AC-9 live probes (2026-10-18)

Script: /home/santiago/.local/share/wf-trees/claude-config-5f0728/feat-0053-local-model-on-the-laptop/scripts/fb-ask.py
Stack: LiteLLM :4000 alive, Ollama :11434 up (qwen2.5-coder:14b), config ~/.config/claude-fb/litellm.yaml (unchanged).

- [ ] P1 FAIL: summarize --local on a 28,902 char log, fact "deploy id ZK-4471 failed at 03:12" in lines 1-2
  - Command: `python3 scripts/fb-ask.py summarize --local --file /tmp/claude-1000/-home-santiago--claude/7692240f-4247-4b06-ac42-86d1193f0505/scratchpad/p0053/log.txt`
  - Run 1: ok, 404.4s (near LOCAL_WAIT 420), answer was a JSON dump of noise lines, no ZK-4471.
  - Run 2: ok, 182.4s, answer is a generic "breakdown of log components", `grep -c ZK-4471` = 0 (p1-answer.txt in scratchpad p0053/).
  - Both runs passed the truncation check (input_tokens < 15,500), so no `fall back: truncated`.
  - Finding: the call path works and no gate fires, but the 14B model at 16k context loses a fact in the first 2 lines of a ~29k char noisy log; the answer does not contain it.
  - can fail: yes, if the model drops the planted line the grep finds 0 matches (it did).

- [x] P2 PASS (no change needed): timed-out local call, then an immediate second call
  - Call 1: copy of fb-ask.py with `LOCAL_WAIT = 5` (the code has no env/flag for it; copy at scratchpad p0053/fb-ask-short.py), `summarize --local --file small.txt`, cold model: exit 3, `fb-ask: fall back: timeout`.
  - Call 2 (immediately, real script): `fb-ask: local fb-local 13.1s`, a correct answer. LiteLLM cooldown did not block it. `grep -ci cooldown ~/.local/state/claude-fb/litellm.log` = 0.
  - Cause of no block: the kill is a client disconnect, which LiteLLM does not count as a deployment failure, so num_retries/allowed_fails/cooldown_time 1800 never engaged.
  - Per spec no litellm.yaml change made (neither worktree nor live). Worktree has no litellm.yaml of its own; live one is ~/.config/claude-fb/litellm.yaml.
  - can fail: yes, if cooldown applied, call 2 would be `http_429/500` or `wrong_proxy` instead of an answer.
  - Not covered: a LiteLLM-side timeout/5xx (Ollama error) was not provoked.

- [x] P1 rerun on a real log. PASS.
  Command: the planted line `2026-10-18T03:12:00-05:00 deploy id ZK-4471 failed at 03:12` followed by real wf run logs (`~/.local/state/wf/runs/*/log.txt`), cut to 28,297 characters; `python3 scripts/fb-ask.py summarize --local --file <log>` from the feature branch.
  Result: exit 0, `fb-ask: local fb-local 227.6s`; the answer opens with "The deployment ID ZK-4471 failed at 03:12." (`grep -c ZK-4471` 1), then summarizes the runs.
  Reading: the first P1 run used a log of repeated random filler, which the model summarized as noise and lost the fact twice; on a real log, the case this mode is for, it keeps it. A call takes 3 to 7 minutes cold on this laptop, so `--local` suits background jobs, not interactive ones.
  can fail: the answer without ZK-4471, or the call past its 420 s limit
