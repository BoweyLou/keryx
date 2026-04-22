from __future__ import annotations

from fastapi import FastAPI, Query

from knowledge_gateway.models import (
    CaptureRequest,
    ProjectContextRequest,
    SearchRequest,
    TaskRequest,
)
from knowledge_gateway.service import KnowledgeGatewayService


def create_app(service: KnowledgeGatewayService) -> FastAPI:
    app = FastAPI(title="Keryx")

    @app.get("/health")
    def health():
        return service.health()

    @app.post("/search")
    def search(request: SearchRequest):
        return service.search(request)

    @app.get("/note")
    def note(path: str | None = Query(default=None), id: str | None = Query(default=None)):
        return service.open_note(path=path, note_id=id)

    @app.post("/capture")
    def capture(request: CaptureRequest):
        return service.capture(request)

    @app.post("/decision")
    def decision(request: dict):
        return service.create_decision(request)

    @app.post("/task")
    def task(request: TaskRequest):
        return service.create_task(request)

    @app.post("/project/context")
    def project_context(request: ProjectContextRequest):
        return service.get_project_context(request.project, mode=request.mode)

    @app.post("/index")
    def index():
        return service.index_now()

    @app.post("/summary")
    def summary(request: dict):
        return service.generate_summary(request["project"])

    @app.get("/recent")
    def recent(limit: int = 10, project: str | None = None):
        return service.list_recent(limit=limit, project=project)

    @app.get("/related")
    def related(path: str, limit: int = 10):
        return service.get_related(path=path, limit=limit)

    @app.post("/promote")
    def promote(request: dict):
        return service.promote_inbox_item(request)

    return app
