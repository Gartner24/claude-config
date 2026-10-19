# Verify: auto handoff display · spec 0064

Run 2026-10-18 by `/check verify auto handoff display` under `wf run`, Claude Code 2.1.303, branch `feat/0064-auto-handoff-display-band-viewer-pages-link` at ba8fe39 plus the reduced motion fix below.
How: the real `server.py` and `pages.ts` driven outside the test harness (`/tmp` driver, bun and python3, server and client in one sandbox command since each command has its own network); the real wf-handoff mod driven through five handoff scenarios in `claude plugin test` (source kept as [verify-checks.test.ts.txt](verify-checks.test.ts.txt)), its `panel.json` writes dumped and fed into the real wf-dash `handoffLine` the band draws from.

Verdict: PASS. Every AC behavior met; the design gate passes with findings on pass 3 after the owner accepted the link width cut (below).

## Commands
- [x] AC-1 the real mod writes `panel.json` on every phase: two handoffs in a row give `gated: pending pending pending`, `rolling: running ...`, `clearing: done running pending` (session S1), `seeding: done done running` (session S2, previous S1), then `idle: done done done` with result `handed off · 210k -> 95k` and the link; the second handoff the same with `210k -> 96k` under S2 then S3. → AC-1
  can fail: a phase change that writes no panel, or the steps written under the new id before the clear, so the old chat's band never sees them
- [x] AC-2 the real panels through the real band line: `⠹ writing the handover`, `⠹ clearing`, `⠹ starting the fresh chat`, then `[result] handed off · 210k -> 95k · http://127.0.0.1:3846/S1aaaaaa-<16 hex>`; 10 s later `[link] handover: <same link>`; a missing slot gives `[sticky] auto handoff failed: the rollover wrote no new handover; nothing was cleared`, still there after 1 h, gone once dismissed; the pause gives `[sticky] auto handoff paused: type anything to resume`; another chat's band draws nothing. → AC-2
  can fail: the band matching only its own id (the steps before the clear vanish), or a sticky line that expires on a timer
- [x] AC-3 toasts: no wf-dash state gives `auto handoff started: writing the handover` and the failure toast with `timeoutMs 30000`; wf-dash loaded with a `mobile` surface gives start, `handed off · 210k -> 95k · <link>` and the pause at 30 s; wf-dash loaded in the terminal only gives no toast. → AC-3
  can fail: toasts while the band draws, or none on a surface with no band
- [x] AC-4 pages: the first page has `first handover of this chain` and `<a href="<second link>">next handover</a>` added at the second seed; the second has `<a href="<first link>">previous handover</a>`; slot text `<b>finish</b> & ship` renders `&lt;b&gt;finish&lt;/b&gt; &amp; ship`; through the real server a slot line `<script>alert(1)</script> & "q" 's` comes back as `&lt;script&gt;alert(1)&lt;/script&gt; &amp; &quot;q&quot; &#39;s`. → AC-4
  can fail: raw slot HTML in the page, or a chain with no previous or next link
- [x] AC-5 real server: `server.py --bind 127.0.0.1 --port 38461 --token-file ...` prints `serving ... on 127.0.0.1:38461`; `ss -ltn` shows only `127.0.0.1:38461`; the link `/sess0001-aaaaaaaaaaaaaaaa` is 200, a wrong key, a wrong prefix, `/../server.token` and `/server.token` are 404; `--bind 0.0.0.0` and `--bind 192.168.1.5` exit 2 `refused bind`; a second server on the port exits 1 `not free`; `--probe` says `ours` with the token, `foreign` with another token, `none` on a free port; the token file is 0600 and gone after the stop. → AC-5
  can fail: a bind to 0.0.0.0, or a page served for a guessed key
- [x] AC-5 bind rule in the mod: `tailscale ip -4` answering `100.88.1.2` spawns `--bind 100.88.1.2` and links `http://100.88.1.2:3846/...`; no Tailscale spawns `--bind 127.0.0.1`; a blank `viewer` spawns nothing and links `file:///h/.claude/state/auto-handoff/pages/S1aaaaaa-1111.html`. → AC-5
  can fail: the default viewer binding loopback while Tailscale is up, or a server started with a blank viewer
- [x] AC-6 the fresh chat (S2) band shows `handover: <link>`; the slot facts block holds `viewer: <link>`; the chain state holds `link` and `pageKey`. → AC-6
  can fail: the link taken from the consumed slot, so the fresh chat shows none
- [x] Reduced motion (design gate must fix 1, fixed in this step): the spin tick in `claude-home/mods/wf-dash/hooks/register.tsx` skips the frame advance when `$.settings.read()` has `prefersReducedMotion`; test `under reduced motion the spinner keeps its first frame` in `handoff.test.ts`; mutant (the guard forced false) red with expected 0, received 3; restored, 36 pass. `claude plugin validate` passes.
  can fail: the spinner turning under reduced motion
- AC-7 read check, not counted: nothing in the mods installs Tailscale; the only call is `tailscale ip -4`.
- AC-8: both suites pass (wf-handoff 65 plus the 5 verify scenarios, wf-dash 36, `server.py --test`); the scan is left to the box: Install both mods live after their scan.

## Design gate (band, `claude-home/mods/wf-dash`)
- Pass 1 FAIL, 2 must fix; pass 2 FAIL, 1 must fix left: the result line `handed off · 210k -> 95k · <link>` needs 76 cells with the loopback link and about 78 to 82 with a Tailscale link, so under about 83 to 89 columns (and always in the 31 cell docked column) the end of the 16 character key is cut and the printed link opens nothing. The `handover: <link>` line (59 cells) fits at 80. The host offers a clickable link element the line does not use. Report in `claude-home/mods/wf-dash/.design/audit-report.md`.
- 2026-10-19 the owner chose "Keep it, full link shows next": the cut lasts 10 s and the `handover: <link>` line after it shows the full link; no spec change. Pass 3: PASS with findings, 0 must fix open, 4 should fix left for the owner.

## Left to boxes
- The band, spinner, dismiss key and toasts in a real interactive chat, and the shape `$.settings.read()` returns live: left to the box: Install both mods live after their scan
- The page opened from the phone over Tailscale: left to the box: Install Tailscale on this laptop and your phone and log in to both (spec 0064 AC-7)
