from __future__ import annotations

from typing import Protocol, runtime_checkable

from muara.models.chapter import ChoiceOption


@runtime_checkable
class Renderer(Protocol):
    """Interface for all game rendering. Implementations handle output."""

    def render_chapter_header(
        self,
        title: str,
        location: str,
        date: str,
        time: str,
        chapter_index: int = 0,
        total_chapters: int = 0,
    ) -> None: ...

    def render_scene_text(self, text: str) -> None: ...

    def render_choice_prompt(
        self, prompt: str, options: list[ChoiceOption]
    ) -> None: ...

    def render_continue_prompt(self) -> None: ...

    def render_error(self, message: str) -> None: ...

    def render_line(self, text: str = "") -> None: ...
