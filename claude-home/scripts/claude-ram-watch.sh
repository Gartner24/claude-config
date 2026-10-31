#!/usr/bin/env bash
# Keeps Claude Code sessions alive under memory pressure.
#
# Why a session died before: a leaking MCP helper (node) got kernel-OOM-killed,
# and systemd's default OOMPolicy=stop on the tmux pane scope then tore down the
# WHOLE pane, claude included. Two defences here:
#   1. drop-in sets OOMPolicy=continue on every scope holding a claude process,
#      so a kernel kill on a helper no longer stops the session.
#   2. this watcher SIGKILLs a leaking helper first. A watcher kill is an
#      ordinary signal, not a kernel OOM, so it never trips OOMPolicy at all.
# Never targets a claude process itself.
# ponytail: 5s polling; switch to cgroup memory.events if a leak ever outruns it.
set -u

# Linux only (/proc, systemd scopes): a Mac has neither, so the watcher does nothing there (spec 0082 AC-4).
[ "$(uname -s)" = Darwin ] && exit 0

INTERVAL=${INTERVAL:-5}
CHILD_MAX_KB=${CHILD_MAX_KB:-2000000}      # 2 GB: any single helper above this is leaking
MEM_FLOOR_KB=${MEM_FLOOR_KB:-3000000}      # below 3 GB available, kill the biggest helper regardless
DRY_RUN=${DRY_RUN:-0}
LOG=${LOG:-$HOME/.claude/logs/ram-watch.log}
UNITDIR=${UNITDIR:-$HOME/.config/systemd/user}

mkdir -p "$(dirname "$LOG")"

log() { printf '%s %s\n' "$(date '+%F %T')" "$*" >>"$LOG"; }

descendants() {
  local c
  for c in $(pgrep -P "$1" 2>/dev/null); do
    echo "$c"
    descendants "$c"
  done
}

# systemd tears the whole pane down on a kernel OOM unless told otherwise.
protect_scope() {
  local pid=$1 unit dir
  unit=$(basename "$(cut -d: -f3 /proc/$pid/cgroup 2>/dev/null | head -1)")
  case "$unit" in tmux-spawn-*.scope) ;; *) return ;; esac
  dir="$UNITDIR/$unit.d"
  [ -f "$dir/oom.conf" ] && return
  [ "$DRY_RUN" = 1 ] && { log "WOULD PROTECT $unit"; return; }
  mkdir -p "$dir" && printf '[Scope]\nOOMPolicy=continue\n' > "$dir/oom.conf" || return
  systemctl --user daemon-reload
  log "PROTECTED $unit OOMPolicy=continue"
}

# Steer the kernel's OOM killer at helpers rather than at the session.
prefer_victim() {
  [ "$DRY_RUN" = 1 ] && return
  [ "$(cat /proc/$1/oom_score_adj 2>/dev/null)" = 1000 ] && return
  echo 1000 > /proc/$1/oom_score_adj 2>/dev/null
}

reap() {
  local pid=$1 rss=$2 why=$3 cmd
  cmd=$(tr '\0' ' ' </proc/$pid/cmdline 2>/dev/null | cut -c1-120)
  [ -z "$cmd" ] && return
  if [ "$DRY_RUN" = 1 ]; then
    log "WOULD KILL pid=$pid rss=${rss}kB ($why) $cmd"
  else
    kill -9 "$pid" 2>/dev/null && log "KILLED pid=$pid rss=${rss}kB ($why) $cmd"
  fi
}

# Drop-ins for panes that no longer exist. Removes only the file this script wrote.
sweep_stale() {
  local dir unit
  for dir in "$UNITDIR"/tmux-spawn-*.scope.d; do
    [ -d "$dir" ] || continue
    unit=$(basename "$dir" .d)
    systemctl --user is-active --quiet "$unit" && continue
    rm -f "$dir/oom.conf"
    rmdir "$dir" 2>/dev/null
  done
}

scan() {
  local avail top_pid=0 top_rss=0 sess pid rss
  avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo)

  for sess in $(pgrep -x claude); do
    protect_scope "$sess"
    for pid in $(descendants "$sess"); do
      [ -r /proc/$pid/status ] || continue
      rss=$(awk '/^VmRSS:/{print $2}' /proc/$pid/status 2>/dev/null)
      [ -z "$rss" ] && continue
      prefer_victim "$pid"
      if [ "$rss" -gt "$CHILD_MAX_KB" ]; then
        reap "$pid" "$rss" "over ${CHILD_MAX_KB}kB"
        continue
      fi
      if [ "$rss" -gt "$top_rss" ]; then top_rss=$rss; top_pid=$pid; fi
    done
  done

  if [ "$avail" -lt "$MEM_FLOOR_KB" ] && [ "$top_pid" -ne 0 ]; then
    reap "$top_pid" "$top_rss" "MemAvailable ${avail}kB below floor"
  fi
}

if [ "${1:-}" = "--once" ]; then scan; sweep_stale; exit 0; fi

log "watcher started interval=${INTERVAL}s child_max=${CHILD_MAX_KB}kB floor=${MEM_FLOOR_KB}kB"
n=0
while :; do
  scan
  n=$((n + 1))
  [ $((n % 120)) -eq 0 ] && sweep_stale
  sleep "$INTERVAL"
done
