# Implementation Plan: World & Time Layer

## Phase 1: Baseline dan Model Data

- [x] Task: Konfirmasi baseline sebelum menyentuh apa pun
    - [x] Jalankan `uv run pytest tests/ -v`, catat jumlah test lulus saat ini
          (JANGAN asumsikan 268 — bisa sudah berubah)
    - [x] Baca `src/muara/models/save_state.py`, `src/muara/engine/state.py`,
          `src/muara/engine/chapter_runner.py`, `src/muara/models/chapter.py`
          penuh (bukan sekadar grep) untuk memastikan pemahaman kontrak yang ada
          cocok dengan design.md
    - [x] Jika ada divergensi antara apa yang tertulis di design.md dan kode
          aktual (misal signature method sudah berubah dari yang didokumentasikan
          di sini), HENTIKAN dan laporkan ke user sebelum melanjutkan — jangan
          menebak-nebak penyesuaian sendiri untuk perubahan struktural
- [x] Task: Buat `src/muara/models/world_clock.py`
    - [x] Implementasikan `Shift` enum persis seperti design.md
    - [x] Implementasikan `WorldClock` model persis seperti design.md
          (`advance_shift()`, `advance_day()`, immutable — return instance baru)
    - [x] Implementasikan `EventTrigger` model, import `FlagCondition` dari
          `muara.models.chapter` (JANGAN duplikasi definisi)
    - [x] Implementasikan `WorldEvent` model
    - [x] Semua model pakai `model_config = ConfigDict(extra="forbid")`, konsisten
          dengan model lain di proyek
- [x] Task: Tulis test untuk `world_clock.py` di `tests/test_world_clock.py`
    - [x] Test: shift maju pagi→siang→malam tanpa ganti hari
    - [x] Test: shift maju malam→pagi DENGAN hari bertambah 1
    - [x] Test: `advance_day()` selalu reset ke shift pagi, hari +1
    - [x] Test: `WorldClock()` default adalah `day=1, shift=pagi`
    - [x] Test: `WorldEvent`/`EventTrigger` bisa dibuat dan divalidasi Pydantic
          dengan kombinasi field opsional (day only, shift only, flags only,
          kombinasi)
- [x] Task: Conductor - User Manual Verification 'Baseline dan Model Data' (Protocol in workflow.md)

## Phase 2: Migrasi SaveState dan Perluasan GameState

- [x] Task: Modifikasi `src/muara/models/save_state.py`
    - [x] Tambahkan import `WorldClock` dari `muara.models.world_clock`
    - [x] Naikkan `version: int = 2`
    - [x] Tambahkan `world_clock: WorldClock = Field(default_factory=WorldClock)`
    - [x] JANGAN ubah field lain apa pun di model ini
- [x] Task: Tulis test migrasi save version 1→2 SEBELUM melanjutkan ke kode lain
    - [x] Di `tests/test_world_clock.py`, buat fixture: string JSON literal yang
          merepresentasikan save version-1 LENGKAP (semua field wajib terisi,
          TANPA field `world_clock` sama sekali) — tulis manual, jangan generate
          dari model versi baru
    - [x] Test: `SaveState.model_validate_json(fixture_json_v1)` berhasil TANPA
          error, dan `.world_clock` menghasilkan `WorldClock(day=1, shift=pagi)`
    - [x] Test ini WAJIB lulus sebelum lanjut ke task berikutnya — ini adalah
          jaminan bahwa save pemain yang sudah ada tidak akan rusak
- [x] Task: Perluas `src/muara/engine/state.py` (`GameState`)
    - [x] Tambahkan method `advance_clock_shift()` persis seperti design.md
    - [x] Tambahkan method `advance_clock_day()` persis seperti design.md
    - [x] Tambahkan method privat `_sync_clock_flags()` persis seperti design.md
    - [x] JANGAN ubah method yang sudah ada (`set_flag`, `get_flag`,
          `increment_counter`, `add_to_set`, `set_contains`, `evaluate_condition`,
          `advance_to`, `mark_chapter_complete`, dst.)
- [x] Task: Tulis test untuk method baru `GameState` di `tests/test_state_helpers.py`
    - [x] Test: `advance_clock_shift()` memanggil `_sync_clock_flags`, dan
          `state.get_flag("world_day")`/`get_flag("world_shift")` mencerminkan
          nilai baru
    - [x] Test: flag `world_day`/`world_shift` bisa dibaca lewat
          `evaluate_condition("world_day >= 2")` dan
          `evaluate_condition("world_shift == siang")` TANPA modifikasi apa pun
          pada `evaluate_condition()` itu sendiri (ini adalah bukti bahwa desain
          "flag turunan" bekerja seperti yang diklaim design.md)
- [x] Task: Conductor - User Manual Verification 'Migrasi SaveState dan Perluasan GameState' (Protocol in workflow.md)

## Phase 3: EventScheduler dan Loader

