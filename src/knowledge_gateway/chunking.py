from __future__ import annotations

from collections.abc import Iterable
import re

from knowledge_gateway.models import NoteChunk, ParsedNote
from knowledge_gateway.util import slugify, tokenize


HEADING_LINE_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def _sections(note: ParsedNote) -> Iterable[tuple[list[str], str]]:
    lines = note.body.splitlines()
    stack: list[str] = []
    current_path: list[str] = []
    current_lines: list[str] = []

    def flush() -> tuple[list[str], str] | None:
        text = "\n".join(current_lines).strip()
        if current_path and text:
            return current_path.copy(), text
        return None

    for line in lines:
        heading_match = HEADING_LINE_RE.match(line)
        if heading_match:
            section = flush()
            if section:
                yield section
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            stack[:] = stack[: level - 1]
            stack.append(title)
            current_path = stack.copy()
            current_lines = []
            continue
        current_lines.append(line)

    section = flush()
    if section:
        yield section


def chunk_note(note: ParsedNote, chunk_size: int = 600, chunk_overlap: int = 80) -> list[NoteChunk]:
    chunks: list[NoteChunk] = []
    chunk_index = 0

    for heading_path, section_text in _sections(note):
        words = section_text.split()
        if not words:
            continue
        if len(words) <= chunk_size + chunk_overlap:
            heading_slug = slugify("/".join(heading_path))
            chunks.append(
                NoteChunk(
                    chunk_id=f"{note.relative_path.as_posix()}::{heading_slug}::{chunk_index}",
                    note_path=note.relative_path.as_posix(),
                    heading_path=heading_path.copy(),
                    text=" ".join(words).strip(),
                    token_count=len(tokenize(section_text)),
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1
            continue
        start = 0
        while start < len(words):
            end = min(len(words), start + chunk_size)
            text = " ".join(words[start:end]).strip()
            if text:
                heading_slug = slugify("/".join(heading_path))
                chunks.append(
                    NoteChunk(
                        chunk_id=f"{note.relative_path.as_posix()}::{heading_slug}::{chunk_index}",
                        note_path=note.relative_path.as_posix(),
                        heading_path=heading_path.copy(),
                        text=text,
                        token_count=len(tokenize(text)),
                        chunk_index=chunk_index,
                    )
                )
                chunk_index += 1
            if end >= len(words):
                break
            start = max(end - chunk_overlap, start + 1)

    if not chunks:
        text = note.body.strip()
        chunks.append(
            NoteChunk(
                chunk_id=f"{note.relative_path.as_posix()}::{slugify(note.metadata.title)}::0",
                note_path=note.relative_path.as_posix(),
                heading_path=[note.metadata.title],
                text=text,
                token_count=len(tokenize(text)),
                chunk_index=0,
            )
        )
    return chunks
