# markpad

`markpad` is a local Markdown editor/reader/translator on the web. Run it in a folder containing Markdown files to get an index page, a left-side Markdown editor, and a right-side HTML preview.

## Install

```bash
./install.sh
```

The installer checks for Python 3.11+ and Poetry, builds the package, installs it
into `~/.local/share/markpad/venv`, and links the `markpad` command into
`~/.local/bin`. Verify installation with:

```bash
markpad --help
```

To remove the installed venv and command link:

```bash
./install.sh uninstall
```

## Run

From any folder containing Markdown files:

```bash
markpad
```

You can also pass an explicit root folder:

```bash
markpad --root /path/to/markdown
markpad serve /path/to/markdown
```

By default the server listens on `127.0.0.1:9526`. If `9526` is occupied, it tries `9527`, `9528`, and so on. To force a port:

```bash
markpad --port 9030
```

Check installation and runtime settings without starting the server:

```bash
markpad doctor
markpad doctor --format json
```

## Eye-friendly themes

The top toolbar includes a `Theme` settings popup with three comfortable reading themes:

- **Clear**: crisp light theme with a modern system font.
- **Paper**: warm paper background with a serif reading font.
- **Dark**: soft dark theme for low-light work.

Settings are saved in the browser with `localStorage`.

The file tree in the left pane has its own scrollbar for large folders. Use the
three compact toolbar icons to show or hide the file tree, Markdown editor, and
HTML preview panes.

## LLM translation

The `Translate` toolbar button translates the selected Markdown text to Chinese by default.
If no text is selected, it translates the whole editor content. Translation streams into the
editor as the LLM returns tokens, then the preview refreshes with the completed Markdown. The
button is enabled when these settings are available from the shell environment or a `.env`
file in the folder where you run `markpad`:

```bash
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=your-model
LLM_API_KEY=your-api-key
```

`LLM_BASE_URL` may point to an OpenAI-compatible API base URL such as `/v1`, or directly to
`/chat/completions`.

## Development

```bash
poetry install
poetry run markpad --help
poetry run ruff check .
poetry run ruff format .
poetry run pytest
```

## Diagrams

Mermaid fenced blocks render in the browser. PlantUML fenced blocks render when a local PlantUML command is configured:

```bash
export MARKPAD_PLANTUML_CMD=plantuml
```
