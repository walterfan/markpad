from __future__ import annotations

import subprocess

from pytest import MonkeyPatch

from markpad.renderer import render_markdown


def test_render_markdown_sanitizes_script() -> None:
    html = render_markdown("# Title\n\n<script>alert(1)</script>")

    assert "<h1>Title</h1>" in html
    assert "<script>" not in html


def test_render_markdown_allows_safe_inline_html_hr() -> None:
    html = render_markdown(
        "<hr/> 本作品采用知识共享署名-非商业性使用-禁止演绎 4.0 国际许可协议进行许可。"
    )

    assert "<hr>" in html
    assert "本作品采用知识共享" in html


def test_render_markdown_keeps_normal_code_block() -> None:
    html = render_markdown("```python\nprint('hi')\n```")

    assert "<pre><code" in html
    assert "print" in html


def test_render_mermaid_block_as_diagram() -> None:
    html = render_markdown("```mermaid\ngraph TD; A-->B\n```")

    assert "diagram-mermaid" in html
    assert "graph TD" in html
    assert "<pre><code>" not in html


def test_render_plantuml_without_renderer_shows_unavailable(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("MARKPAD_PLANTUML_CMD", raising=False)
    monkeypatch.delenv("PLANTUML_CMD", raising=False)
    monkeypatch.setattr("markpad.renderer.shutil.which", lambda _command: None)

    html = render_markdown("```plantuml\n@startuml\nA -> B\n@enduml\n```")

    assert "PlantUML renderer unavailable" in html
    assert "which plantuml" in html
    assert "@startuml" in html


def test_render_plantuml_uses_plantuml_from_path(monkeypatch: MonkeyPatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.delenv("MARKPAD_PLANTUML_CMD", raising=False)
    monkeypatch.delenv("PLANTUML_CMD", raising=False)
    monkeypatch.setattr("markpad.renderer.shutil.which", lambda command: "/usr/local/bin/plantuml")

    def fake_run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="<svg></svg>", stderr="")

    monkeypatch.setattr("markpad.renderer.subprocess.run", fake_run)

    html = render_markdown("```plantuml\n@startuml\nA -> B\n@enduml\n```")

    assert calls == [["/usr/local/bin/plantuml", "-tsvg", "-pipe"]]
    assert "PlantUML renderer unavailable" not in html
    assert "data:image/svg+xml;base64," in html
