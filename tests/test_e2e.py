from __future__ import annotations

from pathlib import Path

from knowledge_gateway.config import Settings
from knowledge_gateway.service import KnowledgeGatewayService


def test_end_to_end_capture_index_retrieve_and_audit(sample_vault: Path, tmp_path: Path) -> None:
    service = KnowledgeGatewayService.from_settings(
        Settings(vault_path=sample_vault, database_path=tmp_path / "gateway.db", semantic_enabled=True)
    )

    service.index_now()
    created = service.capture(
        {
            "text": "Portable local-first memory must be resumable across agents.",
            "target": "project-session",
            "project": "Hermes",
            "tags": ["agents", "memory"],
            "source_type": "agent",
            "agent_origin": "Codex",
        }
    )
    service.index_now()

    opened = service.open_note(path=created.path)
    assert "Portable local-first memory" in opened.content

    results = service.search(
        {
            "query": "resumable across agents",
            "mode": "hybrid",
            "filters": {"project": "Hermes"},
            "limit": 5,
        }
    )
    assert any(result.path == created.path for result in results.results)

    context = service.get_project_context("Hermes", mode="agent")
    assert any(session.path == created.path for session in context.sessions)

    audits = service.audit_store.list_entries(limit=10)
    assert audits
    assert audits[0].operation in {"capture", "index"}

