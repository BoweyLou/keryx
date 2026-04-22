from __future__ import annotations

from pathlib import Path

from knowledge_gateway.config import Settings
from knowledge_gateway.service import KnowledgeGatewayService


def test_project_context_collects_key_note_sets(sample_vault: Path, tmp_path: Path) -> None:
    service = KnowledgeGatewayService.from_settings(
        Settings(vault_path=sample_vault, database_path=tmp_path / "gateway.db", semantic_enabled=True)
    )
    service.index_now()

    context = service.get_project_context("Hermes", mode="agent")

    assert context.overview.path == "02 Projects/Hermes/Overview.md"
    assert context.sessions[0].path.endswith(".md")
    assert context.decisions[0].path.endswith(".md")
    assert context.active_tasks[0]["text"] == "Implement indexing"
    assert "semantic backend" in " ".join(context.unresolved_questions).lower()


def test_project_context_for_missing_project_returns_empty_structured_context(sample_vault: Path, tmp_path: Path) -> None:
    service = KnowledgeGatewayService.from_settings(
        Settings(vault_path=sample_vault, database_path=tmp_path / "gateway.db", semantic_enabled=True)
    )
    service.index_now()

    context = service.get_project_context("MissingProject", mode="agent")

    assert context.project == "MissingProject"
    assert context.overview.title == "MissingProject"
    assert context.sessions == []
    assert context.decisions == []
    assert context.active_tasks == []
    assert "No indexed project context" in context.machine_summary
