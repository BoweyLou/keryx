---
name: keryx
description: Use Keryx as the durable memory layer for Hermes when working against an Obsidian-backed knowledge base. Prefer Keryx MCP tools for retrieval and durable writes, and use Hermes native memory only as short-term context.
version: 1.0.0
metadata:
  hermes:
    tags: [keryx, memory, mcp, obsidian, durable-memory]
    related_skills: [mcp, hermes-agent]
---

# Keryx

Use this skill when Hermes has access to the `keryx` MCP server and should use Keryx as the durable memory layer for Obsidian-backed work.

## Purpose

Keryx gives Hermes a portable, human-readable memory substrate backed by an Obsidian vault.

Use Keryx when you need:

- durable memory outside the Hermes runtime
- resumable project context across days and tools
- safe structured writes into an Obsidian-based knowledge base
- memory that can also be used by Claude Code, Codex, OpenClaw, and other MCP clients

## Mental Model

Treat Hermes native memory as short-term working context.

Treat Keryx as the durable long-term memory layer.

The canonical store is the Obsidian vault. Keryx is the governed interface over it.

Do not assume everything is a project. Keryx is broader than project memory; project context is just the strongest stitched retrieval view available today.

## Preconditions

- The `keryx` MCP server must be configured in Hermes.
- Preferred endpoint: `http://127.0.0.1:8001/mcp`
- The Keryx server should expose tools such as `search_notes`, `open_note`, `append_session_note`, `get_project_context`, `create_decision`, and `create_task`.

Verify if needed:

```bash
hermes mcp test keryx
```

## Startup Sequence

When beginning a task:

1. If the project is known, call `get_project_context(project, mode="agent")`.
2. If the task is not naturally project-scoped, call `search_notes(query, mode="hybrid", limit=5-10)` and `list_recent_notes(...)` to reconstruct the relevant area, daily, topic, or procedural context.
3. Open the most relevant notes with `open_note`.
4. If resuming prior work, call `list_recent_notes(project=..., limit=10)`.

## During The Task

- Use `append_session_note` for durable findings.
- Use `create_decision` for architecture or workflow choices.
- Use `create_task` for durable follow-up actions.
- Use `generate_summary` only after meaningful project changes.

## Write Discipline

- Retrieve before writing.
- Write durable insights, not every passing thought.
- Prefer project-scoped notes over generic inbox capture when the project is known.
- Do not edit vault files directly when a Keryx write operation exists.

## Good Pattern

For a repo task:

1. `get_project_context("ProjectName", "agent")`
2. `open_note(...)` on overview or recent session notes
3. work in code and normal Hermes tools
4. `append_session_note(...)` for important findings
5. `create_decision(...)` for durable choices
6. `create_task(...)` for follow-up work

## What Keryx Is Not

- not a replacement for Obsidian
- not a proprietary memory backend
- not the same thing as Hermes native memory
- not a reason to bypass Hermes tool discipline
