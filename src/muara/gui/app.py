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
from textual.widgets import Footer, Header, OptionList, Static
from textual.widgets.option_list import Option

from muara.constants import END_OF_STORY_MARKER
from muara.engine.chapter_loader import (
    ChapterLoadError,
    load_chapter,
    load_manifest,
)
from muara.engine.save_manager import SaveLoadError, list_saves, load, save
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

ENDING_TEXTS: dict[str, str] = {
    "pembebasan": (
        "[bold]— TAMAT: PEMBEBASAN —[/bold]\n\n"
        "Kebenaran sudah terungkap. Buku kecilku dan kertas-kertas Jaya "
        "sudah di tangan orang-orang yang peduli. Angka-angkaku sudah "
        "memiliki bukti — bukan hanya catatan, bukan hanya ingatan.\n\n"
        "Mungkin perubahan tidak akan datang besok. Mungkin tidak akan "
        "datang tahun ini. Tapi hari ini, aku tahu satu hal: cara aku "
        "mencatat — itu yang tidak bisa diambil dari aku. Dan suatu hari, "
        "seseorang akan menemukan bahwa angka-angkaku benar. Selalu benar."
    ),
    "kehancuran": (
        "[bold]— TAMAT: KEHANCURAN —[/bold]\n\n"
        "Tekanan terlalu besar. Mandor tahu. Orang asing tahu. Dan sekarang, "
        "aku tidak tahu siapa lagi yang tahu. Buku kecilku masih ada — "
        "tapi bukti tidak cukup. Angka tidak cukup. Keberanian tidak cukup.\n\n"
        "Aku berdiri di ujung dermaga. Air laut menghantam batu. Besok, "
        "aku akan menghitung lagi. Tanpa bukti. Tanpa kertas. Hanya angka. "
        "Dan mungkin — mungkin — itu sudah cukup. Karena angka tidak akan "
        "berhenti karena aku berhenti mencatat."
    ),
    "dipercaya": (
        "[bold]— TAMAT: DIPERCAI —[/bold]\n\n"
        "Mandor menerima buku kecilku. Dia membaca setiap halaman. "
        'Lalu dia menutup buku dan berkata: "Kamu harus berhenti mencatat. '
        'Ini bukan urusanmu."\n\n'
        "Buku kecilku hilang. Tapi angkanya sudah ada di kepalaku. "
        "Tiga puluh dua. Tiga puluh tiga. Tiga puluh empat. "
        "Angka-angka yang tidak akan pernah hilang."
    ),
    "dicurigai": (
        "[bold]— TAMAT: DICURIGAI —[/bold]\n\n"
        "Mandor melaporkan ke kantor kabupaten. Aku dipecat minggu depan. "
        "Tapi buku kecilku masih ada — tersembunyi di tempat yang hanya "
        "aku yang tahu.\n\n"
        "Suatu hari, seseorang akan menemukannya. Mereka akan membaca "
        "angka-angka ini dan menemukan bahwa catatanku dan catatan mandor "
        "tidak cocok. Dan selisih antara keduanya akan menjadi satu-satunya "
        "bukti bahwa aku pernah ada."
    ),
    "terlupakan": (
        "[bold]— TAMAT: TERLUPAKAN —[/bold]\n\n"
        "Tidak ada yang terjadi. Aku diam. Mandor tetap menghitung. "
        "Kaleng tetap berjajar. Angka-angka tetap ada di kepalaku — "
        "tapi tidak di kertas mana pun.\n\n"
        "Mungkin ini lebih aman. Mungkin ini lebih bijak. "
        "Tapi setiap malam, aku bertanya-tanya: apa yang terjadi "
        "jika aku bicara?"
    ),
    "sekutu": (
        "[bold]— TAMAT: SEKUTU —[/bold]\n\n"
        "Jaya dan aku menyimpan bukti di dua tempat. Buku kecilku "
        "dan catatannya. Salah satu dari kami mungkin akan hidup lebih "
        "lama dari catatan ini.\n\n"
        "Tapi hari ini, kami masih bisa menghitung. Dan besok, "
        "kami akan menghitung lagi."
    ),
}


