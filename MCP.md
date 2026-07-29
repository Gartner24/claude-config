# MCP Servers

Two MCP servers are active. `magic` is manually configured in `~/.claude.json`.
`context7` is enabled in `settings.local.json` **and** declared in `~/.mcp.json`.

## context7

**Source:** claude.ai MCP connectors, plus a stdio entry in `~/.mcp.json` that jjstack's
`./setup` writes (`npx -y @upstash/context7-mcp`). Setup detects an existing `context7` key
and skips, so re-running it is safe.
**Enabled in:** `settings.local.json` via `enabledMcpjsonServers: ["context7"]`

Fetches live documentation for any library, framework, SDK, or CLI tool. Use when asking
about React, Next.js, Prisma, Tailwind, Django, or any other library - even well-known ones.
Your training data may not reflect recent changes; context7 fetches current docs.

**When to use:** Any question about library API syntax, configuration, version migration,
or CLI usage. Claude will automatically reach for it when you ask about a library.

**Re-enable on new machine:** Go to Claude Code settings -> MCP -> enable context7 connector.

---

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
