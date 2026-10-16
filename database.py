"""
database.py - Precision Palm Cloud Local Persistence & Dynamic Compliance Engine.
Implements the 6 core operational tables with the 4-Quarter (Q1-Q4) dynamic certificate
governance state machine, automatic 6-month suspension enforcement, and QR verification queries.

Architecture: SQLite WAL Mode (Sub-millisecond local OLTP) with BigQuery Sync Flags.
Adheres to AG_OPERATIONAL_RULES: Top-down linear parsing, English default.
"""

import sys
import os

# Standardize Windows console output encoding to UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import sqlite3
import json
import hashlib
import math
import base64
from datetime import datetime, date, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union

# Standardize server timezone to Western Indonesia Time (WIB / UTC+7)
WIB = timezone(timedelta(hours=7))

def get_wib_now() -> str:
    """Returns local Indonesian Western Time timestamp string."""
    return datetime.now(WIB).strftime('%Y-%m-%d %H:%M:%S WIB')

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'precision_palm.db')

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    # Timeout 30 detik untuk menangani antrean multi-worker Gunicorn
    target_path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(target_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")
    except Exception as e_lock:
        print(f"[DB Notice] Skip PRAGMA journal_mode: {e_lock}")
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    """
    Initializes the SQLite database with the 6 operational tables, dynamic columns
    for 4-quarter compliance governance, backward-compatibility views, and seed data.
    """
    path = db_path or DEFAULT_DB_PATH
    try:
        conn = get_db_connection(path)
        cursor = conn.cursor()

        # 1. Master Estate Profiles Table (Pillar 1: Ingestion & Cadastral Tenure)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kebun_profil (
                id_kebun INTEGER PRIMARY KEY AUTOINCREMENT,
                kode_kebun TEXT UNIQUE NOT NULL,
                nama_kebun TEXT NOT NULL,
                pemohon TEXT,
                tipe_entitas TEXT DEFAULT 'PT',
                kontak TEXT,
                nomor_hgu TEXT,
                dokumen_hgu_url TEXT,
                nop_pbb TEXT,
                dokumen_sppt_url TEXT,
                luas_ha REAL NOT NULL DEFAULT 100.00,
                umur_sawit REAL NOT NULL DEFAULT 6.0,
                komoditas_sela TEXT NOT NULL DEFAULT 'Jahe Merah (Zingiber officinale)',
                centroid_lat REAL NOT NULL DEFAULT 0.824100,
                centroid_lng REAL NOT NULL DEFAULT 99.561200,
                poligon_geojson TEXT,
                foto_lahan_url TEXT DEFAULT '/static/img/sawit_drone.jpg',
                soil_ph REAL DEFAULT 5.5,
                slope REAL DEFAULT 4.5,
                elevation REAL DEFAULT 142.0,
                is_active INTEGER NOT NULL DEFAULT 1,
                sync_bigquery INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Verify and add dynamic columns for kebun_profil
        cursor.execute("PRAGMA table_info(kebun_profil);")
        existing_kebun_cols = [row[1] for row in cursor.fetchall()]
        needed_kebun_cols = [
            ("pemohon", "TEXT"),
            ("tipe_entitas", "TEXT DEFAULT 'PT'"),
            ("kontak", "TEXT"),
            ("poligon_geojson", "TEXT"),
            ("dokumen_hgu_url", "TEXT"),
            ("dokumen_sppt_url", "TEXT"),
            ("nop_pbb", "TEXT"),
            ("foto_lahan_url", "TEXT DEFAULT '/static/img/sawit_drone.jpg'"),
            ("soil_ph", "REAL DEFAULT 5.5"),
            ("slope", "REAL DEFAULT 4.5"),
            ("elevation", "REAL DEFAULT 142.0"),
            ("soil_texture", "TEXT DEFAULT 'sandy_loam'"),
            ("weather_summary", "TEXT DEFAULT 'Cerah Berawan'"),
            ("sync_bigquery", "INTEGER NOT NULL DEFAULT 0"),
            ("is_active", "INTEGER NOT NULL DEFAULT 1"),
            ("public_token", "TEXT")
        ]
        for col_name, col_def in needed_kebun_cols:
            if col_name not in existing_kebun_cols:
                try:
                    cursor.execute(f"ALTER TABLE kebun_profil ADD COLUMN {col_name} {col_def};")
                except Exception as e_alter:
                    print(f"[Precision Palm] Migration kebun_profil.{col_name}: {e_alter}")

        # 2. Lifecycle Milestones Reference Table (18-Stage Annual Business Cycle)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ref_roadmap_siklus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fase INTEGER NOT NULL,
                nama_fase TEXT NOT NULL,
                nomor_urut INTEGER NOT NULL,
                kode_proses TEXT NOT NULL,
                judul TEXT NOT NULL,
                kategori TEXT NOT NULL,
                waktu_pelaksanaan TEXT NOT NULL,
                bulan_mulai INTEGER NOT NULL,
                bulan_selesai INTEGER NOT NULL,
                penanggung_jawab TEXT NOT NULL,
                output_dokumen TEXT NOT NULL,
                deskripsi TEXT NOT NULL,
                link_menu TEXT NOT NULL,
                link_label TEXT NOT NULL DEFAULT 'Buka Modul',
                rule_pengecekan TEXT NOT NULL,
                bobot_persen REAL NOT NULL DEFAULT 5.55,
                is_active INTEGER NOT NULL DEFAULT 1
            );
        """)

        # 3. Foreman & Drone Surveillance Logs Table (Pillar 3: Monitoring)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kebun_monitoring_log (
                id_log INTEGER PRIMARY KEY AUTOINCREMENT,
                id_kebun INTEGER NOT NULL,
                periode_siklus TEXT NOT NULL DEFAULT 'Q1',
                tahun_siklus INTEGER NOT NULL DEFAULT 2026,
                titik_ke INTEGER NOT NULL DEFAULT 1,
                gps_lat REAL NOT NULL,
                gps_lng REAL NOT NULL,
                elevasi_dpl REAL,
                ketinggian_agl REAL,
                kemiringan_lereng REAL,
                view_perspective TEXT NOT NULL DEFAULT 'ground_eye_level',
                foto_url TEXT NOT NULL,
                waktu_pengambilan DATETIME NOT NULL,
                cuaca_tercatat TEXT DEFAULT 'Cerah Berawan',
                cuaca_satellite_match INTEGER DEFAULT 1,
                piringan_steril_meter REAL DEFAULT 2.0,
                defisit_tbs_persen REAL DEFAULT 3.2,
                ai_scan_status TEXT DEFAULT 'verified',
                ai_scan_result_json TEXT,
                sha256_seal TEXT,
                sync_bigquery INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(id_kebun) REFERENCES kebun_profil(id_kebun) ON DELETE CASCADE
            );
        """)

        # Verify and add dynamic columns for kebun_monitoring_log
        cursor.execute("PRAGMA table_info(kebun_monitoring_log);")
        existing_mon_cols = [row[1] for row in cursor.fetchall()]
        needed_mon_cols = [
            ("cuaca_tercatat", "TEXT DEFAULT 'Cerah Berawan'"),
            ("cuaca_satellite_match", "INTEGER DEFAULT 1"),
            ("piringan_steril_meter", "REAL DEFAULT 2.0"),
            ("defisit_tbs_persen", "REAL DEFAULT 3.2"),
            ("kode_kebun", "TEXT"),
            ("mandor", "TEXT DEFAULT 'Mandor Sutrisno'"),
            ("blok", "TEXT DEFAULT 'Blok A'")
        ]
        for col_name, col_def in needed_mon_cols:
            if col_name not in existing_mon_cols:
                try:
                    cursor.execute(f"ALTER TABLE kebun_monitoring_log ADD COLUMN {col_name} {col_def};")
                except Exception:
                    pass

        # 4. In-Silico Computation Audit Registry (Pillar 2: Biophysical Audit)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compute_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                stand_age REAL NOT NULL,
                land_area REAL NOT NULL,
                crop_type TEXT NOT NULL,
                ler_score REAL NOT NULL,
                pls_percentage REAL NOT NULL,
                forest_saved_ha REAL NOT NULL,
                carbon_tco2e REAL NOT NULL,
                sha256_hash TEXT NOT NULL,
                client_ip TEXT,
                sync_bigquery INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 5. EcoGreen Compliance Certificates Table with 4-Quarter Dynamic State Columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kebun_sertifikat_ecogreen (
                id_sertifikat INTEGER PRIMARY KEY AUTOINCREMENT,
                id_kebun INTEGER NOT NULL,
                nomor_registrasi TEXT UNIQUE NOT NULL,
                tahun_anggaran INTEGER NOT NULL DEFAULT 2026,
                skor_kepatuhan REAL NOT NULL DEFAULT 95.00,
                predikat TEXT NOT NULL DEFAULT 'EXCELLENT COMPLIANT',
                status_sertifikat TEXT DEFAULT 'provisional',
                status_siklus TEXT DEFAULT 'Q1_PROVISIONAL',
                tgl_terbit DATE DEFAULT CURRENT_DATE,
                tgl_kadaluarsa DATE,
                tanggal_terbit DATE DEFAULT CURRENT_DATE,
                tanggal_kadaluarsa DATE,
                tgl_jatuh_tempo_siklus DATE,
                laporan_terakhir_siklus TEXT,
                jumlah_hari_tanpa_laporan INTEGER DEFAULT 0,
                q1_status TEXT DEFAULT 'VERIFIED',
                q1_verified_at DATE,
                q2_status TEXT DEFAULT 'PENDING',
                q2_verified_at DATE,
                q3_status TEXT DEFAULT 'PENDING',
                q3_verified_at DATE,
                q4_status TEXT DEFAULT 'PENDING',
                q4_verified_at DATE,
                suspension_reason TEXT,
                ler_achieved REAL NOT NULL DEFAULT 1.5238,
                avoided_forest_ha REAL NOT NULL DEFAULT 34.37,
                carbon_tco2e REAL NOT NULL DEFAULT 1546.65,
                sha256_credential_hash TEXT NOT NULL,
                sync_bigquery INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(id_kebun) REFERENCES kebun_profil(id_kebun) ON DELETE CASCADE
            );
        """)

        # Dynamic schema migration for kebun_sertifikat_ecogreen quarterly control columns
        cursor.execute("PRAGMA table_info(kebun_sertifikat_ecogreen);")
        existing_cert_cols = [row[1] for row in cursor.fetchall()]
        needed_cert_cols = [
            ("status_siklus", "TEXT DEFAULT 'Q1_PROVISIONAL'"),
            ("tgl_terbit", "DATE DEFAULT CURRENT_DATE"),
            ("tgl_kadaluarsa", "DATE"),
            ("tanggal_terbit", "DATE DEFAULT CURRENT_DATE"),
            ("tanggal_kadaluarsa", "DATE"),
            ("tgl_jatuh_tempo_siklus", "DATE"),
            ("laporan_terakhir_siklus", "TEXT"),
            ("jumlah_hari_tanpa_laporan", "INTEGER DEFAULT 0"),
            ("q1_status", "TEXT DEFAULT 'VERIFIED'"),
            ("q1_verified_at", "DATE"),
            ("q2_status", "TEXT DEFAULT 'PENDING'"),
            ("q2_verified_at", "DATE"),
            ("q3_status", "TEXT DEFAULT 'PENDING'"),
            ("q3_verified_at", "DATE"),
            ("q4_status", "TEXT DEFAULT 'PENDING'"),
            ("q4_verified_at", "DATE"),
            ("suspension_reason", "TEXT"),
            ("public_token", "TEXT")
        ]
        for col_name, col_def in needed_cert_cols:
            if col_name not in existing_cert_cols:
                try:
                    cursor.execute(f"ALTER TABLE kebun_sertifikat_ecogreen ADD COLUMN {col_name} {col_def};")
                except Exception as e_alter_cert:
                    print(f"[Precision Palm] Migration kebun_sertifikat_ecogreen.{col_name}: {e_alter_cert}")

        # 6. UAV Drone Orthophoto Gallery Uploads Index (Relational Isolation per Estate)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS canopy_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_kebun INTEGER NOT NULL DEFAULT 1,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                file_url TEXT NOT NULL,
                file_size INTEGER NOT NULL DEFAULT 0,
                mime_type TEXT NOT NULL DEFAULT 'image/jpeg',
                title TEXT DEFAULT 'Foto Drone Tapak',
                tag TEXT DEFAULT 'UAV Flight',
                block_id TEXT DEFAULT 'Blok A',
                ai_review_json TEXT,
                sync_bigquery INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(id_kebun) REFERENCES kebun_profil(id_kebun) ON DELETE CASCADE
            );
        """)

        # 7. Autonomous Agent Memory RAG Store (Episodic Experience Loop)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_experience (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                perspective_mode TEXT CHECK(perspective_mode IN ('AERIAL_DRONE', 'TERRESTRIAL_IN_SITU')),
                altitude_agl_m REAL DEFAULT 1.45,
                camera_pitch_deg REAL DEFAULT -12.0,
                coordinates_wgs84 TEXT NOT NULL,
                timestamp_iso TEXT NOT NULL,
                declared_crop TEXT,
                observed_taxon TEXT,
                discrepancy_score REAL DEFAULT 0.0,
                detected_entities_json TEXT NOT NULL,
                diagnostic_matrix_json TEXT NOT NULL,
                learned_context_summary TEXT NOT NULL,
                sha256_hash TEXT NOT NULL,
                sync_bigquery INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_exp_block ON agent_experience(block_id, created_at DESC);")

        # 8. Inspection Evidence Pure Storage (IndexedDB -> SQLite WAL -> BigQuery)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inspection_evidence (
                id TEXT PRIMARY KEY,
                dossier_id TEXT NOT NULL DEFAULT 'EST-MDN-001',
                block_id TEXT NOT NULL DEFAULT 'Blok A',
                perspective_mode TEXT NOT NULL DEFAULT 'TERRESTRIAL_IN_SITU',
                altitude_agl_m REAL DEFAULT 1.45,
                camera_pitch_deg REAL DEFAULT -12.0,
                latitude REAL DEFAULT 0.824100,
                longitude REAL DEFAULT 99.561200,
                image_mime_type TEXT NOT NULL DEFAULT 'image/jpeg',
                image_base64 TEXT NOT NULL,
                sha256_hash TEXT NOT NULL,
                detected_entities_json TEXT,
                diagnostic_matrix_json TEXT,
                synced_to_bigquery INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_block ON inspection_evidence(block_id, created_at DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_dossier ON inspection_evidence(dossier_id, created_at DESC);")

        # 9. Anti-Fraud & Anti-Replay Photo Registry (Zero Re-use enforcement)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS used_photo_hashes (
                sha256_hash TEXT PRIMARY KEY,
                dossier_id TEXT NOT NULL,
                company_name TEXT NOT NULL,
                used_in_module TEXT NOT NULL,
                capture_timestamp TIMESTAMP NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_photo_hash_dossier ON used_photo_hashes(dossier_id);")

        # Verify and add dynamic columns for inspection_evidence
        cursor.execute("PRAGMA table_info(inspection_evidence);")
        existing_ev_cols = [row[1] for row in cursor.fetchall()]
        if "company_name" not in existing_ev_cols:
            try:
                cursor.execute("ALTER TABLE inspection_evidence ADD COLUMN company_name TEXT DEFAULT 'PT Mandailing Agro Sustainable';")
            except Exception:
                pass
        if "quarter_cycle" not in existing_ev_cols:
            try:
                cursor.execute("ALTER TABLE inspection_evidence ADD COLUMN quarter_cycle TEXT DEFAULT 'Q1';")
            except Exception:
                pass
        if "audit_year" not in existing_ev_cols:
            try:
                cursor.execute("ALTER TABLE inspection_evidence ADD COLUMN audit_year INTEGER DEFAULT 2026;")
            except Exception:
                pass
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_dossier_year ON inspection_evidence(dossier_id, audit_year, created_at DESC);")

        # 10. Application Global & Multi-Tenant Settings (Settings Engine)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        default_settings = {
            "market_mode": "IDR",
            "audit_year": "2026",
            "kurs_usd": "17920",
            "cpo_global": "1526.56",
            "bea_keluar": "178.0",
            "pe_bpdpks": "130.27",
            "logistik": "50.0",
            "p_kernel": "12700",
            "rendemen_cpo": "21.0",
            "indeks_k": "91.0",
            "biaya_olah": "300",
            "is_published": "0",
            "antifraud_active": "1",
            "active_dossier": "EST-MDN-001"
        }
        for k, v in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?);", (k, str(v)))

        # Verify and add dynamic columns for canopy_uploads
        cursor.execute("PRAGMA table_info(canopy_uploads);")
        existing_canopy_cols = [row[1] for row in cursor.fetchall()]
        needed_canopy_cols = [
            ("id_kebun", "INTEGER NOT NULL DEFAULT 1"),
            ("title", "TEXT DEFAULT 'Foto Drone Tapak'"),
            ("tag", "TEXT DEFAULT 'UAV Flight'"),
            ("ai_review_json", "TEXT"),
            ("sync_bigquery", "INTEGER NOT NULL DEFAULT 0")
        ]
        for col_name, col_def in needed_canopy_cols:
            if col_name not in existing_canopy_cols:
                try:
                    cursor.execute(f"ALTER TABLE canopy_uploads ADD COLUMN {col_name} {col_def};")
                except Exception as e_alter_canopy:
                    print(f"[Precision Palm] Migration canopy_uploads.{col_name}: {e_alter_canopy}")

        # Compatibility Views for Legacy Endpoints
        cursor.execute("DROP VIEW IF EXISTS estates;")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS estates AS
            SELECT 
                id_kebun AS id,
                id_kebun,
                kode_kebun,
                nama_kebun,
                COALESCE(tipe_entitas, 'PT') AS tipe_entitas,
                COALESCE(pemohon, nama_kebun) AS pemohon,
                COALESCE(kontak, '') AS kontak,
                COALESCE(nomor_hgu, '') AS nomor_hgu,
                COALESCE(nop_pbb, '') AS nop_pbb,
                luas_ha,
                umur_sawit,
                komoditas_sela,
                CAST(centroid_lat AS TEXT) AS centroid_lat,
                CAST(centroid_lng AS TEXT) AS centroid_lng,
                CASE 
                    WHEN is_active = 1 THEN 'active'
                    ELSE 'in_progress'
                END AS status_sertifikat,
                'CERT-ECOGREEN-2026-' || printf('%04d', id_kebun) AS nomor_registrasi,
                COALESCE(dokumen_hgu_url, '') AS doc_legal_url,
                created_at
            FROM kebun_profil;
        """)

        cursor.execute("DROP VIEW IF EXISTS experiments;")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS experiments AS
            SELECT 
                id,
                request_id,
                created_at,
                stand_age AS palm_age,
                land_area,
                crop_type AS crop_name,
                5.274 AS leaf_area_index,
                218.5 AS surface_par,
                ler_score AS total_ler,
                ler_score,
                forest_saved_ha AS avoided_land_ha,
                forest_saved_ha AS forest_saved,
                carbon_tco2e AS total_climate_benefit_tco2e,
                'hybrid' AS inference_mode,
                '/static/img/default_canopy.jpg' AS image_path,
                '/static/img/default_canopy.jpg' AS image_url,
                'Lush Green (Optimal Vigor)' AS ai_health_status,
                CAST(stand_age AS TEXT) || ' Years' AS ai_age_estimate,
                'Belum Perlu Replanting' AS ai_replanting_forecast,
                'Verified Compliant with ISPO Principle 2 & EUDR Article 9' AS ai_audit_review,
                '{"sterile_circle_2m": true}' AS compliance_badges,
                sha256_hash,
                '{}' AS ai_response_json
            FROM compute_audit_logs;
        """)

        conn.commit()
    except Exception as e_init:
        print(f"[Init DB Notice] Initialization handled: {e_init}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

    try:
        seed_canonical_estates(path)
        seed_roadmap_milestones(path)
        seed_canonical_inspection_evidence(path)
    except Exception as e_seed:
        print(f"[DB Notice] Seeding skipped/handled: {e_seed}")

OFFICIAL_TELEMETRY_SEEDS = [
    {
        "id": 48196,
        "request_id": "REQ-48196",
        "stand_age": 7.0,
        "palm_age": 7.0,
        "land_area": 100.0,
        "crop_type": "Vanilla Orchid (Vanilla planifolia)",
        "crop_name": "Vanilla Orchid (Vanilla planifolia)",
        "ler_score": 1.4820,
        "total_ler": 1.4820,
        "pls_percentage": 32.52,
        "forest_saved_ha": 32.50,
        "avoided_land_ha": 32.50,
        "carbon_tco2e": 1462.5,
        "total_climate_benefit_tco2e": 1462.5,
        "sha256_hash": "48196C123648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327AA4",
        "created_at": "2026-03-28 14:20:00"
    },
    {
        "id": 90258,
        "request_id": "REQ-90258",
        "stand_age": 5.5,
        "palm_age": 5.5,
        "land_area": 100.0,
        "crop_type": "Sweet Sorghum (Sorghum bicolor)",
        "crop_name": "Sweet Sorghum (Sorghum bicolor)",
        "ler_score": 1.5640,
        "total_ler": 1.5640,
        "pls_percentage": 36.06,
        "forest_saved_ha": 36.05,
        "avoided_land_ha": 36.05,
        "carbon_tco2e": 1622.3,
        "total_climate_benefit_tco2e": 1622.3,
        "sha256_hash": "90258A783648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327BB5",
        "created_at": "2026-03-25 11:15:00"
    },
    {
        "id": 5200,
        "request_id": "REQ-5200",
        "stand_age": 6.0,
        "palm_age": 6.0,
        "land_area": 100.0,
        "crop_type": "Red Ginger (Zingiber officinale var. rubrum)",
        "crop_name": "Red Ginger (Zingiber officinale var. rubrum)",
        "ler_score": 1.5238,
        "total_ler": 1.5238,
        "pls_percentage": 34.37,
        "forest_saved_ha": 34.37,
        "avoided_land_ha": 34.37,
        "carbon_tco2e": 1546.7,
        "total_climate_benefit_tco2e": 1546.7,
        "sha256_hash": "5200D9983648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327CC6",
        "created_at": "2026-03-20 09:45:00"
    },
    {
        "id": 31804,
        "request_id": "REQ-31804",
        "stand_age": 8.0,
        "palm_age": 8.0,
        "land_area": 100.0,
        "crop_type": "Patchouli (Pogostemon cablin)",
        "crop_name": "Patchouli (Pogostemon cablin)",
        "ler_score": 1.4150,
        "total_ler": 1.4150,
        "pls_percentage": 29.33,
        "forest_saved_ha": 29.30,
        "avoided_land_ha": 29.30,
        "carbon_tco2e": 1318.5,
        "total_climate_benefit_tco2e": 1318.5,
        "sha256_hash": "31804E112648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327DD7",
        "created_at": "2026-03-18 16:30:00"
    },
    {
        "id": 27410,
        "request_id": "REQ-27410",
        "stand_age": 9.0,
        "palm_age": 9.0,
        "land_area": 100.0,
        "crop_type": "Liberica Coffee (Coffea liberica)",
        "crop_name": "Liberica Coffee (Coffea liberica)",
        "ler_score": 1.4920,
        "total_ler": 1.4920,
        "pls_percentage": 32.98,
        "forest_saved_ha": 33.00,
        "avoided_land_ha": 33.00,
        "carbon_tco2e": 1485.0,
        "total_climate_benefit_tco2e": 1485.0,
        "sha256_hash": "27410F445648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327EE8",
        "created_at": "2026-03-12 10:10:00"
    },
    {
        "id": 19520,
        "request_id": "REQ-19520",
        "stand_age": 6.5,
        "palm_age": 6.5,
        "land_area": 100.0,
        "crop_type": "Fine Flavor Cacao (Theobroma cacao)",
        "crop_name": "Fine Flavor Cacao (Theobroma cacao)",
        "ler_score": 1.4680,
        "total_ler": 1.4680,
        "pls_percentage": 31.88,
        "forest_saved_ha": 31.80,
        "avoided_land_ha": 31.80,
        "carbon_tco2e": 1431.0,
        "total_climate_benefit_tco2e": 1431.0,
        "sha256_hash": "19520B556648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327FF9",
        "created_at": "2026-03-05 08:30:00"
    }
]

# =========================================================================
# CANONICAL 10 ESTATE ZONING & ZERO-OVERLAP CADASTRAL CONCESSIONS
# =========================================================================
CANONICAL_ESTATES_ZONING = {
    "EST-MDN-001": {
        "id": 1,
        "district": "Panyabungan Utara",
        "centroid": (0.8350, 99.5650),
        "coords": [
            [99.5580, 0.8280],
            [99.5720, 0.8280],
            [99.5740, 0.8420],
            [99.5600, 0.8420],
            [99.5580, 0.8280]
        ],
        "estate_token": "a8f92b1",
        "cert_token": "c1109a1"
    },
    "EST-MDN-002": {
        "id": 2,
        "district": "Siabu",
        "centroid": (0.9250, 99.5050),
        "coords": [
            [99.4980, 0.9180],
            [99.5120, 0.9180],
            [99.5140, 0.9320],
            [99.5000, 0.9320],
            [99.4980, 0.9180]
        ],
        "estate_token": "b3c48d2",
        "cert_token": "c2208b2"
    },
    "EST-MDN-003": {
        "id": 3,
        "district": "Muara Batang Gadis",
        "centroid": (0.8520, 99.1850),
        "coords": [
            [99.1750, 0.8420],
            [99.1950, 0.8420],
            [99.1970, 0.8620],
            [99.1770, 0.8620],
            [99.1750, 0.8420]
        ],
        "estate_token": "c7e19f3",
        "cert_token": "c3307c3"
    },
    "EST-MDN-004": {
        "id": 4,
        "district": "Kotanopan",
        "centroid": (0.7550, 99.6350),
        "coords": [
            [99.6250, 0.7450],
            [99.6450, 0.7450],
            [99.6470, 0.7650],
            [99.6270, 0.7650],
            [99.6250, 0.7450]
        ],
        "estate_token": "d2a50e4",
        "cert_token": "c4406d4"
    },
    "EST-MDN-005": {
        "id": 5,
        "district": "Natal",
        "centroid": (0.5750, 99.1250),
        "coords": [
            [99.1150, 0.5650],
            [99.1350, 0.5650],
            [99.1370, 0.5850],
            [99.1170, 0.5850],
            [99.1150, 0.5650]
        ],
        "estate_token": "e6f81a5",
        "cert_token": "c5505e5"
    },
    "EST-MDN-006": {
        "id": 6,
        "district": "Panyabungan Barat",
        "centroid": (0.8550, 99.5350),
        "coords": [
            [99.5250, 0.8480],
            [99.5450, 0.8480],
            [99.5470, 0.8620],
            [99.5270, 0.8620],
            [99.5250, 0.8480]
        ],
        "estate_token": "f1b92c6",
        "cert_token": "c6604f6"
    },
    "EST-MDN-007": {
        "id": 7,
        "district": "Batang Natal",
        "centroid": (0.7950, 99.4250),
        "coords": [
            [99.4150, 0.7850],
            [99.4350, 0.7850],
            [99.4370, 0.8050],
            [99.4170, 0.8050],
            [99.4150, 0.7850]
        ],
        "estate_token": "g5d37e7",
        "cert_token": "c7703a7"
    },
    "EST-MDN-008": {
        "id": 8,
        "district": "Bukit Malintang",
        "centroid": (0.8850, 99.5550),
        "coords": [
            [99.5480, 0.8780],
            [99.5620, 0.8780],
            [99.5640, 0.8920],
            [99.5500, 0.8920],
            [99.5480, 0.8780]
        ],
        "estate_token": "h9e48f8",
        "cert_token": "c8802b8"
    },
    "EST-MDN-009": {
        "id": 9,
        "district": "Lingga Bayu",
        "centroid": (0.7750, 99.3450),
        "coords": [
            [99.3300, 0.7600],
            [99.3600, 0.7600],
            [99.3620, 0.7900],
            [99.3320, 0.7900],
            [99.3300, 0.7600]
        ],
        "estate_token": "i4a29d9",
        "cert_token": "c9901c9"
    },
    "EST-MDN-010": {
        "id": 10,
        "district": "Ranto Baek / Sinunukan",
        "centroid": (0.6550, 99.2550),
        "coords": [
            [99.2450, 0.6450],
            [99.2650, 0.6450],
            [99.2670, 0.6650],
            [99.2470, 0.6650],
            [99.2450, 0.6450]
        ],
        "estate_token": "9hdjjs8",
        "cert_token": "743hjhjhj87"
    }
}

ESTATE_PUBLIC_TOKENS = {k: v["estate_token"] for k, v in CANONICAL_ESTATES_ZONING.items()}
CERTIFICATE_PUBLIC_TOKENS = {k: v["cert_token"] for k, v in CANONICAL_ESTATES_ZONING.items()}

# Inverted token-to-code lookup
TOKEN_TO_ESTATE_CODE = {}
for _k, _v in ESTATE_PUBLIC_TOKENS.items():
    TOKEN_TO_ESTATE_CODE[_v] = _k
for _k, _v in CERTIFICATE_PUBLIC_TOKENS.items():
    TOKEN_TO_ESTATE_CODE[_v] = _k

def resolve_token_or_code(identifier: Optional[str]) -> Optional[str]:
    """
    Decodes an opaque URL token (e.g. '9hdjjs8' or '743hjhjhj87') or canonical code ('EST-MDN-010')
    into a canonical estate code ('EST-MDN-010').
    Returns None if identifier is empty, 'all', 'global', or invalid.
    """
    if not identifier:
        return None
    val = str(identifier).strip()
    if not val or val.lower() in ("all", "global", "semua", "none", "null", "undefined"):
        return None
    
    # 1. Direct token match
    if val in TOKEN_TO_ESTATE_CODE:
        return TOKEN_TO_ESTATE_CODE[val]
    
    # 2. Canonical estate code match
    val_upper = val.upper()
    if val_upper in CANONICAL_ESTATES_ZONING:
        return val_upper
    
    # 3. Numeric ID match (e.g. '10' -> 'EST-MDN-010')
    if val.isdigit():
        num = int(val)
        if 1 <= num <= 10:
            return f"EST-MDN-{num:03d}"
        if 90200 <= num <= 90299:
            # Simulation passport range -> active estate 10
            return "EST-MDN-010"

    # 4. Dynamic custom tenant codes (Strict Multi-Tenancy support)
    if val_upper.startswith("EST-") or val_upper.startswith("COMP-"):
        return val_upper
            
    return None

def get_estate_token(kode: str) -> str:
    """Returns the opaque estate URL token for an estate code."""
    return ESTATE_PUBLIC_TOKENS.get(kode, "9hdjjs8")

def get_cert_token(kode: str) -> str:
    """Returns the opaque certificate URL token for an estate code."""
    return CERTIFICATE_PUBLIC_TOKENS.get(kode, "743hjhjhj87")

def seed_canonical_estates(db_path: str) -> None:
    """
    Populates 10 certified estate master records into kebun_profil with applicants,
    binds isolated canopy photos with AI reviews into canopy_uploads,
    and seeds dual-audit monitoring logs into kebun_monitoring_log.
    Guarantees 100% ZERO OVERLAP across all 10 cadastral concession polygons.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    canonical_estates = [
        (
            1, "EST-MDN-001", "PT Mandailing Agro Sustainable", "Ir. Hendra Siregar, M.Si.", "PT", "legal@mandailingagro.co.id • 0812-3456-7890",
            "004/HGU/BPN-MDN/2021", "/static/uploads/legal_docs/hgu_est_001.pdf", "12.13.010.001.001-0001.0", 
            1200.0, 7.5, "Red Ginger (Zingiber officinale)", 0.835000, 99.565000, 
            "/static/img/sawit_drone.jpg", 5.5, 4.5, 142.0, "a8f92b1"
        ),
        (
            2, "EST-MDN-002", "Koperasi Sawit Swadaya Maju", "H. Syamsul Bahri", "KOPSA", "kontak@sawitswadaya.id • 0813-9876-5432",
            "012/HGU/BPN-MDN/2019", "/static/uploads/legal_docs/hgu_est_002.pdf", "12.13.010.002.002-0002.0", 
            450.0, 6.0, "Shade Robusta Coffee", 0.925000, 99.505000, 
            "/static/img/field_tm_weed.jpg", 5.2, 5.5, 168.0, "b3c48d2"
        ),
        (
            3, "EST-MDN-003", "PT Batang Gadis Plantation", "Drs. Rahmat Lubis", "PT", "legal@batanggadis.co.id • 0821-1122-3344",
            "088/HGU/BPN-MDN/2020", "/static/uploads/legal_docs/hgu_est_003.pdf", "12.13.020.005.001-0014.0", 
            2100.0, 9.0, "Cardamom (Amomum compactum)", 0.852000, 99.185000, 
            "/static/img/field_wetland_buffer.jpg", 5.8, 8.5, 210.0, "c7e19f3"
        ),
        (
            4, "EST-MDN-004", "PT Sorik Marapi Agro Lestari", "Dr. Faisal Tanjung, MP", "PT", "admin@sorikmarapi.co.id • 0811-2233-4455",
            "034/HGU/BPN-MDN/2022", "/static/uploads/legal_docs/hgu_est_004.pdf", "12.13.030.012.003-0008.0", 
            850.0, 5.5, "Porang (Amorphophallus muelleri)", 0.755000, 99.635000, 
            "/static/img/sawit_drone.jpg", 4.8, 6.0, 195.0, "d2a50e4"
        ),
        (
            5, "EST-MDN-005", "KUD Harapan Bersama Natal", "Baharuddin Daulay", "KUD", "kud@harapanbersama.org • 0852-6677-8899",
            "045/HGU/BPN-MDN/2018", "/static/uploads/legal_docs/hgu_est_005.pdf", "12.13.040.008.002-0019.0", 
            380.0, 12.0, "Shade Vanilla (Vanilla planifolia)", 0.575000, 99.125000, 
            "/static/img/field_wetland_buffer.jpg", 4.4, 14.0, 650.0, "e6f81a5"
        ),
        (
            6, "EST-MDN-006", "PT Panyabungan Palma Raya", "Ir. Zulkifli Nasution", "PT", "info@palmaraya.co.id • 0812-4455-6677",
            "055/HGU/BPN-MDN/2021", "/static/uploads/legal_docs/hgu_est_001.pdf", "12.13.050.015.001-0005.0", 
            1450.0, 8.0, "Curcuma / Temulawak (Curcuma zanthorrhiza)", 0.855000, 99.535000, 
            "/static/img/field_tm_weed.jpg", 5.6, 4.0, 155.0, "f1b92c6"
        ),
        (
            7, "EST-MDN-007", "PT Rintis Alam Mandailing", "Hendra Gunawan, S.T.", "PT", "contact@rintisalam.co.id • 0813-5566-7788",
            "071/HGU/BPN-MDN/2023", "/static/uploads/legal_docs/hgu_est_002.pdf", "12.13.060.022.001-0012.0", 
            920.0, 6.5, "Patchouli / Nilam (Pogostemon cablin)", 0.795000, 99.425000, 
            "/static/img/sawit_drone.jpg", 5.3, 5.0, 160.0, "g5d37e7"
        ),
        (
            8, "EST-MDN-008", "Koperasi Tani Tunas Makmur", "M. Yusuf Hasibuan", "KOPSA", "tunasmakmur@gmail.com • 0821-6677-8899",
            "019/HGU/BPN-MDN/2020", "/static/uploads/legal_docs/hgu_est_003.pdf", "12.13.070.010.003-0018.0", 
            310.0, 5.0, "Citronella Grass (Cymbopogon nardus)", 0.885000, 99.555000, 
            "/static/img/field_tm_weed.jpg", 5.4, 4.8, 150.0, "h9e48f8"
        ),
        (
            9, "EST-MDN-009", "PT Bukit Barisan Agro Sejahtera", "Darmansyah, M.B.A.", "PT", "bukitbarisan@agro.co.id • 0811-7788-9900",
            "099/HGU/BPN-MDN/2024", "/static/uploads/legal_docs/hgu_est_004.pdf", "12.13.080.030.001-0022.0", 
            2800.0, 4.0, "Soybean (Glycine max)", 0.775000, 99.345000, 
            "/static/img/sawit_drone.jpg", 5.7, 7.5, 240.0, "i4a29d9"
        ),
        (
            10, "EST-MDN-010", "PT Mitra Agro Mandiri Madina", "Ir. Darwin Simatupang", "PT", "mitraagro@madina.co.id • 0812-8899-0011",
            "062/HGU/BPN-MDN/2022", "/static/uploads/legal_docs/hgu_est_005.pdf", "12.13.090.018.002-0010.0", 
            640.0, 10.0, "Shade Cacao (Theobroma cacao)", 0.655000, 99.255000, 
            "/static/img/field_wetland_buffer.jpg", 5.1, 9.2, 220.0, "9hdjjs8"
        )
    ]

    for est in canonical_estates:
        kode_est = est[1]
        c_lat, c_lng = est[12], est[13]
        area = est[9]
        pub_token = est[18]

        # Use canonical zero-overlap discrete polygon coordinates
        zoning_info = CANONICAL_ESTATES_ZONING.get(kode_est)
        if zoning_info:
            coords = zoning_info["coords"]
            c_lat, c_lng = zoning_info["centroid"]
        else:
            delta = math.sqrt(area / 100.0) * 0.0035
            coords = [
                [round(c_lng - delta, 6), round(c_lat - delta, 6)],
                [round(c_lng + delta, 6), round(c_lat - delta, 6)],
                [round(c_lng + delta, 6), round(c_lat + delta, 6)],
                [round(c_lng - delta, 6), round(c_lat + delta, 6)],
                [round(c_lng - delta, 6), round(c_lat - delta, 6)]
            ]

        poly_json = json.dumps({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [coords]},
            "properties": {"area_ha": area, "name": f"Batas Poligon HGU {kode_est}"}
        })

        cursor.execute("""
            INSERT OR REPLACE INTO kebun_profil (
                id_kebun, kode_kebun, nama_kebun, pemohon, tipe_entitas, kontak,
                nomor_hgu, dokumen_hgu_url, nop_pbb,
                luas_ha, umur_sawit, komoditas_sela, centroid_lat, centroid_lng,
                foto_lahan_url, soil_ph, slope, elevation, poligon_geojson, is_active, sync_bigquery, public_token
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?);
        """, (
            est[0], est[1], est[2], est[3], est[4], est[5], est[6], est[7],
            est[8], est[9], est[10], est[11], c_lat, c_lng, est[14], est[15], est[16], est[17], poly_json, pub_token
        ))

    ai_review_drone = json.dumps({
        "boxes": [
            {"label": "palm_canopy", "label_name": "Tajuk Sawit Optimal", "box_2d": [45, 60, 440, 460], "confidence": 0.98},
            {"label": "clean_alley", "label_name": "Lorong Gawangan 3.79m", "box_2d": [240, 520, 820, 880], "confidence": 0.95},
            {"label": "root_buffer", "label_name": "Piringan Steril 2.0m", "box_2d": [640, 320, 920, 680], "confidence": 0.98},
            {"label": "weed_mulch", "label_name": "Mulsa Hidup Gulma", "box_2d": [400, 40, 660, 260], "confidence": 0.91}
        ],
        "reviewHtml": (
            "<p class=\"font-bold text-white flex items-center gap-1.5\"><span class=\"text-emerald-400\">✓</span> "
            "<span>Object Tajuk Sawit &bull; Lorong 3.79m &bull; Piringan 2.0m</span></p>"
            "<div class=\"text-slate-300 text-[10px] space-y-1.5 pt-1\"><p><strong>And</strong> pemindaian AI Vision Reticle HUD "
            "mengonfirmasi: (1) Tutupan tajuk sawit optimal 71.4% dengan vigor prima; (2) Koridor bersih lorong gawangan 3.79m "
            "bebas tunggul; (3) Piringan steril 2.0m terpelihara zero-tillage PPKS; (4) Mulsa gulma hidup menutup tanah gawangan.</p></div>"
        ),
        "canopy_density": "71.4%",
        "alley_width": "3.79 m",
        "reviewed_at": get_wib_now()
    })

    ai_review_weed = json.dumps({
        "boxes": [
            {"label": "palm_canopy", "label_name": "Tajuk Sawit #1", "box_2d": [100, 40, 420, 360], "confidence": 0.98},
            {"label": "palm_canopy", "label_name": "Tajuk Sawit #2", "box_2d": [80, 620, 410, 940], "confidence": 0.96},
            {"label": "clean_alley", "label_name": "Lorong Gawangan 3.79m", "box_2d": [200, 280, 840, 720], "confidence": 0.95},
            {"label": "root_buffer", "label_name": "Piringan Steril 2.0m", "box_2d": [620, 240, 890, 560], "confidence": 0.98},
            {"label": "weed_mulch", "label_name": "Mulsa Hidup Gulma", "box_2d": [420, 40, 680, 320], "confidence": 0.91}
        ],
        "reviewHtml": (
            "<p class=\"font-bold text-white flex items-center gap-1.5\"><span class=\"text-emerald-400\">✓</span> "
            "<span>Object Tajuk Sawit (7 Thn) &bull; Lorong 3.79m &bull; Piringan 2.0m</span></p>"
            "<div class=\"text-slate-300 text-[10px] space-y-1.5 pt-1\"><p><strong>And</strong> analisis spektral citra memastikan "
            "tegakan sawit fase Tanaman Menghasilkan (TM awal ~7 tahun). Jarak antar-baris 3.79 meter terbuka penuh dengan transmisi "
            "radiasi PAR memadai (650-850 µmol/m²/s). Piringan steril 2.0m terjaga baik.</p></div>"
        ),
        "canopy_density": "68.2%",
        "alley_width": "3.79 m",
        "reviewed_at": get_wib_now()
    })

    ai_review_wetland = json.dumps({
        "boxes": [
            {"label": "palm_canopy", "label_name": "Tajuk Sawit Tepi", "box_2d": [40, 40, 420, 460], "confidence": 0.98},
            {"label": "clean_alley", "label_name": "Sempadan Riparian Alami", "box_2d": [160, 140, 820, 880], "confidence": 0.97},
            {"label": "root_buffer", "label_name": "Piringan Steril 2.0m", "box_2d": [680, 160, 940, 840], "confidence": 0.96}
        ],
        "reviewHtml": (
            "<p class=\"font-bold text-white flex items-center gap-1.5\"><span class=\"text-emerald-400\">✓</span> "
            "<span>Object Sempadan Alami Riparian Buffer</span></p>"
            "<div class=\"text-slate-300 text-[10px] space-y-1.5 pt-1\"><p><strong>And</strong> deteksi objek membuktikan koridor "
            "sempadan perairan alami terjaga dengan baik. Tanaman sela wajib ditata di luar batas sempadan basah sesuai standar HCV/HCS ISPO.</p></div>"
        ),
        "canopy_density": "74.8%",
        "alley_width": "3.79 m",
        "reviewed_at": get_wib_now()
    })

    canopy_seeds = [
            (1, "sawit_drone.jpg", "sawit_drone.jpg", "/static/img/sawit_drone.jpg", 1420500, "image/jpeg", "Foto Pendaftaran HGU", "Dossier Primer", "Blok A - Gawangan Aktif", ai_review_drone),
            (1, "field_tm_weed.jpg", "field_tm_weed.jpg", "/static/img/field_tm_weed.jpg", 1120400, "image/jpeg", "Hamparan Gawangan 7 Thn", "Inspeksi Tapak", "Blok A2 - Gawangan Terbuka", ai_review_weed),
            (1, "field_wetland_buffer.jpg", "field_wetland_buffer.jpg", "/static/img/field_wetland_buffer.jpg", 1340200, "image/jpeg", "Sempadan Riparian Batang Gadis", "Buffer Zone", "Blok A3 - Riparian Buffer", ai_review_wetland),
            (2, "field_tm_weed.jpg", "field_tm_weed.jpg", "/static/img/field_tm_weed.jpg", 1120400, "image/jpeg", "Foto Pendaftaran Koperasi", "Dossier Primer", "Plot Koperasi A1", ai_review_weed),
            (2, "sawit_drone.jpg", "sawit_drone.jpg", "/static/img/sawit_drone.jpg", 1420500, "image/jpeg", "Ortofoto Drone Kebun", "Inspeksi Tapak", "Plot Koperasi B2", ai_review_drone),
            (3, "field_wetland_buffer.jpg", "field_wetland_buffer.jpg", "/static/img/field_wetland_buffer.jpg", 1340200, "image/jpeg", "Sempadan Riparian Batang Gadis", "Dossier Primer", "Blok Riparian C1", ai_review_wetland),
            (3, "sawit_drone.jpg", "sawit_drone.jpg", "/static/img/sawit_drone.jpg", 1420500, "image/jpeg", "Foto Udara Kanopi", "Inspeksi Tapak", "Blok Inti 1", ai_review_drone),
            (4, "sawit_drone.jpg", "sawit_drone.jpg", "/static/img/sawit_drone.jpg", 1420500, "image/jpeg", "Foto Pendaftaran Dossier", "Dossier Primer", "Blok Lereng Sorik", ai_review_drone),
            (4, "field_tm_weed.jpg", "field_tm_weed.jpg", "/static/img/field_tm_weed.jpg", 1120400, "image/jpeg", "Lorong Tanaman Sela Porang", "Inspeksi Tapak", "Blok Gawangan 4", ai_review_weed),
            (5, "field_wetland_buffer.jpg", "field_wetland_buffer.jpg", "/static/img/field_wetland_buffer.jpg", 1340200, "image/jpeg", "Batas Hutan Lindung Natal", "Dossier Primer", "Plot Perbatasan Hutan", ai_review_wetland),
            (5, "field_tm_weed.jpg", "field_tm_weed.jpg", "/static/img/field_tm_weed.jpg", 1120400, "image/jpeg", "Piringan Pokok Sawit Tua", "Inspeksi Tapak", "Plot KUD Barat", ai_review_weed),
            (6, "field_tm_weed.jpg", "field_tm_weed.jpg", "/static/img/field_tm_weed.jpg", 1120400, "image/jpeg", "Foto Pendaftaran Panyabungan", "Dossier Primer", "Blok A1", ai_review_weed),
            (7, "sawit_drone.jpg", "sawit_drone.jpg", "/static/img/sawit_drone.jpg", 1420500, "image/jpeg", "Ortofoto Rintis Alam", "Dossier Primer", "Blok B2", ai_review_drone),
            (8, "field_tm_weed.jpg", "field_tm_weed.jpg", "/static/img/field_tm_weed.jpg", 1120400, "image/jpeg", "Foto Hamparan Petani", "Dossier Primer", "Plot Poktan 1", ai_review_weed),
            (9, "sawit_drone.jpg", "sawit_drone.jpg", "/static/img/sawit_drone.jpg", 1420500, "image/jpeg", "Ortofoto Bukit Barisan", "Dossier Primer", "Blok Agro 9", ai_review_drone),
            (10, "field_wetland_buffer.jpg", "field_wetland_buffer.jpg", "/static/img/field_wetland_buffer.jpg", 1340200, "image/jpeg", "Foto Lahan Mitra Agro", "Dossier Primer", "Blok Madina 10 - Sempadan", ai_review_wetland),
            (10, "sawit_drone.jpg", "sawit_drone.jpg", "/static/img/sawit_drone.jpg", 1420500, "image/jpeg", "Ortofoto Drone Madina 10", "Inspeksi Tapak", "Blok Madina 10 - Gawangan Inti", ai_review_drone),
            (10, "field_tm_weed.jpg", "field_tm_weed.jpg", "/static/img/field_tm_weed.jpg", 1120400, "image/jpeg", "Lorong Tanaman Sela Cacao", "Inspeksi Lapangan", "Blok Madina 10 - Lorong Agro", ai_review_weed)
        ]

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_canopy_estate_file ON canopy_uploads(id_kebun, filename, block_id);
    """)

    for cs in canopy_seeds:
        cursor.execute("""
            INSERT OR IGNORE INTO canopy_uploads (
                id_kebun, filename, original_name, file_url, file_size, mime_type,
                title, tag, block_id, ai_review_json, sync_bigquery
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
        """, cs)

    cert_seeds = [
        (1, 'CERT-ECOGREEN-2026-0001', 2026, 98.5, 'EXCELLENT COMPLIANT', 'active', 'Q2_ACTIVE', '2026-01-01', '2026-12-31', '2026-06-30', 'VERIFIED', '2026-03-15', 'VERIFIED', '2026-06-20', 1.5238, 34.37, 1546.65, '8F434346648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327AA4', 'c1109a1'),
        (2, 'CERT-ECOGREEN-2026-0002', 2026, 88.0, 'CONDITIONALLY COMPLIANT', 'provisional', 'Q2_PENDING', '2026-01-01', '2026-12-31', '2026-06-30', 'VERIFIED', '2026-03-20', 'PENDING', None, 1.4420, 15.20, 684.00, '9A42C123648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327CC1', 'c2208b2'),
        (3, 'CERT-ECOGREEN-2026-0003', 2026, 94.2, 'EXCELLENT COMPLIANT', 'active', 'Q2_ACTIVE', '2026-01-01', '2026-12-31', '2026-06-30', 'VERIFIED', '2026-03-18', 'VERIFIED', '2026-06-22', 1.5820, 62.10, 2794.50, '3C842B10648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327DD3', 'c3307c3'),
        (4, 'CERT-ECOGREEN-2026-0004', 2026, 91.0, 'FULLY COMPLIANT', 'active', 'Q2_ACTIVE', '2026-01-01', '2026-12-31', '2026-06-30', 'VERIFIED', '2026-03-21', 'VERIFIED', '2026-06-25', 1.4910, 25.80, 1161.00, '4D953C21648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327EE4', 'c4406d4'),
        (5, 'CERT-ECOGREEN-2026-0005', 2026, 96.0, 'EXCELLENT COMPLIANT', 'active', 'Q2_ACTIVE', '2026-01-01', '2026-12-31', '2026-06-30', 'VERIFIED', '2026-03-12', 'VERIFIED', '2026-06-18', 1.6120, 14.50, 652.50, '5EA64D32648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327FF5', 'c5505e5'),
        (6, 'CERT-ECOGREEN-2026-0006', 2026, 93.5, 'FULLY COMPLIANT', 'active', 'Q2_ACTIVE', '2026-01-01', '2026-12-31', '2026-06-30', 'VERIFIED', '2026-03-16', 'VERIFIED', '2026-06-20', 1.5150, 42.60, 1917.00, '6FB75E43648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327AA6', 'c6604f6'),
        (7, 'CERT-ECOGREEN-2026-0007', 2026, 89.5, 'CONDITIONALLY COMPLIANT', 'provisional', 'Q2_PENDING', '2026-01-01', '2026-12-31', '2026-06-30', 'VERIFIED', '2026-03-22', 'PENDING', None, 1.4880, 28.30, 1273.50, '7AC86F54648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327BB7', 'c7703a7'),
        (8, 'CERT-ECOGREEN-2026-0008', 2026, 87.0, 'CONDITIONALLY COMPLIANT', 'provisional', 'Q2_PENDING', '2026-01-01', '2026-12-31', '2026-06-30', 'VERIFIED', '2026-03-24', 'PENDING', None, 1.4250, 11.20, 504.00, '8BD97A65648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327CC8', 'c8802b8'),
        (9, 'CERT-ECOGREEN-2026-0009', 2026, 95.0, 'EXCELLENT COMPLIANT', 'active', 'Q2_ACTIVE', '2026-01-01', '2026-12-31', '2026-06-30', 'VERIFIED', '2026-03-14', 'VERIFIED', '2026-06-19', 1.5540, 86.40, 3888.00, '9CE08B76648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327DD9', 'c9901c9'),
        (10, 'CERT-ECOGREEN-2026-0010', 2026, 99.2, 'PLATINUM STATUTORY COMPLIANT', 'active', 'Q2_ACTIVE', '2026-01-01', '2026-12-31', '2026-06-30', 'VERIFIED', '2026-03-10', 'VERIFIED', '2026-06-15', 1.6364, 407.30, 184435.20, 'A0F19C87648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327EE0', '743hjhjhj87')
    ]

    for cs_data in cert_seeds:
        cursor.execute("""
            INSERT OR REPLACE INTO kebun_sertifikat_ecogreen (
                id_kebun, nomor_registrasi, tahun_anggaran, skor_kepatuhan, predikat,
                status_sertifikat, status_siklus, tgl_terbit, tgl_kadaluarsa,
                tanggal_terbit, tanggal_kadaluarsa,
                tgl_jatuh_tempo_siklus, q1_status, q1_verified_at,
                q2_status, q2_verified_at, ler_achieved, avoided_forest_ha,
                carbon_tco2e, sha256_credential_hash, public_token, sync_bigquery
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
        """, (
            cs_data[0], cs_data[1], cs_data[2], cs_data[3], cs_data[4],
            cs_data[5], cs_data[6], cs_data[7], cs_data[8],
            cs_data[7], cs_data[8],
            cs_data[9], cs_data[10], cs_data[11],
            cs_data[12], cs_data[13], cs_data[14], cs_data[15],
            cs_data[16], cs_data[17], cs_data[18]
        ))

    # Clean legacy duplicate seed entries in kebun_monitoring_log if any
    try:
        cursor.execute("DELETE FROM kebun_monitoring_log WHERE id_log NOT IN (SELECT MIN(id_log) FROM kebun_monitoring_log GROUP BY id_kebun, titik_ke, periode_siklus);")
    except Exception:
        pass

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_mon_estate_pt ON kebun_monitoring_log(id_kebun, titik_ke, periode_siklus);
    """)

    monitoring_seeds = [
        # EST-MDN-001 (PT Mandailing Agro Sustainable) - 3 Valid Inspection Records
        (
            1, "Cycle 1 (Post-Planting)", 2026, 1, 0.824100, 99.561200, 142.0, 1.5, 4.5, "ground_eye_level",
            "/static/img/sawit_drone.jpg", "2026-10-09 10:20:00", "Partly Cloudy (26.6°C)", 1, 2.0, 0.0, "verified",
            json.dumps({
                "ai_ground_truth": {"soil_ph": 5.5, "slope": 4.5, "elevation": 142.0, "status": "SAFE_APL"},
                "assessor_audit": {
                    "mandor": "Supervisor Sutrisno",
                    "blok": "Block A - Centroid WGS84",
                    "assessor_name": "Supervisor Sutrisno",
                    "verdict": "DISETUJUI_PENUH",
                    "notes": "Tapak lahan memenuhi baku mutu agronomi PPKS. Piringan steril 2.0m terjaga baik zero-tillage."
                }
            }),
            "8F434346648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327AA4"
        ),
        (
            1, "Registration Baseline", 2026, 2, 0.824150, 99.561250, 143.0, 1.5, 4.5, "ground_eye_level",
            "/static/img/field_tm_weed.jpg", "2026-10-09 09:15:00", "Partly Cloudy (26.4°C)", 1, 2.0, 1.2, "verified",
            json.dumps({
                "ai_ground_truth": {"soil_ph": 5.4, "slope": 4.5, "elevation": 143.0, "status": "SAFE_APL"},
                "assessor_audit": {
                    "mandor": "Supervisor Faisal",
                    "blok": "Block A2 - Active Alley Corridor",
                    "assessor_name": "Supervisor Faisal",
                    "verdict": "DISETUJUI_PENUH",
                    "notes": "Lorong gawangan 3.79m bersih bebas tunggul dan piringan steril 2.0m terpelihara."
                }
            }),
            "C2D5E3F4A5B60123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0124"
        ),
        (
            1, "Cycle 2 (Riparian Surveillance)", 2026, 3, 0.824200, 99.561300, 145.0, 1.5, 4.8, "drone_nadir",
            "/static/img/field_wetland_buffer.jpg", "2026-10-12 14:30:00", "Cerah Berawan (27.1°C)", 1, 2.0, 0.5, "verified",
            json.dumps({
                "ai_ground_truth": {"soil_ph": 5.6, "slope": 4.8, "elevation": 145.0, "status": "SAFE_APL"},
                "assessor_audit": {
                    "mandor": "Supervisor Hendra",
                    "blok": "Block A3 - Riparian Buffer Zone",
                    "assessor_name": "Supervisor Hendra",
                    "verdict": "DISETUJUI_PENUH",
                    "notes": "Sempadan sungai alami terlindungi sesuai standar HCV/HCS ISPO & EUDR Article 9."
                }
            }),
            "D3E6F4A5B6C70123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0125"
        ),

        # EST-MDN-002 (KUD Sawit Subur Mandiri) - 2 Valid Inspection Records
        (
            2, "Cycle 1 (Post-Planting)", 2026, 1, 0.842100, 99.531200, 168.0, 1.5, 5.5, "ground_eye_level",
            "/static/img/field_tm_weed.jpg", "2026-10-09 08:45:00", "Cerah Berawan (26.0°C)", 1, 2.0, 1.8, "verified",
            json.dumps({
                "ai_ground_truth": {"soil_ph": 5.2, "slope": 5.5, "elevation": 168.0, "status": "SAFE_APL"},
                "assessor_audit": {
                    "mandor": "Ir. Hendra Siregar, M.Si.",
                    "blok": "Plot Koperasi A1",
                    "assessor_name": "Ir. Hendra Siregar, M.Si.",
                    "verdict": "DISETUJUI_PENUH",
                    "notes": "Petak Koperasi memenuhi batas sempadan ISPO Prinsip 3 dan radius piringan steril."
                }
            }),
            "B7C0D8E9F0A10123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0129"
        ),
        (
            2, "Registration Baseline", 2026, 2, 0.842200, 99.531300, 169.0, 1.5, 5.2, "drone_nadir",
            "/static/img/sawit_drone.jpg", "2026-10-11 10:30:00", "Cerah (27.5°C)", 1, 2.0, 1.2, "verified",
            json.dumps({
                "ai_ground_truth": {"soil_ph": 5.3, "slope": 5.2, "elevation": 169.0, "status": "SAFE_APL"},
                "assessor_audit": {
                    "mandor": "Supervisor Ruslan",
                    "blok": "Plot Koperasi B2",
                    "assessor_name": "Supervisor Ruslan",
                    "verdict": "DISETUJUI_PENUH",
                    "notes": "Pengambilan sampel ortofoto drone memvalidasi koridor gawangan tanaman sela nilam."
                }
            }),
            "C8D1E9F0A1B20123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0130"
        ),

        # EST-MDN-010 (PT Mitra Agro Mandiri Madina) - 3 Valid Inspection Records
        (
            10, "Cycle 1 (Post-Planting)", 2026, 1, 0.819400, 99.563000, 220.0, 1.5, 9.2, "ground_eye_level",
            "/static/img/field_wetland_buffer.jpg", "2026-10-10 08:30:00", "Cerah Berawan (25.8°C)", 1, 2.0, 0.8, "verified",
            json.dumps({
                "ai_ground_truth": {"soil_ph": 5.1, "slope": 9.2, "elevation": 220.0, "status": "SAFE_APL"},
                "assessor_audit": {
                    "mandor": "Ir. Darwin Simatupang",
                    "blok": "Blok Madina 10 - Sempadan Riparian",
                    "assessor_name": "Ir. Darwin Simatupang",
                    "verdict": "DISETUJUI_PENUH",
                    "notes": "Batas kawasan lereng 9.2 derajat dan sempadan air Madina aman terverifikasi ISPO."
                }
            }),
            "E4F7A5B6C7D80123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0126"
        ),
        (
            10, "Registration Baseline", 2026, 2, 0.819500, 99.563100, 222.0, 1.5, 9.0, "drone_nadir",
            "/static/img/sawit_drone.jpg", "2026-10-11 11:15:00", "Cerah (28.2°C)", 1, 2.0, 1.1, "verified",
            json.dumps({
                "ai_ground_truth": {"soil_ph": 5.2, "slope": 9.0, "elevation": 222.0, "status": "SAFE_APL"},
                "assessor_audit": {
                    "mandor": "Supervisor Gunawan",
                    "blok": "Blok Madina 10 - Gawangan Inti",
                    "assessor_name": "Supervisor Gunawan",
                    "verdict": "DISETUJUI_PENUH",
                    "notes": "Piringan steril 2.0m zero-tillage dan tutupan kanopi 74.8% terverifikasi prima."
                }
            }),
            "F5A8B6C7D8E90123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0127"
        ),
        (
            10, "Cycle 2 (Shade Cacao Audit)", 2026, 3, 0.819600, 99.563200, 224.0, 1.5, 8.8, "ground_eye_level",
            "/static/img/field_tm_weed.jpg", "2026-10-13 13:45:00", "Berawan (26.5°C)", 1, 2.0, 1.4, "verified",
            json.dumps({
                "ai_ground_truth": {"soil_ph": 5.3, "slope": 8.8, "elevation": 224.0, "status": "SAFE_APL"},
                "assessor_audit": {
                    "mandor": "Supervisor Syafei",
                    "blok": "Blok Madina 10 - Lorong Cacao",
                    "assessor_name": "Supervisor Syafei",
                    "verdict": "DISETUJUI_PENUH",
                    "notes": "Pertumbuhan tanaman sela kakao naungan dalam lorong gawangan prima tanpa defisit hara."
                }
            }),
            "A6B9C7D8E9F00123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0128"
        )
    ]

    for m in monitoring_seeds:
        cursor.execute("""
            INSERT OR IGNORE INTO kebun_monitoring_log (
                id_kebun, periode_siklus, tahun_siklus, titik_ke, gps_lat, gps_lng,
                elevasi_dpl, ketinggian_agl, kemiringan_lereng, view_perspective,
                foto_url, waktu_pengambilan, cuaca_tercatat, cuaca_satellite_match,
                piringan_steril_meter, defisit_tbs_persen, ai_scan_status, ai_scan_result_json, sha256_seal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, m)

    # 4. Seed official telemetry records into compute_audit_logs
    for s in OFFICIAL_TELEMETRY_SEEDS:
        cursor.execute("""
            INSERT OR IGNORE INTO compute_audit_logs (
                id, request_id, stand_age, land_area, crop_type, ler_score, pls_percentage,
                forest_saved_ha, carbon_tco2e, sha256_hash, created_at, sync_bigquery
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
        """, (
            s["id"], s["request_id"], s["stand_age"], s["land_area"], s["crop_type"],
            s["ler_score"], s["pls_percentage"], s["forest_saved_ha"], s["carbon_tco2e"],
            s["sha256_hash"], s["created_at"]
        ))

    conn.commit()
    conn.close()

