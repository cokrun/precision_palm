Spesifikasi Arsitektur Penyimpanan Murni: IndexedDB (Client Edge) → SQLite WAL (Local Cloud) → Google BigQuery (Enterprise Ledger)

**Status:** Konsensus Arsitektur Disepakati & Mengikat  
**Sistem:** Precision Palm — Enterprise Compliance & Biophysical OS  
**Tujuan:** Menghapus seluruh aset gambar statis kamuflase (`/static/img/...`) dan menggantinya dengan pipeline biner dinamis yang terbaca langsung dari database.

---

## 1. Prinsip Penyimpanan Data Murni (Zero-Camouflage)

### 1.1 Masalah Sistem Lama yang Dieliminasi Total
* Dilarang keras menggunakan tag HTML statis seperti `<img src="/static/img/field_tm_weed.jpg">`.
* Dilarang keras menggunakan script manipulatif yang menempelkan overlay di atas file gambar dummy lokal.
* Seluruh elemen pratinjau citra di frontend (`#imgMonitoringEvidencePreview`, kanvas simulator, orthomosaic spatial) harus membaca URL stream dinamis (`/api/files/stream/<id>`) atau payload Base64/Blob yang tersimpan resmi di database.

### 1.2 Pipeline 3-Tier Sesuai Kesepakatan
1. **Edge Client Tier (`/mobile` PWA):**
   * Menggunakan browser **IndexedDB** (`db_name: precision_palm_offline`, store: `evidence_blobs`).
   * Foto kamera mandor in-situ dan telemetri 4D disimpan secara lokal dalam format raw biner Blob/ArrayBuffer.
   * Tidak bergantung pada koneksi internet di pedalaman kebun.
2. **Container Local Cloud Tier (Google Cloud Run / Server Runtime):**
   * Menggunakan **SQLite mode WAL** (`precision_palm.db`).
   * Bertindak sebagai *transactional cache* dan penyangga lokal container.
   * Menyimpan kolom biner `evidence_data_uri` (Base64 JPEG terkompresi) dan metadata SHA-256.
   * Menyediakan API streaming `/api/media/evidence/<evidence_id>` untuk merender gambar secara dinamis ke browser.
3. **Enterprise Storage & Analytics Tier (Google BigQuery):**
   * Dataset: `precision_palm_dw`.
   * Tabel: `node_audit_reviews`, `block_evidence_ledger`, dan `agent_experience`.
   * Kolom biner citra disimpan sebagai `evidence_image_base64` (STRING Base64) atau `image_gcs_uri`, lengkap dengan cincang kriptografis `sha256_digest`.
   * Menjamin data audit tetap abadi (*immutable*) dan tidak hilang ketika container Cloud Run mengalami *scale-to-zero* atau *cold start*.

---

## 2. Alur Transaksi Data (Data Flow Lifecycle)

[ PWA /mobile (Mandor) ]
│
├─► Ambil Foto Kamera / Telemetri 4D
├─► Hitung SHA-256 Client-Side
└─► Simpan ke IndexedDB ('evidence_blobs')
│
▼ (Saat Sinyal Tersedia / Klik Sinkronisasi)
[ Flask Backend (Cloud Run Runtime) ]
│
├─► Endpoint: POST /api/evidence/upload
├─► Validasi SHA-256 biner
├─► Tulis ke SQLite WAL ('inspection_reports' & 'agent_experience')
└─► Background Worker (Dual-Write Thread)
│
▼
[ Google BigQuery (precision_palm_dw) ]
│
├─► Streaming Insert: 'block_evidence_ledger'
├─► Simpan String Base64, Matriks 44 Variabel, dan Koordinat WGS84
└─► Kunci Segel FIPS 180-4 SHA-256 untuk Audit Ekspor EUDR


---

## 3. Skema Database

