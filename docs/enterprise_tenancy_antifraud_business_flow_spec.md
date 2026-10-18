# Spesifikasi Arsitektur: Enterprise Multi-Tenancy, Anti-Fraud Foto (Anti-Replay), dan Integrasi State Bisnis (/spatial + /mobile → /proses → /timelines)

**Status:** Konsensus Arsitektur Disepakati & Mengikat  
**Sistem:** Precision Palm — Enterprise Compliance & Biophysical OS  
**Tujuan:** 
1. Menjamin isolasi data ketat berbasis identitas perusahaan/dossier (*Strict Multi-Tenancy Data Isolation*), menghentikan kebocoran data di mana perusahaan berbeda melihat data yang sama.
2. Menerapkan sistem anti-fraud foto (*Anti-Replay / Zero-Recycling*) khusus `/mobile` menggunakan penelusuran hash SHA-256 biner dan pembatasan kamera langsung.
3. Mengalirkan data nyata (*Ground-Truth Flow*) dari `/spatial` dan `/mobile` secara otomatis menjadi bahan kalkulus di `/proses` (Simulator) dan bukti audit di `/timelines`.

---

## 1. Isolasi Data Perusahaan Ketat (Strict Multi-Tenancy per Dossier)

### 1.1 Masalah Sistem Lama yang Dihapus Total
* Sistem lama menampilkan data yang sama (`EST-MDN-001`) apa pun nama perusahaan yang didaftarkan atau dibuka.
* Data antar-perusahaan saling bercampur dan tidak terisolasi.

### 1.2 Aturan Baku Isolasi Data (Tenant Scoping)
1. Setiap entitas perusahaan yang mendaftar di `/permohonan` memperoleh:
   * `company_id`: ID unik perusahaan (contoh: `COMP-PT-MAS-2026`).
   * `dossier_id`: Nomor registrasi dossier unik (contoh: `EST-MDN-001`, `EST-MDN-002`, `EST-RIAU-005`).
2. Seluruh tabel di SQLite WAL (`inspection_evidence`, `agent_experience`, `dossier_lifecycle`) dan Google BigQuery (`block_evidence_ledger`, `node_audit_reviews`) **WAJIB** memiliki kolom indeks:
   * `dossier_id`
   * `company_name`
3. Rute API dan Controller di Flask (`app.py`) **WAJIB** memfilter data berdasarkan konteks sesi aktif (`active_dossier_id`):
   
