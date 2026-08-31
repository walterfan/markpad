from __future__ import annotations

from pathlib import Path


def test_install_script_documents_prerequisites() -> None:
    script = Path("install.sh").read_text(encoding="utf-8")

    assert "python3.13 python3.12 python3.11 python3" in script
    assert "command -v uv" in script
    assert "uv sync" in script
    assert "uv build" in script
    assert "uv pip install" in script
    assert ".local/share" in script
    assert "uninstall" in script
    assert "MARKPAD_DEFAULT_ROOT" in script
    assert "${APP_NAME} doctor" in script
    assert "${APP_NAME} --help" in script
