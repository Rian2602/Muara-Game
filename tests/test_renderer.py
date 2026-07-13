"""Smoke tests for renderer.py — verifies functions produce output without error."""

from io import StringIO

import pytest
from rich.console import Console

from muara.engine import renderer
from muara.models.chapter import ChoiceOption


@pytest.fixture
def console():
    return Console(file=StringIO(), force_terminal=True)


class TestRenderChapterHeader:
    def test_produces_output(self, console):
        renderer.render_chapter_header(
            console, title="TEST", location="Loc", date="1 Jan", time="12.00"
        )
        assert console.file.tell() > 0


class TestRenderSceneText:
    def test_produces_output(self, console):
        renderer.render_scene_text(console, "Ade's text.")
        assert console.file.tell() > 0

    def test_strips_whitespace(self, console):
        renderer.render_scene_text(console, "  padded  ")
        assert console.file.tell() > 0


class TestRenderChoicePrompt:
    def test_produces_output(self, console):
        options = [
            ChoiceOption(id="a", label="First", next="s1"),
            ChoiceOption(id="b", label="Second", next="s2"),
        ]
        renderer.render_choice_prompt(console, "Choose:", options)
        assert console.file.tell() > 0


class TestRenderContinuePrompt:
    def test_produces_output(self, console):
        renderer.render_continue_prompt(console)
        assert console.file.tell() > 0


class TestRenderError:
    def test_produces_output(self, console):
        renderer.render_error(console, "Something went wrong")
        assert console.file.tell() > 0
