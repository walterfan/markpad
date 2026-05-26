from __future__ import annotations

import json

from click.testing import CliRunner

from markpad.cli import main
from markpad.ports import DEFAULT_PORT


def test_cli_help_lists_operational_commands() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "doctor" in result.output
    assert "serve" in result.output
    assert "--root" in result.output


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
