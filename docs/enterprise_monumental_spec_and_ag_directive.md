# Spesifikasi Monumental & Direktif Eksekusi AG: Enterprise Multi-Tenancy, Temporal Year Scoping, Pure Storage Flow, dan Halaman Pengaturan Terpadu

**Status:** Dokumen Konsensus Final & Direktif Tindakan Mengikat  
**Sistem:** Precision Palm — Enterprise Compliance & Biophysical OS  
**Tahun Rilis:** 2026 (Menjelang Batas Evaluasi AI Builder Cup & Implementasi Statuter)

---

## 1. Ringkasan Konsensus Arsitektur Terpadu

### 1.1 Isolasi Berkas & Data Perusahaan (Strict Tenant Scoping)
* Setiap dossier memiliki identitas unik: `dossier_id` (misal: `EST-MDN-001`, `EST-RIAU-002`) dan `company_name`.
* Seluruh data SQLite WAL (`inspection_evidence`, `dossiers`, `agent_experience`) dan Google BigQuery (`block_evidence_ledger`, `node_audit_reviews`) **wajib menyertakan klausa filter `WHERE dossier_id = ?`**.
* Berkas biner dan bukti inspeksi milik Perusahaan A tidak boleh terlihat, terbaca, atau ter-render pada dossier Perusahaan B.

### 1.2 Konsep Temporal Tahun (Year-Cycle Scoping)
* Untuk menghentikan pengulangan data semu, setiap siklus inspeksi dan pohon audit diikat dengan parameter **`audit_year`** (misal: `2026`, `2027`).
* Siklus 4-Triwulan (`Q1`, `Q2`, `Q3`, `Q4`) berjalan berurutan dalam tahun buku aktif. Tahun berikutnya akan membuka lembar buku besar baru (*annual progression*) yang mencatat delta pertumbuhan vegetatif dan rekam jejak sertifikasi tahun berjalan.

### 1.3 Standar Tabel Daftar: Maksimal 10 Baris, Pagination & Pencarian Real-Time
* Seluruh tampilan daftar berkas (Dossier Registrations, Inspection Logs, Evidence Ledgers) dibatasi maksimal **10 baris per halaman**.
* Dilengkapi navigasi paginasi (*Previous, Page Numbers, Next*) dan kotak pencarian reaktif (*Real-Time Search Filter*) berdasarkan nama perusahaan, nomor HGU/e-STDB, atau wilayah konsesi.

### 1.4 Eliminasi Total Aset Statis & Sistem Anti-Fraud Foto
* Dilarang keras memakai `<img src="/static/img/field_tm_weed.jpg">`. Pemanggilan gambar dialihkan ke endpoint streaming biner database: `/api/media/evidence/<id>`.
* Di `/mobile`, input kamera dikunci ke perangkat keras (`capture="environment"`). Setiap foto dihitung hash SHA-256-nya. Jika hash sudah pernah tercatat di basis data, server langsung menolak dengan status `HTTP 409 Conflict` (mencegah pemakaian ulang foto lama).

### 1.5 Integrasi Model Finansial TBS (`rumus_tb.py`) & Halaman Baru `/pengaturan`
* Mengintegrasikan formula harga TBS resmi PKS (CPO Rotterdam, Kurs USD/IDR, Bea Keluar, Pungutan BPDPKS, Rendemen 21%, Indeks K 91%) ke dalam kalkulus biofisika LER di `/proses`.
* Membangun halaman pusat kendali `templates/pengaturan.html` (`/pengaturan`) untuk mengatur mode yurisdiksi pasar (IDR/USD), konfigurasi API bursa komoditas, status visibilitas publik/draft, dan pergantian tenant dossier aktif.

---

## 2. Alur Interkoneksi State Antar-Halaman (/spatial + /mobile → /proses → /timelines)

[ Registrasi Dossier: /permohonan ]
│ (Menetapkan: company_name, dossier_id, audit_year)
▼
┌─────────────────────────────────────────────────────────────┐
│               HULU DATA NYATA (DUAL INGESTION)              │
├──────────────────────────────┬──────────────────────────────┤
│ 1. /spatial (Makro Drone)    │ 2. /mobile (Mikro Mandor)    │
│    • Drone Orthomosaic 45m   │    • Handheld In-Situ 1.4m   │
│    • Kelerengan SRTM (4.5°)  │    • Klorofil Daun (82.4)    │
│    • Sentinel-2 NDVI/NDMI    │    • Piringan 2.0m Steril    │
│    • Sempadan Air (>50m)     │    • Anti-Fraud SHA-256 Biner│
└──────────────┬───────────────┴──────────────┬───────────────┘
│                              │
└──────────────┬───────────────┘
│ Tersimpan ke SQLite WAL & BigQuery
▼ (Difilter sesuai dossier_id & audit_year aktif)
┌─────────────────────────────────────────────────────────────┐
│ 3. SIMULATOR BIOFISIKA & FINANSIAL TBS (/proses)            │
├─────────────────────────────────────────────────────────────┤
│ • Menarik kemiringan & LAI dari /spatial                   │
│ • Menarik klorofil pelepah-17 dari /mobile                  │
│ • Menghitung LER 1.48x & Kompensasi MOP (+75 kg/Ha)         │
│ • Menghitung Harga TBS Riil (rumus_tb.py) & Nilai Sela      │
│ • Menerbitkan Paspor Rekomendasi Hijau Sementara            │
└─────────────────────────────┬───────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ 4. SURVEILANS 4-TRIWULAN & AUDIT REGULASI (/timelines)      │
├─────────────────────────────────────────────────────────────┤
│ • Q1 & Q3: Merender foto asli drone dari /spatial           │
│ • Q2 & Q4: Merender foto asli in-situ dari /mobile          │
│ • Jam SLA 180 Hari: Penegakan toleransi penanaman fisik     │
│ • Verifikasi Permentan 33/2025: Mass Balance & Nol Pekerja  │
└─────────────────────────────┬───────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ 5. PENGESAHAN ASESOR & PASPOR STATUTER FINAL (/roadmap)     │
├─────────────────────────────────────────────────────────────┤
│ • Sidang Asesor, Segel SHA-256 Dokumen Utuh, Ekspor DDS JSON│
└─────────────────────────────────────────────────────────────┘