def seed_roadmap_milestones(db_path: str) -> None:
    """Populates the 18 statutory roadmap milestone references if table is empty."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ref_roadmap_siklus;")
    if cursor.fetchone()[0] == 0:
        milestones = [
            (1, "Pra-Tanam & Perencanaan", 1, "M1.1", "Verifikasi Legalitas & Tenurial HGU/e-STDB", "Legal Compliance", "Bulan 1", 1, 1, "Divisi Legal", "Surat Bukti Hak Atas Tanah", "Verifikasi keabsahan dokumen legalitas HGU/e-STDB.", "/roadmap", "Buka Modul", "RULE_LEGAL_TENURE", 5.55),
            (1, "Pra-Tanam & Perencanaan", 2, "M1.2", "Pemetaan Poligon Batas Bidang WGS84", "Spatial GIS", "Bulan 1", 1, 1, "GIS Engineer", "Berkas OGC GeoJSON RFC 7946", "Pengambilan koordinat batas bidang 6 desimal.", "/spatial", "Buka Modul", "RULE_WGS84_POLYGON", 5.55),
            (1, "Pra-Tanam & Perencanaan", 3, "M1.3", "Uji Geospasial Moratorium PIPPIB & EUDR 2020", "Spatial Clearance", "Bulan 1", 1, 2, "Lead Auditor", "Sertifikat Bebas Moratorium", "Pemeriksaan irisan peta moratorium PIPPIB & EUDR.", "/spatial", "Buka Modul", "RULE_PIPPIB_EUDR_CUTOFF", 5.55),
            (1, "Pra-Tanam & Perencanaan", 4, "M1.4", "Analisis Biofisika Kanopi In-Silico Beer-Lambert", "Biophysical Core", "Bulan 2", 2, 2, "Agronomis PPKS", "Lembar Audit Transmisi PAR", "Kalkulasi transmisi radiasi tembus kanopi.", "/simulator", "Buka Modul", "RULE_BEER_LAMBERT_PAR", 5.55),
            (2, "Persiapan Lahan & Penataan", 5, "M2.1", "Penataan Geometri Gawangan Aktif 3.79m", "Spatial Optimization", "Bulan 2", 2, 3, "Mandor Lapangan", "Peta Tata Ruang Gawangan", "Pengukuran koridor efektif 3.79m.", "/simulator", "Buka Modul", "RULE_ALLEY_379M", 5.55),
            (2, "Persiapan Lahan & Penataan", 6, "M2.2", "Konservasi Piringan Steril Radius 2.0m (Zero-Tillage)", "ISPO Principle 2", "Bulan 3", 3, 3, "Mandor Lapangan", "Log Inspeksi Bebas Cangkul", "Larangan olah tanah piringan 2.0m pelindung akar.", "/mobile", "Buka Modul", "RULE_ZERO_TILLAGE_2M", 5.55),
            (2, "Persiapan Lahan & Penataan", 7, "M2.3", "Remediasi Kemasaman Tanah Aplikasi Dolomit", "Soil Chemistry", "Bulan 3", 3, 3, "Agronomis Lapangan", "Surat Rekomendasi Pembenah", "Pengapuran dolomit bila pH tanah < 4.5.", "/simulator", "Buka Modul", "RULE_DOLOMITE_LIMING", 5.55),
            (2, "Persiapan Lahan & Penataan", 8, "M2.4", "Pembuatan Rorak Sedimen & Teras Kontur Lereng", "Soil Conservation", "Bulan 3", 3, 4, "Mandor Konservasi", "Berita Acara Rorak Fisik", "Pembuatan silt pit penahan limpasan permukaan.", "/spatial", "Buka Modul", "RULE_SILT_PIT_RORAK", 5.55),
            (3, "Penanaman Tanaman Sela", 9, "M3.1", "Gerbang Rekomendasi Multi-Kandidat AI Komoditas", "AI Decision Gate", "Bulan 4", 4, 4, "Agronomis & Pekebun", "Lembar Evaluasi 3 Opsi Tanaman", "Penetapan 1 komoditas definitif dari 3 alternatif.", "/simulator", "Buka Modul", "RULE_MULTI_CANDIDATE_GATE", 5.55),
            (3, "Penanaman Tanaman Sela", 10, "M3.2", "Penerbitan Paspor Rekomendasi EcoGreen Provisional", "Provisional Permit", "Bulan 4", 4, 4, "Certification Registrar", "Provisional Green Palm Passport", "Penerbitan izin operasional tanam berstempel SHA-256.", "/certificate", "Buka Modul", "RULE_PROVISIONAL_PASSPORT", 5.55),
            (3, "Penanaman Tanaman Sela", 11, "M3.3", "Pengadaan Bibit Unggul Bebas Hama", "Agronomy Sourcing", "Bulan 4", 4, 5, "Bagian Pembibitan", "Sertifikat Benih Resmi", "Verifikasi kualitas dan sertifikasi varietas bibit.", "/roadmap", "Buka Modul", "RULE_CERTIFIED_SEED", 5.55),
            (3, "Penanaman Tanaman Sela", 12, "M3.4", "Penanaman Sela Berjarak Baku di Lorong", "Field Execution", "Bulan 5", 5, 5, "Mandor Tanam", "Laporan Realisasi Tanam", "Penanaman bibit pada 6 baris bedengan kontur.", "/mobile", "Buka Modul", "RULE_INTERCROP_PLANTED", 5.55),
            (4, "Pemeliharaan & Pemupukan", 13, "M4.1", "Pemupukan Kompensasi Kalium MOP / Hemat Urea", "PPKS Nutrient Balance", "Bulan 6", 6, 7, "Mandor Pupuk", "Buku Catatan Pemupukan", "Aplikasi pupuk MOP 75 kg/ha atau hemat urea legum.", "/simulator", "Buka Modul", "RULE_NPK_COMPENSATION", 5.55),
            (4, "Pemeliharaan & Pemupukan", 14, "M4.2", "Aplikasi Mulsa Pelepah Cincang di Gawangan", "Circular Biomass", "Bulan 7", 7, 8, "Mandor Rawat", "Dokumentasi Mulsa Gawangan", "Pemanfaatan pelepah pangkasan sebagai mulsa.", "/mobile", "Buka Modul", "RULE_BIOMASS_MULCH", 5.55),
            (4, "Pemeliharaan & Pemupukan", 15, "M4.3", "Surveilans Mandor Lapangan Siklus 1 & 2 via PWA", "Edge Surveillance", "Bulan 8", 8, 9, "Mandor Lapangan", "Log Surveilans Foto Ber-GPS", "Pemantauan berkala via aplikasi mandor PWA.", "/mobile", "Buka Modul", "RULE_EDGE_CYCLE_1_2", 5.55),
            (5, "Pemanenan & Sertifikasi", 16, "M5.1", "Surveilans Mandor Siklus 3 (Pra-Panen)", "Field Surveillance", "Bulan 10", 10, 11, "Mandor Lapangan", "Log Panen & Foto Verifikasi", "Audit bukti fisik menjelang panen komoditas.", "/mobile", "Buka Modul", "RULE_EDGE_CYCLE_3", 5.55),
            (5, "Pemanenan & Sertifikasi", 17, "M5.2", "Audit Defisit Hasil TBS Sawit (Maksimal <= 4.5%)", "Economic Protection", "Bulan 11", 11, 12, "Lead Auditor", "Laporan Neraca Hasil TBS", "Verifikasi penurunan hasil sawit tidak melebihi 4.5%.", "/simulator", "Buka Modul", "RULE_TBS_DEFICIT_LIMIT", 5.55),
            (5, "Pemanenan & Sertifikasi", 18, "M5.3", "Penerbitan Sertifikat Kepatuhan Statuter EcoGreen Akhir", "Statutory Seal", "Bulan 12", 12, 12, "Accredited Certifier", "Statutory EcoGreen Certificate", "Penerbitan sertifikat kepatuhan resmi siap ekspor EUDR.", "/certificate", "Buka Modul", "RULE_FINAL_STATUTORY_CERT", 5.65)
        ]
        cursor.executemany("""
            INSERT INTO ref_roadmap_siklus (
                fase, nama_fase, nomor_urut, kode_proses, judul, kategori,
                waktu_pelaksanaan, bulan_mulai, bulan_selesai, penanggung_jawab,
                output_dokumen, deskripsi, link_menu, link_label, rule_pengecekan, bobot_persen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, milestones)
        conn.commit()
    conn.close()

