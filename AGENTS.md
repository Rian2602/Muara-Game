# AGENTS.md — Muara CLI Narrative Engine

## Peran Agent di Proyek Ini

Opencode/Claude Code digunakan untuk dua jenis pekerjaan:
1. **Menulis konten naratif** — file YAML di `content/chapters/`
2. **Mengimplementasikan fitur engine** — Python di `src/muara/`

## Bacaan Wajib Sebelum Mulai

Untuk pekerjaan apapun:
- `docs/02_TECHNICAL_ARCHITECTURE.md` — keputusan stack dan arsitektur

Untuk pekerjaan konten naratif:
- `docs/00_WORLD_BIBLE.md` — **WAJIB DIBACA**, kanon yang tidak boleh dilanggar
- `docs/01_CHARACTER_PLOT_BRIEF.md` — opsi karakter yang sudah diputuskan

## Project Structure

```
src/muara/
├── constants.py           # Shared constants (END_OF_STORY_MARKER)
├── main.py              # CLI entry point (main = run), ending logic
├── models/
│   ├── chapter.py       # Chapter, Scene, Choice, ChoiceOption, FlagAssignment, TextVariant
│   └── save_state.py    # SaveState (Pydantic, extra="forbid")
└── engine/
    ├── chapter_loader.py  # load_chapter(), load_manifest(), load_all_chapters()
    ├── chapter_runner.py  # ChapterRunner — input injection via input_fn, text_variants
    ├── renderer.py        # Pure rendering (console.print only, no input)
    ├── save_manager.py    # save(), load(), list_saves()
    └── state.py           # GameState — flag store, evaluate_condition(), advance_to()
```

## Chapters

16 chapters total (01-06 original, 07-11 expansion). Chapters 01-04 have branching variants (a/b/c/d). Manifest order in `content/manifest.yaml`.

## Flags

### Original flags (chapters 01-06)
`melihat_anomali`, `berbicara_dengan_jaya`, `melapor`, `sembunyikan_bukti`, `terus_mencatat`, `menyimpan_bukti`, `beri_bukti_ke_jaya`, `menghadapi_mandor`, `bukti_kuat`, `trust_level`, `chapter_4_choice`, `chapter_5_choice`

### Expansion flags (chapters 07-11)
`ancaman_diketahui`, `respon_ancaman`, `percaya_jaya`, `tekanan_meningkat`, `pengorbanan`, `bukti_tersembunyi`, `konfrontasi_berhasil`, `kebenaran_terungkap`, `warisan_positif`, `cerita_tertulis`

## Endings (6 total)

| Ending | Condition |
|--------|-----------|
| `pembebasan` | `kebenaran_terungkap == true` AND `warisan_positif == true` |
| `kehancuran` | `konfrontasi_berhasil == false` OR `tekanan_meningkat >= 8` |
| `sekutu` | `beri_bukti_ke_jaya == true` AND `bukti_kuat == true` |
| `dipercaya` | `melapor == true` + `simpan`, or `trust_level >= 5` |
| `dicurigai` | `melapor == true` (without simpan) |
| `terlupakan` | default / `chapter_5_choice == hancurkan` |

## Workflow Wajib

```
1. Baca file yang relevan (lihat "Bacaan Wajib" di atas)
2. Buat atau edit file
3. Jalankan: uv run pytest tests/ -v
4. Semua test harus lulus sebelum commit
5. Commit dengan pesan yang deskriptif
```

**JANGAN** melanjutkan jika ada test yang gagal. Debug dulu.

## Naming Conventions

- **Chapter ID** = YAML filename (without `.yaml`): `01_pembukaan` → `01_pembukaan.yaml`
- **Scene ID**: `scene_1`, `scene_2`, `scene_3a`, `scene_3b` (use `a`/`b` suffixes for branching paths)
- **Flag keys**: `snake_case` Indonesian, past tense for actions: `melapor`, `melihat_asing`, `menyimpan_bukti`
- **Flag values**: `true`/`false` (bool preferred), `int` for counts, `str` only when necessary

## Konvensi Konten (YAML Bab)

### Naming convention — WAJIB
- `chapter.id` HARUS sama dengan nama file tanpa `.yaml`
  - Benar: file `05_pulang.yaml`, id: `"05_pulang"`
  - Salah: file `05_pulang.yaml`, id: `"bab_lima"` ← engine tidak bisa menemukannya

### Struktur file bab
```yaml
id: "NN_nama_singkat"          # sama dengan nama file
title: "JUDUL DALAM CAPS"      # gaya bahasa Inggris seperti naskah sumber
location: "Nama Tempat, Kota"
date: "DD Bulan YYYY"
time: "HH.MM"
scenes:
  - id: "scene_1"
    text: |
      [Narasi POV orang pertama, present tense.]
  - id: "scene_2"
    text: |
      [Berlanjut.]
    choice:
      prompt: "Apa yang kamu lakukan?"
      options:
        - id: "opsi_a"
          label: "Label opsi yang ditampilkan ke pemain"
          next: "scene_3a"           # ← HARUS scene_id yang ada di file ini
          set_flags:
            - "nama_flag: true"      # format: "key: value"
        - id: "opsi_b"
          label: "Label opsi lain"
          next: "scene_3b"
          set_flags:
            - "nama_flag: false"
  - id: "scene_3a"
    text: |
      [Konsekuensi opsi A.]
    next_chapter: "id_bab_berikutnya"
  - id: "scene_3b"
    text: |
      [Konsekuensi opsi B.]
    next_chapter: "id_bab_berikutnya"
```

