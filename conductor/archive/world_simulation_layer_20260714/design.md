# World & Time Layer Design

## Problem Analysis

Engine saat ini tidak punya konsep waktu yang bisa dievaluasi mesin:
1. `Chapter.date`/`Chapter.time` murni string display, tidak pernah dibaca logic
2. Tidak ada cara bagi penulis chapter untuk berkata "scene ini hanya masuk akal
   kalau sudah hari ke-3" tanpa memakai flag manual (`chapter_5_choice` dsb, yang
   semuanya berbasis choice pemain, bukan waktu berjalan)
3. Tidak ada mekanisme "sesuatu terjadi terlepas dari pilihan pemain" — semua
   state saat ini adalah hasil langsung dari `set_flags` di choice

## Proposed Solution

### File Baru

```
src/muara/models/world_clock.py    # WorldClock, WorldEvent Pydantic models
src/muara/engine/event_scheduler.py # EventScheduler class
src/muara/engine/event_loader.py    # load_events(), EventLoadError
content/events.yaml                 # data event (kanonik, seperti chapter YAML)
tests/test_world_clock.py           # test WorldClock + integrasi SaveState
tests/test_event_scheduler.py       # test EventScheduler murni (tanpa I/O)
tests/test_event_loader.py          # test load_events() dari YAML
```

### File yang Dimodifikasi

```
src/muara/models/save_state.py     # +field world_clock, version 1→2
src/muara/engine/state.py          # +GameState.advance_clock_shift/day, +due_events sync
src/muara/engine/chapter_runner.py # +panggilan scheduler setelah _execute_hooks
src/muara/gui/app.py               # +panggilan scheduler setara (lihat bagian GUI)
tests/test_state_helpers.py        # +test clock methods di GameState
tests/test_engine.py               # +test integrasi scheduler di ChapterRunner
```

### `WorldClock` — models/world_clock.py

```python
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class Shift(str, Enum):
    PAGI = "pagi"
    SIANG = "siang"
    MALAM = "malam"

    def next(self) -> tuple["Shift", bool]:
        """Kembalikan shift berikutnya dan apakah hari berganti.
        
        Returns:
            (shift_berikutnya, hari_berganti: bool)
        """
        order = [Shift.PAGI, Shift.SIANG, Shift.MALAM]
        current_index = order.index(self)
        if current_index == len(order) - 1:
            return Shift.PAGI, True
        return order[current_index + 1], False


class WorldClock(BaseModel):
    """Representasi waktu dunia yang bisa dievaluasi mesin.
    
    TIDAK menggantikan Chapter.date/Chapter.time (yang tetap string display untuk
    prosa). Ini adalah lapisan terpisah yang disinkronkan ke flags proyeksi
    (world_day, world_shift) agar bisa dibaca lewat evaluate_condition() yang
    sudah ada tanpa mengubah parsernya.
    """
    model_config = ConfigDict(extra="forbid")

    day: int = 1
    shift: Shift = Shift.PAGI

    def advance_shift(self) -> "WorldClock":
        """Kembalikan WorldClock baru setelah maju satu shift."""
        next_shift, day_changed = self.shift.next()
        return WorldClock(
            day=self.day + 1 if day_changed else self.day,
            shift=next_shift,
        )

    def advance_day(self) -> "WorldClock":
        """Kembalikan WorldClock baru setelah maju satu hari penuh (shift kembali ke pagi)."""
        return WorldClock(day=self.day + 1, shift=Shift.PAGI)
```

**Keputusan desain kunci:** `WorldClock` immutable secara method (mengembalikan
instance baru, bukan mutasi in-place) — konsisten dengan gaya `FlagCondition.evaluate()`
yang sudah ada (pure function, tidak mutasi). `GameState` yang memegang tanggung
jawab mutasi state aktual, sama seperti pola `set_flag`/`increment_counter` yang
sudah ada.

### `WorldEvent` — models/world_clock.py (lanjutan file yang sama)