- [x] Task: Buat `src/muara/engine/event_scheduler.py`
    - [x] Implementasikan `EventScheduler` persis seperti design.md
          (`due_events()`, `apply_event()`, `_matches_trigger()`)
    - [x] Gunakan `FIRED_EVENTS_SET` sebagai konstanta, reuse `add_to_set`/
          `set_contains` yang SUDAH ADA di `GameState` — JANGAN membuat mekanisme
          pelacakan baru
    - [x] Reuse `FlagAssignment.from_raw_string` yang SUDAH ADA di
          `muara.models.chapter` untuk parsing `set_flags` — JANGAN
          reimplementasi parser
- [x] Task: Tulis test murni untuk `EventScheduler` di `tests/test_event_scheduler.py`
    - [x] Test: event dengan trigger `day` cocok hanya ketika `world_day` state
          sama persis
    - [x] Test: event dengan trigger `shift` cocok hanya ketika `world_shift`
          state sama persis
    - [x] Test: event dengan trigger `flags` cocok hanya ketika semua
          `FlagCondition` di dalamnya `True` (AND, bukan OR)
    - [x] Test: event non-repeatable HANYA due sekali — setelah `apply_event()`
          dipanggil, `due_events()` berikutnya TIDAK lagi mengembalikan event itu
          meski trigger masih cocok
    - [x] Test: event repeatable=True due BERULANG KALI selama trigger cocok
    - [x] Test: `apply_event()` benar-benar menerapkan `set_flags` ke state
          (verifikasi lewat `state.get_flag(...)` setelahnya)
    - [x] Test-test ini HARUS jalan tanpa membuat `ChapterRunner`,
          `Chapter`/`Scene` YAML apa pun, atau CLI I/O — murni terhadap
          `GameState` + `EventScheduler` + `WorldEvent` langsung
- [x] Task: Buat `src/muara/engine/event_loader.py`
    - [x] Implementasikan `load_events(path) -> list[WorldEvent]`, mengikuti pola
          persis `chapter_loader.load_chapter()`: baca file → `yaml.safe_load` →
          validasi Pydantic → wrap semua error jadi `EventLoadError`
    - [x] Definisikan `class EventLoadError(Exception)` di file yang sama
- [x] Task: Tulis test untuk loader di `tests/test_event_loader.py`
    - [x] Test: file valid ter-load dengan benar jadi `list[WorldEvent]`
    - [x] Test: file tidak ada → `EventLoadError` (bukan `FileNotFoundError` mentah)
    - [x] Test: YAML tidak valid → `EventLoadError` (bukan `yaml.YAMLError` mentah)
    - [x] Test: skema tidak valid (field salah, `extra="forbid"` dilanggar) →
          `EventLoadError` (bukan `ValidationError` mentah)
- [x] Task: Conductor - User Manual Verification 'EventScheduler dan Loader' (Protocol in workflow.md)

## Phase 4: Integrasi ChapterRunner dan Hook DSL

- [x] Task: Perluas hook DSL di `src/muara/engine/chapter_runner.py`
    - [x] Tambahkan cabang `elif hook.startswith("advance_clock(")` di
          `_execute_hooks()` persis seperti design.md
    - [x] Pastikan argumen tidak dikenal (bukan `shift`/`day`) me-raise
          `ChapterRunError` dengan pesan jelas, konsisten dengan gaya error
          message lain di file ini (menyebutkan scene id/chapter id jika
          konteksnya tersedia)
- [x] Task: Tambahkan parameter `scheduler` ke `ChapterRunner.__init__`
    - [x] Tambahkan parameter baru dengan default `None` di POSISI TERAKHIR
          (setelah `total_chapters`) — JANGAN mengubah urutan/nama parameter yang
          sudah ada, supaya semua pemanggilan `ChapterRunner(...)` lama (termasuk
          di test) tetap valid tanpa modifikasi
    - [x] Simpan sebagai `self._scheduler`
- [x] Task: Tambahkan `_check_and_apply_due_events()` dan panggil dari akhir
      `_execute_hooks()`
    - [x] Implementasi persis seperti design.md — no-op jika
          `self._scheduler is None`
- [x] Task: Tulis test integrasi di `tests/test_engine.py`
    - [x] Test: `ChapterRunner` dengan `scheduler=None` (default) berperilaku
          IDENTIK dengan sebelum track ini — jalankan ulang salah satu playthrough
          test yang sudah ada TANPA argumen scheduler, pastikan lulus tanpa
          modifikasi assertion
    - [x] Test: `ChapterRunner` dengan scheduler terisi, chapter yang scene-nya
          memicu `advance_clock(shift)` di `on_exit`, dan sebuah `WorldEvent`
          yang trigger-nya cocok dengan shift baru — verifikasi event benar-benar
          diterapkan (flag dari `set_flags` event tersebut muncul di state
          setelah scene itu dilalui)
    - [x] Test: chapter TANPA hook `advance_clock` sama sekali, dengan scheduler
          terisi tapi tidak ada event yang trigger-nya cocok — pastikan tidak ada
          efek samping, semua flag tetap seperti semula
