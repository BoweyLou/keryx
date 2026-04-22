from __future__ import annotations

from pathlib import Path

from knowledge_gateway.parsing import parse_note


def test_parse_note_tolerates_invalid_frontmatter(tmp_path: Path) -> None:
    vault = tmp_path / "Vault"
    vault.mkdir()
    note_path = vault / "broken.md"
    note_path.write_text(
        """---
title: Broken
bad: value: still bad
---

# Broken

Body text here.
""",
        encoding="utf-8",
    )

    note = parse_note(note_path, vault)

    assert note.metadata.title == "Broken"
    assert note.frontmatter == {}
    assert "# Broken" in note.body
