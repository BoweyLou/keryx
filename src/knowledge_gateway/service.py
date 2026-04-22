from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
import math
import uuid

from knowledge_gateway.chunking import chunk_note
from knowledge_gateway.config import Settings
from knowledge_gateway.models import (
    CaptureRequest,
    ContextNote,
    HealthResponse,
    NoteDocument,
    NoteMetadata,
    OperationResult,
    ParsedNote,
    ProjectContext,
    ProjectContextRequest,
    SearchRequest,
    SearchResponse,
    SearchResult,
    TaskRequest,
)
from knowledge_gateway.parsing import parse_note
from knowledge_gateway.policies import WriteClass, WritePolicyManager
from knowledge_gateway.ranking import RankingWeights, blend_scores
from knowledge_gateway.semantic import HashingEmbeddingBackend, cosine_similarity
from knowledge_gateway.storage import SQLiteStore
from knowledge_gateway.util import excerpt, from_json, to_json, utcnow
from knowledge_gateway.writing import apply_managed_section_patch, decision_filename, ensure_parent, render_note, today_slug


class KnowledgeGatewayService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.ensure_paths()
        self.store = SQLiteStore(str(settings.database_path))
        self.audit_store = self.store.audit_store
        self.embedding_backend = HashingEmbeddingBackend(enabled=settings.semantic_enabled)
        self.policy_manager = WritePolicyManager(
            allow_class_c=settings.allow_class_c,
            allowed_targets=settings.allowed_targets,
        )
        self.last_index_time: datetime | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "KnowledgeGatewayService":
        return cls(settings)

    def health(self) -> HealthResponse:
        note_count, persisted_last_index_time = self.store.get_index_status()
        last_index_time = self.last_index_time or persisted_last_index_time
        return HealthResponse(
            status="ok",
            vault_path=str(self.settings.vault_path),
            index_state="ready" if note_count > 0 else "not-indexed",
            last_index_time=last_index_time,
        )

    def _discover_notes(self) -> list[Path]:
        return sorted(self.settings.vault_path.rglob("*.md"))

    def _index_note(self, path: Path, *, indexed_at: datetime) -> None:
        note = parse_note(path, self.settings.vault_path)
        chunks = chunk_note(note, chunk_size=self.settings.chunk_size, chunk_overlap=self.settings.chunk_overlap)
        embeddings = {
            chunk.chunk_id: self.embedding_backend.embed(chunk.text)
            for chunk in chunks
            if self.settings.semantic_enabled
        }
        self.store.upsert_note(note, chunks, embeddings, indexed_at=indexed_at)

    def index_now(self) -> dict[str, int]:
        indexed_at = utcnow()
        indexed_paths = self.store.get_indexed_paths()
        current_paths = {path.relative_to(self.settings.vault_path).as_posix(): path for path in self._discover_notes()}
        indexed_count = 0

        for relative_path, absolute_path in current_paths.items():
            modified_time = absolute_path.stat().st_mtime
            if relative_path not in indexed_paths or not math.isclose(indexed_paths[relative_path], modified_time):
                self._index_note(absolute_path, indexed_at=indexed_at)
                indexed_count += 1

        for deleted_path in set(indexed_paths) - set(current_paths):
            self.store.delete_note(deleted_path)

        self.last_index_time = indexed_at
        self.audit_store.log(
            timestamp=indexed_at,
            client_name=self.settings.client_name,
            operation="index",
            note_path="*",
            diff_summary=f"indexed={indexed_count} deleted={len(set(indexed_paths) - set(current_paths))}",
            success=True,
            request_id=str(uuid.uuid4()),
        )
        return {"indexed": indexed_count, "deleted": len(set(indexed_paths) - set(current_paths))}

    def _note_type_weight(self, note_type: str) -> float:
        return {
            "project-note": 1.10,
            "decision-note": 1.05,
            "session-note": 1.03,
            "summary-note": 1.02,
        }.get(note_type, 1.0)

    def _freshness_score(self, updated: str | None, created: str | None) -> float:
        stamp = updated or created
        if not stamp:
            return 0.0
        moment = datetime.fromisoformat(stamp)
        age_days = max((utcnow() - moment.astimezone(UTC)).total_seconds() / 86400.0, 0.0)
        return 1.0 / (1.0 + age_days)

    def search(self, payload: SearchRequest | dict) -> SearchResponse:
        request = payload if isinstance(payload, SearchRequest) else SearchRequest.model_validate(payload)
        filters = request.filters.model_dump()
        weights = RankingWeights(
            freshness_weight=self.settings.freshness_weight,
            project_weight=self.settings.project_weight,
        )

        lexical_map: dict[str, dict] = {}
        if request.mode in {"keyword", "hybrid"}:
            for row in self.store.search_keyword_rows(query=request.query, limit=max(20, request.limit * 5), filters=filters):
                rank = abs(float(row["rank"])) if row["rank"] is not None else 1.0
                lexical_score = 1.0 / (1.0 + rank)
                existing = lexical_map.get(row["note_path"])
                if not existing or lexical_score > existing["lexical_score"]:
                    lexical_map[row["note_path"]] = {
                        "path": row["note_path"],
                        "title": row["title"],
                        "snippet": excerpt(row["text"]),
                        "lexical_score": lexical_score,
                        "semantic_score": 0.0,
                        "note_type": row["note_type"],
                        "updated": row["updated"],
                        "created": row["created"],
                        "project": row["project"],
                        "metadata": {
                            "type": row["note_type"],
                            "project": row["project"],
                            "area": row["area"],
                            "status": row["status"],
                            "tags": from_json(row["tags_json"], []),
                        },
                    }

        semantic_map: dict[str, dict] = {}
        if request.mode in {"semantic", "hybrid"} and self.settings.semantic_enabled:
            query_vector = self.embedding_backend.embed(request.query)
            for row in self.store.all_embedding_rows(filters):
                semantic_score = cosine_similarity(query_vector, from_json(row["vector_json"], []))
                if semantic_score <= 0:
                    continue
                existing = semantic_map.get(row["path"])
                if not existing or semantic_score > existing["semantic_score"]:
                    semantic_map[row["path"]] = {
                        "path": row["path"],
                        "title": row["title"],
                        "snippet": excerpt(row["text"]),
                        "lexical_score": 0.0,
                        "semantic_score": semantic_score,
                        "note_type": row["note_type"],
                        "updated": row["updated"],
                        "created": row["created"],
                        "project": row["project"],
                        "metadata": {
                            "type": row["note_type"],
                            "project": row["project"],
                            "area": row["area"],
                            "status": row["status"],
                            "tags": from_json(row["tags_json"], []),
                        },
                    }

        combined = {**semantic_map}
        for path, item in lexical_map.items():
            existing = combined.get(path, {})
            combined[path] = {**existing, **item, "semantic_score": existing.get("semantic_score", 0.0)}

        results: list[SearchResult] = []
        for item in combined.values():
            score = blend_scores(
                lexical_score=item.get("lexical_score", 0.0),
                semantic_score=item.get("semantic_score", 0.0),
                freshness_score=self._freshness_score(item.get("updated"), item.get("created")),
                project_match=1.0 if request.filters.project and item.get("project") == request.filters.project else 0.0,
                note_type_weight=self._note_type_weight(item["note_type"]),
                pinned=False,
                weights=weights,
            )
            results.append(
                SearchResult(
                    path=item["path"],
                    title=item["title"],
                    snippet=item["snippet"],
                    score=score,
                    metadata=item["metadata"],
                    lexical_score=item.get("lexical_score", 0.0),
                    semantic_score=item.get("semantic_score", 0.0),
                )
            )

        results.sort(key=lambda result: result.score, reverse=True)
        return SearchResponse(results=results[: request.limit])

    def open_note(self, *, path: str | None = None, note_id: str | None = None) -> NoteDocument:
        target = path or note_id
        if target is None:
            raise ValueError("Either path or id must be provided.")
        row = self.store.get_note_row(target)
        if row is None:
            absolute_path = self.settings.vault_path / target
            note = parse_note(absolute_path, self.settings.vault_path)
            return NoteDocument(
                path=note.relative_path.as_posix(),
                metadata=note.metadata.model_dump(mode="json"),
                content=note.content,
            )
        metadata = self.store.row_to_metadata(row)
        return NoteDocument(path=row["path"], metadata=metadata.model_dump(mode="json"), content=row["content"])

    def list_recent(self, *, limit: int = 10, project: str | None = None) -> SearchResponse:
        rows = self.store.list_recent_rows(limit=limit, project=project)
        return SearchResponse(
            results=[
                SearchResult(
                    path=row["path"],
                    title=row["title"],
                    snippet=excerpt(row["content"]),
                    score=1.0,
                    metadata=self.store.row_to_metadata(row).model_dump(mode="json"),
                )
                for row in rows
            ]
        )

    def _session_note_path(self, project: str) -> Path:
        return self.settings.vault_path / f"02 Projects/{project}/Sessions/{today_slug()}-session.md"

    def capture(self, payload: CaptureRequest | dict) -> OperationResult:
        request = payload if isinstance(payload, CaptureRequest) else CaptureRequest.model_validate(payload)
        if request.target == "project-session":
            if not request.project:
                raise ValueError("project is required for project-session capture")
            relative_path = f"02 Projects/{request.project}/Sessions/{today_slug()}-session.md"
            self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_A, note_path=relative_path)
            absolute_path = self.settings.vault_path / relative_path
            body_entry = f"- {request.text.strip()}"
            if absolute_path.exists():
                content = absolute_path.read_text(encoding="utf-8").rstrip() + f"\n{body_entry}\n"
            else:
                metadata = NoteMetadata(
                    title=f"{request.project} Session {today_slug()}",
                    type="session-note",
                    created=utcnow(),
                    updated=utcnow(),
                    tags=request.tags,
                    project=request.project,
                    area=request.area,
                    status="active",
                    source_type=request.source_type,
                    agent_origin=request.agent_origin,
                    write_policy="append-only",
                )
                body = (
                    "# Session\n\n"
                    "## Objective\n"
                    f"Continue work on {request.project}.\n\n"
                    "## Important Findings\n"
                    f"{body_entry}\n"
                )
                content = render_note(metadata, body)
            if not request.dry_run:
                ensure_parent(absolute_path)
                absolute_path.write_text(content, encoding="utf-8")
            self.audit_store.log(
                timestamp=utcnow(),
                client_name=request.agent_origin or self.settings.client_name,
                operation="capture",
                note_path=relative_path,
                diff_summary=excerpt(request.text, 120),
                success=True,
                request_id=str(uuid.uuid4()),
                dry_run=request.dry_run,
            )
            return OperationResult(
                operation="capture",
                path=relative_path,
                dry_run=request.dry_run,
                message="Captured note content.",
            )

        if request.target == "daily-note":
            relative_path = f"01 Daily/{today_slug()}.md"
            self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_A, note_path=relative_path)
            absolute_path = self.settings.vault_path / relative_path
            if absolute_path.exists():
                content = absolute_path.read_text(encoding="utf-8")
                if "## Log" in content:
                    content = content.rstrip() + f"\n- {request.text.strip()}\n"
                else:
                    content = content.rstrip() + f"\n\n## Log\n- {request.text.strip()}\n"
            else:
                metadata = NoteMetadata(
                    title=today_slug(),
                    type="daily-note",
                    created=utcnow(),
                    updated=utcnow(),
                    tags=["daily", *request.tags],
                    area=request.area,
                    source_type=request.source_type,
                    agent_origin=request.agent_origin,
                    write_policy="append-only",
                )
                content = render_note(metadata, f"# Daily Note\n\n## Log\n- {request.text.strip()}")
            if not request.dry_run:
                ensure_parent(absolute_path)
                absolute_path.write_text(content, encoding="utf-8")
            self.audit_store.log(
                timestamp=utcnow(),
                client_name=request.agent_origin or self.settings.client_name,
                operation="capture",
                note_path=relative_path,
                diff_summary=excerpt(request.text, 120),
                success=True,
                request_id=str(uuid.uuid4()),
                dry_run=request.dry_run,
            )
            return OperationResult(operation="capture", path=relative_path, dry_run=request.dry_run, message="Captured daily note entry.")

        if request.target in {"concept-draft", "decision-draft"}:
            folder = "03 Concepts" if request.target == "concept-draft" else f"02 Projects/{request.project or 'General'}/Decisions"
            note_type = "concept-note" if request.target == "concept-draft" else "decision-note"
            title = request.text.splitlines()[0][:60].strip(". ") or "Draft"
            relative_path = f"{folder}/{today_slug()}-{uuid.uuid4().hex[:8]}.md"
            self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_A, note_path=relative_path)
            absolute_path = self.settings.vault_path / relative_path
            metadata = NoteMetadata(
                title=title,
                type=note_type,
                created=utcnow(),
                updated=utcnow(),
                tags=request.tags,
                project=request.project,
                area=request.area,
                source_type=request.source_type,
                agent_origin=request.agent_origin,
                write_policy="human-owned" if note_type == "concept-note" else "immutable",
            )
            content = render_note(metadata, f"# {title}\n\n{request.text.strip()}")
            if not request.dry_run:
                ensure_parent(absolute_path)
                absolute_path.write_text(content, encoding="utf-8")
            self.audit_store.log(
                timestamp=utcnow(),
                client_name=request.agent_origin or self.settings.client_name,
                operation="capture",
                note_path=relative_path,
                diff_summary=excerpt(request.text, 120),
                success=True,
                request_id=str(uuid.uuid4()),
                dry_run=request.dry_run,
            )
            return OperationResult(operation="capture", path=relative_path, dry_run=request.dry_run, message="Created draft note.")

        if request.target == "inbox":
            relative_path = f"00 Inbox/{today_slug()}-{uuid.uuid4().hex[:8]}.md"
            self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_A, note_path=relative_path)
            absolute_path = self.settings.vault_path / relative_path
            metadata = NoteMetadata(
                title="Inbox Capture",
                type="inbox-note",
                created=utcnow(),
                updated=utcnow(),
                tags=request.tags,
                area=request.area,
                source_type=request.source_type,
                agent_origin=request.agent_origin,
                write_policy="append-only",
            )
            content = render_note(metadata, f"# Inbox\n\n{request.text.strip()}")
            if not request.dry_run:
                ensure_parent(absolute_path)
                absolute_path.write_text(content, encoding="utf-8")
            self.audit_store.log(
                timestamp=utcnow(),
                client_name=request.agent_origin or self.settings.client_name,
                operation="capture",
                note_path=relative_path,
                diff_summary=excerpt(request.text, 120),
                success=True,
                request_id=str(uuid.uuid4()),
                dry_run=request.dry_run,
            )
            return OperationResult(operation="capture", path=relative_path, dry_run=request.dry_run, message="Captured note content.")

        raise ValueError(f"Unsupported capture target: {request.target}")

    def create_task(self, payload: TaskRequest | dict) -> OperationResult:
        request = payload if isinstance(payload, TaskRequest) else TaskRequest.model_validate(payload)
        relative_path = f"07 Tasks/{request.project} Tasks.md"
        self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_B, note_path=relative_path)
        absolute_path = self.settings.vault_path / relative_path
        task_line = f"- [ ] {request.text.strip()}"
        if absolute_path.exists():
            content = absolute_path.read_text(encoding="utf-8").rstrip()
            if "<!-- AGENT:END tasks -->" in content:
                content = content.replace("<!-- AGENT:END tasks -->", f"{task_line}\n<!-- AGENT:END tasks -->")
            else:
                content = content + f"\n{task_line}\n"
        else:
            metadata = NoteMetadata(
                title=f"{request.project} Tasks",
                type="task-note",
                created=utcnow(),
                updated=utcnow(),
                tags=request.tags,
                project=request.project,
                area="work",
                status="active",
                source_type="agent",
                write_policy="managed-sections",
            )
            body = f"# {request.project} Tasks\n\n## Active Tasks\n<!-- AGENT:BEGIN tasks -->\n{task_line}\n<!-- AGENT:END tasks -->"
            content = render_note(metadata, body)
        if not request.dry_run:
            ensure_parent(absolute_path)
            absolute_path.write_text(content, encoding="utf-8")
        self.audit_store.log(
            timestamp=utcnow(),
            client_name=self.settings.client_name,
            operation="task",
            note_path=relative_path,
            diff_summary=excerpt(task_line, 120),
            success=True,
            request_id=str(uuid.uuid4()),
            dry_run=request.dry_run,
        )
        return OperationResult(operation="task", path=relative_path, dry_run=request.dry_run, message="Task created.")

    def create_decision(self, payload: dict) -> OperationResult:
        from knowledge_gateway.models import DecisionRequest

        request = DecisionRequest.model_validate(payload)
        relative_path = f"02 Projects/{request.project}/Decisions/{decision_filename(request.title)}"
        self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_A, note_path=relative_path)
        absolute_path = self.settings.vault_path / relative_path
        metadata = NoteMetadata(
            title=request.title,
            type="decision-note",
            created=utcnow(),
            updated=utcnow(),
            tags=request.tags,
            project=request.project,
            area="work",
            status="accepted",
            source_type="derived",
            write_policy="immutable",
        )
        options = "\n".join(f"- {item}" for item in request.options) or "- None recorded"
        trade_offs = "\n".join(f"- {item}" for item in request.trade_offs) or "- None recorded"
        follow_ups = "\n".join(f"- {item}" for item in request.follow_up_actions) or "- None recorded"
        body = (
            "# Decision\n\n"
            "## Context\n"
            f"{request.context}\n\n"
            "## Options\n"
            f"{options}\n\n"
            "## Decision\n"
            f"{request.decision}\n\n"
            "## Rationale\n"
            f"{request.rationale}\n\n"
            "## Trade-offs\n"
            f"{trade_offs}\n\n"
            "## Follow-up Actions\n"
            f"{follow_ups}\n"
        )
        content = render_note(metadata, body)
        if not request.dry_run:
            ensure_parent(absolute_path)
            absolute_path.write_text(content, encoding="utf-8")
        self.audit_store.log(
            timestamp=utcnow(),
            client_name=self.settings.client_name,
            operation="decision",
            note_path=relative_path,
            diff_summary=excerpt(request.decision, 120),
            success=True,
            request_id=str(uuid.uuid4()),
            dry_run=request.dry_run,
        )
        return OperationResult(operation="decision", path=relative_path, dry_run=request.dry_run, message="Decision note created.")

    def _rewrite_note(self, relative_path: str, metadata: NoteMetadata, body: str) -> None:
        absolute_path = self.settings.vault_path / relative_path
        ensure_parent(absolute_path)
        absolute_path.write_text(render_note(metadata, body), encoding="utf-8")

    def update_project_overview(self, project: str, section: str, replacement: str, dry_run: bool = False) -> OperationResult:
        relative_path = f"02 Projects/{project}/Overview.md"
        self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_B, note_path=relative_path)
        note = parse_note(self.settings.vault_path / relative_path, self.settings.vault_path)
        updated_content = apply_managed_section_patch(note.content, section=section, replacement=replacement)
        if not dry_run:
            (self.settings.vault_path / relative_path).write_text(updated_content, encoding="utf-8")
        self.audit_store.log(
            timestamp=utcnow(),
            client_name=self.settings.client_name,
            operation="update-project-overview",
            note_path=relative_path,
            diff_summary=f"section={section}",
            success=True,
            request_id=str(uuid.uuid4()),
            dry_run=dry_run,
        )
        return OperationResult(operation="update-project-overview", path=relative_path, dry_run=dry_run, message="Project overview updated.")

    def _context_note_from_row(self, row) -> ContextNote:
        return ContextNote(
            path=row["path"],
            title=row["title"],
            type=row["note_type"],
            updated=datetime.fromisoformat(row["updated"]) if row["updated"] else None,
            snippet=excerpt(row["content"]),
        )

    def _extract_active_tasks(self, project: str) -> list[dict]:
        tasks: list[dict] = []
        for row in self.store.query_note_rows(project=project, note_type="task-note", limit=10):
            note = parse_note(self.settings.vault_path / row["path"], self.settings.vault_path)
            for task in note.tasks:
                if not task["completed"]:
                    tasks.append({"path": row["path"], "text": task["text"]})
        return tasks

    def _extract_open_questions(self, overview_row) -> list[str]:
        content = overview_row["content"]
        questions: list[str] = []
        capture = False
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if line.startswith("## "):
                capture = line.lower() == "## open questions"
                continue
            if capture and line.startswith("- "):
                questions.append(line[2:])
        return questions

    def get_project_context(self, project: str, mode: str = "agent") -> ProjectContext:
        overview_rows = self.store.query_note_rows(project=project, note_type="project-note", limit=1)
        if not overview_rows:
            return ProjectContext(
                project=project,
                mode=mode,
                overview=ContextNote(
                    path="",
                    title=project,
                    type="project-note",
                    snippet="No indexed project overview was found for this project.",
                ),
                sessions=[],
                decisions=[],
                active_tasks=[],
                related_concepts=[],
                recent_references=[],
                unresolved_questions=[],
                machine_summary=f"No indexed project context was found for {project}.",
                recommended_follow_up=[
                    f"Search for related notes for {project}.",
                    f"Create or capture a project overview note for {project}.",
                ],
            )
        overview_row = overview_rows[0]
        session_rows = self.store.query_note_rows(project=project, note_type="session-note", limit=10)
        decision_rows = self.store.query_note_rows(project=project, note_type="decision-note", limit=10)
        concept_rows = self.store.query_note_rows(project=None, note_type="concept-note", limit=10)
        related_concepts = [
            self._context_note_from_row(row)
            for row in concept_rows
            if project.lower() in (row["content"] or "").lower()
            or overview_row["path"] in from_json(row["related_json"], [])
        ][:10]
        active_tasks = self._extract_active_tasks(project)
        unresolved_questions = self._extract_open_questions(overview_row)
        machine_summary = (
            f"{project} has {len(session_rows)} recent sessions, {len(decision_rows)} decisions, "
            f"and {len(active_tasks)} active tasks."
        )
        recommended_follow_up = [
            f"Review task: {task['text']}" for task in active_tasks[:2]
        ] + unresolved_questions[:2]
        return ProjectContext(
            project=project,
            mode=mode,
            overview=self._context_note_from_row(overview_row),
            sessions=[self._context_note_from_row(row) for row in session_rows],
            decisions=[self._context_note_from_row(row) for row in decision_rows],
            active_tasks=active_tasks,
            related_concepts=related_concepts,
            recent_references=[],
            unresolved_questions=unresolved_questions,
            machine_summary=machine_summary,
            recommended_follow_up=recommended_follow_up,
        )

    def get_daily_context(self, day: str | None = None) -> dict:
        date_slug = day or today_slug()
        path = f"01 Daily/{date_slug}.md"
        note = self.open_note(path=path)
        recent = self.list_recent(limit=5).results
        return {"daily": note.model_dump(mode="json"), "recent": [item.model_dump(mode="json") for item in recent]}

    def get_related(self, path: str, limit: int = 10) -> SearchResponse:
        note = self.open_note(path=path)
        related = []
        for related_path in note.metadata.get("related", []):
            try:
                opened = self.open_note(path=related_path)
            except FileNotFoundError:
                continue
            related.append(
                SearchResult(
                    path=opened.path,
                    title=opened.metadata["title"],
                    snippet=excerpt(opened.content),
                    score=1.0,
                    metadata=opened.metadata,
                )
            )
        if len(related) < limit and note.metadata.get("project"):
            project_related = self.list_recent(limit=limit, project=note.metadata["project"]).results
            for item in project_related:
                if item.path != path and all(existing.path != item.path for existing in related):
                    related.append(item)
                    if len(related) >= limit:
                        break
        return SearchResponse(results=related[:limit])

    def generate_summary(self, project: str) -> OperationResult:
        context = self.get_project_context(project, mode="agent")
        relative_path = f"06 Summaries/{project} Summary.md"
        self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_B, note_path=relative_path)
        absolute_path = self.settings.vault_path / relative_path
        metadata = NoteMetadata(
            title=f"{project} Summary",
            type="summary-note",
            created=utcnow(),
            updated=utcnow(),
            tags=["summary", project.lower()],
            project=project,
            area="work",
            source_type="derived",
            write_policy="managed-sections",
        )
        body = (
            f"# {project} Summary\n\n"
            "## Machine Summary\n"
            "<!-- AGENT:BEGIN summary -->\n"
            f"{context.machine_summary}\n"
            "<!-- AGENT:END summary -->\n"
        )
        ensure_parent(absolute_path)
        absolute_path.write_text(render_note(metadata, body), encoding="utf-8")
        self.audit_store.log(
            timestamp=utcnow(),
            client_name=self.settings.client_name,
            operation="summary",
            note_path=relative_path,
            diff_summary=context.machine_summary,
            success=True,
            request_id=str(uuid.uuid4()),
        )
        return OperationResult(operation="summary", path=relative_path, message="Summary generated.")

    def link_notes(self, source_path: str, target_path: str, reciprocal: bool = True, dry_run: bool = False) -> OperationResult:
        self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_B, note_path=source_path)
        source_note = parse_note(self.settings.vault_path / source_path, self.settings.vault_path)
        source_related = [*source_note.metadata.related]
        if target_path not in source_related:
            source_related.append(target_path)
        source_note.metadata.related = source_related
        if not dry_run:
            self._rewrite_note(source_path, source_note.metadata, source_note.body)
        if reciprocal:
            self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_B, note_path=target_path)
            target_note = parse_note(self.settings.vault_path / target_path, self.settings.vault_path)
            target_related = [*target_note.metadata.related]
            if source_path not in target_related:
                target_related.append(source_path)
            target_note.metadata.related = target_related
            if not dry_run:
                self._rewrite_note(target_path, target_note.metadata, target_note.body)
        self.audit_store.log(
            timestamp=utcnow(),
            client_name=self.settings.client_name,
            operation="link-notes",
            note_path=source_path,
            diff_summary=f"target={target_path} reciprocal={reciprocal}",
            success=True,
            request_id=str(uuid.uuid4()),
            dry_run=dry_run,
        )
        return OperationResult(operation="link-notes", path=source_path, dry_run=dry_run, message="Notes linked.")

    def promote_inbox_item(self, payload: dict) -> OperationResult:
        from knowledge_gateway.models import PromoteRequest

        request = PromoteRequest.model_validate(payload)
        source_note = parse_note(self.settings.vault_path / request.source_path, self.settings.vault_path)
        target_folder = {
            "concept-note": "03 Concepts",
            "reference-note": "05 References",
            "summary-note": "06 Summaries",
            "task-note": "07 Tasks",
        }.get(request.destination_type, "03 Concepts")
        filename = f"{source_note.metadata.title}.md".replace("/", "-")
        relative_path = f"{target_folder}/{filename}"
        self.policy_manager.assert_allowed(write_class=WriteClass.CLASS_A, note_path=relative_path)
        metadata = source_note.metadata.model_copy()
        metadata.type = request.destination_type
        metadata.project = request.project or metadata.project
        metadata.updated = utcnow()
        content = render_note(metadata, source_note.body)
        if not request.dry_run:
            absolute_path = self.settings.vault_path / relative_path
            ensure_parent(absolute_path)
            absolute_path.write_text(content, encoding="utf-8")
        self.audit_store.log(
            timestamp=utcnow(),
            client_name=self.settings.client_name,
            operation="promote",
            note_path=relative_path,
            diff_summary=f"from={request.source_path}",
            success=True,
            request_id=str(uuid.uuid4()),
            dry_run=request.dry_run,
        )
        return OperationResult(operation="promote", path=relative_path, dry_run=request.dry_run, message="Inbox item promoted.")
