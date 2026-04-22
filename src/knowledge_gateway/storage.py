from __future__ import annotations

from datetime import datetime
import sqlite3
from typing import Any

from knowledge_gateway.models import AuditEntry, NoteChunk, NoteMetadata, ParsedNote
from knowledge_gateway.util import from_json, to_json


class AuditStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def log(
        self,
        *,
        timestamp: datetime,
        client_name: str,
        operation: str,
        note_path: str,
        diff_summary: str,
        success: bool,
        request_id: str,
        dry_run: bool = False,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO audit_logs (
                timestamp, client_name, operation, note_path, diff_summary, success, request_id, dry_run
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp.isoformat(), client_name, operation, note_path, diff_summary, int(success), request_id, int(dry_run)),
        )
        self.connection.commit()

    def list_entries(self, limit: int = 20) -> list[AuditEntry]:
        rows = self.connection.execute(
            """
            SELECT timestamp, client_name, operation, note_path, diff_summary, success, request_id, dry_run
            FROM audit_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            AuditEntry(
                timestamp=datetime.fromisoformat(row["timestamp"]),
                client_name=row["client_name"],
                operation=row["operation"],
                note_path=row["note_path"],
                diff_summary=row["diff_summary"],
                success=bool(row["success"]),
                request_id=row["request_id"],
                dry_run=bool(row["dry_run"]),
            )
            for row in rows
        ]


class SQLiteStore:
    def __init__(self, database_path: str) -> None:
        self.connection = sqlite3.connect(database_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.audit_store = AuditStore(self.connection)
        self._init_schema()

    def _init_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS notes (
                path TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                note_type TEXT NOT NULL,
                project TEXT,
                area TEXT,
                status TEXT,
                created TEXT,
                updated TEXT,
                tags_json TEXT NOT NULL,
                aliases_json TEXT NOT NULL,
                related_json TEXT NOT NULL,
                source TEXT,
                source_type TEXT,
                confidence REAL,
                agent_origin TEXT,
                write_policy TEXT,
                content TEXT NOT NULL,
                frontmatter_json TEXT NOT NULL,
                modified_time REAL NOT NULL,
                indexed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                note_path TEXT NOT NULL REFERENCES notes(path) ON DELETE CASCADE,
                heading_path_json TEXT NOT NULL,
                text TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS embeddings (
                chunk_id TEXT PRIMARY KEY REFERENCES chunks(chunk_id) ON DELETE CASCADE,
                vector_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                client_name TEXT NOT NULL,
                operation TEXT NOT NULL,
                note_path TEXT NOT NULL,
                diff_summary TEXT NOT NULL,
                success INTEGER NOT NULL,
                request_id TEXT NOT NULL,
                dry_run INTEGER NOT NULL DEFAULT 0
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
                chunk_id UNINDEXED,
                note_path UNINDEXED,
                title,
                path,
                headings,
                tags,
                body
            );
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def get_indexed_paths(self) -> dict[str, float]:
        rows = self.connection.execute("SELECT path, modified_time FROM notes").fetchall()
        return {row["path"]: float(row["modified_time"]) for row in rows}

    def delete_note(self, path: str) -> None:
        self.connection.execute("DELETE FROM notes WHERE path = ?", (path,))
        self.connection.execute("DELETE FROM chunk_fts WHERE note_path = ?", (path,))
        self.connection.commit()

    def upsert_note(
        self,
        note: ParsedNote,
        chunks: list[NoteChunk],
        embeddings: dict[str, list[float]],
        indexed_at: datetime,
    ) -> None:
        metadata = note.metadata
        self.connection.execute(
            """
            INSERT INTO notes (
                path, title, note_type, project, area, status, created, updated, tags_json,
                aliases_json, related_json, source, source_type, confidence, agent_origin,
                write_policy, content, frontmatter_json, modified_time, indexed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                title=excluded.title,
                note_type=excluded.note_type,
                project=excluded.project,
                area=excluded.area,
                status=excluded.status,
                created=excluded.created,
                updated=excluded.updated,
                tags_json=excluded.tags_json,
                aliases_json=excluded.aliases_json,
                related_json=excluded.related_json,
                source=excluded.source,
                source_type=excluded.source_type,
                confidence=excluded.confidence,
                agent_origin=excluded.agent_origin,
                write_policy=excluded.write_policy,
                content=excluded.content,
                frontmatter_json=excluded.frontmatter_json,
                modified_time=excluded.modified_time,
                indexed_at=excluded.indexed_at
            """,
            (
                note.relative_path.as_posix(),
                metadata.title,
                metadata.type,
                metadata.project,
                metadata.area,
                metadata.status,
                metadata.created.isoformat() if metadata.created else None,
                metadata.updated.isoformat() if metadata.updated else None,
                to_json(metadata.tags),
                to_json(metadata.aliases),
                to_json(metadata.related),
                metadata.source,
                metadata.source_type,
                metadata.confidence,
                metadata.agent_origin,
                metadata.write_policy,
                note.content,
                to_json(note.frontmatter),
                note.modified_time,
                indexed_at.isoformat(),
            ),
        )
        self.connection.execute("DELETE FROM chunks WHERE note_path = ?", (note.relative_path.as_posix(),))
        self.connection.execute("DELETE FROM chunk_fts WHERE note_path = ?", (note.relative_path.as_posix(),))
        for chunk in chunks:
            self.connection.execute(
                """
                INSERT INTO chunks (chunk_id, note_path, heading_path_json, text, token_count, chunk_index)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.chunk_id,
                    chunk.note_path,
                    to_json(chunk.heading_path),
                    chunk.text,
                    chunk.token_count,
                    chunk.chunk_index,
                ),
            )
            self.connection.execute(
                """
                INSERT INTO chunk_fts (chunk_id, note_path, title, path, headings, tags, body)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.chunk_id,
                    chunk.note_path,
                    metadata.title,
                    note.relative_path.as_posix(),
                    " > ".join(chunk.heading_path),
                    " ".join(metadata.tags),
                    chunk.text,
                ),
            )
            if embeddings:
                self.connection.execute(
                    """
                    INSERT INTO embeddings (chunk_id, vector_json)
                    VALUES (?, ?)
                    ON CONFLICT(chunk_id) DO UPDATE SET vector_json=excluded.vector_json
                    """,
                    (chunk.chunk_id, to_json(embeddings.get(chunk.chunk_id, []))),
                )
        self.connection.commit()

    def get_note_row(self, path: str) -> sqlite3.Row | None:
        return self.connection.execute("SELECT * FROM notes WHERE path = ?", (path,)).fetchone()

    def list_recent_rows(self, *, limit: int, project: str | None = None) -> list[sqlite3.Row]:
        if project:
            return self.connection.execute(
                """
                SELECT * FROM notes
                WHERE project = ?
                ORDER BY COALESCE(updated, created, indexed_at) DESC
                LIMIT ?
                """,
                (project, limit),
            ).fetchall()
        return self.connection.execute(
            """
            SELECT * FROM notes
            ORDER BY COALESCE(updated, created, indexed_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def get_index_status(self) -> tuple[int, datetime | None]:
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS note_count, MAX(indexed_at) AS last_index_time
            FROM notes
            """
        ).fetchone()
        note_count = int(row["note_count"]) if row and row["note_count"] is not None else 0
        last_index_time = datetime.fromisoformat(row["last_index_time"]) if row and row["last_index_time"] else None
        return note_count, last_index_time

    def query_note_rows(
        self,
        *,
        project: str | None = None,
        note_type: str | None = None,
        limit: int = 50,
    ) -> list[sqlite3.Row]:
        clauses: list[str] = []
        params: list[Any] = []
        if project:
            clauses.append("project = ?")
            params.append(project)
        if note_type:
            clauses.append("note_type = ?")
            params.append(note_type)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        return self.connection.execute(
            f"""
            SELECT * FROM notes
            {where_sql}
            ORDER BY COALESCE(updated, created, indexed_at) DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()

    def search_keyword_rows(
        self,
        *,
        query: str,
        limit: int,
        filters: dict[str, Any],
    ) -> list[sqlite3.Row]:
        clauses = ["chunk_fts MATCH ?"]
        params: list[Any] = [query]
        if filters.get("project"):
            clauses.append("notes.project = ?")
            params.append(filters["project"])
        if filters.get("area"):
            clauses.append("notes.area = ?")
            params.append(filters["area"])
        if filters.get("type"):
            note_types = filters["type"]
            placeholders = ",".join("?" for _ in note_types)
            clauses.append(f"notes.note_type IN ({placeholders})")
            params.extend(note_types)
        if filters.get("tags"):
            for tag in filters["tags"]:
                clauses.append("notes.tags_json LIKE ?")
                params.append(f'%"{tag}"%')
        params.append(limit)
        return self.connection.execute(
            f"""
            SELECT
                chunk_fts.chunk_id,
                chunk_fts.note_path,
                chunks.text,
                chunks.heading_path_json,
                notes.title,
                notes.note_type,
                notes.project,
                notes.area,
                notes.status,
                notes.updated,
                notes.created,
                notes.tags_json,
                bm25(chunk_fts) AS rank
            FROM chunk_fts
            JOIN chunks ON chunks.chunk_id = chunk_fts.chunk_id
            JOIN notes ON notes.path = chunk_fts.note_path
            WHERE {' AND '.join(clauses)}
            ORDER BY rank
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()

    def all_embedding_rows(self, filters: dict[str, Any]) -> list[sqlite3.Row]:
        clauses: list[str] = []
        params: list[Any] = []
        if filters.get("project"):
            clauses.append("notes.project = ?")
            params.append(filters["project"])
        if filters.get("area"):
            clauses.append("notes.area = ?")
            params.append(filters["area"])
        if filters.get("type"):
            note_types = filters["type"]
            placeholders = ",".join("?" for _ in note_types)
            clauses.append(f"notes.note_type IN ({placeholders})")
            params.extend(note_types)
        if filters.get("tags"):
            for tag in filters["tags"]:
                clauses.append("notes.tags_json LIKE ?")
                params.append(f'%"{tag}"%')
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return self.connection.execute(
            f"""
            SELECT
                embeddings.chunk_id,
                embeddings.vector_json,
                chunks.text,
                chunks.heading_path_json,
                notes.path,
                notes.title,
                notes.note_type,
                notes.project,
                notes.area,
                notes.status,
                notes.updated,
                notes.created,
                notes.tags_json
            FROM embeddings
            JOIN chunks ON chunks.chunk_id = embeddings.chunk_id
            JOIN notes ON notes.path = chunks.note_path
            {where_sql}
            """,
            tuple(params),
        ).fetchall()

    def row_to_metadata(self, row: sqlite3.Row) -> NoteMetadata:
        return NoteMetadata.model_validate(
            {
                "title": row["title"],
                "type": row["note_type"],
                "created": row["created"],
                "updated": row["updated"],
                "tags": from_json(row["tags_json"], []),
                "project": row["project"],
                "area": row["area"],
                "status": row["status"],
                "source_type": None,
                "related": from_json(row["related_json"], []) if "related_json" in row.keys() else [],
                "aliases": from_json(row["aliases_json"], []) if "aliases_json" in row.keys() else [],
                "confidence": row["confidence"] if "confidence" in row.keys() else None,
                "agent_origin": row["agent_origin"] if "agent_origin" in row.keys() else None,
                "write_policy": row["write_policy"] if "write_policy" in row.keys() else None,
            }
        )