```python
class EventTrigger(BaseModel):
    """Syarat sebuah WorldEvent dianggap 'due'.
    
    Semua field yang diisi (bukan None) harus cocok — AND, bukan OR. Untuk logika
    OR, definisikan event terpisah.
    """
    model_config = ConfigDict(extra="forbid")

    day: int | None = None
    shift: Shift | None = None
    flags: list["FlagCondition"] | None = None  # reuse FlagCondition dari models/chapter.py


class WorldEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    trigger: EventTrigger
    set_flags: list[str] = []  # format sama persis dengan Scene.on_enter: "key: value"
    repeatable: bool = False
```

**Catatan implementasi:** `EventTrigger.flags` mereferensikan `FlagCondition` yang
sudah didefinisikan di `models/chapter.py`. Import lintas modul, JANGAN duplikasi
definisi `FlagCondition`. `WorldEvent.set_flags` memakai format string yang IDENTIK
dengan `Scene.on_enter`/`on_exit` (`"key: value"`) sehingga
`FlagAssignment.from_raw_string` yang sudah ada bisa dipakai ulang tanpa modifikasi.

### `EventScheduler` — engine/event_scheduler.py

```python
from __future__ import annotations

from muara.engine.state import GameState
from muara.models.chapter import FlagAssignment
from muara.models.world_clock import WorldEvent

FIRED_EVENTS_SET = "_fired_world_events"  # nama set internal di flag_sets


class EventScheduler:
    def __init__(self, events: list[WorldEvent]) -> None:
        self._events = events

    def due_events(self, state: GameState) -> list[WorldEvent]:
        """Kembalikan semua event yang due dan BELUM diterapkan (untuk non-repeatable).
        
        TIDAK menerapkan efeknya — hanya menentukan mana yang due. Pemanggilan
        apply_event() adalah langkah terpisah, disengaja, agar due_events() tetap
        pure function yang mudah diuji tanpa mutasi state.
        """
        due = []
        for event in self._events:
            if not self._matches_trigger(event, state):
                continue
            if not event.repeatable and state.set_contains(FIRED_EVENTS_SET, event.id):
                continue
            due.append(event)
        return due

    def apply_event(self, event: WorldEvent, state: GameState) -> None:
        """Terapkan efek flag sebuah event dan catat sebagai 'sudah fired'."""
        for raw in event.set_flags:
            assignment = FlagAssignment.from_raw_string(raw)
            state.set_flag(assignment.key, assignment.value)
        if not event.repeatable:
            state.add_to_set(FIRED_EVENTS_SET, event.id)

    def _matches_trigger(self, event: WorldEvent, state: GameState) -> bool:
        trigger = event.trigger
        if trigger.day is not None and state.get_flag("world_day") != trigger.day:
            return False
        if trigger.shift is not None and state.get_flag("world_shift") != trigger.shift.value:
            return False
        if trigger.flags:
            flags = state.save_state.flags
            if not all(cond.evaluate(flags) for cond in trigger.flags):
                return False
        return True
```

**Keputusan desain kunci:** `FIRED_EVENTS_SET` memakai `flag_sets` yang SUDAH ADA
di `SaveState` (lewat `add_to_set`/`set_contains`), BUKAN field baru. Ini
menghindari migrasi skema tambahan — `flag_sets: dict[str, list[str]]` sudah
ada sejak `SaveState` versi 1 dan otomatis persisten lewat save/load yang ada.
Prefix underscore (`_fired_world_events`) menandai ini sebagai bookkeeping
internal, bukan flag yang dimaksudkan untuk dibaca penulis chapter YAML — tapi
secara teknis tetap bisa dibaca kalau penulis YAML sungguh-sungguh membutuhkannya
(tidak ada mekanisme "private" sungguhan di `flag_sets`, dan itu tidak masalah).

### Perluasan `GameState` — engine/state.py

Method baru yang ditambahkan ke `GameState` (JANGAN membuat class baru — ini adalah
extension dari class yang sudah ada, konsisten dengan bagaimana
`increment_counter`/`add_to_set` ditambahkan sebelumnya di riwayat proyek):