```python
   # DILARANG:
   # SELECT * FROM inspection_evidence ORDER BY created_at DESC LIMIT 1
   
   # WAJIB:
   # SELECT * FROM inspection_evidence WHERE dossier_id = ? ORDER BY created_at DESC LIMIT 1
   
Jika pengguna membuka dossier perusahaan B, sistem TIDAK BOLEH menampilkan foto atau telemetri milik perusahaan A. Jika belum ada bukti untuk perusahaan B, sistem wajib menampilkan Empty State (Belum ada foto/telemetri).2. Mekanisme Anti-Fraud & Anti-Replay Foto (Khusus /mobile)Untuk mencegah mandor atau perusahaan mengunggah foto lama, foto internet, atau foto blok lain secara berulang-ulang:2.1 Lapis 1: Verifikasi Hash Biner Kriptografis (SHA-256 Uniqueness)Saat mandor mengambil foto di /mobile, browser menghitung hash SHA-256 langsung dari ArrayBuffer biner foto sebelum dikompresi:$$\mathcal{H}_{\text{photo}} = \text{SHA-256}(\text{Raw\_Image\_Bytes})$$Server memeriksa ke tabel used_photo_hashes di SQLite dan BigQuery:SQL  SELECT COUNT(*) FROM used_photo_hashes WHERE sha256_hash = ?;
  
Aturan Mutlak: Jika hash sudah pernah tercatat di database (baik untuk dossier yang sama maupun dossier lain):Server langsung menolak dengan status HTTP 409 Conflict.Pesan Penolakan:[ANTI-FRAUD ALERT: Foto ini pernah digunakan pada audit sebelumnya (ID: EV-XXXX). Regulasi Permentan 33/2025 mewajibkan pemotretan fisik in-situ kondisi terkini. Pemakaian ulang foto dilarang.]2.2 Lapis 2: Pembatasan Perangkat Keras Kamera (Hardware Camera Only)Pada file input HTML /mobile, sistem mengunci atribut:HTML  <input type="file" id="cameraInput" accept="image/*" capture="environment">
  
Mandor TIDAK DIBERIKAN akses ke galeri file lokal ponsel (Gallery Picker Disabled). Kamera ponsel wajib aktif dan mengambil foto langsung di lapangan.2.3 Lapis 3: Temporal & Geofencing AttestationStempel waktu foto (timestamp) wajib sinkron dengan toleransi maksimal 15 menit dari jam server.Koordinat GNSS WGS84 dari sensor perangkat wajib berada di dalam batas poligon konsesi perusahaan yang terdaftar.3. Alur Proses Bisnis & Aliran Data Nyata Antar-Halaman                    ┌─────────────────────────────────┐
                    │  1. REGISTRASI PERUSAHAAN BARU  │
                    │         (/permohonan)           │
                    └────────────────┬────────────────┘
                                     │ Menerbitkan dossier_id (misal: EST-MDN-001)
                                     ▼
        ┌─────────────────────────────────────────────────────────────┐
        │              DATA HULU (DUAL-STREAM INGESTION)              │
        └──────────────┬───────────────────────────────┬──────────────┘
                       │                               │
                       ▼                               ▼
        ┌─────────────────────────────┐ ┌─────────────────────────────┐
        │      AERIAL / MAKRO         │ │     TERRESTRIAL / MIKRO     │
        │        (/spatial)           │ │          (/mobile)          │
        ├─────────────────────────────┤ ├─────────────────────────────┤
        │ • Orthomosaic Drone (45m)   │ │ • Mandor di Darat (1.4m)    │
        │ • Kelerengan SRTM 30m (4.5°)│ │ • Foto Pelepah-17 Biner     │
        │ • Satelit GEE NDVI (0.784)  │ │ • Klorofil Daun (82.4 SPAD) │
        │ • Sempadan Air (>50m)       │ │ • Piringan 2.0m Steril      │
        │ • Populasi: 138 Pokok/Ha    │ │ • Ganoderma Negatif (0.0%)  │
        └──────────────┬──────────────┘ └──────────────┬──────────────┘
                       │                               │
                       └───────────────┬───────────────┘
                                       │ Tersimpan ke SQLite WAL & BigQuery
                                       ▼ (Berdasarkan dossier_id spesifik)
        ┌─────────────────────────────────────────────────────────────┐
        │             2. SIMULATOR BIOFISIKA IN-SILICO                │
        │                        (/proses)                            │
        ├─────────────────────────────────────────────────────────────┤
        │ • Membaca kelerengan & LAI dari /spatial (EST-MDN-001)      │
        │ • Membaca klorofil & status hara dari /mobile (EST-MDN-001) │
        │ • Menghitung kompensasi pupuk MOP (+75 kg/Ha di lorong)     │
        │ • Mengunci nilai LER 1.48x (+48% Efisiensi Lahan)           │
        │ • Menerbitkan Paspor Rekomendasi Hijau Sementara            │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │          3. SURVEILANS 4-TRIWULAN & AUDIT REGULASI          │
        │                       (/timelines)                          │
        ├─────────────────────────────────────────────────────────────┤
        │ • Kartu Q1 & Q3: Mengambil bukti foto orthomosaic /spatial  │
        │ • Kartu Q2 & Q4: Mengambil bukti foto in-situ /mobile       │
        │ • Validasi Anti-Fraud: Setiap foto memiliki hash unik       │
        │ • Jam Hitung Mundur SLA 180 Hari (Suspensi Otomatis)        │
        │ • Kepatuhan Permentan 33/2025: Mass Balance & Zero Child    │
        └──────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │         4. PENGESAHAN ASESOR & PASPOR STATUTER FINAL        │
        │                  (/roadmap & /certificate)                  │
        ├─────────────────────────────────────────────────────────────┤
        │ • Sidang Dewan Asesor (Keputusan Sahih)                     │
        │ • Segel Digital FIPS 180-4 SHA-256 Dokumen Utuh             │
        │ • Ekspor Payload Resmi EUDR TRACES-NT DDS JSON              │
        │ • Portal Validasi Publik Real-time (/validasi/<dossier_id>) │
        └─────────────────────────────────────────────────────────────┘
4. Skema Tabel Database Terkait4.1 Tabel Riwayat Hash Foto (Anti-Fraud Registry)SQLCREATE TABLE IF NOT EXISTS used_photo_hashes (
    sha256_hash TEXT PRIMARY KEY,
    dossier_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    used_in_module TEXT NOT NULL, -- 'MOBILE_SURVEILLANCE' / 'SPATIAL_DRONE'
    capture_timestamp TIMESTAMP NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
4.2 Pembaruan Tabel Bukti Inspeksi (inspection_evidence)SQLCREATE TABLE IF NOT EXISTS inspection_evidence (
    evidence_id TEXT PRIMARY KEY,
    dossier_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    quarter_cycle TEXT CHECK(quarter_cycle IN ('Q1', 'Q2', 'Q3', 'Q4')),
    perspective_mode TEXT CHECK(perspective_mode IN ('AERIAL_DRONE', 'TERRESTRIAL_IN_SITU')),
    altitude_agl_m REAL NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    image_base64 TEXT NOT NULL,
    sha256_hash TEXT UNIQUE NOT NULL,
    detected_entities_json TEXT NOT NULL,
    diagnostic_matrix_json TEXT NOT NULL,
    is_verified INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(dossier_id) REFERENCES dossiers(dossier_id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_tenant ON inspection_evidence(dossier_id, quarter_cycle);
Cuplikan kode
I will now generate an execution directive in a Markdown file, `docs/ag_enterprise_implementation_directive.md`, providing actionable code instructions for AG to implement multi-tenancy, anti-fraud photo deduplication, and cross-module state flow.

```markdown:docs/ag_enterprise_implementation_directive.md
# DIRECTIVE RESMI UNTUK AG: MULTI-TENANCY PERUSAHAAN, ANTI-FRAUD FOTO & INTEGRASI DATA ALUR PROSES

