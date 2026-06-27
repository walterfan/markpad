from __future__ import annotations

import asyncio
import json
import os
import signal
from collections.abc import AsyncIterator
from contextlib import suppress
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from watchfiles import awatch

from .files import (
    PathOutsideRootError,
    build_file_index,
    create_markdown,
    delete_markdown_target,
    read_absolute_markdown,
    read_markdown,
    resolve_markdown_path,
    save_absolute_markdown,
    save_markdown,
)
from .models import (
    AbsoluteFileContent,
    AppConfigResponse,
    CreateFileRequest,
    DeleteFileRequest,
    DeleteFileResponse,
    EditRequest,
    EditResponse,
    FileContent,
    RenderRequest,
    RenderResponse,
    SaveRequest,
    SaveResponse,
    TranslateRequest,
    TranslateResponse,
)
from .renderer import render_markdown


def create_app(root: Path) -> FastAPI:
    content_root = root.resolve(strict=True)
    app = FastAPI(title="markpad")
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.state.content_root = content_root

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return (static_dir / "index.html").read_text(encoding="utf-8")

    @app.get("/api/files")
    async def list_files() -> list[dict[str, object]]:
        return [entry.model_dump() for entry in build_file_index(content_root)]

    @app.post("/api/files", response_model=SaveResponse)
    async def create_file(request: CreateFileRequest) -> SaveResponse:
        try:
            path, mtime = create_markdown(
                content_root,
                request.directory,
                request.name,
                request.content,
            )
        except (PathOutsideRootError, NotADirectoryError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return SaveResponse(path=path, mtime=mtime)

    @app.delete("/api/files", response_model=DeleteFileResponse)
    async def delete_file(request: DeleteFileRequest) -> DeleteFileResponse:
        try:
            path = delete_markdown_target(content_root, request.type, request.path)
        except (PathOutsideRootError, NotADirectoryError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return DeleteFileResponse(path=path, type=request.type)

    @app.get("/api/config", response_model=AppConfigResponse)
    async def get_config() -> AppConfigResponse:
        config = _llm_config(content_root)
        return AppConfigResponse(
            translate_available=config is not None,
            llm_model=config["model"] if config else None,
        )

    @app.get("/api/file", response_model=FileContent)
    async def get_file(path: str) -> FileContent:
        try:
            content, mtime = read_markdown(content_root, path)
        except (FileNotFoundError, PathOutsideRootError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return FileContent(path=path, content=content, mtime=mtime)

    @app.get("/api/absolute-file", response_model=AbsoluteFileContent)
    async def get_absolute_file(path: str) -> AbsoluteFileContent:
        try:
            content, mtime, resolved_path = read_absolute_markdown(path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return AbsoluteFileContent(path=resolved_path, content=content, mtime=mtime)

    @app.post("/api/render", response_model=RenderResponse)
    async def render(request: RenderRequest) -> RenderResponse:
        return RenderResponse(html=render_markdown(request.content))

    @app.post("/api/translate", response_model=TranslateResponse)
    async def translate(request: TranslateRequest) -> TranslateResponse:
        config = _llm_config(content_root)
        if config is None:
            raise HTTPException(
                status_code=503,
                detail="Translation requires LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY.",
            )
        content = await translate_with_llm(
            config=config,
            content=request.content,
            target_language=request.target_language,
        )
        return TranslateResponse(content=content)

    @app.post("/api/translate/stream")
    async def translate_stream(request: TranslateRequest) -> StreamingResponse:
        config = _llm_config(content_root)
        if config is None:
            raise HTTPException(
                status_code=503,
                detail="Translation requires LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY.",
            )
        stream = await stream_translation_with_llm(
            config=config,
            content=request.content,
            target_language=request.target_language,
        )
        return StreamingResponse(stream, media_type="text/plain; charset=utf-8")

    @app.post("/api/edit", response_model=EditResponse)
    async def edit(request: EditRequest) -> EditResponse:
        config = _llm_config(content_root)
        if config is None:
            raise HTTPException(
                status_code=503,
                detail="LLM editing requires LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY.",
            )
        content = await edit_markdown_with_llm(
            config=config,
            content=request.content,
            instruction=request.instruction,
        )
        return EditResponse(content=content)

    @app.post("/api/edit/stream")
    async def edit_stream(request: EditRequest) -> StreamingResponse:
        config = _llm_config(content_root)
        if config is None:
            raise HTTPException(
                status_code=503,
                detail="LLM editing requires LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY.",
            )
        stream = await stream_edit_markdown_with_llm(
            config=config,
            content=request.content,
            instruction=request.instruction,
        )
        return StreamingResponse(stream, media_type="text/plain; charset=utf-8")

    @app.post("/api/file", response_model=SaveResponse)
    async def save_file(request: SaveRequest) -> SaveResponse:
        try:
            mtime = save_markdown(content_root, request.path, request.content)
        except PathOutsideRootError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return SaveResponse(path=request.path, mtime=mtime)

    @app.post("/api/absolute-file", response_model=SaveResponse)
    async def save_absolute_file(request: SaveRequest) -> SaveResponse:
        try:
            mtime, resolved_path = save_absolute_markdown(request.path, request.content)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return SaveResponse(path=resolved_path, mtime=mtime)

    @app.post("/api/shutdown")
    async def shutdown() -> JSONResponse:
        """Gracefully stop the running uvicorn server process."""
        loop = asyncio.get_running_loop()
        loop.call_later(0.25, _trigger_shutdown)
        return JSONResponse({"status": "stopping", "pid": os.getpid()})

    @app.websocket("/ws")
    async def websocket_updates(websocket: WebSocket) -> None:
        await websocket.accept()
        watch_task = asyncio.create_task(_watch_and_send(content_root, websocket))
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            watch_task.cancel()
            with suppress(asyncio.CancelledError):
                await watch_task

    @app.get("/{requested_path:path}", response_class=HTMLResponse)
    async def markdown_deep_link(requested_path: str) -> str:
        if requested_path.startswith(("api/", "static/")):
            raise HTTPException(status_code=404, detail="Not found")
        return (static_dir / "index.html").read_text(encoding="utf-8")

    return app


def ensure_path_allowed(root: Path, relative_path: str) -> Path:
    return resolve_markdown_path(root.resolve(strict=True), relative_path)


def _trigger_shutdown() -> None:
    """Send SIGTERM to the current process so uvicorn shuts down cleanly."""
    with suppress(ProcessLookupError, OSError):
        os.kill(os.getpid(), signal.SIGTERM)


def _llm_config(root: Path) -> dict[str, str] | None:
    env_file = _read_dotenv(root / ".env")
    config = {
        "base_url": os.environ.get("LLM_BASE_URL") or env_file.get("LLM_BASE_URL", ""),
        "model": os.environ.get("LLM_MODEL") or env_file.get("LLM_MODEL", ""),
        "api_key": os.environ.get("LLM_API_KEY") or env_file.get("LLM_API_KEY", ""),
    }
    if all(config.values()):
        return config
    return None


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


async def translate_with_llm(
    *,
    config: dict[str, str],
    content: str,
    target_language: str,
) -> str:
    payload = _translation_payload(
        model=config["model"],
        content=content,
        target_language=target_language,
    )
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                _chat_completions_url(config["base_url"]),
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=_llm_http_error_detail(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"LLM translation failed: {exc}") from exc

    data = response.json()
    try:
        translated = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="LLM translation response was invalid.",
        ) from exc
    if not isinstance(translated, str):
        raise HTTPException(status_code=502, detail="LLM translation response was invalid.")
    return translated


def _translation_payload(
    *,
    model: str,
    content: str,
    target_language: str,
    stream: bool = False,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Translate Markdown into the requested language. Preserve Markdown "
                    "structure, code blocks, front matter, links, tables, and diagram code. "
                    "Return only the translated Markdown."
                ),
            },
            {
                "role": "user",
                "content": f"Target language: {target_language}\n\nMarkdown:\n{content}",
            },
        ],
    }
    if stream:
        payload["stream"] = True
    return payload


