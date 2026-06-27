# AGENTS.md - markpad

<!-- This file follows the open agents.md standard: https://agents.md -->
<!-- It is the predictable entry point that coding agents and human contributors read before working on this repo. -->

`markpad` is a local Markdown editor/reader/translator on the web. It indexes Markdown files in the current folder and subfolders, renders them to HTML, and supports live editing with live preview.

> **Audience:** coding agents and human developers making their first change here.
> Read this file first, then use the linked OpenSpec files when a change needs design context.

## 1. What This Project Is

This repo implements a Poetry-managed Python CLI for a local Markdown web server. Keep it as a small developer tool that can:

- Start a local web server from the current working directory, using port `9526` by default.
- Discover and index `*.md` files recursively.
- Render Markdown to HTML with predictable styling.
- Support live editing and live preview without manual refresh.
- Style the browser UI with Tailwind CSS.
- Keep implementation details simple enough for local development and future packaging.

Key facts:

- **Language / runtime:** Python 3.11+
- **Package manager:** Poetry (`pyproject.toml`, `poetry.lock`)
- **Task runner:** Poetry commands
- **Primary entry point:** `markpad`

## 2. Repository Layout

```text
.
├── .claude/              # Claude Code commands and OpenSpec skills
├── .codex/               # Codex-local OpenSpec skills
├── .cursor/              # Cursor commands and OpenSpec skills
├── src/markpad/          # CLI, FastAPI server, Markdown renderer, static UI
├── tests/                # pytest coverage for CLI support modules, APIs, renderer, install script
├── openspec/             # Spec-driven change workflow and project context
│   ├── changes/          # Proposed and active changes
│   ├── specs/            # Accepted behavior specs
│   └── config.yaml       # OpenSpec configuration
└── AGENTS.md             # Agent and contributor instructions
```

Boundaries that matter:

- **Public surface:** the future CLI flags, HTTP routes, file index JSON shape, rendered HTML contract, and editor behavior; breaking these surprises users and should be captured in a spec.
- **Internal modules:** markdown parsing, file watching, search/indexing, HTML templating, and live-reload transport; refactor freely once tests cover behavior.
- **Danger zones:** file writes and path traversal handling; mistakes can overwrite user files or expose files outside the served root, so require tests and a design note before changing them.
- **Danger zones:** live editing and websocket/event-stream behavior; race conditions can drop edits or render stale content, so add integration coverage before changing the protocol.

## 3. Commands

Use Poetry for development tasks:

```bash
poetry install                 # install Python dependencies and the editable CLI.
poetry run markpad --help      # smoke-test the CLI entry point.
poetry run markpad             # start the local server with the current folder as root.
poetry run markpad ./docs      # start the local server with an explicit folder as root.
poetry run markpad -d          # start the server in the background; pairs with `markpad stop`.
poetry run markpad stop        # stop a background server (also exposed as a Shutdown button in the UI).
poetry run markpad status      # check whether a background server is running.
poetry run ruff check .        # catch style and static-analysis drift before review.
poetry run ruff format .       # keep Python and config diffs reviewable.
poetry run pytest              # run unit and integration coverage for rendering, indexing, and live editing.
./install.sh                   # install the wrapper command at ~/.local/bin/markpad.
```

OpenSpec is available in this workspace:

```bash
openspec --help                # inspect the local OpenSpec CLI before using it in scripts.
```

The installed wrapper preserves the folder where `markpad` is invoked, then runs the Poetry-managed app from this repo.

## 4. Implementation Conventions

- Keep the server local-first by default - prevents accidentally exposing private Markdown files on the network.
- Serve only inside the chosen root directory - prevents path traversal and unintended file disclosure.
- Preserve Markdown source exactly during edits - avoids silent data loss in user-authored notes.
- Render through a maintained Markdown parser - avoids hand-written parsing bugs and inconsistent HTML.
- Sanitize rendered HTML unless trusted mode is explicit - prevents script injection from Markdown content.
- Add tests before changing file watching or save behavior - catches dropped edits and stale previews.
- Keep the file index deterministic - stable ordering makes search results, snapshots, and tests predictable.
- Keep generated assets out of source control unless intentionally checked in - avoids noisy diffs from build output.

## 5. Change Workflow

Use OpenSpec for non-trivial changes because the repo is behavior-driven and not implemented yet.

1. Create a change under `openspec/changes/<change-id>/` for new capabilities, protocol changes, storage behavior, or user-visible CLI behavior.
2. Write the proposal, design notes, and tasks before coding; this keeps the scope visible while the codebase is still small.
3. Update or add specs under `openspec/specs/` when behavior becomes accepted.
4. Keep `openspec/config.yaml` current when the selected stack, commands, or conventions become concrete.

Small documentation-only fixes can be made directly, but update this file when commands, layout, or danger zones change.

## 6. Working Protocol For AI Assistants

Follow this minimal contract on every task.

### Behavioral Guardrails

- State material assumptions before editing - this repo is still a scaffold and stack choices matter.
- Prefer the smallest useful implementation - the tool should stay easy to run locally.
- Touch only files required by the task - unrelated scaffold churn makes early history harder to review.
- Verify behavior with commands or mark it unverified - no command should be claimed as passing without evidence.

### Input Contract

```yaml
goal: what problem to solve
context: files, specs, links, or examples
constraints: what must not change; compatibility rules
definition_of_done: what done looks like
verification: tests, lints, or manual checks to run
```

If the goal, root directory behavior, write semantics, or live preview contract is ambiguous, ask before coding.

### Output Contract

```yaml
summary: what changed
assumptions: what was assumed
changes: files, configs, or commands touched
risks: what might break and how to detect it
verification: what was actually run and the result
next_step: recommended follow-up
```

## 7. Agent-Client Wiring

| Client | Commands directory | Skills / rules directory |
| --- | --- | --- |
| Claude Code | `.claude/commands/` | `.claude/skills/` |
| Cursor | `.cursor/commands/` | `.cursor/skills/` |
| Codex | - | `.codex/skills/` |

The checked-in client folders currently focus on OpenSpec workflows. Keep them aligned if the OpenSpec command names or skills change.

## 8. Keeping This File Useful

Update this file when:

- A package manifest, lockfile, or task runner is added.
- The chosen language/runtime changes.
- A new top-level source, docs, or test directory appears.
- CLI flags, routes, live editing behavior, or index format change.
- OpenSpec workflow files move or new project docs are added.

Do not grow this into a full manual. Keep architecture notes, protocol details, and design tradeoffs in OpenSpec artifacts, then link to them from here.

<!-- last_updated: 2026-05-26 -->
