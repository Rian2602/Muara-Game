# Design: NPC Trait & Trust Model

## File & Komponen Baru

1. `src/muara/models/npc.py`
2. `src/muara/engine/npc_loader.py`
3. `content/npcs.yaml`
4. Modifikasi `SaveState` v2 -> v3
5. Ekstensi DSL Hook di `_execute_hooks`

## Model Desain

### NPCEntity
```python
class NPCSchedule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shift: Shift
    location: str

class NPCEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    traits: list[str] = Field(default_factory=list)
    default_location: str
    schedules: list[NPCSchedule] = Field(default_factory=list)
```

### Sinkronisasi Lokasi
Karena model naratif tidak memiliki sistem spatial yang konkret (hanya sebatas teks "location" di bab), lokasi direpresentasikan dengan sebuah string ID lokasi (misal: `"gudang_utama"`, `"pelabuhan"`, `"kantor_mandor"`).
Di dalam `GameState._sync_clock_flags()`, pembaruan lokasi seluruh NPC terjadi otomatis berdasarkan jam saat ini:
```python
def _sync_npc_locations(self, npcs: list[NPCEntity]) -> None:
    current_shift = self._save_state.world_clock.shift
    for npc in npcs:
        loc = npc.default_location
        for sch in npc.schedules:
            if sch.shift == current_shift:
                loc = sch.location
                break
        self.set_flag(f"npc_{npc.id}_location", loc)
```

### Ekstensi DSL Hook
Dukungan string DSL baru pada `ChapterRunner._execute_hooks` (dan `GameScreen` GUI):
`"change_rep(sutisna, trust, 1)"`
Yang dipilah (parse) lalu dieksekusi dengan metode `GameState.change_reputation("sutisna", "trust", 1)`.

## Penanganan Reputasi dan Backward Compatibility
Migrasi `SaveState` ke versi 3 akan memperkenalkan `reputations: dict[str, dict[str, int]] = Field(default_factory=dict)`. Sama dengan teknik di Track 1, kita akan mengandalkan inisialisasi fallback Pydantic untuk mendukung berkas save v1 maupun v2 dengan aman tanpa memecahkan status pemain lama.