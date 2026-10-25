# ==============================================================================
# Precision Palm - Enterprise Relational Database Engine (SQLite WAL & BigQuery)
# Auto-Seeder Disabled for Diagnostic Proof Testing
# ==============================================================================

import os
import sqlite3
import hashlib
import json
import logging

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
    _ensure_inspection_evidence_process_stage(conn)
    return conn

def _ensure_inspection_evidence_process_stage(conn):
    table_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'inspection_evidence';"
    ).fetchone()
    if not table_exists:
        return

    columns = {row[1] for row in conn.execute("PRAGMA table_info(inspection_evidence);")}
    if "process_stage" in columns:
        return

    try:
        conn.execute(
            "ALTER TABLE inspection_evidence ADD COLUMN process_stage TEXT DEFAULT 'STAGE_3';"
        )
        conn.commit()
    except sqlite3.OperationalError:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(inspection_evidence);")}
        if "process_stage" not in columns:
            raise

def initialize_pure_relational_schema():
    """
    Mendirikan 9 tabel relasional terstruktur tanpa ada fallback hardcoded.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Tabel Master Perusahaan (Multi-Tenancy Root)
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

        # 2. Tabel Berkas Konsesi & Konsep Tahun (dossiers)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dossiers (
            dossier_id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            audit_year INTEGER NOT NULL,
            estate_block_name TEXT NOT NULL,
            legal_title_type TEXT NOT NULL CHECK(legal_title_type IN ('HGU', 'SHM', 'E_STDB')),
            legal_deed_number TEXT NOT NULL,
            tax_nop_pbb TEXT NOT NULL,
            certified_area_ha REAL NOT NULL CHECK(certified_area_ha > 0),
            palm_stand_age_years REAL NOT NULL,
            planting_pattern TEXT DEFAULT 'SEGITIGA_9M',
            centroid_lat REAL NOT NULL,
            centroid_lng REAL NOT NULL,
            boundary_geojson TEXT NOT NULL,
            status_permohonan TEXT NOT NULL CHECK(status_permohonan IN ('DRAFT', 'SPATIAL_CLEARED', 'PROVISIONAL_ISSUED', 'VERIFIED', 'SUSPENDED')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
        );
        """)

        # 3. Tabel Mandor Lapangan (field_mandors)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_mandors (
            mandor_id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            full_name TEXT NOT NULL,
            nik_ktp TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            assigned_block_id TEXT NOT NULL,
            device_hardware_uuid TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
        );
        """)

        # 4. Tabel Telemetri Penginderaan Jauh Satelit (spatial_telemetry)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS spatial_telemetry (
            telemetry_id TEXT PRIMARY KEY,
            dossier_id TEXT NOT NULL,
            audit_year INTEGER NOT NULL,
            sentinel2_ndvi_mean REAL NOT NULL,
            sentinel2_ndmi_moisture REAL NOT NULL,
            srtm_slope_degrees REAL NOT NULL CHECK(srtm_slope_degrees <= 15.0),
            srtm_elevation_asl_m REAL NOT NULL,
            hansen_loss_post2020_ha REAL NOT NULL DEFAULT 0.00,
            pippib_moratorium_distance_m REAL NOT NULL CHECK(pippib_moratorium_distance_m >= 50.0),
            watercourse_proximity_m REAL NOT NULL,
            soil_taxonomy_type TEXT NOT NULL,
            soil_ph REAL NOT NULL,
            gee_cloud_mask_pct REAL NOT NULL,
            raw_spectral_json TEXT NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(dossier_id) ON DELETE CASCADE
        );
        """)

        # 5. Tabel Bukti Inspeksi Multi-Foto Murni (inspection_evidence)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspection_evidence (
            evidence_id TEXT PRIMARY KEY,
            dossier_id TEXT NOT NULL,
            mandor_id TEXT NOT NULL,
            audit_year INTEGER NOT NULL,
            quarter_cycle TEXT NOT NULL CHECK(quarter_cycle IN ('Q1', 'Q2', 'Q3', 'Q4')),
            process_stage TEXT DEFAULT 'STAGE_3' CHECK(process_stage IN (
                'STAGE_3',
                'STAGE-0-ANNUAL-REG',
                'STAGE-1-Q1', 'STAGE-1-Q2', 'STAGE-1-Q3', 'STAGE-1-Q4',
                'STAGE-2-Q2', 'STAGE-3-Q3', 'STAGE-4-Q4'
            )),
            perspective_mode TEXT NOT NULL CHECK(perspective_mode IN ('AERIAL_DRONE', 'TERRESTRIAL_IN_SITU')),
            altitude_agl_m REAL NOT NULL,
            camera_pitch_degrees REAL NOT NULL,
            latitude_exif REAL NOT NULL,
            longitude_exif REAL NOT NULL,
            image_raw_base64 TEXT NOT NULL,
            image_sha256_hash TEXT UNIQUE NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            ai_vision_model TEXT DEFAULT 'gemini-3.8-flash',
            detected_entities_json TEXT NOT NULL,
            chlorophyll_spad_inferred REAL,
            root_clearance_verified_m REAL NOT NULL CHECK(root_clearance_verified_m >= 2.0),
            weather_satellite_validation TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(dossier_id) ON DELETE CASCADE,
            FOREIGN KEY (mandor_id) REFERENCES field_mandors(mandor_id)
        );
        """)

        # 6. Spatial field-surveillance ledger used by the Stage 2A Save action.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_surveillance_records (
            record_id TEXT PRIMARY KEY,
            id_log TEXT,
            dossier_id TEXT NOT NULL,
            kode_kebun TEXT,
            estate_id TEXT,
            audit_year INTEGER NOT NULL DEFAULT 2026,
            process_stage TEXT DEFAULT 'STAGE_3',
            periode_siklus TEXT,
            mandor_name TEXT,
            block_id TEXT,
            latitude REAL,
            longitude REAL,
            elevation_m REAL,
            slope_deg REAL,
            soil_ph REAL,
            weather_condition TEXT,
            evidence_id TEXT,
            foto_url TEXT,
            detected_entities_json TEXT,
            sha256_seal TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        surveillance_columns = {
            "record_id": "TEXT",
            "id_log": "TEXT",
            "dossier_id": "TEXT",
            "kode_kebun": "TEXT",
            "estate_id": "TEXT",
            "audit_year": "INTEGER DEFAULT 2026",
            "process_stage": "TEXT DEFAULT 'STAGE_3'",
            "periode_siklus": "TEXT",
            "mandor_name": "TEXT",
            "block_id": "TEXT",
            "latitude": "REAL",
            "longitude": "REAL",
            "elevation_m": "REAL",
            "slope_deg": "REAL",
            "soil_ph": "REAL",
            "weather_condition": "TEXT",
            "evidence_id": "TEXT",
            "foto_url": "TEXT",
            "detected_entities_json": "TEXT",
            "sha256_seal": "TEXT",
            "recorded_at": "TIMESTAMP",
        }
        cursor.execute("PRAGMA table_info(field_surveillance_records);")
        existing_surveillance_columns = {row[1] for row in cursor.fetchall()}
        for column_name, column_definition in surveillance_columns.items():
            if column_name not in existing_surveillance_columns:
                cursor.execute(
                    "ALTER TABLE field_surveillance_records "
                    f"ADD COLUMN {column_name} {column_definition};"
                )
        cursor.execute("""
            UPDATE field_surveillance_records
            SET record_id = COALESCE(record_id, id_log, 'SURV-LEGACY-' || rowid),
                dossier_id = COALESCE(dossier_id, kode_kebun, estate_id, 'EST-MDN-001'),
                recorded_at = COALESCE(recorded_at, CURRENT_TIMESTAMP)
            WHERE record_id IS NULL OR dossier_id IS NULL OR recorded_at IS NULL;
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_surveillance_dossier_recorded "
            "ON field_surveillance_records(dossier_id, recorded_at DESC);"
        )

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

        # 7. Tabel Simulasi Biofisika & Ekonomi TBS (in_silico_simulations)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS in_silico_simulations (
            simulation_id TEXT PRIMARY KEY,
            dossier_id TEXT NOT NULL,
            audit_year INTEGER NOT NULL,
            lai_canopy_value REAL NOT NULL,
            par_transmittance_pct REAL NOT NULL,
            net_corridor_width_m REAL NOT NULL,
            companion_crop_selected TEXT NOT NULL,
            companion_harvest_ton_ha REAL NOT NULL,
            land_equivalent_ratio REAL NOT NULL CHECK(land_equivalent_ratio >= 1.0),
            percentage_land_saved REAL NOT NULL,
            palm_yield_deficit_pct REAL NOT NULL CHECK(palm_yield_deficit_pct <= 4.5),
            compensatory_mop_kg_ha REAL NOT NULL,
            cpo_global_usd_mt REAL NOT NULL,
            kurs_usd_idr REAL NOT NULL,
            tbs_price_per_kg_idr REAL NOT NULL,
            tbs_price_per_ton_idr REAL NOT NULL,
            total_combined_revenue_idr REAL NOT NULL,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(dossier_id) ON DELETE CASCADE
        );
        """)

        # 8. Tabel Sertifikasi & Keputusan Sidang Asesor (certification_audits)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS certification_audits (
            audit_id TEXT PRIMARY KEY,
            dossier_id TEXT UNIQUE NOT NULL,
            audit_year INTEGER NOT NULL,
            lead_assessor_name TEXT NOT NULL,
            assessor_registration_no TEXT NOT NULL,
            final_verdict TEXT NOT NULL CHECK(final_verdict IN ('APPROVED_CERTIFIED', 'PROVISIONAL_PERMIT', 'REJECTED')),
            sla_180d_countdown_expiry TIMESTAMP NOT NULL,
            immutable_dossier_sha256 TEXT NOT NULL,
            eudr_traces_nt_dds_json TEXT NOT NULL,
            public_validation_qr_url TEXT NOT NULL,
            certified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(dossier_id) ON DELETE CASCADE
        );
        """)

        # 9. Tabel Log Audit Aktivitas Sistem (system_audit_logs)
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

        # Indeks Pencarian Cepat & Pagination
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dossier_company ON dossiers(company_id, audit_year);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_dossier_q ON inspection_evidence(dossier_id, quarter_cycle, audit_year);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_dossier ON spatial_telemetry(dossier_id, audit_year);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sim_dossier ON in_silico_simulations(dossier_id, audit_year);")

        conn.commit()
        logger.info("[OK] Seluruh 9 tabel basis data murni berhasil didirikan TANPA AUTO-SEEDING.")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"[ERR] Gagal mendirikan skema relasional: {e}")
        raise e
    finally:
        conn.close()