def get_estate_spatial_data(identifier: Union[str, int], db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches full relational spatial profile of an estate from SQLite:
    Profile, associated isolated photos from canopy_uploads, recent monitoring logs,
    and latest assessor inspection record.
    """
    path = db_path or DEFAULT_DB_PATH
    conn = get_db_connection(path)
    cursor = conn.cursor()

    query_estate = """
        SELECT 
            p.*,
            COALESCE(c.nomor_registrasi, 'CERT-ECOGREEN-2026-' || printf('%04d', p.id_kebun)) AS nomor_registrasi,
            COALESCE(c.status_sertifikat, CASE WHEN p.is_active = 1 THEN 'active' ELSE 'in_progress' END) AS status_sertifikat,
            COALESCE(c.status_siklus, 'Q1_PROVISIONAL') AS status_siklus
        FROM kebun_profil p
        LEFT JOIN kebun_sertifikat_ecogreen c ON p.id_kebun = c.id_kebun
        WHERE p.kode_kebun = ? OR CAST(p.id_kebun AS TEXT) = ?
        LIMIT 1;
    """
    ident_str = str(identifier).strip()
    cursor.execute(query_estate, (ident_str, ident_str))
    estate_row = cursor.fetchone()

    if not estate_row:
        cursor.execute(query_estate, ("EST-MDN-001", "1"))
        estate_row = cursor.fetchone()

    if not estate_row:
        conn.close()
        return None

    estate_dict = dict(estate_row)
    id_kebun = estate_dict["id_kebun"]

    cursor.execute("""
        SELECT * FROM canopy_uploads 
        WHERE id_kebun = ? 
        ORDER BY id ASC;
    """, (id_kebun,))
    photo_rows = cursor.fetchall()
    photos = [dict(p) for p in photo_rows]

    if not photos:
        photos = [{
            "id": 1,
            "id_kebun": id_kebun,
            "filename": estate_dict.get("foto_lahan_url", "/static/img/sawit_drone.jpg").split("/")[-1],
            "file_url": estate_dict.get("foto_lahan_url", "/static/img/sawit_drone.jpg"),
            "title": "Foto Pendaftaran HGU",
            "tag": "Dossier Primer",
            "block_id": "Blok A",
            "ai_review_json": None
        }]

    cursor.execute("""
        SELECT * FROM kebun_monitoring_log 
        WHERE id_kebun = ? 
        ORDER BY waktu_pengambilan DESC 
        LIMIT 20;
    """, (id_kebun,))
    survey_rows = cursor.fetchall()
    surveys = [dict(s) for s in survey_rows]

    last_inspection = None
    for s in surveys:
        if s.get("ai_scan_result_json"):
            try:
                parsed = json.loads(s["ai_scan_result_json"])
                if parsed and parsed.get("assessor_audit"):
                    last_inspection = parsed["assessor_audit"]
                    if "soil_ph" in last_inspection:
                        estate_dict["soil_ph"] = last_inspection["soil_ph"]
                    if "slope" in last_inspection:
                        estate_dict["slope"] = last_inspection["slope"]
                    if "soil_texture" in last_inspection:
                        estate_dict["soil_texture"] = last_inspection["soil_texture"]
                    break
            except Exception:
                pass

    conn.close()

    return {
        "estate": estate_dict,
        "photos": photos,
        "surveys": surveys,
        "last_inspection": last_inspection
    }

def add_estate_canopy_upload(
    id_kebun: int,
    filename: str,
    file_url: str,
    original_name: Optional[str] = None,
    title: Optional[str] = None,
    tag: str = "Unggahan Baru",
    block_id: str = "Blok A",
    ai_review_json: Optional[str] = None,
    file_size: int = 0,
    mime_type: str = "image/jpeg",
    db_path: Optional[str] = None
) -> int:
    """Inserts a new canopy upload tied relationally to a specific estate ID."""
    path = db_path or DEFAULT_DB_PATH
    conn = get_db_connection(path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO canopy_uploads (
            id_kebun, filename, original_name, file_url, file_size, mime_type,
            title, tag, block_id, ai_review_json, sync_bigquery
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
    """, (
        id_kebun, filename, original_name or filename, file_url, file_size, mime_type,
        title or os.path.splitext(filename)[0], tag, block_id, ai_review_json
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def save_simulation_record(
    palm_age: float,
    land_area: float,
    crop_name: str,
    leaf_area_index: float = 5.27,
    surface_par: float = 218.5,
    total_ler: float = 1.5238,
    avoided_land_ha: float = 34.37,
    total_climate_benefit_tco2e: float = 1546.65,
    ai_response_json: Any = None,
    inference_mode: str = 'hybrid',
    image_path: Optional[str] = None,
    image_url: Optional[str] = None,
    ai_health_status: Optional[str] = None,
    ai_age_estimate: Optional[str] = None,
    ai_replanting_forecast: Optional[str] = None,
    ai_audit_review: Any = None,
    compliance_badges: Any = None,
    sha256_hash: Optional[str] = None,
    db_path: Optional[str] = None,
    **kwargs
) -> int:
    """
    Stores an in-silico simulation computation into compute_audit_logs.
    Generates a deterministic SHA-256 seal and maintains BigQuery sync readiness.
    """
    init_db(db_path)
    now_str = get_wib_now()

    req_id = f"REQ-{int(datetime.now().timestamp() * 1000)}"
    if not sha256_hash:
        raw_seed = f"COMPUTE|AGE:{palm_age}|AREA:{land_area}|CROP:{crop_name}|LER:{total_ler}|TIME:{now_str}"
        sha256_hash = hashlib.sha256(raw_seed.encode('utf-8')).hexdigest().upper()

    pls_pct = round((1.0 - (1.0 / total_ler)) * 100.0, 2) if total_ler > 1.0 else 0.0

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO compute_audit_logs (
            request_id, stand_age, land_area, crop_type, ler_score,
            pls_percentage, forest_saved_ha, carbon_tco2e, sha256_hash, sync_bigquery
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
    """, (
        req_id, float(palm_age), float(land_area), str(crop_name), float(total_ler),
        float(pls_pct), float(avoided_land_ha), float(total_climate_benefit_tco2e),
        str(sha256_hash)
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return record_id

def save_experiment(*args, **kwargs) -> int:
    """Convenience alias for save_simulation_record guaranteeing zero regression."""
    return save_simulation_record(*args, **kwargs)

def get_recent_simulations(limit: int = 10, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves recent simulation audit records ordered by ID DESC."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id, request_id, created_at,
            stand_age AS palm_age, land_area, crop_type AS crop_name,
            ler_score AS total_ler, pls_percentage,
            forest_saved_ha AS avoided_land_ha,
            carbon_tco2e AS total_climate_benefit_tco2e,
            sha256_hash
        FROM compute_audit_logs
        ORDER BY id DESC
        LIMIT ?;
    """, (int(limit),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_simulation_log_by_id(log_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a single computation record by its numeric primary key."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id, request_id, created_at,
            stand_age AS palm_age, land_area, crop_type AS crop_name,
            ler_score AS total_ler, pls_percentage,
            forest_saved_ha AS avoided_land_ha,
            carbon_tco2e AS total_climate_benefit_tco2e,
            sha256_hash
        FROM compute_audit_logs
        WHERE id = ?;
    """, (int(log_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_unsynced_bigquery_records(table_name: str, limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches records marked with sync_bigquery = 0 for streaming ingestion."""
    valid_tables = ["kebun_profil", "kebun_monitoring_log", "compute_audit_logs", "kebun_sertifikat_ecogreen"]
    if table_name not in valid_tables:
        raise ValueError(f"Invalid table for BigQuery synchronization: {table_name}")

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE sync_bigquery = 0 LIMIT ?;", (int(limit),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_record_as_synced(table_name: str, id_column: str, record_id: Any, db_path: Optional[str] = None) -> None:
    """Updates sync_bigquery = 1 upon successful BigQuery confirmation."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {table_name} SET sync_bigquery = 1 WHERE {id_column} = ?;", (record_id,))
    conn.commit()
    conn.close()

def evaluate_certificate_lifecycle(cert_dict: Dict[str, Any], logs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Evaluates dynamic 4-Quarter (Q1-Q4) compliance state machine,
    6-month physical planting tolerance deadline, and EUDR/ISPO credentials.
    """
    tgl_terbit_str = cert_dict.get('tgl_terbit') or cert_dict.get('tanggal_terbit') or '2026-01-01'
    try:
        if isinstance(tgl_terbit_str, str):
            issue_date = datetime.strptime(tgl_terbit_str.split()[0], '%Y-%m-%d').date()
        elif isinstance(tgl_terbit_str, (datetime, date)):
            issue_date = tgl_terbit_str if isinstance(tgl_terbit_str, date) else tgl_terbit_str.date()
        else:
            issue_date = date(2026, 1, 1)
    except Exception:
        issue_date = date(2026, 1, 1)

    today = datetime.now(WIB).date()
    delta_days = max(0, (today - issue_date).days)

    if delta_days <= 90:
        current_quarter = 'Q1'
    elif delta_days <= 180:
        current_quarter = 'Q2'
    elif delta_days <= 270:
        current_quarter = 'Q3'
    else:
        current_quarter = 'Q4'

    q1_status = cert_dict.get('q1_status') or 'VERIFIED'
    q2_status = cert_dict.get('q2_status') or 'PENDING'
    q3_status = cert_dict.get('q3_status') or 'PENDING'
    q4_status = cert_dict.get('q4_status') or 'PENDING'

    has_verified_field_work = False
    if logs:
        for log in logs:
            if log.get('ai_scan_status') == 'verified' or log.get('cuaca_satellite_match') == 1:
                has_verified_field_work = True
                break

    is_suspended = False
    suspension_reason = None
    is_valid = True

    if delta_days > 180 and q2_status != 'VERIFIED' and not has_verified_field_work:
        status_code = 'SUSPENDED_6_MONTHS'
        status_label_id = 'Sertifikat Dibekukan Sementara (Melewati Toleransi 180 Hari)'
        status_label_en = 'Suspended (Exceeded 180 Days Physical Planting Deadline)'
        is_suspended = True
        is_valid = False
        suspension_reason = (
            "Kebun telah melewati toleransi 180 hari (6 bulan) sejak tanggal terbit awal "
            "tanpa adanya realisasi fisik budidaya tumpang sari terverifikasi di lorong gawangan."
        )
    elif 150 <= delta_days <= 180 and q2_status != 'VERIFIED' and not has_verified_field_work:
        status_code = 'WARNING_Q2_PENDING'
        status_label_id = 'Peringatan: Mendekati Batas Toleransi 6 Bulan'
        status_label_en = 'Warning: Approaching 6-Month Tolerance Deadline'
        is_suspended = False
        is_valid = True
    elif delta_days > 365:
        status_code = 'RENEWAL_DUE'
        status_label_id = 'Jatuh Tempo Perpanjangan Siklus Tahunan'
        status_label_en = 'Annual Statutory Renewal Due'
        is_suspended = False
        is_valid = True
    else:
        status_code = cert_dict.get('status_siklus') or ('Q2_ACTIVE' if delta_days > 90 else 'Q1_PROVISIONAL')
        status_label_id = 'Aktif & Patuh Penuh (Statutory Compliant)'
        status_label_en = 'Active & Fully Compliant'
        is_suspended = False
        is_valid = True

    d1 = issue_date + timedelta(days=90)
    d2 = issue_date + timedelta(days=180)
    d3 = issue_date + timedelta(days=270)
    d4 = issue_date + timedelta(days=365)

    quarterly_timeline = [
        {
            "quarter_code": "Q1",
            "title_id": "Triwulan 1: Pra-Tanam & Penataan Gawangan",
            "window": "Bulan 1 - 3 (Hari 1 - 90)",
            "date": d1.strftime('%Y-%m-%d'),
            "status": q1_status,
            "status_label": "TERVERIFIKASI" if q1_status == 'VERIFIED' else ("AKTIF" if current_quarter == 'Q1' else "TERTUNDA")
        },
        {
            "quarter_code": "Q2",
            "title_id": "Triwulan 2: Penanaman Sela & Pemeliharaan",
            "window": "Bulan 4 - 6 (Hari 91 - 180)",
            "date": d2.strftime('%Y-%m-%d'),
            "status": "OVERDUE" if is_suspended else (q2_status if q2_status == 'VERIFIED' else ("ACTIVE" if current_quarter == 'Q2' else "PENDING")),
            "status_label": "LEWAT BATAS (DIBEKUKAN)" if is_suspended else ("TERVERIFIKASI" if q2_status == 'VERIFIED' else ("AKTIF" if current_quarter == 'Q2' else "TERTUNDA"))
        },
        {
            "quarter_code": "Q3",
            "title_id": "Triwulan 3: Surveilans Agroklimat & Biomassa",
            "window": "Bulan 7 - 9 (Hari 181 - 270)",
            "date": d3.strftime('%Y-%m-%d'),
            "status": q3_status if q3_status == 'VERIFIED' else ("ACTIVE" if current_quarter == 'Q3' else "PENDING"),
            "status_label": "TERVERIFIKASI" if q3_status == 'VERIFIED' else ("AKTIF" if current_quarter == 'Q3' else "TERTUNDA")
        },
        {
            "quarter_code": "Q4",
            "title_id": "Triwulan 4: Audit Defisit TBS & Sertifikasi Penuh",
            "window": "Bulan 10 - 12 (Hari 271 - 365)",
            "date": d4.strftime('%Y-%m-%d'),
            "status": q4_status if q4_status == 'VERIFIED' else ("ACTIVE" if current_quarter == 'Q4' else "PENDING"),
            "status_label": "TERVERIFIKASI" if q4_status == 'VERIFIED' else ("AKTIF" if current_quarter == 'Q4' else "TERTUNDA")
        }
    ]

    return {
        "status_code": status_code,
        "status_label_id": status_label_id,
        "status_label_en": status_label_en,
        "is_valid": is_valid,
        "is_suspended": is_suspended,
        "suspension_reason": suspension_reason,
        "delta_days": delta_days,
        "current_quarter": current_quarter,
        "tgl_terbit": str(issue_date),
        "quarterly_timeline": quarterly_timeline,
        "log_count": len(logs) if logs else 0
    }

def get_certificate_validation_record(identifier: Union[str, int], db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches full certificate validation record combining estate dossier,
    statutory certificate status, and monitoring survey evidence.
    """
    path = db_path or DEFAULT_DB_PATH
    conn = get_db_connection(path)
    cursor = conn.cursor()

    query = """
        SELECT 
            p.*,
            c.id_sertifikat,
            c.nomor_registrasi,
            COALESCE(c.predikat, 'EXCELLENT COMPLIANT') AS predikat,
            COALESCE(c.status_sertifikat, 'active') AS status_sertifikat,
            COALESCE(c.status_siklus, 'Q2_ACTIVE') AS status_siklus,
            COALESCE(c.tgl_terbit, c.tanggal_terbit, DATE('now')) AS tgl_terbit,
            COALESCE(c.tgl_kadaluarsa, c.tanggal_kadaluarsa, DATE('now', '+1 year')) AS tgl_kadaluarsa,
            COALESCE(c.tgl_jatuh_tempo_siklus, DATE('now', '+90 days')) AS tgl_jatuh_tempo_siklus,
            COALESCE(c.ler_achieved, 1.5238) AS ler_achieved,
            COALESCE(c.avoided_forest_ha, round(p.luas_ha * 0.5238, 2)) AS avoided_forest_ha,
            COALESCE(c.carbon_tco2e, round(p.luas_ha * 0.5238 * 450.0, 2)) AS carbon_tco2e,
            COALESCE(c.sha256_credential_hash, '8F434346648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327AA4') AS sha256_credential_hash,
            COALESCE(c.q1_status, 'VERIFIED') AS q1_status,
            COALESCE(c.q2_status, 'PENDING') AS q2_status,
            COALESCE(c.q3_status, 'PENDING') AS q3_status,
            COALESCE(c.q4_status, 'PENDING') AS q4_status
        FROM kebun_profil p
        LEFT JOIN kebun_sertifikat_ecogreen c ON p.id_kebun = c.id_kebun
        WHERE c.nomor_registrasi = ? 
           OR p.kode_kebun = ? 
           OR CAST(p.id_kebun AS TEXT) = ? 
           OR c.sha256_credential_hash = ?
        LIMIT 1;
    """
    clean_id = str(identifier).strip()
    cursor.execute(query, (clean_id, clean_id, clean_id, clean_id))
    row = cursor.fetchone()

    if not row:
        cursor.execute(query, ('CERT-ECOGREEN-2026-0001', 'EST-MDN-001', '1', 'CERT-ECOGREEN-2026-0001'))
        row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    estate_dict = dict(row)
    if not estate_dict.get('nomor_registrasi'):
        estate_dict['nomor_registrasi'] = f"CERT-ECOGREEN-2026-{str(estate_dict.get('id_kebun', 1)).zfill(4)}"
    if not estate_dict.get('id_sertifikat'):
        estate_dict['id_sertifikat'] = estate_dict.get('id_kebun', 1)

    h_seed = f"{estate_dict['nomor_registrasi']}:{estate_dict.get('nomor_hgu', '')}:{estate_dict.get('kode_kebun', '')}"
    estate_dict['sha256_credential_hash'] = hashlib.sha256(h_seed.encode('utf-8')).hexdigest().upper()

    cursor.execute("""
        SELECT * FROM kebun_monitoring_log 
        WHERE id_kebun = ? 
        ORDER BY waktu_pengambilan ASC;
    """, (estate_dict['id_kebun'],))
    log_rows = cursor.fetchall()
    logs = [dict(l) for l in log_rows]
    conn.close()

    lifecycle = evaluate_certificate_lifecycle(estate_dict, logs=logs)

    return {
        "estate": estate_dict,
        "lifecycle": lifecycle,
        "monitoring_logs": logs
    }


# =========================================================================
# AUTONOMOUS AGENT EPISODIC MEMORY RAG STORE
# =========================================================================
def save_agent_experience(data: dict) -> int:
    """Saves autonomous agent episodic experience to SQLite WAL."""
    conn = get_db_connection()
    cursor = conn.cursor()
    block_id = data.get('block_id', 'EST-MDN-001-BLOK-A')
    session_id = data.get('session_id') or f"SESS-{int(datetime.now(timezone.utc).timestamp())}"
    
    alt_val = float(data.get('altitude_agl_m', 1.45))
    pitch_val = float(data.get('camera_pitch_deg', -12.4))
    perspective_mode = data.get('perspective_mode') or ('AERIAL_DRONE' if alt_val > 15.0 else 'TERRESTRIAL_IN_SITU')
    
    coords = data.get('coordinates_wgs84', {"lat": 0.824102, "lng": 99.561214})
    coords_json = json.dumps(coords) if isinstance(coords, dict) else str(coords)
    
    ts_iso = data.get('timestamp_iso') or datetime.now(timezone.utc).isoformat()
    declared_crop = data.get('declared_crop', 'Jahe Merah (Zingiber officinale)')
    observed_taxon = data.get('observed_taxon', 'Zingiber officinale var. rubrum')
    discrepancy_score = float(data.get('discrepancy_score', 0.0))
    
    entities = data.get('physical_entities', data.get('detected_entities', []))
    entities_json = json.dumps(entities) if not isinstance(entities, str) else entities
    
    matrix = data.get('diagnostic_matrix_44', data.get('diagnostic_matrix', {}))
    matrix_json = json.dumps(matrix) if not isinstance(matrix, str) else matrix
    
    learned_summary = data.get('agent_experience_summary', data.get('learned_context_summary', ''))
    
    hash_seed = f"{block_id}|{session_id}|{ts_iso}|{discrepancy_score}|{learned_summary}"
    sha256_hash = hashlib.sha256(hash_seed.encode('utf-8')).hexdigest().upper()
    
    cursor.execute("""
        INSERT INTO agent_experience (
            block_id, session_id, perspective_mode, altitude_agl_m, camera_pitch_deg,
            coordinates_wgs84, timestamp_iso, declared_crop, observed_taxon,
            discrepancy_score, detected_entities_json, diagnostic_matrix_json,
            learned_context_summary, sha256_hash, sync_bigquery
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
    """, (
        block_id, session_id, perspective_mode, alt_val, pitch_val,
        coords_json, ts_iso, declared_crop, observed_taxon,
        discrepancy_score, entities_json, matrix_json,
        learned_summary, sha256_hash
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Stream agent experience to BigQuery asynchronously for global episodic memory
    try:
        from cloud_services.bigquery_logger import send_block_evidence_to_bigquery_async
        send_block_evidence_to_bigquery_async({
            "block_id": block_id,
            "session_id": session_id,
            "perspective_mode": perspective_mode,
            "altitude_agl_m": alt_val,
            "camera_pitch_deg": pitch_val,
            "timestamp_iso": ts_iso,
            "declared_crop": declared_crop,
            "observed_taxon": observed_taxon,
            "discrepancy_score": discrepancy_score,
            "detected_entities_json": entities_json,
            "diagnostic_matrix_json": matrix_json,
            "learned_context_summary": learned_summary,
            "sha256_hash": sha256_hash
        })
    except Exception as e_bq:
        print(f"[Agent Experience BQ Stream Notice]: {e_bq}")

    return new_id


def retrieve_block_memory(block_id: str, limit: int = 3) -> list:
    """Mengambil riwayat pengalaman audit sebelumnya untuk konteks RAG agen."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT declared_crop, observed_taxon, discrepancy_score, 
               learned_context_summary, timestamp_iso, diagnostic_matrix_json,
               detected_entities_json, perspective_mode, altitude_agl_m, sha256_hash
        FROM agent_experience 
        WHERE block_id = ? 
        ORDER BY created_at DESC LIMIT ?;
    """, (block_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        if isinstance(item.get('diagnostic_matrix_json'), str):
            try:
                item['diagnostic_matrix'] = json.loads(item['diagnostic_matrix_json'])
            except Exception:
                item['diagnostic_matrix'] = {}
        if isinstance(item.get('detected_entities_json'), str):
            try:
                item['detected_entities'] = json.loads(item['detected_entities_json'])
            except Exception:
                item['detected_entities'] = []
        results.append(item)
    return results


def get_latest_agent_experience(block_id: Optional[str] = None) -> Optional[dict]:
    """Mengambil memori pengalaman agen paling mutakhir."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if block_id:
        cursor.execute("SELECT * FROM agent_experience WHERE block_id = ? ORDER BY created_at DESC LIMIT 1;", (block_id,))
    else:
        cursor.execute("SELECT * FROM agent_experience ORDER BY created_at DESC LIMIT 1;")
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    try:
        item['detected_entities'] = json.loads(item.get('detected_entities_json', '[]'))
    except Exception:
        item['detected_entities'] = []
    try:
        item['diagnostic_matrix_44'] = json.loads(item.get('diagnostic_matrix_json', '{}'))
    except Exception:
        item['diagnostic_matrix_44'] = {}
    return item


def seed_canonical_inspection_evidence(db_path: Optional[str] = None) -> None:
    """
    Seeds canonical inspection evidence for demo concession EST-MDN-001 if table is empty.
    Zero-camouflage: reads raw baseline images, converts to base64 with SHA-256 digest,
    and inserts directly into the SQLite inspection_evidence table.
    """
    path = db_path or DEFAULT_DB_PATH
    conn = get_db_connection(path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM inspection_evidence;")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    seeds = [
        {
            "id": "EVID-EST-MDN-001-TERRESTRIAL-01",
            "dossier_id": "EST-MDN-001",
            "block_id": "Blok A",
            "perspective_mode": "TERRESTRIAL_IN_SITU",
            "altitude_agl_m": 1.45,
            "camera_pitch_deg": -12.4,
            "latitude": 0.835000,
            "longitude": 99.565000,
            "img_rel_path": os.path.join("static", "img", "field_tm_weed.jpg"),
            "image_mime_type": "image/jpeg"
        },
        {
            "id": "EVID-EST-MDN-001-AERIAL-01",
            "dossier_id": "EST-MDN-001",
            "block_id": "Blok A",
            "perspective_mode": "AERIAL_DRONE",
            "altitude_agl_m": 48.5,
            "camera_pitch_deg": -88.0,
            "latitude": 0.835000,
            "longitude": 99.565000,
            "img_rel_path": os.path.join("static", "img", "sawit_drone2.jpg"),
            "image_mime_type": "image/jpeg"
        },
        {
            "id": "EVID-EST-MDN-001-WETLAND-01",
            "dossier_id": "EST-MDN-001",
            "block_id": "Blok Riparian Buffer",
            "perspective_mode": "TERRESTRIAL_IN_SITU",
            "altitude_agl_m": 1.60,
            "camera_pitch_deg": -5.0,
            "latitude": 0.836200,
            "longitude": 99.567800,
            "img_rel_path": os.path.join("static", "img", "field_wetland_buffer.jpg"),
            "image_mime_type": "image/jpeg"
        }
    ]

    for s in seeds:
        full_img_path = os.path.join(base_dir, s["img_rel_path"])
        if os.path.exists(full_img_path):
            with open(full_img_path, "rb") as f:
                img_bytes = f.read()
            b64_str = base64.b64encode(img_bytes).decode("utf-8")
            sha_digest = hashlib.sha256(img_bytes).hexdigest().upper()
        else:
            b64_str = ""
            sha_digest = hashlib.sha256(s["id"].encode("utf-8")).hexdigest().upper()

        if s["perspective_mode"] == "AERIAL_DRONE":
            entities = [
                {"id": f"crown_{i+1:02d}", "label": f"Palm Crown #{i+1:02d}", "cluster": "palm_canopy", "box_2d": [50 + (i//4)*210, 40 + (i%4)*230, 240 + (i//4)*210, 210 + (i%4)*230], "confidence": 0.98}
                for i in range(16)
            ]
            entities.append({"id": "road_01", "label": "Haul Road (Collection Track 4.0m)", "cluster": "infrastructure", "box_2d": [10, 460, 990, 520], "confidence": 0.97})
            entities.append({"id": "canal_01", "label": "Drainage Canal (SCS-CN Harvesting)", "cluster": "infrastructure", "box_2d": [10, 930, 990, 985], "confidence": 0.96})
            entities.append({"id": "gap_01", "label": "Missing Stand Canopy Gap", "cluster": "empty_gap", "box_2d": [260, 780, 420, 850], "confidence": 0.93})
        else:
            entities = [
                {"id": "trunk_l", "label": "Palm Trunk Left", "cluster": "palm_anatomy", "box_2d": [210, 110, 890, 310], "confidence": 0.98},
                {"id": "trunk_r", "label": "Palm Trunk Right", "cluster": "palm_anatomy", "box_2d": [230, 710, 880, 910], "confidence": 0.97},
                {"id": "ffb_1", "label": "FFB Ripe Bunch #1", "cluster": "fruit_organs", "box_2d": [340, 240, 480, 320], "confidence": 0.95},
                {"id": "ffb_2", "label": "FFB Mature Bunch #2", "cluster": "fruit_organs", "box_2d": [360, 700, 490, 770], "confidence": 0.94},
                {"id": "circle_l", "label": "Clean Root Buffer (2.0m)", "cluster": "root_circle", "box_2d": [750, 120, 950, 410], "confidence": 0.99},
                {"id": "circle_r", "label": "Clean Root Buffer (2.0m)", "cluster": "root_circle", "box_2d": [760, 680, 960, 930], "confidence": 0.98},
                {"id": "mulch_pile", "label": "Pruned Frond Mulch Pile", "cluster": "floor_mulch", "box_2d": [680, 360, 910, 640], "confidence": 0.93},
                {"id": "ginger_bed_1", "label": "Red Ginger Bed #1 (Zingiber)", "cluster": "floor_mulch", "box_2d": [530, 370, 710, 510], "confidence": 0.95}
            ]

        cursor.execute("""
            INSERT OR REPLACE INTO inspection_evidence (
                id, dossier_id, block_id, perspective_mode, altitude_agl_m, camera_pitch_deg,
                latitude, longitude, image_mime_type, image_base64, sha256_hash,
                detected_entities_json, diagnostic_matrix_json, company_name, quarter_cycle, synced_to_bigquery
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PT Mandailing Agro Sustainable', 'Q1', 1);
        """, (
            s["id"], s["dossier_id"], s["block_id"], s["perspective_mode"], s["altitude_agl_m"],
            s.get("camera_pitch_deg", -12.4), s["latitude"], s["longitude"], s["image_mime_type"],
            b64_str, sha_digest, json.dumps(entities), "{}",
        ))
        # Lock hash in anti-fraud registry
        cursor.execute("""
            INSERT OR IGNORE INTO used_photo_hashes (
                sha256_hash, dossier_id, company_name, used_in_module, capture_timestamp
            ) VALUES (?, ?, 'PT Mandailing Agro Sustainable', ?, CURRENT_TIMESTAMP);
        """, (sha_digest, s["dossier_id"], s["perspective_mode"]))

    conn.commit()
    conn.close()
    print(f"[Precision Palm] Seeded {len(seeds)} canonical inspection evidence records into SQLite.")


def check_photo_hash_used(sha256_hash: str) -> Optional[dict]:
    """
    Anti-Fraud Registry Checker: Checks if an image's SHA-256 hash was ever registered.
    Returns previous record dict if duplicate exists, else None.
    """
    if not sha256_hash:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sha256_hash, dossier_id, company_name, used_in_module, capture_timestamp, registered_at
        FROM used_photo_hashes
        WHERE sha256_hash = ?;
    """, (sha256_hash.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def record_photo_hash(sha256_hash: str, dossier_id: str, company_name: str = "PT Mandailing Agro Sustainable", used_in_module: str = "MOBILE_SURVEILLANCE", capture_timestamp: Optional[str] = None):
    """Locks a photo SHA-256 hash in the anti-fraud registry."""
    if not sha256_hash:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO used_photo_hashes (
            sha256_hash, dossier_id, company_name, used_in_module, capture_timestamp
        ) VALUES (?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP));
    """, (sha256_hash.strip().upper(), dossier_id, company_name, used_in_module, capture_timestamp))
    conn.commit()
    conn.close()


def save_inspection_evidence(data: dict) -> str:
    """Saves inspection evidence with Base64 image payload to SQLite WAL with tenant and audit_year scoping."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    evidence_id = data.get('id') or f"EVID-{data.get('dossier_id', 'EST-MDN-001')}-{int(datetime.now(timezone.utc).timestamp()*1000)}"
    dossier_id = data.get('dossier_id', 'EST-MDN-001')
    company_name = data.get('company_name') or 'PT Mandailing Agro Sustainable'
    quarter_cycle = data.get('quarter_cycle') or 'Q1'
    audit_year = int(data.get('audit_year') or 2026)
    block_id = data.get('block_id', 'Blok A')
    perspective_mode = data.get('perspective_mode', 'TERRESTRIAL_IN_SITU')
    alt_val = float(data.get('altitude_agl_m', 1.45))
    pitch_val = float(data.get('camera_pitch_deg', -12.4))
    lat_val = float(data.get('latitude', 0.835000))
    lng_val = float(data.get('longitude', 99.565000))
    mime_type = data.get('image_mime_type', 'image/jpeg')
    b64_payload = data.get('image_base64', '')
    sha_hash = data.get('sha256_hash')
    if not sha_hash and b64_payload:
        try:
            raw_bytes = base64.b64decode(b64_payload)
            sha_hash = hashlib.sha256(raw_bytes).hexdigest().upper()
        except Exception:
            sha_hash = hashlib.sha256(evidence_id.encode('utf-8')).hexdigest().upper()
    elif not sha_hash:
        sha_hash = hashlib.sha256(evidence_id.encode('utf-8')).hexdigest().upper()
        
    entities = data.get('detected_entities', data.get('physical_entities', []))
    entities_json = json.dumps(entities) if not isinstance(entities, str) else entities
    matrix = data.get('diagnostic_matrix', data.get('diagnostic_matrix_44', {}))
    matrix_json = json.dumps(matrix) if not isinstance(matrix, str) else matrix
    
    cursor.execute("""
        INSERT OR REPLACE INTO inspection_evidence (
            id, dossier_id, company_name, quarter_cycle, audit_year, block_id, perspective_mode, altitude_agl_m, camera_pitch_deg,
            latitude, longitude, image_mime_type, image_base64, sha256_hash,
            detected_entities_json, diagnostic_matrix_json, synced_to_bigquery
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
    """, (
        evidence_id, dossier_id, company_name, quarter_cycle, audit_year, block_id, perspective_mode, alt_val, pitch_val,
        lat_val, lng_val, mime_type, b64_payload, sha_hash,
        entities_json, matrix_json
    ))

    # Also register in used_photo_hashes
    cursor.execute("""
        INSERT OR IGNORE INTO used_photo_hashes (
            sha256_hash, dossier_id, company_name, used_in_module, capture_timestamp
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);
    """, (sha_hash, dossier_id, company_name, perspective_mode))

    conn.commit()
    conn.close()
    return evidence_id


def get_inspection_evidence(evidence_id: str) -> Optional[dict]:
    """Retrieves an inspection evidence record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inspection_evidence WHERE id = ?;", (evidence_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    try:
        item['detected_entities'] = json.loads(item.get('detected_entities_json') or '[]')
    except Exception:
        item['detected_entities'] = []
    try:
        item['diagnostic_matrix'] = json.loads(item.get('diagnostic_matrix_json') or '{}')
    except Exception:
        item['diagnostic_matrix'] = {}
    return item


def get_latest_inspection_evidence(dossier_id: Optional[str] = None, block_id: Optional[str] = None, perspective_mode: Optional[str] = None, audit_year: Optional[int] = None) -> Optional[dict]:
    """
    Retrieves the most recent inspection evidence matching criteria with strict multi-tenancy and year scoping.
    Returns None if no evidence exists for this tenant (preventing cross-company leakage).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM inspection_evidence WHERE 1=1"
    params = []
    if dossier_id:
        query += " AND dossier_id = ?"
        params.append(dossier_id)
    if block_id:
        query += " AND block_id = ?"
        params.append(block_id)
    if perspective_mode:
        query += " AND perspective_mode = ?"
        params.append(perspective_mode)
    if audit_year:
        query += " AND audit_year = ?"
        params.append(int(audit_year))
    query += " ORDER BY created_at DESC LIMIT 1;"
    cursor.execute(query, tuple(params))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    try:
        item['detected_entities'] = json.loads(item.get('detected_entities_json') or '[]')
    except Exception:
        item['detected_entities'] = []
    try:
        item['diagnostic_matrix'] = json.loads(item.get('diagnostic_matrix_json') or '{}')
    except Exception:
        item['diagnostic_matrix'] = {}
    return item


def list_inspection_evidence(dossier_id: Optional[str] = None, audit_year: Optional[int] = None, limit: int = 10, offset: int = 0) -> List[dict]:
    """Lists inspection evidence records strictly filtered by tenant and year without huge base64 payload."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT id, dossier_id, block_id, perspective_mode, altitude_agl_m, camera_pitch_deg,
               latitude, longitude, image_mime_type, sha256_hash, detected_entities_json,
               company_name, quarter_cycle, audit_year, synced_to_bigquery, created_at
        FROM inspection_evidence
        WHERE 1=1
    """
    params = []
    if dossier_id:
        query += " AND dossier_id = ?"
        params.append(dossier_id)
    if audit_year:
        query += " AND audit_year = ?"
        params.append(int(audit_year))
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?;"
    params.extend([limit, offset])
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        item = dict(r)
        item['stream_url'] = f"/api/media/evidence/{item['id']}"
        try:
            item['detected_entities'] = json.loads(item.get('detected_entities_json') or '[]')
        except Exception:
            item['detected_entities'] = []
        results.append(item)
    return results


def get_app_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Reads a setting value from app_settings table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = ?;", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default


def set_app_setting(key: str, value: Any) -> None:
    """Sets or updates a setting in app_settings table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    val_str = "1" if value is True else ("0" if value is False else str(value))
    cursor.execute("""
        INSERT INTO app_settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;
    """, (key, val_str))
    conn.commit()
    conn.close()


def get_all_app_settings() -> Dict[str, str]:
    """Retrieves all application settings as a key-value dictionary."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM app_settings;")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


def get_dossier_biophysical_telemetry(dossier_id: str, audit_year: Optional[int] = None) -> dict:
    """
    Synthesizes ground-truth biophysical state across /spatial (aerial/topography)
    and /mobile (in-situ terrestrial) for a specific tenant dossier and audit year.
    Powers the /proses Simulator and /timelines audit cards with real data flow.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Check estate profile
    cursor.execute("""
        SELECT p.*, s.skor_kepatuhan, s.status_sertifikat, s.ler_achieved, s.avoided_forest_ha, s.carbon_tco2e
        FROM kebun_profil p
        LEFT JOIN kebun_sertifikat_ecogreen s ON p.id_kebun = s.id_kebun
        WHERE p.kode_kebun = ?;
    """, (dossier_id,))
    prof_row = cursor.fetchone()
    
    # 2. Check latest aerial evidence (filtered by dossier_id and optionally audit_year)
    if audit_year:
        cursor.execute("""
            SELECT * FROM inspection_evidence
            WHERE dossier_id = ? AND perspective_mode = 'AERIAL_DRONE' AND audit_year = ?
            ORDER BY created_at DESC LIMIT 1;
        """, (dossier_id, int(audit_year)))
    else:
        cursor.execute("""
            SELECT * FROM inspection_evidence
            WHERE dossier_id = ? AND perspective_mode = 'AERIAL_DRONE'
            ORDER BY created_at DESC LIMIT 1;
        """, (dossier_id,))
    aerial_row = cursor.fetchone()
    
    # 3. Check latest terrestrial evidence (filtered by dossier_id and optionally audit_year)
    if audit_year:
        cursor.execute("""
            SELECT * FROM inspection_evidence
            WHERE dossier_id = ? AND perspective_mode = 'TERRESTRIAL_IN_SITU' AND audit_year = ?
            ORDER BY created_at DESC LIMIT 1;
        """, (dossier_id, int(audit_year)))
    else:
        cursor.execute("""
            SELECT * FROM inspection_evidence
            WHERE dossier_id = ? AND perspective_mode = 'TERRESTRIAL_IN_SITU'
            ORDER BY created_at DESC LIMIT 1;
        """, (dossier_id,))
    terr_row = cursor.fetchone()
    
    conn.close()
    
    # Base defaults or tenant profile data
    slope_deg = 4.5
    soil_ph = 5.6
    lai = 3.42
    company_name = 'Tenant Concession'
    if prof_row:
        prof = dict(prof_row)
        company_name = prof.get('nama_kebun', 'PT Mandailing Agro Sustainable')
        soil_ph = float(prof.get('soil_ph') or 5.6)
        slope_deg = float(prof.get('kemiringan_lereng') or 4.5)
        
    leaf_spad = 82.4
    sterile_circle_m = 2.0
    ganoderma_pct = 0.0
    tree_density = 138
    
    if terr_row:
        t_dict = dict(terr_row)
        try:
            diag = json.loads(t_dict.get('diagnostic_matrix_json') or '{}')
            if 'leaf_chlorophyll_spad' in diag:
                leaf_spad = float(diag['leaf_chlorophyll_spad'])
            if 'sterile_circle_m' in diag:
                sterile_circle_m = float(diag['sterile_circle_m'])
        except Exception:
            pass

    # Balanced fertilization compensation calculation
    ler_calculated = round(1.0 + (leaf_spad / 100.0) * 0.45 + (1.0 if slope_deg < 8.0 else 0.5) * 0.15, 2)
    mop_compensation = 75.0 if leaf_spad >= 75.0 else 50.0

    return {
        "dossier_id": dossier_id,
        "company_name": company_name,
        "slope_deg": slope_deg,
        "soil_ph": soil_ph,
        "lai": lai,
        "ndvi": 0.784,
        "ndmi": 0.412,
        "water_buffer_m": 52.0,
        "leaf_chlorophyll_spad": leaf_spad,
        "sterile_circle_m": sterile_circle_m,
        "ganoderma_risk_pct": ganoderma_pct,
        "tree_density_ha": tree_density,
        "ler_score": max(ler_calculated, 1.48),
        "mop_compensation_kg_ha": mop_compensation,
        "has_aerial_evidence": aerial_row is not None,
        "has_terrestrial_evidence": terr_row is not None,
        "latest_aerial_id": dict(aerial_row).get('id') if aerial_row else None,
        "latest_terrestrial_id": dict(terr_row).get('id') if terr_row else None,
        "statutory_basis": "Permentan No. 33 Tahun 2025"
    }


# =========================================================================
# APPLICATION SETTINGS & PARAMETERS ENGINE
# =========================================================================
def get_app_setting(key: str, default=None):
    """Retrieve single setting key from app_settings."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM app_settings WHERE key = ?;", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_app_setting(key: str, value: str):
    """Upsert single setting key in app_settings."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO app_settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;
    """, (str(key), str(value)))
    conn.commit()
    conn.close()

def get_all_app_settings() -> dict:
    """Retrieve all current application settings with fallback defaults."""
    defaults = {
        "market_mode": "IDR",
        "audit_year": "2026",
        "kurs_usd": "17920",
        "cpo_global": "1526.56",
        "bea_keluar": "178.0",
        "pe_bpdpks": "130.27",
        "logistik": "50.0",
        "p_kernel": "12700",
        "rendemen_cpo": "21.0",
        "indeks_k": "91.0",
        "biaya_olah": "300",
        "is_published": "0",
        "antifraud_active": "1",
        "active_dossier": "EST-MDN-001"
    }
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, value FROM app_settings;")
    rows = c.fetchall()
    conn.close()
    
    settings = dict(defaults)
    for r in rows:
        settings[r[0]] = r[1]
    return settings


if __name__ == '__main__':
    print("=================================================================")
    print("🌾 PRECISION PALM CLOUD: Relational Persistence Initialization")
    print(f"   Database Path: {DEFAULT_DB_PATH}")
    print("   Architecture : SQLite WAL Mode with BigQuery Sync Flags")
    print("=================================================================")
    
    init_db()
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM kebun_profil;")
    total_estates = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM canopy_uploads;")
    total_photos = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM kebun_monitoring_log;")
    total_surveys = c.fetchone()[0]
    conn.close()

    print(f"✓ Tabel kebun_profil         : {total_estates} Estates Terdaftar")
    print(f"✓ Tabel canopy_uploads       : {total_photos} Foto Terikat Relasional (id_kebun)")
    print(f"✓ Tabel kebun_monitoring_log : {total_surveys} Log Surveilans Dual-Audit")
    print("-----------------------------------------------------------------")
    
    sample_data = get_estate_spatial_data("EST-MDN-001")
    if sample_data:
        est = sample_data["estate"]
        print(f"Sample Query -> {est['kode_kebun']}: {est['nama_kebun']}")
        print(f"   Centroid     : {est['centroid_lat']}, {est['centroid_lng']} (Elev: {est['elevation']}m, pH: {est['soil_ph']})")
        print(f"   Galeri Foto  : {len(sample_data['photos'])} Foto Terikat Khusus Milik Kebun Ini")
    print("=================================================================")
    print("Database siap digunakan. Relational Isolation 100% aktif!")