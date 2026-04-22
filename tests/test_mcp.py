from __future__ import annotations

from pathlib import Path

from knowledge_gateway.config import Settings
from knowledge_gateway.mcp_server import build_mcp_handlers, create_mcp_server
from knowledge_gateway.service import KnowledgeGatewayService


def test_mcp_handlers_wrap_service_operations(sample_vault: Path, tmp_path: Path) -> None:
    service = KnowledgeGatewayService.from_settings(
        Settings(vault_path=sample_vault, database_path=tmp_path / "gateway.db", semantic_enabled=True)
    )
    service.index_now()

    handlers = build_mcp_handlers(service)

    search_result = handlers.search_notes(query="portable agent", mode="hybrid", filters={"project": "Hermes"}, limit=5)
    assert search_result["results"]

    note = handlers.open_note(path="02 Projects/Hermes/Overview.md")
    assert note["metadata"]["type"] == "project-note"

    recent = handlers.list_recent_notes(limit=2, project="Hermes")
    assert len(recent["results"]) == 2


def test_mcp_server_uses_keryx_name(sample_vault: Path, tmp_path: Path) -> None:
    service = KnowledgeGatewayService.from_settings(
        Settings(
            vault_path=sample_vault,
            database_path=tmp_path / "gateway.db",
            semantic_enabled=True,
            mcp_allowed_hosts=["keryx.example.ts.net:*"],
            mcp_allowed_origins=["https://keryx.example.ts.net:*"],
        )
    )
    server = create_mcp_server(service)

    assert server.name == "keryx"
    assert server.settings.transport_security is not None
    assert "127.0.0.1:*" in server.settings.transport_security.allowed_hosts
    assert "keryx.example.ts.net:*" in server.settings.transport_security.allowed_hosts
    assert "https://keryx.example.ts.net:*" in server.settings.transport_security.allowed_origins
