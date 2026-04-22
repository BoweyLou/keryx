from __future__ import annotations

from pathlib import Path

import typer
import uvicorn

from knowledge_gateway.api import create_app
from knowledge_gateway.config import Settings
from knowledge_gateway.mcp_server import create_mcp_server
from knowledge_gateway.service import KnowledgeGatewayService
from knowledge_gateway.watcher import PollingWatcher


app = typer.Typer(no_args_is_help=True)


def _load_settings(config_path: Path) -> Settings:
    return Settings.from_yaml(config_path)


@app.command()
def serve(config: Path = typer.Option(..., exists=True, dir_okay=False, readable=True)) -> None:
    settings = _load_settings(config)
    service = KnowledgeGatewayService.from_settings(settings)
    uvicorn.run(create_app(service), host=settings.api_host, port=settings.api_port)


@app.command()
def index(config: Path = typer.Option(..., exists=True, dir_okay=False, readable=True)) -> None:
    settings = _load_settings(config)
    service = KnowledgeGatewayService.from_settings(settings)
    typer.echo(service.index_now())


@app.command()
def mcp(config: Path = typer.Option(..., exists=True, dir_okay=False, readable=True)) -> None:
    settings = _load_settings(config)
    service = KnowledgeGatewayService.from_settings(settings)
    server = create_mcp_server(service)
    server.run(transport="streamable-http")


@app.command()
def watch(config: Path = typer.Option(..., exists=True, dir_okay=False, readable=True), interval: float = 1.0) -> None:
    settings = _load_settings(config)
    service = KnowledgeGatewayService.from_settings(settings)
    watcher = PollingWatcher(settings.vault_path)

    def callback(_: list[str]) -> None:
        typer.echo(service.index_now())

    watcher.watch_forever(callback, interval=interval)


if __name__ == "__main__":
    app()
