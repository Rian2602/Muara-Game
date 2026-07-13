from __future__ import annotations

from typing import Callable

from muara.engine.render_protocol import Renderer
from muara.engine.state import GameState
from muara.models.chapter import Chapter, Choice, ChoiceOption, Scene


class ChapterRunError(Exception):
    """Raised when ChapterRunner encounters an inconsistent chapter structure at runtime."""


class ChapterRunner:
    def __init__(
        self,
        chapter: Chapter,
        state: GameState,
        renderer: Renderer,
        input_fn: Callable[[str], str] = input,
        chapter_index: int = 0,
        total_chapters: int = 0,
    ) -> None:
        self.chapter = chapter
        self.state = state
        self.renderer = renderer
        self._input_fn = input_fn
        self.chapter_index = chapter_index
        self.total_chapters = total_chapters

    def run(self, start_scene_id: str | None = None) -> str | None:
        self.renderer.render_chapter_header(
            title=self.chapter.title,
            location=self.chapter.location,
            date=self.chapter.date,
            time=self.chapter.time,
            chapter_index=self.chapter_index,
            total_chapters=self.total_chapters,
        )

        current_scene = self._resolve_start_scene(start_scene_id)

        while True:
            self.state.advance_to(self.chapter.id, current_scene.id)
            text = self._resolve_text(current_scene)
            self.renderer.render_scene_text(text)

            if current_scene.choice is not None:
                current_scene = self._handle_choice(current_scene)
                continue

            if current_scene.next_chapter is not None:
                self.state.mark_chapter_complete(self.chapter.id)
                return current_scene.next_chapter

            if current_scene.next_ending is not None:
                self.state.mark_chapter_complete(self.chapter.id)
                return f"__ENDING__:{current_scene.next_ending}"

            current_scene = self._next_linear_scene(current_scene)
            self.renderer.render_continue_prompt()
            self._input_fn("")

    def _resolve_text(self, scene: Scene) -> str:
        if not scene.text_variants:
            return scene.text
        for variant in scene.text_variants:
            if variant.default:
                continue
            if self.state.evaluate_condition(variant.condition):
                return variant.text
        for variant in scene.text_variants:
            if variant.default:
                return variant.text
        return scene.text

    def _resolve_start_scene(self, start_scene_id: str | None) -> Scene:
        if not start_scene_id:
            return self.chapter.scenes[0]
        try:
            return self.chapter.get_scene(start_scene_id)
        except KeyError as exc:
            raise ChapterRunError(
                f"start_scene_id {start_scene_id!r} tidak ditemukan di bab "
                f"{self.chapter.id!r}"
            ) from exc

    def _next_linear_scene(self, current: Scene) -> Scene:
        current_index = self.chapter._scene_order[current.id]
        if current_index + 1 >= len(self.chapter.scenes):
            raise ChapterRunError(
                f"Scene {current.id!r} di bab {self.chapter.id!r} tidak punya "
                "'choice' maupun 'next_chapter', tapi juga tidak ada scene "
                "berikutnya dalam urutan — dead-end yang tidak disengaja. "
                "Tambahkan 'next_chapter' atau scene lanjutan."
            )
        return self.chapter.scenes[current_index + 1]

    def _handle_choice(self, scene: Scene) -> Scene:
        if scene.choice is None:
            raise ChapterRunError(
                f"_handle_choice dipanggil untuk scene {scene.id!r} "
                "yang tidak punya choice — bug internal."
            )
        choice = scene.choice
        self.renderer.render_choice_prompt(choice.prompt, choice.options)

        selected_option = self._prompt_for_valid_option(choice)

        for flag in selected_option.parsed_flags:
            self.state.set_flag(flag.key, flag.value)

        try:
            return self.chapter.get_scene(selected_option.next)
        except KeyError as exc:
            raise ChapterRunError(
                f"Option {selected_option.id!r} di scene {scene.id!r} "
                f"menunjuk ke scene {selected_option.next!r} yang tidak ada "
                f"di bab {self.chapter.id!r}"
            ) from exc

    def _prompt_for_valid_option(self, choice: Choice) -> ChoiceOption:
        while True:
            raw = self._input_fn(
                f"Pilih (1-{len(choice.options)}): "
            ).strip()
            if raw.isdigit():
                index = int(raw) - 1
                if 0 <= index < len(choice.options):
                    return choice.options[index]
            self.renderer.render_error(
                f"Masukan tidak valid. Ketik angka 1 sampai {len(choice.options)}.",
            )