### Flag naming
- Selalu `snake_case`
- Deskriptif dari **aksi pemain**, bukan outcome: `melapor_ke_mandor`, bukan `laporan_diterima`
- Boolean untuk pilihan biner: `melapor: true` / `melapor: false`

### Scene branching pattern
- Scene linear: `scene_1`, `scene_2`, `scene_3`
- Scene hasil branching: `scene_3a`, `scene_3b` (suffix huruf, bukan angka)
- Scene terakhir selalu punya `next_chapter`; scene sebelumnya yang punya pilihan pakai `choice`
- **Satu scene tidak boleh punya `choice` DAN `next_chapter` sekaligus**

### Setelah menulis bab baru
1. Tambahkan id bab ke `content/manifest.yaml` di posisi naratif yang tepat (bukan selalu di akhir)
2. Jalankan full test: `uv run pytest tests/ -v`

### Text Variants
Scenes can have conditional text based on flags:
```yaml
scenes:
  - id: "scene_2"
    text: |
      [Default text when no condition matches.]
    text_variants:
      - condition: "chapter_5_choice == simpan"
        text: |
          [Text shown when chapter_5_choice is "simpan".]
      - condition: "chapter_5_choice == hancurkan"
        text: |
          [Text shown when chapter_5_choice is "hancurkan".]
        default: true  # ← fallback if no condition matches
```
- One variant MUST have `default: true`
- `text` field is required on the scene (even if overridden by variants)
- Conditions use the same syntax as `evaluate_condition()`: `==`, `!=`, `>=`, `not`

## Validation Rules (enforced by Pydantic)

- `Choice` requires ≥ 2 options with unique IDs
- `Scene.text` must not be blank
- `Scene.choice` and `Scene.next_chapter` are mutually exclusive — pick one
- `Chapter.scenes` must have ≥ 1 scene with unique IDs
- `ChoiceOption.next` must reference a scene ID that exists in the same chapter
- `FlagAssignment.from_raw_string` accepts `"key: true"`, `"key: false"`, `"key: -5"`, `"key: word"`
- All models use `extra="forbid"` — no typos in YAML keys

## Prose Style (World Bible §6)

- POV orang pertama, present-tense reflektif
- Sensory before emotional (suhu, tekstur, bau, bunyi)
- Short repetitive sentences for emphasis
- Precise administrative details contrasted with intangible
- No exposition dumps — world details via passing mention

## Batasan Konten — WAJIB DIPATUHI

- **JANGAN** membuat karakter yang identik atau merupakan salah satu dari 8 garis kanon tertutup: Sutisna, Kusuma, Rusli, Indra, Bella, Lottie, Vivi, Emiko (lihat World Bible §2)
- **JANGAN** menempatkan karakter baru di lokasi/tahun yang sama persis dengan momen kanon yang sudah tertulis (lihat World Bible §3)
- **JANGAN** menambah objek motif berulang (caliper, kotak kayu, bola kaca, serbet Birdland) dengan origin story berbeda dari yang tersirat di World Bible §5
- **BOLEH** membuat karakter baru yang bersinggungan dengan dunia yang sama tanpa menjadi bagian dari 8 garis

## Testing

```bash
uv run pytest tests/ -v          # all tests
uv run pytest tests/test_models.py -v   # model validation only
```

### Definition of Done for New Content

A chapter is done ONLY when:
1. It passes `test_content_integrity.py` (schema valid, all scene refs resolve)
2. It can be played through via `test_engine.py` playthrough helpers
3. The prose follows World Bible §6 style

### Key Test Patterns

- `make_runner(chapter_id, input_values=[...])` — single chapter with scripted input
- `run_chapter(chapter_id, state, input_sequence)` — single chapter, returns next_chapter
- Playthrough tests chain `run_chapter` across all chapters

## Code Conventions

- **Pydantic**: `extra="forbid"` on all models, `field_validator` for field-level checks, `model_validator` for cross-field
- **Error wrapping**: custom exceptions (`ChapterLoadError`, `SaveLoadError`, `ChapterRunError`) wrap library errors
- **Input injection**: `ChapterRunner(chapter, state, console, input_fn=...)` — never call `input()` directly in engine code
- **Renderer purity**: `renderer.py` only prints, never reads input
- **Timezone**: always `datetime.now(timezone.utc)` — never naive datetimes
- **Constants**: `END_OF_STORY_MARKER` lives in `constants.py`, never hardcoded as `"__END__"`
