# 01_capture

Records the behavior outputs of one side (`base` or `head`) of the restructure in a scratch worktree.

Model: haiku low

`<run>` below is `<repo>/.workflow/runs/restructure-check/<run id>`; the prompt gives you both values, your side
(`base` or `head`) and the full sha to check out (use the sha, not a branch name).

## Inputs
- The ref the prompt names, checked out in a scratch worktree. No docs are loaded.

## Process
1. `git -C <repo> worktree add --detach <run>/01_capture/<side>/tree <ref>`. Work only inside that tree. Do not
   change HOME. Do not run install without `--dry-run`.
2. Run each command below from the tree root, in this order, and save its stdout, stderr and exit code to
   `<run>/01_capture/output/<side>/<command-slug>.txt` (slug: the command with every run of non letters and digits as
   `-`; first line of the file `exit: <code>`). A command that fails or is missing still gets its file, with its error.
   Never retry and never fix anything.
   A tree with no `tools/` folder (a ref from before the tools folder move) has the same files one level up: run
   each `tools/bin/...` and `tools/scripts/...` command below without the `tools/` prefix, and keep the slug the
   `tools/` spelling gives, so both sides' files pair up.
   - `tools/bin/install.sh --dry-run`
   - `python3 tools/bin/claude-config.py drift`
   - `python3 tools/bin/claude-config.py docs`, then `git status --porcelain` (saved as its own file, slug `git-status-after-docs`).
     Leave the scratch tree as it is; never `git checkout -- .`.
   - Self checks, each `--test`:
     `python3 tools/scripts/design-check.py --test`, `tools/scripts/fb-ask.py`, `tools/scripts/start-gates.py`,
     `tools/scripts/handover-memory.py`, `tools/scripts/issue-reread.py`, `tools/scripts/private-names.py`, `tools/scripts/ref-check.py`,
     `tools/scripts/review-isolated.py`, `tools/scripts/spec-paths.py` (same form), then
     `python3 claude-home/hooks/chain-catch.py --test`, `live-tick.py`, `plain-panel.py`, `no-jjstack-bar.py`,
     `node claude-home/hooks/context-monitor.js --test`, and `bash claude-home/hooks/block-destructive.sh --test`,
     `handover-start.sh`, `workflow-start.sh` (same form). Then run
     `grep -lE -e '--test' tools/scripts/*.py claude-home/hooks/*` and, for any file that is in that list but not above,
     run it the same way (python3 for `.py`, node for `.js`, bash for `.sh`) and note it in the summary.
   - `python3 tests/fast.py`
   - Base side only: `python3 tools/scripts/ref-check.py snapshot --repo <tree> --home <run>/01_capture/base/emptyhome --out <run>/01_capture/base/snapshot.json`
     (make the empty home dir first), then copy `snapshot.json` into the output folder.
   - Head side only: `python3 tools/scripts/ref-check.py verify --repo <tree> --home <run>/01_capture/head/emptyhome <run>/01_capture/output/base/snapshot.json --map-from-git <base ref>`
     (make the empty home dir first; the base ref is the one the prompt names; the base side has already finished,
     so the snapshot exists; when it is missing, save that error as the command's file).
   - For every spec top file, `docs/specs/NNNN-*.md` or `docs/specs/NNNN-*/index.md`: take NNNN as the first 4 digits
     of the file name or, for `index.md`, of its folder name (never a fragment of `index`), then run
     `python3 tools/scripts/spec-paths.py --spec NNNN` (one file per spec, slug includes the number).
   - `live-links.txt`: every link target `tools/bin/install.sh --dry-run` would make, one `link -> target` per line, copied from
     that dry run's output.
3. `git -C <repo> worktree remove --force <run>/01_capture/<side>/tree`, then write the outputs below and return the
   schema the prompt names.

## Outputs
- `<run>/01_capture/output/<side>/<command-slug>.txt`: one file per command, plus `live-links.txt` and (base only) `snapshot.json`
- `<run>/01_capture/output/<side>/index.md`: one line per command: slug, exit code, ok or failed

## Human check
Every command has an output file on both sides or a recorded failure.

## Do NOT load
- Any doc, spec or scope file; this stage only runs commands and saves what they print
- The other side's output
