from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

from rich.console import Console

from muara.constants import END_OF_STORY_MARKER
from muara.engine.chapter_loader import ChapterLoadError, load_chapter, load_manifest
from muara.engine.chapter_runner import ChapterRunError, ChapterRunner
from muara.engine.ending import ENDING_TEXTS, determine_ending
from muara.engine.render_cli import CLIRenderer
from muara.engine.render_protocol import Renderer
from muara.engine.save_manager import SaveLoadError, list_saves, load, save
from muara.engine.state import GameState

if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys._MEIPASS)
    PROJECT_ROOT = Path(sys.executable).parent
    CONTENT_DIR = BUNDLE_DIR / "content"
    CHAPTERS_DIR = CONTENT_DIR / "chapters"
    SAVES_DIR = PROJECT_ROOT / "saves"
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    CONTENT_DIR = PROJECT_ROOT / "content"
    CHAPTERS_DIR = CONTENT_DIR / "chapters"
    SAVES_DIR = PROJECT_ROOT / "saves"

DEFAULT_SAVE_ID = "default"


def _format_elapsed(start: "datetime", end: "datetime") -> str:
    from datetime import datetime as _dt

    elapsed = (end - start).total_seconds()
    hours, remainder = divmod(int(elapsed), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _prompt_new_or_continue(
    renderer: Renderer,
    existing_saves: list[str],
    chapter_sequence: list[str],
    input_fn: Callable[[str], str] = input,
) -> tuple[str, "GameState | None"]:
    renderer.render_line("\n[bold]Selamat datang di Muara.[/bold]\n")
    if not existing_saves:
        renderer.render_line("Tidak ada save sebelumnya. Memulai permainan baru.\n")
        return "new", None

    try:
        save_state = load(DEFAULT_SAVE_ID, SAVES_DIR)
    except SaveLoadError as exc:
        renderer.render_line(f"[bold red]Gagal memuat save: {exc}[/bold red]")
        renderer.render_line("Memulai permainan baru.\n")
        return "new", None

    if save_state.completed or save_state.current_chapter == END_OF_STORY_MARKER:
        if not save_state.completed:
            save_state.completed = True
        endings = ", ".join(save_state.endings_achieved) if save_state.endings_achieved else "belum ada"
        renderer.render_line(f"Save ditemukan: permainan sudah tamat.")
        renderer.render_line(f"Ending tercapai: {endings}\n")
        while True:
            answer = input_fn("Mulai permainan baru? (y/n): ").strip().lower()
            if answer in ("y", "yes", "ya"):
                return "new", None
            if answer in ("n", "no", "tidak"):
                return "continue", GameState(save_state)
            renderer.render_line("Jawab 'y' atau 'n'.")
    else:
        chapter_title = "Unknown"
        for ch_id in chapter_sequence:
            if ch_id == save_state.current_chapter:
                try:
                    ch_path = CHAPTERS_DIR / f"{ch_id}.yaml"
                    if ch_path.exists():
                        ch = load_chapter(ch_path)
                        chapter_title = ch.title
                except ChapterLoadError:
                    pass
                break
        elapsed_str = _format_elapsed(save_state.playthrough_start, save_state.last_saved)
        renderer.render_line(f"[bold]Save:[/bold] {chapter_title}")
        renderer.render_line(f"  Bab: {save_state.current_chapter}")
        renderer.render_line(f"  Waktu bermain: {elapsed_str}")
        renderer.render_line(
            f"  Terakhir disimpan: "
            f"{save_state.last_saved.strftime('%d %b %Y, %H:%M')}"
        )
        if save_state.flags:
            key_flags = []
            if save_state.flags.get("berbicara_dengan_jaya"):
                key_flags.append("Jaya")
            if save_state.flags.get("melihat_anomali"):
                key_flags.append("Anomali")
            if save_state.flags.get("melapor"):
                key_flags.append("Lapor")
            if save_state.flags.get("percaya_jaya"):
                key_flags.append("Percaya Jaya")
            if save_state.flags.get("konfrontasi_berhasil"):
                key_flags.append("Konfrontasi")
            if key_flags:
                renderer.render_line(f"  Pilihan kunci: {', '.join(key_flags)}")
        renderer.render_line()
        while True:
            answer = input_fn("Lanjutkan permainan? (y/n): ").strip().lower()
            if answer in ("y", "yes", "ya"):
                return "continue", GameState(save_state)
            if answer in ("n", "no", "tidak"):
                return "new", None
            renderer.render_line("Jawab 'y' atau 'n'.")


def _resolve_chapter_sequence(renderer: Renderer) -> list[str]:
    try:
        manifest_chapters = load_manifest(CONTENT_DIR)
    except ChapterLoadError as exc:
        renderer.render_line(f"[bold red]Gagal membaca manifest: {exc}[/bold red]")
        sys.exit(1)

    if manifest_chapters:
        return manifest_chapters

    renderer.render_line(
        "[dim yellow]manifest.yaml masih kosong (Fase 4 belum dikerjakan). "
        "Fallback: memuat semua file di content/chapters/ untuk keperluan "
        "verifikasi Fase 3.[/dim yellow]\n"
    )
    fallback_ids: list[str] = []
    for yaml_file in sorted(CHAPTERS_DIR.glob("*.yaml")):
        try:
            chapter = load_chapter(yaml_file)
        except ChapterLoadError as exc:
            renderer.render_line(f"[bold red]{exc}[/bold red]")
            sys.exit(1)
        fallback_ids.append(chapter.id)

    if not fallback_ids:
        renderer.render_line(
            "[bold red]Tidak ada file bab di content/chapters/ sama sekali. "
            "Tidak ada yang bisa dijalankan.[/bold red]"
        )
        sys.exit(1)
    return fallback_ids


def _find_chapter_path_by_id(chapter_id: str, renderer: Renderer) -> Path:
    convention_path = CHAPTERS_DIR / f"{chapter_id}.yaml"
    if convention_path.exists():
        return convention_path

    for yaml_file in sorted(CHAPTERS_DIR.glob("*.yaml")):
        try:
            chapter = load_chapter(yaml_file)
        except ChapterLoadError as exc:
            renderer.render_line(f"[bold red]{exc}[/bold red]")
            sys.exit(1)
        if chapter.id == chapter_id:
            return yaml_file

    renderer.render_line(
        f"[bold red]Chapter id {chapter_id!r} tidak ditemukan di file mana pun "
        f"dalam content/chapters/.[/bold red]"
    )
    sys.exit(1)


def run() -> None:
    console = Console()
    renderer = CLIRenderer(console)

    chapter_sequence = _resolve_chapter_sequence(renderer)

    existing_saves = list_saves(SAVES_DIR)
    action, existing_state = _prompt_new_or_continue(
        renderer, existing_saves, chapter_sequence
    )

    if action == "continue" and existing_state is not None:
        state = existing_state
        current_chapter_id = save_state.current_chapter if (save_state := existing_state.save_state) else chapter_sequence[0]
        start_scene_id = save_state.current_scene if save_state and not save_state.completed else None
    else:
        current_chapter_id = chapter_sequence[0]
        state = GameState.new_playthrough(
            save_id=DEFAULT_SAVE_ID,
            chapter_id=current_chapter_id,
            scene_id="",
        )
        start_scene_id = None

    while current_chapter_id is not None:
        chapter_path = _find_chapter_path_by_id(current_chapter_id, renderer)
        try:
            chapter = load_chapter(chapter_path)
        except ChapterLoadError as exc:
            renderer.render_line(f"[bold red]{exc}[/bold red]")
            sys.exit(1)

        chapter_index = chapter_sequence.index(current_chapter_id) + 1
        total_chapters = len(chapter_sequence)

        runner = ChapterRunner(
            chapter,
            state,
            renderer,
            chapter_index=chapter_index,
            total_chapters=total_chapters,
        )
        try:
            next_chapter_id = runner.run(start_scene_id=start_scene_id)
        except ChapterRunError as exc:
            renderer.render_line(f"[bold red]Kesalahan struktur bab: {exc}[/bold red]")
            sys.exit(1)

        start_scene_id = None

        if next_chapter_id and next_chapter_id.startswith("__ENDING__:"):
            ending_id = next_chapter_id.split(":", 1)[1]
            state.save_state.endings_achieved.append(ending_id)
            state.save_state.completed = True
            next_chapter_id = None
        elif next_chapter_id == END_OF_STORY_MARKER:
            ending_id = determine_ending(state)
            state.save_state.endings_achieved.append(ending_id)
            state.save_state.completed = True
            next_chapter_id = None
        elif next_chapter_id:
            state.advance_to(next_chapter_id, "")
        else:
            ending_id = determine_ending(state)
            state.save_state.endings_achieved.append(ending_id)
            state.save_state.completed = True

        state.touch_last_saved()
        save_path = save(state.save_state, SAVES_DIR)
        renderer.render_line(
            f"[dim]✓ Progres tersimpan — {chapter.title}, "
            f"{chapter.date} {chapter.time}[/dim]\n"
        )

        current_chapter_id = next_chapter_id

    if state.save_state.endings_achieved:
        last_ending = state.save_state.endings_achieved[-1]
        if last_ending in ENDING_TEXTS:
            renderer.render_line()
            renderer.render_line(ENDING_TEXTS[last_ending])
            renderer.render_line()
        else:
            renderer.render_line(f"\n[bold]— TAMAT: {last_ending.upper()} —[/bold]\n")
    else:
        renderer.render_line("\n[bold]— Tamat (untuk sekarang) —[/bold]\n")


main = run

if __name__ == "__main__":
    run()
