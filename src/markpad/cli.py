from __future__ import annotations

import json
import os
import sys
import webbrowser
from pathlib import Path

import click
import uvicorn

from . import __version__
from .files import normalize_root
from .ports import DEFAULT_PORT, choose_port
from .server import _llm_config, create_app


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["--help"]},
)
@click.version_option(version=__version__, prog_name="markpad")
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Host to bind. Defaults to local-only 127.0.0.1.",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help=f"Port to listen on. Defaults to {DEFAULT_PORT} with automatic fallback.",
)
@click.option(
    "--open",
    "open_browser",
    is_flag=True,
    help="Open the server URL in the default browser.",
)
@click.option(
    "--root",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Folder containing Markdown files. Defaults to the current folder.",
)
@click.pass_context
def main(
    ctx: click.Context,
    host: str,
    port: int | None,
    open_browser: bool,
    root: Path | None,
) -> None:
    """Start a local Markdown web server with live editing and preview."""
    if ctx.invoked_subcommand is not None:
        return
    start_server(root=root, host=host, port=port, open_browser=open_browser)


def start_server(
    *,
    root: Path | None,
    host: str,
    port: int | None,
    open_browser: bool,
) -> None:
    try:
        default_root = os.environ.get("MARKPAD_DEFAULT_ROOT")
        content_root = normalize_root(root or default_root)
    except FileNotFoundError:
        click.echo(f"Content root does not exist: {root}", err=True)
        raise click.ClickException("Missing content root.") from None

    try:
        selected_port = choose_port(host, port)
    except OSError as exc:
        raise click.ClickException(str(exc)) from exc

    url = f"http://{host}:{selected_port}"
    click.echo(f"Serving Markdown from {content_root}")
    click.echo(f"Open {url}")
    if open_browser:
        webbrowser.open(url)

    uvicorn.run(create_app(content_root), host=host, port=selected_port, log_level="info")


@main.command()
@click.argument(
    "root",
    required=False,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Host to bind. Defaults to local-only 127.0.0.1.",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help=f"Port to listen on. Defaults to {DEFAULT_PORT} with automatic fallback.",
)
@click.option(
    "--open",
    "open_browser",
    is_flag=True,
    help="Open the server URL in the default browser.",
)
def serve(root: Path | None, host: str, port: int | None, open_browser: bool) -> None:
    """Start the Markdown web server."""
    start_server(root=root, host=host, port=port, open_browser=open_browser)


@main.command()
@click.argument(
    "root",
    required=False,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def doctor(root: Path | None, output_format: str) -> None:
    """Show install/runtime diagnostics without starting the server."""
    try:
        default_root = os.environ.get("MARKPAD_DEFAULT_ROOT")
        content_root = normalize_root(root or default_root)
    except FileNotFoundError:
        raise click.ClickException("Missing content root.") from None

    llm_config = _llm_config(content_root)
    diagnostics = {
        "version": __version__,
        "content_root": str(content_root),
        "default_port": DEFAULT_PORT,
        "translate_available": llm_config is not None,
        "llm_model": llm_config["model"] if llm_config else None,
        "llm_config_source": _llm_config_source(content_root),
    }
    if output_format == "json":
        click.echo(json.dumps(diagnostics, indent=2, sort_keys=True))
        return

    click.echo(f"markpad {diagnostics['version']}")
    click.echo(f"Content root: {diagnostics['content_root']}")
    click.echo(f"Default port: {diagnostics['default_port']}")
    click.echo(
        "Translation: "
        + (
            f"enabled ({diagnostics['llm_model']}, {diagnostics['llm_config_source']})"
            if diagnostics["translate_available"]
            else "disabled (set LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY)"
        )
    )


def _llm_config_source(root: Path) -> str | None:
    required = ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY")
    if all(os.environ.get(key) for key in required):
        return "environment"
    env_path = root / ".env"
    if env_path.exists():
        return str(env_path)
    return None


def run() -> None:
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    run()