async def edit_markdown_with_llm(
    *,
    config: dict[str, str],
    content: str,
    instruction: str,
) -> str:
    payload = _edit_payload(
        model=config["model"],
        content=content,
        instruction=instruction,
    )
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                _chat_completions_url(config["base_url"]),
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=_llm_http_error_detail(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"LLM editing failed: {exc}") from exc

    data = response.json()
    try:
        edited = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="LLM editing response was invalid.",
        ) from exc
    if not isinstance(edited, str):
        raise HTTPException(status_code=502, detail="LLM editing response was invalid.")
    return edited


def _edit_payload(
    *,
    model: str,
    content: str,
    instruction: str,
    stream: bool = False,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Edit the provided Markdown according to the user's instruction. "
                    "Preserve Markdown structure, front matter, links, tables, code blocks, "
                    "and diagram code unless the instruction explicitly asks to change them. "
                    "Return only the edited Markdown."
                ),
            },
            {
                "role": "user",
                "content": f"Instruction:\n{instruction}\n\nMarkdown:\n{content}",
            },
        ],
    }
    if stream:
        payload["stream"] = True
    return payload


async def stream_edit_markdown_with_llm(
    *,
    config: dict[str, str],
    content: str,
    instruction: str,
) -> AsyncIterator[str]:
    payload = _edit_payload(
        model=config["model"],
        content=content,
        instruction=instruction,
        stream=True,
    )
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    client = httpx.AsyncClient(timeout=60)
    try:
        request = client.build_request(
            "POST",
            _chat_completions_url(config["base_url"]),
            headers=headers,
            json=payload,
        )
        response = await client.send(request, stream=True)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        await client.aclose()
        raise HTTPException(status_code=502, detail=_llm_http_error_detail(exc)) from exc
    except httpx.HTTPError as exc:
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"LLM editing failed: {exc}") from exc

    return _iter_translation_stream(response, client)


