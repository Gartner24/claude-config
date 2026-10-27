#!/bin/bash
# Starts the claude-fb LiteLLM proxy on localhost only.
set -a; . "$HOME/.config/claude-fb/keys.env"; set +a
export LITELLM_TELEMETRY=False
exec "$HOME/.local/share/claude-fb/venv/bin/litellm" --config "$HOME/.config/claude-fb/litellm.yaml" --host 127.0.0.1 --port 4000
