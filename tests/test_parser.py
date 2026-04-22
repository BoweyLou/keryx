from __future__ import annotations

from pathlib import Path

from knowledge_gateway.chunking import chunk_note
from knowledge_gateway.parsing import parse_note


def test_parse_note_extracts_frontmatter_headings_links_and_regions(sample_vault: Path) -> None:
    note = parse_note(sample_vault / "02 Projects/Hermes/Overview.md", sample_vault)

    assert note.metadata.title == "Hermes Overview"
    assert note.metadata.type == "project-note"
    assert note.metadata.project == "Hermes"
    assert note.metadata.tags == ["agents", "memory"]
    assert note.headings == [("Hermes", 1), ("Summary", 2), ("Open Questions", 2)]
    assert note.managed_regions["summary"].strip() == "Hermes is a portable agent memory project."
    assert note.wikilinks == []
    assert note.related_links == ["03 Concepts/Vector Retrieval.md"]
    assert note.relative_path.as_posix() == "02 Projects/Hermes/Overview.md"


def test_chunk_note_is_heading_aware_and_stable(sample_vault: Path) -> None:
    note = parse_note(sample_vault / "02 Projects/Hermes/Sessions/2026-04-12-session.md", sample_vault)

    chunks = chunk_note(note, chunk_size=22, chunk_overlap=4)

    assert len(chunks) >= 2
    assert all(chunk.chunk_id.startswith("02 Projects/Hermes/Sessions/2026-04-12-session.md::") for chunk in chunks)
    assert chunks[0].heading_path == ["Session", "Objective"]
    assert "portable agent" not in chunks[0].text
    assert "Hybrid retrieval" in chunks[-1].text