def _determine_ending(state: GameState) -> str:
    kebenaran_terungkap = state.get_flag("kebenaran_terungkap")
    warisan_positif = state.get_flag("warisan_positif")
    konfrontasi_berhasil = state.get_flag("konfrontasi_berhasil")
    tekanan_meningkat = state.get_flag("tekanan_meningkat", 0)
    melihat_anomali = state.get_flag("melihat_anomali")

    if (
        kebenaran_terungkap is True
        and warisan_positif is True
        and melihat_anomali is True
    ):
        return "pembebasan"
    if konfrontasi_berhasil is False or (
        isinstance(tekanan_meningkat, int) and tekanan_meningkat >= 6
    ):
        return "kehancuran"

    melapor = state.get_flag("melapor")
    bukti_kuat = state.get_flag("bukti_kuat")
    beri_bukti_ke_jaya = state.get_flag("beri_bukti_ke_jaya")
    berbicara_dengan_jaya = state.get_flag("berbicara_dengan_jaya")
    chapter_5_choice = state.get_flag("chapter_5_choice")

    if (
        beri_bukti_ke_jaya is True
        and bukti_kuat is True
        and berbicara_dengan_jaya is True
    ):
        return "sekutu"
    if melapor is True and chapter_5_choice == "simpan":
        return "dipercaya"
    if bukti_kuat is True and chapter_5_choice == "simpan":
        return "dipercaya"
    if chapter_5_choice == "hancurkan":
        return "terlupakan"
    if melapor is True:
        return "dicurigai"
    return "terlupakan"


def _resolve_text(scene: Scene, state: GameState) -> str:
    if not scene.text_variants:
        return scene.text
    for variant in scene.text_variants:
        if variant.default:
            continue
        if state.evaluate_condition(variant.condition):
            return variant.text
    for variant in scene.text_variants:
        if variant.default:
            return variant.text
    return scene.text


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
    ) -> None:
        super().__init__()
        self.chapter = chapter
        self.state = state
        self.chapter_index = chapter_index
        self.total_chapters = total_chapters
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

    def on_mount(self) -> None:
        self._show_current_scene()

    # ── Scene traversal ────────────────────────────────────

    def _show_current_scene(self) -> None:
        if self.current_scene is None:
            self.current_scene = self.chapter.scenes[0]

        self.state.advance_to(self.chapter.id, self.current_scene.id)

        header = self.query_one("#chapter-header", Static)
        header.update(
            f"[dim][Bab {self.chapter_index}/{self.total_chapters}][/dim]\n"
            f"[bold]{self.chapter.title}[/bold]\n"
            f"[bold italic]{self.chapter.location}[/bold italic]\n"
            f"[bold italic]{self.chapter.date}, {self.chapter.time}[/bold italic]"
        )

        text = _resolve_text(self.current_scene, self.state)
        self.query_one("#scene-text", Static).update(text.strip())
        self.query_one("#story-scroll").scroll_home(animate=False)

        self._update_status_bar()

        if self.current_scene.choice is not None:
            self._show_choices(self.current_scene.choice)
        elif self.current_scene.next_chapter is not None:
            self.state.mark_chapter_complete(self.chapter.id)
            self._hide_choices()
            self.app.post_message(NextChapterLoaded(self.current_scene.next_chapter))
        elif self.current_scene.next_ending is not None:
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
        current_index = self.chapter._scene_order[self.current_scene.id]
        next_index = current_index + 1
        if next_index < len(self.chapter.scenes):
            self.current_scene = self.chapter.scenes[next_index]
            self._show_current_scene()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if self.current_choice is None:
            return
        selected = self.current_choice.options[event.option_index]
        for flag in selected.parsed_flags:
            self.state.set_flag(flag.key, flag.value)
        self.current_scene = self.chapter.get_scene(selected.next)
        self.current_choice = None
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

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    async def on_mount(self) -> None:
        self.chapter_sequence = load_manifest(CONTENT_DIR)
        if not self.chapter_sequence:
            self.exit()
            return

        existing_saves = list_saves(SAVES_DIR)
        if existing_saves:
            try:
                save_state = load(DEFAULT_SAVE_ID, SAVES_DIR)
                if not save_state.completed:
                    self.state = GameState(save_state)
                    self.current_chapter_id = save_state.current_chapter
                    self.start_scene_id = (
                        save_state.current_scene or None
                    )
                    await self._load_chapter(self.current_chapter_id)
                    return
            except SaveLoadError:
                pass

        self.current_chapter_id = self.chapter_sequence[0]
        self.state = GameState.new_playthrough(
            save_id=DEFAULT_SAVE_ID,
            chapter_id=self.current_chapter_id,
            scene_id="",
        )
        self.start_scene_id = None
        await self._load_chapter(self.current_chapter_id)

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
        )
        if self.start_scene_id:
            screen.current_scene = chapter.get_scene(self.start_scene_id)
            self.start_scene_id = None
        self.push_screen(screen)

    def on_next_chapter_loaded(self, event: NextChapterLoaded) -> None:
        self.current_chapter_id = event.chapter_id
        self.state.touch_last_saved()
        save(self.state.save_state, SAVES_DIR)
        self._load_chapter(event.chapter_id)

    def on_ending_reached(self, event: EndingReached) -> None:
        ending_id = event.ending_id
        if ending_id == "__END__":
            ending_id = _determine_ending(self.state)
        self.state.save_state.endings_achieved.append(ending_id)
        self.state.save_state.completed = True
        self.state.touch_last_saved()
        save(self.state.save_state, SAVES_DIR)
        self.push_screen(EndingScreen(ending_id))
