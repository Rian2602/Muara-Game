"""Legacy renderer — delegates to CLIRenderer. Kept for backward compatibility."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console

from muara.models.chapter import ChoiceOption

if TYPE_CHECKING:
    pass

_cache: dict[int, "CLIRenderer"] = {}


def _get_renderer(console: Console) -> "CLIRenderer":
    from muara.engine.render_cli import CLIRenderer

    key = id(console)
    if key not in _cache:
        _cache[key] = CLIRenderer(console)
    return _cache[key]


def render_chapter_header(
    console: Console,
    title: str,
    location: str,
    date: str,
    time: str,
    chapter_index: int = 0,
    total_chapters: int = 0,
) -> None:
    _get_renderer(console).render_chapter_header(
        title, location, date, time, chapter_index, total_chapters
    )


def render_scene_text(console: Console, text: str) -> None:
    _get_renderer(console).render_scene_text(text)


def render_choice_prompt(
    console: Console, prompt: str, options: list[ChoiceOption]
) -> None:
    _get_renderer(console).render_choice_prompt(prompt, options)


def render_continue_prompt(console: Console) -> None:
    _get_renderer(console).render_continue_prompt()


def render_error(console: Console, message: str) -> None:
    _get_renderer(console).render_error(message)