async def stream_translation_with_llm(
    *,
    config: dict[str, str],
    content: str,
    target_language: str,
) -> AsyncIterator[str]:
    payload = _translation_payload(
        model=config["model"],
        content=content,
        target_language=target_language,
        stream=True,
    )
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    client = httpx.AsyncClient(timeout=60)
    try:
        request = client.build_request(
            "POST",
            _chat_completions_url(config["base_url"]),
            headers=headers,
            json=payload,
        )
        response = await client.send(request, stream=True)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        await client.aclose()
        raise HTTPException(status_code=502, detail=_llm_http_error_detail(exc)) from exc
    except httpx.HTTPError as exc:
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"LLM translation failed: {exc}") from exc

    return _iter_translation_stream(response, client)


async def _iter_translation_stream(
    response: httpx.Response,
    client: httpx.AsyncClient,
) -> AsyncIterator[str]:
    try:
        async for line in response.aiter_lines():
            if line.strip() == "data: [DONE]":
                break
            delta = _stream_delta_from_line(line)
            if delta:
                yield delta
    finally:
        await response.aclose()
        await client.aclose()


def _stream_delta_from_line(line: str) -> str:
    stripped = line.strip()
    if not stripped.startswith("data:"):
        return ""
    data = stripped.removeprefix("data:").strip()
    if not data or data == "[DONE]":
        return ""
    try:
        payload = json.loads(data)
        delta = payload["choices"][0].get("delta", {})
        content = delta.get("content", "")
    except (json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
        return ""
    return content if isinstance(content, str) else ""


def _llm_http_error_detail(exc: httpx.HTTPStatusError) -> str:
    response = exc.response
    detail = f"LLM translation failed: {response.status_code} {response.reason_phrase}"
    body = response.text.strip()
    if body:
        if len(body) > 500:
            body = f"{body[:500]}..."
        detail = f"{detail}: {body}"
    return detail


async def _watch_and_send(root: Path, websocket: WebSocket) -> None:
    async for changes in awatch(root):
        payload = [
            {
                "change": change.name,
                "path": path,
            }
            for change, path in changes
            if _is_markdown_event(root, Path(path))
        ]
        if payload:
            await websocket.send_json({"type": "files-changed", "changes": payload})
        await asyncio.sleep(0)


def _is_markdown_event(root: Path, path: Path) -> bool:
    try:
        relative = path.resolve(strict=False).relative_to(root)
    except ValueError:
        return False
    return relative.suffix.lower() in {".md", ".markdown", ".mdown"}
