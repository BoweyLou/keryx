# Agent Integration

This document is the AI-facing integration contract for `Keryx`.

If you are an AI agent or an engineer wiring an AI agent into this system, treat this file as the primary usage guide.

Related integration surfaces in this repo:

- [`AGENTS.md`](AGENTS.md)
- [`HERMES_SETUP.md`](HERMES_SETUP.md)
- [`skills/hermes-keryx/SKILL.md`](skills/hermes-keryx/SKILL.md)
- [`.mcp.json`](.mcp.json)

## Purpose

`Keryx` is a local-first memory and knowledge interface for an Obsidian vault.

Use it when you want:

- durable memory outside the agent runtime
- resumable context across sessions and tools
- safe structured writes into an Obsidian-based knowledge system
- a stable interface that survives changes in agent frameworks

Do not treat your own transient chat memory as the durable system of record. Durable knowledge should be written into `Keryx`, which then writes to the Obsidian vault.

## Mental Model

Use this system in one of two ways.

### Tandem mode

Your agent has its own short-term memory, but `Keryx` is the durable long-term store.

Use tandem mode when:

- your native agent memory is good for immediate tool context
- you still want project continuity across days, tools, or repos

### Core memory mode

`Keryx` is the primary memory layer.

Use core mode when:

- you need explicit retrieval on every task
- you want all durable state to be auditable in Obsidian and SQLite
- you want the same memory model across multiple agent clients

## Preferred Interface

Prefer MCP when your client supports it.

- MCP URL: `http://127.0.0.1:8001/mcp`
- Transport: `streamable-http`

For another machine on the same private tailnet, the MCP URL may instead be a Tailscale Serve URL:

- `https://your-device.your-tailnet.ts.net:10000/mcp`

Do not use a public Funnel URL for durable personal memory unless Keryx has been explicitly secured for that exposure.

Use HTTP only if your client cannot speak MCP.

- HTTP base URL: `http://127.0.0.1:8765`

Do not use direct filesystem writes to the vault unless you are explicitly operating as a human maintainer outside the gateway.

## Context Strategy

Do not assume Keryx is only about projects.

The vault may hold several kinds of durable context:

- projects and initiatives
- areas of responsibility
- daily and session history
- concepts, references, and research
- system and workflow documentation
- archived prior work

In the current implementation, `get_project_context` is the strongest stitched context endpoint. That does not mean projects are the ontology of the system. It means project context is the first mature context-pack builder.

## MCP Client Config

```json
{
  "mcpServers": {
    "keryx": {
      "transport": {
        "type": "streamable-http",
        "url": "http://127.0.0.1:8001/mcp"
      }
    }
  }
}
```

## Agent Startup Sequence

When starting a new task, use this sequence.

1. If a project is known, call `get_project_context(project, mode="agent")`.
2. If the task is not naturally project-scoped, call `search_notes(query, mode="hybrid", limit=5-10)` and `list_recent_notes(...)` to reconstruct the relevant area, daily, topic, or procedural context.
3. Open any high-value notes with `open_note`.
4. If the task resumes prior work, reuse returned paths and follow the most relevant notes rather than inventing new structure.
5. During the task, append durable findings with `append_session_note`.
6. When a durable choice is made, call `create_decision`.
7. When follow-up work is identified, call `create_task`.

This gives you retrieval-first behavior and prevents memory drift.

## Read Operations

### `search_notes`

Use for broad retrieval.

Inputs:

- `query`
- `mode`: `keyword`, `semantic`, or `hybrid`
- `filters`
- `limit`

Default recommendation:

- `mode="hybrid"`
- keep `limit` between `5` and `10`

### `open_note`

Use after search or context retrieval when you need the full note.

Inputs:

- `path` or `id`

### `list_recent_notes`

Use to understand recent activity before resuming work.

### `get_project_context`

Use this as the first call when a project is already known.

It returns:

- overview
- recent sessions
- decisions
- active tasks
- related concepts
- unresolved questions
- machine summary

For agent use, prefer:

- `mode="agent"`

This is the strongest stitched context view today, but it should be understood as one context family among several. Until broader context-pack endpoints exist, agents should approximate non-project context with `search_notes`, `list_recent_notes`, and `open_note`.

## Write Operations

