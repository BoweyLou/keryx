# ADR 0003: MCP-First Interface With CLI And Skill Adapters

- Status: Accepted
- Date: 2026-04-15

## Context

Keryx exists to provide a portable durable memory layer across agent systems such as Claude Code, Codex, Hermes, and OpenClaw.

CLI wrappers and agent-specific skills are useful, but they are not themselves the portability layer. They are host-specific guidance and operations surfaces.

## Decision

Keryx will remain MCP-first as its primary agent interface.

Supporting layers remain important:

- HTTP for fallback and scripting
- CLI for local administration and debugging
- skills and repo instructions for host-specific guidance

## Consequences

- Tool schemas and MCP resources remain the primary machine contract.
- Hermes skills, AGENTS.md guidance, and CLI commands are treated as adapters, not the core interface.
- Documentation should explain that MCP is the portable layer and the CLI is an operational surface.
- Future integrations should prefer adding thin skills/adapters on top of MCP rather than creating agent-specific memory backends.
