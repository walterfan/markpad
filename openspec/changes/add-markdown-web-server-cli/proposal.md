## Why

Markdown-heavy folders need a fast local preview tool that can browse, edit, and render files without leaving the current working tree. Existing static preview flows do not cover recursive indexing, live editing, and diagram rendering in one local CLI.

## What Changes

- Add a CLI command that starts a local web server rooted at the current folder or an explicitly supplied folder.
- Use port `9026` by default and automatically choose `9026 + n` when the default port is occupied.
- Add an install shell script that installs or links the CLI so it can be run from any folder containing Markdown files.
- Add recursive Markdown discovery and an index view for Markdown files in the root and subfolders.
- Add Markdown-to-HTML rendering with a Tailwind-styled live preview/editor workflow.
- Add a split editor/preview layout with controls to hide either pane and resize the pane widths.
- Add safe file read/write behavior for editing Markdown files from the browser.
- Add rendering support for Mermaid and PlantUML code blocks so diagrams appear as images or rendered SVG/HTML instead of raw script blocks.
- Add tests and development commands for server startup, indexing, rendering, editing, and diagram conversion behavior.

## Capabilities

### New Capabilities

- `markdown-web-server-cli`: CLI startup, server binding, root folder selection, and local-only serving defaults.
- `markdown-cli-installation`: shell-script installation flow and post-install command availability.
- `markdown-file-index`: recursive Markdown discovery, index metadata, navigation, and deterministic ordering.
- `markdown-live-editor`: browser-based Markdown reading, editing, saving, and live rendered preview.
- `diagram-block-rendering`: Mermaid and PlantUML block detection and rendering inside Markdown output.

### Modified Capabilities

None. This repo has no accepted specs yet.

## Impact

- Adds Python application source code, Poetry package metadata, install script, test configuration, and developer commands.
- Introduces HTTP routes or equivalent web app endpoints for the index, document content, rendered HTML, save operations, and live updates.
- Introduces Markdown parsing/sanitization and diagram rendering dependencies.
- Requires path traversal protections and local-only defaults because the tool reads and writes files from the user-selected folder.
