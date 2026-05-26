## Context

The repo is currently a scaffold with OpenSpec files and no application implementation. The requested product is a local developer tool: install a CLI with a shell script, run that CLI in a folder, open a browser to an index page, browse Markdown files recursively, edit a selected file in a left Markdown pane, and see rendered HTML update live in a right preview pane. Markdown may contain Mermaid or PlantUML code blocks, and those blocks must render as diagrams rather than plain code.

The design must protect local files because the server reads and writes from the user's working tree. It must use Poetry to manage Python dependencies and avoid a large custom framework because the first implementation should be small enough to verify end to end.

## Goals / Non-Goals

**Goals:**

- Provide a CLI that starts a local-only web server from the current directory on port `9026` by default.
- Provide an install shell script that makes the CLI available from arbitrary Markdown folders.
- Index Markdown files under the selected root with deterministic ordering and metadata.
- Render Markdown to sanitized HTML and support live editing/preview.
- Provide a Tailwind-styled split-pane UI where the Markdown source pane and HTML preview pane can be hidden or resized.
- Render Mermaid and PlantUML code blocks into visual diagrams.
- Manage Python dependencies, scripts, and packaging through Poetry.
- Keep the stack conventional and testable for future packaging.

**Non-Goals:**

- Do not build a hosted multi-user documentation platform.
- Do not add authentication, remote sharing, or cloud storage.
- Do not edit files outside the selected root.
- Do not require users to convert Markdown into a proprietary document format.

## Decisions

### Use Python, Poetry, FastAPI, Tailwind CSS, and a lightweight browser UI

Use a Poetry-managed Python package with a FastAPI server and lightweight browser UI:

- `pyproject.toml` and `poetry.lock` for dependency and script management.
- `typer` or `click` for the CLI.
- `fastapi` and `uvicorn` for HTTP routes, static files, and websocket/live events.
- `watchfiles` or `watchdog` for file watching.
- `markdown-it-py` or `pymdown-extensions` for Markdown parsing.
- `bleach` or an equivalent sanitizer for rendered HTML.
- Tailwind CSS for the browser UI styling.
- Plain HTML/JavaScript for the first browser UI behavior, served by FastAPI static/template routes.

Rationale: Poetry gives a reproducible Python environment and an installable CLI, while FastAPI provides explicit route contracts, websocket support, and straightforward testing. Tailwind keeps the split-pane UI consistent without a large component framework.

Alternatives considered:

- Python + Streamlit: fastest to prototype, but weaker for custom split-pane editing, route contracts, and filesystem save semantics.
- Python + FastAPI + Vue: viable later, but introduces npm/Vite alongside Poetry for the first implementation.
- TypeScript + Node + Vue: strong browser tooling, but conflicts with the requested Poetry-managed Python dependency model.

### Use port 9026 with incremental fallback

The CLI uses port `9026` by default. If `9026` is unavailable and the user did not explicitly request a port, the server tries `9027`, then `9028`, continuing as `9026 + n` until it finds a free port within a bounded retry range. If the user explicitly passes `--port`, the CLI uses that port and reports a clear error if it is unavailable.

Rationale: the default port is predictable, while automatic fallback avoids startup failure during local development when another instance is already running.

### Provide an install shell script for local CLI setup

Add `install.sh` at the repo root. The script checks for Python 3 and Poetry, runs `poetry install`, and links or installs the CLI command into a user-writable location. It must print the installed command name and a smoke-test command such as `markpad --help`.

Rationale: the user wants to run the tool from any folder containing Markdown files without remembering project-internal Poetry commands.

Alternatives considered:

- Documenting `poetry run markpad`: useful for contributors but does not satisfy installed CLI usage from arbitrary folders.
- Publishing directly to PyPI first: useful later, but unnecessary for local iteration.

### Serve localhost by default and require explicit opt-in for external binding

The server binds to `127.0.0.1` by default. A user may pass `--host` to override the bind address, but the CLI must make external binding explicit.

Rationale: Markdown folders may contain private notes or credentials, and the tool should not expose them on the network by accident.

### Use root-relative paths and strict path resolution

All API calls identify files by normalized POSIX-style paths relative to the selected root. The server resolves every requested path against the root and rejects paths that escape it after symlink and `..` normalization.

Rationale: this gives the UI stable IDs while preventing path traversal and unintended reads or writes.

### Render Mermaid client-side and PlantUML server-side

Mermaid blocks render in the browser using the Mermaid library because it naturally emits SVG in the DOM and can update with the preview. PlantUML blocks render through a server-side renderer because PlantUML commonly depends on Java or a command/JAR process. The first implementation should support a configured local PlantUML command or JAR path and return SVG or PNG data to the browser. If PlantUML rendering is unavailable or fails, the preview displays a visible diagram error block with the underlying stderr or validation message.

Rationale: Mermaid works best in the browser; PlantUML needs controlled process execution and clear error handling.

### Save full-file edits through an explicit API

The editor sends full Markdown content to a save endpoint for the selected file. The server writes atomically by writing a temporary file in the same directory and renaming it over the target when possible.

Rationale: full-file saves are simpler to reason about than patch streams, and atomic writes reduce the risk of truncated files.

### Use an index-first shell with resizable editor and preview panes

The browser opens to an index page that lists Markdown files discovered under the root. Selecting a file opens a work area with Markdown source on the left and rendered HTML preview on the right. The UI includes controls to hide the source pane, hide the preview pane, restore both panes, and drag a divider to adjust their relative widths.

Rationale: the index makes navigation obvious, while a resizable split view supports both editing-focused and reading-focused workflows.

## Risks / Trade-offs

- Path traversal or symlink escape could expose private files -> centralize path resolution and test escape attempts.
- Browser preview could execute unsafe HTML -> sanitize rendered HTML before injecting it and render diagrams through controlled components.
- PlantUML process execution could be slow or unsafe -> apply timeouts, size limits, and no shell interpolation.
- Large folders could make indexing slow -> ignore common heavy directories and expose refresh/focused search behavior.
- Pane state could become awkward on small screens -> enforce minimum pane widths and provide one-pane modes.
- Port fallback could hide an already-running instance -> always print the actual selected port and URL.
- External file edits could race with browser saves -> track file `mtime` or content hash and warn before overwriting changed content.
- Mermaid and PlantUML errors could break the whole preview -> isolate each diagram block and show per-block errors.

## Migration Plan

1. Scaffold the Poetry Python package, CLI entry point, FastAPI server, tests, and static browser UI.
2. Add `install.sh` and verify the installed CLI can run `--help` from outside the repo.
3. Implement port selection, root resolution, Markdown indexing, and read-only preview routes.
4. Add editor save behavior and live file watcher events.
5. Add Mermaid rendering and PlantUML rendering with tests for success and failure cases.
6. Update `AGENTS.md` with verified Poetry commands and Python version.

Rollback is straightforward during initial development: remove the Poetry package scaffold or disable diagram rendering behind feature flags if renderer dependencies block the base server.

## Open Questions

- Should PlantUML support require a local `plantuml` command, a configured JAR path, or both?
- Should the editor support autosave in the first release, or only explicit save?
- Which directories should be ignored by default beyond `.git`, `node_modules`, and build output?
