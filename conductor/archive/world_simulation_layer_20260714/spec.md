# Specification: World & Time Layer

## Overview

Track ini mengimplementasikan padanan teknis dari **Level 2 — World Simulation
Layer** pada roadmap ChatGPT (lihat `conductor/roadmap_complexity_evolution.md`
untuk peta lengkap 15 level). Tujuannya: memberi Muara representasi waktu dunia
(`GameClock`) dan mekanisme event terjadwal (`EventScheduler`) yang berjalan DI
ATAS engine naratif yang sudah ada — bukan menggantikannya.

## Background

Engine saat ini (`ChapterRunner`, `GameState`) memindahkan pemain antar scene murni
berdasarkan pilihan pemain atau urutan linear. Tidak ada konsep "jam berapa
sekarang" atau "hari ke berapa" di luar field display `date`/`time` per-chapter
(yang murni teks statis, tidak dievaluasi mesin).

ChatGPT mengusulkan tiga komponen (Game Clock, NPC Scheduler, Dynamic Event) dengan
tiga file (`time_engine.py`, `event_scheduler.py`, `world_state.py`). Setelah audit
codebase, keputusan berikut diambil untuk kompatibilitas dengan struktur yang ada:

- **NPC Scheduler** (bagian dari Level 3 ChatGPT, Character AI) DIKELUARKAN dari
  track ini. NPC scheduler butuh skema Identity/Personality/Trust NPC yang belum
  ada — itu didesain di Track 2. Track ini hanya menyediakan clock yang akan
  dikonsumsi Track 2, bukan konsumen NPC itu sendiri.
- **`world_state.py` yang diusulkan ChatGPT DIHAPUS sebagai file terpisah.**
  `GameState` (di `engine/state.py`) SUDAH menjadi world state holder — ia
  membungkus `SaveState` dan menjadi satu-satunya sumber kebenaran untuk flags,
  chapter/scene position. Membuat `world_state.py` terpisah akan menciptakan DUA
  sumber kebenaran yang bisa divergen. `GameClock` menjadi properti baru di dalam
  `GameState`/`SaveState`, bukan modul paralel.
- **Dynamic Event (Inspeksi, Hujan, Gudang Terbakar, Demo Buruh) DIPERSEMPIT** untuk
  track ini menjadi mekanisme scheduling generik (`EventScheduler` + `WorldEvent`
  model) TANPA menulis event konten spesifik itu sendiri. Menulis event "Gudang
  Terbakar" adalah pekerjaan **konten naratif** (YAML + prose, mengikuti World
  Bible §6), bukan pekerjaan **engine**. Track ini membangun mesinnya; menulis
  event aktual adalah task terpisah (lihat Out of Scope) yang bisa dikerjakan
  kapan saja setelah engine ini siap, oleh siapa pun yang menulis chapter YAML —
  tidak harus Big Pickle sendiri.

## Functional Requirements

### 1. GameClock (waktu dunia)

Representasi waktu bertingkat: `day` (int, mulai dari 1) → `shift` (enum:
`pagi`/`siang`/`malam`, TIGA shift per hari, BUKAN 24 jam — karena chapter yang ada
sudah pakai format jam manusiawi seperti "05.30", "08.00", cocokkan dengan realita
kerja buruh pelabuhan kolonial, bukan jam presisi menit). Field `date`/`time` yang
sudah ada di `Chapter` (string statis untuk display) TIDAK diubah — `GameClock`
berjalan paralel sebagai state yang bisa dievaluasi mesin, sedangkan `date`/`time`
tetap murni untuk tampilan prosa seperti sekarang.

- Clock disimpan sebagai bagian dari `SaveState` (field baru), bukan komputasi
  ulang dari `chapters_completed`.
- Clock HANYA maju melalui hook eksplisit di YAML (`advance_clock(...)`), TIDAK
  otomatis maju per scene atau per chapter. Ini konsisten dengan filosofi hook DSL
  yang sudah ada (`on_enter`/`on_exit` adalah opt-in eksplisit per scene, bukan
  side-effect implisit dari engine).
- Clock harus bisa dibaca sebagai kondisi di `text_variants` dan `requires` —
  artinya representasi clock harus bisa diproyeksikan ke flag yang kompatibel
  dengan `FlagCondition`/`evaluate_condition()` yang sudah ada, BUKAN tipe data
  baru yang butuh parser kondisi terpisah.

### 2. EventScheduler (jadwal event dunia)

- `WorldEvent` adalah model data (bukan logic) yang mendeskripsikan: id, trigger
  condition (kombinasi day/shift ATAU kombinasi flag), dan efek (set flags — pakai
  ulang `FlagAssignment.from_raw_string` yang sudah ada, JANGAN reimplementasi
  parser assignment).
