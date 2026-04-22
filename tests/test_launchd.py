from __future__ import annotations

from pathlib import Path
import plistlib

from knowledge_gateway.launchd import API_LAUNCHD_LABEL, MCP_LAUNCHD_LABEL, api_launch_agent, mcp_launch_agent


def test_launchd_generators_emit_expected_labels_and_commands(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    config_path = repo_root / "local.config.yaml"
    logs_dir = tmp_path / "logs"
    executable = repo_root / ".venv/bin/keryx"

    api_payload = plistlib.loads(
        api_launch_agent(
            repo_root=repo_root,
            config_path=config_path,
            logs_dir=logs_dir,
            executable=executable,
        )
    )
    mcp_payload = plistlib.loads(
        mcp_launch_agent(
            repo_root=repo_root,
            config_path=config_path,
            logs_dir=logs_dir,
            executable=executable,
        )
    )

    assert api_payload["Label"] == API_LAUNCHD_LABEL
    assert api_payload["ProgramArguments"][-2:] == ["--config", str(config_path)]
    assert "serve" in api_payload["ProgramArguments"]
    assert api_payload["ProgramArguments"][0] == str(executable)
    assert api_payload["KeepAlive"] is True
    assert api_payload["StandardErrorPath"].endswith("keryx-api.err.log")

    assert mcp_payload["Label"] == MCP_LAUNCHD_LABEL
    assert "mcp" in mcp_payload["ProgramArguments"]
    assert mcp_payload["WorkingDirectory"] == str(repo_root)
    assert mcp_payload["StandardErrorPath"].endswith("keryx-mcp.err.log")