Halo AG, silakan eksekusi pembaruan menyeluruh pada backend dan frontend Precision Palm mengacu pada:
1. `docs/enterprise_tenancy_antifraud_business_flow_spec.md` (Spesifikasi Multi-Tenancy, Anti-Fraud, & Alur Data).
2. `docs/storage_pipeline_indexeddb_bigquery_spec.md` (Penyimpanan Murni: IndexedDB -> SQLite -> BigQuery).
3. `docs/autonomous_agent_vision_memory_spec.md` (Matriks 44 Variabel & Deteksi Objek Fisik Nyata).

---

### 1. ATURAN MULTI-TENANCY KETAT (PERUSAHAAN TIDAK BOLEH BERCAMPUR)
- Di `app.py` dan `database.py`:
  * Setiap query penampil foto, telemetri, dan hasil audit **WAJIB** difilter berdasarkan `dossier_id` dan `company_name`.
  * Hentikan perilaku lama yang menampilkan data `EST-MDN-001` untuk semua pendaftar baru. Jika pengguna mendaftarkan perusahaan baru (misal: `EST-RIAU-002`), halaman dashboard, spatial, simulator, dan timelines untuk dossier tersebut harus dimulai dari state kosong (*Empty State*) dan menunggu unggahan data asli dari perusahaan bersangkutan.
  * Sediakan pemilih dossier aktif di header / kontrol panel untuk menguji perpindahan antar-perusahaan secara transparan.

