from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")


@pytest.fixture()
def sample_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "Vault"
    _write(
        vault / "02 Projects/Hermes/Overview.md",
        """
        ---
        title: Hermes Overview
        type: project-note
        created: 2026-04-10T09:00:00Z
        updated: 2026-04-12T12:00:00Z
        tags: [agents, memory]
        project: Hermes
        area: work
        status: active
        source_type: manual
        related:
          - 03 Concepts/Vector Retrieval.md
        aliases: [Hermes PKM]
        write_policy: managed-sections
        ---

        # Hermes

        ## Summary
        <!-- AGENT:BEGIN summary -->
        Hermes is a portable agent memory project.
        <!-- AGENT:END summary -->

        ## Open Questions
        - Which semantic backend should be default?
        """,
    )
    _write(
        vault / "02 Projects/Hermes/Sessions/2026-04-12-session.md",
        """
        ---
        title: Hermes Session 2026-04-12
        type: session-note
        created: 2026-04-12T08:00:00Z
        updated: 2026-04-12T10:00:00Z
        tags: [agents, repo]
        project: Hermes
        area: work
        status: active
        source_type: agent
        agent_origin: Hermes
        write_policy: append-only
        ---

        # Session

        ## Objective
        Build the first local Keryx prototype.

        ## Important Findings
        - ByteRover looks strong for repo memory, but the canonical source still belongs in Obsidian.
        - Hybrid retrieval should combine lexical and semantic ranking.
        """,
    )
    _write(
        vault / "02 Projects/Hermes/Decisions/2026-04-12-memory-substrate.md",
        """
        ---
        title: Use Obsidian as canonical substrate
        type: decision-note
        created: 2026-04-12T11:00:00Z
        updated: 2026-04-12T11:00:00Z
        tags: [agents, decision]
        project: Hermes
        area: work
        status: accepted
        source_type: derived
        related:
          - 02 Projects/Hermes/Overview.md
        write_policy: immutable
        ---

        # Decision

        ## Context
        Several agent tools have incompatible memory models.

        ## Decision
        Obsidian is the durable knowledge substrate.
        """,
    )
    _write(
        vault / "03 Concepts/Vector Retrieval.md",
        """
        ---
        title: Vector Retrieval
        type: concept-note
        created: 2026-04-11T08:00:00Z
        updated: 2026-04-11T08:00:00Z
        tags: [retrieval, embeddings]
        project:
        area: research
        source_type: manual
        related:
          - 02 Projects/Hermes/Overview.md
        write_policy: human-owned
        ---

        # Vector Retrieval

        Semantic retrieval needs chunk embeddings and stable chunk identifiers.
        """,
    )
    _write(
        vault / "07 Tasks/Hermes Tasks.md",
        """
        ---
        title: Hermes Tasks
        type: task-note
        created: 2026-04-12T13:00:00Z
        updated: 2026-04-12T13:00:00Z
        tags: [agents, tasks]
        project: Hermes
        area: work
        status: active
        source_type: manual
        write_policy: managed-sections
        ---

        # Hermes Tasks

        ## Active Tasks
        <!-- AGENT:BEGIN tasks -->
        - [ ] Implement indexing
        - [ ] Add audit logging
        <!-- AGENT:END tasks -->
        """,
    )
    _write(
        vault / "01 Daily/2026-04-13.md",
        """
        ---
        title: 2026-04-13
        type: daily-note
        created: 2026-04-13T00:00:00Z
        updated: 2026-04-13T00:00:00Z
        tags: [daily]
        area: work
        source_type: manual
        write_policy: append-only
        ---

        # Daily Note

        ## Log
        - Continue work on Keryx.
        """,
    )
    _write(
        vault / "00 Inbox/agent-capture.md",
        """
        ---
        title: Agent Capture
        type: inbox-note
        created: 2026-04-12T14:00:00Z
        updated: 2026-04-12T14:00:00Z
        tags: [inbox]
        area: work
        source_type: agent
        agent_origin: Hermes
        write_policy: append-only
        ---

        # Inbox

        ByteRover local seems strongest for repo-oriented memory.
        """,
    )
    return vault