- [x] Task: Jalankan test suite penuh
    - [x] `uv run pytest tests/ -v`
    - [x] SEMUA test harus lulus, termasuk seluruh test yang sudah ada sebelum
          track ini dimulai (jumlah dari baseline Phase 1)
- [x] Task: Conductor - User Manual Verification 'Integrasi ChapterRunner dan Hook DSL' (Protocol in workflow.md)

## Phase 5: Integrasi GUI (atau Dokumentasi Limitation)

- [x] Task: Investigasi `src/muara/gui/app.py`
    - [x] Baca `GameScreen` penuh, cari implementasi paralel dari parsing
          `on_enter`/`on_exit` (jika ada)
    - [x] Tentukan: apakah GUI mereplikasi hook DSL sama sekali?
- [x] Task: JIKA GUI mereplikasi hook DSL
    - [x] Tambahkan titik integrasi scheduler yang setara, mengikuti pola yang
          sama (scheduler opsional, default tidak mengubah perilaku existing)
    - [x] Tulis test GUI setara di `tests/test_gui.py` menggunakan Textual Pilot
          (ikuti pola test GUI yang sudah ada di file itu)
- [x] Task: JIKA GUI TIDAK mereplikasi hook DSL, atau integrasi ternyata butuh
      restrukturisasi GUI yang signifikan
    - [x] JANGAN memaksakan perubahan arsitektur GUI
    - [x] Tulis catatan eksplisit di `AGENTS.md` bagian yang relevan: "World &
          Time Layer (event scheduler + advance_clock hook) saat ini hanya aktif
          di mode CLI. GUI belum terintegrasi — lihat Track 1 spec/design untuk
          detail keputusan ini."
    - [x] Laporkan temuan ini secara eksplisit sebagai bagian dari ringkasan
          pekerjaan ke user, BUKAN sebagai catatan tersembunyi di commit message
          saja
- [x] Task: Conductor - User Manual Verification 'Integrasi GUI (atau Dokumentasi Limitation)' (Protocol in workflow.md)

## Phase 6: Konten Contoh dan Dokumentasi

- [x] Task: Buat `content/events.yaml` dengan event contoh
    - [x] Minimal satu event, mengikuti skema di design.md
    - [x] Event ini HANYA untuk membuktikan skema berfungsi ujung-ke-ujung —
          BUKAN konten naratif final (tidak perlu prose Batavia 1899 yang
          matang, cukup penanda fungsional)
    - [x] Verifikasi manual: `load_events("content/events.yaml")` berhasil
          tanpa error
- [x] Task: Update `AGENTS.md`
    - [x] Tambahkan section baru yang mendokumentasikan: `WorldClock`, hook
          `advance_clock(shift|day)`, `content/events.yaml`, dan CATATAN PENTING
          bahwa `world_day`/`world_shift` adalah flag TURUNAN — jangan pernah
          di-set manual lewat `set_flags` di choice, karena akan tertimpa balik
          saat clock maju lagi
    - [x] Sertakan contoh YAML pemakaian `advance_clock(shift)` di `on_exit`,
          persis seperti contoh di design.md
    - [x] Update jumlah test di section "Testing" (`uv run pytest tests/ -v`)
          ke angka baru yang benar setelah track ini
- [x] Task: Update `README.md`
    - [x] Tambahkan satu baris di bagian "Features" yang menyebut world clock/
          event scheduler sebagai kapabilitas engine baru (SATU baris, bukan
          section besar — README ini untuk pemain/kontributor baru, bukan
          dokumentasi teknis mendalam)
- [x] Task: Jalankan test suite penuh sekali lagi sebagai gerbang akhir
    - [x] `uv run pytest tests/ -v`
    - [x] Bandingkan jumlah test lulus dengan baseline Phase 1 — harus lebih
          besar (test baru ditambahkan) dan TIDAK ADA yang gagal
- [x] Task: Conductor - User Manual Verification 'Konten Contoh dan Dokumentasi' (Protocol in workflow.md)

## Definition of Done

Track ini selesai HANYA jika SEMUA berikut benar:
1. Semua acceptance criteria di `spec.md` terpenuhi
2. Save file version-1 asli (fixture nyata) berhasil di-load tanpa error
3. `uv run pytest tests/ -v` — 100% lulus, termasuk seluruh test lama
4. Tidak ada perubahan pada signature publik yang memutus test lama tanpa
   modifikasi test tersebut
5. Status integrasi GUI (selesai ATAU didokumentasikan sebagai limitation)
   sudah eksplisit, tidak ambigu
6. `AGENTS.md` dan `README.md` sudah diperbarui mencerminkan kapabilitas baru
