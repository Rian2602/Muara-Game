# TECHNICAL ARCHITECTURE — Muara CLI Narrative Engine

## 1. Pemilihan Stack

**Bahasa: Python 3.11+.** Alasan: tidak butuh performa tinggi (ini game teks,
bukan real-time), ekosistem library CLI TUI matang (`rich`, `textual`), JSON/YAML
parsing native, dan cocok dengan pola kerja Rian yang sudah ada di ekosistem
Python untuk AILex.

**Library inti:**
- `rich` — rendering teks CLI (warna, panel, format bab ala naskah sumber)
- `prompt_toolkit` atau `rich.prompt` — input pilihan dialog interaktif
- `pydantic` — validasi skema data bab/karakter (schema-first, sesuai kebiasaan
  kerja Rian di AILex/claude-obsidian yang selalu pakai skema tervalidasi)
- `pyyaml` — format file bab (lebih mudah ditulis/diedit manusia dibanding JSON
  untuk teks naratif panjang)

**TIDAK dipakai (dan kenapa):**
- Game engine besar (Godot/Ren'Py dsb) — ini eksplisit CLI text-based dioperasikan
  OpenCode, bukan visual engine.
- Database (SQLite dkk) untuk konten bab — konten bab adalah **data statis** yang
  ditulis manusia/agent, bukan data transaksional. File YAML per-bab lebih sesuai
  dan lebih mudah di-diff/review di git.
- Sistem stat/inventory/combat — sudah diputuskan game ini murni naratif.

---

## 2. Struktur Folder Proyek

```
muara-game/
├── README.md                      # ringkasan proyek + cara jalankan
├── pyproject.toml                 # dependency management (uv/poetry)
├── docs/
│   ├── 00_WORLD_BIBLE.md          # kanon dunia (sudah dibuat, copy ke sini)
│   ├── 01_CHARACTER_PLOT_BRIEF.md # brief karakter (sudah dibuat, copy ke sini)
│   └── 02_TECHNICAL_ARCHITECTURE.md
├── src/
│   └── muara/
│       ├── __init__.py
│       ├── main.py                # entry point CLI
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── chapter_loader.py  # load + validasi YAML bab
│       │   ├── chapter_runner.py  # jalankan satu bab: render teks, tangani pilihan
│       │   ├── save_manager.py    # save/load state pemain
│       │   ├── state.py           # model state: bab saat ini, pilihan yang diambil, flags
│       │   ├── render_cli.py      # render teks dengan rich (chapter header, dialog, dsb)
│       │   └── render_protocol.py # renderer protocol/interface
│       └── models/
│           ├── __init__.py
│           ├── chapter.py         # skema pydantic: Chapter, Scene, Choice
│           └── save_state.py      # skema pydantic: SaveState
├── content/
│   ├── chapters/
│   │   ├── 01_pembukaan.yaml
│   │   ├── 02_keputusan.yaml
│   │   └── ...                    # satu file YAML per bab
│   └── manifest.yaml              # urutan bab, metadata linimasa
├── saves/                         # save file pemain (gitignored, kecuali contoh)
│   └── .gitkeep
├── tests/
│   ├── test_chapter_loader.py
│   ├── test_chapter_runner.py
│   └── test_save_manager.py
└── .gitignore
```

---

## 3. Skema Data Bab (`content/chapters/*.yaml`)

Format bab mengikuti konvensi naskah sumber: setiap bab punya judul, lokasi,
tanggal, jam (lihat World Bible §6). Struktur di bawah dirancang agar bisa
ditulis manusia dengan mudah DAN divalidasi otomatis oleh pydantic.

```yaml
# content/chapters/01_pembukaan.yaml
id: "01_pembukaan"
title: "THE COUNTED SEN"          # judul bab, gaya bahasa Inggris seperti sumber
location: "Pergudangan Pelabuhan Sunda Kelapa, Batavia"
date: "3 Maret 1899"
time: "05.40"

# Urutan scene di dalam bab — dibaca berurutan, teks panjang dipecah
# supaya tidak satu wall-of-text raksasa di terminal
scenes:
  - id: "scene_1"
    text: |
      Teks naratif di sini. Bisa multi-paragraf.
      Ikuti gaya POV orang pertama, present-tense reflektif
      seperti naskah sumber.
    # scene tanpa 'choice' otomatis lanjut ke scene berikutnya
    # setelah pemain menekan Enter/lanjut

  - id: "scene_2"
    text: |
      Scene yang berakhir dengan keputusan pemain.
    choice:
      prompt: "Apa yang kamu lakukan?"
      options:
        - id: "lapor"
          label: "Laporkan apa yang kamu lihat ke mandor"
          # 'next' menentukan scene/bab berikutnya jika opsi ini dipilih
          next: "scene_3a"
          # 'set_flags' menyimpan konsekuensi ke save state untuk dibaca
          # bab-bab selanjutnya (tanpa perlu sistem stat/skor)
          set_flags:
            - "melapor_ke_mandor: true"
        - id: "diam"
          label: "Diam saja, pura-pura tidak melihat"
          next: "scene_3b"
          set_flags:
            - "melapor_ke_mandor: false"

  - id: "scene_3a"
    text: |
      Konsekuensi dari melapor.
    next_chapter: "02_keputusan"   # scene terakhir menentukan bab berikutnya

  - id: "scene_3b"
    text: |
      Konsekuensi dari diam.
    next_chapter: "02_keputusan"
```

**Kenapa `set_flags` dan bukan sistem stat/skor:** ini menjaga game tetap murni
naratif (branching dialog choices) sesuai keputusan awal, sambil tetap
memungkinkan pilihan awal memengaruhi teks/dialog di bab-bab berikutnya —
`chapter_runner.py` bisa membaca flag untuk menampilkan variasi teks
(lihat §5, conditional text) tanpa perlu UI stat/HP/dsb yang terlihat pemain.

---

## 4. Skema Save State (`models/save_state.py`)

```python
from pydantic import BaseModel
from datetime import datetime

class SaveState(BaseModel):
    save_id: str
    player_name: str | None = None          # jika game minta nama pemain
    current_chapter: str
    current_scene: str
    flags: dict[str, bool | str | int] = {}  # semua set_flags terkumpul di sini
    chapters_completed: list[str] = []
    last_saved: datetime
    playthrough_start: datetime
```

Save file disimpan sebagai JSON di `saves/<save_id>.json`. Autosave setelah
setiap bab selesai (bukan setiap scene — supaya tidak terlalu granular tapi
tetap aman dari kehilangan progres kalau CLI ditutup paksa).

---

## 5. Conditional Text (opsional, untuk fase lanjut)

Kalau nanti dibutuhkan dialog/teks yang berubah berdasar flag sebelumnya, skema
scene bisa diperluas dengan `text_variants`:

```yaml
  - id: "scene_5"
    text_variants:
      - condition: "melapor_ke_mandor == true"
        text: |
          Mandor mengingatmu sekarang. Ada yang berubah di caranya menyapa.
      - condition: "melapor_ke_mandor == false"
        text: |
          Tidak ada yang tahu apa yang kamu lihat pagi itu.
      - default: true
        text: |
          Teks fallback jika tidak ada flag relevan.
```

**Catatan implementasi:** untuk MVP awal, JANGAN implementasikan sistem
`condition` string-parsing yang rumit. Cukup dukung pengecekan flag boolean
sederhana lewat kode Python langsung di `chapter_runner.py` (dict lookup),
baru pindah ke mini expression parser kalau kompleksitas cerita benar-benar
membutuhkannya. Ini mencegah over-engineering di fase awal.

---

## 6. Alur Eksekusi (`main.py` → `chapter_runner.py`)

```
1. main.py: cek apakah ada save file → tanya lanjutkan atau mulai baru
2. chapter_loader.py: load + validasi YAML bab dari content/manifest.yaml
3. chapter_runner.py:
   a. render chapter header (judul, lokasi, tanggal, jam) via render_cli.py
   b. iterasi scene satu per satu
   c. render teks scene
   d. jika scene punya 'choice': tampilkan opsi, tunggu input, terapkan set_flags
   e. jika scene punya 'next_chapter': simpan progress, muat bab berikutnya
4. save_manager.py: autosave setelah setiap bab
```

---

## 7. Testing Strategy

Mengikuti pola kerja audit forensik yang biasa dipakai Rian (jalankan skrip
nyata, bukan hanya baca kode) — setiap komponen inti perlu test yang benar-benar
dieksekusi, bukan sekadar ditulis:

- `test_chapter_loader.py` — validasi bahwa SEMUA file YAML di `content/chapters/`
  ter-parse tanpa error dan sesuai skema pydantic (test ini harus jalan sebagai
  bagian dari setiap perubahan konten, bukan hanya perubahan kode).
- `test_chapter_runner.py` — simulasikan playthrough otomatis (pilih opsi
  pertama selalu, pilih opsi terakhir selalu) untuk memastikan tidak ada
  scene/bab yang tidak bisa dijangkau (broken link) atau dead-end yang tidak
  disengaja.
- `test_save_manager.py` — save lalu load, pastikan state identik.

**Definition of Done untuk setiap bab baru:** bab dianggap selesai HANYA jika
lulus `test_chapter_loader.py` (skema valid) DAN `test_chapter_runner.py` bisa
menjangkau semua scene di dalamnya tanpa error — bukan hanya karena teksnya
sudah ditulis.
