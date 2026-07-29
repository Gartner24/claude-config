#!/usr/bin/env bash
# chroma-reaper: bound runaway chroma-mcp processes leaked by claude-mem.
#
# claude-mem spawns a local `chroma-mcp` vector-DB process per worker/session but
# its supervisor only tracks one; the rest orphan to systemd --user and accumulate
# (~100-400MB each), eventually exhausting RAM and crashing the desktop.
#
# This keeps the KEEP most-recently-started chroma-mcp processes (the active one is
# always newest, so it is never killed) and SIGKILLs the older orphans.
#
# ponytail: watchdog, not a root fix. The real fix is upstream in claude-mem's
# mcp-server.cjs (reap on session end) or CLAUDE_MEM_CHROMA_ENABLED=false to drop
# the vector DB entirely. This bounds the blast radius without losing semantic search.

KEEP="${CHROMA_REAPER_KEEP:-6}"
INTERVAL="${CHROMA_REAPER_INTERVAL:-45}"

reap() {
  # pid + elapsed-seconds for every chroma-mcp process (uv launchers and python children).
  # sort ascending by etimes => newest first; skip the KEEP newest; kill the rest.
  ps -eo pid,etimes,args 2>/dev/null \
    | grep '[c]hroma-mcp' \
    | sort -k2 -n \
    | awk -v k="$KEEP" 'NR>k {print $1}' \
    | xargs -r kill -9 2>/dev/null
}

# Single-instance guard: exit if another reaper is already looping.
LOCK="/tmp/chroma-reaper.$(id -u).lock"
exec 9>"$LOCK" 2>/dev/null || exit 0
flock -n 9 || exit 0

while true; do
  reap
  sleep "$INTERVAL"
done
