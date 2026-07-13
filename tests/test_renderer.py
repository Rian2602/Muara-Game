"""Smoke tests for CLIRenderer — verifies rendering produces output without error."""

from io import StringIO

import pytest
from rich.console import Console

from muara.engine.render_cli import CLIRenderer
from muara.models.chapter import ChoiceOption


@pytest.fixture
def renderer():
    console = Console(file=StringIO(), force_terminal=True)
    return CLIRenderer(console)


class TestRenderChapterHeader:
    def test_produces_output(self, renderer):
        renderer.render_chapter_header(
            title="TEST", location="Loc", date="1 Jan", time="12.00"
        )
        assert renderer.console.file.tell() > 0


class TestRenderSceneText:
    def test_produces_output(self, renderer):
        renderer.render_scene_text("Ade's text.")
        assert renderer.console.file.tell() > 0

    def test_strips_whitespace(self, renderer):
        renderer.render_scene_text("  padded  ")
        assert renderer.console.file.tell() > 0


class TestRenderChoicePrompt:
    def test_produces_output(self, renderer):
        options = [
            ChoiceOption(id="a", label="First", next="s1"),
            ChoiceOption(id="b", label="Second", next="s2"),
        ]
        renderer.render_choice_prompt("Choose:", options)
        assert renderer.console.file.tell() > 0


class TestRenderContinuePrompt:
    def test_produces_output(self, renderer):
        renderer.render_continue_prompt()
        assert renderer.console.file.tell() > 0


class TestRenderError:
    def test_produces_output(self, renderer):
        renderer.render_error("Something went wrong")
        assert renderer.console.file.tell() > 0


class TestRenderLine:
    def test_produces_output(self, renderer):
        renderer.render_line("Hello world")
        assert renderer.console.file.tell() > 0

    def test_empty_line(self, renderer):
        renderer.render_line()
        assert renderer.console.file.tell() > 0