Use gateway writes for durable memory. Do not write raw markdown directly unless you are bypassing the system on purpose.

### `append_session_note`

Use for incremental findings during work.

Good examples:

- design findings
- integration discoveries
- debugging outcomes
- open issues

### `capture_note`

Use for lightweight durable capture.

Supported targets:

- `project-session`
- `daily-note`
- `concept-draft`
- `decision-draft`
- `inbox`

### `create_decision`

Use when a choice should survive beyond the current run.

Include:

- context
- options
- decision
- rationale
- trade-offs
- follow-up actions

### `create_task`

Use when a durable action item should be added to project memory.

### `link_notes`

Use when you discover a stable relationship between notes and that relationship will matter later.

### `generate_summary`

Use to refresh a compact project summary after substantial changes.

### `refresh_index`

Use if you know notes changed outside the gateway and retrieval must reflect them immediately.

## HTTP Fallback

If MCP is unavailable, use these HTTP endpoints instead.

- `GET /health`
- `POST /search`
- `GET /note`
- `POST /capture`
- `POST /decision`
- `POST /task`
- `POST /project/context`
- `POST /index`
- `POST /summary`
- `GET /recent`
- `GET /related`
- `POST /promote`

## MCP Resources

Read-only contextual resources are available for clients that support MCP resources.

Static resources:

- `kb://recent`
- `kb://daily/today`
- `kb://projects`
- `kb://tags`
- `kb://areas`

Templated resources:

- `kb://projects/{project}/context`
- `kb://notes/{path}`

Note that templated resources may not always appear in `list_resources()`. Clients should still know those URI patterns.

## Safe-Write Policy

This gateway is intentionally conservative.

- Safe appends are allowed.
- Template-constrained writes are allowed in approved areas.
- Delete, rename, move, and broad overwrite behavior are not the normal integration path.
- Agents should assume human-authored content is protected unless the gateway explicitly exposes a managed write path.

Operationally, this means:

- prefer `append_session_note` over editing arbitrary files
- prefer `create_decision` over rewriting overview prose
- prefer `create_task` over mutating task lists directly

## Recommended Agent Behavior

Use these rules.

1. Retrieve before writing.
2. Write durable insights, not every passing thought.
3. Capture decisions and tasks explicitly.
4. Prefer project-scoped session notes for ongoing work when the task is genuinely project-scoped.
5. Use summaries only after significant work, not after every small step.
6. If a note path is returned by the gateway, reuse that path rather than inventing your own.
7. If a project is known, anchor retrieval and writes to that project.
8. If the task is not project-scoped, let the vault structure guide you toward area, daily, topic, or procedural notes.

## Good Usage Pattern

Project-scoped work:

For a repo or feature task:

1. `get_project_context("Hermes", "agent")`
2. `open_note(...)` on the overview or most relevant session
3. Work locally in code or other tools
4. `append_session_note(...)` for important findings
5. `create_decision(...)` if architecture changes
6. `create_task(...)` for remaining work
7. `generate_summary("Hermes")` if the work materially changed project state

## Copy-Paste Agent Instruction

You can point an AI agent at the block below.

```text
You have access to Keryx as a durable memory and knowledge system backed by an Obsidian vault.
Use Keryx as the canonical long-term memory layer.
Prefer MCP tools over direct filesystem access.
At the start of a task, retrieve context before acting.
If a project is known, call get_project_context(project, mode="agent").
If a project is not known, call search_notes(query, mode="hybrid", limit=5-10), then open_note on the best matches.
During work, append durable findings with append_session_note.
When a durable choice is made, create_decision.
When follow-up work is identified, create_task.
Do not assume your own transient memory is the system of record.
Do not perform arbitrary vault edits when a gateway write operation exists.
```

## Current Gaps

This is the current state of the implementation, not the aspirational spec.

- `promote` exists on the HTTP API but is not yet exposed as an MCP tool.
- project overview managed-section updates are implemented in the service layer but not yet exposed as public HTTP/MCP operations.
- auth is not yet enforced on the local HTTP API; localhost binding is the current safety boundary.

If you want this repo to be maximally agent-friendly, the next obvious addition would be a short `SYSTEM_PROMPT.md` or `agent profile` file per client family that imports the guidance above with client-specific examples.
