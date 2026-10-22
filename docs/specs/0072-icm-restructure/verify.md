# 0072 verify

## Probes before accept

### Symlink survives the file tools (2026-10-22)
Setup in a scratch folder: `CLAUDE.md` with one line, `ln -s CLAUDE.md AGENTS.md`.
- Edit tool on `AGENTS.md`: refused, "it is a symbolic link. Write to the link's target path instead: .../CLAUDE.md". Link kept.
- Write tool on `AGENTS.md`: same refusal. Link kept.
- `sed -i 's/line one/line one by sed/' AGENTS.md`: exit 0, and `ls -l` shows `AGENTS.md` as a regular 16 byte file. The link was REPLACED, the two files now differ.
Result: the link alone is not enough; AC-9 (commit refusal) and AC-8 (suite test) are required.

### Mod API sees workflow agents
Not run here: it belongs to row 100 (where runs show), not this spec.
