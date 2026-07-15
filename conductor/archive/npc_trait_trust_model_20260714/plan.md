# Implementation Plan: NPC Trait & Trust Model

## Phase 1: Baseline & Skema Pydantic
- [x] Konfirmasi jumlah test *passing* saat ini (`uv run pytest tests/ -v`).
- [x] Buat file `src/muara/models/npc.py` untuk struktur `NPCEntity` dan `NPCSchedule` sesuai dengan `design.md`.
- [x] Tulis test murni untuk validasi `NPCEntity` di `tests/test_npc_models.py`.
- [x] Conductor - User Manual Verification (Fase 1)

## Phase 2: NPC Loader & Yaml Kanon
- [x] Implementasikan `load_npcs` di `src/muara/engine/npc_loader.py`.
- [x] Tulis dan buat kerangka `content/npcs.yaml` dengan entitas sesuai kanon dunia (contoh: Sutisna, Kusuma).
- [x] Tulis unit test untuk *yaml loading* (`tests/test_npc_loader.py`).
- [x] Conductor - User Manual Verification (Fase 2)

## Phase 3: Migrasi SaveState & Reputasi
- [x] Tingkatkan versi `SaveState` di `src/muara/models/save_state.py` ke v3.
- [x] Tambahkan properti `reputations: dict[str, dict[str, int]]` pada `SaveState`.
- [x] Tulis test migrasi *SaveState* v2 -> v3 yang memastikan persistensi file save lama tetap utuh.
- [x] Modifikasi `GameState` dengan metode baru `change_reputation(npc_id, rep_type, amount)` dan sinkronisasi clock `_sync_npc_locations()`.
- [x] Conductor - User Manual Verification (Fase 3)

## Phase 4: Integrasi DSL Hooks
- [x] Tambahkan parsing `change_rep(...)` ke dalam `_execute_hooks` di `src/muara/engine/chapter_runner.py`.
- [x] Lakukan penambahan hook yang sama di `src/muara/gui/app.py` agar GUI juga mendukung modul ini.
- [x] Tulis test integrasi (playthrough script dan textual pilot) yang memvalidasi bahwa poin reputasi bisa didapat dari hook transisi *scene*.
- [x] Conductor - User Manual Verification (Fase 4)

## Phase 5: Kualitas & Dokumentasi
- [x] Validasi *pass rate* keseluruhan test suite.
- [x] Perbarui `AGENTS.md` (bagian hooks baru dan penjelasan modul NPCEntity).
- [x] Pastikan kode memenuhi standard format pep8/black di repositori.
- [x] Conductor - User Manual Verification (Fase 5)