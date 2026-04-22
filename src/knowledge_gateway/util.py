from __future__ import annotations

from datetime import UTC, datetime
import json
import re
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-]*")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "note"


def utcnow() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, default=str)


def from_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def excerpt(text: str, length: int = 220) -> str:
    compact = re.sub(r"\s+", " ", text.strip())
    if len(compact) <= length:
        return compact
    return compact[: length - 3].rstrip() + "..."


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]

