# Specification: Perbaikan Label Section AGENTS.md

## Overview

Track ini memperbaiki satu anomali dokumentasi di `AGENTS.md` sebelum Track 1
(World & Time Layer) dan track-track berikutnya dimulai. Ini BUKAN bagian dari
15-level roadmap ChatGPT — ini adalah prasyarat kebersihan dokumentasi yang
ditemukan saat audit repo.

## Background

`AGENTS.md` memiliki section berjudul **"New Features (Cultivation World Simulator
Adaptation)"** yang mendeskripsikan: Multi-Slot Saves, Typewriter Effect, Scene
Hooks (on_enter/on_exit), GUI Save Slot Selection, Enhanced GameState.

Judul section ini tidak konsisten dengan identitas proyek:
- `README.md` menegaskan: "CLI/GUI narrative game set in colonial-era Batavia, 1899"
- `docs/00_WORLD_BIBLE.md` menegaskan: prequel dari naskah "Structure Needs Chaos"
- Tidak ada satu pun chapter YAML, flag, atau ending yang menyebut "cultivation",
  "kultivasi", atau elemen genre xianxia/wuxia manapun

Fitur teknis yang dideskripsikan di section itu **nyata dan sudah berfungsi** (sudah
diverifikasi lewat pembacaan `state.py`, `save_manager.py`, `render_cli.py`,
`chapter_runner.py`, dan lulus test `test_new_features.py`). Yang keliru murni
judul/framing section, bukan isinya. Kemungkinan besar berasal dari boilerplate
proyek lain yang ikut ter-commit saat fitur-fitur ini ditambahkan.

## Functional Requirements

### 1. Ganti judul section
Judul "New Features (Cultivation World Simulator Adaptation)" diganti menjadi
"New Features (Engine Enhancements)" atau judul netral setara yang tidak menyiratkan
genre/tema yang tidak ada di proyek ini.

### 2. Audit isi section untuk sisa kontaminasi lain
Baca ulang seluruh section tersebut baris per baris. Jika ada istilah, contoh kode,
atau penjelasan lain yang menyinggung tema di luar Batavia 1899/Rasmi/mandor
(misalnya nama variabel atau contoh yang tidak related), laporkan temuan tersebut
sebagai catatan terpisah — JANGAN dihapus otomatis tanpa dicatat, karena bisa jadi
false positive.

### 3. Tidak ada perubahan kode
Track ini murni perubahan teks di `AGENTS.md`. Tidak ada file `.py` atau `.yaml`
yang disentuh.

## Non-Functional Requirements

- Seluruh 268 test yang ada harus tetap lulus setelah perubahan ini (perubahan
  murni dokumentasi, jadi ini adalah sanity check, bukan ekspektasi risiko).

## Acceptance Criteria

- [x] Judul section diganti, tidak lagi menyebut "Cultivation" atau istilah genre
      yang tidak sesuai
- [x] Isi section (deskripsi fitur) tidak diubah kecuali ditemukan kontaminasi lain
      yang dilaporkan eksplisit ke user untuk keputusan lanjut
- [x] `uv run pytest tests/ -v` tetap 268 passed (atau jumlah saat ini pada saat
      track dieksekusi, jika sudah bertambah dari track lain)
- [x] Tidak ada file `.py`/`.yaml` yang tersentuh

## Out of Scope

- Perubahan pada `docs/00_WORLD_BIBLE.md` atau `docs/01_CHARACTER_PLOT_BRIEF.md`
- Investigasi asal-usul boilerplate (bukan prioritas — cukup diperbaiki)
- Perubahan pada `conductor/` files lain

## Dependencies

Tidak ada. Track ini bisa dieksekusi kapan saja, independen dari track lain.

## Risks

1. **Over-correction** — Big Pickle menghapus konten yang sebenarnya valid karena
   terlalu agresif mencari "kontaminasi"
   - Mitigasi: Task eksplisit meminta laporan sebelum penghapusan apa pun di luar
     judul section
