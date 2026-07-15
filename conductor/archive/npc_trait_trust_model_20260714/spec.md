# Specification: NPC Trait & Trust Model

## Overview

Track ini mengimplementasikan padanan teknis **Level 3 (Character AI)** dan **Level 4 (Reputation System)** pada roadmap ChatGPT (digabung karena sangat berkaitan). 

Dengan `GameClock` dari Track 1 yang kini memicu berjalannya *Dynamic Events*, kita kini memiliki waktu dunia (pagi, siang, malam). Track ini menambahkan representasi NPC (Non-Player Character) yang jadwal dan lokasinya terkait dengan *GameClock*, serta sistem reputasi yang berevolusi dari flag primitif `trust_level` menjadi sistem yang matang.

## Background

Saat ini, lokasi NPC dan "siapa berada di mana" diprogram *hardcoded* di dalam teks YAML. Reputasi pemain dengan faksi/NPC masih dibatasi pada satu flag integer primitif `trust_level` yang diubah secara manual. Agar game dapat menangani agenda faksi (Level 12) di masa depan, karakter harus direpresentasikan sebagai entitas data (`NPCEntity`).

**PENTING (Batasan Kanon):** Seperti tertuang dalam `docs/00_WORLD_BIBLE.md`, hanya 8 karakter kanon yang diizinkan berinteraksi di level terdalam: Sutisna, Kusuma, Rusli, Indra, Bella, Lottie, Vivi, Emiko. Sistem ini tidak boleh secara otomatis mem-generate identitas nama acak yang berinteraksi di ruang utama ini.

## Functional Requirements

### 1. NPCEntity Data Model
Mendefinisikan entitas Pydantic `NPCEntity` yang menampung profil karakter:
- `id`: identifier (misal: "sutisna", "kusuma").
- `name`: nama *display*.
- `traits`: list of string yang mendefinisikan *personality* dasar.
- `default_location`: lokasi default jika jadwal tidak menimpa.
- `schedule`: list of `NPCSchedule` (mapping `shift` ke `location`).

### 2. Reputation System
Meningkatkan `trust_level` menjadi `ReputationSystem` yang melacak *trust* (kepercayaan) dan *fear* (rasa takut) pemain secara per-entitas, di mana nilai ini diinjeksikan secara transparan ke *GameState*.
- Format data di dalam `SaveState`: `reputations: dict[str, dict[str, int]]` (contoh: `{"sutisna": {"trust": 5, "fear": 2}}`).
- Hook DSL baru: `change_rep(npc_id, type, amount)`.

### 3. NPCScheduler
Scheduler yang berjalan seiring berubahnya `world_shift` dari Track 1:
- Saat `advance_clock_shift` terpanggil, `NPCScheduler` akan mengevaluasi di mana setiap NPC berada dan menyimpan nilai tersebut ke flag proyeksional `npc_<id>_location`.
- Flag ini dapat dievaluasi oleh sistem yaml menggunakan `evaluate_condition("npc_sutisna_location == gudang")`.

## Acceptance Criteria
- [ ] Model `NPCEntity`, `NPCSchedule` selesai dibuat di `src/muara/models/npc.py`.
- [ ] Berkas kanon `content/npcs.yaml` ter-load menggunakan `load_npcs()`.
- [ ] `GameState` memiliki utilitas untuk menangani reputasi (`change_rep`).
- [ ] Terdapat flag turunan `npc_<id>_location` yang otomatis ter-update saat `advance_clock_shift` dipanggil.
- [ ] Hook `change_rep` terdaftar dan dieksekusi di `ChapterRunner` dan `GameScreen`.
- [ ] *Backward Compatibility*: Save lama (versi 2) dapat dimuat dengan lancar dan ditingkatkan menjadi versi 3 (memuat data reputasi).
- [ ] Semua test (291 tests) lulus.
- [ ] Uji fungsional tambahan untuk reputasi dan lokasi NPC.

## Dependencies
Bergantung langsung pada `world_shift` dari implementasi Track 1. Track ini tidak memerlukan Track 3 (Evidence).