- `EventScheduler` adalah komponen yang, diberi `GameState` saat ini, mengembalikan
  daftar event yang "due" (harus terjadi) berdasarkan clock/flag saat ini.
- Scheduler TIDAK mengeksekusi rendering atau prose — ia hanya menentukan APAKAH
  suatu event due dan APA efek flag-nya. Prose/scene aktual untuk merespons event
  itu tetap tanggung jawab penulis chapter YAML (lewat `requires`/`text_variants`
  yang sudah ada, mengecek flag yang di-set event).
- Event terdaftar lewat YAML terpisah (`content/events.yaml`), BUKAN hardcoded di
  Python — konsisten dengan filosofi "YAML sebagai sumber kanonik" yang sudah
  berlaku untuk chapter.

### 3. Integrasi dengan ChapterRunner

- `ChapterRunner` mendapat satu titik integrasi baru: setelah `_execute_hooks`
  dipanggil (baik `on_enter` maupun `on_exit`), scheduler dicek. Jika ada event
  due, efek flag-nya diterapkan SEBELUM scene berikutnya di-resolve. Ini artinya
  urutan hook DSL yang ada (`"flag: value"`, `increment(...)`, `add_to_set(...)`)
  harus diperluas dengan SATU hook baru: `advance_clock(shift)` atau
  `advance_clock(day)` — mengikuti pola parsing yang sama persis dengan hook yang
  sudah ada (`hook.startswith("advance_clock(")`).
- TIDAK ada perubahan pada signature publik `ChapterRunner.run()` atau
  `ChapterRunner.__init__()`.

### 4. Migrasi SaveState

- `SaveState.version` naik dari `1` ke `2`.
- Field baru: `world_clock: WorldClock` (model baru, lihat design.md), dengan
  default factory sehingga save lama (version 1, tanpa field ini) TETAP BISA
  di-load — Pydantic default factory menghasilkan `WorldClock` state awal
  (`day=1, shift="pagi"`) untuk save lama yang belum punya field ini.
- TIDAK ADA migrasi data yang menghapus atau mengubah field lain di `SaveState`.

## Non-Functional Requirements

### 1. Quality Gates
- Seluruh test yang ada saat ini (jumlah tepatnya harus dicek Big Pickle sendiri
  di awal task lewat `uv run pytest tests/ -v`, karena bisa sudah berbeda dari 268
  jika ada track lain yang berjalan lebih dulu) harus tetap lulus.
- Save file versi 1 (dibuat sebelum track ini) HARUS tetap bisa di-load tanpa
  error. Ini WAJIB diuji dengan fixture save file version-1 eksplisit, bukan
  diasumsikan dari default factory Pydantic saja.
- Tidak ada perubahan pada `Renderer` protocol.

### 2. Compatibility
- `GameClock`/`WorldClock` harus bisa dibaca lewat kondisi string yang sudah
  didukung `evaluate_condition()` (format `"key == value"`, `"key >= value"`,
  dsb) TANPA mengubah `evaluate_condition()` untuk menerima sintaks baru. Artinya
  clock harus diekspos sebagai flag biasa (misal `world_day` sebagai int flag,
  `world_shift` sebagai string flag) yang disinkronkan otomatis oleh
  `GameClock`, BUKAN sebagai objek terpisah yang butuh sintaks kondisi baru.

### 3. GUI Compatibility
- `AGENTS.md` mencatat bahwa GUI (`gui/app.py`) TIDAK memakai `ChapterRunner` —
  ia adalah state machine async terpisah yang mereplikasi sebagian logic
  `ChapterRunner` secara manual. Titik integrasi scheduler HARUS ditambahkan di
  KEDUA tempat (`ChapterRunner._execute_hooks` dan titik setara di `GameScreen`
  GUI), atau CLI dan GUI akan divergen secara perilaku. Ini adalah risiko
  terbesar track ini — lihat Risks.

## Acceptance Criteria

### Model & Engine Criteria
- [x] `WorldClock` Pydantic model dibuat (day: int, shift: Literal["pagi","siang","malam"])
- [x] `SaveState.version` = 2, field `world_clock: WorldClock` ditambahkan dengan default factory
- [x] `GameState` punya method baru: `advance_clock_shift()`, `advance_clock_day()`,
      keduanya mensinkronkan flag proyeksi (`world_day`, `world_shift`) otomatis
- [x] Hook DSL baru `advance_clock(shift)` dan `advance_clock(day)` berfungsi di
      `on_enter`/`on_exit`, mengikuti pola parsing hook yang sudah ada
