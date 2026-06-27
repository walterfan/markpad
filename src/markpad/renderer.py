from __future__ import annotations

import base64
import html
import os
import re
import shutil
import subprocess
from dataclasses import dataclass

import bleach
from markdown_it import MarkdownIt

FENCE_RE = re.compile(
    r"```(?P<info>[A-Za-z0-9_-]+)?[^\n]*\n(?P<body>.*?)(?:\n```|$)",
    re.DOTALL,
)

ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS).union(
    {
        "article",
        "aside",
        "blockquote",
        "br",
        "code",
        "div",
        "figcaption",
        "figure",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "img",
        "li",
        "ol",
        "p",
        "pre",
        "section",
        "span",
        "strong",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "ul",
    }
)
ALLOWED_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "*": ["class", "id", "data-diagram-index"],
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title", "class"],
}


@dataclass(frozen=True)
class DiagramPlaceholder:
    token: str
    html: str


def render_markdown(content: str) -> str:
    placeholders: list[DiagramPlaceholder] = []

    def replace_diagram(match: re.Match[str]) -> str:
        info = (match.group("info") or "").lower()
        source = match.group("body")
        if info == "mermaid":
            token = f"@@MARKPAD_DIAGRAM_{len(placeholders)}@@"
            escaped = html.escape(source)
            placeholders.append(
                DiagramPlaceholder(
                    token=token,
                    html=(
                        '<div class="diagram diagram-mermaid" data-diagram-type="mermaid">'
                        f'<div class="mermaid">{escaped}</div>'
                        '<div class="diagram-error hidden"></div>'
                        "</div>"
                    ),
                )
            )
            return token
        if info in {"plantuml", "puml"}:
            token = f"@@MARKPAD_DIAGRAM_{len(placeholders)}@@"
            placeholders.append(DiagramPlaceholder(token=token, html=render_plantuml_block(source)))
            return token
        return match.group(0)

    content_with_tokens = FENCE_RE.sub(replace_diagram, content)
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    rendered = md.render(content_with_tokens)
    cleaned = bleach.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols={"http", "https", "data"},
    )
    for placeholder in placeholders:
        cleaned = cleaned.replace(f"<p>{placeholder.token}</p>", placeholder.html)
        cleaned = cleaned.replace(placeholder.token, placeholder.html)
    return cleaned


def render_plantuml_block(source: str) -> str:
    command = _plantuml_command()
    if not command:
        escaped = html.escape(source)
        return (
            '<figure class="diagram diagram-plantuml diagram-unavailable">'
            "<figcaption>PlantUML renderer unavailable. Set MARKPAD_PLANTUML_CMD "
            "or install PlantUML so `which plantuml` prints a command path.</figcaption>"
            f"<pre><code>{escaped}</code></pre>"
            "</figure>"
        )

    try:
        result = subprocess.run(
            [command, "-tsvg", "-pipe"],
            input=source,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _plantuml_error(source, str(exc))

    if result.returncode != 0:
        return _plantuml_error(source, result.stderr.strip() or "PlantUML rendering failed.")

    svg = result.stdout.encode("utf-8")
    encoded = base64.b64encode(svg).decode("ascii")
    return (
        '<figure class="diagram diagram-plantuml">'
        f'<img alt="PlantUML diagram" src="data:image/svg+xml;base64,{encoded}">'
        "</figure>"
    )


def _plantuml_command() -> str | None:
    return (
        os.environ.get("MARKPAD_PLANTUML_CMD")
        or os.environ.get("PLANTUML_CMD")
        or shutil.which("plantuml")
    )


def _plantuml_error(source: str, message: str) -> str:
    escaped_message = html.escape(message)
    escaped_source = html.escape(source)
    return (
        '<figure class="diagram diagram-plantuml diagram-error">'
        f"<figcaption>{escaped_message}</figcaption>"
        f"<pre><code>{escaped_source}</code></pre>"
        "</figure>"
    )
