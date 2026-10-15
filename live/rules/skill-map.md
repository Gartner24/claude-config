# Skill map (which skill, when, what it costs, who starts it)

Pick by the situation, not by habit. "wf" = may run inside an unattended `wf run` call.
Costs are rough, on the subscription. Anything marked "ask" needs the user's yes first.

| Situation | Skill | Cost | Who starts it |
|---|---|---|---|
| Session start in a repo, or plan / replan / enroll a feature | `/scope` | low | session |
| Repo has no AGENTS.md | `/audit` | low | session |
| A load bearing choice is unmade (stack, data model, provider, behavior, page design) | `/architect` | medium | session, never wf |
| Build a scoped feature or fix | `/develop` | medium to high | session, wf |
| Prove it works against the spec | `/check verify` | medium | session, wf |
| Lock it with tests | `/test` | medium | session, wf |
| Bug, failing test, verify FAIL | `/debug` | medium | session, wf |
| After a change lands: AGENTS.md, scope, stale specs | `/sync` | low | session, wf (final call) |
| Docs, PR text | `/document` (`/document pr`) | low | session, wf |
| Other prose: commits, issues, READMEs | `/write`, then `/polish` | low | session |
| Quick bug check of a small own diff (under ~200 lines, no risk path) | `/code-review` | low | session |
| Default review before landing, own and freelance repos | `/review` (jjstack) | medium | session, never in bot-reviewed repos |
| Risk path (auth, permissions, sandbox, payments, migrations), someone else's PR, or a framing you distrust | `/review-stack` | high | session; in bot-reviewed repos only when asked |
| Same, but the blind lane must not share any memory | `/review-stack sealed` | 5 to 19 USD a run | ask, never on your own |
| Security only pass | `/jj-security-review` (jjstack) or `/security-review` (built in) | medium | session |
| Deep multi-agent cloud review | `/code-review ultra` | billed | the user types it |
| New UI, redesign, restyle, polish | `design` (runs `design-gate` itself) | high | session, never wf |
| Audit a built UI | `design-gate` | medium | session, wf only through `/check verify` |
| Images, icons, logos | `assets` | low; image generation bills | session, ask before generating |
| A client's brand system | `brand-system` | medium | session |
| Research with sources | `/deep-research` | high | ask when it is large |
| Feature still open, context full | `/rollover` (user types `/clear`, `/resume-from-clear`) | low | session |
| Feature closed or switching task | `/save-and-clear` (user types `/clear`) | low | session |

Never: `/review` and `/review-stack` over the same diff; `/check review`; anything that pushes, merges, posts or bills without the user. `wf run` refuses every command not marked wf above.
