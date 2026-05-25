# MCP Servers

Configured in `~/.claude.json` under `mcpServers`.

## magic (21st-dev)

**Package:** `@21st-dev/magic@latest`
**Type:** stdio via npx

Generates UI components using the 21st.dev design system. Has access to a library of
polished components. Use when you want a production-quality component as a starting
point rather than generating from scratch.

**Config to add to `~/.claude.json`:**
```json
{
  "mcpServers": {
    "magic": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@21st-dev/magic@latest"],
      "env": {
        "API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

Get your API key at https://21st.dev

## Adding MCP servers

```bash
# Edit ~/.claude.json directly and add to mcpServers
# Or use the Claude Code settings UI: /config
```
