# Verify: guard hook false alarms · spec 0016 · updated 2026-10-13
_Steps derived from spec 0016 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Commands
- [ ] `bash hooks/block-destructive.sh --test` → prints `all self-checks passed`, exit 0 → AC-1 to AC-5
- [ ] Feed the hook a command with no quotes and no `<<`, e.g. `jq -n '{tool_input:{command:"rm -rf ~"}}' | bash hooks/block-destructive.sh` → exit 2, same message as before → AC-1
- [ ] Feed `git commit -m "docs: rm -rf / was the bug"` through the hook as JSON (as above) → exit 0 → AC-3
- [ ] Feed the `git commit -m "$(cat <<'EOF' ... EOF\n)"` form with a body line naming `rm -rf ~` → exit 0 → AC-3 item 2
- [ ] Feed `cat <<EOF | sh` with body `mkfs.ext4 /dev/sdb1` → exit 2 → AC-2
- [ ] Feed `git commit -m "x; mkfs.ext4 /dev/sdb1` (unclosed quote) → exit 2 → AC-4
- [ ] Run `blank_data` with `PATH=/nonexistent` (the `--test` run does this) → the raw command comes back unchanged → AC-4
- [ ] Mutation check: make `blank()` a no op in a scratch copy, run its `--test` → each of the six AC-5 allow cases fails `should-allow`; restore → AC-5
- [ ] Mutation check: drop the executor check in a scratch copy → every executor case fails `should-block` → AC-2, AC-5

## Manual
- [ ] Copy the hook live outside any `wf run`: `cp ~/claude-config/hooks/block-destructive.sh ~/.claude/hooks/block-destructive.sh`, then make one real commit in a session whose message names a deletion command → the commit is not blocked → AC-6

## Acceptance-criteria coverage
- AC-1: command step 2 and the `--test` fast path cases (all old cases with no quotes)
- AC-2: command step 5, `--test` executor cases, executor mutation check
- AC-3: command steps 3 and 4, `--test` `allow_data` cases
- AC-4: command steps 6 and 7
- AC-5: command step 1 and both mutation checks
- AC-6: the manual step
