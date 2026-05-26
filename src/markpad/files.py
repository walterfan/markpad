from __future__ import annotations

import os
from pathlib import Path

from .models import FileEntry

MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown"}
IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}


class PathOutsideRootError(ValueError):
    """Raised when a requested file path escapes the content root."""


def normalize_root(root: Path | str | None = None) -> Path:
    selected = Path.cwd() if root is None else Path(root)
    return selected.expanduser().resolve(strict=True)


def resolve_markdown_path(root: Path, relative_path: str) -> Path:
    if not relative_path:
        raise PathOutsideRootError("Path is required.")

    requested = Path(relative_path)
    if requested.is_absolute():
        raise PathOutsideRootError("Absolute paths are not allowed.")

    resolved = (root / requested).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PathOutsideRootError("Path escapes the content root.") from exc

    return resolved


def to_relative_posix(root: Path, file_path: Path) -> str:
    return file_path.relative_to(root).as_posix()


def is_markdown_file(file_path: Path) -> bool:
    return file_path.is_file() and file_path.suffix.lower() in MARKDOWN_EXTENSIONS


def should_skip_dir(dir_name: str) -> bool:
    return dir_name in IGNORED_DIRECTORIES


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = [name for name in dir_names if not should_skip_dir(name)]
        current_path = Path(current_root)
        for file_name in file_names:
            file_path = current_path / file_name
            if is_markdown_file(file_path):
                files.append(file_path)
    return sorted(files, key=lambda path: to_relative_posix(root, path).lower())


def build_file_index(root: Path) -> list[FileEntry]:
    entries: list[FileEntry] = []
    for file_path in iter_markdown_files(root):
        stat = file_path.stat()
        relative = to_relative_posix(root, file_path)
        directory = Path(relative).parent.as_posix()
        entries.append(
            FileEntry(
                path=relative,
                name=file_path.name,
                directory="" if directory == "." else directory,
                size=stat.st_size,
                mtime=stat.st_mtime,
            )
        )
    return entries


def read_markdown(root: Path, relative_path: str) -> tuple[str, float]:
    file_path = resolve_markdown_path(root, relative_path)
    if not is_markdown_file(file_path):
        raise FileNotFoundError(relative_path)
    return file_path.read_text(encoding="utf-8"), file_path.stat().st_mtime


def save_markdown(root: Path, relative_path: str, content: str) -> float:
    file_path = resolve_markdown_path(root, relative_path)
    if file_path.suffix.lower() not in MARKDOWN_EXTENSIONS:
        raise FileNotFoundError(relative_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_name(f".{file_path.name}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(file_path)
    return file_path.stat().st_mtime
