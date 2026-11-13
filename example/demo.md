# Markpad Markdown Demo

This page shows Markdown features that Markpad can render. Open it in Markpad and
edit the source to see the preview update.

## Text and headings

Use **bold**, *italic*, ~~strikethrough~~, and `inline code` in a sentence.

> Blockquotes are useful for notes, tips, and excerpts.
>
> They can contain multiple paragraphs.

## Lists

Shopping list:

- Coffee
- Tea
  - Green tea
  - Black tea
- Water

Steps to preview a file:

1. Start Markpad in the folder containing the file.
2. Select `example/demo.md` in the file list.
3. Edit the Markdown and watch the preview update.

## Table

| Feature | Markdown syntax | Markpad preview |
| --- | --- | --- |
| Bold | `**text**` | **text** |
| Link | `[Markpad](https://example.com)` | [Markpad](https://example.com) |
| Inline code | `` `code` `` | `code` |

## Code block

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

## Mermaid diagrams

Use a fenced code block labeled `mermaid` for diagrams.

### Flowchart

```mermaid
flowchart LR
    A[Write Markdown] --> B[Markpad renders preview]
    B --> C{Looks good?}
    C -->|Yes| D[Save]
    C -->|Edit| A
```

### Sequence diagram

```mermaid
sequenceDiagram
    actor Reader
    participant Browser
    participant Markpad
    Reader->>Browser: Open demo.md
    Browser->>Markpad: Request Markdown file
    Markpad-->>Browser: Markdown source
    Browser->>Browser: Render preview and Mermaid diagram
    Browser-->>Reader: Show the page
```

### Class diagram

```mermaid
classDiagram
    class MarkdownFile {
        +string path
        +string content
        +save()
    }
    class Preview {
        +render(content)
    }
    MarkdownFile --> Preview : updates
```

### State diagram

```mermaid
stateDiagram-v2
    [*] --> Editing
    Editing --> Previewing : content changes
    Previewing --> Editing : continue editing
    Previewing --> Saved : save file
    Saved --> [*]
```

## Links and horizontal rule

Visit the [Markpad repository](https://github.com/walterfan/markpad) for more information.

---

That is the end of the demo page.
