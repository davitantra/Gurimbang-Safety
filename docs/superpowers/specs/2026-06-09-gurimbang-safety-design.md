# Gurimbang Safety Intelligence System — Design Spec
**Date:** 2026-06-09  
**Status:** Approved

---

## Overview

Sistem pemrosesan data safety harian berbasis AI agents yang berjalan sepenuhnya di dalam Claude Code. Setiap pagi, agen-agen secara otomatis menarik data dari AWS RDS MySQL dan Google Sheets, memvalidasi temuan inspeksi dengan kombinasi rule-based dan LLM, lalu menghasilkan laporan intervensi harian langsung di Claude Code.

---

## Data Sources

| No | Data | Sumber |
|----|------|--------|
| 1 | Data insiden | AWS RDS MySQL |
| 2 | Data inspeksi & temuan | AWS RDS MySQL |
| 3 | Data penanggung jawab (PJ) area | Google Sheets |
| 4 | Data lokasi & detail lokasi | AWS RDS MySQL |
| 5 | Validasi temuan (blindspot, level risiko, kategori risiko tinggi) | Rule-based + LLM (Claude) |
| 6 | Kategori temuan berisiko tinggi | Google Sheets |

Google Sheets diupdate manual oleh tim HSE, relatif jarang berubah (mingguan/bulanan).

---

## Architecture

### Layer 1 — Data Connectors
Python scripts yang menangani koneksi ke masing-masing sumber data:

- `connectors/mysql_connector.py` — koneksi ke AWS RDS MySQL, query insiden, inspeksi, lokasi
- `connectors/sheets_connector.py` — koneksi ke Google Sheets API, baca PJ area & kategori risiko tinggi

Koneksi dikonfigurasi via environment variables (`.env`), tidak ada kredensial hardcoded.

### Layer 2 — Processing Agents
Tiga agen berjalan berurutan:

**Agent 1: Agregasi**
- Menarik semua data dari connectors
- Menggabungkan data insiden, inspeksi, lokasi, PJ area dalam satu struktur
- Output: dataset terpadu dalam memory (dict/dataframe)

**Agent 2: Validasi**
- Step 1 (Rule-based): 
  - Deteksi blindspot berdasarkan kriteria tetap (lokasi tanpa inspeksi dalam N hari, dsb.)
  - Hitung due date berdasarkan level risiko
  - Flag temuan overdue
- Step 2 (LLM — Claude API):
  - Kasus abu-abu yang tidak terjawab rule-based dikirim ke Claude
  - Claude menentukan: apakah blindspot, level risiko, apakah masuk kategori risiko tinggi
- Output: dataset tervalidasi dengan flag risiko dan due date

**Agent 3: Pelaporan**
- Menyusun laporan harian terstruktur dari dataset tervalidasi
- Format output:
  - Ringkasan eksekutif (jumlah temuan, overdue, risiko tinggi)
  - Daftar intervensi: PJ area, temuan, level risiko, due date, status
  - File `.docx` tersimpan di folder `reports/YYYY-MM-DD/`

### Layer 3 — Scheduler
- Menggunakan `CronCreate` bawaan Claude Code
- Berjalan otomatis setiap pagi pukul 05.00
- Manual trigger tersedia kapan saja lewat perintah di Claude Code

### Layer 4 — Output
Laporan muncul di Claude Code sebagai:
1. **Ringkasan eksekutif** — markdown singkat: total temuan, jumlah overdue, jumlah risiko tinggi
2. **Daftar intervensi** — tabel: siapa PJ-nya, temuan apa, risiko, due date, status
3. **File arsip** — `.docx` tersimpan lokal di `Gurimbang-Safety/reports/`

---

## Validation Logic

### Rule-Based (dijalankan lebih dulu)
- Temuan dengan level risiko **High** → due date 1x24 jam
- Temuan dengan level risiko **Medium** → due date 3 hari
- Temuan dengan level risiko **Low** → due date 7 hari
- Lokasi tanpa inspeksi lebih dari threshold → flagged sebagai blindspot
- Temuan melewati due date → flagged overdue

### LLM Fallback (Claude API)
- Dipanggil hanya jika rule-based tidak bisa memutuskan
- Prompt berisi: deskripsi temuan, konteks lokasi, kategori dari Google Sheets
- Output terstruktur: `{ "is_blindspot": bool, "risk_level": "Low|Medium|High", "is_high_risk": bool }`

---

## Access Control

Tim HSE dengan level akses berbeda:
- **Viewer** — hanya bisa membaca laporan
- **Admin** — bisa trigger manual refresh, melihat semua area
- **Supervisor** — melihat laporan area tanggung jawabnya saja

Implementasi akses control pada fase berikutnya setelah sistem inti berjalan.

---

## Notifications (Fase Berikutnya)

Notifikasi ke PJ area akan ditambahkan setelah sistem inti stabil:
- Channel: WhatsApp dan/atau Email (belum ditentukan)
- Trigger: temuan overdue atau risiko tinggi baru
- Konten: nama PJ, detail temuan, due date, link laporan

---

## Project Structure

```
Gurimbang-Safety/
├── connectors/
│   ├── mysql_connector.py
│   └── sheets_connector.py
├── agents/
│   ├── agent_agregasi.py
│   ├── agent_validasi.py
│   └── agent_pelaporan.py
├── reports/               # output .docx harian
├── docs/
│   └── superpowers/specs/
│       └── 2026-06-09-gurimbang-safety-design.md
├── .env.example
├── requirements.txt
└── main.py               # entry point, orchestrates semua agents
```

---

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Language | Python 3.11+ |
| MySQL client | `pymysql` atau `SQLAlchemy` |
| Google Sheets | `gspread` + Google Service Account |
| LLM | Claude API (`anthropic` SDK) |
| Report generation | `python-docx` |
| Scheduler | Claude Code `CronCreate` |
| Config | `python-dotenv` |

---

## Out of Scope (v1)

- Web dashboard / UI terpisah
- Notifikasi WhatsApp / Email
- Multi-user login / autentikasi web
- Mobile app
