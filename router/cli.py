"""`router` command line. Slice 1: `serve`. Later: `names list|add|remove|sync`, `listen`."""

from __future__ import annotations

import logging

import typer

from router.settings import Settings

app = typer.Typer(help="voice-router: talk to any assistant by name.", no_args_is_help=True)


@app.callback()
def _main() -> None:
    pass


@app.command()
def serve(
    host: str | None = typer.Option(None, help="Bind address (default from config.yaml)."),
    port: int | None = typer.Option(None, help="Port (default from config.yaml)."),
    reload: bool = typer.Option(False, help="Auto-reload on code changes (development)."),
) -> None:
    """Run the router."""
    import uvicorn

    settings = Settings()
    config = settings.load_config()
    logging.basicConfig(level=settings.log_level.upper())
    uvicorn.run(
        "router.app:default_app",
        factory=True,
        host=host or config.server.host,
        port=port or config.server.port,
        reload=reload,
        log_level=settings.log_level.lower(),
    )


@app.command()
def check() -> None:
    """Validate assistants.yaml and config.yaml, then print the registry."""
    from router.registry import Registry, RegistryError

    settings = Settings()
    try:
        registry = Registry.load(settings.assistants_file)
    except RegistryError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from None
    settings.load_config()
    typer.echo(
        f"default: {registry.default_assistant}  sticky: {registry.sticky_minutes} min  "
        f"fuzzy: {registry.fuzzy_threshold}"
    )
    for a in registry.assistants.values():
        what = a.model or (f"council of {', '.join(a.council)}" if a.council else "auto router")
        extra = " private" if a.private else ""
        typer.echo(f"  {a.key:<8} {a.display_name:<8} {what}{extra}")
        typer.echo(
            f"           names: {', '.join(a.names)}"
            + (f"   mishears: {', '.join(a.mishears)}" if a.mishears else "")
        )


if __name__ == "__main__":
    app()
