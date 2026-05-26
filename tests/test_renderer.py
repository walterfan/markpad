from __future__ import annotations

from markpad.renderer import render_markdown


def test_render_markdown_sanitizes_script() -> None:
    html = render_markdown("# Title\n\n<script>alert(1)</script>")

    assert "<h1>Title</h1>" in html
    assert "<script>" not in html


def test_render_markdown_keeps_normal_code_block() -> None:
    html = render_markdown("```python\nprint('hi')\n```")

    assert "<pre><code" in html
    assert "print" in html


def test_render_mermaid_block_as_diagram() -> None:
    html = render_markdown("```mermaid\ngraph TD; A-->B\n```")

    assert "diagram-mermaid" in html
    assert "graph TD" in html
    assert "<pre><code>" not in html


def test_render_plantuml_without_renderer_shows_unavailable() -> None:
    html = render_markdown("```plantuml\n@startuml\nA -> B\n@enduml\n```")

    assert "PlantUML renderer unavailable" in html
    assert "@startuml" in html
