from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import yaml
from yaml import YAMLError

from knowledge_gateway.models import NoteMetadata, ParsedNote


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
MANAGED_REGION_RE = re.compile(
    r"<!--\s*AGENT:BEGIN\s+([a-zA-Z0-9_\-]+)\s*-->\n?(.*?)\n?<!--\s*AGENT:END\s+\1\s*-->",
    re.DOTALL,
)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
TASK_RE = re.compile(r"^\s*-\s\[(?P<done>[ xX])\]\s+(?P<text>.+?)\s*$", re.MULTILINE)
TAG_RE = re.compile(r"(?:^|\s)#([a-zA-Z0-9_\-/]+)")


def _split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content
    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except YAMLError:
        return {}, content
    body = content[match.end() :]
    return frontmatter, body


def _normalize_metadata(frontmatter: dict[str, Any], fallback_title: str) -> NoteMetadata:
    data = dict(frontmatter)
    data.setdefault("title", fallback_title)
    data.setdefault("type", "reference-note")
    if "title" in data and data["title"] is not None:
        data["title"] = str(data["title"])
    if "type" in data and data["type"] is not None:
        data["type"] = str(data["type"])
    for key in ("tags", "related", "aliases"):
        if data.get(key) is None:
            data[key] = []
    return NoteMetadata.model_validate(data)


def parse_note(path: Path, vault_root: Path) -> ParsedNote:
    content = path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(content)
    metadata = _normalize_metadata(frontmatter, fallback_title=path.stem.replace("-", " ").title())
    headings = [(match.group(2).strip(), len(match.group(1))) for match in HEADING_RE.finditer(body)]
    managed_regions = {match.group(1): match.group(2).strip() for match in MANAGED_REGION_RE.finditer(body)}
    wikilinks = [match.group(1).strip() for match in WIKILINK_RE.finditer(body)]
    related_links = [str(item) for item in metadata.related]
    tasks = [
        {"text": match.group("text"), "completed": match.group("done").lower() == "x"}
        for match in TASK_RE.finditer(body)
    ]

    inline_tags = [match.group(1) for match in TAG_RE.finditer(body)]
    if inline_tags:
        metadata.tags = sorted({*metadata.tags, *inline_tags})

    return ParsedNote(
        absolute_path=path,
        relative_path=path.relative_to(vault_root),
        metadata=metadata,
        content=content,
        body=body,
        frontmatter=frontmatter,
        headings=headings,
        managed_regions=managed_regions,
        wikilinks=wikilinks,
        related_links=related_links,
        tasks=tasks,
        modified_time=path.stat().st_mtime,
    )
