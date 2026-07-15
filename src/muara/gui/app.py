"""Textual-based Muara narrative game — async state machine replacing ChapterRunner."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, OptionList, Static
from textual.widgets.option_list import Option

from muara.constants import END_OF_STORY_MARKER
from muara.engine.chapter_loader import (
    ChapterLoadError,
    load_chapter,
    load_manifest,
)
from muara.engine.ending import ENDING_TEXTS, determine_ending, resolve_text
from muara.engine.event_loader import load_events, EventLoadError
from muara.engine.event_scheduler import EventScheduler
from muara.engine.save_manager import SaveLoadError, list_save_slots, load, save, delete_save, SaveSlotInfo
from muara.engine.state import GameState
from muara.models.chapter import Chapter, ChoiceOption, Scene

if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys._MEIPASS)
    PROJECT_ROOT = Path(sys.executable).parent
    CONTENT_DIR = BUNDLE_DIR / "content"
    CHAPTERS_DIR = CONTENT_DIR / "chapters"
    SAVES_DIR = PROJECT_ROOT / "saves"
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    CONTENT_DIR = PROJECT_ROOT / "content"
    CHAPTERS_DIR = CONTENT_DIR / "chapters"
    SAVES_DIR = PROJECT_ROOT / "saves"

DEFAULT_SAVE_ID = "default"


# ── Messages ──────────────────────────────────────────────


class NextChapterLoaded(Message):
    def __init__(self, chapter_id: str) -> None:
        self.chapter_id = chapter_id
        super().__init__()


class EndingReached(Message):
    def __init__(self, ending_id: str) -> None:
        self.ending_id = ending_id
        super().__init__()


# ── Screens ───────────────────────────────────────────────


class GameScreen(Screen):
    """Main game screen — async state machine replacing ChapterRunner.run()."""

    BINDINGS = [
        Binding("enter", "continue", "Lanjutkan", show=True, key_display="enter"),
    ]

    def __init__(
        self,
        chapter: Chapter,
        state: GameState,
        chapter_index: int = 0,
        total_chapters: int = 0,
        scheduler: EventScheduler | None = None,
    ) -> None:
        super().__init__()
        self.chapter = chapter
        self.state = state
        self.chapter_index = chapter_index
        self.total_chapters = total_chapters
        self.scheduler = scheduler
        self.current_scene: Scene | None = None
        self.waiting_for_continue = False
        self.current_choice = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="chapter-header")
        with VerticalScroll(id="story-scroll"):
            yield Static(id="scene-text")
        yield OptionList(id="choices")
        yield Static(id="status-bar")
        yield Footer()

    def _check_and_apply_due_events(self) -> None:
        if self.scheduler is not None:
            for event in self.scheduler.due_events(self.state):
                self.scheduler.apply_event(event, self.state)

    def on_mount(self) -> None:
        self._show_current_scene()

    # ── Scene traversal ────────────────────────────────────

    def _show_current_scene(self) -> None:
        if self.current_scene is None:
            self.current_scene = self.chapter.scenes[0]
            self.state.execute_hooks(self.current_scene.on_enter)
            self._check_and_apply_due_events()

        self.state.advance_to(self.chapter.id, self.current_scene.id)

        header = self.query_one("#chapter-header", Static)
        header.update(
            f"[dim][Bab {self.chapter_index}/{self.total_chapters}][/dim]\n"
            f"[bold]{self.chapter.title}[/bold]\n"
            f"[bold italic]{self.chapter.location}[/bold italic]\n"
            f"[bold italic]{self.chapter.date}, {self.chapter.time}[/bold italic]"
        )

        text = resolve_text(self.current_scene, self.state)
        self.query_one("#scene-text", Static).update(text.strip())
        self.query_one("#story-scroll").scroll_home(animate=False)

        self._update_status_bar()

        if self.current_scene.choice is not None:
            self._show_choices(self.current_scene.choice)
        elif self.current_scene.next_chapter is not None:
            self.state.execute_hooks(self.current_scene.on_exit)
            self._check_and_apply_due_events()
            self.state.mark_chapter_complete(self.chapter.id)
            self._hide_choices()
            self.app.post_message(NextChapterLoaded(self.current_scene.next_chapter))
        elif self.current_scene.next_ending is not None:
            self.state.execute_hooks(self.current_scene.on_exit)
            self._check_and_apply_due_events()
            self.state.mark_chapter_complete(self.chapter.id)
            self._hide_choices()
            self.app.post_message(EndingReached(self.current_scene.next_ending))
        else:
            self._hide_choices()
            self.waiting_for_continue = True

    def _show_choices(self, choice) -> None:
        ol = self.query_one("#choices", OptionList)
        ol.clear_options()
        for opt in choice.options:
            ol.add_option(Option(opt.label, id=opt.id))
        ol.display = True
        ol.focus()
        self.current_choice = choice

    def _hide_choices(self) -> None:
        ol = self.query_one("#choices", OptionList)
        ol.clear_options()
        ol.display = False
        self.current_choice = None

    def _update_status_bar(self) -> None:
        flags = self.state.save_state.flags
        parts: list[str] = []
        
        world_day = flags.get("world_day")
        world_shift = flags.get("world_shift")
        if world_day is not None and world_shift is not None:
            parts.append(f"Hari {world_day}, {str(world_shift).title()}")

        if flags.get("berbicara_dengan_jaya"):
            parts.append("Jaya ✓")
        if flags.get("melihat_anomali"):
            parts.append("Anomali ✓")
        if flags.get("melapor"):
            parts.append("Lapor ✓")
        if flags.get("percaya_jaya"):
            parts.append("Percaya Jaya ✓")
        if flags.get("konfrontasi_berhasil"):
            parts.append("Konfrontasi ✓")
        status = " | ".join(parts) if parts else ""
        self.query_one("#status-bar", Static).update(f"[dim]{status}[/dim]")

    # ── Input handlers ─────────────────────────────────────

    def action_continue(self) -> None:
        if not self.waiting_for_continue:
            return
        self.waiting_for_continue = False
        self.state.execute_hooks(self.current_scene.on_exit)
        self._check_and_apply_due_events()
        current_index = self.chapter._scene_order[self.current_scene.id]
        next_index = current_index + 1
        if next_index < len(self.chapter.scenes):
            self.current_scene = self.chapter.scenes[next_index]
            self.state.execute_hooks(self.current_scene.on_enter)
            self._check_and_apply_due_events()
            self._show_current_scene()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if self.current_choice is None:
            return
        self.state.execute_hooks(self.current_scene.on_exit)
        self._check_and_apply_due_events()
        selected = self.current_choice.options[event.option_index]
        for flag in selected.parsed_flags:
            self.state.set_flag(flag.key, flag.value)
        self.current_scene = self.chapter.get_scene(selected.next)
        self.current_choice = None
        self.state.execute_hooks(self.current_scene.on_enter)
        self._check_and_apply_due_events()
        self._show_current_scene()


class EndingScreen(Screen):
    """Screen displayed when the game ends."""

    BINDINGS = [Binding("q", "quit", "Keluar", show=True)]

    def __init__(self, ending_id: str) -> None:
        super().__init__()
        self.ending_id = ending_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            ENDING_TEXTS.get(
                self.ending_id,
                f"[bold]— TAMAT: {self.ending_id.upper()} —[/bold]",
            ),
            id="ending-text",
        )
        yield Footer()

    def action_quit(self) -> None:
        self.app.exit()


class SaveSlotScreen(Screen):
    """Screen for selecting save slots."""

    BINDINGS = [
        Binding("n", "new_game", "Game Baru", show=True),
        Binding("d", "delete_save", "Hapus Save", show=True),
        Binding("r", "rename_save", "Rename Save", show=True),
        Binding("q", "quit", "Keluar", show=True),
    ]

    def __init__(self, chapter_sequence: list[str]) -> None:
        super().__init__()
        self.chapter_sequence = chapter_sequence
        self.save_slots: list[SaveSlotInfo] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold]Pilih Save Slot[/bold]", id="save-header")
        yield OptionList(id="save-list")
        yield Footer()

    def on_mount(self) -> None:
        self.save_slots = list_save_slots(SAVES_DIR)
        ol = self.query_one("#save-list", OptionList)
        ol.clear_options()
        
        for i, slot in enumerate(self.save_slots, 1):
            status = "[green]Tamat[/green]" if slot.completed else "[yellow]Bermain[/yellow]"
            chapter_title = "Unknown"
            for ch_id in self.chapter_sequence:
                if ch_id == slot.current_chapter:
                    try:
                        ch_path = CHAPTERS_DIR / f"{ch_id}.yaml"
                        if ch_path.exists():
                            ch = load_chapter(ch_path)
                            chapter_title = ch.title
                    except ChapterLoadError:
                        pass
                    break
            flags = ", ".join(slot.key_flags) if slot.key_flags else "-"
            label = f"{i}. {status} | {chapter_title} | {slot.last_saved} | {flags}"
            ol.add_option(Option(label, id=slot.save_id))
        
        if not self.save_slots:
            ol.add_option(Option("Tidak ada save slot", id="empty"))
        
        ol.focus()

    def action_new_game(self) -> None:
        self.app.push_screen(GameSelectScreen(self.chapter_sequence))

    async def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if not self.save_slots:
            return
        
        selected_index = event.option_index
        if selected_index >= len(self.save_slots):
            return
        
        selected_slot = self.save_slots[selected_index]
        try:
            save_state = load(selected_slot.save_id, SAVES_DIR)
            self.app.state = GameState(save_state)
            self.app.current_chapter_id = save_state.current_chapter
            self.app.start_scene_id = save_state.current_scene or None
            await self.app._load_chapter(self.app.current_chapter_id)
        except SaveLoadError:
            pass

    def action_quit(self) -> None:
        self.app.exit()

    async def action_delete_save(self) -> None:
        """Delete the currently selected save slot."""
        ol = self.query_one("#save-list", OptionList)
        selected_index = ol.option_list_index
        if selected_index is None or selected_index >= len(self.save_slots):
            return
        
        selected_slot = self.save_slots[selected_index]
        
        from textual.app import ModalScreen
        
        class ConfirmDeleteScreen(ModalScreen[bool]):
            """Modal to confirm deletion."""
            
            CSS = """
            ConfirmDeleteScreen {
                align: center middle;
            }
            #dialog {
                width: 50;
                height: auto;
                border: solid $primary;
                padding: 1 2;
            }
            """
            
            def __init__(self, save_id: str) -> None:
                super().__init__()
                self.save_id = save_id
            
            def compose(self) -> ComposeResult:
                with VerticalScroll(id="dialog"):
                    yield Static(f"Hapus save '{self.save_id}'?")
                    yield Static("[y] Ya  [n] Tidak")
            
            def on_key(self, event) -> None:
                if event.key == "y":
                    self.dismiss(True)
                elif event.key == "n":
                    self.dismiss(False)
        
        confirm = await self.app.push_screen_wait(ConfirmDeleteScreen(selected_slot.save_id))
        if confirm:
            try:
                delete_save(selected_slot.save_id, SAVES_DIR)
                self.on_mount()  # Refresh the list
            except Exception:
                pass

    async def action_rename_save(self) -> None:
        """Rename the currently selected save slot."""
        ol = self.query_one("#save-list", OptionList)
        selected_index = ol.option_list_index
        if selected_index is None or selected_index >= len(self.save_slots):
            return
        
        selected_slot = self.save_slots[selected_index]
        
        from textual.app import ModalScreen
        from textual.widgets import Input
        
        class RenameScreen(ModalScreen[str]):
            """Modal to input new save name."""
            
            CSS = """
            RenameScreen {
                align: center middle;
            }
            #dialog {
                width: 50;
                height: auto;
                border: solid $primary;
                padding: 1 2;
            }
            """
            
            def __init__(self, current_name: str) -> None:
                super().__init__()
                self.current_name = current_name
            
            def compose(self) -> ComposeResult:
                with VerticalScroll(id="dialog"):
                    yield Static(f"Rename '{self.current_name}' ke:")
                    yield Input(placeholder="Nama baru...", id="rename-input")
            
            def on_input_submitted(self, event) -> None:
                self.dismiss(event.value)
        
        new_name = await self.app.push_screen_wait(RenameScreen(selected_slot.save_id))
        if new_name and new_name != selected_slot.save_id:
            try:
                rename_save(selected_slot.save_id, new_name, SAVES_DIR)
                self.on_mount()  # Refresh the list
            except Exception:
                pass


class GameSelectScreen(Screen):
    """Screen for starting a new game."""

    BINDINGS = [Binding("n", "new_game", "Mulai Game Baru", show=True)]

    def __init__(self, chapter_sequence: list[str]) -> None:
        super().__init__()
        self.chapter_sequence = chapter_sequence

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold]Mulai Permainan Baru[/bold]", id="new-header")
        yield Static("Tekan 'n' untuk memulai permainan baru", id="new-prompt")
        yield Footer()

    async def action_new_game(self) -> None:
        self.app.current_chapter_id = self.chapter_sequence[0]
        self.app.state = GameState.new_playthrough(
            save_id=DEFAULT_SAVE_ID,
            chapter_id=self.app.current_chapter_id,
            scene_id="",
        )
        self.app.start_scene_id = None
        await self.app._load_chapter(self.app.current_chapter_id)


# ── Main App ──────────────────────────────────────────────


class MuaraApp(App):
    """Textual-based Muara narrative game."""

    CSS_PATH = "muara.tcss"
    TITLE = "Muara"
    SUB_TITLE = "Narrative Game"

    def __init__(self) -> None:
        super().__init__()
        self.chapter_sequence: list[str] = []
        self.state: GameState | None = None
        self.current_chapter_id: str = ""
        self.start_scene_id: str | None = None
        self.scheduler: EventScheduler | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    async def on_mount(self) -> None:
        self.chapter_sequence = load_manifest(CONTENT_DIR)
        if not self.chapter_sequence:
            self.exit()
            return

        try:
            events = load_events(CONTENT_DIR / "events.yaml")
            self.scheduler = EventScheduler(events)
        except EventLoadError:
            self.scheduler = None

        # Show save slot selection screen
        self.push_screen(SaveSlotScreen(self.chapter_sequence))

    async def _load_chapter(self, chapter_id: str) -> None:
        path = CHAPTERS_DIR / f"{chapter_id}.yaml"
        try:
            chapter = load_chapter(path)
        except ChapterLoadError:
            self.exit()
            return

        idx = self.chapter_sequence.index(chapter_id) + 1
        screen = GameScreen(
            chapter,
            self.state,
            chapter_index=idx,
            total_chapters=len(self.chapter_sequence),
            scheduler=self.scheduler,
        )
        if self.start_scene_id:
            screen.current_scene = chapter.get_scene(self.start_scene_id)
            self.start_scene_id = None
        self.push_screen(screen)

    async def on_next_chapter_loaded(self, event: NextChapterLoaded) -> None:
        self.current_chapter_id = event.chapter_id
        self.state.touch_last_saved()
        save(self.state.save_state, SAVES_DIR)
        await self._load_chapter(event.chapter_id)

    def on_ending_reached(self, event: EndingReached) -> None:
        ending_id = event.ending_id
        if ending_id == "__END__":
            ending_id = determine_ending(self.state)
        self.state.save_state.endings_achieved.append(ending_id)
        self.state.save_state.completed = True
        self.state.touch_last_saved()
        save(self.state.save_state, SAVES_DIR)
        self.push_screen(EndingScreen(ending_id))
