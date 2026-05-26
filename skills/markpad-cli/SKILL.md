---
name: markpad-cli
description: Use when the user wants to install, run, debug, publish, or extend markpad, a Poetry-managed Python CLI for serving local Markdown files with indexing, live editing, preview, Mermaid rendering, and LLM translation.
version: 1.0.0
repository: https://github.com/walterfan/markpad
tags:
  - markdown
  - cli
  - fastapi
  - poetry
  - llm-translation
---

# markpad CLI

Use this skill for tasks involving the `markpad` local Markdown editor/reader/translator on the web.

## When To Use

Invoke this skill when the user asks to:

- Install or run the `markpad` CLI.
- Start, debug, or configure the local Markdown web server.
- Work on Markdown indexing, rendering, live editing, Mermaid diagrams, or LLM translation.
- Change project code, tests, packaging, or installation behavior for this repository.

## Project Shape

`markpad` is a Python 3.11+ Poetry project. It serves Markdown files from a local root directory, renders HTML previews, supports live editing, watches file changes, renders Mermaid diagrams, and can translate Markdown through an OpenAI-compatible LLM gateway.

## Common Commands

Run commands from the repository root:

```bash
poetry install
poetry run markpad --help
poetry run markpad
poetry run markpad --root /path/to/notes --port 9526
poetry run pytest
poetry run ruff check .
./install.sh
```

The installed wrapper exposes `markpad` from `~/.local/bin/markpad` and preserves the folder where the user invokes it.

## Runtime Configuration

- Default host: `127.0.0.1`
- Default port: `9526`, with automatic fallback when unavailable
- Default content root: current working directory, unless `--root` or `MARKPAD_DEFAULT_ROOT` is set
- LLM translation requires `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` from the shell environment or a `.env` file in the served root

`LLM_BASE_URL` may point to an OpenAI-compatible `/v1` base URL or directly to `/chat/completions`.

## Implementation Guardrails

- Keep the server local-first by default.
- Serve only files inside the selected root directory.
- Preserve Markdown source exactly during edits.
- Use the maintained Markdown renderer and sanitizer already in the repo.
- Add tests before changing save, path traversal, file watching, websocket, or LLM streaming behavior.
- Keep the file index deterministic.

## Verification

Before claiming a code change works, run the focused tests for the touched area and prefer a full verification pass:

```bash
poetry run pytest
poetry run ruff check .
```

If dependencies are missing, run `poetry install` first.
