#!/usr/bin/env bash
# Auto-install dependencies for any claude-mem plugin version missing node_modules.
# Runs at SessionStart to silently fix the "Cannot find module 'zod/v3'" error
# that appears after each new plugin version is cached without running bun install.

PLUGIN_BASE="/home/santiago/.claude/plugins/cache/thedotmack/claude-mem"

[ -d "$PLUGIN_BASE" ] || exit 0

for version_dir in "$PLUGIN_BASE"/*/; do
  [ -f "$version_dir/package.json" ] || continue
  if [ ! -d "$version_dir/node_modules" ]; then
    cd "$version_dir" && /home/santiago/.bun/bin/bun install --silent 2>/dev/null
  fi
done
