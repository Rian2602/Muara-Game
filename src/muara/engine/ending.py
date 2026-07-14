"""Shared ending logic — used by both CLI and GUI frontends."""

from __future__ import annotations

from muara.engine.state import GameState
from muara.models.chapter import Scene


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
        "[bold]— TAMAT: DIPERCAYA —[/bold]\n\n"
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


def determine_ending(state: GameState) -> str:
    """Determine ending based on cumulative flags."""
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


def resolve_text(scene: Scene, state: GameState) -> str:
    """Resolve conditional text variants for a scene."""
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
