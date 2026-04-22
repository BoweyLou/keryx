from __future__ import annotations

from pathlib import Path

from knowledge_gateway.config import Settings
from knowledge_gateway.service import KnowledgeGatewayService


def test_link_notes_and_promote_inbox_item(sample_vault: Path, tmp_path: Path) -> None:
    service = KnowledgeGatewayService.from_settings(
        Settings(vault_path=sample_vault, database_path=tmp_path / "gateway.db", semantic_enabled=True)
    )
    service.index_now()

    promote_result = service.promote_inbox_item(
        {
            "source_path": "00 Inbox/agent-capture.md",
            "destination_type": "concept-note",
            "project": "Hermes",
        }
    )
    assert promote_result.path == "03 Concepts/Agent Capture.md"

    link_result = service.link_notes(
        "02 Projects/Hermes/Overview.md",
        "03 Concepts/Vector Retrieval.md",
        reciprocal=True,
    )
    assert link_result.operation == "link-notes"

    service.index_now()
    related = service.get_related("02 Projects/Hermes/Overview.md", limit=10)
    assert any(item.path == "03 Concepts/Vector Retrieval.md" for item in related.results)


def test_generate_summary_writes_summary_note(sample_vault: Path, tmp_path: Path) -> None:
    service = KnowledgeGatewayService.from_settings(
        Settings(vault_path=sample_vault, database_path=tmp_path / "gateway.db", semantic_enabled=True)
    )
    service.index_now()

    summary = service.generate_summary("Hermes")

    assert summary.path == "06 Summaries/Hermes Summary.md"
    assert (sample_vault / summary.path).exists()
