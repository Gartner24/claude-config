# Brief: work names out of the public repo (feature 21, spec 0013)

## Agreed so far, do not ask again

Decided in the 2026-10-12 `/architect` session. The names themselves are never written in this repo; this brief lists their categories only.

- Private names, all of them leave the repo: the work orgs and the team PR bot, the client skill names (in `.gitignore` and `settings.json`), the private tool paths in the `settings.json` deny rules, jjstack's publishing org, five more internal tool names you listed in the session, the client photo product skill name, and the client site names (you add those to `names.txt` yourself).
- Shapes to list in `names.txt` for each name, since only case variants are caught for free: the bare name, its hyphenated and spaced forms, any domain or URL form, and folder style forms such as `<name>-website`.
- Private text lives in `~/.claude/private/` and is pulled in by an import line in the live `~/.claude/CLAUDE.md`.
- `sync.sh` strips known spots (settings list items and keys) and refuses any name elsewhere. A missing names list refuses.
- A commit hook (`pre-commit` and `commit-msg`) runs the same check.
- Stripped settings entries go into a private fragment that `install.sh` merges back.
- History: rewrite every commit, delete the GitHub repo, recreate it with the same name, push `main` only. You run the delete and the push.
- Replacements come per name from `names.txt` (`name==>replacement`).
- Cross check: all 12 gaps applied as recommended.
