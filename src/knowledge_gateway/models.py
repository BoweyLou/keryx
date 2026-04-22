from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class NoteMetadata(BaseModel):
    title: str
    type: str
    created: datetime | None = None
    updated: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    project: str | None = None
    area: str | None = None
    status: str | None = None
    source: str | None = None
    source_type: str | None = None
    related: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    confidence: float | None = None
    agent_origin: str | None = None
    write_policy: str | None = None


@dataclass(slots=True)
class ParsedNote:
    absolute_path: Path
    relative_path: Path
    metadata: NoteMetadata
    content: str
    body: str
    frontmatter: dict[str, Any]
    headings: list[tuple[str, int]]
    managed_regions: dict[str, str]
    wikilinks: list[str]
    related_links: list[str]
    tasks: list[dict[str, Any]]
    modified_time: float


@dataclass(slots=True)
class NoteChunk:
    chunk_id: str
    note_path: str
    heading_path: list[str]
    text: str
    token_count: int
    chunk_index: int


class SearchFilters(BaseModel):
    project: str | None = None
    area: str | None = None
    tags: list[str] = Field(default_factory=list)
    type: list[str] = Field(default_factory=list)
    date_from: datetime | None = None
    date_to: datetime | None = None


class SearchRequest(BaseModel):
    query: str
    mode: Literal["keyword", "semantic", "hybrid"] = "hybrid"
    filters: SearchFilters = Field(default_factory=SearchFilters)
    limit: int = 10


class SearchResult(BaseModel):
    path: str
    title: str
    snippet: str
    score: float
    metadata: dict[str, Any]
    lexical_score: float = 0.0
    semantic_score: float = 0.0


class SearchResponse(BaseModel):
    results: list[SearchResult]


class NoteDocument(BaseModel):
    path: str
    metadata: dict[str, Any]
    content: str


class CaptureRequest(BaseModel):
    text: str
    target: str
    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    area: str | None = "work"
    source_type: str = "agent"
    agent_origin: str | None = None
    dry_run: bool = False


class DecisionRequest(BaseModel):
    project: str
    title: str
    context: str
    options: list[str] = Field(default_factory=list)
    decision: str
    rationale: str
    trade_offs: list[str] = Field(default_factory=list)
    follow_up_actions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    dry_run: bool = False


class TaskRequest(BaseModel):
    project: str
    text: str
    tags: list[str] = Field(default_factory=list)
    dry_run: bool = False


class PromoteRequest(BaseModel):
    source_path: str
    destination_type: str
    project: str | None = None
    dry_run: bool = False


class ProjectContextRequest(BaseModel):
    project: str
    mode: Literal["full", "brief", "agent", "human"] = "agent"


class OperationResult(BaseModel):
    operation: str
    path: str
    dry_run: bool = False
    message: str


class ContextNote(BaseModel):
    path: str
    title: str
    type: str
    updated: datetime | None = None
    snippet: str = ""


class ProjectContext(BaseModel):
    project: str
    mode: str
    overview: ContextNote
    sessions: list[ContextNote]
    decisions: list[ContextNote]
    active_tasks: list[dict[str, Any]]
    related_concepts: list[ContextNote]
    recent_references: list[ContextNote]
    unresolved_questions: list[str]
    machine_summary: str
    recommended_follow_up: list[str]


class HealthResponse(BaseModel):
    status: str
    vault_path: str
    index_state: str
    last_index_time: datetime | None = None


class AuditEntry(BaseModel):
    timestamp: datetime
    client_name: str
    operation: str
    note_path: str
    diff_summary: str
    success: bool
    request_id: str
    dry_run: bool = False

