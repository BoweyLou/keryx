# ADR 0002: Path-First Discovery Over Strict Typing

- Status: Accepted
- Date: 2026-04-15

## Context

Many Obsidian vaults have inconsistent or sparse note typing. Folder structure, filenames, dashboards, daily-note conventions, and linking patterns often carry more meaning than explicit `type:` frontmatter.

If Keryx depends too heavily on strict typed-note schemas, it will fit only highly curated vaults and become brittle on ordinary human-maintained knowledge systems.

## Decision

Keryx will prefer path and vault-structure semantics as first-class discovery signals, while still using explicit metadata when present.

The retrieval and indexing model should combine:

- path segments and folder roles
- note titles and filenames
- headings
- tags
- backlinks and outgoing links
- freshness
- explicit frontmatter typing

## Consequences

- Indexing should preserve path structure and folder roles in queryable form.
- Ranking should treat path and area/project matches as strong signals.
- Documentation should not imply that users must fully normalize their vault before Keryx is useful.
- Future context-pack builders should rely on both path semantics and note metadata.

