# Keryx Context Model

Keryx should be understood as a context-oriented memory interface over an Obsidian vault.

It is not only a project-memory layer.

## Design Judgement

Many real Obsidian vaults are not organized as a clean collection of typed project notes. They often blend:

- daily notes
- areas of responsibility
- projects
- research and references
- dashboards and system notes
- transcripts, clippings, and archives

Keryx needs to fit that broader reality.

The right conceptual model is:

- Obsidian vault: canonical durable knowledge
- Keryx: governed retrieval and write interface
- context packs: the primary unit of retrieval for agents
- project context: one important context-pack type, not the ontology

## Memory Layers

Keryx should support these durable memory layers.

### Episodic memory

What happened recently.

Examples:

- daily notes
- session notes
- transcripts
- meeting notes
- recent captures

### Operational memory

What is active and being driven forward.

Examples:

- projects
- dashboards
- tasks
- decision notes
- current status notes

### Semantic memory

What is generally true or reusable.

Examples:

- concept notes
- reference notes
- research summaries
- clippings
- reusable insights

### Procedural memory

How work gets done.

Examples:

- system documentation
- workflows
- templates
- playbooks
- operating guides

### Historical memory

What happened before and may still matter.

Examples:

- archived projects
- past decisions
- prior analyses
- historical daily notes

## Retrieval Units

Keryx should expose three useful levels of retrieval.

### 1. Note-level retrieval

Search and open a specific note.

Current surface:

- `search_notes`
- `open_note`
- `list_recent_notes`

### 2. Context-pack retrieval

Assemble a compact bundle of notes, metadata, and summary for a working context.

Current surface:

- `get_project_context`

Planned context-pack families:

- `project`
- `area`
- `daily`
- `topic`
- `system`
- `history`

### 3. Durable write flows

Persist new state back into the vault in a governed way.

Current surface:

- `append_session_note`
- `capture_note`
- `create_decision`
- `create_task`
- `generate_summary`
- `link_notes`

## Context Types

### Project context

Use when work is anchored to a named project, repo, deliverable, or initiative.

This is the most mature stitched context in the current implementation.

### Area context

Use when the task belongs to an ongoing area of responsibility rather than a single project.

Examples:

- work
- personal systems
- research
- health
- home operations

### Daily context

Use when the task is anchored to current-day activity, recency, or a specific date.

Examples:

- resume what was happening today
- recover open loops from yesterday
- build a morning brief from recent notes

### Topic context

Use when the task is about a theme, tool, problem space, or research topic that spans multiple projects and folders.

Examples:

- agent tooling
- local memory systems
- market research
- architecture decisions

### System context

Use when the agent needs operating guidance, process knowledge, templates, or dashboards.

Examples:

- writing workflow
- repo conventions
- maintenance checklists
- system dashboards

### History context

Use when the task depends on prior work that may now live in archives or older notes.

Examples:

- prior experiments
- superseded decisions
- older summaries
- archived projects

## Discovery Strategy

Keryx should not rely only on strict note typing.

In many vaults, typed frontmatter is sparse or inconsistent. Discovery therefore needs to combine:

- path and folder semantics
- note titles and filenames
- headings
- tags
- links and backlinks
- freshness
- explicit note types when present

This lets Keryx fit human-organized vaults instead of requiring a perfect schema before it becomes useful.

## Current State Versus Target State

Current state:

- the richest stitched view is `get_project_context`
- broader contexts are assembled indirectly with `search_notes`, `list_recent_notes`, and `open_note`

Target state:

- multiple first-class context-pack endpoints and MCP tools
- ranking that understands area, daily, system, and history signals
- path-aware retrieval that works well even when note typing is sparse

## Near-Term Interface Plan

The next logical retrieval additions are:

1. `get_area_context(area, mode)`
2. `get_daily_context(date, mode)`
3. `get_topic_context(query, mode)`
4. `get_system_context(query, mode)`
5. `get_history_context(query, mode)`

Until those exist, agents should approximate broader context by combining:

1. `search_notes`
2. `list_recent_notes`
3. `open_note`
4. `get_project_context` when the task is genuinely project-scoped

## Agent Guidance

Agents should choose retrieval mode like this.

1. Known project or deliverable: start with project context.
2. Ongoing responsibility area: search and recent notes scoped to that area.
3. Current-day resumption: start from daily notes and recent activity.
4. Cross-project theme: search topic/context notes and references.
5. Process or workflow question: search system and procedural notes.
6. Historical comparison: search older notes and archive/history material.

Keryx is therefore best understood as a governed memory interface over a whole human-readable knowledge system, with project context as the first mature retrieval lens.

