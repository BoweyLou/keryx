from __future__ import annotations

from pathlib import Path

from knowledge_gateway.config import Settings


def test_settings_defaults_match_documented_local_ports(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path / "vault", database_path=tmp_path / "gateway.db")

    assert settings.api_port == 8765
    assert settings.mcp_port == 8001


def test_settings_from_yaml_accepts_nested_sections_and_env_refs(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
vault_path: "/tmp/vault"
database_path: "/tmp/gateway.db"
api:
  host: "127.0.0.1"
  port: 9999
mcp:
  enabled: true
  host: "127.0.0.1"
  port: 9001
  allowed_hosts:
    - "keryx.example.ts.net:*"
  allowed_origins:
    - "https://keryx.example.ts.net:*"
security:
  local_token: "env:KB_LOCAL_TOKEN"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("KB_LOCAL_TOKEN", "secret-token")

    settings = Settings.from_yaml(config_path)

    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 9999
    assert settings.mcp_enabled is True
    assert settings.mcp_host == "127.0.0.1"
    assert settings.mcp_port == 9001
    assert settings.mcp_allowed_hosts == ["keryx.example.ts.net:*"]
    assert settings.mcp_allowed_origins == ["https://keryx.example.ts.net:*"]
    assert settings.local_token == "secret-token"
