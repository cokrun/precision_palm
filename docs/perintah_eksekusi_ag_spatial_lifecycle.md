# SPESIFIKASI STANDAR TATA KELOLA IDENTITAS & SIKLUS AUDIT KONSESI (PRECISION PALM ENTERPRISE)

**Status:** Disepakati & Menjadi Acuan Baku Sistem  
**Tujuan:** Mencegah pencampuran data (*data mixing*), menetapkan penanda proses unik (*state tagging*), dan menjamin data persisten saat peramban dimuat ulang (*anti-data loss on refresh*).

---

## 🏢 1. STRUKTUR HIERARKI DATA 4 TINGKAT

[ LEVEL 1: CORPORATE ENTITY ]
company_id: COMP-MDN-001 (PT Mandailing Agro Sustainable)
│
└── [ LEVEL 2: ESTATE PARCEL / KEBUN ]
estate_id: EST-MDN-001 (Blok Mandailing Percontohan)
│
└── [ LEVEL 3: DOSSIER TAHUN BUKU / AUDIT YEAR ]
dossier_id: EST-MDN-001-2026 (Tahun Audit Berjalan)
│
└── [ LEVEL 4: SIKLUS PROSES OPERASIONAL (5 TAHAPAN) ]
├─ STAGE-0-ANNUAL-REG  : Registrasi & Audit Spasial (1x/thn)
├─ STAGE-1-Q1          : Surveilans Mandor Triwulan I
├─ STAGE-2-Q2          : Surveilans Mandor Triwulan II
├─ STAGE-3-Q3          : Surveilans Mandor Triwulan III
└─ STAGE-4-Q4          : Surveilans Q4 & Sidang Paspor EUDR


---

## 🏷️ 2. NOMENKLATUR PENANDA BUKTI FOTO (EVIDENCE ID)

Setiap foto yang diunggah ke GCS/Cloud Storage atau disimpan ke database wajib memiliki format identitas:

$$\text{Evidence ID} = \text{ESTATE\_ID} + \text{"-"} + \text{TAHUN} + \text{"-"} + \text{PROCESS\_STAGE} + \text{"-"} + \text{URUTAN}$$

* **Contoh Foto Ortofoto Drone Pendaftaran:**  
  `EV-EST-MDN-001-2026-REG-01`
* **Contoh Foto In-Situ Mandor Q1 (Piringan 2.0m):**  
  `EV-EST-MDN-001-2026-Q1-01`
* **Contoh Foto Sempadan Riparian Q2:**  
  `EV-EST-MDN-001-2026-Q2-01`

---

## 🔒 3. ATURAN PENYIMPANAN PERSISTEN PADA HALAMAN SPASIAL (`/spatial`)

1. **Active Dossier Session:** Parameter `kode_kebun` dan `audit_year` selalu dipertahankan di URL (`/spatial?kode=EST-MDN-001&year=2026`) dan disinkronkan ke sesi pengguna.
2. **Kueri Data Selektif:**
   * Saat halaman Spasial dimuat, backend membaca seluruh bukti foto pada `dossier_id = 'EST-MDN-001-2026'` dengan filter bawaan tahap `STAGE-0-ANNUAL-REG` dan surveilans berjalan.
3. **Pemberian Skor & Sintesis Otomatis:**
   * Jika minimal 2 foto bukti (Drone + In-Situ) telah diverifikasi AI, sistem menerbitkan status *Consolidated Evidence Ledger: APPROVED_ELIGIBLE*.
```eof

```python:database_schema_engine.py
# ==============================================================================
# Precision Palm - Enterprise Relational Database Engine (SQLite WAL & BigQuery)
# Hierarki Baku: Company -> Estate -> Audit Dossier (Year) -> 5 Process Stages
# ==============================================================================

import os
import sqlite3
import hashlib
import json
import logging
from datetime import datetime

logger = logging.getLogger("precision_palm.database_engine")

DB_PATH = os.path.join(os.path.dirname(__file__), "precision_palm.db")