- [x] `WorldEvent` Pydantic model dibuat, memuat trigger condition + `set_flags`
      (reuse `FlagAssignment.from_raw_string`)
- [x] `EventScheduler` class dibuat: method `due_events(state: GameState) -> list[WorldEvent]`
- [x] `content/events.yaml` skema dan loader dibuat (`load_events()` di
      `chapter_loader.py` atau file baru `event_loader.py`, mengikuti pola
      error-wrapping yang sama — custom exception, bukan exception library mentah)
- [x] Integrasi di `ChapterRunner`: event due diterapkan efeknya setelah hooks
      scene dieksekusi
- [x] Integrasi setara ditambahkan di GUI (`gui/app.py`) — LIHAT Risks untuk
      keputusan yang harus diambil user sebelum ini dikerjakan

### Test Criteria
- [x] Test baru: `WorldClock` maju dengan benar (pagi→siang→malam→hari
      berikutnya→pagi)
- [x] Test baru: flag proyeksi (`world_day`, `world_shift`) tersinkron setelah
      clock maju
- [x] Test baru: save file version-1 (fixture eksplisit, HARUS ditulis manual
      sebagai JSON tanpa field `world_clock`) berhasil di-load, `world_clock`
      terisi default
- [x] Test baru: `EventScheduler.due_events()` mengembalikan event yang tepat
      untuk kombinasi day/shift/flag tertentu, dan TIDAK mengembalikan event yang
      belum due
- [x] Test baru: event yang sudah pernah due tidak due lagi berulang-ulang tanpa
      sengaja (event one-shot vs repeatable — HARUS didesain eksplisit, lihat
      design.md)
- [x] Semua test lama tetap lulus

### Content Criteria
- [x] `content/events.yaml` dibuat dengan MINIMAL SATU event contoh (boleh
      sederhana, misal event penanda hari berganti) untuk membuktikan skema
      berfungsi ujung-ke-ujung — BUKAN tugas track ini untuk menulis event
      "Inspeksi/Hujan/Gudang Terbakar/Demo Buruh" secara naratif lengkap

## Out of Scope

- Menulis prose/scene YAML untuk event spesifik yang disebut ChatGPT (Inspeksi,
  Hujan, Gudang Terbakar, Demo Buruh) — ini pekerjaan konten naratif, dijadwalkan
  terpisah setelah engine ini lulus verifikasi
- NPC Scheduler (Level 3 ChatGPT) — lihat Track 2
- Perubahan pada `determine_ending()` — clock tidak boleh mengubah logic ending
  yang sudah ada di track ini
- Perubahan pada 16 chapter YAML yang sudah ada
- UI/display baru untuk menampilkan clock ke pemain (misal indikator "Hari 3,
  Sore" di renderer) — ini keputusan UX terpisah, di luar cakupan spec teknis ini

## Dependencies

- `models/save_state.py` (SaveState, akan dimodifikasi)
- `models/chapter.py` (FlagAssignment.from_raw_string, akan di-reuse)
- `engine/state.py` (GameState, akan diperluas)
- `engine/chapter_runner.py` (ChapterRunner, titik integrasi baru)
- `engine/chapter_loader.py` (pola error-wrapping untuk loader baru)
- `gui/app.py` (titik integrasi setara — lihat Risks)

## Risks

1. **Divergensi CLI/GUI** — karena GUI tidak memakai `ChapterRunner`, ada risiko
   nyata scheduler hanya terintegrasi di CLI dan GUI diam-diam berjalan tanpa
   event. Mitigasi: task eksplisit di plan.md mewajibkan integrasi ganda DAN
   memberi Big Pickle jalan keluar (dokumentasikan sebagai known limitation dan
   laporkan ke user) jika integrasi GUI ternyata butuh refactor GUI yang lebih
   besar dari perkiraan — JANGAN dipaksakan sampai merusak arsitektur GUI yang ada.
2. **Event repeatable vs one-shot ambigu** — jika tidak didesain eksplisit,
   event yang sama bisa terus-menerus "due" setiap kali kondisinya cocok
   (misal event yang trigger di "shift == malam" akan due tiap malam selamanya).
   Mitigasi: `WorldEvent` punya field eksplisit `repeatable: bool` dan
   `EventScheduler` melacak event id yang sudah pernah due lewat
   `flag_sets` yang SUDAH ADA (`add_to_set`/`set_contains`) — bukan mekanisme
   pelacakan baru.
3. **Migrasi save yang diam-diam merusak save lama** — mitigasi: acceptance
   criteria eksplisit mewajibkan fixture save version-1 nyata (bukan
   hipotetis) diuji sebelum track dianggap selesai.
