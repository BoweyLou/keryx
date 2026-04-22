from __future__ import annotations

from datetime import UTC
from pathlib import Path
import re

import yaml

from knowledge_gateway.models import NoteMetadata
from knowledge_gateway.util import slugify, utcnow


MANAGED_SECTION_RE = r"(<!--\s*AGENT:BEGIN\s+{name}\s*-->)(.*?)(<!--\s*AGENT:END\s+{name}\s*-->)"


def apply_managed_section_patch(content: str, *, section: str, replacement: str) -> str:
    pattern = re.compile(MANAGED_SECTION_RE.format(name=re.escape(section)), re.DOTALL)
    match = pattern.search(content)
    if not match:
        raise ValueError(f"Managed section '{section}' not found.")
    return pattern.sub(rf"\1\n{replacement.strip()}\n\3", content, count=1)


def render_note(metadata: NoteMetadata, body: str) -> str:
    payload = metadata.model_dump(mode="json", exclude_none=True)
    frontmatter = yaml.safe_dump(payload, sort_keys=False, allow_unicode=False).strip()
    return f"---\n{frontmatter}\n---\n\n{body.strip()}\n"


def today_slug() -> str:
    return utcnow().astimezone(UTC).date().isoformat()


def decision_filename(title: str) -> str:
    return f"{today_slug()}-{slugify(title)}.md"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

