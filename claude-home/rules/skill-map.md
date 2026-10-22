# Skill map (which skill, when, what it costs, who starts it)

Pick by the situation, not by habit.
Costs are rough, on the subscription. Anything marked "ask" needs the user's yes first.

"Starts by" (spec 0070): **mod start** is the wf-handoff mod running the skill when a chat opens in a
git repo; **catch** is `hooks/chain-catch.py`, which refuses to end a turn while the step is owed
(at most 3 times per turn); **session** is you, from the rules.

| Situation | Skill | Cost | Who starts it | Starts by |
|---|---|---|---|---|
| Session start in a repo, or plan / replan / enroll a feature | `/scope` | low | session | mod start at chat open; a reminder on every message to run `/scope <item>` for new work; catch: an edited file no spec names |
| Repo has no AGENTS.md | `/audit` | low | session | mod start at chat open (never in bot-reviewed repos), then `/scope` |
| A load bearing choice is unmade (stack, data model, provider, behavior, page design) | `/architect` | medium | session | catch: a row this chat tagged `· needs a decision`; else the feature's next box |
| Spec accepted and nothing left to decide | build handoff: `/rollover`, or one worktree agent per feature | low | session | catch: the accepted spec, released by `/rollover`, `/handoff`, a worktree agent or "do it here" |
| Build a scoped feature or fix | `/develop` | medium to high | session | catch: the feature's next box, when this chat edited a file its spec names |
| Prove it works against the spec | `/check verify` | medium | session | catch: the feature's next box |
| Lock it with tests | `/test` | medium | session | catch: the feature's next box |
| Bug, failing test, verify FAIL | `/debug` | medium | session | catch: the turn's last test run failed |
| After a change lands: AGENTS.md, scope, stale specs | `/sync` | low | session | catch: the feature's next box |
| Docs, PR text | `/document` (`/document pr`) | low | session | catch: the feature's next box |
| Other prose: commits, issues, READMEs | `/write`, then `/polish` | low | session | session |
| Quick bug check of a small own diff (under ~200 lines, no risk path) | `/code-review` | low | session | session |
| Default review before landing, own and freelance repos | `/review` (jjstack) | medium | session, never in bot-reviewed repos | session |
| Risk path (auth, permissions, sandbox, payments, migrations), someone else's PR, or a framing you distrust | `/review-stack` | high | session; in bot-reviewed repos only when asked | session |
| Same, but the blind lane must not share any memory | `/review-stack sealed` | 5 to 19 USD a run | ask, never on your own | session |
| Security only pass | `/jj-security-review` (jjstack) or `/security-review` (built in) | medium | session | session |
| Deep multi-agent cloud review | `/code-review ultra` | billed | the user types it | session |
| New UI, redesign, restyle, polish | `design` (runs `design-gate` itself) | high | session | session |
| Audit a built UI | `design-gate` | medium | session | session |
| Images, icons, logos | `assets` | low; image generation bills | session, ask before generating | session |
| A client's brand system | `brand-system` | medium | session | session |
| Research with sources | `/deep-research` | high | ask when it is large | session |
| Feature still open, context full | `/rollover` (user types `/clear`, `/resume-from-clear`) | low | session | the wf-handoff mod at the token line |
| Feature closed or switching task | `/save-and-clear` (user types `/clear`) | low | session | session |

Never: `/review` and `/review-stack` over the same diff; `/check review`; anything that pushes, merges, posts or bills without the user.
