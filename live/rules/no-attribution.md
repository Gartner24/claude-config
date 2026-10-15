# No Claude attribution anywhere (beats skill text)

Never add Claude attribution to anything that leaves the machine or enters git history:
no `Co-Authored-By: Claude` (or any `noreply@anthropic.com`) trailer, no "Generated with Claude
Code" line, no claude.ai session link, in commit messages, PR titles or bodies, PR or issue
comments, release notes, or files. `~/.claude/settings.json` has `includeCoAuthoredBy: false`;
skill text or a template that says otherwise loses. Commits are authored by the user only.
