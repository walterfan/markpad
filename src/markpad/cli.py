from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import webbrowser
from contextlib import contextmanager, suppress
from pathlib import Path
from urllib.parse import quote

import click
import httpx
import uvicorn

from . import __version__
from .files import MARKDOWN_EXTENSIONS, normalize_root, to_relative_posix
from .ports import DEFAULT_PORT, choose_port
from .server import _llm_config, create_app


def _runtime_dir() -> Path:
    base = os.environ.get("XDG_RUNTIME_DIR") or os.path.join(
        os.path.expanduser("~"), ".local", "state"
    )
    path = Path(base) / "markpad"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _pid_file() -> Path:
    return _runtime_dir() / "markpad.pid"


def _info_file() -> Path:
    return _runtime_dir() / "markpad.json"


def _write_runtime_info(pid: int, host: str, port: int, root: Path) -> None:
    _pid_file().write_text(str(pid), encoding="utf-8")
    _info_file().write_text(
        json.dumps(
            {"pid": pid, "host": host, "port": port, "root": str(root)},
            indent=2,
        ),
        encoding="utf-8",
    )


def _read_runtime_info() -> dict | None:
    info = _info_file()
    if not info.exists():
        return None
    try:
        return json.loads(info.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _clear_runtime_info() -> None:
    for path in (_pid_file(), _info_file()):
        with suppress(FileNotFoundError):
            path.unlink()


def _process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _display_url(host: str, port: int, markdown_path: str | None = None) -> str:
    """Return a user-friendly URL, mapping bind addresses to localhost."""
    display_host = host
    if host in {"0.0.0.0", "127.0.0.1", "::", "::1"}:
        display_host = "localhost"
    base_url = f"http://{display_host}:{port}"
    if markdown_path:
        return f"{base_url}/{quote(markdown_path, safe='/')}"
    return base_url


def _print_welcome_banner(content_root: Path, url: str, markdown_path: str | None = None) -> None:
    """Print a friendly banner so the user knows where to open the app."""
    click.echo("")
    click.echo("  markpad is ready.")
    click.echo(f"  Serving Markdown from: {content_root}")
    if markdown_path:
        click.echo(f"  Opening Markdown file: {markdown_path}")
    click.echo("")
    click.echo(f"  Open {url} in your browser to:")
    click.echo("    - read your Markdown files with live preview")
    click.echo("    - edit them with instant rendering")
    click.echo("    - translate or improve them with the LLM tools")
    click.echo("")


class RootAwareGroup(click.Group):
    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if _should_route_to_serve(args, self.commands):
            args = ["serve", *args]
        return super().parse_args(ctx, args)


def _should_route_to_serve(args: list[str], commands: dict[str, click.Command]) -> bool:
    if not args or any(arg in commands for arg in args):
        return False
    if "--root" in args:
        return False
    return any(not arg.startswith("-") for arg in args)


@click.group(
    cls=RootAwareGroup,
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
@click.option(
    "--background",
    "-d",
    is_flag=True,
    help="Run the server as a background process. Use 'markpad stop' to terminate it.",
)
@click.pass_context
def main(
    ctx: click.Context,
    host: str,
    port: int | None,
    open_browser: bool,
    root: Path | None,
    background: bool,
) -> None:
    """Start a local Markdown web server with live editing and preview."""
    if ctx.invoked_subcommand is not None:
        return
    start_server(
        root=root,
        host=host,
        port=port,
        open_browser=open_browser,
        background=background,
    )


def start_server(
    *,
    root: Path | None,
    host: str,
    port: int | None,
    open_browser: bool,
    background: bool = False,
) -> None:
    default_root = os.environ.get("MARKPAD_DEFAULT_ROOT")
    target = root or default_root
    try:
        content_root, initial_path = _resolve_startup_target(target)
    except FileNotFoundError:
        click.echo(f"Content target does not exist: {target or Path.cwd()}", err=True)
        raise click.ClickException("Missing content target.") from None

    existing = _read_runtime_info()
    if existing and _process_alive(existing.get("pid", 0)):
        raise click.ClickException(
            f"markpad already running (pid={existing['pid']}) at "
            f"http://{existing.get('host')}:{existing.get('port')}. "
            "Run 'markpad stop' first."
        )

    try:
        selected_port = choose_port(host, port)
    except OSError as exc:
        raise click.ClickException(str(exc)) from exc

    url = _display_url(host, selected_port, initial_path)

    if background:
        _spawn_background(content_root, host, selected_port, open_browser, initial_path)
        return

    _print_welcome_banner(content_root, url, initial_path)
    if open_browser:
        webbrowser.open(url)

    _write_runtime_info(os.getpid(), host, selected_port, content_root)
    try:
        uvicorn.run(
            create_app(content_root),
            host=host,
            port=selected_port,
            log_level="info",
        )
    finally:
        _clear_runtime_info()


def _spawn_background(
    content_root: Path,
    host: str,
    port: int,
    open_browser: bool,
    initial_path: str | None = None,
) -> None:
    log_path = _runtime_dir() / "markpad.log"
    env = os.environ.copy()
    env["MARKPAD_DEFAULT_ROOT"] = str(content_root)
    cmd = [
        sys.executable,
        "-m",
        "markpad",
        "serve",
        "--host",
        host,
        "--port",
        str(port),
        str(content_root),
    ]
    with open(log_path, "ab") as log_file:
        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
            close_fds=True,
        )

    url = _display_url(host, port, initial_path)
    probe_url = f"http://{host}:{port}/api/files"
    deadline = time.time() + 8.0
    ready = False
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        try:
            with httpx.Client(timeout=0.5) as client:
                client.get(probe_url)
            ready = True
            break
        except httpx.HTTPError:
            time.sleep(0.2)

    if proc.poll() is not None:
        raise click.ClickException(
            f"Background server exited early. See log: {log_path}"
        )

    _write_runtime_info(proc.pid, host, port, content_root)
    click.echo(f"markpad started in background (pid={proc.pid})")
    _print_welcome_banner(content_root, url, initial_path)
    click.echo(f"Logs: {log_path}")
    click.echo("Stop with: markpad stop  (or click the Shutdown button in the browser)")
    if not ready:
        click.echo("Note: server did not respond within 8s; it may still be starting.")
    if open_browser:
        webbrowser.open(url)


@main.command()
@click.argument(
    "root",
    required=False,
    type=click.Path(file_okay=True, dir_okay=True, path_type=Path),
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
@click.option(
    "--background",
    "-d",
    is_flag=True,
    help="Run the server as a background process. Use 'markpad stop' to terminate it.",
)
def serve(
    root: Path | None,
    host: str,
    port: int | None,
    open_browser: bool,
    background: bool,
) -> None:
    """Start the Markdown web server."""
    start_server(
        root=root,
        host=host,
        port=port,
        open_browser=open_browser,
        background=background,
    )


def _resolve_startup_target(target: Path | str | None) -> tuple[Path, str | None]:
    if target is None:
        return normalize_root(), None

    resolved = Path(target).expanduser().resolve(strict=True)
    if resolved.is_dir():
        return resolved, None

    if resolved.suffix.lower() not in MARKDOWN_EXTENSIONS:
        raise click.ClickException("Startup file must use a Markdown extension.")

    cwd = Path.cwd().resolve(strict=True)
    try:
        return cwd, to_relative_posix(cwd, resolved)
    except ValueError:
        return resolved.parent, resolved.name


@main.command()
def stop() -> None:
    """Stop a background markpad server started with --background."""
    info = _read_runtime_info()
    if not info:
        raise click.ClickException("No background markpad server is recorded.")
    pid = int(info.get("pid", 0))
    host = info.get("host")
    port = info.get("port")
    if not _process_alive(pid):
        _clear_runtime_info()
        click.echo("No running markpad process. Cleared stale runtime info.")
        return

    # Try the HTTP shutdown endpoint first, then fall back to signals.
    if host and port:
        url = f"http://{host}:{port}/api/shutdown"
        try:
            with httpx.Client(timeout=2.0) as client:
                client.post(url)
        except httpx.HTTPError:
            pass

    deadline = time.time() + 5.0
    while time.time() < deadline and _process_alive(pid):
        time.sleep(0.2)

    if _process_alive(pid):
        with suppress_oserror():
            os.kill(pid, signal.SIGTERM)
        deadline = time.time() + 5.0
        while time.time() < deadline and _process_alive(pid):
            time.sleep(0.2)

    if _process_alive(pid):
        with suppress_oserror():
            os.kill(pid, signal.SIGKILL)

    _clear_runtime_info()
    click.echo(f"Stopped markpad (pid={pid}).")


@main.command()
def status() -> None:
    """Show whether a background markpad server is running."""
    info = _read_runtime_info()
    if not info:
        click.echo("markpad is not running.")
        return
    pid = int(info.get("pid", 0))
    if not _process_alive(pid):
        _clear_runtime_info()
        click.echo("markpad is not running (cleared stale runtime info).")
        return
    click.echo(
        f"markpad is running (pid={pid}) at "
        f"http://{info.get('host')}:{info.get('port')} root={info.get('root')}"
    )


@contextmanager
def suppress_oserror():
    with suppress(ProcessLookupError, OSError):
        yield


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
