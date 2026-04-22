# Hermes Setup

This repo includes a Hermes-native Keryx skill at [`skills/hermes-keryx/SKILL.md`](skills/hermes-keryx/SKILL.md).

## What Hermes Needs

- Keryx MCP server reachable at `http://127.0.0.1:8001/mcp`
- a `keryx` entry under `mcp_servers` in `~/.hermes/config.yaml`
- the Keryx skill installed under `~/.hermes/skills/keryx/SKILL.md`

## Minimal Hermes Config

```yaml
mcp_servers:
  keryx:
    url: http://127.0.0.1:8001/mcp
    connect_timeout: 60
    timeout: 120
```

## Recommended Use

When Hermes is working against an Obsidian-backed knowledge base:

1. Use the `keryx` MCP tools first for durable memory.
2. Use Hermes native memory for short-term working context.
3. If the task is project-scoped, start with `get_project_context`.
4. If the task is broader than a single project, use `search_notes`, `list_recent_notes`, and `open_note` to reconstruct area, daily, topic, or procedural context.
5. Retrieve before writing.
6. Write durable findings through Keryx, not by editing the vault directly.

## Verification

```bash
hermes mcp list
hermes mcp test keryx
```

You should see the `keryx` server enabled and the Keryx tools discovered.
