# AGENTS.md — Muara Narrative Engine

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
├── constants.py              # Shared constants (END_OF_STORY_MARKER)
├── main.py                   # CLI entry point (main = run), ending logic, argparse
├── gui_cli.py                # GUI entry point (muara-gui command)
├── models/
│   ├── chapter.py            # Chapter, Scene, Choice, ChoiceOption, FlagAssignment, TextVariant, FlagCondition
│   └── save_state.py         # SaveState (Pydantic, extra="forbid")
├── engine/
│   ├── chapter_loader.py     # load_chapter(), load_manifest(), load_all_chapters()
│   ├── chapter_runner.py     # ChapterRunner — sync CLI game loop (input injection via input_fn)
│   ├── render_protocol.py    # Renderer Protocol — interface for all backends
│   ├── render_cli.py         # CLIRenderer — Rich-based terminal rendering with typewriter
│   ├── renderer.py           # Legacy wrapper (backward compat for tests)
│   ├── save_manager.py       # save(), load(), list_saves(), list_save_slots(), delete_save(), rename_save()
│   └── state.py              # GameState — flag store, evaluate_condition(), advance_to(), increment_counter(), add_to_set()
└── gui/
    ├── __init__.py
    ├── app.py                # MuaraApp + GameScreen + SaveSlotScreen — async Textual GUI
    ├── screens.py            # EndingScreen
    ├── gui_cli.py            # Entry point for GUI mode
    └── muara.tcss            # Textual CSS stylesheet
```

## Dual Mode: CLI + GUI

Muara supports two frontends sharing the same engine:

| Mode | Command | Frontend | Engine |
|------|---------|----------|--------|
| CLI | `uv run muara` | Rich terminal | `ChapterRunner` (sync while-loop) |
| GUI | `uv run muara-gui` | Textual TUI | `GameScreen` (async state machine) |

Both modes use the same:
- `engine/state.py` — GameState, flag store, condition evaluation
- `engine/chapter_loader.py` — YAML loading
- `engine/save_manager.py` — JSON persistence
- `models/` — Pydantic data models
- `content/` — YAML chapters

### Renderer Protocol

`engine/render_protocol.py` defines the `Renderer` interface:
```python
class Renderer(Protocol):
    def render_chapter_header(self, title, location, date, time, ...) -> None: ...
    def render_scene_text(self, text: str) -> None: ...
    def render_choice_prompt(self, prompt, options) -> None: ...
    def render_continue_prompt(self) -> None: ...
    def render_error(self, message: str) -> None: ...
    def render_line(self, text: str = "") -> None: ...
```

- `CLIRenderer` (`render_cli.py`) — implements for Rich console
- GUI mode (`gui/app.py`) — implements inline in `GameScreen` (does not use `ChapterRunner`)

### GUI Architecture

The GUI (`gui/app.py`) does NOT use `ChapterRunner`. Instead:
- `GameScreen` is an async state machine driven by Textual events
- Scene traversal happens via `_show_current_scene()` triggered by user input
- Choices use `OptionList` widget with `on_option_list_option_selected` handler
- Linear continuation uses `action_continue()` bound to Enter key
- `NextChapterLoaded` and `EndingReached` messages drive chapter transitions

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
| `pembebasan` | `kebenaran_terungkap == true` AND `warisan_positif == true` AND `melihat_anomali == true` |
| `kehancuran` | `konfrontasi_berhasil == false` OR `tekanan_meningkat >= 6` |
| `sekutu` | `beri_bukti_ke_jaya == true` AND `bukti_kuat == true` AND `berbicara_dengan_jaya == true` |
| `dipercaya` | (`melapor == true` AND `chapter_5_choice == simpan`) OR (`bukti_kuat == true` AND `chapter_5_choice == simpan`) |
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
uv run pytest tests/test_narrative_graph.py -v  # narrative graph validation
```

### Definition of Done for New Content

A chapter is done ONLY when:
1. It passes `test_content_integrity.py` (schema valid, all scene refs resolve)
2. It can be played through via `test_engine.py` playthrough helpers
3. The prose follows World Bible §6 style
4. All flags set by choices are checked somewhere (text_variants or ending logic)

### Key Test Patterns

- `make_runner(chapter_id, input_values=[...])` — single chapter with scripted input
- `run_chapter(chapter_id, state, input_sequence)` — single chapter, returns next_chapter
- Playthrough tests chain `run_chapter` across all chapters
- Narrative graph tests validate structural integrity (no orphans, no dead ends, no unreachable scenes)

## Code Conventions

- **Pydantic**: `extra="forbid"` on all models, `field_validator` for field-level checks, `model_validator` for cross-field
- **Error wrapping**: custom exceptions (`ChapterLoadError`, `SaveLoadError`, `ChapterRunError`) wrap library errors
- **Input injection**: `ChapterRunner(chapter, state, console, input_fn=...)` — never call `input()` directly in engine code
- **Renderer purity**: `renderer.py` only prints, never reads input
- **Timezone**: always `datetime.now(timezone.utc)` — never naive datetimes
- **Constants**: `END_OF_STORY_MARKER` lives in `constants.py`, never hardcoded as `"__END__"`

