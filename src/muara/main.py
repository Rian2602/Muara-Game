from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

from rich.console import Console

from muara.constants import END_OF_STORY_MARKER
from muara.engine.chapter_loader import ChapterLoadError, load_chapter, load_manifest
from muara.engine.chapter_runner import ChapterRunError, ChapterRunner
from muara.engine.save_manager import SaveLoadError, list_saves, load, save
from muara.engine.state import GameState

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTENT_DIR = PROJECT_ROOT / "content"
CHAPTERS_DIR = CONTENT_DIR / "chapters"
SAVES_DIR = PROJECT_ROOT / "saves"

DEFAULT_SAVE_ID = "default"

ENDING_TEXTS = {
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
        "Lalu dia menutup buku dan berkata: \"Kamu harus berhenti mencatat. "
        "Ini bukan urusanmu.\"\n\n"
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
    """Determine ending based on cumulative flags."""
    kebenaran_terungkap = state.get_flag("kebenaran_terungkap")
    warisan_positif = state.get_flag("warisan_positif")
    konfrontasi_berhasil = state.get_flag("konfrontasi_berhasil")
    tekanan_meningkat = state.get_flag("tekanan_meningkat", 0)

    if kebenaran_terungkap is True and warisan_positif is True:
        return "pembebasan"
    if konfrontasi_berhasil is False or (
        isinstance(tekanan_meningkat, int) and tekanan_meningkat >= 8
    ):
        return "kehancuran"

    melapor = state.get_flag("melapor")
    bukti_kuat = state.get_flag("bukti_kuat")
    beri_bukti_ke_jaya = state.get_flag("beri_bukti_ke_jaya")
    chapter_5_choice = state.get_flag("chapter_5_choice")
    trust_level = state.get_flag("trust_level", 0)

    if beri_bukti_ke_jaya is True and bukti_kuat is True:
        return "sekutu"
    if melapor is True and chapter_5_choice == "simpan":
        return "dipercaya"
    if bukti_kuat is True and chapter_5_choice == "simpan":
        return "dipercaya"
    if chapter_5_choice == "hancurkan":
        return "terlupakan"
    if isinstance(trust_level, int) and trust_level >= 5:
        return "dipercaya"
    if melapor is True:
        return "dicurigai"
    return "terlupakan"


def _format_elapsed(start: "datetime", end: "datetime") -> str:
    from datetime import datetime as _dt

    elapsed = (end - start).total_seconds()
    hours, remainder = divmod(int(elapsed), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _prompt_new_or_continue(
    console: Console,
    existing_saves: list[str],
    chapter_sequence: list[str],
    input_fn: Callable[[str], str] = input,
) -> tuple[str, "GameState | None"]:
    console.print("\n[bold]Selamat datang di Muara.[/bold]\n")
    if not existing_saves:
        console.print("Tidak ada save sebelumnya. Memulai permainan baru.\n")
        return "new", None

    try:
        save_state = load(DEFAULT_SAVE_ID, SAVES_DIR)
    except SaveLoadError as exc:
        console.print(f"[bold red]Gagal memuat save: {exc}[/bold red]")
        console.print("Memulai permainan baru.\n")
        return "new", None

    if save_state.completed:
        endings = ", ".join(save_state.endings_achieved) if save_state.endings_achieved else "belum ada"
        console.print(f"Save ditemukan: permainan sudah tamat.")
        console.print(f"Ending tercapai: {endings}\n")
        while True:
            answer = input_fn("Mulai permainan baru? (y/n): ").strip().lower()
            if answer in ("y", "yes", "ya"):
                return "new", None
            if answer in ("n", "no", "tidak"):
                return "continue", GameState(save_state)
            console.print("Jawab 'y' atau 'n'.")
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
        console.print(f"Save: {chapter_title}")
        console.print(
            f"{save_state.current_chapter} — {elapsed_str} dimainkan\n"
        )
        while True:
            answer = input_fn("Lanjutkan permainan? (y/n): ").strip().lower()
            if answer in ("y", "yes", "ya"):
                return "continue", GameState(save_state)
            if answer in ("n", "no", "tidak"):
                return "new", None
            console.print("Jawab 'y' atau 'n'.")


def _resolve_chapter_sequence(console: Console) -> list[str]:
    try:
        manifest_chapters = load_manifest(CONTENT_DIR)
    except ChapterLoadError as exc:
        console.print(f"[bold red]Gagal membaca manifest: {exc}[/bold red]")
        sys.exit(1)

    if manifest_chapters:
        return manifest_chapters

    console.print(
        "[dim yellow]manifest.yaml masih kosong (Fase 4 belum dikerjakan). "
        "Fallback: memuat semua file di content/chapters/ untuk keperluan "
        "verifikasi Fase 3.[/dim yellow]\n"
    )
    fallback_ids: list[str] = []
    for yaml_file in sorted(CHAPTERS_DIR.glob("*.yaml")):
        try:
            chapter = load_chapter(yaml_file)
        except ChapterLoadError as exc:
            console.print(f"[bold red]{exc}[/bold red]")
            sys.exit(1)
        fallback_ids.append(chapter.id)

    if not fallback_ids:
        console.print(
            "[bold red]Tidak ada file bab di content/chapters/ sama sekali. "
            "Tidak ada yang bisa dijalankan.[/bold red]"
        )
        sys.exit(1)
    return fallback_ids


def _find_chapter_path_by_id(chapter_id: str, console: Console) -> Path:
    convention_path = CHAPTERS_DIR / f"{chapter_id}.yaml"
    if convention_path.exists():
        return convention_path

    for yaml_file in sorted(CHAPTERS_DIR.glob("*.yaml")):
        try:
            chapter = load_chapter(yaml_file)
        except ChapterLoadError as exc:
            console.print(f"[bold red]{exc}[/bold red]")
            sys.exit(1)
        if chapter.id == chapter_id:
            return yaml_file

    console.print(
        f"[bold red]Chapter id {chapter_id!r} tidak ditemukan di file mana pun "
        f"dalam content/chapters/.[/bold red]"
    )
    sys.exit(1)


def run() -> None:
    console = Console()

    chapter_sequence = _resolve_chapter_sequence(console)

    existing_saves = list_saves(SAVES_DIR)
    action, existing_state = _prompt_new_or_continue(
        console, existing_saves, chapter_sequence
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
        chapter_path = _find_chapter_path_by_id(current_chapter_id, console)
        try:
            chapter = load_chapter(chapter_path)
        except ChapterLoadError as exc:
            console.print(f"[bold red]{exc}[/bold red]")
            sys.exit(1)

        chapter_index = chapter_sequence.index(current_chapter_id) + 1
        total_chapters = len(chapter_sequence)

        runner = ChapterRunner(
            chapter,
            state,
            console,
            chapter_index=chapter_index,
            total_chapters=total_chapters,
        )
        try:
            next_chapter_id = runner.run(start_scene_id=start_scene_id)
        except ChapterRunError as exc:
            console.print(f"[bold red]Kesalahan struktur bab: {exc}[/bold red]")
            sys.exit(1)

        start_scene_id = None

        if next_chapter_id and next_chapter_id.startswith("__ENDING__:"):
            ending_id = next_chapter_id.split(":", 1)[1]
            state.save_state.endings_achieved.append(ending_id)
            state.save_state.completed = True
            next_chapter_id = None
        elif next_chapter_id == END_OF_STORY_MARKER:
            ending_id = _determine_ending(state)
            state.save_state.endings_achieved.append(ending_id)
            state.save_state.completed = True
            next_chapter_id = None
        elif next_chapter_id:
            state.advance_to(next_chapter_id, "")
        else:
            ending_id = _determine_ending(state)
            state.save_state.endings_achieved.append(ending_id)
            state.save_state.completed = True

        state.touch_last_saved()
        save_path = save(state.save_state, SAVES_DIR)
        console.print(
            f"[dim]✓ Progres tersimpan — {chapter.title}, "
            f"{chapter.date} {chapter.time}[/dim]\n"
        )

        current_chapter_id = next_chapter_id

    if state.save_state.endings_achieved:
        last_ending = state.save_state.endings_achieved[-1]
        if last_ending in ENDING_TEXTS:
            console.print()
            console.print(ENDING_TEXTS[last_ending])
            console.print()
        else:
            console.print(f"\n[bold]— TAMAT: {last_ending.upper()} —[/bold]\n")
    else:
        console.print("\n[bold]— Tamat (untuk sekarang) —[/bold]\n")


main = run

if __name__ == "__main__":
    run()
