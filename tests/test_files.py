from __future__ import annotations

from pathlib import Path

import pytest

from markpad.files import (
    PathOutsideRootError,
    build_file_index,
    create_markdown,
    delete_markdown_target,
    read_absolute_markdown,
    read_markdown,
    resolve_markdown_path,
    save_absolute_markdown,
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


def test_absolute_markdown_can_be_read_and_saved(tmp_path: Path) -> None:
    note = tmp_path / "absolute.md"
    note.write_text("# Old", encoding="utf-8")

    content, mtime, resolved_path = read_absolute_markdown(str(note))

    assert content == "# Old"
    assert mtime > 0
    assert resolved_path == str(note)

    saved_mtime, saved_path = save_absolute_markdown(str(note), "# Saved")

    assert saved_mtime > 0
    assert saved_path == str(note)
    assert note.read_text(encoding="utf-8") == "# Saved"


def test_absolute_markdown_rejects_relative_and_non_markdown_paths(tmp_path: Path) -> None:
    plain = tmp_path / "plain.txt"
    plain.write_text("plain", encoding="utf-8")

    with pytest.raises(ValueError, match="Absolute path is required"):
        read_absolute_markdown("note.md")

    with pytest.raises(ValueError, match="Markdown extension"):
        read_absolute_markdown(str(plain))


def test_create_markdown_creates_file_in_existing_directory(tmp_path: Path) -> None:
    (tmp_path / "notes").mkdir()

    path, mtime = create_markdown(tmp_path, "notes", "draft", "# Draft")

    assert path == "notes/draft.md"
    assert mtime > 0
    assert (tmp_path / "notes" / "draft.md").read_text(encoding="utf-8") == "# Draft"


def test_create_markdown_rejects_overwrite_and_nested_name(tmp_path: Path) -> None:
    (tmp_path / "existing.md").write_text("# Existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        create_markdown(tmp_path, "", "existing.md")

    with pytest.raises(ValueError, match="must not include directories"):
        create_markdown(tmp_path, "", "nested/file.md")


def test_delete_markdown_target_removes_file_and_folder(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    folder = tmp_path / "notes"
    folder.mkdir()
    nested = folder / "nested.md"
    plain = folder / "plain.txt"
    note.write_text("# Note", encoding="utf-8")
    nested.write_text("# Nested", encoding="utf-8")
    plain.write_text("plain", encoding="utf-8")

    assert delete_markdown_target(tmp_path, "file", "note.md") == "note.md"
    assert not note.exists()

    assert delete_markdown_target(tmp_path, "folder", "notes") == "notes"
    assert not folder.exists()


def test_delete_markdown_target_rejects_root_and_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Root folder cannot be deleted"):
        delete_markdown_target(tmp_path, "folder", "")

    with pytest.raises(PathOutsideRootError):
        delete_markdown_target(tmp_path, "folder", "../outside")