```python
def advance_clock_shift(self) -> None:
    """Majukan world_clock satu shift, sinkronkan flag proyeksi."""
    new_clock = self._save_state.world_clock.advance_shift()
    self._save_state.world_clock = new_clock
    self._sync_clock_flags()

def advance_clock_day(self) -> None:
    """Majukan world_clock satu hari penuh, sinkronkan flag proyeksi."""
    new_clock = self._save_state.world_clock.advance_day()
    self._save_state.world_clock = new_clock
    self._sync_clock_flags()

def _sync_clock_flags(self) -> None:
    """Proyeksikan world_clock ke flags biasa agar bisa dibaca evaluate_condition().
    
    Dipanggil setiap kali clock berubah. Flag ini adalah TURUNAN, jangan pernah
    di-set manual lewat set_flag() — akan langsung tertimpa saat clock maju lagi.
    """
    self.set_flag("world_day", self._save_state.world_clock.day)
    self.set_flag("world_shift", self._save_state.world_clock.shift.value)
```

**Keputusan desain kunci:** `world_day`/`world_shift` adalah flag TURUNAN
(derived), bukan sumber kebenaran. Sumber kebenaran adalah
`SaveState.world_clock`. Ini penting supaya tidak ada dua tempat yang bisa
divergen — kalau penulis chapter YAML iseng meng-set `world_day: 99` lewat
`on_enter`, itu HANYA mengubah proyeksi flag, TIDAK mengubah `world_clock` yang
sebenarnya, dan proyeksi itu akan langsung tertimpa balik saat clock maju lagi
via `advance_clock(...)`. Ini harus didokumentasikan dengan jelas di AGENTS.md
(lihat plan.md task dokumentasi) supaya tidak membingungkan penulis chapter di
masa depan.

### Hook DSL baru — engine/chapter_runner.py, method `_execute_hooks`

Tambahan ke method yang SUDAH ADA (bukan method baru), mengikuti pola
`if/elif` yang sudah dipakai persis untuk `increment(...)` dan `add_to_set(...)`:

```python
elif hook.startswith("advance_clock("):
    arg = hook[14:-1].strip()
    if arg == "shift":
        self.state.advance_clock_shift()
    elif arg == "day":
        self.state.advance_clock_day()
    else:
        raise ChapterRunError(
            f"advance_clock() argumen tidak dikenal: {arg!r} — "
            "gunakan 'shift' atau 'day'"
        )
```

Contoh pemakaian di YAML (untuk task dokumentasi/contoh di AGENTS.md, BUKAN
konten chapter aktual yang akan ditulis di track ini):

```yaml
scenes:
  - id: "scene_5"
    text: "Malam turun. Aku menutup buku kecilku."
    on_exit:
      - "advance_clock(shift)"
    next_chapter: "next_chapter_id"
```

### Integrasi scheduler di `ChapterRunner.run()`

Titik integrasi TEPAT SETELAH `self._execute_hooks(...)` dipanggil (baik untuk
`on_enter` maupun `on_exit`) — karena hook adalah tempat clock/flag berubah, dan
event harus dicek SEGERA setelah perubahan itu, sebelum scene berikutnya
di-resolve:

```python
def _execute_hooks(self, hooks: list[str]) -> None:
    # ... (kode existing tidak berubah) ...
    self._check_and_apply_due_events()

def _check_and_apply_due_events(self) -> None:
    if self._scheduler is None:
        return
    for event in self._scheduler.due_events(self.state):
        self._scheduler.apply_event(event, self.state)
```

`ChapterRunner.__init__` mendapat SATU parameter baru dengan default `None`
(BUKAN mengubah urutan parameter yang sudah ada, untuk menjaga backward
compatibility signature):

```python
def __init__(
    self,
    chapter: Chapter,
    state: GameState,
    renderer: Renderer,
    input_fn: Callable[[str], str] = input,
    chapter_index: int = 0,
    total_chapters: int = 0,
    scheduler: "EventScheduler | None" = None,  # BARU
) -> None:
    # ...
    self._scheduler = scheduler
```

Dengan default `None`, semua test lama yang membuat `ChapterRunner(...)` tanpa
argumen scheduler TETAP BERFUNGSI tanpa modifikasi — `_check_and_apply_due_events`
no-op ketika `scheduler is None`.

