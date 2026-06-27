from __future__ import annotations

import json

from click.testing import CliRunner

import markpad.cli as cli
from markpad.cli import main
from markpad.ports import DEFAULT_PORT


def test_cli_help_lists_operational_commands() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "doctor" in result.output
    assert "serve" in result.output
    assert "--root" in result.output


def test_cli_routes_first_argument_to_server_root(tmp_path, monkeypatch) -> None:
    captured = {}

    def fake_start_server(*, root, host, port, open_browser, background=False):
        captured["root"] = root
        captured["host"] = host
        captured["port"] = port
        captured["open_browser"] = open_browser
        captured["background"] = background

    monkeypatch.setattr(cli, "start_server", fake_start_server)

    result = CliRunner().invoke(main, [str(tmp_path)])

    assert result.exit_code == 0
    assert captured == {
        "root": tmp_path,
        "host": "127.0.0.1",
        "port": None,
        "open_browser": False,
        "background": False,
    }


def test_cli_resolves_markdown_file_target_under_current_directory(tmp_path, monkeypatch) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    note = docs / "guide.md"
    note.write_text("# Guide", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    content_root, initial_path = cli._resolve_startup_target(note)

    assert content_root == tmp_path
    assert initial_path == "docs/guide.md"


def test_cli_resolves_markdown_file_target_outside_current_directory(tmp_path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    note = docs / "guide.md"
    note.write_text("# Guide", encoding="utf-8")

    content_root, initial_path = cli._resolve_startup_target(note)

    assert content_root == docs
    assert initial_path == "guide.md"


def test_cli_display_url_includes_encoded_markdown_path() -> None:
    url = cli._display_url("127.0.0.1", 9526, "docs/My Note.md")

    assert url == "http://localhost:9526/docs/My%20Note.md"


def test_cli_without_folder_uses_default_current_root(monkeypatch) -> None:
    captured = {}

    def fake_start_server(*, root, host, port, open_browser, background=False):
        captured["root"] = root

    monkeypatch.delenv("MARKPAD_DEFAULT_ROOT", raising=False)
    monkeypatch.setattr(cli, "start_server", fake_start_server)

    result = CliRunner().invoke(main, [])

    assert result.exit_code == 0
    assert captured == {"root": None}


def test_cli_background_flag_propagates(tmp_path, monkeypatch) -> None:
    captured = {}

    def fake_start_server(*, root, host, port, open_browser, background=False):
        captured["root"] = root
        captured["background"] = background

    monkeypatch.setattr(cli, "start_server", fake_start_server)

    result = CliRunner().invoke(main, ["serve", str(tmp_path), "--background"])

    assert result.exit_code == 0, result.output
    assert captured == {"root": tmp_path, "background": True}


def test_doctor_reports_runtime_config_without_llm(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    result = CliRunner().invoke(main, ["doctor", str(tmp_path), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["content_root"] == str(tmp_path)
    assert payload["default_port"] == DEFAULT_PORT
    assert payload["translate_available"] is False
    assert payload["llm_model"] is None


def test_doctor_reports_dotenv_llm_config(tmp_path, monkeypatch) -> None:
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

    result = CliRunner().invoke(main, ["doctor", str(tmp_path), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["translate_available"] is True
    assert payload["llm_model"] == "test-model"
    assert payload["llm_config_source"] == str(tmp_path / ".env")
