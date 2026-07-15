from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

from rich.console import Console
from rich.table import Table

from muara.constants import END_OF_STORY_MARKER
from muara.engine.chapter_loader import ChapterLoadError, load_chapter, load_manifest
from muara.engine.chapter_runner import ChapterRunError, ChapterRunner
from muara.engine.ending import ENDING_TEXTS, determine_ending
from muara.engine.event_loader import load_events, EventLoadError
from muara.engine.event_scheduler import EventScheduler
from muara.engine.render_cli import CLIRenderer
from muara.engine.render_protocol import Renderer
from muara.engine.save_manager import SaveLoadError, list_save_slots, load, save, delete_save, rename_save, SaveSlotInfo
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
MAX_SAVE_SLOTS = 10


def _format_elapsed(start: datetime, end: datetime) -> str:
    elapsed = (end - start).total_seconds()
    hours, remainder = divmod(int(elapsed), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _prompt_save_slot_selection(
    renderer: Renderer,
    chapter_sequence: list[str],
    input_fn: Callable[[str], str] = input,
) -> tuple[str, "GameState | None"]:
    """Prompt user to select a save slot or start a new game."""
    renderer.render_line("\n[bold]Selamat datang di Muara.[/bold]\n")
    
    save_slots = list_save_slots(SAVES_DIR)
    
    if not save_slots:
        renderer.render_line("Tidak ada save sebelumnya. Memulai permainan baru.\n")
        return "new", None
    
    # Display save slots
    table = Table(title="Save Slots")
    table.add_column("No", style="dim", width=4)
    table.add_column("Status", width=8)
    table.add_column("Chapter", width=20)
    table.add_column("Last Saved", width=20)
    table.add_column("Flags", width=15)
    
    for i, slot in enumerate(save_slots, 1):
        status = "[green]Tamat[/green]" if slot.completed else "[yellow]Bermain[/yellow]"
        chapter_title = "Unknown"
        for ch_id in chapter_sequence:
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
        table.add_row(str(i), status, chapter_title, slot.last_saved, flags)
    
    renderer.render_line(table)
    renderer.render_line()
    
    # Prompt for selection
    while True:
        answer = input_fn(
            f"Pilih save slot (1-{len(save_slots)}), 'b' baru, "
            f"'d'+nomor hapus, 'r'+nomor rename: "
        ).strip().lower()
        
        if answer in ("b", "baru", "new"):
            return "new", None
        
        # Delete save: d1, d2, etc.
        if answer.startswith("d") and answer[1:].isdigit():
            index = int(answer[1:]) - 1
            if 0 <= index < len(save_slots):
                selected_slot = save_slots[index]
                confirm = input_fn(
                    f"Hapus save '{selected_slot.save_id}'? (y/n): "
                ).strip().lower()
                if confirm in ("y", "ya", "yes"):
                    try:
                        delete_save(selected_slot.save_id, SAVES_DIR)
                        renderer.render_line(
                            f"[green]✓ Save '{selected_slot.save_id}' dihapus.[/green]"
                        )
                        save_slots = list_save_slots(SAVES_DIR)
                        if not save_slots:
                            return "new", None
                        continue
                    except Exception as exc:
                        renderer.render_line(f"[bold red]Gagal menghapus save: {exc}[/bold red]")
                        continue
        
        # Rename save: r1, r2, etc.
        if answer.startswith("r") and answer[1:].isdigit():
            index = int(answer[1:]) - 1
            if 0 <= index < len(save_slots):
                selected_slot = save_slots[index]
                new_name = input_fn(
                    f"Nama baru untuk '{selected_slot.save_id}': "
                ).strip()
                if new_name and new_name != selected_slot.save_id:
                    try:
                        rename_save(selected_slot.save_id, new_name, SAVES_DIR)
                        renderer.render_line(
                            f"[green]✓ Save renamed ke '{new_name}'.[/green]"
                        )
                        save_slots = list_save_slots(SAVES_DIR)
                        continue
                    except Exception as exc:
                        renderer.render_line(f"[bold red]Gagal rename save: {exc}[/bold red]")
                        continue
        
        if answer.isdigit():
            index = int(answer) - 1
            if 0 <= index < len(save_slots):
                selected_slot = save_slots[index]
                try:
                    save_state = load(selected_slot.save_id, SAVES_DIR)
                    return "continue", GameState(save_state)
                except SaveLoadError as exc:
                    renderer.render_line(f"[bold red]Gagal memuat save: {exc}[/bold red]")
                    continue
        
        renderer.render_line("Jawab tidak valid. Coba lagi.")


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


def run(input_fn: Callable[[str], str] = input) -> None:
    import argparse
    
    parser = argparse.ArgumentParser(description="Muara - Narrative Game")
    parser.add_argument(
        "--typewriter",
        action="store_true",
        help="Enable typewriter effect for scene text",
    )
    parser.add_argument(
        "--typewriter-delay",
        type=float,
        default=0.03,
        help="Delay between characters in typewriter effect (seconds)",
    )
    args = parser.parse_args()
    
    console = Console()
    renderer = CLIRenderer(
        console,
        typewriter=args.typewriter,
        typewriter_delay=args.typewriter_delay,
    )

    chapter_sequence = _resolve_chapter_sequence(renderer)

    action, existing_state = _prompt_save_slot_selection(
        renderer, chapter_sequence, input_fn=input_fn
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

    # Load world events for event scheduler
    scheduler: EventScheduler | None = None
    events_file = CONTENT_DIR / "events.yaml"
    if events_file.exists():
        try:
            events = load_events(events_file)
            scheduler = EventScheduler(events)
        except EventLoadError:
            pass  # Event loading failed, continue without scheduler

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
            input_fn=input_fn,
            chapter_index=chapter_index,
            total_chapters=total_chapters,
            scheduler=scheduler,
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
