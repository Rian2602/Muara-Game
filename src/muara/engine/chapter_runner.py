from __future__ import annotations

from typing import Callable

from muara.engine.render_protocol import Renderer
from muara.engine.state import GameState
from muara.models.chapter import Chapter, Choice, ChoiceOption, Scene
from muara.engine.event_scheduler import EventScheduler
from muara.engine.ending import resolve_text


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
        scheduler: EventScheduler | None = None,
    ) -> None:
        self.chapter = chapter
        self.state = state
        self.renderer = renderer
        self._input_fn = input_fn
        self.chapter_index = chapter_index
        self.total_chapters = total_chapters
        self._scheduler = scheduler

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
        self._execute_hooks(current_scene.on_enter)

        while True:
            self._check_requires(current_scene)
            self.state.advance_to(self.chapter.id, current_scene.id)
            text = resolve_text(current_scene, self.state)
            self.renderer.render_scene_text(text)

            if current_scene.choice is not None:
                self._execute_hooks(current_scene.on_exit)
                current_scene = self._handle_choice(current_scene)
                self._execute_hooks(current_scene.on_enter)
                continue

            if current_scene.next_chapter is not None:
                self._execute_hooks(current_scene.on_exit)
                self.state.mark_chapter_complete(self.chapter.id)
                return current_scene.next_chapter

            if current_scene.next_ending is not None:
                self._execute_hooks(current_scene.on_exit)
                self.state.mark_chapter_complete(self.chapter.id)
                return f"__ENDING__:{current_scene.next_ending}"

            self._execute_hooks(current_scene.on_exit)
            current_scene = self._next_linear_scene(current_scene)
            self._execute_hooks(current_scene.on_enter)
            self.renderer.render_continue_prompt()
            self._input_fn("")

    def _check_requires(self, scene: Scene) -> None:
        flags = self.state.save_state.flags
        for condition in scene.requires:
            if not condition.evaluate(flags):
                raise ChapterRunError(
                    f"Scene {scene.id!r} di bab {self.chapter.id!r} tidak "
                    f"bisa dimasuki: syarat {condition.flag!r} "
                    f"{condition.operator.value} {condition.value!r} tidak "
                    "terpenuhi. Ini kemungkinan bug di alur bab."
                )

    def _execute_hooks(self, hooks: list[str]) -> None:
        """Execute scene transition hooks (on_enter/on_exit)."""
        for hook in hooks:
            # Parse hook format: "flag: value" or "method(args)"
            if ":" in hook:
                # Flag assignment: "flag_name: value"
                key, _, value_str = hook.partition(":")
                key = key.strip()
                value_str = value_str.strip()
                
                # Parse value
                if value_str.lower() == "true":
                    value = True
                elif value_str.lower() == "false":
                    value = False
                else:
                    try:
                        value = int(value_str)
                    except ValueError:
                        value = value_str
                
                self.state.set_flag(key, value)
            elif hook.startswith("increment("):
                # Counter increment: "increment(flag_name)"
                flag_name = hook[10:-1].strip()
                self.state.increment_counter(flag_name)
            elif hook.startswith("add_to_set("):
                # Add to set: "add_to_set(set_name, item)"
                args = hook[11:-1].strip()
                set_name, _, item = args.partition(",")
                self.state.add_to_set(set_name.strip(), item.strip())
            elif hook.startswith("advance_clock("):
                arg = hook[14:-1].strip()
                if arg == "shift":
                    self.state.advance_clock_shift()
                elif arg == "day":
                    self.state.advance_clock_day()
                else:
                    raise ChapterRunError(
                        f"advance_clock() argumen tidak dikenal: {arg!r} — "
                        "gunakan 'shift' atau 'day'"
                    )
        self._check_and_apply_due_events()

    def _check_and_apply_due_events(self) -> None:
        if self._scheduler is None:
            return
        for event in self._scheduler.due_events(self.state):
            self._scheduler.apply_event(event, self.state)

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
        flags = self.state.save_state.flags
        visible_options = [
            option
            for option in choice.options
            if all(condition.evaluate(flags) for condition in option.visible_if)
        ]

        if not visible_options:
            raise ChapterRunError(
                f"Scene {scene.id!r} di bab {self.chapter.id!r}: tidak ada "
                "opsi yang visible untuk choice ini dengan flag saat ini — "
                "dead-end tersembunyi. Periksa visible_if di setiap opsi."
            )

        self.renderer.render_choice_prompt(choice.prompt, visible_options)

        selected_option = self._prompt_for_valid_option(visible_options)

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

    def _prompt_for_valid_option(self, options: list[ChoiceOption]) -> ChoiceOption:
        while True:
            raw = self._input_fn(
                f"Pilih (1-{len(options)}): "
            ).strip()
            if raw.isdigit():
                index = int(raw) - 1
                if 0 <= index < len(options):
                    return options[index]
            self.renderer.render_error(
                f"Masukan tidak valid. Ketik angka 1 sampai {len(options)}.",
            )
