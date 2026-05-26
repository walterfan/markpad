## 1. Project Scaffold

- [x] 1.1 Create `pyproject.toml`, `poetry.lock`, pytest config, and source directory layout for CLI, server, shared models, templates, and static browser assets.
- [x] 1.2 Add Poetry scripts and developer commands for `dev`, `test`, `lint`, `format`, and CLI execution.
- [x] 1.3 Add Python dependencies for CLI parsing, HTTP server, websocket/live events, file watching, Markdown parsing, sanitization, diagram rendering integration, Tailwind asset handling, and testing.
- [x] 1.4 Add a minimal `README.md` with install, run, and development command examples.
- [x] 1.5 Update `AGENTS.md` with verified package manager and commands after scripts exist.

## 2. CLI Installation

- [x] 2.1 Implement `install.sh` to check Python 3 and Poetry, install dependencies with `poetry install`, and link or install the CLI command.
- [x] 2.2 Make `install.sh` print the installed command name and a smoke-test command such as `markpad --help`.
- [x] 2.3 Add a CLI `--help` path that works after installation.
- [x] 2.4 Verify the installed CLI can be run from a separate folder that contains Markdown files.
- [x] 2.5 Add tests or scripted checks for install-script failure messages when Python, Poetry, or install steps fail.

## 3. CLI And Server Runtime

- [x] 3.1 Implement CLI options for root directory, host, port, and optional browser-open behavior.
- [x] 3.2 Start the server with the current working directory as the default content root.
- [x] 3.3 Bind to `127.0.0.1` by default and require explicit host configuration for other addresses.
- [x] 3.4 Use port `9026` by default when no explicit port is provided.
- [x] 3.5 If the default port is occupied, choose the next available fallback port using `9026 + n`.
- [x] 3.6 Print the active browser URL with the actual selected port after the server is ready.
- [x] 3.7 Return clear non-zero errors for missing roots and unavailable explicitly requested ports.
- [x] 3.8 Implement centralized root-relative path resolution with traversal and absolute-path rejection tests.

## 4. Markdown File Index

- [x] 4.1 Implement recursive Markdown discovery for `.md`, `.markdown`, and `.mdown` files case-insensitively.
- [x] 4.2 Exclude default generated/dependency directories such as `.git`, `node_modules`, `dist`, and build output.
- [x] 4.3 Return deterministic root-relative ordering for index results.
- [x] 4.4 Include path, display name, directory, size, and last modified time in each index entry.
- [x] 4.5 Add tests for nested files, ignored directories, alternate extensions, and deterministic ordering.

## 5. Markdown Rendering And Live Editor

- [x] 5.1 Implement API routes for listing files, reading Markdown source, rendering Markdown HTML, and saving edited content.
- [x] 5.2 Sanitize rendered HTML before sending it to the browser or injecting it in the UI.
- [x] 5.3 Build the Tailwind-styled browser UI so the server opens to a Markdown file index page.
- [x] 5.4 Open clicked index files into a workspace with editable Markdown source on the left and rendered HTML preview on the right.
- [x] 5.5 Add controls to hide the source pane, hide the preview pane, and restore the split view.
- [x] 5.6 Add a draggable divider to adjust source and preview pane widths with minimum usable widths.
- [x] 5.7 Update preview content live as the user edits without requiring a manual page refresh.
- [x] 5.8 Save full-file edits atomically and reject save requests outside the content root.
- [x] 5.9 Add file watcher events so added, removed, or externally changed Markdown files refresh the index and selected document state.
- [x] 5.10 Add unit and integration tests for open, render, edit, save, missing-file, external-change, split-pane controls, pane resizing, and path-safety behavior.

## 6. Diagram Rendering

- [x] 6.1 Detect fenced `mermaid`, `plantuml`, and `puml` blocks during Markdown rendering.
- [x] 6.2 Render Mermaid blocks in the browser and show per-block errors for invalid Mermaid source.
- [x] 6.3 Implement PlantUML rendering through a configured local command or JAR path with timeout and size limits.
- [x] 6.4 Return PlantUML output as SVG or image data and show a renderer-unavailable message when no renderer is configured.
- [x] 6.5 Preserve Mermaid and PlantUML fenced source exactly in the editor while rendering diagrams in the preview.
- [x] 6.6 Add tests for valid diagrams, invalid diagrams, renderer-unavailable behavior, and mixed valid/invalid diagrams.

## 7. Verification

- [x] 7.1 Run `poetry run ruff check .` and fix reported issues.
- [x] 7.2 Run `poetry run pytest` and ensure CLI, server, indexing, editing, and diagram tests pass.
- [x] 7.3 Run the Poetry-installed CLI entry point and verify it starts from outside the repo.
- [x] 7.4 Run `./install.sh`, then run the installed CLI from a sample Markdown folder.
- [x] 7.5 Manually verify a browser session can index Markdown files, open a clicked file, edit in the left pane, render HTML in the right pane, hide either pane, resize pane widths, save edits, live-refresh preview, and display Mermaid and PlantUML diagrams.
