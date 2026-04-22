from __future__ import annotations

from pathlib import Path
import plistlib

API_LAUNCHD_LABEL = "io.keryx.api"
MCP_LAUNCHD_LABEL = "io.keryx.mcp"


def build_launch_agent_plist(
    *,
    label: str,
    program_arguments: list[str],
    working_directory: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> bytes:
    payload = {
        "Label": label,
        "ProgramArguments": program_arguments,
        "WorkingDirectory": str(working_directory),
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(stdout_path),
        "StandardErrorPath": str(stderr_path),
        "ProcessType": "Background",
    }
    return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False)


def api_launch_agent(
    *,
    repo_root: Path,
    config_path: Path,
    logs_dir: Path,
    executable: Path,
) -> bytes:
    return build_launch_agent_plist(
        label=API_LAUNCHD_LABEL,
        program_arguments=[
            str(executable),
            "serve",
            "--config",
            str(config_path),
        ],
        working_directory=repo_root,
        stdout_path=logs_dir / "keryx-api.out.log",
        stderr_path=logs_dir / "keryx-api.err.log",
    )


def mcp_launch_agent(
    *,
    repo_root: Path,
    config_path: Path,
    logs_dir: Path,
    executable: Path,
) -> bytes:
    return build_launch_agent_plist(
        label=MCP_LAUNCHD_LABEL,
        program_arguments=[
            str(executable),
            "mcp",
            "--config",
            str(config_path),
        ],
        working_directory=repo_root,
        stdout_path=logs_dir / "keryx-mcp.out.log",
        stderr_path=logs_dir / "keryx-mcp.err.log",
    )
