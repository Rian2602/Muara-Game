# Narrative Expansion Design

## Problem Analysis

The current 11-chapter structure has these issues:
1. **Branches converge quickly** — All paths (03a/03b/03c) eventually lead to similar outcomes
2. **No failure state** — Player never experiences meaningful loss or consequence
3. **Passive protagonist** — Rasmi reacts but doesn't drive action
4. **No escalation** — Conflict doesn't build through narrative
5. **Abrupt ending** — 06_penutup is too short and unsatisfying

## Proposed Solution: 5 New Chapters (07-11)

### Chapter 07: AKIBAT (Consequences)
**Purpose:** Show immediate consequences of player's choice in Ch05
- Scene 1: Morning after — Rasmi wakes to find something changed
- Scene 2: First consequence — based on chapter_5_choice flag
- Scene 3: New threat emerges — someone knows about the book
- Scene 4: Choice — confront the threat or avoid it
- **New Flags:** `ancaman_diketahui` (bool), `respon_ancaman` (string)

### Chapter 08: TEKANAN (Pressure)
**Purpose:** Escalate conflict — external forces close in
- Scene 1: Mandor calls a meeting — something is wrong
- Scene 2: Jaya approaches with urgent news
- Scene 3: Player must decide — trust Jaya or protect yourself
- Scene 4: Consequence of choice — immediate impact
- **New Flags:** `percaya_jaya` (bool), `tekanan_meningkat` (int)

### Chapter 09: PILIHAN SULIT (Difficult Choice)
**Purpose:** Force meaningful sacrifice — player must give something up
- Scene 1: The cost of truth becomes clear
- Scene 2: Three paths diverge — each requires sacrifice
- Scene 3: Path A — Sacrifice safety for evidence
- Scene 4: Path B — Sacrifice evidence for safety
- Scene 5: Path C — Sacrifice relationship for truth
- **New Flags:** `pengorbanan` (string), `bukti_tersembunyi` (bool)

### Chapter 10: KONFRONTASI (Confrontation)
**Purpose:** Climactic showdown — player faces the antagonist
- Scene 1: The moment arrives — no more hiding
- Scene 2: Face the antagonist — based on accumulated flags
- Scene 3: The truth comes out — or stays hidden
- Scene 4: Immediate aftermath — player must live with choice
- **New Flags:** `konfrontasi_berhasil` (bool), `kebenaran_terungkap` (bool)

### Chapter 11: WARISAN (Legacy)
**Purpose:** Meaningful ending — player's choices create lasting impact
- Scene 1: Time passes — show long-term consequences
- Scene 2: Rasmi's legacy — based on all accumulated choices
- Scene 3: Final reflection — what did it all mean?
- Scene 4: Open ending — leave player with question
- **New Flags:** `warisan_positif` (bool), `cerita_tertulis` (bool)

## New Flag System

### Existing Flags (kept)
- melihat_anomali (bool)
- berbicara_dengan_jaya (bool)
- melapor (bool)
- sembunyikan_bukti (bool)
- terus_mencatat (bool)
- trust_level (int)
- bukti_kuat (bool)
- chapter_5_choice (string)

### New Flags (added)
- `ancaman_diketahui` (bool) — Does someone know about the book?
- `respon_ancaman` (string: hadapi/hindari) — How did player respond?
- `percaya_jaya` (bool) — Does player trust Jaya?
- `tekanan_meningkat` (int: 0-10) — How much pressure has built?
- `pengorbanan` (string: bukti/keselamatan/hubungan) — What did player sacrifice?
- `bukti_tersembunyi` (bool) — Is evidence still hidden?
- `konfrontasi_berhasil` (bool) — Did confrontation succeed?
- `kebenaran_terungkap` (bool) — Is truth revealed?
- `warisan_positif` (bool) — Is legacy positive?
- `cerita_tertulis` (bool) — Is story written down?

## New Endings (2 added)

### Ending 5: "PEMBEBASAN" (Liberation)
- **Trigger:** kebenaran_terungkap == true AND warisan_positif == true
- **Description:** Truth is revealed, Rasmi is freed from oppression
- **Emotional tone:** Hope, liberation, justice

### Ending 6: "KEHANCURAN" (Destruction)
- **Trigger:** konfrontasi_berhasil == false OR tekanan_meningkat >= 8
- **Description:** Everything falls apart — Rasmi loses everything
- **Emotional tone:** Loss, despair, tragedy

## Branching Structure

```
Ch05 → Ch07 (consequences)
         ↓
       Ch08 (pressure)
         ↓
       Ch09 (difficult choice)
         ↓
       Ch10 (confrontation)
         ↓
       Ch11 (legacy)
         ↓
       Endings (1-6)
```

Each chapter has 2-3 major branches, creating 6-9 distinct paths through the new content.

## Success Metrics

- [ ] 5 new chapters created (07-11)
- [ ] 10 new flags added
- [ ] 2 new endings added
- [ ] At least 3 distinct narrative branches
- [ ] At least 1 failure state branch
- [ ] All paths lead to valid endings
- [ ] No dead-end branches