## New Features (Engine Enhancements)

### World & Time Layer (Game Clock & Event Scheduler)

Muara sekarang memiliki representasi waktu dunia (`world_clock`) dan event scheduler:

- `WorldClock` berjalan dengan siklus `day` (hari ke-N) dan `shift` (pagi, siang, malam).
- Flag turunan `world_day` dan `world_shift` disinkronkan otomatis dan dapat dibaca melalui `evaluate_condition()`.
- **CATATAN PENTING**: Jangan pernah mengatur flag `world_day` atau `world_shift` secara manual (misal lewat `set_flags` di pilihan), karena ini adalah flag turunan yang akan tertimpa saat clock maju.
- Hook baru `advance_clock(shift)` dan `advance_clock(day)` dapat digunakan di `on_enter` atau `on_exit` YAML scene untuk memajukan waktu dunia. Contoh:
  ```yaml
  scenes:
    - id: "scene_5"
      text: "Malam turun. Aku menutup buku kecilku."
      on_exit:
        - "advance_clock(shift)"
      next_chapter: "next_chapter_id"
  ```
- File `content/events.yaml` dapat digunakan untuk mendaftarkan kejadian dunia berdasarkan trigger tertentu (hari, shift, atau kondisi flag), di mana efek flag akan diterapkan secara otomatis saat kondisi terpenuhi.
- **KNOWN LIMITATION (Batasan Diketahui):** Saat ini, eksekusi event scheduler dan hook `advance_clock` hanya beroperasi di mode CLI (`ChapterRunner`). Integrasi pada mode GUI (`gui/app.py`) **belum diimplementasikan** karena mode GUI saat ini tidak mengeksekusi lifecycle hook (`on_enter`/`on_exit`). Detail keputusan desain ini dapat dilihat di dokumen Track 1.

### Multi-Slot Saves

The save system now supports multiple save slots with metadata:

```python
from muara.engine.save_manager import (
    list_save_slots,      # Returns list[SaveSlotInfo] with metadata
    delete_save,          # Delete a save file
    rename_save,          # Rename a save file
)

# List all saves with metadata
slots = list_save_slots(saves_dir)
for slot in slots:
    print(f"{slot.save_id}: {slot.current_chapter}, flags={slot.key_flags}")
```

**SaveSlotInfo model:**
- `save_id`: Unique identifier
- `player_name`: Optional player name
- `current_chapter`: Current chapter ID
- `current_scene`: Current scene ID
- `completed`: Whether game is finished
- `last_saved`: Timestamp string
- `key_flags`: Important flags for display

### Typewriter Effect

CLI renderer supports typewriter effect for scene text:

```python
from muara.engine.render_cli import CLIRenderer
from rich.console import Console

console = Console()
renderer = CLIRenderer(
    console,
    typewriter=True,           # Enable typewriter effect
    typewriter_delay=0.03,     # Seconds between characters
)
```

**CLI arguments:**
```bash
uv run muara --typewriter
uv run muara --typewriter --typewriter-delay 0.05
```

### Scene Hooks (on_enter/on_exit)

Scenes can now have transition hooks that execute when entering or exiting:

```yaml
scenes:
  - id: "scene_1"
    text: "You enter the room."
    on_enter:
      - "entered_room: true"      # Set flag
      - "increment(visit_count)"  # Increment counter
      - "add_to_set(visited_places, room_1)"  # Add to set
    on_exit:
      - "left_room: true"
    next_chapter: "chapter_2"
```

**Supported hook formats:**
- `"flag_name: value"` — Set a flag (bool, int, or string)
- `"increment(flag_name)"` — Increment an integer counter
- `"add_to_set(set_name, item)"` — Add item to a set

### GUI Save Slot Selection

The GUI now shows a save slot selection screen on startup:

- `SaveSlotScreen` — Displays all save slots with metadata
- `GameSelectScreen` — For starting new games
- Users can select a save slot or start a new game

### Enhanced GameState

GameState now includes helper methods for advanced flag operations:

```python
state.increment_counter("visit_count")  # Increment by 1
state.increment_counter("visit_count", by=5)  # Increment by 5
state.add_to_set("evidence", "document_1")  # Add to set
state.set_contains("evidence", "document_1")  # Check membership
```

## Testing

```bash
uv run pytest tests/ -v          # all tests (290 tests)
uv run pytest tests/test_models.py -v   # model validation only
uv run pytest tests/test_narrative_graph.py -v  # narrative graph validation
uv run pytest tests/test_new_features.py -v  # new features tests
uv run pytest tests/test_gui.py -v  # GUI tests with Textual Pilot
```
