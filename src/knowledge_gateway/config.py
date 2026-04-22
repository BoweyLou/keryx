from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Settings(BaseModel):
    vault_path: Path
    database_path: Path
    api_host: str = "127.0.0.1"
    api_port: int = 8765
    mcp_enabled: bool = True
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8001
    mcp_allowed_hosts: list[str] = Field(default_factory=list)
    mcp_allowed_origins: list[str] = Field(default_factory=list)
    semantic_enabled: bool = False
    chunk_size: int = 600
    chunk_overlap: int = 80
    freshness_weight: float = 0.15
    project_weight: float = 0.25
    default_mode: str = "hybrid"
    allow_class_c: bool = False
    allowed_targets: list[str] = Field(
        default_factory=lambda: ["00 Inbox", "01 Daily", "02 Projects", "03 Concepts", "05 References", "06 Summaries", "07 Tasks"]
    )
    local_token: str | None = None
    client_name: str = "local"

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Settings":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        api = data.pop("api", None) or {}
        if "host" in api and "api_host" not in data:
            data["api_host"] = api["host"]
        if "port" in api and "api_port" not in data:
            data["api_port"] = api["port"]
        mcp = data.pop("mcp", None) or {}
        if "enabled" in mcp and "mcp_enabled" not in data:
            data["mcp_enabled"] = mcp["enabled"]
        if "host" in mcp and "mcp_host" not in data:
            data["mcp_host"] = mcp["host"]
        if "port" in mcp and "mcp_port" not in data:
            data["mcp_port"] = mcp["port"]
        if "allowed_hosts" in mcp and "mcp_allowed_hosts" not in data:
            data["mcp_allowed_hosts"] = mcp["allowed_hosts"]
        if "allowed_origins" in mcp and "mcp_allowed_origins" not in data:
            data["mcp_allowed_origins"] = mcp["allowed_origins"]
        security = data.pop("security", None) or {}
        if "local_token" in security and "local_token" not in data:
            data["local_token"] = security["local_token"]
        local_token = data.get("local_token")
        if isinstance(local_token, str) and local_token.startswith("env:"):
            data["local_token"] = os.getenv(local_token.removeprefix("env:"))
        return cls.model_validate(data)

    def ensure_paths(self) -> None:
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
