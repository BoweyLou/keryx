# AGENTS

This repository is `Keryx`, a portable, human-readable memory layer for AI agents backed by an Obsidian vault.

If your environment exposes the `keryx` MCP server, treat that as the preferred durable-memory interface.

## Core Model

- Obsidian vault is the canonical source of truth.
- SQLite is derived index, retrieval, and audit state.
- Keryx is a thin local service that exposes safe reads and writes.
- MCP is the portability layer across Claude Code, Codex, Hermes, OpenClaw, and other clients.
- Keryx is broader than project memory; project context is one stitched view over a larger vault-shaped knowledge system.

## Preferred Agent Behavior

- Retrieve before writing.
- Prefer MCP over direct filesystem edits to the vault.
- If a project is known, start with `get_project_context(project, mode="agent")`.
- If a task is not naturally project-scoped, start with `search_notes(query, mode="hybrid", limit=5-10)` and `list_recent_notes(...)` to recover area, daily, topic, or procedural context.
- Open important notes with `open_note`.
- Persist durable findings with `append_session_note`.
- Persist important choices with `create_decision`.
- Persist follow-up work with `create_task`.

## What Not To Do

- Do not treat your own transient context window as the system of record.
- Do not bypass Keryx with arbitrary vault edits when a Keryx write exists.
- Do not assume SQLite or embeddings are the canonical memory store.
- Do not frame Keryx as a replacement for all agent-native memory. It is usually the durable long-term layer used in tandem with short-term runtime memory.

## Repo Pointers

- Start with [`README.md`](README.md) for positioning and architecture.
- Use [`AGENT_INTEGRATION.md`](AGENT_INTEGRATION.md) as the agent-facing contract.
- Use [`.mcp.json`](.mcp.json) as the local MCP wiring example.
- Use [`skills/hermes-keryx/SKILL.md`](skills/hermes-keryx/SKILL.md) for Hermes-specific operating guidance.
