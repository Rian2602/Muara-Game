# Implementation Plan: Perbaikan Label Section AGENTS.md

## Phase 1: Audit dan Perbaikan

- [x] Task: Baca ulang section penuh
    - [x] Buka `AGENTS.md`, cari heading `## New Features (Cultivation World Simulator Adaptation)`
    - [x] Baca seluruh isi section sampai heading berikutnya atau akhir file
    - [x] Catat baris mana pun (selain judul) yang menyebut istilah di luar tema
          Batavia 1899 (contoh istilah yang WAJIB dicek: "cultivation", "kultivasi",
          "cangkir", "qi", "sect", "cultivator" — atau nama karakter yang tidak ada
          di daftar flag/chapter yang sudah dikonfirmasi di `AGENTS.md` bagian atas)
- [x] Task: Ganti judul section
    - [x] Ganti `## New Features (Cultivation World Simulator Adaptation)` menjadi
          `## New Features (Engine Enhancements)`
    - [x] Jangan ubah isi di bawahnya kecuali ada temuan dari task audit di atas
- [x] Task: Jika ditemukan kontaminasi lain di isi section
    - [x] JANGAN hapus otomatis
    - [x] Tulis daftar baris yang dicurigai ke output/laporan task (bukan commit
          message — laporkan ke user secara eksplisit sebagai bagian dari
          ringkasan pekerjaan)
- [x] Task: Verifikasi tidak ada file lain yang tersentuh
    - [x] Jalankan `git diff --stat` — hasil harus menunjukkan HANYA `AGENTS.md`
          yang berubah
- [x] Task: Jalankan test suite penuh
    - [x] `uv run pytest tests/ -v`
    - [x] Semua test harus tetap lulus (perubahan ini murni dokumentasi)
- [x] Task: Conductor - User Manual Verification 'Audit dan Perbaikan' (Protocol in workflow.md)

## Definition of Done

Track ini selesai HANYA jika:
1. Judul section sudah diganti
2. `git diff --stat` menunjukkan hanya `AGENTS.md` yang berubah
3. Semua test yang ada tetap lulus
4. Jika ada temuan kontaminasi tambahan, sudah dilaporkan eksplisit ke user
   (bukan dihapus diam-diam)
