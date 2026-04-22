# Architecture

This repo is branded publicly as `Keryx`. The current Python module path remains `knowledge_gateway`.

## Canonical Storage

The Obsidian vault remains the durable source of truth. Durable knowledge is stored as markdown plus YAML frontmatter. The gateway adds only local index and audit metadata in SQLite.

## Context Model

Keryx is broader than project memory.

The system should be understood as a context-oriented interface over a whole Obsidian vault. In practice that means the vault may contain:

- episodic memory such as daily notes and session notes
- operational memory such as projects, dashboards, tasks, and decisions
- semantic memory such as concepts, references, and research notes
- procedural memory such as system docs, templates, and workflows
- historical memory such as archives and prior work

`get_project_context` is currently the richest stitched retrieval surface, but projects are only one context family. The broader target model is multiple context-pack builders spanning projects, areas, daily activity, topics, procedures, and history.

## Runtime Layers

1. `parsing.py` reads markdown notes, frontmatter, headings, tasks, links, and managed regions.
2. `chunking.py` produces heading-aware chunks with stable chunk IDs.
3. `storage.py` stores note metadata, chunks, embeddings, and audit logs in SQLite and exposes FTS5 search.
4. `semantic.py` provides a pluggable embedding backend. The default backend uses deterministic token hashing so the system works fully locally without model downloads.
5. `service.py` coordinates indexing, retrieval, project context generation, and guarded writes.
6. `api.py` and `mcp_server.py` expose the same service surface over HTTP and MCP.

## Retrieval

- Keyword search: SQLite FTS5 over note path, title, headings, tags, and chunk text.
- Semantic search: local vector comparison over stored chunk embeddings.
- Hybrid search: blends lexical score, semantic score, freshness, and project match.

Retrieval should not depend only on strict note typing. Folder structure, filenames, links, headings, and tags are important signals because many real vaults encode meaning through path semantics rather than exhaustive frontmatter.

## Write Governance

- Class A: append-safe writes such as inbox capture and session capture
- Class B: template-constrained writes such as task sections and summaries
- Class C: protected mutations, disabled by default

Machine-managed sections use fenced markers:

```markdown
<!-- AGENT:BEGIN summary -->
...
<!-- AGENT:END summary -->
```

## Indexing

`index_now()` walks the vault, reparses only changed markdown files, removes deleted notes from the index, stores updated chunks, and refreshes embeddings when semantic retrieval is enabled.

See [`docs/CONTEXT_MODEL.md`](docs/CONTEXT_MODEL.md) for the broader memory model and [`docs/adr/`](docs/adr) for the design decisions behind it.