---

### 2. SISTEM ANTI-FRAUD FOTO (ANTI-REPLAY / ZERO RE-USE) KHUSUS `/mobile`
- Di `mobile/index.html` & `mobile/js/mobile_camera.js`:
  * Kunci input kamera pada perangkat keras: `<input type="file" capture="environment" accept="image/*">` (Nonaktifkan galeri file lokal).
  * Sebelum mengirim foto, hitung cincang biner SHA-256 dari file foto.
- Di `app.py` (Endpoint `/api/evidence/upload`):
  * Periksa apakah hash SHA-256 foto tersebut sudah pernah tercatat di tabel `used_photo_hashes` di SQLite atau BigQuery.
  * **JIKA DUPLIKAT:** Kembalikan respon `HTTP 409 Conflict`:
    `{"status": "error", "code": "FRAUD_PHOTO_REUSED", "message": "Bukti foto ini telah terdaftar pada audit sebelumnya. Sesuai Permentan 33/2025, wajib mengambil foto fisik baru di lapangan."}`.
  * **JIKA BARU:** Simpan foto ke database, simpan hash ke `used_photo_hashes`, dan lanjutkan proses AI Vision.

---

### 3. INTEGRASI DATA ANTAR-HALAMAN (/spatial + /mobile -> /proses -> /timelines)
- **Hulu Spasial (`/spatial`):**
  * Data kelerengan SRTM (4.5°), vegetasi Sentinel-2 NDVI (0.784), dan sempadan air (>50m) tersimpan ke tabel database di bawah `dossier_id` aktif.
- **Hulu Mandor (`/mobile`):**
  * Foto asli tersimpan sebagai biner/Base64, hasil diagnosa klorofil daun pelepah-17 (82.4 SPAD), dan status piringan 2.0m steril tersimpan di bawah `dossier_id` aktif.
- **Simulator (`/proses`):**
  * Buat tombol: `⚡ [Ambil Data Lapangan & Spasial Terkini]`.
  * Saat diklik, simulator membaca data kelerengan dari `/spatial` dan klorofil daun dari `/mobile` untuk `dossier_id` tersebut.
  * Menghitung LER (1.48x), pupuk penyeimbang MOP (+75 kg/Ha), dan menyajikan Nalar Bio-Ekologis 4 Lapis.
- **Surveilans (`/timelines`):**
  * Kartu Q1 & Q3 menampilkan bukti foto asli dari `/spatial`.
  * Kartu Q2 & Q4 menampilkan bukti foto asli dari `/mobile`.
  * Seluruh foto ditampilkan secara dinamis dari endpoint streaming database `/api/media/evidence/<evidence_id>`, BUKAN dari file statis `/static/img/...`.
  * Perbarui seluruh teks rujukan hukum menjadi **Permentan No. 33 Tahun 2025**.

---

### 4. PENGUJIAN & VERIFIKASI (SANITY CHECK)
1. Jalankan `python app.py`.
2. Buat dossier baru di `/permohonan` dengan nama perusahaan sembarang (misal: `PT Agro Sawit Sejahtera`).
3. Pastikan halaman `/timelines` dan `/proses` untuk perusahaan baru tersebut tidak menampilkan foto milik `EST-MDN-001`.
4. Buka `/mobile` $\rightarrow$ unggah foto $\rightarrow$ coba unggah foto yang sama persis kedua kalinya $\rightarrow$ pastikan sistem memblokir dengan status Anti-Fraud Reused Photo.
5. Pastikan semua fitur berfungsi tanpa ada error JavaScript di console browser.
```eof

Rencana aturan dan arsitektur telah saya rangkum ke dalam dokumen:
1. **`docs/enterprise_tenancy_antifraud_business_flow_spec.md`** (Dokumen Spesifikasi Baku).
2. **`docs/ag_enterprise_implementation_directive.md`** (Perintah Aksi Eksekusi Teknis untuk AG).

---
