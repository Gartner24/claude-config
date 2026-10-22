# 0072 rationale

## Context
claude-config grew without a skeleton: an 86 line `AGENTS.md` and a 1391 line plan load in every chat, the retired runner still sits beside live code, and its test folder is also the suite for live scripts. The owner wants the repo in the ICM layout (icm-architect, arXiv 2603.16021) without losing quality. Many paths are load bearing: 27 links in `~/.claude`, 3 in `~/.local/bin`, `settings.json`, every JSM skill's `docs/specs/` and `docs/scope/`. Research and the skill's own read only run are in [icm-research.md](../../briefs/icm-research.md) sections 1 to 6; the owner's answers are in [icm-restructure.md](../../briefs/icm-restructure.md).

## Options considered
### Option 1: Map only
Add `map/` and shorten the entry file, move nothing. Pros: smallest, no breakage. Cons: the 28k plan file and the dead runner stay.

### Option 2: Map plus safe moves, phase 2 after review (chosen)
Do the skill's safe moves now, prove nothing broke, then design the whole restructure. Pros: the ICM gain where it is safe, each PR small. Cons: about 3 PRs now and a second design later.

### Option 3: Whole restructure at once
Numbered ICM folders everywhere. Pros: pure ICM. Cons: breaks the held paths, and ICM's own restructure mode forbids moving a file with a live referrer unless every referrer changes in the same commit.

## Rationale
The owner chose a whole restructure in two phases. Phase 1 is exactly the set the skill's reference integrity step found safe, so it can land without touching any outside consumer. Phase 2 then gets a migration map built from phase 1's reference check, which turns "nothing broke" from a review opinion into a script result. The owner asked to keep review usage low, so the check is a script plus one regression agent, not a review stack.

`CLAUDE.md` as the source is the owner's pick, following ICM's system map text. The probe in verify.md showed the file tools keep a symlink but `sed -i` breaks it, so the commit check is what brings drift risk to zero.

## Evidence
- icm-architect run, migration map and blockers: icm-research.md section 6.
- Symlink probe: [verify.md](verify.md).
