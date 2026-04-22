from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

from knowledge_gateway.launchd import API_LAUNCHD_LABEL, MCP_LAUNCHD_LABEL, api_launch_agent, mcp_launch_agent


def write_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def bootout_if_loaded(label: str) -> None:
    uid = os.getuid()
    subprocess.run(
        ["launchctl", "bootout", f"gui/{uid}/{label}"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def remove_legacy_plist_if_present(label: str) -> None:
    legacy_path = Path.home() / "Library/LaunchAgents" / f"{label}.plist"
    if legacy_path.exists():
        legacy_path.unlink()


def discover_existing_gateway_labels() -> list[str]:
    agents_dir = Path.home() / "Library/LaunchAgents"
    if not agents_dir.exists():
        return []
    labels: list[str] = []
    for pattern in (
        "*.knowledge-gateway.api.plist",
        "*.knowledge-gateway.mcp.plist",
        "*.keryx.api.plist",
        "*.keryx.mcp.plist",
    ):
        for path in agents_dir.glob(pattern):
            labels.append(path.stem)
    return sorted(set(labels))


def bootstrap(label_path: Path) -> None:
    uid = os.getuid()
    subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(label_path)], check=True)
    subprocess.run(["launchctl", "enable", f"gui/{uid}/{label_path.stem}"], check=True)
    subprocess.run(["launchctl", "kickstart", "-k", f"gui/{uid}/{label_path.stem}"], check=True)


def provision_runtime(repo_root: Path, runtime_root: Path) -> tuple[Path, Path]:
    runtime_root.mkdir(parents=True, exist_ok=True)
    runtime_venv = runtime_root / "venv"
    runtime_python = runtime_venv / "bin/python"
    runtime_config = runtime_root / "local.config.yaml"

    shutil.copy2(repo_root / "local.config.yaml", runtime_config)
    if not runtime_python.exists():
        subprocess.run([sys.executable, "-m", "venv", str(runtime_venv)], check=True)

    subprocess.run([str(runtime_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(runtime_python), "-m", "pip", "install", str(repo_root)], check=True)

    return runtime_venv / "bin/keryx", runtime_config


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    config_path = repo_root / "local.config.yaml"
    if not config_path.exists():
        print(f"missing config: {config_path}", file=sys.stderr)
        return 1

    runtime_root = Path.home() / "Library/Application Support/keryx"
    executable, runtime_config = provision_runtime(repo_root, runtime_root)
    logs_dir = Path.home() / "Library/Logs/keryx"
    agents_dir = Path.home() / "Library/LaunchAgents"
    api_path = agents_dir / f"{API_LAUNCHD_LABEL}.plist"
    mcp_path = agents_dir / f"{MCP_LAUNCHD_LABEL}.plist"

    write_file(
        api_path,
        api_launch_agent(
            repo_root=repo_root,
            config_path=runtime_config,
            logs_dir=logs_dir,
            executable=executable,
        ),
    )
    write_file(
        mcp_path,
        mcp_launch_agent(
            repo_root=repo_root,
            config_path=runtime_config,
            logs_dir=logs_dir,
            executable=executable,
        ),
    )

    existing_labels = discover_existing_gateway_labels()
    for label in (*existing_labels, API_LAUNCHD_LABEL, MCP_LAUNCHD_LABEL):
        bootout_if_loaded(label)
    for label in existing_labels:
        if label in (API_LAUNCHD_LABEL, MCP_LAUNCHD_LABEL):
            continue
        remove_legacy_plist_if_present(label)
    bootstrap(api_path)
    bootstrap(mcp_path)

    print(api_path)
    print(mcp_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
