from __future__ import annotations

from pathlib import Path

from knowledge_gateway.config import Settings
from knowledge_gateway.service import KnowledgeGatewayService


def test_health_reads_index_state_from_database(sample_vault: Path, tmp_path: Path) -> None:
    settings = Settings(vault_path=sample_vault, database_path=tmp_path / "gateway.db", semantic_enabled=True)

    first = KnowledgeGatewayService.from_settings(settings)
    first.index_now()

    second = KnowledgeGatewayService.from_settings(settings)
    health = second.health()

    assert health.index_state == "ready"
    assert health.last_index_time is not None
