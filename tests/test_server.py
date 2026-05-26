from __future__ import annotations

from pathlib import Path

import httpx
from fastapi.testclient import TestClient

import markpad.server as server
from markpad.server import create_app


def test_api_lists_opens_renders_and_saves_markdown(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text("# Old", encoding="utf-8")
    client = TestClient(create_app(tmp_path))

    files = client.get("/api/files")
    assert files.status_code == 200
    assert files.json()[0]["path"] == "note.md"

    opened = client.get("/api/file", params={"path": "note.md"})
    assert opened.status_code == 200
    assert opened.json()["content"] == "# Old"

    rendered = client.post("/api/render", json={"content": "# New"})
    assert rendered.status_code == 200
    assert "<h1>New</h1>" in rendered.json()["html"]

    saved = client.post("/api/file", json={"path": "note.md", "content": "# Saved"})
    assert saved.status_code == 200
    assert note.read_text(encoding="utf-8") == "# Saved"


def test_api_rejects_path_escape(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.get("/api/file", params={"path": "../secret.md"})

    assert response.status_code == 404


def test_api_reports_translate_config_from_dotenv(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "LLM_BASE_URL=http://llm.example/v1",
                "LLM_MODEL=test-model",
                "LLM_API_KEY=test-key",
            ]
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(tmp_path))

    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.json() == {"translate_available": True, "llm_model": "test-model"}


def test_api_rejects_translate_without_llm_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    client = TestClient(create_app(tmp_path))

    response = client.post("/api/translate", json={"content": "Hello"})

    assert response.status_code == 503


def test_api_translates_with_llm_config(tmp_path: Path, monkeypatch) -> None:
    async def fake_translate_with_llm(*, config, content, target_language):
        assert config["base_url"] == "http://llm.example/v1"
        assert config["model"] == "test-model"
        assert config["api_key"] == "test-key"
        assert target_language == "Chinese"
        return f"translated: {content}"

    monkeypatch.setenv("LLM_BASE_URL", "http://llm.example/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr(server, "translate_with_llm", fake_translate_with_llm)
    client = TestClient(create_app(tmp_path))

    response = client.post("/api/translate", json={"content": "# Hello"})

    assert response.status_code == 200
    assert response.json() == {"content": "translated: # Hello"}


def test_api_streams_translation_with_llm_config(tmp_path: Path, monkeypatch) -> None:
    async def fake_stream():
        for chunk in ("# ", "Ni hao"):
            yield chunk

    async def fake_stream_translation_with_llm(*, config, content, target_language):
        assert config["base_url"] == "http://llm.example/v1"
        assert config["model"] == "test-model"
        assert config["api_key"] == "test-key"
        assert target_language == "Chinese"
        assert content == "# Hello"
        return fake_stream()

    monkeypatch.setenv("LLM_BASE_URL", "http://llm.example/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr(server, "stream_translation_with_llm", fake_stream_translation_with_llm)
    client = TestClient(create_app(tmp_path))

    response = client.post("/api/translate/stream", json={"content": "# Hello"})

    assert response.status_code == 200
    assert response.text == "# Ni hao"


def test_translation_payload_uses_minimal_chat_completion_schema() -> None:
    payload = server._translation_payload(
        model="test-model",
        content="# Hello",
        target_language="Chinese",
    )

    assert payload["model"] == "test-model"
    assert "temperature" not in payload
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1] == {
        "role": "user",
        "content": "Target language: Chinese\n\nMarkdown:\n# Hello",
    }

    stream_payload = server._translation_payload(
        model="test-model",
        content="# Hello",
        target_language="Chinese",
        stream=True,
    )
    assert stream_payload["stream"] is True


def test_stream_delta_from_openai_compatible_sse_line() -> None:
    line = 'data: {"choices":[{"delta":{"content":"hello"}}]}'

    assert server._stream_delta_from_line(line) == "hello"
    assert server._stream_delta_from_line("data: [DONE]") == ""
    assert server._stream_delta_from_line(": ping") == ""


def test_llm_http_error_detail_includes_gateway_body() -> None:
    request = httpx.Request("POST", "http://llm.example/v1/chat/completions")
    response = httpx.Response(
        400,
        json={"error": "unsupported parameter: temperature"},
        request=request,
    )
    exc = httpx.HTTPStatusError("bad request", request=request, response=response)

    detail = server._llm_http_error_detail(exc)

    assert "400 Bad Request" in detail
    assert "unsupported parameter: temperature" in detail


def test_index_serves_tailwind_split_pane_ui(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "Markdown Reader" in response.text
    assert "v1.0 - Local Markdown index, editor, preview, and diagram renderer" in response.text
    assert "app-title-main" in response.text
    assert "app-title-meta" in response.text
    assert "cdn.tailwindcss.com" in response.text
    assert "Author: Walter Fan" in response.text
    assert "Copyright 2026 Walter Fan" in response.text
    assert "status-attribution" in response.text
    assert "status-metrics" in response.text
    assert "total-files" in response.text
    assert "char-count" in response.text
    assert "Theme" in response.text
    assert "Eye-friendly Theme" not in response.text
    assert "theme-dialog" in response.text
    assert "open-theme-settings" in response.text
    assert "Theme Settings" in response.text
    assert "translate" in response.text
    assert "Translate" in response.text
    assert 'data-theme="clear"' in response.text
    assert 'data-theme="paper"' in response.text
    assert 'data-theme="dark"' in response.text
    assert "app-layout" in response.text
    assert "sidebar" in response.text
    assert "toggle-sidebar" in response.text
    assert "toggle-editor" in response.text
    assert "toggle-preview" in response.text
    assert "Toggle file pane" in response.text
    assert "Toggle Markdown pane" in response.text
    assert "Toggle HTML pane" in response.text
    assert "file-tree" in response.text
    assert "editor-pane" in response.text
    assert "preview-pane" in response.text
    assert "overflow-y-auto" in response.text
    assert "min-h-0 min-w-0 flex-col" in response.text
    assert "divider" in response.text

    app_js = client.get("/static/app.js")
    assert app_js.status_code == 200
    assert "buildFileTree" in app_js.text
    assert "renderTreeNode" in app_js.text
    assert "toggleSidebar" in app_js.text
    assert "toggleEditorPane" in app_js.text
    assert "togglePreviewPane" in app_js.text
    assert "markpad.sidebarHidden" in app_js.text
    assert "markpad.editorHidden" in app_js.text
    assert "markpad.previewHidden" in app_js.text
    assert "markpad.theme" in app_js.text
    assert "loadServerConfig" in app_js.text
    assert "/api/translate" in app_js.text
    assert "/api/translate/stream" in app_js.text
    assert "TextDecoder" in app_js.text
    assert "selectionStart" in app_js.text
    assert "Charter" in app_js.text
    assert "folder-button" in app_js.text

    styles = client.get("/static/styles.css")
    assert styles.status_code == 200
    assert "overflow-y: scroll" in styles.text
    assert "scrollbar-gutter: stable" in styles.text
    assert "#preview::-webkit-scrollbar" in styles.text
    assert "#preview h1" in styles.text
    assert "#preview h6" in styles.text
    assert "font-size: 2.1em" in styles.text
    assert "font-weight: 700" in styles.text
    assert ".settings-dialog" in styles.text
    assert ".theme-option" in styles.text