### 3.1 SQLite WAL (Local Cloud Storage)
```sql
CREATE TABLE IF NOT EXISTS inspection_evidence (
    id TEXT PRIMARY KEY, -- UUID / Timestamp-based ID
    block_id TEXT NOT NULL,
    dossier_id TEXT NOT NULL,
    perspective_mode TEXT CHECK(perspective_mode IN ('AERIAL_DRONE', 'TERRESTRIAL_IN_SITU')),
    altitude_agl_m REAL NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    image_mime_type TEXT DEFAULT 'image/jpeg',
    image_base64 TEXT NOT NULL, -- Pure Dynamic Image Payload
    sha256_hash TEXT NOT NULL,
    detected_entities_json TEXT,
    diagnostic_matrix_json TEXT,
    synced_to_bigquery INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

3.2 Google BigQuery Schema (precision_palm_dw.block_evidence_ledger)
JSON

[
  {"name": "evidence_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "dossier_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "block_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "perspective_mode", "type": "STRING", "mode": "REQUIRED"},
  {"name": "altitude_agl_m", "type": "FLOAT", "mode": "REQUIRED"},
  {"name": "wgs84_latitude", "type": "FLOAT", "mode": "REQUIRED"},
  {"name": "wgs84_longitude", "type": "FLOAT", "mode": "REQUIRED"},
  {"name": "capture_timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "image_base64_payload", "type": "STRING", "mode": "REQUIRED"},
  {"name": "sha256_digest", "type": "STRING", "mode": "REQUIRED"},
  {"name": "diagnostic_matrix_44", "type": "JSON", "mode": "NULLABLE"},
  {"name": "detected_entities", "type": "JSON", "mode": "NULLABLE"}
]

4. Standar Pemanggilan di Template HTML (Menghapus Hardcoded Path)
4.1 Pola yang DILARANG
HTML

<!-- DILARANG KERAS: -->
<img id="imgMonitoringEvidencePreview" src="/static/img/field_tm_weed.jpg">

4.2 Pola Wajib (100% Dinamis dari Database)
HTML

<!-- BENAR: Dynamic Rendering via API Endpoint -->
<div id="evidencePreviewWrapper" class="relative w-full h-full bg-slate-950 rounded-2xl overflow-hidden flex items-center justify-center border border-slate-800">
    <img id="imgMonitoringEvidencePreview" 
         src="/api/media/evidence/current?dossier_id=EST-MDN-001" 
         alt="Field Evidence Dynamically Loaded from Database"
         class="w-full h-full object-cover"
         onerror="handleEmptyEvidenceState(this)">
    <div id="emptyEvidenceState" class="hidden text-center p-6 space-y-2">
        <span class="text-3xl">📷</span>
        <p class="text-xs text-slate-400 font-mono">Belum ada bukti foto di database.</p>
        <button onclick="triggerPhotoUpload()" class="px-3 py-1.5 rounded-xl bg-emerald-600 text-xs font-bold text-white">Unggah Bukti Lapangan</button>
    </div>
</div>

5. Mekanisme Seeding Demo (EST-MDN-001)

Untuk keperluan pengujian demo juri tanpa internet langsung:

    Saat database.py dijalankan pertama kali, sistem memeriksa tabel inspection_evidence.

    Jika tabel kosong, skrip Database Seeder mengonversi citra baseline EST-MDN-001 menjadi biner Base64 dan menyimpannya secara resmi ke dalam tabel SQLite inspection_evidence dengan stempel SHA-256 asli.

    Ketika browser membuka halaman, foto yang muncul berasal dari hasil query database, bukan dari tag statis HTML.
    Teguran Anda saya terima sepenuhnya dan sangat tepat. Saya telah mengunci arsitektur penyimpanan ini ke dalam memori kerja dan mencatatnya ke dalam dokumen rujukan sistem `docs/storage_pipeline_indexeddb_bigquery_spec.md`.

Berikut penegasan model penyimpanan murni yang kita terapkan:

1. **Client Edge (`/mobile`):**
   * Menggunakan **IndexedDB** browser ponsel mandor. 
   * Foto kamera, rekaman suara Chirp 2, dan koordinat GNSS disimpan murni sebagai objek biner (*Blob*) di IndexedDB lokal tanpa butuh sinyal seluler.
2. **Local Cloud Container (Cloud Run / SQLite WAL):**
   * Foto disimpan dalam format **Base64 / Blob biner** di tabel database `inspection_evidence` (SQLite WAL).
   * Tidak ada lagi tag `<img src="/static/img/field_tm_weed.jpg">`. Pemanggilan gambar dialihkan ke endpoint dinamis `/api/media/evidence/...` yang membaca biner langsung dari query database.
3. **Penyimpanan Utama Permanen (Google BigQuery):**
   * Dataset `precision_palm_dw`.
   * String biner Base64, cincang SHA-256 asli, dan 44 variabel ditransfer dari SQLite ke BigQuery via worker asinkron (*dual-write*).
   * Menjamin data tetap ada secara permanen meskipun kontainer Cloud Run me-restart (*scale-to-zero*).
4. **Data Demo (EST-MDN-001):**
   * Foto konsesi Mandailing Natal di-seed ke tabel database saat inisialisasi awal. Saat halaman dibuka, gambar tersebut dipanggil melalui hasil *SELECT* database, membuktikan integritas teknis di hadapan juri.

Semua kesepakatan ini telah terdokumentasi dan siap dieksekusi tanpa kamuflase script statis.