def get_dossier_by_id(dossier_id, audit_year=2026):
    """
    Mengambil data dossier berdasarkan dossier_id dan audit_year.
    """
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM dossiers WHERE dossier_id = ? AND audit_year = ?;", (dossier_id, audit_year)).fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"[ERR] get_dossier_by_id error: {e}")
        return None
    finally:
        conn.close()

def get_latest_evidence(dossier_id, audit_year=2026, perspective=None):
    """
    Mengambil bukti inspeksi terbaru untuk dossier tertentu.
    """
    conn = get_db_connection()
    try:
        if perspective:
            row = conn.execute(
                "SELECT * FROM inspection_evidence WHERE dossier_id = ? AND audit_year = ? AND perspective_mode = ? ORDER BY uploaded_at DESC LIMIT 1;",
                (dossier_id, audit_year, perspective)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM inspection_evidence WHERE dossier_id = ? AND audit_year = ? ORDER BY uploaded_at DESC LIMIT 1;",
                (dossier_id, audit_year)
            ).fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"[ERR] get_latest_evidence error: {e}")
        return None
    finally:
        conn.close()

def is_photo_hash_reused(image_sha256_hash):
    """
    Memeriksa apakah hash SHA-256 foto sudah pernah dipakai sebelumnya (anti-reuse).
    """
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM inspection_evidence WHERE image_sha256_hash = ? LIMIT 1;",
            (image_sha256_hash,)
        ).fetchone()
        return bool(row)
    except Exception as e:
        logger.error(f"[ERR] is_photo_hash_reused error: {e}")
        return False
    finally:
        conn.close()

def seed_formal_test_data():
    """
    AUTO-SEEDER DIMATIKAN UNTUK DIAGNOSIS.
    """
    logger.info("[INFO] Auto-Seeder dinonaktifkan sesuai permintaan diagnosis.")
    pass

if __name__ == "__main__":
    print("[*] Menginisialisasi Skema Basis Data Murni (Tanpa Seeder)...")
    initialize_pure_relational_schema()
    print("[OK] Selesai. Silakan uji hapus file database lokal.")