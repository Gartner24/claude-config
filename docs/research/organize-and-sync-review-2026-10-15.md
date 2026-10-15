# Is spec 0048 the right way? Research report
*Generated: 2026-10-15 | Sources: about 25 opened | Confidence: Medium (strong on Claude Code docs and licensing, thin on real world examples)*

## Executive summary
Spec 0048 has the right shape. The `claude-home/` mirror, the thin top level, a manifest with source and pinned commit, and AGENTS.md for AI with README for people all match established practice (Chromium's third party metadata, GNU Stow, the agents.md convention, Claude Code memory docs). Three parts should change. Copying untraceable skills into a public repo is a licensing problem, because no license means all rights reserved. Detached full copies of edited skills are weaker than a pinned upstream plus a patch. And the docs rewrite should shrink AI facing text, not just regroup it. The spec also misses the biggest cheap optimization: 77 skills still put full descriptions into every session, above Anthropic's 30 to 50 tool guidance.

## 1. What tools already exist
- **Claude Code plugin marketplaces** can be private git repos or local folders. A plugin bundles skills, commands, agents, hooks (in `hooks.json`), MCP and settings, and pins by `ref` or full commit `sha`. Updates are `claude plugin update`. No feature merges user edits into an upstream update; the cache copy is not durable. Plugin skills are namespaced (`plugin:skill`), which renames slash commands. (https://code.claude.com/docs/en/plugins/marketplace-reference, https://code.claude.com/docs/en/plugins/loading, https://code.claude.com/docs/en/plugins-reference)
- **skills CLI** (`npx skills`): add, list, find, remove, update, init. Its lock file records a content hash, not a commit, and `update` goes to latest. Local edit handling is not documented. Only 10 of your skills are in it. (https://github.com/vercel-labs/skills, local `~/.agents/.skill-lock.json`)
- **chezmoi externals**: git repo externals are a plain pull with no documented pinning, and chezmoi cannot manage other files in that directory. No local patch layer. (https://www.chezmoi.io/reference/special-files/chezmoiexternal-format/, https://www.chezmoi.io/user-guide/include-files-from-elsewhere/)
- **vendir**: pins git refs in a lock file, but sync overwrites directories, with no patch or merge. (https://carvel.dev/vendir/docs/v0.46.x/vendir-spec/)
- **Real examples** (thin): people either vendor their whole `~/.claude` in git (a Stow package) or keep only their own skills. Nobody found runs a manifest plus merge tool. (https://www.yurikoval.com/blog/manage-ai-config-with-dotfiles.html, https://github.com/manzt/dotfiles/tree/main/.claude/skills)

**So:** no existing tool covers "pinned third party folder plus my edits, merged on update". A custom tool is justified, but the merge part can be much smaller than the spec draws.

## 2. Vendoring and patches
- Chromium prefers a pinned upstream revision over a snapshot. Its metadata file (URL, revision, license, update mechanism) is the model the manifest already follows. A diverged copy is labelled `Static.HardFork`, "no longer updatable", and needs an exception. (https://chromium.googlesource.com/chromium/src/+/main/docs/adding_to_third_party.md)
- patch-package and Debian quilt keep the upstream pinned and your edits as a patch, which warns loudly when upstream moves under it. (https://github.com/ds300/patch-package, https://www.debian.org/doc/manuals/maint-guide/modify.en.html)
- **Inference for skills:** store the pin plus a `.patch` of your edits. On update, apply the patch to the new upstream. If it applies cleanly you are done, and if not, `git merge-file` shows the conflict. That is the same outcome as the spec's take or keep for each hunk, with far less code.

## 3. Licensing (the real risk in the spec)
- No license means all rights reserved: nobody may reproduce or distribute it. (https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository, https://choosealicense.com/no-permission/)
- MIT requires the notice in every copy. Apache 2.0 requires the license, a NOTICE carry over, and "prominent notices" on changed files. (https://choosealicense.com/licenses/mit/, https://www.apache.org/licenses/LICENSE-2.0.txt)
- **Consequence:** the spec's "not found, copy into the public repo marked source unknown" republishes files with no license evidence. Those belong in a private place. Edited MIT or Apache skills may go public with their LICENSE beside them and a changed file note.

## 4. Layout and docs
- A path for path mirror is the Stow model, and it is sound. (https://www.gnu.org/software/stow/manual/stow.html)
- Claude Code docs: CLAUDE.md under about 200 lines, "Longer files consume more context and reduce adherence", and `@AGENTS.md` imports are supported. (https://code.claude.com/docs/en/memory)
- Gloaguen et al. 2026: context files raise cost over 20% without generally raising success. Repository overviews are not helpful. Non standard practices are. (https://arxiv.org/abs/2602.11988)
- Diataxis: keep tutorial, how to, reference and explanation apart. Five task guides work if each states its type. (https://diataxis.fr/)

## 5. Does 265 skills hurt?
- Claude Code lists every skill name. Descriptions are capped at 1,536 characters each and budgeted at 1% of the context window, and the least used are dropped first. `skillOverrides` can set `name-only`, `user-invocable-only` or `off`. Plugin skills ignore it. (https://code.claude.com/docs/en/skills.md)
- Measured: 260 real skills, 94.8k characters of descriptions if all shown. Your 209 `name-only` overrides cut that to about 36.8k characters (about 9k tokens), under 1% of the window.
- Anthropic: tool choice "degrades once you exceed 30-50 available tools". (https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool.md) You still describe 77, plus plugin skills, with overlap clusters in review (17), design (67) and test (15). No skill specific benchmark exists. This is an inference from tool studies.
- Deleting saves almost nothing over `name-only` (about 13 characters a name). Disable but keep is the right policy.

## Key takeaways
1. Keep spec 0048's shape: the mirror rename, thin top level, manifest, `/claude-config`, and the weekly reminder.
2. Untraceable or unlicensed skills go to a private store, never the public repo.
3. Edited skills become pin plus patch, not detached copies. Update applies the patch and falls back to `git merge-file`.
4. Docs: AGENTS.md shrinks to non obvious rules, under 200 lines. Each guide states its Diataxis type, and the mapping table stays.
5. A separate small feature: run `/skill-doctor`, cut described skills from 77 to about 35, trim the 8 descriptions over 1,024 characters, and review plugin skills.

## Methodology
Three parallel research agents (Sonnet), each opening sources with firecrawl or curl. Claude Code docs were fetched raw and quoted. Not opened: GNU Stow alternatives yadm and home manager, git subtree docs, and the Go vendoring docs (no usable text). `npx skills --help` was unavailable locally because npx had no cached package.
