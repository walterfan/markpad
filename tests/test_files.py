from __future__ import annotations

from pathlib import Path

import pytest

from markpad.files import (
    PathOutsideRootError,
    build_file_index,
    read_markdown,
    resolve_markdown_path,
)


def test_build_file_index_is_recursive_and_deterministic(tmp_path: Path) -> None:
    (tmp_path / "b").mkdir()
    (tmp_path / "a").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "b" / "Guide.MD").write_text("# B", encoding="utf-8")
    (tmp_path / "a" / "notes.markdown").write_text("# A", encoding="utf-8")
    (tmp_path / "plain.txt").write_text("no", encoding="utf-8")
    (tmp_path / "node_modules" / "ignored.md").write_text("no", encoding="utf-8")

    entries = build_file_index(tmp_path)

    assert [entry.path for entry in entries] == ["a/notes.markdown", "b/Guide.MD"]
    assert entries[0].name == "notes.markdown"
    assert entries[0].directory == "a"
    assert entries[0].size > 0
    assert entries[0].mtime > 0


def test_resolve_markdown_path_rejects_escape(tmp_path: Path) -> None:
    with pytest.raises(PathOutsideRootError):
        resolve_markdown_path(tmp_path, "../secret.md")

    with pytest.raises(PathOutsideRootError):
        resolve_markdown_path(tmp_path, "/tmp/secret.md")


def test_read_markdown_rejects_non_markdown(tmp_path: Path) -> None:
    (tmp_path / "plain.txt").write_text("no", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        read_markdown(tmp_path, "plain.txt")