def get_db_connection():
    """
    Membuka koneksi SQLite dengan mode Write-Ahead Logging (WAL)
    dan mengaktifkan penegakan Foreign Key Constraints secara mutlak.
    """
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def initialize_pure_relational_schema():
    """
    Mendirikan 9 tabel relasional terstruktur dengan penegakan hierarki 4-tingkat.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Tabel Master Perusahaan (Multi-Tenancy Corporate)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            legal_entity_type TEXT NOT NULL CHECK(legal_entity_type IN ('PT_CORPORATE', 'KOPERASI_PLASMA', 'PEKEBUN_SWADAYA')),
            tax_identification_npwp TEXT NOT NULL,
            pic_name TEXT NOT NULL,
            pic_contact_email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Tabel Bidang Lahan / Kebun Konsesi (Estates)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS estates (
            estate_id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            estate_name TEXT NOT NULL,
            legal_title_type TEXT NOT NULL CHECK(legal_title_type IN ('HGU', 'SHM', 'E_STDB')),
            legal_deed_number TEXT NOT NULL,
            tax_nop_pbb TEXT NOT NULL,
            certified_area_ha REAL NOT NULL CHECK(certified_area_ha > 0),
            planting_pattern TEXT DEFAULT 'SEGITIGA_9M',
            centroid_lat REAL NOT NULL,
            centroid_lng REAL NOT NULL,
            boundary_geojson TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
        );
        """)

        # 3. Tabel Berkas Tahunan Konsesi (Dossiers per Audit Year)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dossiers (
            dossier_id TEXT PRIMARY KEY, -- Format: {estate_id}-{audit_year}
            estate_id TEXT NOT NULL,
            company_id TEXT NOT NULL,
            audit_year INTEGER NOT NULL,
            palm_stand_age_years REAL NOT NULL,
            active_companion_crop TEXT DEFAULT 'Jahe Merah',
            status_permohonan TEXT NOT NULL CHECK(status_permohonan IN ('DRAFT', 'SPATIAL_CLEARED', 'PROVISIONAL_ISSUED', 'VERIFIED', 'SUSPENDED')),
            current_stage TEXT NOT NULL CHECK(current_stage IN ('STAGE-0-ANNUAL-REG', 'STAGE-1-Q1', 'STAGE-2-Q2', 'STAGE-3-Q3', 'STAGE-4-Q4')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE,
            FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
        );
        """)

        # 4. Tabel Bukti Inspeksi Multi-Foto Berdasarkan Tahap Proses (inspection_evidence)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspection_evidence (
            evidence_id TEXT PRIMARY KEY, -- Format: EV-{estate_id}-{year}-{process_stage}-{seq}
            dossier_id TEXT NOT NULL,
            estate_id TEXT NOT NULL,
            company_id TEXT NOT NULL,
            audit_year INTEGER NOT NULL,
            process_stage TEXT NOT NULL CHECK(process_stage IN ('STAGE-0-ANNUAL-REG', 'STAGE-1-Q1', 'STAGE-2-Q2', 'STAGE-3-Q3', 'STAGE-4-Q4')),
            perspective_mode TEXT NOT NULL CHECK(perspective_mode IN ('AERIAL_DRONE', 'TERRESTRIAL_IN_SITU')),
            altitude_agl_m REAL NOT NULL,
            camera_pitch_degrees REAL NOT NULL,
            latitude_exif REAL NOT NULL,
            longitude_exif REAL NOT NULL,
            image_raw_base64 TEXT NOT NULL,
            image_gcs_url TEXT,
            image_sha256_hash TEXT UNIQUE NOT NULL,
            ai_vision_model TEXT DEFAULT 'gemini-3.8-flash',
            detected_entities_json TEXT NOT NULL,
            chlorophyll_spad_inferred REAL,
            root_clearance_verified_m REAL NOT NULL CHECK(root_clearance_verified_m >= 2.0),
            auditor_verdict TEXT DEFAULT 'VERIFIED_COMPLIANT',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(dossier_id) ON DELETE CASCADE,
            FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
        );
        """)

        # 5. Tabel Telemetri Penginderaan Jauh Satelit (spatial_telemetry)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS spatial_telemetry (
            telemetry_id TEXT PRIMARY KEY,
            dossier_id TEXT NOT NULL,
            audit_year INTEGER NOT NULL,
            sentinel2_ndvi_mean REAL NOT NULL,
            sentinel2_ndmi_moisture REAL NOT NULL,
            srtm_slope_degrees REAL NOT NULL,
            srtm_elevation_asl_m REAL NOT NULL,
            hansen_loss_post2020_ha REAL NOT NULL DEFAULT 0.00,
            pippib_moratorium_distance_m REAL NOT NULL,
            watercourse_proximity_m REAL NOT NULL,
            soil_taxonomy_type TEXT NOT NULL,
            soil_ph REAL NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(dossier_id) ON DELETE CASCADE
        );
        """)

        # 6. Tabel Registri Pencegahan Manipulasi Foto (used_photo_hashes)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS used_photo_hashes (
            sha256_hash TEXT PRIMARY KEY,
            evidence_id TEXT NOT NULL,
            dossier_id TEXT NOT NULL,
            company_id TEXT NOT NULL,
            first_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 7. Tabel Surveilans Mandor Lapangan (field_surveillance_records)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_surveillance_records (
            record_id TEXT PRIMARY KEY,
            dossier_id TEXT NOT NULL,
            estate_id TEXT NOT NULL,
            audit_year INTEGER NOT NULL,
            process_stage TEXT NOT NULL CHECK(process_stage IN ('STAGE-0-ANNUAL-REG', 'STAGE-1-Q1', 'STAGE-2-Q2', 'STAGE-3-Q3', 'STAGE-4-Q4')),
            mandor_name TEXT NOT NULL,
            block_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            elevation_m REAL NOT NULL,
            slope_deg REAL NOT NULL,
            soil_ph REAL NOT NULL,
            weather_condition TEXT NOT NULL,
            evidence_id TEXT,
            sha256_seal TEXT NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(dossier_id) ON DELETE CASCADE,
            FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
        );
        """)

        # 8. Tabel Log Audit Aktivitas Sistem (system_audit_logs)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_audit_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dossier_id TEXT NOT NULL,
            actor_identity TEXT NOT NULL,
            action_type TEXT NOT NULL,
            ip_address TEXT,
            payload_snapshot TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 9. Tabel Sertifikasi & Paspor Ekspor (certification_audits)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS certification_audits (
            audit_id TEXT PRIMARY KEY,
            dossier_id TEXT UNIQUE NOT NULL,
            audit_year INTEGER NOT NULL,
            final_verdict TEXT NOT NULL CHECK(final_verdict IN ('APPROVED_CERTIFIED', 'PROVISIONAL_PERMIT', 'REJECTED')),
            eudr_traces_nt_dds_json TEXT NOT NULL,
            certified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(dossier_id) ON DELETE CASCADE
        );
        """)

        # Indeks Pencarian Integritas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dossier_estate ON dossiers(estate_id, audit_year);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_stage ON inspection_evidence(dossier_id, process_stage);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_surv_stage ON field_surveillance_records(dossier_id, process_stage);")

        conn.commit()
        logger.info("[OK] Skema relasional 4-tingkat berhasil ditegakkan tanpa duplikasi.")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"[ERR] Gagal mendirikan skema: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    print("[*] Inisialisasi Skema Relasional Hierarkis...")
    initialize_pure_relational_schema()
    print("[OK] Sistem Basis Data Murni Telah Dikonfigurasi.")
```eof

```markdown:docs/perintah_eksekusi_ag_spatial_lifecycle.md
# INSTRUKSI EKSEKUSI RESMI UNTUK AG: INTEGRASI PENANDA SIKLUS & KETAHANAN DATA REFRESH PADA HALAMAN SPASIAL

**Perihal:** Pembaruan Endpoint Backend di `app.py` agar Menyimpan Bukti Foto & Log Survei Terikat pada Identitas Kebun (`estate_id`) dan Tahun Audit (`audit_year`).

---

## 🛠️ ENDPOINT DI `app.py`:

Pastikan endpoint `/api/spatial/estate-data` dan `/api/media/evidence/list` mendukung parameter `kode` dan `year`:

```python
@app.route('/api/spatial/estate-data', methods=['GET'])
def api_spatial_estate_data():
    kode = request.args.get('kode', 'EST-MDN-001')
    year = int(request.args.get('year', 2026))
    dossier_id = f"{kode}-{year}"
    
    try:
        from database_schema_engine import get_db_connection
        conn = get_db_connection()
        
        # 1. Ambil data lahan
        estate = conn.execute("""
            SELECT e.*, c.company_name
            FROM estates e
            JOIN companies c ON e.company_id = c.company_id
            WHERE e.estate_id = ?;
        """, (kode,)).fetchone()
        
        # 2. Ambil bukti foto terikat pada dossier tahun berjalan
        photos = conn.execute("""
            SELECT evidence_id, process_stage, perspective_mode, image_gcs_url,
                   image_raw_base64, detected_entities_json, uploaded_at
            FROM inspection_evidence
            WHERE dossier_id = ?
            ORDER BY uploaded_at DESC;
        """, (dossier_id,)).fetchall()
        
        # 3. Ambil log survei mandor
        surveys = conn.execute("""
            SELECT * FROM field_surveillance_records
            WHERE dossier_id = ?
            ORDER BY recorded_at DESC;
        """, (dossier_id,)).fetchall()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "estate": dict(estate) if estate else None,
            "photos": [dict(p) for p in photos],
            "surveys": [dict(s) for s in surveys]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500