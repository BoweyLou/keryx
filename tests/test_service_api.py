from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from knowledge_gateway.api import create_app
from knowledge_gateway.config import Settings
from knowledge_gateway.service import KnowledgeGatewayService


def test_search_and_recent_endpoints(sample_vault: Path, tmp_path: Path) -> None:
    settings = Settings(
        vault_path=sample_vault,
        database_path=tmp_path / "gateway.db",
        semantic_enabled=True,
    )
    service = KnowledgeGatewayService.from_settings(settings)
    service.index_now()

    client = TestClient(create_app(service))
    assert client.app.title == "Keryx"

    search_response = client.post(
        "/search",
        json={
            "query": "portable agent memory",
            "mode": "hybrid",
            "filters": {"project": "Hermes"},
            "limit": 5,
        },
    )
    assert search_response.status_code == 200
    results = search_response.json()["results"]
    assert results
    assert results[0]["path"] == "02 Projects/Hermes/Overview.md"

    recent_response = client.get("/recent", params={"limit": 3, "project": "Hermes"})
    assert recent_response.status_code == 200
    assert len(recent_response.json()["results"]) == 3


def test_capture_and_project_context_endpoints(sample_vault: Path, tmp_path: Path) -> None:
    settings = Settings(
        vault_path=sample_vault,
        database_path=tmp_path / "gateway.db",
        semantic_enabled=True,
    )
    service = KnowledgeGatewayService.from_settings(settings)
    service.index_now()
    client = TestClient(create_app(service))

    capture_response = client.post(
        "/capture",
        json={
            "text": "Local hashing embeddings are enough for the first pass.",
            "target": "project-session",
            "project": "Hermes",
            "tags": ["agents", "memory"],
            "source_type": "agent",
            "agent_origin": "Codex",
        },
    )
    assert capture_response.status_code == 200
    payload = capture_response.json()
    assert payload["dry_run"] is False
    assert payload["path"].startswith("02 Projects/Hermes/Sessions/")

    service.index_now()
    context_response = client.post("/project/context", json={"project": "Hermes", "mode": "agent"})
    assert context_response.status_code == 200
    context = context_response.json()
    assert context["overview"]["path"] == "02 Projects/Hermes/Overview.md"
    assert context["sessions"]
    assert context["decisions"]
    assert context["active_tasks"]
    assert context["machine_summary"]
