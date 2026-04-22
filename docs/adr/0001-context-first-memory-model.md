# ADR 0001: Context-First Memory Model

- Status: Accepted
- Date: 2026-04-15

## Context

Keryx currently exposes a strong `get_project_context` flow. That can create the impression that the system is fundamentally about project memory.

In practice, durable personal knowledge systems are broader than projects. They usually include daily notes, areas of responsibility, references, procedures, dashboards, archives, and cross-project themes.

## Decision

Keryx will be modeled as a context-oriented memory interface over the whole Obsidian vault.

Project context remains important, but it is only one context-pack type.

The broader retrieval model includes:

- project context
- area context
- daily context
- topic/reference context
- system/procedural context
- history/archive context

## Consequences

- Documentation must describe Keryx as broader than project memory.
- New retrieval surfaces should be designed around context packs, not only project notes.
- Agents should be taught to choose the right context family for the task, not assume everything is project-scoped.
- `get_project_context` remains a supported and valuable primitive, but not the ontology of the system.

