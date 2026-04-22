from __future__ import annotations

from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from knowledge_gateway.service import KnowledgeGatewayService


DEFAULT_ALLOWED_HOSTS = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
DEFAULT_ALLOWED_ORIGINS = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


@dataclass
class MCPHandlers:
    service: KnowledgeGatewayService

    def search_notes(self, query: str, mode: str = "hybrid", filters: dict | None = None, limit: int = 10) -> dict:
        return self.service.search(
            {"query": query, "mode": mode, "filters": filters or {}, "limit": limit}
        ).model_dump(mode="json")

    def open_note(self, path: str | None = None, id: str | None = None) -> dict:
        return self.service.open_note(path=path, note_id=id).model_dump(mode="json")

    def capture_note(self, **payload) -> dict:
        return self.service.capture(payload).model_dump(mode="json")

    def append_session_note(self, **payload) -> dict:
        payload["target"] = "project-session"
        return self.service.capture(payload).model_dump(mode="json")

    def get_project_context(self, project: str, mode: str = "agent") -> dict:
        return self.service.get_project_context(project, mode=mode).model_dump(mode="json")

    def create_decision(self, **payload) -> dict:
        return self.service.create_decision(payload).model_dump(mode="json")

    def create_task(self, **payload) -> dict:
        return self.service.create_task(payload).model_dump(mode="json")

    def list_recent_notes(self, limit: int = 10, project: str | None = None) -> dict:
        return self.service.list_recent(limit=limit, project=project).model_dump(mode="json")

    def refresh_index(self) -> dict:
        return self.service.index_now()

    def generate_summary(self, project: str) -> dict:
        return self.service.generate_summary(project).model_dump(mode="json")

    def link_notes(self, source_path: str, target_path: str, reciprocal: bool = True) -> dict:
        return self.service.link_notes(source_path=source_path, target_path=target_path, reciprocal=reciprocal).model_dump(
            mode="json"
        )


def build_mcp_handlers(service: KnowledgeGatewayService) -> MCPHandlers:
    return MCPHandlers(service=service)


def create_mcp_server(service: KnowledgeGatewayService) -> FastMCP:
    handlers = build_mcp_handlers(service)
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_dedupe(DEFAULT_ALLOWED_HOSTS + service.settings.mcp_allowed_hosts),
        allowed_origins=_dedupe(DEFAULT_ALLOWED_ORIGINS + service.settings.mcp_allowed_origins),
    )
    mcp = FastMCP(
        "keryx",
        host=service.settings.mcp_host,
        port=service.settings.mcp_port,
        json_response=True,
        transport_security=transport_security,
    )

    @mcp.tool()
    def search_notes(query: str, mode: str = "hybrid", filters: dict | None = None, limit: int = 10) -> dict:
        return handlers.search_notes(query=query, mode=mode, filters=filters, limit=limit)

    @mcp.tool()
    def open_note(path: str | None = None, id: str | None = None) -> dict:
        return handlers.open_note(path=path, id=id)

    @mcp.tool()
    def capture_note(text: str, target: str, project: str | None = None, tags: list[str] | None = None, source_type: str = "agent", agent_origin: str | None = None) -> dict:
        return handlers.capture_note(
            text=text,
            target=target,
            project=project,
            tags=tags or [],
            source_type=source_type,
            agent_origin=agent_origin,
        )

    @mcp.tool()
    def append_session_note(text: str, project: str, tags: list[str] | None = None, source_type: str = "agent", agent_origin: str | None = None) -> dict:
        return handlers.append_session_note(
            text=text,
            project=project,
            tags=tags or [],
            source_type=source_type,
            agent_origin=agent_origin,
        )

    @mcp.tool()
    def get_project_context(project: str, mode: str = "agent") -> dict:
        return handlers.get_project_context(project=project, mode=mode)

    @mcp.tool()
    def create_decision(payload: dict) -> dict:
        return handlers.create_decision(**payload)

    @mcp.tool()
    def create_task(project: str, text: str, tags: list[str] | None = None) -> dict:
        return handlers.create_task(project=project, text=text, tags=tags or [])

    @mcp.tool()
    def list_recent_notes(limit: int = 10, project: str | None = None) -> dict:
        return handlers.list_recent_notes(limit=limit, project=project)

    @mcp.tool()
    def refresh_index() -> dict:
        return handlers.refresh_index()

    @mcp.tool()
    def generate_summary(project: str) -> dict:
        return handlers.generate_summary(project=project)

    @mcp.tool()
    def link_notes(source_path: str, target_path: str, reciprocal: bool = True) -> dict:
        return handlers.link_notes(source_path=source_path, target_path=target_path, reciprocal=reciprocal)

    @mcp.resource("kb://projects/{project}/context")
    def project_context_resource(project: str) -> str:
        return handlers.get_project_context(project=project, mode="agent").__str__()

    @mcp.resource("kb://notes/{path}")
    def note_resource(path: str) -> str:
        return handlers.open_note(path=path).__str__()

    @mcp.resource("kb://recent")
    def recent_resource() -> str:
        return handlers.list_recent_notes(limit=10).__str__()

    @mcp.resource("kb://daily/today")
    def daily_today_resource() -> str:
        return str(service.get_daily_context())

    @mcp.resource("kb://projects")
    def projects_resource() -> str:
        rows = service.store.query_note_rows(note_type="project-note", limit=100)
        return str([row["project"] or row["title"] for row in rows])

    @mcp.resource("kb://tags")
    def tags_resource() -> str:
        rows = service.store.list_recent_rows(limit=1000)
        tags = sorted({tag for row in rows for tag in service.store.row_to_metadata(row).tags})
        return str(tags)

    @mcp.resource("kb://areas")
    def areas_resource() -> str:
        rows = service.store.list_recent_rows(limit=1000)
        areas = sorted({row["area"] for row in rows if row["area"]})
        return str(areas)

    return mcp
