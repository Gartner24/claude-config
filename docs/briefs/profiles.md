# Profiles: brief and handover memory
**Feature:** profiles
**Updated:** 2026-10-29 19:20 by 56988615

## Open questions
- Q1 | done | 2026-10-27 | AC-22: remotion-dev/skills has no license (no LICENSE file, GitHub reports none). Install the 12 Remotion skills anyway, | claude 56988615 "if something actually needs my answer wait till Im back" | owner 2026-10-29: install anyway; landed: tools/config/manifest.json
- Q2 | done | 2026-10-27 | Merging #239, #241, #243, #244: the self merge checklist needs the feature's verify and test boxes ticked, and those cov | claude 56988615 "if something actually needs my answer wait till Im back" | owner 2026-10-29: merge now; #239 #241 #244 merged, #243 next

## Shown to the owner, still needed
- none

## Agreed so far, do not ask again
- D1 | done | 2026-10-27 | Skills are shared core; a profile changes only the active skill set (what triggers or is always on) | owner session_ "the skills part is shared, thats part of the core of claude-config" | landed: docs/specs/0081-profiles/index.md
- D2 | done | 2026-10-27 | The design pipeline is shared core | owner session_ "the design pipeline, can be shared too I thjink thats part of the core of claude-config too" | landed: docs/specs/0081-profiles/index.md
- D3 | done | 2026-10-27 | Owner-only parts stay in claude-config, separated into named profiles | owner session_ "there are some mine only but that still are part of claude-config, just separated on different named profiles" | landed: docs/specs/0081-profiles/index.md
- D4 | done | 2026-10-27 | Quality bar is the same in every profile; a profile changes how much the owner is asked | owner session_ "Quality bar: Yes!" | landed: docs/specs/0081-profiles/index.md
- D5 | done | 2026-10-27 | The partner's existing ask-less configs get adapted to the same quality bar and wired in when they arrive | owner session_ "he already has a lot of configurations for that, when we get them we need just to adapt them with his same quallity but wire it to claude-config" | landed: docs/specs/0081-profiles/index.md (PR D)
- D6 | done | 2026-10-27 | Video-only profile part is built later, when the partner's configs arrive | owner session_ "I do want still that part, but I will activate it when it is here" | landed: docs/specs/0081-profiles/index.md (PR D)
- D7 | done | 2026-10-27 | Updates go through the existing /claude-config skill | owner session_ "needs a simple way to update, meaby with the existing claude-config skill" | landed: docs/specs/0081-profiles/index.md
- D8 | done | 2026-10-27 | An update touches only the installing person's own profile | owner session_ "the things that get updated for me are the ones for my profile" | landed: docs/specs/0081-profiles/index.md
- D9 | done | 2026-10-27 | Profiles are a standard that works for anyone, not partner-specific | owner session_ "we need to standarize this then and make it work for anyone" | landed: docs/specs/0081-profiles/index.md
- D10 | done | 2026-10-27 | Profile can be switched on the same machine, e.g. a chip-profile | owner session_ "about when I want to make videos I will change it lets say with chip-profile" | landed: docs/specs/0081-profiles/index.md
- D11 | done | 2026-10-27 | claude-config must work on macOS and Linux | owner session_ "He is ussing mac we need to make claude-config work for mac and linux too" | landed: docs/specs/0082-mac-support.md
- D12 | done | 2026-10-27 | The partner is a collaborator on the same claude-config repo and will change skills | owner session_ "he will also change skills, we will share the repo he will be a collaborator on it" | landed: docs/specs/0081-profiles/index.md
- D13 | done | 2026-10-27 | A profile limits what its user may edit: core engineering skills and configs are locked; design skills and rules of thei | owner session_ "that profile shouldnt be able to edit really important skills or configurations within claude, but he can edit design skills and things like that, or rules that" | landed: docs/specs/0081-profiles/index.md
- D14 | done | 2026-10-27 | Editing a rule of a profile never changes that profile; it creates a new custom-profile-[id] with a custom name | owner session_ "he wont edit his profile it will create automatically a custom-profile-[id], this way we can have custom profiles with a custom profile name and dont destroy ex" | landed: docs/specs/0081-profiles/index.md
- D15 | done | 2026-10-27 | claude-fb and its fb-ask config are shared in the repo (PR 233); the two claude-fb keys.env entries left names.txt; pack | owner session_ "fb-ask.conf, fb-ok.txt - this could be on claude-config, including claude-fb no problem on sharing that" | landed: tools/claude-fb/ (PR 233)
- D16 | done | 2026-10-27 | Repo wins for profile built files; install first lists what it would overwrite or lose, then fixes it or asks | owner session_ "Priority repo, if live will be overwritten check what is gonna get overwritten check what's gonna get missing and fix it or ask to fix it" | landed: docs/specs/0081-profiles/index.md
- D17 | done | 2026-10-27 | The first two profiles are engineer and creator | owner session_ "engineer and creator (Recommended)" | landed: docs/specs/0081-profiles/index.md
- D18 | done | 2026-10-27 | Lock the core with both a Claude hook and GitHub code owners | owner session_ "Hook and GitHub (Recommended)" | landed: docs/specs/0081-profiles/index.md
- D19 | done | 2026-10-27 | creator may edit the design and content skills, the taste patches and its own custom profiles, not design-gate | owner session_ "List minus design-gate (Recommended)" | landed: docs/specs/0081-profiles/index.md
- D20 | done | 2026-10-27 | Only non owner profiles get a custom-<name> copy on a rule edit; engineer is edited directly | owner session_ "Non-owner profiles only (Recommended)" | landed: docs/specs/0081-profiles/index.md
- D21 | done | 2026-10-27 | Switch with /claude-config profile <name>; the band shows the active profile | owner session_ "/claude-config profile (Recommended)" | landed: docs/specs/0081-profiles/index.md
- D22 | done | 2026-10-27 | creator asks the same questions as engineer until the partner's configs arrive | owner session_ "Wait for his configs" | landed: docs/specs/0081-profiles/index.md
- D23 | done | 2026-10-27 | Profile data model approved: name, description, owner, base, skills, rules, hooks_off, editable | owner session_ "It matches (Recommended)" | landed: docs/specs/0081-profiles/index.md
- D24 | done | 2026-10-27 | Cross check fixes applied to spec 0081; custom profiles are created automatically by Claude, which proposes the name | owner session_ "Automatic (Recommended); Apply all (Recommended)" | landed: docs/specs/0081-profiles/index.md
- D25 | done | 2026-10-27 | Mac support: portable code (no GNU tools required) proven by a macOS and Linux GitHub Actions job on every PR | owner session_ "Portable code (Recommended); Mac CI job (Recommended)" | landed: docs/specs/0082-mac-support.md
- D26 | done | 2026-10-27 | Mac CI job lands first as advisory, becomes required after the last fix; all 11 cross check fixes applied to spec 0082 | owner session_ "First, advisory (Recommended); Apply all (Recommended)" | landed: docs/specs/0082-mac-support.md
- D27 | done | 2026-10-27 | Creator turns off the ASCII rule and changes /scope and /audit behavior with a creator rule overlay that beats CLAUDE.md | owner daea8db3 "Rule overlay, but I think scope and audit is really important, so would be like still ussing them but stopping or changing their behavours" | landed: docs/specs/0081-profiles/index.md (PR D)
- D28 | done | 2026-10-27 | In creator, /scope and /audit still auto-start each chat but stay quiet: one plain next step, ask only real decisions | owner daea8db3 "Start, but quiet (Recommended)" | landed: docs/specs/0081-profiles/index.md (PR D)
- D29 | done | 2026-10-27 | Partner's private parts (his studio repo, work rules, memory, registry, work-guard and install-guard) live in his own ~ | owner daea8db3 "His private layer (Recommended)" | landed: docs/specs/0081-profiles/index.md (PR D)
- D30 | done | 2026-10-27 | Profiles gain an optional settings field (env, model, enabledPlugins, extraKnownMarketplaces) merged before the private  | owner daea8db3 "New profile field (Recommended); It matches (Recommended)" | landed: docs/specs/0081-profiles/index.md (PR D)
- D31 | done | 2026-10-27 | careful-worker and mechanical-worker join the core agents (web-researcher dropped); his model routing rule loads only in | owner daea8db3 "Agents core, rule creator (Recommended)" | landed: docs/specs/0081-profiles/index.md (PR D)
- D32 | open | 2026-10-29 | GitHub branch rule (AC-15) waits: turn it on the day the partner gets push access to claude-config. | owner 56988615 "Later (Recommended)" | -

## Live state
- L1 | open | 2026-10-27 | Partner zip received 2026-10-27 (extracted to the job tmp, not in the repo); our watch | claude daea8db3 "we recieved the setup from my partner" | -
