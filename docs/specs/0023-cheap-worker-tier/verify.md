# Verify: cheap worker tier · spec 0023

Run 2026-10-14 by `/check verify cheap worker tier` (inside a `wf run` call, so `WF_RUN` is set; steps that need it off use `env -u WF_RUN`). Rerun the same day after fix 6c5c324 (files under a client repo's `.git/`): every step below passed.
## Commands
- [x] `python3 -B scripts/fb-ask.py --test` -> `fb-ask: all self checks passed` -> AC-1 to AC-9, AC-13, AC-14
  can fail: any gate or fall back reason stops matching its exit code or stderr line.
- [x] `python3 -B -m unittest discover -s runner/tests -p test_cheap.py -v` -> 6 tests OK -> AC-7, AC-10, AC-11, AC-14
  can fail: the debug prompt drops the summary, or keeps it after a fall back, or the report line is missing.
- [x] `fb-ask edit`, `fb-ask review`, `fb-ask decide` -> each exit 2, empty stdout, usage line naming the five tasks -> AC-1, AC-14
  can fail: an unknown task reaches the gates or the network.
- [x] `env WF_RUN=1 fb-ask summarize --file AGENTS.md` -> exit 3, `fb-ask: fall back: in_call` -> AC-7
  can fail: the `WF_RUN` check runs after the file or key read.
- [x] scratch repo named `claude-config` with origin `github.com/someclient/claude-config`, `env -u WF_RUN -C <it> fb-ask summarize --file AGENTS.md` -> exit 4, `fb-ask: refused: client_repo`, no origin printed -> AC-4, AC-5
  can fail: the gate reads the folder name instead of the origin.
- [x] `env -u WF_RUN -C ~/claude-config fb-ask summarize --file <client repo>/notes.md` -> exit 4 `client_repo` -> AC-5
  can fail: only the working directory is checked, not each `--file`.
- [x] `env -u WF_RUN -C <plain dir> fb-ask commit-msg --file <client repo>/.git/COMMIT_EDITMSG` -> exit 4 `client_repo`; and with `<client repo>/.git` as working directory -> exit 4 `client_repo` -> AC-5
  can fail: `origin_ok` (`scripts/fb-ask.py:121-133`) finds no work tree inside `.git/` and treats the file as "in no repo" (it did before 6c5c324: exit 3 `no_key`).
- [x] `env -u WF_RUN -C ~/claude-config fb-ask summarize --file AGENTS.md` -> exit 3 `no_key` (origin and names gates passed with the real `fb-ok.txt`; the key file sits in `~/.config/claude-fb`, which this session's sandbox hides) -> AC-5, AC-8
  can fail: the real `fb-ok.txt` line does not match this repo's origin, giving `client_repo`.
- [x] `env -u WF_RUN -C <plain dir> fb-ask summarize --file ~/.claude/private/names.txt` -> exit 4 `fb-ask: refused: private_name`, no name printed -> AC-6
  can fail: the names checker is skipped or its hit line is echoed.
- [x] 300,001 character file -> exit 3 `fb-ask: fall back: too_large` -> AC-9
  can fail: the size limit is checked after the request.
- [x] own fake proxy driver (`fb-ask.py` loaded, only `PROXY` patched, temp live dir) -> `summarize` and `extract --fields a,b` exit 0, stdout the answer (`{"a": "1", "b": "2"}` for extract), stderr `fb-ask: fake/m 0.0s`, request model `fb-safe`, no `tools`, input inside `<data>` with an inner `</data>` defused (one closing tag), key in no output; calls go liveliness, `/v1/models`, `/v1/messages`. With no `names.txt` in the live dir -> exit 4 `no_names_list` -> AC-2, AC-4, AC-6, AC-8, AC-9
  can fail: the answer shape, model, data wrapping or key handling changes.
- [x] `ls -l ~/.local/bin/fb-ask` -> link to `scripts/fb-ask.py`; `diff rules/cheap-worker.md ~/.claude/rules/cheap-worker.md` -> same, 7 lines with job kinds, when it pays, the never list, exit 3/4, data may be wrong -> AC-12, AC-13
  can fail: install did not link it, or the live rule drifted from the repo copy.
## Blocked (waits on you)
- Probes P1 to P3 against the real claude-fb proxy: the key file is hidden from this sandbox and the sandbox has its own localhost. They have their own scope box.
## Acceptance-criteria coverage
- AC-1 met · AC-2 met · AC-3 met (self checks) · AC-4 met · AC-5 met (`.git/` case fixed in 6c5c324) · AC-6 met · AC-7 met · AC-8 met on a fake proxy, real proxy blocked (probe box) · AC-9 met · AC-10 met (runner tests) · AC-11 met (runner tests) · AC-12 met · AC-13 met · AC-14 met
- 2026-10-14, done by Claude in the conductor session: fb-ok.txt (claude-config, dotfiles) and fb-ask.conf written. P1: without the key the proxy serves nothing (HTTP 500, not the 401 expected; no model list). P2: `fb-ask summarize` answered through fb-safe in 1.7 s, the key read only inside fb-ask. P3: proxy stopped, then `fb-ask summarize` started it and answered in 4.2 s total (limit 20 s). PASS, with the P1 status note.