### Integrasi GUI — gui/app.py

**Ini bagian paling berisiko di track ini.** `AGENTS.md` menyatakan GUI TIDAK
memakai `ChapterRunner` — ia adalah state machine async terpisah di `GameScreen`.
Big Pickle HARUS:

1. Baca `gui/app.py` untuk menemukan titik yang setara secara fungsional dengan
   `_execute_hooks` di `ChapterRunner` (kemungkinan besar tempat GUI memproses
   `on_enter`/`on_exit` scene secara manual — cari implementasi paralel dari
   parsing hook string yang sama)
2. Tambahkan pemanggilan scheduler yang SETARA di titik itu
3. **Jika ternyata GUI tidak mereplikasi parsing hook `on_enter`/`on_exit` sama
   sekali** (mungkin GUI belum mendukung hook, hanya CLI yang mendukung) — JANGAN
   memaksakan penambahan scheduler ke GUI dengan menulis ulang arsitektur GUI.
   Sebagai gantinya: dokumentasikan sebagai **known limitation** di
   `AGENTS.md`/laporan task ("World & Time Layer saat ini hanya aktif di mode CLI;
   GUI belum mereplikasi hook DSL sama sekali sehingga event dunia tidak berjalan
   di GUI"), dan laporkan eksplisit ke user untuk keputusan: apakah GUI hook
   parity adalah track terpisah, atau memang belum prioritas.

### Migrasi `SaveState` — models/save_state.py

```python
from muara.models.world_clock import WorldClock

class SaveState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = 2  # naik dari 1
    save_id: str
    player_name: str | None = None
    current_chapter: str
    current_scene: str
    completed: bool = False
    flags: dict[str, bool | str | int] = Field(default_factory=dict)
    flag_sets: dict[str, list[str]] = Field(default_factory=dict)
    chapters_completed: list[str] = Field(default_factory=list)
    endings_achieved: list[str] = Field(default_factory=list)
    last_saved: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    playthrough_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    world_clock: WorldClock = Field(default_factory=WorldClock)  # BARU
```

**Kenapa ini aman untuk save lama:** Pydantic `model_validate_json()` (dipakai di
`save_manager.load()`) akan mengisi `world_clock` dengan `default_factory` kalau
field itu tidak ada di JSON lama — TIDAK akan raise `ValidationError`. `version`
field yang sudah ada di model TIDAK divalidasi secara khusus di kode saat ini
(hanya field biasa) — artinya save lama dengan `"version": 1` akan ter-load
dengan `version=1` apa adanya (bukan otomatis jadi 2). Ini SENGAJA dibiarkan
sebagai catatan historis, bukan bug — kalau butuh migrasi version yang
menandai save sebagai "sudah lihat clock", itu keputusan produk terpisah di
luar cakupan track ini (lihat Out of Scope di spec.md).

### `content/events.yaml` — skema contoh

```yaml
events:
  - id: "hari_kedua_dimulai"
    trigger:
      day: 2
      shift: "pagi"
    set_flags:
      - "memasuki_hari_kedua: true"
    repeatable: false
```

Loader (`event_loader.py`) mengikuti pola `chapter_loader.py` PERSIS: baca file,
`yaml.safe_load`, validasi Pydantic, wrap error jadi custom exception
(`EventLoadError`), JANGAN biarkan `yaml.YAMLError`/`ValidationError` mentah bocor
ke caller.

## Success Metrics

- [ ] `WorldClock` + `WorldEvent` model selesai, test lulus
- [ ] `EventScheduler` selesai dan diuji SEPENUHNYA sebagai pure logic (tanpa
      bergantung pada `ChapterRunner`/CLI I/O)
- [ ] Integrasi `ChapterRunner` selesai, TIDAK mengubah signature publik yang
      sudah dipakai test lama
- [ ] Integrasi GUI selesai ATAU didokumentasikan eksplisit sebagai known
      limitation dengan laporan ke user
- [ ] Migrasi save version 1→2 terbukti aman lewat fixture nyata, bukan asumsi
- [ ] Minimal satu event contoh di `content/events.yaml` berfungsi ujung-ke-ujung
